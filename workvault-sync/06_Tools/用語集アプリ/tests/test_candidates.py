from __future__ import annotations

from glossary.stats.candidates import extract


def surfaces(text: str) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for c in extract(text):
        out.setdefault(c.surface, set()).add(c.kind)
    return out


def test_compound_noun_is_joined() -> None:
    got = surfaces("星読み台帳に結果を記入する。")
    assert "星読み台帳" in got and "compound" in got["星読み台帳"]


def test_acronym_and_katakana() -> None:
    got = surfaces("MGKの結果はスカイポストで送る。")
    assert "acronym" in got["MGK"]
    assert "katakana" in got["スカイポスト"]


def test_mask_tokens_do_not_become_terms() -> None:
    got = surfaces("<PERSON>さんが<MONEY>を支払った。")
    assert not any(s in got for s in ("PERSON", "MONEY"))


def test_stopwords_are_removed() -> None:
    from glossary.stats.normalize import normalize_key

    got = [c.surface for c in extract("今回の確認事項", {normalize_key("今回")})]
    assert "今回" not in got
