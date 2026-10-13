"""SudachiPy の辞書読み込みは重いので、プロセスで1つだけ作って使い回す。"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from sudachipy import Dictionary, SplitMode


@lru_cache(maxsize=1)
def tokenizer() -> Any:
    return Dictionary().create()


def split_mode(name: str) -> Any:
    return {"A": SplitMode.A, "B": SplitMode.B, "C": SplitMode.C}[name]
