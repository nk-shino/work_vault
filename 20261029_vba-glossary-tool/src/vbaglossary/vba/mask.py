"""禁止情報の検査とマスキング。ルールは config/masking_rules.yaml。

1 件でも一致したら、そのプロシージャの提案は保留になり、全文は保持しない
（一致部分を ■ で置き換えた断片だけを残す）。
"""

from __future__ import annotations

import functools
import re
from pathlib import Path

import yaml

MASK_CHAR = "■"


@functools.lru_cache(maxsize=4)
def load_rules(config_path: str) -> tuple[tuple[str, re.Pattern[str]], ...]:
    data = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    return tuple(
        (rule["name"], re.compile(rule["pattern"])) for rule in data.get("rules", [])
    )


def scan(text: str, config_path: str) -> list[str]:
    """一致したルール名の一覧を返す。空なら問題なし。"""
    return [name for name, pattern in load_rules(config_path) if pattern.search(text)]


def mask(text: str, config_path: str) -> str:
    """一致部分を ■ で置き換える。マスキング済みの文は保存してよい。"""
    for _name, pattern in load_rules(config_path):
        text = pattern.sub(MASK_CHAR * 6, text)
    return text
