from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from glossary.adapters.source.export_file_adapter import ExportFileAdapter
from glossary.adapters.source.knowledge_api_adapter import KnowledgeApiAdapter

ROOT = Path(__file__).resolve().parents[1]
JST = timezone(timedelta(hours=9))
ALL = (datetime(1900, 1, 1), datetime(2999, 1, 1))


def test_reads_fixture_emls() -> None:
    docs = list(ExportFileAdapter(ROOT / "fixtures" / "mails").fetch_documents(*ALL))
    assert len(docs) == 50
    # 返信は References の先頭（最初のメール）でスレッドにまとまる
    assert docs[0].thread_id == docs[1].thread_id == "<fx-001-0@example.invalid>"
    assert docs[0].source_ref.startswith("eml:0001.eml#")
    assert docs[0].occurred_at.tzinfo is not None


def test_csv_utf8_bom_and_cp932(tmp_path: Path) -> None:
    header = "body,thread_id,occurred_at,source_ref\n"
    row = "竜舎の点検,t1,2031-04-01T09:00:00,csv:1\n"
    (tmp_path / "a.csv").write_text(header + row, encoding="utf-8-sig")
    (tmp_path / "b.csv").write_bytes((header + row.replace("csv:1", "csv:2")).encode("cp932"))
    docs = list(ExportFileAdapter(tmp_path).fetch_documents(*ALL))
    assert [d.body for d in docs] == ["竜舎の点検", "竜舎の点検"]
    # 時差の無い日時は日本時間とみなす
    assert docs[0].occurred_at == datetime(2031, 4, 1, 9, tzinfo=JST)


def test_jsonl_and_date_filter(tmp_path: Path) -> None:
    (tmp_path / "x.jsonl").write_text(
        '{"body": "古い", "thread_id": "t", "occurred_at": "2031-01-01T00:00:00+09:00", "source_ref": "j:1"}\n'
        '{"body": "新しい", "thread_id": "t", "occurred_at": "2031-06-01T00:00:00+09:00", "source_ref": "j:2"}\n',
        encoding="utf-8",
    )
    docs = list(
        ExportFileAdapter(tmp_path).fetch_documents(
            datetime(2031, 3, 1, tzinfo=JST), datetime(2031, 12, 1, tzinfo=JST)
        )
    )
    assert [d.body for d in docs] == ["新しい"]


def test_missing_required_field(tmp_path: Path) -> None:
    (tmp_path / "x.jsonl").write_text('{"body": "本文", "thread_id": "t"}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="必須項目"):
        list(ExportFileAdapter(tmp_path).fetch_documents(*ALL))


def test_knowledge_api_is_a_stub() -> None:
    with pytest.raises(NotImplementedError):
        KnowledgeApiAdapter().fetch_documents(*ALL)
