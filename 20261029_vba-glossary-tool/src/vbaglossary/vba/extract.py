"""VBA コードの取り出し。

- 実ブック（.xlsm など）は oletools (olevba) で展開する。Excel 本体とマクロの
  信頼設定に触れないのが利点。
- fixtures やデモ用に、.bas/.cls/.frm を並べたフォルダも受け付ける。
- どちらも「Attribute 行の除去」と「行継続 ( _ ) の結合」を済ませて返す。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

ATTR_RE = re.compile(r"^\s*Attribute\s+VB_\w+", re.IGNORECASE)
CONT_RE = re.compile(r"[ \t]+_[ \t]*\r?\n")
DOC_NAME_RE = re.compile(r"^(thisworkbook|thisdocument|sheet\d+|chart\d+|グラフ\d+)$", re.IGNORECASE)
CLASS_HINT_RE = re.compile(
    r"^\s*(Implements\s+\w|Public\s+Event\s|Private\s+Sub\s+Class_\w+)", re.MULTILINE
)


@dataclass(frozen=True)
class RawModule:
    """クリーニング済みの 1 モジュール。kind は標準/クラス/シート等の推定。"""

    name: str
    kind: str
    code: str


def clean_code(raw: str) -> str:
    lines = [line for line in raw.splitlines() if not ATTR_RE.match(line)]
    code = "\n".join(lines)
    code = CONT_RE.sub(" ", code)
    return code


def module_kind(name: str, code: str) -> str:
    if DOC_NAME_RE.match(name):
        return "document"
    if CLASS_HINT_RE.search(code):
        return "class"
    return "standard"


def _read_text(path: Path) -> str:
    data = path.read_bytes()
    for enc in ("utf-8-sig", "cp932"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("cp932", errors="replace")


def extract_modules(source: Path) -> list[RawModule]:
    """ブックまたはフォルダからモジュールの一覧を取り出す。"""
    out: list[RawModule] = []
    if source.is_dir():
        for pattern in ("*.bas", "*.cls", "*.frm"):
            for path in sorted(source.glob(pattern)):
                code = clean_code(_read_text(path))
                out.append(RawModule(path.stem, module_kind(path.stem, code), code))
        return out

    from oletools.olevba import VBA_Parser

    parser = VBA_Parser(str(source))
    try:
        seen: set[str] = set()
        for _fn, _stream, vba_filename, vba_code in parser.extract_all_macros():
            name = Path(vba_filename).stem
            if name in seen:
                continue
            seen.add(name)
            code = clean_code(vba_code)
            out.append(RawModule(name, module_kind(name, code), code))
        return out
    finally:
        parser.close()
