# -*- coding: utf-8 -*-
"""回帰テスト（合成データ・個人情報なし）。v2 前処理パイプラインの検証。

検証項目:
  ① 役割語に隣接する人名がマスクされる（keep 廃止の確認）
  ② 敬称直前の人名がマスクされる
  ③ URL / file:// / UNC 共有パスがマスクされる
  ④ マスクトークンが用語候補として抽出されない
  ⑤ 罫線・「〜書きました」行で本文が打ち切られない（Cleaner 未適用の確認）
  ⑥ 7桁以上の数字で漏えいゲートが発火する
  ⑦ 不透明IDの安定性（同一パス→同一ID・接頭辞・16桁16進）

使い方: glossary_venv の python で PYTHONIOENCODING=utf-8 を付けて実行する。
人名には実在しない組み合わせの一般的な姓のみを使う（個人情報は含まない）。
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collect_scope2 as cs  # noqa: E402

# 標準出力のUTF-8化は collect_scope2 側のラップに任せる（二重ラップを避ける）

from glossary.preprocess.masking import Masker  # noqa: E402
from glossary.stats.candidates import extract, load_stopwords  # noqa: E402


def main() -> None:
    masker = Masker.from_yaml(Path(cs.ensure_mask_config()))
    results: dict[str, bool] = {}
    details: dict[str, str] = {}

    # ① 役割語に隣接する人名がマスクされる（v1 では keep_after で残っていた形）
    text = "山田が担当です。進捗を確認します。"
    out, reason, _ = cs.process_document(text, masker)
    ok = (reason is None and out is not None
          and "<PERSON>が担当" in out and "山田" not in out)
    results["1_役割文脈の人名マスク"] = ok
    details["1_役割文脈の人名マスク"] = f"reason={reason}"

    # ② 敬称直前の人名がマスクされる
    text = "鈴木さんに依頼する。"
    out, reason, _ = cs.process_document(text, masker)
    ok = (reason is None and out is not None
          and "<PERSON>さん" in out and "鈴木" not in out)
    results["2_敬称直前の人名マスク"] = ok
    details["2_敬称直前の人名マスク"] = f"reason={reason}"

    # ③ URL / file:// / UNC 共有パスがマスクされる
    text = ("資料は https://intra.example.co.jp/manual/q.pdf にある。"
            "社内の手順は file://filesv01/pub/手順.pdf、"
            "共有は \\\\filesv01\\共有\\手順書.pdf を使う。")
    out, reason, _ = cs.process_document(text, masker)
    ok = (reason is None and out is not None
          and "<URL>" in out and "<PATH>" in out
          and "https://" not in out and "file://" not in out
          and "filesv01" not in out)
    results["3_URLと共有パスのマスク"] = ok
    details["3_URLと共有パスのマスク"] = f"reason={reason}"

    # ④ マスクトークンが用語候補として抽出されない
    masked_sample = ("印刷機のノズルを交換する。担当は<PERSON>、"
                     "資料は<URL>と<PATH>、連絡先は<EMAIL>、型番は<SERIAL>。")
    stop = load_stopwords(Path(cs.APP) / "config" / "stopwords.txt")
    cands = extract(masked_sample, stop)
    bad = [c for c in cands
           if "<" in c.surface or ">" in c.surface or "<" in c.key or ">" in c.key]
    results["4_マスクトークンが候補にならない"] = len(bad) == 0
    details["4_マスクトークンが候補にならない"] = f"候補{len(cands)}件・違反{len(bad)}件"

    # ⑤ 罫線・「〜書きました」行で本文が打ち切られない（Cleaner 未適用の確認）
    text = ("手順書の抜粋です。\n"
            "----\n"
            "この区切り行の後も本文が続きます。電源スイッチを押します。\n"
            "この手順は前任者が書きました。\n"
            "打ち切られないことを確認する最終行です。点検完了。")
    out, reason, _ = cs.process_document(text, masker)
    ok = (reason is None and out is not None
          and "電源スイッチを押します。" in out and "点検完了。" in out)
    results["5_本文打ち切りなし"] = ok
    details["5_本文打ち切りなし"] = f"reason={reason}"

    # ⑥ 7桁以上の数字で漏えいゲートが発火する
    text = "管理コードは1234567です。"
    out, reason, _ = cs.process_document(text, masker)
    ok = reason == "digit7" and out is None
    results["6_7桁ゲート発火"] = ok
    details["6_7桁ゲート発火"] = f"reason={reason}"

    # ⑦ 不透明IDの安定性（同一パス→同一ID・別パス→別ID・doc: 接頭辞・16桁16進）
    id1 = cs.opaque_id(r"C:\Sample\Dir\File.md")
    id2 = cs.opaque_id("c:/sample/dir/file.md")   # 大小と区切り文字の違いは同一視
    id3 = cs.opaque_id(r"C:\Sample\Dir\Other.md")
    suffix = id1.removeprefix("doc:")
    ok = (id1 == id2 and id1 != id3 and id1.startswith("doc:")
          and len(suffix) == 16 and int(suffix, 16) >= 0)
    results["7_不透明IDの安定性"] = ok
    details["7_不透明IDの安定性"] = f"別パス衝突={id1 == id3}"

    passed = sum(1 for v in results.values() if v)
    print(f"tests: {passed}/{len(results)} passed")
    for name in sorted(results):
        mark = "PASS" if results[name] else "FAIL"
        print(f"  {mark}  {name}  ({details[name]})")
    if passed != len(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
