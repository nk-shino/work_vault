"""マスキング：対象パターンが確実に消えること。ルールごとに確かめる。"""

from __future__ import annotations

from pathlib import Path

import pytest

from glossary.preprocess.masking import Masker, MaskingLeak

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def masker() -> Masker:
    return Masker.from_yaml(ROOT / "config" / "masking_rules.yaml")


@pytest.mark.parametrize(
    "text, gone, token",
    [
        ("連絡先は sora.tatsuno@example.invalid です", "sora.tatsuno@example.invalid", "<EMAIL>"),
        ("窓口は 000-1234-5678 まで", "000-1234-5678", "<PHONE>"),
        ("窓口は 03(1234)5678 まで", "1234", "<PHONE>"),
        ("窓口は +81-00-1234-5678 まで", "1234-5678", "<PHONE>"),
        ("見積もりは1,200円でした", "1,200円", "<MONEY>"),
        ("見積もりは￥3,500でした", "3,500", "<MONEY>"),
        ("見積もりは12万円でした", "12万円", "<MONEY>"),
        ("シリアルは SN: RYU-0001-AX です", "RYU-0001-AX", "<SERIAL>"),
        ("製造番号 FLT7781ZZ を確認", "FLT7781ZZ", "<SERIAL>"),
        ("部品 KMO-3141-59 を交換", "KMO-3141-59", "<SERIAL>"),
        ("雲居さんに確認します", "雲居", "<PERSON>"),
        ("霧島です。", "霧島", "<PERSON>"),
    ],
)
def test_rule_removes_target(masker: Masker, text: str, gone: str, token: str) -> None:
    out = masker.mask(text).text
    assert gone not in out
    assert token in out


@pytest.mark.parametrize(
    "text",
    [
        "申請書は https://example.invalid/forms/0312345678 から",  # URL の中の数字も崩さない
        r"様式は \\nas-01\共有\申請書 にある",  # 共有フォルダのパス
    ],
)
def test_document_locations_are_kept(masker: Masker, text: str) -> None:
    assert masker.mask(text).text == text


@pytest.mark.parametrize(
    "text, name",
    [
        ("星見部長の承認が必要", "星見"),
        ("雲居さんが担当している", "雲居"),
        ("窓口は霧島さんです", "霧島"),
        ("担当：田中", "田中"),
    ],
)
def test_names_with_roles_are_kept(masker: Masker, text: str, name: str) -> None:
    # 誰に聞けばよいかという情報なので、役割と一緒に出る名前は残す
    assert name in masker.mask(text).text


def test_names_without_roles_are_still_masked(masker: Masker) -> None:
    out = masker.mask("昨日、雲居さんに確認した。\n担当：星見\n田中が来た").text
    # 2行目の「担当」は3行目の田中には効かない（同じ行の中だけを見る）
    assert "雲居" not in out and "星見" in out and "田中" not in out


def test_pos_rule_masks_dictionary_person_name(masker: Masker) -> None:
    # 敬称も名乗りも無い位置の人名は、SudachiPy の品詞（固有名詞・人名）で拾う
    out = masker.mask("昨日は田中が現場に来た").text
    assert "田中" not in out and "<PERSON>" in out


@pytest.mark.parametrize(
    "text", ["皆さんへ共有します", "仕様様式の変更", "変更点は\n新しい仕様です。", "同様の手順"]
)
def test_does_not_mask_non_names(masker: Masker, text: str) -> None:
    assert "<PERSON>" not in masker.mask(text).text


def test_self_intro_only_on_first_line(masker: Masker) -> None:
    out = masker.mask("霧島です。\n竜舎の点検です。").text
    assert out.startswith("<PERSON>です。") and "竜舎の点検です。" in out


def test_glossary_terms_survive(masker: Masker) -> None:
    # 用語集が欲しい語まで消えては意味が無い
    text = "星読み台帳にMGKの結果を記入し、FLT点検の予定を立てる。"
    out = masker.mask(text).text
    for word in ("星読み台帳", "MGK", "FLT点検"):
        assert word in out


def test_counts_per_rule(masker: Masker) -> None:
    result = masker.mask("a@example.invalid と b@example.invalid に 1,000円")
    assert result.counts["email"] == 2
    assert result.counts["money"] == 1


def test_leak_check_raises(masker: Masker) -> None:
    with pytest.raises(MaskingLeak):
        masker.assert_clean("残っている a@example.invalid")


def test_rule_can_be_added_without_code_change(tmp_path: Path) -> None:
    rules = tmp_path / "rules.yaml"
    rules.write_text(
        "rules:\n"
        "  - name: badge\n"
        "    type: regex\n"
        "    pattern: 'ID[0-9]{4}'\n"
        "    token: '<BADGE>'\n",
        encoding="utf-8",
    )
    out = Masker.from_yaml(rules).mask("入館証 ID1234 を返却").text
    assert out == "入館証 <BADGE> を返却"
