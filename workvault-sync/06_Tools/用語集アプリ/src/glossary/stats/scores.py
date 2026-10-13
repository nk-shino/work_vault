"""頻度・TF-IDF・共起・PMI。LLM は使わない。

どれも「語のリストのリスト」か「語の集合のリスト」を受け取る純粋な関数にしてある。
小さな入力で手計算と突き合わせられるようにするため（tests/test_scores.py）。
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Iterable, Sequence
from datetime import UTC, datetime, timedelta
from itertools import combinations

Pair = tuple[str, str]


def term_frequency(docs: Sequence[Sequence[str]]) -> Counter[str]:
    total: Counter[str] = Counter()
    for d in docs:
        total.update(d)
    return total


def document_frequency(docs: Sequence[Sequence[str]]) -> Counter[str]:
    df: Counter[str] = Counter()
    for d in docs:
        df.update(set(d))
    return df


def tfidf(docs: Sequence[Sequence[str]]) -> dict[str, float]:
    """コーパス全体での TF-IDF = Σ_d tf(t, d) × ln(N / df(t))。

    全文書に出る語は 0 になる。「どこにでも出る語は用語集の候補として弱い」をそのまま表す。
    """
    n = len(docs)
    df = document_frequency(docs)
    tf = term_frequency(docs)
    return {t: tf[t] * math.log(n / df[t]) for t in tf}


def cooccurrence(units: Iterable[set[str]]) -> Counter[Pair]:
    """単位（スレッドや時間窓）ごとに、両方の語が現れた単位の数を数える。ペアは辞書順。"""
    counts: Counter[Pair] = Counter()
    for unit in units:
        for a, b in combinations(sorted(unit), 2):
            counts[(a, b)] += 1
    return counts


def pmi(pair_count: int, count_a: int, count_b: int, n_units: int) -> float:
    """PMI = log2( P(a,b) / (P(a) P(b)) ) = log2( c(a,b) N / (c(a) c(b)) )。"""
    if pair_count == 0:
        return float("-inf")
    return math.log2(pair_count * n_units / (count_a * count_b))


def unit_counts(units: Sequence[set[str]]) -> Counter[str]:
    c: Counter[str] = Counter()
    for u in units:
        c.update(u)
    return c


def thread_units(items: Iterable[tuple[str, Sequence[str]]]) -> list[set[str]]:
    """(thread_id, 語のリスト) をスレッドごとの語の集合にまとめる。"""
    by_thread: dict[str, set[str]] = defaultdict(set)
    for thread_id, terms in items:
        by_thread[thread_id].update(terms)
    return [by_thread[k] for k in sorted(by_thread)]


_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


def time_window_units(
    items: Iterable[tuple[datetime, Sequence[str]]], window: timedelta
) -> list[set[str]]:
    """発生日時を固定幅の窓で区切り、同じ窓に入った文書の語を1つの集合にする。

    スレッドが別でも、同じ時期に話題になった語どうしを拾うため。
    窓の境界は 1970-01-01 UTC 起点で固定する（入力によって境界がずれないように）。
    """
    buckets: dict[int, set[str]] = defaultdict(set)
    for at, terms in items:
        aware = at if at.tzinfo else at.replace(tzinfo=UTC)
        buckets[int((aware - _EPOCH) // window)].update(terms)
    return [buckets[k] for k in sorted(buckets)]
