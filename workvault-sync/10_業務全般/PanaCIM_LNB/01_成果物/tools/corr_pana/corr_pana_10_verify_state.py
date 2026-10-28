# -*- coding: utf-8 -*-
"""corr_pana_10_verify_state.py — 構築前の状態検証(読み取り専用)
- シート数・名前・相関図/相関図_old の図形数と名前一覧
- 相関図シートのセル A1:AZ12 値・列幅・行高・PageSetup
結果は corr_pana_10_state.json へ。保存はしない。
"""
import json, time, subprocess

DST = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\issue6263_work\corr_dryrun_pana.xlsx"
RESULT = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\issue6263_work\corr_pana_10_state.json"

out = {"ok": False, "pid": None, "errors": []}

def col_letter(n):
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s

import win32com.client
import win32process

xl = win32com.client.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
out["pid"] = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
print("EXCEL PID", out["pid"], flush=True)

try:
    wb = xl.Workbooks.Open(DST, None, True)  # positional: (Filename, UpdateLinks, ReadOnly)
    out["sheets"] = [wb.Worksheets(i).Name for i in range(1, wb.Worksheets.Count + 1)]
    out["sheet_count"] = wb.Worksheets.Count

    ws = wb.Worksheets("相関図")
    out["corr_shapes"] = ws.Shapes.Count
    out["corr_shape_names"] = [ws.Shapes(i).Name for i in range(1, ws.Shapes.Count + 1)]

    ws_old = wb.Worksheets("相関図_old")
    out["old_shapes"] = ws_old.Shapes.Count

    out["a6_main"] = str(ws.Range("A6").Value)
    out["a6_old"] = str(ws_old.Range("A6").Value)

    # セル内容 A1:AZ12(値のみ)
    cells = {}
    for r in range(1, 13):
        for c in range(1, 52):
            v = ws.Cells(r, c).Value
            if v is not None and str(v).strip() != "":
                cells[col_letter(c) + str(r)] = str(v)
    out["cells"] = cells

    # 列幅 A..AY(1..51)
    out["col_widths"] = {col_letter(c): round(ws.Columns(c).ColumnWidth, 2) for c in range(1, 52)}
    # 行高 1..58
    out["row_heights"] = {str(r): round(ws.Rows(r).RowHeight, 2) for r in range(1, 59)}

    ps = ws.PageSetup
    out["pagesetup"] = {
        "PaperSize": ps.PaperSize, "Orientation": ps.Orientation,
        "Zoom": ps.Zoom, "PrintArea": ps.PrintArea,
        "FitToPagesWide": ps.FitToPagesWide, "FitToPagesTall": ps.FitToPagesTall,
    }

    wb.Close(False)
    out["ok"] = True
finally:
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
print("ok:", out["ok"], "| corr:", out.get("corr_shapes"), "| old:", out.get("old_shapes"),
      "| sheets:", out.get("sheet_count"), "| a6 match:", out.get("a6_main") == out.get("a6_old"))
