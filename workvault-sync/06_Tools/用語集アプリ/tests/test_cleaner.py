from __future__ import annotations

from pathlib import Path

from glossary.preprocess.cleaner import Cleaner

ROOT = Path(__file__).resolve().parents[1]
MAIL = """霧島さん

お疲れ様です。
雲居です。

浮遊石のFLT点検は来週です。
> 前のメールの引用行
点検手順は共有フォルダにあります。

よろしくお願いいたします。

--
雲居 ほし
浮遊島 第2竜舎

このメールは機密情報を含む場合があります。誤って届いた場合は破棄してください。
"""


def test_clean_removes_boilerplate() -> None:
    out = Cleaner.from_yaml(ROOT / "config" / "cleaning_rules.yaml").clean(MAIL)
    assert "浮遊石のFLT点検は来週です。" in out
    assert "点検手順は共有フォルダにあります。" in out
    for gone in ("霧島さん", "お疲れ様です", "引用行", "よろしくお願い", "第2竜舎", "機密"):
        assert gone not in out


def test_disclaimer_paragraph_is_dropped_even_before_signature() -> None:
    text = "本文です。\n\n本メールは宛先以外の方が受け取った場合は削除してください。\n\n続きの本文。"
    out = Cleaner.from_yaml(ROOT / "config" / "cleaning_rules.yaml").clean(text)
    assert out == "本文です。\n\n続きの本文。"


def test_english_reply_header_cuts_rest() -> None:
    text = "本文です。\nOn Mon, 1 Apr 2031 someone wrote:\n古い本文"
    assert Cleaner.from_yaml(ROOT / "config" / "cleaning_rules.yaml").clean(text) == "本文です。"
