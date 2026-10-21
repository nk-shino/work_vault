"""候補語と共起から提案を作り、自動判定で「用例の追加・自動採用・保留」に振り分ける。

2026-09-28 の設計方針（社内用語集アプリの設計・実装方針）で、全件を人が事前に承認する運用をやめた。
件数が多く、人が全部を見る運用は続かないため。人は登録後の評価と、保留になったものの確認に回る。

書き込みは必ず domain.proposals.accept を通す。自動でも人でも、用例必須・履歴・楽観ロックは同じにかかる。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from glossary.adapters.llm.mock_adapter import MOCK_MODEL_NAME
from glossary.db.models import EXCERPT_MAX_LEN, Proposal, Sense, Term
from glossary.domain.evaluations import review_queue
from glossary.domain.proposals import accept, add_proposal
from glossary.factory import model_name
from glossary.ports import LlmPort, is_document
from glossary.preprocess.masking import Masker
from glossary.preprocess.pipeline import MaskedDocument

# プロンプトを変えたら上げる。どの版の指示で出た草案かを後で分けて評価するため
PROMPT_VERSION = "sense-draft-v1"
SNIPPET_LEN = 120
MAX_EVIDENCES = 3

SENSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "definition": {"type": "string"},
        "context_tag": {"type": "string", "enum": ["業務", "設備", "物流", "品質", "その他"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        # 用例が定義を支えているかを LLM 自身にも答えさせる。自動採用の条件の1つにする
        "supported": {"type": "boolean"},
    },
    "required": ["definition", "context_tag", "confidence", "supported"],
}

# 独立した正誤判定。草案を作らせた呼び出しとは別に、定義と用例だけを見直させる。
# 出した本人の自己申告（supported）と、別の呼び出しでの検証の両方を通さないと自動採用にしない
VERIFY_PROMPT_VERSION = "sense-verify-v1"
VERIFY_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "supported": {"type": "boolean"},
        "reason": {"type": "string"},
    },
    "required": ["supported", "reason"],
}

# 自己改修。「修正が必要」の評価が付いた定義を、用例と指摘を根拠に書き直させる。
# 改稿案は人の確認を待つため、自動採用にはしない
REVISE_PROMPT_VERSION = "sense-revise-v1"
REVISE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "definition": {"type": "string"},
        "context_tag": {"type": "string", "enum": ["業務", "設備", "物流", "品質", "その他"]},
        "note": {"type": "string"},
    },
    "required": ["definition", "note"],
}

assert SNIPPET_LEN <= EXCERPT_MAX_LEN

_SENTENCE = re.compile(r"[^。！？!?\n]+[。！？!?]?")


def snippet(text: str, word: str, width: int = SNIPPET_LEN) -> str | None:
    """語を含む1文を抜き出す。長ければ語を中心に切り詰める。"""
    for m in _SENTENCE.finditer(text):
        sentence = m.group().strip()
        pos = sentence.find(word)
        if pos < 0:
            continue
        if len(sentence) <= width:
            return sentence
        start = max(0, min(pos - width // 3, len(sentence) - width))
        return "…" + sentence[start : start + width - 2] + "…"
    return None


def build_prompt(word: str, excerpts: list[str]) -> str:
    # 「対象語:」の行はモックも読む約束なので、形を変えるときは mock_adapter も合わせる
    lines = [
        "以下の用例から、社内用語としての意味を1〜2文で定義してください。",
        "用例に書かれていないことは推測しないでください。",
        "用例だけで意味が決められないときは confidence を低くし、supported を false にしてください。",
        f"対象語: {word}",
        "用例:",
    ]
    lines += [f"- {e}" for e in excerpts]
    return "\n".join(lines)


def build_verify_prompt(word: str, definition: str, excerpts: list[str]) -> str:
    lines = [
        "次の定義が、用例だけから裏付けられるかを確かめてください。",
        "定義に用例からは読み取れない推測や、用例と矛盾する部分があれば supported を false にし、",
        "reason にその箇所を1文で書いてください。裏付けられるなら supported を true にしてください。",
        f"対象語: {word}",
        f"定義: {definition}",
        "用例:",
    ]
    lines += [f"- {e}" for e in excerpts]
    return "\n".join(lines)


def build_revise_prompt(
    word: str, current_definition: str, comments: list[str], excerpts: list[str]
) -> str:
    lines = [
        "次の定義は、読んだ人から「修正が必要」と評価されています。",
        "現在の定義・指摘・用例だけを根拠に、定義を1〜2文で書き直してください。",
        "用例と指摘から読み取れないことは書かないでください。どこをどう直したかを note に書いてください。",
        f"対象語: {word}",
        f"現在の定義: {current_definition}",
    ]
    if comments:
        lines.append("指摘:")
        lines += [f"- {c}" for c in comments]
    lines.append("用例:")
    lines += [f"- {e}" for e in excerpts]
    return "\n".join(lines)


@dataclass(frozen=True)
class AdoptionRules:
    """自動判定のしきい値。config/adoption.yaml から読む（意味は同ファイルの説明を参照）。"""

    auto_adopt_new_terms: bool = True
    min_evidences: int = 2
    min_sources: int = 2
    min_confidence: float = 0.7
    require_supported: bool = True
    max_evidences_per_sense: int = 10

    @classmethod
    def from_yaml(cls, path: Path) -> AdoptionRules:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Outcome:
    proposed: int = 0  # 新しい語として提案した数（自動採用と保留の合計）
    auto_adopted: int = 0
    held: int = 0
    evidence_added: int = 0  # 登録済みの語に足した用例の数


# 自動判定が採用したことを示す名前。提案の reviewed_by と履歴の理由に残す
AUTO = "自動判定"


def collect_evidences(word: str, docs: list[MaskedDocument], limit: int) -> list[dict[str, Any]]:
    evidences: list[dict[str, Any]] = []
    for d in docs:
        s = snippet(d.text, word)
        # 同じ文面の用例を並べても裏付けは増えない。定型文の繰り返しで枠を埋めないようにする
        if s and all(e["excerpt"] != s for e in evidences):
            evidences.append(
                {
                    "source_type": "doc" if is_document(d.source_ref) else "mail",
                    "source_ref": d.source_ref,
                    "excerpt": s,
                    "occurred_at": d.occurred_at.isoformat(),
                    "masked": True,
                }
            )
        if len(evidences) >= limit:
            break
    return evidences


def judge(
    result: dict[str, Any],
    evidences: list[dict[str, Any]],
    word: str,
    is_mock: bool,
    rules: AdoptionRules,
) -> list[str]:
    """新しい語を自動採用してよいかを見る。返すのは満たしていない条件（空なら採用してよい）。"""
    reasons: list[str] = []
    if is_mock:
        reasons.append("定義文がモック（仮の文）")
    if not rules.auto_adopt_new_terms:
        reasons.append("新しい語の自動採用を止めている設定")
    if len(evidences) < rules.min_evidences:
        reasons.append(f"用例が {len(evidences)} 件（{rules.min_evidences} 件以上が必要）")
    sources = len({e["source_ref"] for e in evidences})
    if sources < rules.min_sources:
        reasons.append(f"出典が {sources} 種類（{rules.min_sources} 種類以上が必要）")
    if float(result.get("confidence") or 0) < rules.min_confidence:
        reasons.append(f"確からしさ {result.get('confidence')}（{rules.min_confidence} 以上が必要）")
    if rules.require_supported and result.get("supported") is not True:
        reasons.append("用例が定義を支えているとは答えていない")
    if not all(word in e["excerpt"] for e in evidences):
        reasons.append("見出しを含まない用例がある")
    if not str(result.get("definition", "")).strip():
        reasons.append("定義が空")
    return reasons


def pending_headwords(session: Session) -> set[str]:
    """未処理の提案に入っている語。取り込みを繰り返しても同じ提案を積まないため。"""
    return {
        json.loads(payload)["headword"]
        for payload in session.scalars(
            select(Proposal.payload_json).where(
                Proposal.status == "pending", Proposal.proposal_type == "sense"
            )
        )
    }


def _live_sense(session: Session, headword: str) -> Sense | None:
    return session.scalars(
        select(Sense)
        .join(Term)
        .where(
            Term.headword == headword,
            Term.status != "archived",
            Sense.status.not_in(("rejected",)),
        )
        .order_by(Sense.created_at)
    ).first()


def _add_to_existing(
    session: Session, sense: Sense, evidences: list[dict[str, Any]], rules: AdoptionRules
) -> int:
    room = rules.max_evidences_per_sense - len(sense.evidences)
    have = {(e.source_ref, e.excerpt) for e in sense.evidences}
    fresh = [e for e in evidences if (e["source_ref"], e["excerpt"]) not in have][: max(0, room)]
    if not fresh:
        return 0
    p = add_proposal(
        session,
        proposal_type="evidence",
        payload={"headword": sense.term.headword, "sense_id": sense.id, "evidences": fresh},
        model_name="statistics",
        prompt_version="evidence-v1",
        score=None,
    )
    p.decision_note = "登録済みの語に、まだ無い用例を足す（定義は変えない）"
    session.flush()
    accept(session, p.id, reviewer=AUTO, reason="自動判定：用例を追加")
    return len(fresh)


def propose_senses(
    session: Session,
    llm: LlmPort,
    candidates: list[dict[str, str]],
    docs: list[MaskedDocument],
    *,
    limit: int = 20,
    rules: AdoptionRules | None = None,
    send_masker: Masker | None = None,
) -> int:
    """propose_and_adopt の件数だけを返す版（新しく提案した語の数）。"""
    return propose_and_adopt(
        session, llm, candidates, docs, limit=limit, rules=rules, send_masker=send_masker
    ).proposed


def propose_and_adopt(
    session: Session,
    llm: LlmPort,
    candidates: list[dict[str, str]],
    docs: list[MaskedDocument],
    *,
    limit: int = 20,
    rules: AdoptionRules | None = None,
    send_masker: Masker | None = None,
) -> Outcome:
    """候補語を1つずつ判定する。登録済みなら用例を足し、新しい語は自動採用か保留にする。

    send_masker は LLM へ送る文にだけかける追加のマスキング（config/llm_send_masking.yaml）。
    DB に残す用例は変えない。モック以外の LLM へは、これを通さずに送らせない。
    """
    rules = rules or AdoptionRules()
    out = Outcome()
    is_mock = model_name(llm) == MOCK_MODEL_NAME
    if not is_mock and send_masker is None:
        raise RuntimeError("外部の LLM へは、送信用のマスキング（send_masker）を通さずに送らない")
    top_score = max((float(c["tfidf"]) for c in candidates), default=1.0) or 1.0
    pending = pending_headwords(session)
    for cand in candidates[:limit]:
        word = cand["surface"]
        if word in pending:
            continue
        existing = _live_sense(session, word)
        evidences = collect_evidences(
            word, docs, rules.max_evidences_per_sense if existing else MAX_EVIDENCES
        )
        # 用例の無い定義は保存できないので、そもそも判定に回さない
        if not evidences:
            continue
        if existing is not None:
            out.evidence_added += _add_to_existing(session, existing, evidences, rules)
            continue
        if session.scalars(select(Term).where(Term.headword == word)).first() is not None:
            continue  # アーカイブ済みの語は、取り込みで生き返らせない
        sent = [send_masker.mask(e["excerpt"]).text if send_masker else e["excerpt"] for e in evidences]
        prompt = build_prompt(word, sent)
        try:
            result = llm.complete_json(prompt, SENSE_SCHEMA)
        except Exception as e:  # LLM が失敗しても取り込み全体は止めず、その語だけ保留にする
            result = {"definition": "", "context_tag": "その他", "confidence": 0, "error": str(e)}
        verify: dict[str, Any] | None = None
        if not is_mock and not result.get("error") and str(result.get("definition", "")).strip():
            # 草案を作らせた呼び出しとは別に、定義と用例だけを見直させる（正誤判定の二段構え）
            try:
                verify = llm.complete_json(
                    build_verify_prompt(word, str(result["definition"]), sent), VERIFY_SCHEMA
                )
            except Exception as e:
                verify = {"supported": None, "reason": f"検証の呼び出しに失敗: {e}"}
        p = add_proposal(
            session,
            proposal_type="sense",
            payload={
                "headword": word,
                "definition": result.get("definition", ""),
                "context_tag": result.get("context_tag"),
                "confidence": result.get("confidence"),
                "evidences": evidences,
                "verification": None
                if verify is None
                else {"supported": verify.get("supported"), "reason": verify.get("reason")},
            },
            model_name=model_name(llm),
            prompt_version=PROMPT_VERSION,
            score=round(float(cand["tfidf"]) / top_score, 4),
        )
        out.proposed += 1
        pending.add(word)
        reasons = judge(result, evidences, word, is_mock, rules)
        if "error" in result:
            reasons.insert(0, f"LLM の呼び出しに失敗: {result['error']}")
        if verify is not None:
            if verify.get("supported") is False:
                detail = str(verify.get("reason") or "").strip()
                reasons.append("独立した検証で用例が定義を支えていないと判定" + (f"（{detail}）" if detail else ""))
            elif verify.get("supported") is None:
                reasons.append(str(verify.get("reason") or "検証に失敗"))
        session.flush()
        if reasons:
            p.decision_note = "保留：" + " / ".join(reasons)
            out.held += 1
        else:
            p.decision_note = "自動採用：用例・出典・確からしさの条件をすべて満たした"
            accept(session, p.id, reviewer=AUTO, reason="自動判定：新しい語を採用", adopted_by="auto")
            out.auto_adopted += 1
    session.flush()
    return out


def propose_relations(
    session: Session, pairs: list[dict[str, str]], headwords: set[str], *, limit: int = 20
) -> int:
    """共起の強いペアを「関連」として提案する。両端が語義の提案に入っている語だけ。"""
    made = 0
    for p in pairs:
        if made >= limit:
            break
        if p["a"] in headwords and p["b"] in headwords:
            add_proposal(
                session,
                proposal_type="relation",
                payload={
                    "from_headword": p["a"],
                    "to_headword": p["b"],
                    "relation_type": "related",
                    "method": "cooccurrence",
                    "score": float(p["thread_pmi"]),
                },
                model_name="statistics",
                prompt_version="cooccurrence-v0",
                score=float(p["thread_pmi"]),
            )
            made += 1
    return made


def revise_flagged(
    session: Session,
    llm: LlmPort,
    *,
    limit: int = 5,
    send_masker: Masker | None = None,
) -> int:
    """自己改修。「修正が必要」の評価が付いた語義の定義を書き直させ、改稿案を提案キューに積む。

    採用は人の確認を待つ（自動採用にしない）。元の語義は消さずに残るので、
    採用すると同じ見出しに新しい語義が1つ足り、評価は別々に付く。
    同じ語で未処理の提案があるときは積まない（取り込みと改稿の二重申請を防ぐ）。
    """
    is_mock = model_name(llm) == MOCK_MODEL_NAME
    if not is_mock and send_masker is None:
        raise RuntimeError("外部の LLM へは、送信用のマスキング（send_masker）を通さずに送らない")
    pending = pending_headwords(session)
    made = 0
    for item in review_queue(session, "needs_fix"):
        if made >= limit:
            break
        sense = item.sense
        word = sense.term.headword
        if word in pending:
            continue
        excerpts = [e.excerpt for e in sense.evidences]
        comments = [c.comment for c in item.summary.comments if c.comment][:5]
        to_send = excerpts + [sense.definition]
        sent = [send_masker.mask(t).text if send_masker else t for t in to_send]
        prompt = build_revise_prompt(word, sent[-1], comments, sent[:-1])
        try:
            result = llm.complete_json(prompt, REVISE_SCHEMA)
        except Exception:  # 1語の失敗で全体を止めない。次の語へ
            continue
        definition = str(result.get("definition", "")).strip()
        if not definition:
            continue
        evidences = [
            {
                "source_type": e.source_type,
                "source_ref": e.source_ref,
                "excerpt": e.excerpt,
                "occurred_at": e.occurred_at.isoformat() if e.occurred_at else None,
                "masked": e.masked,
            }
            for e in sense.evidences
        ]
        p = add_proposal(
            session,
            proposal_type="sense",
            payload={
                "headword": word,
                "definition": definition,
                "context_tag": result.get("context_tag") or sense.context_tag,
                "confidence": None,
                "evidences": evidences,
                "revises_sense_id": sense.id,
                "revises_revision": sense.revision_number,
            },
            model_name=model_name(llm),
            prompt_version=REVISE_PROMPT_VERSION,
            score=None,
        )
        note = str(result.get("note", "")).strip()
        p.decision_note = (
            f"自己改修：版{sense.revision_number}への「修正が必要」の評価を受けた改稿案"
            + (f"。{note}" if note else "")
            + "。元の語義は残る"
        )
        session.flush()
        pending.add(word)
        made += 1
    return made
