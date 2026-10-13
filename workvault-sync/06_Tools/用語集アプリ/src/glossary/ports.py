"""コアが依存してよい境界はここだけ。

取得元と LLM は仕様が決まっていないので、コアは具体的な実装を知らずに済むよう
この抽象だけを見る。仕様が決まったらアダプタを差し替え、コアは触らない。
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol


@dataclass(frozen=True)
class RawDocument:
    """取得元から受け取った1通分。

    body はマスキング前の本文なのでメモリ上だけで扱い、ディスクにも DB にも書かない。
    source_ref は出典に戻るためのキーで、本文を持たなくても元をたどれるようにする。
    """

    body: str
    thread_id: str
    occurred_at: datetime
    source_ref: str


def is_document(source_ref: str) -> bool:
    """メールではなく資料（メモ・手順書）から来たものか。出典キーの頭で見分ける。"""
    return source_ref.startswith("doc:")


class SourcePort(Protocol):
    def fetch_documents(self, since: datetime, until: datetime) -> Iterable[RawDocument]:
        """[since, until) に発生した文書を返す。"""
        ...


class LlmPort(Protocol):
    def complete_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        """schema（JSON Schema のサブセット）に沿った dict を返す。"""
        ...

    def embed(self, texts: list[str]) -> list[list[float]]: ...
