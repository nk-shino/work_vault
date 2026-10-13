"""表記ゆれの名寄せ。見出しは人が読む表記のまま残し、数えるときだけこのキーでまとめる。

全角半角・大文字小文字・ひらがなカタカナ・長音符・送り仮名の揺れを1つのキーに寄せる。
送り仮名（打合せ／打ち合わせ）は規則では決めきれないので、SudachiPy の正規化形に頼る。
"""

from __future__ import annotations

import re
import unicodedata

from glossary.nlp import split_mode, tokenizer

# NFKC で半角カナの長音は「ー」になるが、ハイフン類は残る（全角ハイフンは半角の - になる）。
# カタカナの直後にあるものだけ長音に寄せる
_DASHES = re.compile(r"(?<=[ァ-ヶー])[-‐‑‒–—―−－ｰ]")
# カタカナ語の末尾の長音は付ける流儀と付けない流儀がある（サーバー／サーバ）ので落とす
_TRAILING_CHOON = re.compile(r"(?<=[ァ-ヶー][ァ-ヶ])ー+(?![ァ-ヶー])")


def hira_to_kata(text: str) -> str:
    return "".join(chr(ord(c) + 0x60) if "ぁ" <= c <= "ゖ" else c for c in text)


def normalize_surface(text: str) -> str:
    s = unicodedata.normalize("NFKC", text).casefold()
    s = hira_to_kata(s)
    s = _DASHES.sub("ー", s)
    return _TRAILING_CHOON.sub("", s)


def normalize_key(text: str) -> str:
    s = unicodedata.normalize("NFKC", text)
    morphs = tokenizer().tokenize(s, split_mode("A"))
    return normalize_surface("".join(m.normalized_form() for m in morphs))
