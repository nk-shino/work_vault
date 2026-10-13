"""マスキング済み文書から、候補語ランキングと共起ペアランキングの CSV を作る。

CSV は BOM 付き UTF-8 で書く。社用PCの Excel でそのまま開いて文字化けしないように。
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

from glossary.preprocess.pipeline import MaskedDocument
from glossary.stats import scores
from glossary.stats.candidates import Candidate, extract


@dataclass(frozen=True)
class CandidateRow:
    surface: str
    key: str
    kinds: str
    freq: int
    df: int
    tfidf: float


@dataclass(frozen=True)
class PairRow:
    a: str
    b: str
    thread_count: int
    thread_pmi: float
    window_count: int
    window_pmi: float


def analyze(
    docs: list[MaskedDocument],
    stopwords: set[str],
    *,
    min_df: int = 2,
    top_k_for_pairs: int = 100,
    min_pair_count: int = 2,
    window: timedelta = timedelta(days=7),
) -> tuple[list[CandidateRow], list[PairRow]]:
    per_doc: list[list[Candidate]] = [extract(d.text, stopwords) for d in docs]
    keys_per_doc = [[c.key for c in cands] for cands in per_doc]

    # 同じキーに寄った表記のうち、いちばん多く出たものを見出しにする
    surfaces: dict[str, Counter[str]] = defaultdict(Counter)
    kinds: dict[str, set[str]] = defaultdict(set)
    for cands in per_doc:
        for c in cands:
            surfaces[c.key][c.surface] += 1
            kinds[c.key].add(c.kind)

    tf = scores.term_frequency(keys_per_doc)
    df = scores.document_frequency(keys_per_doc)
    ti = scores.tfidf(keys_per_doc)
    rows = [
        CandidateRow(
            surface=surfaces[k].most_common(1)[0][0],
            key=k,
            kinds="+".join(sorted(kinds[k])),
            freq=tf[k],
            df=df[k],
            tfidf=round(ti[k], 4),
        )
        for k in tf
        if df[k] >= min_df
    ]
    rows.sort(key=lambda r: (-r.tfidf, -r.freq, r.key))

    top = {r.key for r in rows[:top_k_for_pairs]}
    kept = [[k for k in keys if k in top] for keys in keys_per_doc]
    t_units = scores.thread_units((d.thread_id, ks) for d, ks in zip(docs, kept, strict=True))
    w_units = scores.time_window_units(
        ((d.occurred_at, ks) for d, ks in zip(docs, kept, strict=True)), window
    )
    t_pairs, t_counts = scores.cooccurrence(t_units), scores.unit_counts(t_units)
    w_pairs, w_counts = scores.cooccurrence(w_units), scores.unit_counts(w_units)
    label = {r.key: r.surface for r in rows}
    pairs = [
        PairRow(
            a=label[a],
            b=label[b],
            thread_count=n,
            thread_pmi=round(scores.pmi(n, t_counts[a], t_counts[b], len(t_units)), 4),
            window_count=w_pairs[(a, b)],
            window_pmi=round(
                scores.pmi(w_pairs[(a, b)], w_counts[a], w_counts[b], len(w_units)), 4
            ),
        )
        for (a, b), n in t_pairs.items()
        if n >= min_pair_count
    ]
    pairs.sort(key=lambda p: (-p.thread_pmi, -p.thread_count, p.a, p.b))
    return rows, pairs


def _write(path: Path, header: list[str], rows: list[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def write_candidates(rows: list[CandidateRow], path: Path) -> None:
    _write(
        path,
        ["rank", "surface", "key", "kinds", "freq", "df", "tfidf"],
        [[i, r.surface, r.key, r.kinds, r.freq, r.df, r.tfidf] for i, r in enumerate(rows, 1)],
    )


def write_pairs(rows: list[PairRow], path: Path) -> None:
    _write(
        path,
        ["rank", "a", "b", "thread_count", "thread_pmi", "window_count", "window_pmi"],
        [
            [i, p.a, p.b, p.thread_count, p.thread_pmi, p.window_count, p.window_pmi]
            for i, p in enumerate(rows, 1)
        ],
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))
