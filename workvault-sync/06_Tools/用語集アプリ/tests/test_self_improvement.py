"""正誤判定の検証パスと自己改修。2026-10-20 の方針（LiteLLM での自動取込・評価ループ）の分。"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import pytest
from conftest import ROOT
from sqlalchemy import select
from sqlalchemy.orm import Session

from glossary.adapters.llm.mock_adapter import MockLlmAdapter
from glossary.db.models import Proposal, Sense, Term
from glossary.domain import evaluations
from glossary.preprocess.masking import Masker
from glossary.preprocess.pipeline import MaskedDocument
from glossary.propose import propose_and_adopt, revise_flagged

AT = datetime(2031, 4, 1, 9).astimezone()
SEND = Masker.from_yaml(ROOT / "config" / "llm_send_masking.yaml")
CAND = [{"surface": "竜舎", "tfidf": "1"}]


def docs(*pairs: tuple[str, str]) -> list[MaskedDocument]:
    return [MaskedDocument(ref, AT, ref, body) for ref, body in pairs]


TWO_SOURCES = docs(("eml:1", "竜舎の点検をした。"), ("doc:a.md", "竜舎は東棟にある。"))


class FakeDraftLlm:
    """草案と検証で別の答えを返す仮の LLM。検証の呼び出しは「裏付けられるか」で見分ける。"""

    model_name = "fake-llm"

    def __init__(self, verify_supported: bool = True, verify_fail: bool = False) -> None:
        self.verify_supported, self.verify_fail = verify_supported, verify_fail
        self.prompts: list[str] = []

    def complete_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        self.prompts.append(prompt)
        if "裏付けられるかを確かめて" in prompt:
            if self.verify_fail:
                raise RuntimeError("検証で接続できない")
            return {"supported": self.verify_supported, "reason": "用例に定義の後半の根拠が無い"}
        return {"definition": "竜を飼う建物。", "context_tag": "設備",
                "confidence": 0.9, "supported": True}  # fmt: skip

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] for _ in texts]


class FakeReviseLlm:
    model_name = "fake-llm"

    def __init__(self, definition: str = "東棟にある竜を飼う建物。") -> None:
        self.definition = definition
        self.prompts: list[str] = []

    def complete_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        self.prompts.append(prompt)
        return {"definition": self.definition, "context_tag": "設備", "note": "推測を除いた"}

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] for _ in texts]


# ---- 正誤判定（草案とは別の呼び出しで見直す） ----


def test_verify_rejection_holds_new_term(db: Session) -> None:
    out = propose_and_adopt(db, FakeDraftLlm(verify_supported=False), CAND, TWO_SOURCES,
                            send_masker=SEND)  # fmt: skip
    db.commit()
    assert (out.auto_adopted, out.held) == (0, 1)
    p = db.scalars(select(Proposal)).one()
    assert "独立した検証" in (p.decision_note or "")
    assert "用例に定義の後半の根拠が無い" in (p.decision_note or "")
    payload = json.loads(p.payload_json)
    assert payload["verification"] == {"supported": False, "reason": "用例に定義の後半の根拠が無い"}


def test_verify_failure_holds_new_term(db: Session) -> None:
    out = propose_and_adopt(db, FakeDraftLlm(verify_fail=True), CAND, TWO_SOURCES,
                            send_masker=SEND)  # fmt: skip
    db.commit()
    assert (out.auto_adopted, out.held) == (0, 1)
    p = db.scalars(select(Proposal)).one()
    assert "検証の呼び出しに失敗" in (p.decision_note or "")


def test_verify_pass_allows_auto_adoption(db: Session) -> None:
    llm = FakeDraftLlm()
    out = propose_and_adopt(db, llm, CAND, TWO_SOURCES, send_masker=SEND)
    db.commit()
    assert (out.auto_adopted, out.held) == (1, 0)
    assert len(llm.prompts) == 2  # 草案の呼び出しと、検証の呼び出し


def test_mock_skips_verify(db: Session) -> None:
    out = propose_and_adopt(db, MockLlmAdapter(), CAND, TWO_SOURCES, send_masker=SEND)
    db.commit()
    assert (out.auto_adopted, out.held) == (0, 1)
    p = db.scalars(select(Proposal)).one()
    assert json.loads(p.payload_json)["verification"] is None


def test_verify_result_is_visible_in_proposals_ui(db_url: str, db: Session) -> None:
    from fastapi.testclient import TestClient

    from glossary.web.app import create_app

    propose_and_adopt(db, FakeDraftLlm(verify_supported=False), CAND, TWO_SOURCES,
                      send_masker=SEND)  # fmt: skip
    db.commit()
    with TestClient(create_app(db_url)) as c:
        html = c.get("/proposals").text
    assert "独立検証：裏付けなし" in html
    assert "用例に定義の後半の根拠が無い" in html


# ---- 自己改修（「修正が必要」の評価から改稿案を作る） ----


def needs_fix_sense(db: Session) -> Any:
    from helpers import accepted_sense

    sense = accepted_sense(db, "竜舎", "架空の定義。")
    evaluations.evaluate(
        db, sense.id, seen_revision=sense.revision_number,
        accuracy="needs_fix", comment="用例と合っていない",  # fmt: skip
    )
    db.commit()
    return sense


def test_revise_queues_new_proposal_for_human_review(db: Session) -> None:
    sense = needs_fix_sense(db)
    llm = FakeReviseLlm()
    made = revise_flagged(db, llm, send_masker=SEND)
    db.commit()
    assert made == 1
    p = db.scalars(select(Proposal).where(Proposal.status == "pending")).one()
    assert p.model_name == "fake-llm" and p.status == "pending"
    payload = json.loads(p.payload_json)
    assert payload["headword"] == "竜舎"
    assert payload["revises_sense_id"] == sense.id
    assert payload["definition"] == "東棟にある竜を飼う建物。"
    assert "自己改修" in (p.decision_note or "") and "推測を除いた" in (p.decision_note or "")
    # 指摘と現在の定義がプロンプトに載る
    sent = "\n".join(llm.prompts)
    assert "用例と合っていない" in sent and "架空の定義。" in sent


def test_revise_never_auto_adopts_and_dedupes(db: Session) -> None:
    needs_fix_sense(db)
    first = revise_flagged(db, FakeReviseLlm(), send_masker=SEND)
    second = revise_flagged(db, FakeReviseLlm(), send_masker=SEND)
    db.commit()
    assert (first, second) == (1, 0)
    assert len(db.scalars(select(Sense)).all()) == 1  # 採用は人の確認を待つので語義は増えない


def test_revise_limit(db: Session) -> None:
    from helpers import accepted_sense

    for word in ("竜舎", "竜車", "浮遊石"):
        sense = accepted_sense(db, word, "架空の定義。")
        evaluations.evaluate(db, sense.id, seen_revision=sense.revision_number, accuracy="needs_fix")
    db.commit()
    made = revise_flagged(db, FakeReviseLlm(), limit=2, send_masker=SEND)
    db.commit()
    assert made == 2


def test_revise_requires_send_masker(db: Session) -> None:
    needs_fix_sense(db)
    with pytest.raises(RuntimeError, match="送信用のマスキング"):
        revise_flagged(db, FakeReviseLlm())


def test_revise_sends_masked_prompts(db: Session) -> None:
    from glossary.domain import proposals  # noqa: I001
    from helpers import evidence

    p = proposals.add_proposal(
        db,
        proposal_type="sense",
        payload={
            "headword": "竜舎",
            "definition": "架空の定義。",
            "context_tag": "その他",
            "confidence": 0.5,
            "evidences": [evidence(r"竜舎の手順は \\nas-01\共有\竜舎 にある。", "eml:0002.eml")],
        },
        model_name="mock-llm",
        prompt_version="test",
        score=1.0,
    )
    db.flush()
    proposals.accept(db, p.id, reviewer="テスト")
    db.commit()
    sense = db.scalars(select(Sense).join(Term).where(Sense.definition == "架空の定義。")).one()
    evaluations.evaluate(db, sense.id, seen_revision=sense.revision_number, accuracy="needs_fix")
    db.commit()
    llm = FakeReviseLlm()
    revise_flagged(db, llm, send_masker=SEND)
    db.commit()
    assert "\\nas-01" not in "\n".join(llm.prompts)
    assert "<PATH>" in "\n".join(llm.prompts)
