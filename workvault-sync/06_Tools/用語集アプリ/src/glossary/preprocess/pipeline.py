"""取得 → 除去 → マスキングをまとめて行い、マスキング済みのものだけを書き出す。"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from glossary.ports import SourcePort, is_document
from glossary.preprocess.cleaner import Cleaner
from glossary.preprocess.masking import Masker


@dataclass(frozen=True)
class MaskedDocument:
    thread_id: str
    occurred_at: datetime
    source_ref: str
    text: str


def preprocess(
    source: SourcePort,
    cleaner: Cleaner,
    masker: Masker,
    since: datetime,
    until: datetime,
) -> tuple[list[MaskedDocument], Counter[str]]:
    docs: list[MaskedDocument] = []
    totals: Counter[str] = Counter()
    for raw in source.fetch_documents(since, until):
        # raw.body（伏せる前の本文）はこのループの外へ持ち出さない
        # 署名・引用・あいさつの除去はメール向け。資料にかけると「〜書きました」の行で以降を捨ててしまう
        body = raw.body if is_document(raw.source_ref) else cleaner.clean(raw.body)
        result = masker.mask(body)
        totals.update(result.counts)
        if result.text.strip():
            docs.append(MaskedDocument(raw.thread_id, raw.occurred_at, raw.source_ref, result.text))
    return docs, totals


def save_jsonl(docs: Iterable[MaskedDocument], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        for d in docs:
            row = asdict(d) | {"occurred_at": d.occurred_at.isoformat()}
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_jsonl(path: Path) -> list[MaskedDocument]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            out.append(
                MaskedDocument(
                    r["thread_id"], datetime.fromisoformat(r["occurred_at"]), r["source_ref"], r["text"]
                )
            )
    return out
