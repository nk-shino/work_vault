# -*- coding: utf-8 -*-
"""corr_lnb_19_check_orig_change.py — LNB原本の変更内容の特定(読み取り専用·一時診断)。
並行レーン(用語適用)による原本更新の想定の下、相関図シートが未変更かを確認する。
"""
import hashlib
import json
import os
import sys
import time
import subprocess

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ORIG = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\LNB管理手順書案_未承認.xlsx"
ORIG_PANA = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\Pana-CIM管理手順書案_未承認.xlsx"
OUT = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\corr_lnb_work\corr_lnb_19_orig_check.json"

info = {"lnb_sha256": hashlib.sha256(open(ORIG, "rb").read()).hexdigest(),
        "pana_sha256": hashlib.sha256(open(ORIG_PANA, "rb").read()).hexdigest(),
        "lnb_mtime": os.path.getmtime(ORIG)}
import win32com.client
import win32process

xl = win32com.client.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
pid = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
try:
    wb = xl.Workbooks.Open(ORIG, UpdateLinks=0, ReadOnly=True)
    info["sheets"] = [wb.Worksheets(i).Name for i in range(1, wb.Worksheets.Count + 1)]
    ws = wb.Worksheets("相関図")
    info["corr_shape_count"] = ws.Shapes.Count
    info["corr_shape_names_head"] = [ws.Shapes.Item(i).Name for i in range(1, min(ws.Shapes.Count, 6) + 1)]
    ps = ws.PageSetup
    info["corr_pagesetup"] = {"orientation": int(ps.Orientation), "print_area": ps.PrintArea}
    info["corr_B11"] = [round(float(ws.Range("B11").Left), 1), round(float(ws.Range("B11").Top), 1)]
    info["corr_A6"] = str(ws.Range("A6").Value)
    info["corr_C7"] = str(ws.Range("C7").Value)[:60]
    wsg = wb.Worksheets("用語")
    info["yogo_usedrange"] = {"rows": wsg.UsedRange.Rows.Count, "cols": wsg.UsedRange.Columns.Count}
    info["yogo_last_row_sample"] = [str(wsg.Cells(r, 1).Value)[:40] for r in range(max(1, wsg.UsedRange.Rows.Count - 2),
                                                                                    wsg.UsedRange.Rows.Count + 1)]
    info["kanri_A103"] = str(wb.Worksheets("構成と管理情報").Range("A103").Value)
    wb.Close(SaveChanges=False)
finally:
    try:
        xl.Quit()
    except Exception:
        pass
    time.sleep(2)
    try:
        chk = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid], capture_output=True, text=True)
        if "EXCEL" in chk.stdout.upper():
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
    except Exception:
        pass
info["mtime_str"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(info["lnb_mtime"]))
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(info, f, ensure_ascii=False, indent=1)
print("written:", OUT)
