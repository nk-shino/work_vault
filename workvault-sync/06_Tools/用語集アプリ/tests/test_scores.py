"""スコア計算：小さな既知入力で、手計算の値と一致することを確かめる。"""

from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta, timezone

import pytest

from glossary.stats import scores

DOCS = [["a", "a", "b"], ["a", "c"], ["c", "d"]]


def test_term_frequency() -> None:
    assert scores.term_frequency(DOCS) == {"a": 3, "b": 1, "c": 2, "d": 1}


def test_document_frequency() -> None:
    assert scores.document_frequency(DOCS) == {"a": 2, "b": 1, "c": 2, "d": 1}


def test_tfidf_known_values() -> None:
    # N=3。a: tf=3, df=2 → 3·ln(3/2)。b: 1·ln3。c: 2·ln(3/2)。d: 1·ln3
    got = scores.tfidf(DOCS)
    assert got["a"] == pytest.approx(3 * math.log(1.5))
    assert got["b"] == pytest.approx(math.log(3))
    assert got["c"] == pytest.approx(2 * math.log(1.5))
    assert got["d"] == pytest.approx(math.log(3))


def test_tfidf_is_zero_for_word_in_every_doc() -> None:
    assert scores.tfidf([["x", "y"], ["x"]])["x"] == 0


def test_cooccurrence_counts_units_not_occurrences() -> None:
    units = [{"a", "b"}, {"a", "b", "c"}, {"b", "c"}]
    got = scores.cooccurrence(units)
    assert got == {("a", "b"): 2, ("a", "c"): 1, ("b", "c"): 2}


def test_pmi_known_values() -> None:
    # c(a,b)=2, c(a)=2, c(b)=4, N=8 → log2(2·8 / (2·4)) = log2(2) = 1
    assert scores.pmi(2, 2, 4, 8) == pytest.approx(1.0)
    # 独立（期待どおりの頻度）なら 0: c(a,b)=1, c(a)=2, c(b)=4, N=8
    assert scores.pmi(1, 2, 4, 8) == pytest.approx(0.0)
    # 必ず一緒に出る: c(a,b)=c(a)=c(b)=1, N=4 → log2(4) = 2
    assert scores.pmi(1, 1, 1, 4) == pytest.approx(2.0)
    assert scores.pmi(0, 1, 1, 4) == float("-inf")


def test_pmi_on_units_end_to_end() -> None:
    units = [{"a", "b"}, {"a", "b"}, {"c"}, {"c"}]
    pairs, counts = scores.cooccurrence(units), scores.unit_counts(units)
    # a と b は常に一緒: log2(2·4/(2·2)) = 1
    assert scores.pmi(pairs[("a", "b")], counts["a"], counts["b"], len(units)) == pytest.approx(1.0)


def test_thread_units_merge_by_thread() -> None:
    items = [("t1", ["a"]), ("t2", ["c"]), ("t1", ["b"])]
    assert scores.thread_units(items) == [{"a", "b"}, {"c"}]


def test_time_window_units() -> None:
    jst = timezone(timedelta(hours=9))
    # 窓は 1970-01-01 起点の7日刻み。1/5 は最初の窓（0〜6日目）の4日目
    base = datetime(1970, 1, 5, tzinfo=UTC)
    week = timedelta(days=7)
    items = [
        (base + timedelta(days=1), ["a"]),
        (base + timedelta(days=2), ["b"]),  # a と同じ窓
        (base + timedelta(days=8), ["c"]),  # 次の窓
        ((base + timedelta(days=9)).astimezone(jst), ["a"]),  # 時差があっても同じ窓に入る
    ]
    got = scores.time_window_units(items, week)
    assert got == [{"a", "b"}, {"a", "c"}]
