# -*- coding: utf-8 -*-
"""corr_pana_11_style.py — Stage 1: セル様式(印刷設定·列幅·行高·見出し/前置き)
- 印刷: A4横·拡大縮小100%·範囲A1:AY58·余白10mm·罫線非表示
- 列幅: A..AY = 2.0字(実測770pt超なら比例縮小)
- 行高: R9=14(見出し)/R10=12.5(前置き)/R11-58=7.4/R1-8維持 → 総高≈537pt(189.5mm)
- 旧見出しA6·旧前置きC7:C10 をクリアし、R9/R10 に §6.5 の新文言(前置きはspec本文から抽出)
保存後 corr_pana_restore_printer.py を実行する。
"""
import json, re, time, subprocess, os, io, sys
warnings_ignored = True

HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(HERE, "corr_dryrun_pana.xlsx")
SPEC = os.path.join(HERE, "correlation_rebuild_spec.md")
RESULT = os.path.join(HERE, "corr_pana_11_style_result.json")

out = {"ok": False, "pid": None, "errors": [], "measured": {}}

# §6.5 前置き文を spec 本文から抽出(転写誤り防止)
spec_text = open(SPEC, encoding="utf-8").read()
m = re.search(r"確定事項と推定事項を区別して記載する。[^\n]+", spec_text)
assert m, "spec から前置き文を抽出できなかった"
PREFACE = m.group(0).strip()
out["preface"] = PREFACE

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

    # 印刷設定
    ps = ws.PageSetup
    ps.Orientation = 2          # xlLandscape
    ps.Zoom = 100
    ps.PrintArea = "$A$1:$AY$58"
    ps.PrintGridlines = False
    ps.LeftMargin = 28.35; ps.RightMargin = 28.35
    ps.TopMargin = 28.35; ps.BottomMargin = 28.35
    ps.HeaderMargin = 14.17; ps.FooterMargin = 14.17

    # 列幅
    ws.Columns("A:AY").ColumnWidth = 2.0
    w1 = ws.Range("A1:AY1").Width
    if w1 > 770.0:
        f = 770.0 / w1
        for c in range(1, 52):
            ws.Columns(c).ColumnWidth = 2.0 * f
    w2 = ws.Range("A1:AY1").Width
    out["measured"]["width_pt"] = round(w2, 1)

    # 行高
    ws.Rows(9).RowHeight = 14.0
    ws.Rows(10).RowHeight = 12.5
    for r in range(11, 59):
        ws.Rows(r).RowHeight = 7.4
    h_total = ws.Range("A1:A58").Height
    out["measured"]["height_pt"] = round(h_total, 1)
    out["measured"]["height_mm"] = round(h_total * 25.4 / 72.0, 1)

    # 旧見出し・前置きのクリア(内容のみ)
    ws.Range("A6").ClearContents()
    ws.Range("C7:C10").ClearContents()

    # 新見出し・前置き
    a9 = ws.Range("A9")
    a9.Value = "2-2 相関図(構成管理情報)"
    a9.Font.Size = 11
    a9.Font.Bold = True
    a10 = ws.Range("A10")
    a10.Value = PREFACE
    a10.Font.Size = 9
    a10.WrapText = False
    for rng in (a9, a10):
        try:
            rng.Font.Name = "Meiryo UI"
            rng.Font.NameFarEast = "Meiryo UI"
        except Exception as e:
            out["errors"].append("font:" + repr(e)[:80])

    wb.Save()
    out["ok"] = True
    print("saved: width=%s height=%s" % (out["measured"]["width_pt"], out["measured"]["height_pt"]), flush=True)
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
