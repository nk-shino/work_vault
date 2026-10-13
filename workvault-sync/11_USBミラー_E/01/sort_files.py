# -*- coding: utf-8 -*-
"""
================================================================
 共有フォルダ 仕分けスクリプト

----------------------------------------------------------------

 作成日 : 2026-07-31
 用途   : 在庫管理手順に関する確認内容フォルダ内のファイルを
          分類フォルダへ振り分ける。

 安全設計 :
   1) 既定は DRY_RUN（何もせずログだけ出す）
   2) 既定は copy（原本を残す）
   3) 分類不明なものは _未分類 へ。推測で振り分けない
   4) 同名ファイルが存在する場合は上書きせずスキップ

 使い方 :
   > python sort_files.py
   まず DRY_RUN=True で実行 → ログ確認 → DRY_RUN=False で本実行
================================================================
"""

import os
import re
import csv
import shutil
import sys
from pathlib import Path
from datetime import datetime

# ============================================================
# 設定  ★ここだけ触る
# ============================================================

SRC = Path(r"E:\在庫管理システム関連データ")

DST = Path("E:/")          # 仕分け先。SRC と同じにすればその場で整理される

DRY_RUN = True             # True = 何もしない（ログのみ）  ★最初は必ず True
MODE    = "copy"           # "copy" = 原本を残す（推奨） / "move" = 原本を移動

WORK = "B列上書き_20260731"


# ============================================================
# 分類ルール（完全一致）  ファイル名 : 振り分け先
# ============================================================
EXACT = {

    # ---------- 参照・削除禁止（代替不可の一次資料）----------

    "Module1.bas":                                    "_参照_削除禁止",
    "Module2.bas":                                    "_参照_削除禁止",
    "Module3.bas":                                    "_参照_削除禁止",
    "PrintBarCode.bas":                               "_参照_削除禁止",
    "S1.cls":                                         "_参照_削除禁止",
    "tmp_sql.txt":                                    "_参照_削除禁止",
    "強制移動.txt":                                    "_参照_削除禁止",
    "在庫データ取得.txt":                              "_参照_削除禁止",
    "実棚卸データ取得SQL.txt":                         "_参照_削除禁止",
    "pp.pdf":                                         "_参照_削除禁止",
    "固定テーブル　棚卸し方法.pptx":                    "_参照_削除禁止",
    "セットアップレポート計算機原本.xlsm":              "_参照_削除禁止",
    "【本番環境】_EGPro使用実績訂正メンテツール_1_0_1.xlsm": "_参照_削除禁止",

    # ---------- 過去データ（隔離。消さない）----------

    "2026_07_22_171922_EGProWhereHouse.csv":          "_過去データ_使用禁止",
    "2026_07_22_171934_EGProWhereHouse.csv":          "_過去データ_使用禁止",
    "2026_07_24_155814_EGProWhereHouse.csv":          "_過去データ_使用禁止",
    "2026_07_30_112331_EGProWhereHouse.csv":          "_過去データ_使用禁止",
    "2026_07_31_131912_EGProWhereHouse.csv":          "_過去データ_使用禁止",
    "2026_07_21_143848_EGTanaoroshi.csv":             "_過去データ_使用禁止",
    "2026_07_23_094110_EGTanaoroshi.csv":             "_過去データ_使用禁止",
    "2026_07_29_163413_EGTanaoroshi.csv":             "_過去データ_使用禁止",
    "(棚卸し結果)2026_03_30_135244_EGTanaoroshi.csv":  "_過去データ_使用禁止",
    "L2セットアップレポート　20260729.csv":            "_過去データ_使用禁止",
    "L3セットアップレポート　20260728.csv":            "_過去データ_使用禁止",
    "EGProInventory_20241029.log":                    "_過去データ_使用禁止",
    "Bef-不足部品リスト作成(AED)_ver6.xlsm":           "_過去データ_使用禁止",
    "Aft-不足部品リスト作成(AED)_ver6 - コピー.xlsm":  "_過去データ_使用禁止",

    # ---------- AI生成・要検証（根拠に使わない）----------

    "AED_B列_EGPro突合マスター_20260730.csv":                          "_AI生成_要検証",
    "現場在庫とEG-Pro在庫のずれに関する調査メモ_V3.md":                 "_AI生成_要検証",
    "現場在庫とEG-Pro在庫のずれに関する調査メモ_最新版.md":             "_AI生成_要検証",
    "現場在庫とEG-Pro在庫の差異の出し方_調査レポート_V1.md":            "_AI生成_要検証",
    "現場在庫とEG-Pro在庫の差異解消手順に関する調査メモ_V4.md":         "_AI生成_要検証",
    "20260727_セットアップレポート検証準備書.md":                        "_AI生成_要検証",
    "xlsm_candidate_investigation_results_20260730_044015.docx":        "_AI生成_要検証",
    "EGPro_AED_差異調査_再生成版":                                      "_AI生成_要検証",
    "EGPro_AED_引継ぎ資料":                                            "_AI生成_要検証",
    "EGPro_AED_完全引継ぎ_再生成版.zip":                                "_AI生成_要検証",
    "EGPro_AED_差異調査_完全引継ぎ_再生成版.zip":                       "_AI生成_要検証",
    "EGPro_AED_差異調査_完全引継ぎ_再生成版_MODIFIED.zip":              "_AI生成_要検証",

    # ---------- 他機種（今回は触らない）----------

    "不足部品リスト作成(NKV)_ver6.xlsm":               "_他機種_参考",
    "不足部品リスト作成(TEC1000)_ver6.xlsm":           "_他機種_参考",
    "不足部品リスト作成(TEC5600)_ver6.xlsm":           "_他機種_参考",
    "不足部品リスト作成(送信機)_ver6.xlsm":            "_他機種_参考",
    "AED_NPM検索用.csv":                               "_他機種_参考",
    "NKV_NPM検索用.csv":                               "_他機種_参考",
    "TEC-1000_NPM検索用.csv":                          "_他機種_参考",
    "TEC-5600_NPM検索用.csv":                          "_他機種_参考",
    "L2送信機_NPM検索用.csv":                          "_他機種_参考",
    "送信機_NPM検索用.csv":                            "_他機種_参考",
    "セットアップレポート計算機TEC56 (1).xlsm":        "_他機種_参考",
    "セットアップレポート計算機 - コピー.xlsm":        "_他機種_参考",

    # ---------- 別件（手順書リファクタリング案件）----------

    "WIPジョブ作成手順書.docx":                        "_別件_手順書関係",
    "3_ジョブ作成手順書.docx":                         "_別件_手順書関係",
    "3_ジョブ作成手順書_改.docx":                      "_別件_手順書関係",
    "3_ジョブ作成手順書_改.pdf":                       "_別件_手順書関係",
    "[WIP]3_ジョブ作成手順書_改.docx":                 "_別件_手順書関係",
    "[WIP]4_ジョブ作成手順書_改_色統一.docx":          "_別件_手順書関係",
    "[WIP]5_ジョブ作成手順書_改_色統一v2.docx":        "_別件_手順書関係",
    "手順書_記法仕様書_v1.0.md":                       "_別件_手順書関係",
    "記法仕様書_v1.1.md":                              "_別件_手順書関係",
    "記法仕様書_v1.2.md":                              "_別件_手順書関係",
    "色判定結果一覧_レビュー用.md":                     "_別件_手順書関係",
    "着色テキスト網羅リスト_v1.0.md":                   "_別件_手順書関係",
    "手順書画像_注釈指示書_v0.1.md":                    "_別件_手順書関係",
    "手順書画像素材_自動生成_v0.1.pptx":                "_別件_手順書関係",
    "手順書画像_抽出":                                 "_別件_手順書関係",
    "_annots.json":                                    "_別件_手順書関係",
    "_img_records.json":                               "_別件_手順書関係",
    "_prompts.json":                                   "_別件_手順書関係",
    "_精査用セグメント一覧.txt":                        "_別件_手順書関係",
    "反映レポート.md":                                 "_別件_手順書関係",
    "反映レポート_v5.md":                              "_別件_手順書関係",
    "プロンプト作成手順書_v1.0.docx":                   "_別件_手順書関係",
    "複合機表示名変更手順書.docx":                      "_別件_手順書関係",
    "setup-guide.md":                                  "_別件_手順書関係",
    "color_palette_compare_v2.png":                    "_別件_手順書関係",
    "color_palette_preview.png":                       "_別件_手順書関係",
    "std_tone_preview_v5.png":                         "_別件_手順書関係",

    # ---------- 判断保留（中身を見ないと分類できない）----------

    "リール消費マクロ.xlsm":                           "_判断保留",
    "スプライシング解除・在庫修正手順.pptx":            "_判断保留",
    "ラベル再発行マクロ.xlsm":                         "_判断保留",
    "怪しい部品.xlsx":                                 "_判断保留",
    "移動部品分割台帳 - コピー.xlsx":                  "_判断保留",
    "リール巻き数検証の対象シリアル一覧.xlsx":          "_判断保留",
    "EGPro差異確認まとめ.xlsx":                        "_判断保留",
    "EGPro必要在庫計算シート - コピー.xlsx":           "_判断保留",
    "math-不足部品リスト作成(AED)_ver6 - コピー - コピー.xlsm": "_判断保留",
    "4_リファクタリング作業手順書_v1.1.docx":          "_判断保留",
    "260604-101.csv":                                  "_判断保留",
    "①T_ピッキング_Tmp生成.sql":                       "_判断保留",
    "②T_ピック用データ_Tmp生成.sql":                   "_判断保留",
    "③SP_ピッキングTmp.sql":                           "_判断保留",
    "業務内容 棚卸表（佐藤）.xlsx":                     "_判断保留",
    "棚カウント済シール.xlsx":                          "_判断保留",
    "NEW_NPM_Search - ショートカット.lnk":              "_判断保留",
    "不足部品リスト関係 - ショートカット.lnk":          "_判断保留",
    "不足部品リスト関係.lnk":                          "_判断保留",

    # ---------- 削除候補（重複・不完全）----------

    "固定テーブル　棚卸し方法 - コピー.pptx":          "_削除候補",
    "固定テーブル　棚卸し方法 - コピー.pdf":           "_削除候補",
    "不足部品リスト作成(AED)_ver6 - コピー.xlsm":      "_削除候補",
    "不足部品リスト作成(AED)_ver6 - コピー - コピー.xlsm": "_削除候補",
    "2026_07_21_143053_EGTanaoroshi.csv.crdownload":   "_削除候補",
    "zip_temp":                                        "_削除候補",
    "temp_extract":                                    "_削除候補",
    "色統一":                                          "_削除候補",

    # ---------- 作業対象（本体）----------

    "不足部品リスト作成(AED)_ver6.xlsm":               WORK + "/04_作業中",

    # ---------- ツール ----------

    "B列上書き値_生成.py":                             WORK + "/99_ツール",
    "create_folders.py":                               WORK + "/99_ツール",
    "sort_files.py":                                   WORK + "/99_ツール",
}


# ============================================================
# 分類ルール（パターン）  上から順に評価
# ============================================================
PATTERNS = [
    (r"^Sheet\d+\.cls$",                          "_参照_削除禁止"),
    (r"^WIP-作業手順書運用ルール.*\.md$",          "_別件_手順書関係"),
    (r"^SharePoint完成イメージ_モック.*\.html$",   "_別件_手順書関係"),
    (r"^ルール適用プレビュー_v.*\.html$",          "_別件_手順書関係"),
    (r"^v5_.*\.html$",                             "_別件_手順書関係"),
    # 当日取得ぶんは作業フォルダへ
    (r"^L3セットアップレポート.*20260731\.csv$",   WORK + "/01_入力_当日取得"),
    (r"^2026_07_31_\d{6}_EGProWhereHouse\.csv$",  WORK + "/01_入力_当日取得"),
    # 突合スクリプトの出力
    (r"^B列上書き値_\d{8}_\d{4}\.csv$",           WORK + "/03_出力_突合結果"),
    (r"^B列上書き_欠落シリアル_.*\.csv$",          WORK + "/03_出力_突合結果"),
    (r"^B列上書き_判定サマリ_.*\.txt$",            WORK + "/03_出力_突合結果"),
    # 退避
    (r"^AB列退避_.*\.xlsx$",                       WORK + "/02_退避"),
    (r"^不足部品リスト作成\(AED\)_ver6_bak_.*\.xlsm$", WORK + "/02_退避"),
]

UNKNOWN = "_未分類"   # ルールに無いものは全部ここ。推測しない


# ============================================================
def classify(name):
    """ファイル名から振り分け先を決める。決まらなければ UNKNOWN。"""
    if name in EXACT:
        return EXACT[name], "完全一致"
    for pat, dest in PATTERNS:
        if re.match(pat, name):
            return dest, "パターン:" + pat
    return UNKNOWN, "ルールなし"


def main():
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("=" * 64)
    print(" 共有フォルダ 仕分けスクリプト")
    print(" 実行日時 : " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print(" 元       : %s" % SRC)
    print(" 先       : %s" % DST)
    print(" モード   : %s" % ("下見のみ（DRY RUN）" if DRY_RUN else MODE))
    print("=" * 64)

    if not SRC.exists():
        print("[中止] 元フォルダにアクセスできません。")
        print("       パス・ネットワーク接続・アクセス権を確認してください。")
        input("\nEnterキーで終了します...")
        sys.exit(1)

    if not DST.exists():
        print("[中止] 仕分け先が見つかりません: %s" % DST)
        input("\nEnterキーで終了します...")
        sys.exit(1)

    entries = sorted(os.listdir(SRC))
    rows = []
    stat = {}

    for name in entries:
        src_path = SRC / name

        # ログ・スクリプト自身は対象外
        if name.startswith("_仕分けログ_"):
            continue

        dest_rel, why = classify(name)
        dest_dir = DST / dest_rel
        dest_path = dest_dir / name

        kind = "フォルダ" if src_path.is_dir() else "ファイル"
        result = ""

        if DRY_RUN:
            result = "下見"
        else:
            try:
                dest_dir.mkdir(parents=True, exist_ok=True)
                if dest_path.exists():
                    result = "スキップ（同名あり）"
                else:
                    if MODE == "move":
                        shutil.move(str(src_path), str(dest_path))
                        result = "移動"
                    else:
                        if src_path.is_dir():
                            shutil.copytree(str(src_path), str(dest_path))
                        else:
                            shutil.copy2(str(src_path), str(dest_path))
                        result = "コピー"
            except Exception as e:
                result = "エラー: %s" % e

        rows.append([name, kind, dest_rel, why, result])
        stat[dest_rel] = stat.get(dest_rel, 0) + 1

    # ---- 集計表示 ----

    print("\n【振り分け先ごとの件数】")
    for k in sorted(stat, key=lambda x: (-stat[x], x)):
        mark = "  ★要確認" if k == UNKNOWN else ""
        print("  %-28s %4d 件%s" % (k, stat[k], mark))
    print("  " + "-" * 40)
    print("  %-28s %4d 件" % ("合計", len(rows)))

    # ---- 未分類の一覧 ----

    unknown = [r[0] for r in rows if r[2] == UNKNOWN]
    if unknown:
        print("\n【_未分類（ルールに無かったもの）】")
        for u in unknown:
            print("  " + u)
        print("\n  ※これらは推測で振り分けていません。中身を確認してください。")

    # ---- ログ出力 ----

    log = DST / ("_仕分けログ_%s.csv" % stamp)
    try:
        with open(log, "w", encoding="cp932", newline="", errors="replace") as f:
            w = csv.writer(f)
            w.writerow(["ファイル名", "種別", "振り分け先", "判定根拠", "結果"])
            w.writerows(rows)
        print("\nログ出力 : %s" % log)
    except Exception as e:
        print("\n[警告] ログ出力に失敗: %s" % e)

    if DRY_RUN:
        print("\n" + "=" * 64)
        print(" 下見モードのため、ファイルには一切触れていません。")
        print(" 内容を確認し、問題なければ DRY_RUN = False にして再実行してください。")
        print("=" * 64)

    print()
    input("Enterキーで終了します...")


if __name__ == "__main__":
    main()
