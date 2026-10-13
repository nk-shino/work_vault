"""表記ゆれの名寄せ：揺れの種類ごとに、同じキーに寄ることを確かめる。"""

from __future__ import annotations

import pytest

from glossary.stats.normalize import hira_to_kata, normalize_key, normalize_surface


@pytest.mark.parametrize(
    "a, b",
    [
        ("ＭＧＫ", "MGK"),  # 全角・半角
        ("ｽｶｲﾎﾟｽﾄ", "スカイポスト"),  # 半角カナ
        ("mgk", "MGK"),  # 大文字・小文字
        ("すかいぽすと", "スカイポスト"),  # ひらがな・カタカナ
        ("サーバー", "サーバ"),  # 末尾の長音符
        ("サーバ－", "サーバ"),  # 長音の代わりに全角ハイフン
        ("打合せ", "打ち合わせ"),  # 送り仮名
        ("取扱い", "取り扱い"),  # 送り仮名
    ],
)
def test_same_key(a: str, b: str) -> None:
    assert normalize_key(a) == normalize_key(b)


@pytest.mark.parametrize("a, b", [("竜舎", "竜車"), ("浮遊石", "浮遊島")])
def test_different_words_stay_apart(a: str, b: str) -> None:
    # 読みが同じでも漢字が違えば別の語。ここを寄せると「混同注意」の対象が消える
    assert normalize_key(a) != normalize_key(b)


def test_long_vowel_inside_word_is_kept() -> None:
    assert normalize_surface("スーパー") == "スーパ"
    assert "ー" in normalize_surface("スーパー")


def test_hira_to_kata() -> None:
    assert hira_to_kata("りゅうしゃ") == "リュウシャ"
