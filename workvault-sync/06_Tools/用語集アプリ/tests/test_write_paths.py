"""書き込み経路の静的検査。実行時のガードと合わせて、経路が増えていないことを確かめる。"""

from __future__ import annotations

import ast
import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "glossary"
ALLOWED_SENSE_WRITER_CALLERS = {"domain/proposals.py", "domain/review.py"}


def py_files() -> list[tuple[str, ast.Module, str]]:
    out = []
    for p in SRC.rglob("*.py"):
        text = p.read_text(encoding="utf-8")
        out.append((p.relative_to(SRC).as_posix(), ast.parse(text), text))
    return out


def imported_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            names.add(node.module or "")
            names.update(f"{node.module}.{a.name}" for a in node.names)
        elif isinstance(node, ast.Import):
            names.update(a.name for a in node.names)
    return names


def test_only_two_modules_use_sense_writer() -> None:
    # `from glossary.domain import sense_writer` も `from glossary.domain.sense_writer import x` も拾う
    users = {
        rel
        for rel, tree, _ in py_files()
        if rel != "domain/sense_writer.py"
        and any(n.startswith("glossary.domain.sense_writer") for n in imported_names(tree))
    }
    assert users == ALLOWED_SENSE_WRITER_CALLERS


def test_only_sense_writer_opens_write_scope() -> None:
    users = {rel for rel, _, text in py_files() if "sense_write_scope" in text}
    assert users == {"db/guards.py", "domain/sense_writer.py"}


def test_no_physical_delete_in_code() -> None:
    pattern = re.compile(r"\.delete\(|DELETE\s+FROM|\bdelete\(\s*[A-Z]", re.IGNORECASE)
    offenders = [rel for rel, _, text in py_files() if pattern.search(text)]
    assert offenders == []
