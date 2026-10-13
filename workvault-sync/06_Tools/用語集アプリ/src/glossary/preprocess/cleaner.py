"""署名・引用・定型あいさつ・免責文を落とす。ルールは config/cleaning_rules.yaml。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


def _compile(items: list[dict[str, Any]] | None) -> list[re.Pattern[str]]:
    return [re.compile(str(item["pattern"])) for item in items or []]


@dataclass(frozen=True)
class Cleaner:
    cut_after: list[re.Pattern[str]]
    drop_lines: list[re.Pattern[str]]
    drop_paragraphs: list[re.Pattern[str]]

    @classmethod
    def from_yaml(cls, path: Path) -> Cleaner:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return cls(
            _compile(data.get("cut_after")),
            _compile(data.get("drop_lines")),
            _compile(data.get("drop_paragraphs")),
        )

    def clean(self, text: str) -> str:
        kept: list[str] = []
        for line in text.replace("\r\n", "\n").split("\n"):
            if any(p.search(line) for p in self.cut_after):
                break
            if any(p.search(line) for p in self.drop_lines):
                continue
            kept.append(line.rstrip())
        paragraphs = re.split(r"\n\s*\n", "\n".join(kept))
        body = [p.strip() for p in paragraphs if p.strip()]
        body = [p for p in body if not any(r.search(p) for r in self.drop_paragraphs)]
        return "\n\n".join(body)
