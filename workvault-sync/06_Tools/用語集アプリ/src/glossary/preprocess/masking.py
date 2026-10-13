"""個人情報などを伏せる。ルールは config/masking_rules.yaml。

伏せる前の文字列はメモリの外へ出さない。この関数の出力だけがディスクや DB へ行く。

伏せないものが2種類ある（2026-09-24 決定）。
- 必要書類の URL・共有フォルダのパス（protect）。用語集で「どこにあるか」を引けないと意味が無い
- 役割と一緒に出る人名（keep_before / keep_after）。「〇〇部長の承認」「〇〇さんが担当」は
  誰に聞けばよいかという情報そのもので、伏せると引継ぎ資料として役に立たない
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from glossary.nlp import split_mode, tokenizer

_MASK_TOKEN = re.compile(r"(<[A-Z]+>)")
# 保護した部分の置き場。<[A-Z]+> の形なので、品詞ルールも他の正規表現もこれを避けて通る
_KEEP = "<KEEP>"


class MaskingLeak(RuntimeError):
    """伏せたはずの形が残っていた。ここで止めて、ディスクへ書かせない。"""


@dataclass(frozen=True)
class RegexRule:
    name: str
    pattern: re.Pattern[str]
    token: str
    group: int = 0
    exclude: frozenset[str] = frozenset()
    exclude_suffix: tuple[str, ...] = ()
    keep_before: re.Pattern[str] | None = None
    keep_after: re.Pattern[str] | None = None

    def _skip(self, text: str, start: int, end: int) -> bool:
        hit = text[start:end]
        return (
            hit in self.exclude
            or (bool(self.exclude_suffix) and hit.endswith(self.exclude_suffix))
            or _in_role(text, start, end, self.keep_before, self.keep_after)
        )

    def apply(self, text: str) -> tuple[str, int]:
        count = 0
        parts: list[str] = []
        last = 0
        for m in self.pattern.finditer(text):
            start, end = m.span(self.group)
            if start < 0 or self._skip(text, start, end):
                continue
            parts.append(text[last:start])
            parts.append(self.token)
            last = end
            count += 1
        parts.append(text[last:])
        return "".join(parts), count

    def leaks(self, text: str) -> bool:
        # 置換後の token 自体には当たらない前提で、同じ形が残っていないかを見る
        return any(
            not self._skip(text, *m.span(self.group))
            for m in self.pattern.finditer(text)
            if m.group(self.group)
        )


@dataclass(frozen=True)
class PosRule:
    name: str
    pos: tuple[str, ...]
    token: str
    keep_before: re.Pattern[str] | None = None
    keep_after: re.Pattern[str] | None = None

    def _apply_segment(self, text: str) -> tuple[str, int]:
        count = 0
        parts: list[str] = []
        last = 0
        for m in tokenizer().tokenize(text, split_mode("C")):
            if tuple(m.part_of_speech()[: len(self.pos)]) == self.pos and not _in_role(
                text, m.begin(), m.end(), self.keep_before, self.keep_after
            ):
                parts.append(text[last : m.begin()])
                parts.append(self.token)
                last = m.end()
                count += 1
        parts.append(text[last:])
        return "".join(parts), count

    def apply(self, text: str) -> tuple[str, int]:
        # 置換済みの <PHONE> などは解析に回さない。辞書が中の英字を人名と判定して二重に置き換えるため
        count = 0
        parts: list[str] = []
        for i, seg in enumerate(_MASK_TOKEN.split(text)):
            if i % 2:
                parts.append(seg)
            else:
                out, n = self._apply_segment(seg)
                parts.append(out)
                count += n
        return "".join(parts), count


Rule = RegexRule | PosRule


def _in_role(
    text: str, start: int, end: int, before: re.Pattern[str] | None, after: re.Pattern[str] | None
) -> bool:
    # 前は同じ行の中だけを見る。前の行の「担当」に引きずられて無関係な名前まで残さないため
    line_start = text.rfind("\n", 0, start) + 1
    return bool(
        (before and before.search(text[line_start:start]))
        or (after and after.match(text, end))
    )


def _opt(item: dict[str, Any], key: str) -> re.Pattern[str] | None:
    return re.compile(str(item[key])) if item.get(key) else None


def _flags(names: list[str]) -> re.RegexFlag:
    flags = re.RegexFlag(0)
    for name in names:
        flags |= re.RegexFlag[name]
    return flags


def _rule(item: dict[str, Any]) -> Rule:
    kind = item.get("type", "regex")
    if kind == "regex":
        return RegexRule(
            name=str(item["name"]),
            pattern=re.compile(str(item["pattern"]), _flags(item.get("flags", []))),
            token=str(item["token"]),
            group=int(item.get("group", 0)),
            exclude=frozenset(item.get("exclude", [])),
            exclude_suffix=tuple(item.get("exclude_suffix", [])),
            keep_before=_opt(item, "keep_before"),
            keep_after=_opt(item, "keep_after"),
        )
    if kind == "pos":
        return PosRule(
            str(item["name"]),
            tuple(item["pos"]),
            str(item["token"]),
            _opt(item, "keep_before"),
            _opt(item, "keep_after"),
        )
    raise ValueError(f"未知のルール種別: {kind}")


@dataclass
class MaskResult:
    text: str
    counts: Counter[str] = field(default_factory=Counter)


@dataclass(frozen=True)
class Masker:
    rules: list[Rule]
    protect: re.Pattern[str] | None = None

    @classmethod
    def from_yaml(cls, path: Path) -> Masker:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        # 1本の正規表現にまとめる。別々に退避すると、戻すときに本文の順番とずれる
        keep = [f"(?:{item['pattern']})" for item in data.get("protect", [])]
        return cls(
            [_rule(item) for item in data.get("rules", [])],
            re.compile("|".join(keep)) if keep else None,
        )

    def mask(self, text: str) -> MaskResult:
        # 残すものを先に退避する。URL の中の数字を電話番号やシリアルのルールが崩さないように
        kept: list[str] = []

        def stash(m: re.Match[str]) -> str:
            kept.append(m.group())
            return _KEEP

        if self.protect:
            text = self.protect.sub(stash, text)
        result = MaskResult(text)
        for rule in self.rules:
            result.text, n = rule.apply(result.text)
            if n:
                result.counts[rule.name] += n
        self.assert_clean(result.text)
        restore = iter(kept)
        result.text = re.sub(re.escape(_KEEP), lambda _m: next(restore), result.text)
        return result

    def assert_clean(self, text: str) -> None:
        for rule in self.rules:
            if isinstance(rule, RegexRule) and rule.leaks(text):
                raise MaskingLeak(f"マスキング漏れ: {rule.name}")
