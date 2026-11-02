# -*- coding: utf-8 -*-
"""corr_lnb_21_wording.py — 解決報告 §7 の文言更新(相関図シート C7〜C10)をドライラン冊へ適用。
原本へは corr_lnb_20 のシート複製で運ばれるため、本スクリプトは temp のドライラン冊が既定対象。
方針: 既存の確定事項(出典·事象別図のdrawio残置)は消さず、図の変更に追従する部分のみ更新する。
  C7 確定/推定の区別へ(Pana-CIM冊の前置きに揃える·出典は維持+実機確認を追加)
  C8 凡例を Stage 5 の分類色体系へ(旧【表示】は廃止·【外部】を追加)
  C9 線種と出典符の定義(図内の出典符 T1/T1b/T2/T3)
  C10 A4縦→A4横1頁·Pana-CIM Stage 5 からの複製元を明記·機器アイコンの補助表記を追加
Assert: 現行値が解決報告§7の想定(調査時の旧文言)と完全一致しなければ書き換えないで停止。
"""
import json
import os
import sys
import time
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WORK = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\corr_lnb_work"
DRY = os.path.join(WORK, "corr_dryrun_lnb.xlsx")
RESULT = os.path.join(HERE, "corr_lnb_21_wording_result.json")
SHEET = "相関図"

OLD = {
    "C7": "確定事項のみ記載。出典：公式資料・操作手順書 0494-912039(06)・会議記録。暫定・未確認の経路は含まない",
    "C8": "凡例：【サーバ】=サーバー(VM含む)／【端末(PC)】=作業員が操作するPC／【設備】=製造設備／【表示】=画面・表示装置",
    "C9": "　　　【保存領域】=ファイル保存場所。色: 青=サーバ・表示系／黄=PC・操作端末／緑=設備・データ保存",
    "C10": "配置：A4縦1頁。事象別の図(アンドン・稼働モニタ異常/月次再起動/異常時再起動)は確実構成図.drawioに残置",
}
NEW = {
    "C7": "確定事項と推定事項を区別して記載する。実線=確定／グレー破線=推定(未確認)。出典：公式資料・操作手順書 0494-912039(06)・会議記録・実機確認。",
    "C8": "凡例：青=サーバ系(サーバー・ハイパーバイザ・VM含む)／黄=端末系(PC・表示端末)／緑=設備系(ライン・現場装置・データ保存域)／白抜き=外部(管理境界の外)／グレー破線枠=推定(当Siteで未確認)",
    "C9": "　　　線：実線=確定・破線=推定(要確認)・矢頭=データの向きが確定。出典符：T1=PanaCIM-EE仕様説明書 A680-004624(00)・T1b=社内確定資料・実機確認・T2=現場確認済み運用・T3=会議ホワイトボード(2026-10-14・証跡ではない)",
    "C10": "配置：A4横1頁(縮小率約85%)。Pana-CIM管理手順書の相関図(Stage 5・2026-10-28確定)と同一の図(2026-11-02複製)。機器アイコン(濃灰単色)は機器種の補助表記。事象別の図(アンドン・稼働モニタ異常/月次再起動/異常時再起動)は確実構成図.drawioに残置",
}
ORDER = ["C7", "C8", "C9", "C10"]

out = {"ok": False, "target": DRY, "pid": None, "before": {}, "after": {},
       "assert_fails": [], "errors": []}

import win32com.client
import win32process

xl = win32com.client.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
out["pid"] = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
print("EXCEL PID", out["pid"], flush=True)


def quit_and_cleanup():
    try:
        xl.Quit()
    except Exception as e:
        out["errors"].append(("quit: %r" % e)[:80])
    time.sleep(2)
    try:
        chk = subprocess.run(["tasklist", "/FI", "PID eq %d" % out["pid"]],
                             capture_output=True, text=True)
        if "EXCEL" in chk.stdout.upper():
            subprocess.run(["taskkill", "/PID", str(out["pid"]), "/F"], capture_output=True)
            out["cleanup"] = "killed residual %d" % out["pid"]
    except Exception as e:
        out["errors"].append(("cleanup: %r" % e)[:80])


try:
    wb = xl.Workbooks.Open(DRY)
    ws = wb.Worksheets(SHEET)
    out["A6_heading"] = str(ws.Range("A6").Value)
    for c in ORDER:
        out["before"][c] = str(ws.Range(c).Value)
    mismatch = [c for c in ORDER if out["before"][c] != OLD[c]]
    if mismatch:
        for c in mismatch:
            out["assert_fails"].append("%s old text mismatch: got %r" % (c, out["before"][c][:60]))
        raise RuntimeError("old text mismatch — no write performed")
    for c in ORDER:
        ws.Range(c).Value = NEW[c]
    for c in ORDER:
        out["after"][c] = str(ws.Range(c).Value)
        if out["after"][c] != NEW[c]:
            out["assert_fails"].append("%s write verify NG" % c)
    wb.Save()
    wb.Close(False)
    print("saved.", flush=True)
except Exception as e:
    out["errors"].append(("EXC %r" % (e,))[:200])
finally:
    quit_and_cleanup()

out["ok"] = not out["assert_fails"] and not out["errors"]
with open(RESULT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("ok:", out["ok"])
print("assert:", out["assert_fails"])
print("errors:", out["errors"])
print("after C7:", out["after"].get("C7", "")[:50])
