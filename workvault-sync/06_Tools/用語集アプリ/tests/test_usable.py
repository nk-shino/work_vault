"""実際に使うための機能：資料の取り込み・手動登録・用語情報の編集・関連語の追加・CSV出力。"""

from __future__ import annotations

import csv
import io
import os
from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient
from helpers import accepted_sense
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from glossary.adapters.llm.mock_adapter import MOCK_MODEL_NAME, MockLlmAdapter
from glossary.adapters.source.export_file_adapter import ExportFileAdapter
from glossary.db.models import Evidence, Proposal, Sense, Term
from glossary.domain import proposals
from glossary.preprocess.cleaner import Cleaner
from glossary.preprocess.masking import Masker
from glossary.preprocess.pipeline import preprocess
from glossary.propose import propose_senses
from glossary.web.app import create_app

ROOT = Path(__file__).resolve().parents[1]
ALL = (datetime(1900, 1, 1), datetime(2999, 1, 1))


# ---- 資料（.md / .txt）の取り込み ----


def test_notes_are_read_recursively_and_hidden_dirs_skipped(tmp_path: Path) -> None:
    (tmp_path / "09_引継ぎ").mkdir()
    (tmp_path / "09_引継ぎ" / "手順.md").write_text("# 手順\n星読み台帳を確認する。", encoding="utf-8")
    (tmp_path / "メモ.txt").write_bytes("竜舎の点検。".encode("cp932"))
    (tmp_path / ".obsidian").mkdir()
    (tmp_path / ".obsidian" / "設定.md").write_text("読まない", encoding="utf-8")
    docs = list(ExportFileAdapter(tmp_path).fetch_documents(*ALL))
    refs = sorted(d.source_ref for d in docs)
    assert refs == ["doc:09_引継ぎ/手順.md", "doc:メモ.txt"]
    assert all(d.occurred_at.tzinfo for d in docs)


def test_mail_cleaning_is_not_applied_to_notes(tmp_path: Path) -> None:
    # メール向けの「〜書きました」で以降を捨てるルールが、資料の本文を切らないこと
    (tmp_path / "a.md").write_text("前任者が書きました。\n星読み台帳の手順。", encoding="utf-8")
    cfg = ROOT / "config"
    docs, _ = preprocess(
        ExportFileAdapter(tmp_path),
        Cleaner.from_yaml(cfg / "cleaning_rules.yaml"),
        Masker.from_yaml(cfg / "masking_rules.yaml"),
        *ALL,
    )
    assert "星読み台帳の手順" in docs[0].text


def test_evidence_from_notes_is_marked_doc(db: Session) -> None:
    from glossary.preprocess.pipeline import MaskedDocument

    doc = MaskedDocument("doc:a.md", datetime(2031, 4, 1).astimezone(), "doc:a.md", "卵温計を交換する。")
    propose_senses(db, MockLlmAdapter(), [{"surface": "卵温計", "tfidf": "1"}], [doc])
    p = db.scalars(select(Proposal)).one()
    assert '"source_type": "doc"' in p.payload_json


def test_known_headwords_are_not_proposed_again(db: Session) -> None:
    accepted_sense(db, "卵温計")
    from glossary.preprocess.pipeline import MaskedDocument

    doc = MaskedDocument("t", datetime(2031, 4, 1).astimezone(), "eml:1", "卵温計と竜舎。")
    cands = [{"surface": "卵温計", "tfidf": "2"}, {"surface": "竜舎", "tfidf": "1"}]
    assert propose_senses(db, MockLlmAdapter(), cands, [doc]) == 1
    # もう一度流しても、未処理の提案に入っている語は積まない
    assert propose_senses(db, MockLlmAdapter(), cands, [doc]) == 0


# ---- 画面 ----


def client(db_url: str) -> TestClient:
    return TestClient(create_app(db_url))


def test_manual_registration(db_url: str, factory: sessionmaker[Session]) -> None:
    c = client(db_url)
    form = {"headword": "星読み台帳", "definition": "月に一度の校正結果を残す帳簿。",
            "excerpt": "星読み台帳にMGKの結果を記入する。", "source_ref": "引継ぎ資料 p.3",
            "abbreviation": "HYD"}  # fmt: skip
    r = c.post("/new", data=form, follow_redirects=False)
    assert r.status_code == 303
    detail = c.get(r.headers["location"]).text
    assert "月に一度の校正結果を残す帳簿。" in detail and "引継ぎ資料 p.3" in detail
    # 同じ見出しでもう一度登録すると、2つ目の語義になる
    c.post("/new", data=form | {"definition": "別の意味。", "excerpt": "別の用例。"})
    with factory() as db:
        term = db.scalars(select(Term).where(Term.headword == "星読み台帳")).one()
        senses = db.scalars(select(Sense).where(Sense.term_id == term.id)).all()
        assert term.abbreviation == "HYD"
        assert len(senses) == 2 and {s.source_type for s in senses} == {"human"}
        ev = db.scalars(select(Evidence)).first()
        assert ev is not None and ev.source_type == "manual" and ev.masked is False


def test_manual_registration_requires_example(db_url: str) -> None:
    r = client(db_url).post("/new", data={"headword": "竜舎", "definition": "定義", "excerpt": ""})
    assert r.status_code == 400 and "用例" in r.text


def test_mock_draft_cannot_be_accepted_as_is(db_url: str, factory: sessionmaker[Session]) -> None:
    with factory() as db:
        p = proposals.add_proposal(
            db, proposal_type="sense",
            payload={"headword": "竜舎", "definition": "【モック草案】…", "evidences": [
                {"source_type": "mail", "source_ref": "eml:1", "excerpt": "竜舎の点検。",
                 "occurred_at": None, "masked": True}]},
            model_name=MOCK_MODEL_NAME, prompt_version="t", score=1.0,
        )  # fmt: skip
        db.commit()
        pid = p.id
    c = client(db_url)
    assert c.post(f"/proposals/{pid}/accept").status_code == 400
    assert "【モック草案】" not in c.get(f"/proposals/{pid}/edit").text
    empty = c.post(f"/proposals/{pid}/edit", data={"definition": "", "change_reason": "r"})
    assert empty.status_code == 400
    ok = c.post(f"/proposals/{pid}/edit", data={"definition": "竜を飼う建物。", "change_reason": "定義を記入"},
                follow_redirects=False)  # fmt: skip
    assert ok.status_code == 303


def test_term_edit_and_conflict(db_url: str, factory: sessionmaker[Session]) -> None:
    with factory() as db:
        term_id = accepted_sense(db, "竜舎").term_id
    c = client(db_url)
    form = {"revision_number": "2", "headword": "竜舎", "reading": "りゅうしゃ",
            "english": "", "abbreviation": "", "status": "active", "change_reason": "読みを追加"}  # fmt: skip
    assert c.post(f"/terms/{term_id}/edit", data=form, follow_redirects=False).status_code == 303
    assert "りゅうしゃ" in c.get(f"/terms/{term_id}").text
    stale = c.post(f"/terms/{term_id}/edit", data=form | {"reading": "古い画面"})
    assert stale.status_code == 409
    archived = c.post(f"/terms/{term_id}/edit", data=form | {"revision_number": "3", "status": "archived"})
    assert archived.status_code == 400


def test_add_relation_from_detail(db_url: str, factory: sessionmaker[Session]) -> None:
    with factory() as db:
        term_id = accepted_sense(db, "竜舎").term_id
        accepted_sense(db, "竜車")
    c = client(db_url)
    r = c.post(f"/terms/{term_id}/relations", data={"relation_type": "confused_with", "other": "竜車"},
               follow_redirects=False)  # fmt: skip
    assert r.status_code == 303
    assert "混同注意" in c.get(f"/terms/{term_id}").text
    missing = c.post(f"/terms/{term_id}/relations", data={"relation_type": "related", "other": "無い語"})
    assert missing.status_code == 400


def test_csv_export(db_url: str, factory: sessionmaker[Session]) -> None:
    with factory() as db:
        accepted_sense(db, "竜舎", "竜を飼う建物。")
        gone = accepted_sense(db, "古い語").term
        from glossary.domain import review

        review.archive_term(db, gone.id, expected_revision=gone.revision_number,
                            editor_name=None, change_reason="使われなくなった")  # fmt: skip
        db.commit()
    r = client(db_url).get("/export.csv")
    assert r.status_code == 200
    raw = r.content.decode("utf-8")
    assert raw.startswith("﻿")  # Excel で開いて化けないように
    rows = list(csv.reader(io.StringIO(raw.lstrip("﻿"))))
    assert rows[0][0] == "見出し"
    assert [row[0] for row in rows[1:]] == ["竜舎"]  # アーカイブ済みは出さない
    assert rows[1][6] == "竜を飼う建物。"


def test_nav_links_exist(db_url: str) -> None:
    html = client(db_url).get("/terms").text
    assert 'href="/new"' in html and 'href="/export.csv"' in html
    assert os.environ["LLM_BACKEND"] == "mock"
