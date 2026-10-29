"""モジュールコードからプロシージャを抜き出す。

- ヘッダ（Sub/Function/Property）は 1 行に結合してから正規表現で取る
- 本文は対応する End Sub / End Function / End Property まで
- 呼び出しは「既知のプロシージャ名が本文に出てくる」方法で集める（2 パス）
- タグは本文の特徴（エラー処理・Static・ループ等）から自動で付ける
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from vbaglossary.vba.extract import RawModule

HEADER_RE = re.compile(
    r"""^\s*
        (?:(?P<access>Public|Private|Friend)\s+)?
        (?:(?P<static>Static)\s+)?
        (?P<kind>Sub|Function|Property\s+(?:Get|Let|Set))\s+
        (?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*
        \((?P<args>[^)]*)\)\s*
        (?:As\s+(?P<returns>[A-Za-z_][\w.]*(?:\s*\(\s*\))?))?\s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)

PARAM_WORDS_RE = re.compile(
    r"""^\s*
        (?:(?P<optional>Optional)\s+)?
        (?:(?P<modifier>ByVal|ByRef|ParamArray)\s+)?
        (?P<name>[A-Za-z_][A-Za-z0-9_]*\s*(?:\(\s*\))?)
        (?:\s+As\s+(?P<type>[A-Za-z_][\w.]*))?
        (?:\s*=\s*(?P<default>[^\s].*?))?
        \s*$""",
    re.IGNORECASE | re.VERBOSE,
)


@dataclass
class ParsedParam:
    name: str
    type: str | None
    modifier: str | None
    optional: bool
    default: str | None


@dataclass
class ParsedProc:
    name: str
    kind: str
    access: str
    static: bool
    signature: str
    params: list[ParsedParam]
    returns: str | None
    start_line: int
    end_line: int
    body_lines: list[str]
    comment_text: str = ""
    calls: set[str] = field(default_factory=set)
    tags: list[str] = field(default_factory=list)

    @property
    def line_count(self) -> int:
        return self.end_line - self.start_line + 1

    @property
    def body_code(self) -> str:
        """ヘッダと End 行を除いた本文。"""
        inner = self.body_lines[1:-1] if len(self.body_lines) > 2 else []
        return "\n".join(line for line in inner if line.strip())


def _kind_label(raw: str) -> str:
    return re.sub(r"\s+", " ", raw.strip().title()).replace("Let", "Let")


def _end_token(kind_label: str) -> str:
    if kind_label.startswith("Property"):
        return "End Property"
    return "End " + kind_label


def _split_args(args: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    buf = ""
    for ch in args:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    if buf.strip():
        parts.append(buf)
    return [p.strip() for p in parts if p.strip()]


def _parse_args(args: str) -> list[ParsedParam]:
    out = []
    for part in _split_args(args):
        m = PARAM_WORDS_RE.match(part)
        if m is None:
            out.append(ParsedParam(name=part, type=None, modifier=None, optional=False, default=None))
            continue
        out.append(
            ParsedParam(
                name=m.group("name").strip(),
                type=m.group("type"),
                modifier=m.group("modifier"),
                optional=m.group("optional") is not None,
                default=m.group("default"),
            )
        )
    return out


def _collect_header_comment(lines: list[str], header_index: int) -> str:
    comment_lines: list[str] = []
    i = header_index - 1
    while i >= 0 and lines[i].strip().startswith("'"):
        comment_lines.append(lines[i].strip().lstrip("'").strip())
        i -= 1
    comment_lines.reverse()
    return " ".join(line for line in comment_lines if line)


def _compute_tags(p: ParsedProc, body: str) -> list[str]:
    tags: list[str] = []
    if p.access == "Private":
        tags.append("private")
    if re.search(r"\bOn Error\b", body, re.IGNORECASE):
        tags.append("error-handling")
    if p.static or re.search(r"^\s*Static\s+\w", body, re.IGNORECASE | re.MULTILINE):
        tags.append("static-state")
    if re.search(r"\b(For\s|Do\s(While|Until)?|While\s)", body, re.IGNORECASE):
        tags.append("loop")
    if re.search(r"\bSelect Case\b", body, re.IGNORECASE):
        tags.append("select-case")
    if re.search(r"\bUserForm\w*\.Show\b|\bMsgBox\b|\bInputBox\b", body, re.IGNORECASE):
        tags.append("gui")
    if p.kind == "Sub" and p.access == "Private" and re.search(r"_\w+$", p.name):
        tags.append("event")
    if p.line_count >= 100:
        tags.append("long")
    return tags


def parse_module(mod: RawModule) -> list[ParsedProc]:
    lines = mod.code.splitlines()
    procs: list[ParsedProc] = []
    i = 0
    while i < len(lines):
        m = HEADER_RE.match(lines[i])
        if m is None:
            i += 1
            continue
        kind = _kind_label(m.group("kind"))
        end_token = _end_token(kind)
        j = i + 1
        while j < len(lines) and not re.match(rf"^\s*{end_token}\s*$", lines[j], re.IGNORECASE):
            j += 1
        end_index = j if j < len(lines) else len(lines) - 1
        body_lines = lines[i : end_index + 1]
        procs.append(
            ParsedProc(
                name=m.group("name"),
                kind=kind,
                access=(m.group("access") or "Public").title(),
                static=m.group("static") is not None,
                signature=lines[i].strip(),
                params=_parse_args(m.group("args") or ""),
                returns=m.group("returns"),
                start_line=i + 1,
                end_line=end_index + 1,
                body_lines=body_lines,
                comment_text=_collect_header_comment(lines, i),
            )
        )
        i = end_index + 1

    names = {p.name.lower() for p in procs}
    for p in procs:
        body = p.body_code
        for word in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", body):
            low = word.lower()
            if low in names and low != p.name.lower():
                p.calls.add(word)
        p.tags = _compute_tags(p, body)
    return procs
