# -*- coding: utf-8 -*-
"""回帰テスト（合成データ・個人情報なし）。v3 前処理・採点パイプラインの検証。

検証項目:
  ① 役割語に隣接する人名がマスクされる（keep 廃止の確認）
  ② 敬称直前の人名がマスクされる
  ③ URL / file:// / UNC 共有パスがマスクされる
  ④ マスクトークンが用語候補として抽出されない
  ⑤ 罫線・「〜書きました」行で本文が打ち切られない（Cleaner 未適用の確認）
  ⑥ 7桁以上の数字で漏えいゲートが発火する
  ⑦ 不透明IDの安定性（同一パス→同一ID・接頭辞・16桁16進）
  ⑧ R1: 疑わしい語を含む抜粋は用例検査で除外される（素のsnippetには残る=RED、
     検査つきsnippetはNone=GREEN・安全な用例が無い候補は用例0で検出）
  ⑨ R2: 合成DBで正常登録はcommit・不一致はrollback（DB不変）
  ⑩ minor: 入力内容の SHA-256 は安定して計算でき、内容変更は承認照合で拒否される
  ⑪ R1修正1: 候補検査と用例検査で敬称・役職語の集合が一致する（ちゃん・監査役）

使い方: glossary_venv の python で PYTHONIOENCODING=utf-8 を付けて実行する。
人名には実在しない組み合わせの一般的な姓のみを使う（個人情報は含まない）。
"""
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import collect_scope2 as cs  # noqa: E402
import run_score2 as rs  # noqa: E402

# 標準出力のUTF-8化は collect_scope2 側のラップに任せる（二重ラップを避ける）

from glossary.preprocess.masking import Masker  # noqa: E402
from glossary.preprocess.pipeline import MaskedDocument  # noqa: E402
from glossary.propose import Outcome, snippet as orig_snippet  # noqa: E402
from glossary.stats.candidates import extract, load_stopwords  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy import text as sa_text  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402


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

    # ⑧ R1: 疑わしい語を含む抜粋の用例検査（RED→GREEN）
    # 素の snippet には人名＋役割がそのまま残る（修正前はこのまま DB へ保存され得た）
    leak_text = "スミス部長の指示でノズルを交換した。"
    raw = orig_snippet(leak_text, "ノズル")
    red_ok = raw is not None and "スミス部長" in raw          # 漏えい経路の存在確認（RED根拠）
    v = rs.snippet_privacy_verdict(raw) if raw else None
    green_verdict = v is not None and "人名" in v             # 用例検査が検出する
    safe_fn = rs.make_safe_snippet(orig_snippet)
    green_masked = safe_fn(leak_text, "ノズル") is None        # 疑わしい抜粋は返さない
    normal = safe_fn("ノズルを交換した。記録を残す。", "ノズル")
    green_normal = normal is not None and "ノズル" in normal   # 正常な抜粋はそのまま
    doc = MaskedDocument("doc:0123456789abcdef", datetime.now(timezone.utc),
                         "doc:0123456789abcdef", leak_text)
    n_safe, drop_reasons = rs.safe_evidence_stats("ノズル", [doc])
    green_noevidence = n_safe == 0 and sum(drop_reasons.values()) == 1  # 用例0で検出
    results["8_用例検査(R1)"] = red_ok and green_verdict and green_masked and green_normal and green_noevidence
    details["8_用例検査(R1)"] = (f"素のsnippetに残る={red_ok} 判定={green_verdict} "
                                 f"除外={green_masked} 正常保持={green_normal} 用例0={green_noevidence}")

    # ⑨ R2: 合成DBでのトランザクション検証（正常登録=commit・不一致=rollback）
    def make_session(name):
        p = os.path.join(cs.TMP, name)
        if os.path.exists(p):
            os.remove(p)
        eng = create_engine(f"sqlite:///{p}", future=True)
        with eng.begin() as c:
            c.execute(sa_text("CREATE TABLE proposals (id integer primary key, status text)"))
        return sessionmaker(bind=eng, future=True)()

    def fake_propose(n_insert, proposed, auto=0, ev=0):
        def _f(db, llm, cands, docs, limit=None, rules=None, send_masker=None):
            for _ in range(n_insert):
                db.execute(sa_text("INSERT INTO proposals (status) VALUES ('pending')"))
            return Outcome(proposed=proposed, auto_adopted=auto, evidence_added=ev)
        return _f

    def count_rows(db):
        return db.execute(sa_text("SELECT count(*) FROM proposals")).scalar()

    db_ok = make_session("test_r2_ok.db")
    ok1, _, _ = rs.register_with_verification(
        db_ok, fake_propose(2, 2), [{}, {}], [], rules=None, send_masker=None, llm=None)
    committed = count_rows(db_ok) == 2
    db_ng = make_session("test_r2_ng.db")
    ok2, _, _ = rs.register_with_verification(
        db_ng, fake_propose(1, 1), [{}, {}], [], rules=None, send_masker=None, llm=None)
    rolled_back = count_rows(db_ng) == 0        # rollback 後も DB は空のまま
    db_auto = make_session("test_r2_auto.db")
    ok3, _, _ = rs.register_with_verification(
        db_auto, fake_propose(2, 2, auto=1), [{}, {}], [], rules=None, send_masker=None, llm=None)
    rolled_back_auto = count_rows(db_auto) == 0
    results["9_トランザクション検証(R2)"] = ok1 and committed and (not ok2) and rolled_back \
        and (not ok3) and rolled_back_auto
    details["9_トランザクション検証(R2)"] = (f"正常登録={ok1}/{committed} 不一致rollback={(not ok2) and rolled_back} "
                                             f"自動採用rollback={(not ok3) and rolled_back_auto}")

    # ⑩ minor: 入力内容の SHA-256 は安定して計算でき、内容変更は承認照合で拒否される
    p = os.path.join(cs.TMP, "test_content_hash.txt")
    with open(p, "w", encoding="utf-8") as f:
        f.write("hash test")
    h1, h2 = rs.content_sha256(p), rs.content_sha256(p)
    ap = os.path.join(cs.TMP, "test_approved_input.json")
    rs.save_approved_input(p, "test", ap)
    ok_match = rs.approved_input_matches(p, ap)          # 同一内容は承認される
    with open(p, "w", encoding="utf-8") as f:
        f.write("tampered content")
    ok_reject = not rs.approved_input_matches(p, ap)     # 内容変更は拒否される
    results["10_内容ハッシュ(minor)"] = (h1 == h2 and len(h1) == 64
                                         and ok_match and ok_reject)
    details["10_内容ハッシュ(minor)"] = (f"安定={h1 == h2} 長さ={len(h1)} "
                                         f"同一内容承認={ok_match} 内容変更拒否={ok_reject}")

    # ⑪ R1修正1: 候補検査と用例検査で敬称・役職語の集合が一致する（ちゃん・監査役）
    ok_a = (rs.privacy_flag("サンプルちゃん") == "敬称結合"
            and rs.privacy_flag("サンプル監査役") == "敬称結合")   # (a) 候補検査で除外
    t_chan = "サンプルちゃんの設定変更でノズルを交換した。"
    t_kansa = "サンプル監査役の指示でノズルを交換した。"
    safe_fn2 = rs.make_safe_snippet(orig_snippet)
    # (b) 素の snippet には結合語が残る（RED根拠）が、検査つき snippet は除外する
    ok_b = (orig_snippet(t_chan, "ノズル") is not None
            and safe_fn2(t_chan, "ノズル") is None
            and orig_snippet(t_kansa, "ノズル") is not None
            and safe_fn2(t_kansa, "ノズル") is None)
    # (c) 正常文の抜粋は保持される
    ok_c = safe_fn2("ノズルを交換した。記録を残す。", "ノズル") is not None
    results["11_敬称群一致(R1修正1)"] = ok_a and ok_b and ok_c
    details["11_敬称群一致(R1修正1)"] = f"候補除外={ok_a} 抜粋除外={ok_b} 正常保持={ok_c}"

    passed = sum(1 for v in results.values() if v)
    print(f"tests: {passed}/{len(results)} passed")
    for name in sorted(results):
        mark = "PASS" if results[name] else "FAIL"
        print(f"  {mark}  {name}  ({details[name]})")
    if passed != len(results):
        sys.exit(1)


if __name__ == "__main__":
    main()
