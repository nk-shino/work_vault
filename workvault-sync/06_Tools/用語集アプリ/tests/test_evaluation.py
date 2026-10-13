from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from glossary.evaluation import metrics

ROOT = Path(__file__).resolve().parents[1]


def test_candidate_precision() -> None:
    rows = [{"rank": str(i), "is_term": v} for i, v in enumerate(["1", "0", "1", "1"], 1)]
    assert metrics.candidate_precision(rows) == pytest.approx(0.75)
    assert metrics.candidate_precision(rows, k=2) == pytest.approx(0.5)
    assert metrics.candidate_precision([]) is None


def test_definition_adoption() -> None:
    rows = [{"decision": d} for d in ["accepted", "edited", "rejected", "accepted"]]
    got = metrics.definition_adoption(rows)
    assert got.as_is == pytest.approx(0.5)
    assert got.with_edit == pytest.approx(0.75)
    with pytest.raises(ValueError):
        metrics.definition_adoption([{"decision": "maybe"}])


def test_relation_validity() -> None:
    assert metrics.relation_validity([{"valid": "1"}, {"valid": "0"}]) == pytest.approx(0.5)


def test_mean_review_seconds_sums_per_term() -> None:
    rows = [
        {"term": "A", "started_at": "2031-01-01T10:00:00", "finished_at": "2031-01-01T10:01:00"},
        {"term": "A", "started_at": "2031-01-02T10:00:00", "finished_at": "2031-01-02T10:01:00"},
        {"term": "B", "started_at": "2031-01-01T10:00:00", "finished_at": "2031-01-01T10:00:30"},
    ]
    # A は合計120秒、B は30秒 → (120 + 30) / 2
    assert metrics.mean_review_seconds(rows) == pytest.approx(75.0)


def test_contradiction_counts_senses_once() -> None:
    rows = [
        {"sense_id": "s1", "contradicts": "1"},
        {"sense_id": "s1", "contradicts": "1"},
        {"sense_id": "s2", "contradicts": "0"},
        {"sense_id": "s3", "contradicts": "1"},
    ]
    assert metrics.contradiction_count(rows) == 2


def test_templates_are_readable(tmp_path: Path) -> None:
    # 配布しているテンプレートがそのまま評価に通ること（書式が崩れていないこと）
    for name in metrics.FILES.values():
        shutil.copy(ROOT / "eval" / "templates" / name, tmp_path / name)
    got = metrics.evaluate_dir(tmp_path)
    assert got["candidate_precision"] == pytest.approx(0.5)
    assert got["contradiction_count"] == 0
