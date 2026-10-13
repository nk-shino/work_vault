"""自動判定（用例の追加・自動採用・保留）と、登録後の評価。2026-09-28 の設計方針の分。"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from conftest import ROOT
from fastapi.testclient import TestClient
from helpers import accepted_sense
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session, sessionmaker

from glossary.adapters.llm.litellm_adapter import LlmError, parse_chat_json, parse_embeddings
from glossary.adapters.llm.mock_adapter import MockLlmAdapter
from glossary.db.models import Evaluation, Proposal, Sense
from glossary.domain import evaluations, review
from glossary.domain.errors import ValidationFailed
from glossary.preprocess.masking import Masker
from glossary.preprocess.pipeline import MaskedDocument
from glossary.propose import SENSE_SCHEMA, AdoptionRules, propose_and_adopt
from glossary.web.app import create_app

AT = datetime(2031, 4, 1, 9).astimezone()


class FakeLlm:
    """本物の LLM の代わり。決まった答えを返すだけで、外へは出ない。"""

    model_name = "fake-llm"

    def __init__(self, confidence: float = 0.9, supported: bool = True, fail: bool = False) -> None:
        self.confidence, self.supported, self.fail = confidence, supported, fail
        self.prompts: list[str] = []  # 外へ送られるはずだった文。送信前マスキングの確認に使う

    def complete_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        self.prompts.append(prompt)
        if self.fail:
            raise RuntimeError("接続できない")
        return {"definition": "竜を飼う建物。", "context_tag": "設備",
                "confidence": self.confidence, "supported": self.supported}  # fmt: skip

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.0] for _ in texts]


def docs(*pairs: tuple[str, str]) -> list[MaskedDocument]:
    return [MaskedDocument(ref, AT, ref, body) for ref, body in pairs]


SEND = Masker.from_yaml(ROOT / "config" / "llm_send_masking.yaml")


def run(db: Session, llm: Any, cands: Any, texts: Any, **kw: Any) -> Any:
    return propose_and_adopt(db, llm, cands, texts, send_masker=SEND, **kw)


TWO_SOURCES = docs(("eml:1", "竜舎の点検をした。"), ("doc:a.md", "竜舎は東棟にある。"))
CAND = [{"surface": "竜舎", "tfidf": "1"}]


# ---- 自動判定 ----


def test_new_term_auto_adopted_when_all_conditions_met(db: Session) -> None:
    out = run(db, FakeLlm(), CAND, TWO_SOURCES)
    db.commit()
    assert (out.auto_adopted, out.held) == (1, 0)
    sense = db.scalars(select(Sense)).one()
    assert sense.adopted_by == "auto" and sense.status == "confirmed"
    p = db.scalars(select(Proposal)).one()
    assert p.status == "accepted" and p.reviewed_by == "自動判定"
    assert "自動採用" in (p.decision_note or "")


@pytest.mark.parametrize(
    "llm, texts, reason",
    [
        (FakeLlm(), docs(("eml:1", "竜舎の点検をした。"), ("eml:1", "竜舎は東棟にある。")), "出典が 1 種類"),
        (FakeLlm(confidence=0.3), TWO_SOURCES, "確からしさ"),
        (FakeLlm(supported=False), TWO_SOURCES, "支えている"),
        (MockLlmAdapter(), TWO_SOURCES, "モック"),
        (FakeLlm(fail=True), TWO_SOURCES, "LLM の呼び出しに失敗"),
    ],
)
def test_new_term_held_with_reason(db: Session, llm: Any, texts: list[MaskedDocument], reason: str) -> None:
    out = run(db, llm, CAND, texts)
    db.commit()
    assert (out.auto_adopted, out.held) == (0, 1)
    p = db.scalars(select(Proposal)).one()
    assert p.status == "pending" and reason in (p.decision_note or "")
    assert db.scalars(select(Sense)).first() is None


def test_rules_can_turn_off_auto_adoption(db: Session, tmp_path: Path) -> None:
    f = tmp_path / "adoption.yaml"
    f.write_text("auto_adopt_new_terms: false\nmin_sources: 1\n", encoding="utf-8")
    rules = AdoptionRules.from_yaml(f)
    assert rules.min_sources == 1 and rules.min_evidences == 2  # 書いていない項目は既定値
    out = run(db, FakeLlm(), CAND, TWO_SOURCES, rules=rules)
    assert out.held == 1


def test_existing_term_gets_new_evidence_not_new_definition(db: Session) -> None:
    sense = accepted_sense(db, "竜舎", "人が書いた定義。")
    out = run(db, FakeLlm(), CAND, TWO_SOURCES)
    db.commit()
    assert out.evidence_added == 2 and out.proposed == 0
    db.refresh(sense)
    assert sense.definition == "人が書いた定義。"  # 人が書いた定義は上書きしない
    assert sense.revision_number == 1  # 用例を足しても版は上がらない（評価が無効にならない）
    assert len(sense.evidences) == 3
    # 取り込みを繰り返しても同じ用例は増えない
    again = run(db, FakeLlm(), CAND, TWO_SOURCES)
    assert again.evidence_added == 0


def test_evidence_cap(db: Session) -> None:
    accepted_sense(db, "竜舎")
    many = docs(*[(f"eml:{i}", f"竜舎の記録{i}。") for i in range(20)])
    out = run(db, FakeLlm(), CAND, many, rules=AdoptionRules(max_evidences_per_sense=5))
    assert out.evidence_added == 4  # 既存の1件と合わせて上限5件


def test_archived_term_is_not_revived(db: Session) -> None:
    term = accepted_sense(db, "竜舎").term
    review.archive_term(db, term.id, expected_revision=term.revision_number,
                        editor_name=None, change_reason="使わない")  # fmt: skip
    db.commit()
    out = run(db, FakeLlm(), CAND, TWO_SOURCES)
    assert out.proposed == 0 and out.evidence_added == 0


def test_rerun_does_not_duplicate_held_proposals(db: Session) -> None:
    run(db, MockLlmAdapter(), CAND, TWO_SOURCES)
    again = run(db, MockLlmAdapter(), CAND, TWO_SOURCES)
    assert again.proposed == 0


# ---- 評価 ----


def test_evaluation_is_tied_to_revision(db: Session) -> None:
    s = accepted_sense(db, "竜舎")
    evaluations.evaluate(db, s.id, seen_revision=1, accuracy="needs_fix", comment="範囲が広すぎる")
    evaluations.evaluate(db, s.id, seen_revision=1, usefulness="useful")
    db.commit()
    sm = evaluations.summaries(db, [s])[s.id]
    assert sm.needs_fix and sm.usefulness["useful"] == 1
    # 定義を直すと、旧版への評価は今の版の評価として数えない
    review.edit_sense(db, s.id, expected_revision=1, changes={"definition": "直した定義。"},
                      editor_name=None, change_reason="評価を受けて修正")  # fmt: skip
    db.commit()
    sm = evaluations.summaries(db, [s])[s.id]
    assert sm.unevaluated and sm.older == 2
    # 古い画面から押した評価は受け付けない
    with pytest.raises(ValidationFailed, match="更新されました"):
        evaluations.evaluate(db, s.id, seen_revision=1, accuracy="correct")


def test_evaluation_does_not_change_definition(db: Session) -> None:
    s = accepted_sense(db, "竜舎", "元の定義。")
    evaluations.evaluate(db, s.id, seen_revision=1, accuracy="needs_fix")
    db.commit()
    db.refresh(s)
    assert s.definition == "元の定義。" and s.revision_number == 1


def test_evaluations_are_append_only(db: Session) -> None:
    s = accepted_sense(db, "竜舎")
    evaluations.evaluate(db, s.id, seen_revision=1, accuracy="correct")
    db.commit()
    for sql in ("UPDATE evaluations SET accuracy = 'needs_fix'", "DELETE FROM evaluations"):
        with pytest.raises((IntegrityError, OperationalError)):
            db.execute(text(sql))
        db.rollback()


def test_review_queue_kinds(db: Session) -> None:
    a = accepted_sense(db, "竜舎")
    b = accepted_sense(db, "竜車")
    accepted_sense(db, "浮遊石")
    evaluations.evaluate(db, a.id, seen_revision=1, accuracy="correct")
    evaluations.evaluate(db, a.id, seen_revision=1, accuracy="needs_fix")
    evaluations.evaluate(db, b.id, seen_revision=1, usefulness="not_useful")
    db.commit()
    heads = {k: [i.term.headword for i in evaluations.review_queue(db, k)] for k in evaluations.REVIEW_KINDS}
    assert heads["needs_fix"] == ["竜舎"] and heads["split"] == ["竜舎"]
    assert heads["not_useful"] == ["竜車"] and heads["unevaluated"] == ["浮遊石"]
    assert heads["auto_unevaluated"] == []  # 3つとも人が採用したもの


def test_evaluate_from_screen(db_url: str, factory: sessionmaker[Session]) -> None:
    with factory() as db:
        s = accepted_sense(db, "竜舎")
        term_id, sid = s.term_id, s.id
    c = TestClient(create_app(db_url))
    page = c.get(f"/terms/{term_id}").text
    assert "まだ評価はありません" in page and 'value="needs_fix"' in page
    r = c.post(f"/senses/{sid}/evaluate",
               data={"revision_number": "1", "accuracy": "needs_fix", "comment": "範囲が違う"},
               follow_redirects=False)  # fmt: skip
    assert r.status_code == 303
    page = c.get(f"/terms/{term_id}").text
    assert "修正が必要 1 回" in page and "人数ではありません" in page and "範囲が違う" in page
    assert "竜舎" in c.get("/review?kind=needs_fix").text
    with factory() as db:
        assert db.scalars(select(Evaluation)).one().sense_revision == 1


def test_cross_site_post_is_rejected(db_url: str, factory: sessionmaker[Session]) -> None:
    with factory() as db:
        sid = accepted_sense(db, "竜舎").id
    c = TestClient(create_app(db_url))
    data = {"revision_number": "1", "accuracy": "correct"}
    evil = c.post(f"/senses/{sid}/evaluate", data=data, headers={"Origin": "https://evil.example"})
    assert evil.status_code == 403
    same = c.post(f"/senses/{sid}/evaluate", data=data,
                  headers={"Origin": "http://testserver"}, follow_redirects=False)  # fmt: skip
    assert same.status_code == 303


# ---- マイグレーション ----


def test_upgrade_from_0001_keeps_data(tmp_path: Path) -> None:
    from alembic import command
    from alembic.config import Config

    db_file = tmp_path / "old.db"
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.attributes["database_url"] = f"sqlite:///{db_file.as_posix()}"
    command.upgrade(cfg, "0001")
    con = sqlite3.connect(db_file)
    con.execute("INSERT INTO proposals (id, proposal_type, payload_json, model_name, prompt_version,"
                " status, created_at) VALUES ('p1', 'sense', '{}', 'm', 'v', 'pending', '2031-01-01')")  # fmt: skip
    con.commit()
    con.close()
    command.upgrade(cfg, "head")
    con = sqlite3.connect(db_file)
    assert con.execute("SELECT id, decision_note FROM proposals").fetchall() == [("p1", None)]
    with pytest.raises(sqlite3.IntegrityError):  # 削除禁止のトリガーが付け直されている
        con.execute("DELETE FROM proposals")
    con.execute("INSERT INTO proposals (id, proposal_type, payload_json, model_name, prompt_version,"
                " status, created_at) VALUES ('p2', 'evidence', '{}', 'm', 'v', 'pending', '2031-01-01')")  # fmt: skip
    con.close()


# ---- LiteLLM の応答の解析（通信はしない） ----


def chat(content: str) -> dict[str, Any]:
    return {"choices": [{"message": {"content": content}}]}


def test_parse_chat_json() -> None:
    ok = '{"definition": "d", "context_tag": "設備", "confidence": 0.8, "supported": true}'
    assert parse_chat_json(chat(ok), SENSE_SCHEMA)["confidence"] == 0.8
    assert parse_chat_json(chat("```json\n" + ok + "\n```"), SENSE_SCHEMA)["definition"] == "d"
    for bad in ('{"definition": "d"}', "定義です", "[1, 2]"):
        with pytest.raises(LlmError):
            parse_chat_json(chat(bad), SENSE_SCHEMA)
    with pytest.raises(LlmError):
        parse_chat_json({"error": "x"}, SENSE_SCHEMA)


def test_parse_embeddings_orders_by_index() -> None:
    res = {"data": [{"index": 1, "embedding": [2.0]}, {"index": 0, "embedding": [1.0]}]}
    assert parse_embeddings(res, 2) == [[1.0], [2.0]]
    with pytest.raises(LlmError):
        parse_embeddings(res, 3)


def test_litellm_adapter_refuses_plain_http(monkeypatch: pytest.MonkeyPatch) -> None:
    from glossary.adapters.llm.litellm_adapter import LiteLlmAdapter

    for k, v in {"LITELLM_BASE_URL": "http://x.invalid", "LITELLM_API_KEY": "k",
                 "LITELLM_CHAT_MODEL": "m"}.items():  # fmt: skip
        monkeypatch.setenv(k, v)
    with pytest.raises(RuntimeError, match="https"):
        LiteLlmAdapter()  # 作るだけ。接続はしない
    monkeypatch.delenv("LITELLM_API_KEY")
    with pytest.raises(RuntimeError, match="環境変数"):
        LiteLlmAdapter()



# ---- LLM へ送る直前のマスキング（pending E 節の推奨案2） ----


def test_external_llm_requires_send_masking(db: Session) -> None:
    with pytest.raises(RuntimeError, match="送信用のマスキング"):
        propose_and_adopt(db, FakeLlm(), CAND, TWO_SOURCES)


def test_send_masking_hides_internal_info_but_db_keeps_it(db: Session) -> None:
    texts = docs(
        # 用例は語を含む1文だけを抜き出すので、社内の情報は同じ文に入れておく
        ("eml:1", r"竜舎の手順は \\nas-01\共有\竜舎 にあり、担当：雲居"),
        ("doc:a.md", "竜舎の点検は星見部長の承認が要る（https://example.invalid/ryusha）"),
    )
    llm = FakeLlm()
    run(db, llm, CAND, texts)
    db.commit()
    sent = "\n".join(llm.prompts)
    for secret in ("nas-01", "雲居", "星見", "example.invalid"):
        assert secret not in sent, secret
    assert "<PATH>" in sent and "<PERSON>" in sent and "<URL>" in sent
    # 用語集の DB には、今の方針どおり残る（社内の用語集としては必要な情報）
    stored = " ".join(e.excerpt for e in db.scalars(select(Sense)).one().evidences)
    for kept in ("nas-01", "雲居", "星見部長"):
        assert kept in stored, kept
