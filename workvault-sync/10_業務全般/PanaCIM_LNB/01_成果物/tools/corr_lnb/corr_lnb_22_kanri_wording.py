# -*- coding: utf-8 -*-
"""corr_lnb_22_kanri_wording.py — 構成と管理情報シート §2-3 の文言更新(report §7·§8.3)。
原本の「構成と管理情報」シートに対して:
  C104: 元坯の記述を Pana-CIM Stage 5 相関図(複製元)へ更新
        (LNB⇔Pana-CIM 間のデータの向きが実機未確認である旨は維持)
  C106: 作図形式の記述を「テキストボックス·フリーフォーム直線·ラベル」へ更新
安全策: 置換対象の断片が各セルにちょうど1回出現することを確認してから置換する。
断片が見つからない·複数ある場合は書き込まず結果に記録する(文言の実物をfirstに記録)。
注意: 原本は OneDrive 配下のため AutoSave が働く(20 の実績)。編集後は明示的に Save する。
"""
import json
import os
import sys
import time
import subprocess

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
VAULT = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
ORIG = os.path.join(VAULT, "LNB管理手順書案_未承認.xlsx")
RESULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corr_lnb_22_kanri_wording_result.json")

REPL = [
    ("C104", "PanaCIM_LNB_確実構成図.drawio(第一層)",
     "Pana-CIM管理手順書の相関図(Stage 5·2026-10-28確定)"),
    ("C106", "コネクタ", "フリーフォーム直線・ラベル"),
]

out = {"ok": False, "pid": None, "cells": {}, "assert_fails": [], "errors": []}
import win32com.client
import win32process

xl = win32com.client.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
pid = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
out["pid"] = pid
print("EXCEL PID", pid, flush=True)
try:
    wb = xl.Workbooks.Open(ORIG)
    ws = wb.Worksheets("構成と管理情報")
    out["A103_heading"] = str(ws.Range("A103").Value)
    for cell, frag, new in REPL:
        cur = str(ws.Range(cell).Value)
        rec = {"before": cur, "count": cur.count(frag)}
        if rec["count"] == 1:
            ws.Range(cell).Value = cur.replace(frag, new)
            rec["after"] = str(ws.Range(cell).Value)
        else:
            rec["after"] = None
            out["assert_fails"].append("%s: fragment %r count %d != 1 (未書換)" % (cell, frag, rec["count"]))
        out["cells"][cell] = rec
    if not out["assert_fails"]:
        wb.Save()
        print("saved.", flush=True)
    else:
        print("NOT saved (assert_fails).", flush=True)
    wb.Close(False)
finally:
    try:
        xl.Quit()
    except Exception as e:
        out["errors"].append(("quit: %r" % e)[:80])
    time.sleep(2)
    try:
        chk = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid], capture_output=True, text=True)
        if "EXCEL" in chk.stdout.upper():
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
            out["cleanup"] = "killed residual %d" % pid
    except Exception as e:
        out["errors"].append(("cleanup: %r" % e)[:80])

out["ok"] = not out["assert_fails"] and not out["errors"]
with open(RESULT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("ok:", out["ok"])
for c, rec in out["cells"].items():
    print(c, "count:", rec["count"])
    print("  after:", (rec["after"] or rec["before"])[:90])
print("assert:", out["assert_fails"])
print("errors:", out["errors"])
