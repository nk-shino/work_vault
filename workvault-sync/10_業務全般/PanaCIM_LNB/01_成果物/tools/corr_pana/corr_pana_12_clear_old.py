# -*- coding: utf-8 -*-
"""corr_pana_12_clear_old.py — Stage 2: 相関図シートの旧図形34個を削除(退避済み)
- 事前確認: 相関図=34図形·相関図_old=34図形(退避の完全性)
- 削除は後方から。削除後 相関図=0 を確認して保存。
保存後 corr_pana_restore_printer.py を実行する。
"""
import json, time, subprocess, os

HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(HERE, "corr_dryrun_pana.xlsx")
RESULT = os.path.join(HERE, "corr_pana_12_clear_old_result.json")

out = {"ok": False, "pid": None, "deleted": 0, "errors": []}

import win32com.client
import win32process

xl = win32com.client.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
out["pid"] = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
print("EXCEL PID", out["pid"], flush=True)

try:
    wb = xl.Workbooks.Open(DST)
    ws = wb.Worksheets("相関図")
    ws_old = wb.Worksheets("相関図_old")
    n_main = ws.Shapes.Count
    n_old = ws_old.Shapes.Count
    if n_main != 34 or n_old != 34:
        out["errors"].append("事前確認NG: main=%d old=%d — 削除を中止" % (n_main, n_old))
        print(out["errors"][-1], flush=True)
    else:
        for i in range(n_main, 0, -1):
            ws.Shapes(i).Delete()
        out["deleted"] = n_main
        if ws.Shapes.Count != 0:
            out["errors"].append("削除後に残存: %d" % ws.Shapes.Count)
        else:
            wb.Save()
            out["ok"] = True
            print("deleted %d shapes, saved" % n_main, flush=True)
finally:
    try:
        wb.Close(SaveChanges=False)
    except Exception as e:
        out["errors"].append("close:" + repr(e)[:80])
    try:
        xl.Quit()
    except Exception as e:
        out["errors"].append("quit:" + repr(e)[:80])
    time.sleep(2)
    try:
        chk = subprocess.run(["tasklist", "/FI", "PID eq %d" % out["pid"]], capture_output=True, text=True)
        if "EXCEL" in chk.stdout.upper():
            subprocess.run(["taskkill", "/PID", str(out["pid"]), "/F"], capture_output=True)
            out["errors"].append("killed residual %d" % out["pid"])
    except Exception as e:
        out["errors"].append("cleanup:" + repr(e)[:80])

with open(RESULT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("ok:", out["ok"])
