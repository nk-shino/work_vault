"""語義（senses）へ書き込む唯一の場所。

呼んでよいのは proposals.py（提案の受理）と review.py（レビュー画面）の2つだけ。
それ以外から書こうとすると guards の before_flush で止まり、
どこから呼ばれているかは tests/test_write_paths.py が静的に検査する。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from glossary.db.guards import sense_write_scope, snapshot
from glossary.db.models import EXCERPT_MAX_LEN, SENSE_STATUSES, Evidence, Sense, Term, new_id
from glossary.domain.errors import ConflictError, ValidationFailed

EDITABLE_FIELDS = ("definition", "scope_note", "context_tag", "status", "confidence")


@dataclass(frozen=True)
class EvidenceInput:
    source_type: str
    source_ref: str
    excerpt: str
    occurred_at: datetime | None
    masked: bool


def _check_evidences(evidences: list[EvidenceInput]) -> None:
    if not evidences:
        raise ValidationFailed("用例が1件も無い定義は保存できない")
    for ev in evidences:
        if not ev.excerpt.strip():
            raise ValidationFailed("空の用例は保存できない")
        if len(ev.excerpt) > EXCERPT_MAX_LEN:
            raise ValidationFailed(f"用例は {EXCERPT_MAX_LEN} 文字まで（{len(ev.excerpt)} 文字）")
        if ev.source_type == "mail" and not ev.masked:
            raise ValidationFailed("メール由来の用例はマスキング済みのものしか保存できない")


def _check_fields(fields: dict[str, Any]) -> None:
    if "definition" in fields and not str(fields["definition"] or "").strip():
        raise ValidationFailed("定義は空にできない")
    if "status" in fields and fields["status"] not in SENSE_STATUSES:
        raise ValidationFailed(f"語義の状態が不正: {fields['status']}")


def create_sense(
    session: Session,
    term: Term,
    *,
    definition: str,
    evidences: list[EvidenceInput],
    source_type: str,
    status: str,
    scope_note: str | None = None,
    context_tag: str | None = None,
    confidence: float | None = None,
    adopted_by: str = "human",
) -> Sense:
    _check_evidences(evidences)
    _check_fields({"definition": definition, "status": status})
    # 語義は最初の用例を指す必要があるので、用例の ID を先に決めておく
    ev_ids = [new_id() for _ in evidences]
    with sense_write_scope():
        sense = Sense(
            id=new_id(),
            term=term,
            first_evidence_id=ev_ids[0],
            definition=definition.strip(),
            scope_note=scope_note,
            context_tag=context_tag,
            source_type=source_type,
            confidence=confidence,
            status=status,
            adopted_by=adopted_by,
        )
        session.add(sense)
        for ev_id, ev in zip(ev_ids, evidences, strict=True):
            session.add(
                Evidence(
                    id=ev_id,
                    sense=sense,
                    source_type=ev.source_type,
                    source_ref=ev.source_ref,
                    excerpt=ev.excerpt,
                    occurred_at=ev.occurred_at,
                    masked=ev.masked,
                )
            )
        session.flush()
    return sense


def update_sense(
    session: Session, sense: Sense, *, expected_revision: int, changes: dict[str, Any]
) -> Sense:
    unknown = set(changes) - set(EDITABLE_FIELDS)
    if unknown:
        raise ValidationFailed(f"編集できない項目: {sorted(unknown)}")
    _check_fields(changes)
    # 画面を開いた時点の版と今の版が違えば、誰かが先に保存している。上書きせずに返す
    if sense.revision_number != expected_revision:
        raise ConflictError(snapshot(sense), changes, expected_revision)
    with sense_write_scope():
        for key, value in changes.items():
            setattr(sense, key, value)
        session.flush()
    return sense


def add_evidences(session: Session, sense: Sense, evidences: list[EvidenceInput]) -> int:
    """登録済みの語義に用例を足す。同じ出典・同じ文面のものは足さない（取り込みを繰り返しても増えない）。

    定義は変えないので語義の版は上がらない。版に結び付いた評価もそのまま有効。
    """
    _check_evidences(evidences)
    have = {(e.source_ref, e.excerpt) for e in sense.evidences}
    added = 0
    for ev in evidences:
        if (ev.source_ref, ev.excerpt) in have:
            continue
        session.add(
            Evidence(
                sense=sense,
                source_type=ev.source_type,
                source_ref=ev.source_ref,
                excerpt=ev.excerpt,
                occurred_at=ev.occurred_at,
                masked=ev.masked,
            )
        )
        have.add((ev.source_ref, ev.excerpt))
        added += 1
    session.flush()
    return added
