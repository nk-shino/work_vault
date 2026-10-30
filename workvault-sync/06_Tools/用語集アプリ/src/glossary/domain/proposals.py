"""提案キュー。LLM や統計が出したものは、人が採用するまで用語集に入らない。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from glossary.db.guards import edit_context
from glossary.db.models import (
    RELATION_METHODS,
    RELATION_TYPES,
    Proposal,
    Relation,
    Sense,
    Term,
    now,
)
from glossary.domain import sense_writer
from glossary.domain.errors import NotFound, ValidationFailed
from glossary.domain.sense_writer import EvidenceInput


@dataclass(frozen=True)
class SenseOverrides:
    """「修正して採用」で人が書き換えた項目。None は提案のまま。"""

    definition: str | None = None
    context_tag: str | None = None
    scope_note: str | None = None


# 人が画面から直接入れたものの生成元。統計やモデルの提案と区別して、採用率の計算から外せるように
HUMAN = "human"


def add_proposal(
    session: Session,
    *,
    proposal_type: str,
    payload: dict[str, Any],
    model_name: str,
    prompt_version: str,
    score: float | None,
) -> Proposal:
    p = Proposal(
        proposal_type=proposal_type,
        payload_json=json.dumps(payload, ensure_ascii=False, default=str),
        model_name=model_name,
        prompt_version=prompt_version,
        score=score,
        status="pending",
    )
    session.add(p)
    return p


def _pending(session: Session, proposal_id: str) -> Proposal:
    p = session.get(Proposal, proposal_id)
    if p is None:
        raise NotFound(f"提案が無い: {proposal_id}")
    if p.status != "pending":
        raise ValidationFailed(f"この提案は処理済み（{p.status}）")
    return p


def _find_or_create_term(session: Session, headword: str) -> Term:
    term = session.scalars(select(Term).where(Term.headword == headword)).first()
    if term is None:
        term = Term(headword=headword, status="draft")
        session.add(term)
    return term


def _first_live_sense(session: Session, headword: str) -> Sense | None:
    return session.scalars(
        select(Sense)
        .join(Term)
        .where(Term.headword == headword, Sense.status.not_in(("rejected",)))
        .order_by(Sense.created_at)
    ).first()


def _evidence_inputs(payload: dict[str, Any]) -> list[EvidenceInput]:
    return [
        EvidenceInput(
            source_type=e["source_type"],
            source_ref=e["source_ref"],
            excerpt=e["excerpt"],
            occurred_at=datetime.fromisoformat(e["occurred_at"]) if e.get("occurred_at") else None,
            masked=bool(e["masked"]),
        )
        for e in payload.get("evidences", [])
    ]


def _accept_evidence(session: Session, payload: dict[str, Any]) -> None:
    sense = session.get(Sense, payload["sense_id"])
    if sense is None or sense.status == "rejected":
        raise ValidationFailed("用例を足す先の語義が無い（却下済みを含む）")
    sense_writer.add_evidences(session, sense, _evidence_inputs(payload))


def _accept_sense(
    session: Session,
    payload: dict[str, Any],
    ov: SenseOverrides | None,
    by_human: bool,
    adopted_by: str,
) -> None:
    evidences = _evidence_inputs(payload)
    edited = ov is not None and any(
        v is not None for v in (ov.definition, ov.context_tag, ov.scope_note)
    )
    term = _find_or_create_term(session, payload["headword"])
    # 手動登録で読み・英語・略語が添えられていれば、空いている欄にだけ入れる（既存の値は上書きしない）
    for key in ("reading", "english", "abbreviation"):
        if payload.get(key) and not getattr(term, key):
            setattr(term, key, payload[key])
    sense_writer.create_sense(
        session,
        term,
        definition=(ov.definition if ov and ov.definition else payload["definition"]),
        context_tag=(ov.context_tag if ov and ov.context_tag else payload.get("context_tag")),
        scope_note=(ov.scope_note if ov and ov.scope_note else payload.get("scope_note")),
        evidences=evidences,
        # 人が手を入れたものは出どころを human にする。後で AI 草案の採用率を測るときに分けるため
        source_type="human" if edited or by_human else "ai",
        confidence=payload.get("confidence"),
        status="confirmed",
        adopted_by=adopted_by,
    )
    if term.status == "draft":
        term.status = "active"


def _accept_relation(session: Session, payload: dict[str, Any]) -> None:
    if payload["relation_type"] not in RELATION_TYPES or payload["method"] not in RELATION_METHODS:
        raise ValidationFailed("関係の種類または算出方法が不正")
    src = _first_live_sense(session, payload["from_headword"])
    dst = _first_live_sense(session, payload["to_headword"])
    if src is None or dst is None:
        raise ValidationFailed("関係の両端の語に、先に語義を採用しておく必要がある")
    if src.id == dst.id:
        raise ValidationFailed("同じ語義どうしは関係付けできない")
    session.add(
        Relation(
            from_sense_id=src.id,
            to_sense_id=dst.id,
            relation_type=payload["relation_type"],
            score=payload.get("score"),
            method=payload["method"],
        )
    )


def accept(
    session: Session,
    proposal_id: str,
    *,
    reviewer: str | None,
    overrides: SenseOverrides | None = None,
    reason: str | None = None,
    adopted_by: str = "human",
) -> Proposal:
    """提案を受理する。画面から人が押したときも、自動判定が採用したときも、ここを通る。

    自動判定は adopted_by="auto" を渡す。確定（掲載）したことと人が確かめたことを区別するため。
    """
    p = _pending(session, proposal_id)
    payload = json.loads(p.payload_json)
    label = "修正して採用" if overrides else "採用"
    with edit_context(session, reviewer, reason or f"提案 {p.id[:8]} を{label}"):
        if p.proposal_type == "sense":
            _accept_sense(
                session, payload, overrides, by_human=p.model_name == HUMAN, adopted_by=adopted_by
            )
        elif p.proposal_type == "evidence":
            _accept_evidence(session, payload)
        else:
            _accept_relation(session, payload)
        p.status = "accepted"
        p.reviewed_by = reviewer
        p.reviewed_at = now()
        session.flush()
    return p


def reject(session: Session, proposal_id: str, *, reviewer: str | None) -> Proposal:
    p = _pending(session, proposal_id)
    p.status = "rejected"
    p.reviewed_by = reviewer
    p.reviewed_at = now()
    session.flush()
    return p


def accept_many(
    session: Session, proposal_ids: list[str], *, reviewer: str | None
) -> list[Proposal]:
    """選択した提案をまとめて受理する。

    1件でも処理できないものがあれば例外を出し、呼び出し側がコミットしないので
    全体が無効になる（全部か無しか）。モック定義の保護は画面側（web/app.py）の
    検査を通ったものだけがここへ届く前提だが、ここでも各提案は accept() の
    未処理チェックを通る。途中で失敗したら以降の採用は行われない。
    """
    done: list[Proposal] = []
    for pid in proposal_ids:
        done.append(accept(session, pid, reviewer=reviewer))
    return done


def reject_many(
    session: Session, proposal_ids: list[str], *, reviewer: str | None
) -> list[Proposal]:
    """選択した提案をまとめて却下する。扱いは accept_many と同じ（全部か無しか）。"""
    done: list[Proposal] = []
    for pid in proposal_ids:
        done.append(reject(session, pid, reviewer=reviewer))
    return done


def register_manually(
    session: Session,
    *,
    headword: str,
    definition: str,
    excerpt: str,
    source_ref: str,
    context_tag: str | None = None,
    scope_note: str | None = None,
    reading: str | None = None,
    english: str | None = None,
    abbreviation: str | None = None,
) -> Proposal:
    """画面から手で用語を登録する。

    語義へ書ける経路を「提案の受理」と「レビュー画面」の2つに絞っているので、
    手入力も提案として積んでからその場で受理する。履歴にも「手動で登録」と残る。
    用例は人が選んで書いたものなので、マスキングはしない（masked = False）。
    """
    headword = headword.strip()
    if not headword:
        raise ValidationFailed("見出し語は必須")
    p = add_proposal(
        session,
        proposal_type="sense",
        payload={
            "headword": headword,
            "definition": definition,
            "context_tag": context_tag or None,
            "scope_note": scope_note or None,
            "reading": reading or None,
            "english": english or None,
            "abbreviation": abbreviation or None,
            "evidences": [
                {
                    "source_type": "manual",
                    "source_ref": source_ref.strip() or "手入力",
                    "excerpt": excerpt.strip(),
                    "occurred_at": now().isoformat(),
                    "masked": False,
                }
            ],
        },
        model_name=HUMAN,
        prompt_version="manual",
        score=None,
    )
    session.flush()
    return accept(session, p.id, reviewer=None, reason="手動で登録")


def relate_manually(
    session: Session, *, from_headword: str, to_headword: str, relation_type: str
) -> Proposal:
    """画面から関連語を足す。同音異表記（混同注意）のように、統計では見つからない関係の入口。"""
    p = add_proposal(
        session,
        proposal_type="relation",
        payload={
            "from_headword": from_headword,
            "to_headword": to_headword.strip(),
            "relation_type": relation_type,
            "method": HUMAN,
            "score": None,
        },
        model_name=HUMAN,
        prompt_version="manual",
        score=None,
    )
    session.flush()
    return accept(session, p.id, reviewer=None, reason="関連語を手動で追加")
