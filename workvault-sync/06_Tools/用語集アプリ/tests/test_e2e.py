"""fixtures の架空メールで、前処理 → 統計 → モックLLMの提案 → 採用 → レビューUI表示まで通す。"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from glossary.adapters.llm.mock_adapter import MockLlmAdapter
from glossary.adapters.source.export_file_adapter import ExportFileAdapter
from glossary.db.models import Proposal, Sense, Term
from glossary.domain import proposals
from glossary.preprocess.cleaner import Cleaner
from glossary.preprocess.masking import Masker
from glossary.preprocess.pipeline import load_jsonl, preprocess, save_jsonl
from glossary.propose import propose_relations, propose_senses
from glossary.stats.candidates import load_stopwords
from glossary.stats.extract import analyze, read_csv, write_candidates, write_pairs
from glossary.web.app import create_app

ROOT = Path(__file__).resolve().parents[1]
RAW_PATTERNS = re.compile(r"@example\.invalid|000-\d{4}-\d{4}|\d,\d{3}円|霧島|雲居|竜乃|星見|羽根田")


@pytest.fixture
def pipeline(tmp_path: Path, factory: sessionmaker[Session]) -> Path:
    cfg = ROOT / "config"
    docs, counts = preprocess(
        ExportFileAdapter(ROOT / "fixtures" / "mails"),
        Cleaner.from_yaml(cfg / "cleaning_rules.yaml"),
        Masker.from_yaml(cfg / "masking_rules.yaml"),
        datetime(1900, 1, 1),
        datetime(2999, 1, 1),
    )
    masked = tmp_path / "work" / "masked.jsonl"
    save_jsonl(docs, masked)
    rows, pairs = analyze(load_jsonl(masked), load_stopwords(cfg / "stopwords.txt"))
    write_candidates(rows, tmp_path / "out" / "candidates.csv")
    write_pairs(pairs, tmp_path / "out" / "cooccurrence.csv")
    cands = read_csv(tmp_path / "out" / "candidates.csv")
    with factory() as db:
        assert propose_senses(db, MockLlmAdapter(), cands, docs) > 0
        propose_relations(db, read_csv(tmp_path / "out" / "cooccurrence.csv"),
                          {c["surface"] for c in cands[:20]})  # fmt: skip
        db.commit()
    return tmp_path


def test_masked_output_has_no_raw_personal_data(pipeline: Path) -> None:
    for d in load_jsonl(pipeline / "work" / "masked.jsonl"):
        assert not RAW_PATTERNS.search(d.text), d.source_ref


def test_expected_terms_rank_high(pipeline: Path) -> None:
    top = [r["surface"] for r in read_csv(pipeline / "out" / "candidates.csv")[:15]]
    for word in ("竜車", "卵温計", "MGK", "スカイポスト", "ドラゴンミルク"):
        assert word in top


def test_review_ui_end_to_end(pipeline: Path, db_url: str, factory: sessionmaker[Session]) -> None:
    with factory() as db:
        pending = db.scalars(
            select(Proposal).where(Proposal.proposal_type == "sense").order_by(Proposal.score.desc())
        ).all()
        first_id = pending[0].id
        for p in pending[1:6]:
            proposals.accept(db, p.id, reviewer="テスト")
        db.commit()

    client = TestClient(create_app(db_url))

    # 提案キュー → 採用
    page = client.get("/proposals")
    assert page.status_code == 200 and "採用" in page.text
    # モックの定義文はそのまま採用できない。定義を書いて「修正して採用」する
    assert client.post(f"/proposals/{first_id}/accept").status_code == 400
    r = client.post(f"/proposals/{first_id}/edit",
                    data={"definition": "人が書いた定義。", "change_reason": "定義を記入"},
                    follow_redirects=False)  # fmt: skip
    assert r.status_code == 303

    # 用語一覧（検索条件は URL で再現できる）
    listing = client.get("/terms")
    assert listing.status_code == 200
    with factory() as db:
        term = db.scalars(select(Term).order_by(Term.headword)).first()
        assert term is not None
        sense = db.scalars(select(Sense).where(Sense.term_id == term.id)).one()
    found = client.get("/terms", params={"q": term.headword})
    assert term.headword in found.text
    assert "条件に合う用語がありません" in client.get("/terms", params={"q": "存在しない語"}).text

    # 詳細：用例と出典日時が出る
    detail = client.get(f"/terms/{term.id}")
    assert detail.status_code == 200
    assert "用例" in detail.text and "2031-" in detail.text

    # 編集：理由が無ければ保存しない
    form = {"revision_number": "1", "definition": "修正した定義", "status": "disputed",
            "context_tag": "", "scope_note": "", "editor_name": ""}  # fmt: skip
    assert client.post(f"/senses/{sense.id}/edit", data=form).status_code == 400
    ok = client.post(f"/senses/{sense.id}/edit", data=form | {"change_reason": "テスト"},
                     follow_redirects=False)  # fmt: skip
    assert ok.status_code == 303
    detail = client.get(f"/terms/{term.id}").text
    assert "係争中" in detail and "修正した定義" in detail

    # 同じ版1のまま保存しようとすると 409 で差分が出て、上書きされない
    stale = client.post(f"/senses/{sense.id}/edit",
                        data=form | {"definition": "古い画面からの保存", "change_reason": "r"})  # fmt: skip
    assert stale.status_code == 409
    assert "古い画面からの保存" in stale.text and "修正した定義" in stale.text
    assert "古い画面からの保存" not in client.get(f"/terms/{term.id}").text

    # 履歴と差分
    hist = client.get(f"/history/sense/{sense.id}")
    assert hist.status_code == 200 and "版 2" in hist.text and "修正した定義" in hist.text
    # 差分には変えた項目だけが出る（DB を往復した日時が別物に見えて混ざらない）
    latest = hist.text.split("版 2", 1)[1].split("版 1", 1)[0]
    assert "created_at" not in latest and "definition" in latest


def test_definition_is_escaped(db_url: str, factory: sessionmaker[Session]) -> None:
    from helpers import accepted_sense

    with factory() as db:
        term_id = accepted_sense(db, "架空語", "<script>alert(1)</script>").term_id
    html = TestClient(create_app(db_url)).get(f"/terms/{term_id}").text
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_confused_with_is_highlighted(db_url: str, factory: sessionmaker[Session]) -> None:
    from helpers import accepted_sense

    with factory() as db:
        a = accepted_sense(db, "竜舎")
        accepted_sense(db, "竜車")
        p = proposals.add_proposal(
            db, proposal_type="relation",
            payload={"from_headword": "竜舎", "to_headword": "竜車",
                     "relation_type": "confused_with", "method": "human"},
            model_name="human", prompt_version="t", score=None,
        )  # fmt: skip
        db.flush()
        proposals.accept(db, p.id, reviewer=None)
        db.commit()
    html = TestClient(create_app(db_url)).get(f"/terms/{a.term_id}").text
    assert "混同注意" in html and "竜車" in html


def test_empty_and_error_states(db_url: str) -> None:
    client = TestClient(create_app(db_url))
    assert "「用語を登録」から手で入れるか" in client.get("/terms").text
    assert "未処理の提案はありません" in client.get("/proposals").text
    missing = client.get("/terms/does-not-exist")
    assert missing.status_code == 404 and "処理できませんでした" in missing.text


def test_all_inputs_have_labels(pipeline: Path, db_url: str) -> None:
    with TestClient(create_app(db_url)) as c:
        pages = [c.get("/terms").text, c.get("/proposals").text]
    for html in pages:
        ids = re.findall(r'<(?:input|select|textarea)(?![^>]*type="hidden")[^>]*\bid="([^"]+)"', html)
        fields = re.findall(r'<(?:input|select|textarea)(?![^>]*type="hidden")[^>]*>', html)
        assert len(ids) == len(fields), "id の無い入力欄がある"
        # id が重複すると、ラベルもスクリプトも別の要素を掴む（処理中表示が絞り込み欄を隠した実例あり）
        all_ids = re.findall(r'\bid="([^"]+)"', html)
        assert len(all_ids) == len(set(all_ids)), "id が重複している"
        # 編集者の欄は置かない（誰でも編集でき、今は誰が直したかを残さない方針）
        assert 'name="editor_name"' not in html and 'name="reviewer"' not in html
        for i in ids:
            assert f'for="{i}"' in html, f"ラベルの無い入力欄: {i}"
