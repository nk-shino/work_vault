"""候補語の抽出。形態素解析による複合語と、正規表現による略語・カタカナ語の2系統。

社内用語は辞書に無い複合語（「〇〇台帳」「〇〇便」）や略語であることが多いので、
形態素を名詞の連続でつなぎ直したものを主な候補にする。
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from glossary.nlp import split_mode, tokenizer
from glossary.stats.normalize import normalize_key

# マスキングで入れた <PERSON> などは語の途中に挟まらないよう、区切りに置き換えてから解析する
_MASK_TOKEN = re.compile(r"<[A-Z]+>")
_ACRONYM = re.compile(r"(?<![A-Za-z0-9])[A-Z][A-Z0-9]{1,9}(?:-[A-Z0-9]{1,6})?(?![A-Za-z0-9])")
_KATAKANA = re.compile(r"[ァ-ヶ][ァ-ヶー]{2,}")
_JOINABLE = {"名詞", "接尾辞", "接頭辞"}
_SKIP_NOUN_SUB = {"数詞", "代名詞"}


@dataclass(frozen=True)
class Candidate:
    surface: str
    key: str
    kind: str  # compound / noun / acronym / katakana


def load_stopwords(path: Path) -> set[str]:
    words = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        w = line.strip()
        if w and not w.startswith("#"):
            words.add(normalize_key(w))
    return words


def _morph_candidates(text: str) -> list[Candidate]:
    out: list[Candidate] = []
    run: list[tuple[str, str]] = []  # (表層, 品詞大分類)

    def flush() -> None:
        # 接頭辞で終わる・接尾辞で始まる連続は語として不完全なので端を落とす。
        # 動詞の連用形は名詞にはさまれたときだけ残す（「記入し」の「し」は落ちる）
        while run and run[-1][1] in ("接頭辞", "動詞"):
            run.pop()
        while run and run[0][1] in ("接尾辞", "動詞"):
            run.pop(0)
        if run:
            surface = "".join(s for s, _ in run)
            kind = "compound" if len(run) >= 2 else "noun"
            if len(surface) >= 2:
                out.append(Candidate(surface, normalize_key(surface), kind))
        run.clear()

    for m in tokenizer().tokenize(text, split_mode("A")):
        pos = m.part_of_speech()
        if pos[0] in _JOINABLE and pos[1] not in _SKIP_NOUN_SUB and m.surface().strip():
            run.append((m.surface(), pos[0]))
        elif pos[0] == "動詞" and pos[5].startswith("連用形") and run:
            # 「星読み台帳」「霧抜き作業」のように、動詞の連用形が名詞をつなぐ社内用語は多い
            run.append((m.surface(), "動詞"))
        else:
            flush()
    flush()
    return out


def extract(text: str, stopwords: set[str] | None = None) -> list[Candidate]:
    """1文書から候補を出す。同じ語が何度出ても、出た回数だけ返す（頻度に使うため）。"""
    stop = stopwords or set()
    s = _MASK_TOKEN.sub("\n", unicodedata.normalize("NFKC", text))
    found = _morph_candidates(s)
    found += [Candidate(m.group(), normalize_key(m.group()), "acronym") for m in _ACRONYM.finditer(s)]
    found += [
        Candidate(m.group(), normalize_key(m.group()), "katakana") for m in _KATAKANA.finditer(s)
    ]
    return [c for c in found if c.key and c.key not in stop]
