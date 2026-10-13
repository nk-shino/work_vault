"""評価指標。人手ラベルは CSV（eval/templates/ の形式）で受け取る。

実データが無い今は計算だけを固めておく。指標の定義がぶれると、
Phase 1 以降で「前より良くなったか」を比べられなくなるため。
"""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _flag(value: str) -> bool:
    v = value.strip().lower()
    if v in ("1", "true", "yes", "y", "○"):
        return True
    if v in ("0", "false", "no", "n", "×", ""):
        return False
    raise ValueError(f"0/1 で付けること: {value!r}")


def _ratio(num: int, den: int) -> float | None:
    # ラベルが0件なら 0% ではなく「測れていない」を返す
    return num / den if den else None


def candidate_precision(rows: list[dict[str, str]], k: int | None = None) -> float | None:
    """候補語の適合率。rank 順の上位 k 件（省略時は全件）のうち is_term=1 の割合。"""
    ranked = sorted(rows, key=lambda r: int(r["rank"]))
    top = ranked[:k] if k else ranked
    return _ratio(sum(_flag(r["is_term"]) for r in top), len(top))


@dataclass(frozen=True)
class Adoption:
    as_is: float | None  # そのまま採用
    with_edit: float | None  # 修正して採用も含める


def definition_adoption(rows: list[dict[str, str]]) -> Adoption:
    """定義草案の採用率。decision は accepted / edited / rejected のいずれか。"""
    decided = [r["decision"].strip() for r in rows]
    unknown = set(decided) - {"accepted", "edited", "rejected"}
    if unknown:
        raise ValueError(f"decision の値が不正: {sorted(unknown)}")
    n = len(decided)
    return Adoption(
        _ratio(decided.count("accepted"), n),
        _ratio(decided.count("accepted") + decided.count("edited"), n),
    )


def relation_validity(rows: list[dict[str, str]]) -> float | None:
    """関係付けの妥当率。valid=1 の割合。"""
    return _ratio(sum(_flag(r["valid"]) for r in rows), len(rows))


def mean_review_seconds(rows: list[dict[str, str]]) -> float | None:
    """1語あたりの平均レビュー時間。同じ語を複数回見た場合は合計してから語数で割る。"""
    per_term: dict[str, float] = defaultdict(float)
    for r in rows:
        start = datetime.fromisoformat(r["started_at"])
        end = datetime.fromisoformat(r["finished_at"])
        if end < start:
            raise ValueError(f"終了が開始より前: {r['term']}")
        per_term[r["term"]] += (end - start).total_seconds()
    return sum(per_term.values()) / len(per_term) if per_term else None


def contradiction_count(rows: list[dict[str, str]]) -> int:
    """用例と矛盾する定義の件数。1つの語義に矛盾する用例が複数あっても1件と数える。"""
    return len({r["sense_id"] for r in rows if _flag(r["contradicts"])})


FILES = {
    "candidates": "candidate_labels.csv",
    "definitions": "definition_reviews.csv",
    "relations": "relation_labels.csv",
    "review_times": "review_times.csv",
    "contradictions": "contradiction_labels.csv",
}


def evaluate_dir(directory: Path, k: int = 50) -> dict[str, object]:
    """ラベル CSV の置かれたフォルダをまとめて評価する。無いファイルの指標は None。"""

    def load(name: str) -> list[dict[str, str]] | None:
        p = directory / FILES[name]
        return _rows(p) if p.exists() else None

    cands, defs, rels, times, contra = (load(n) for n in FILES)
    adoption = definition_adoption(defs) if defs is not None else None
    return {
        "candidate_precision": candidate_precision(cands) if cands is not None else None,
        f"candidate_precision_at_{k}": candidate_precision(cands, k) if cands is not None else None,
        "definition_adoption_as_is": adoption.as_is if adoption else None,
        "definition_adoption_with_edit": adoption.with_edit if adoption else None,
        "relation_validity": relation_validity(rels) if rels is not None else None,
        "mean_review_seconds": mean_review_seconds(times) if times is not None else None,
        "contradiction_count": contradiction_count(contra) if contra is not None else None,
    }
