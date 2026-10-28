# -*- coding: utf-8 -*-
"""corr_pana_15_patch_e09.py — P-1適用(2026-10-28ユーザー承認): edge_E09を新経路で作り直す。
旧: (8,67)->(2,67)->(2,190)->(662,190)->(662,353)->(650,353) 西回り
新: (382,95)->(386,95)->(386,190)->(662,190)->(662,353)->(650,353) N03起点·x386下降
様式は元ビルドと同一(黒1pt·破線·三角矢頭·終点=To側)。図形総数57を維持。
"""
import json, os, sys, time, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import corr_pana_15_tables as T
import win32com.client, win32process

DST = os.path.join(HERE, "corr_dryrun_pana.xlsx")
RESULT = os.path.join(HERE, "corr_pana_15_patch_e09_result.json")

def rgb(hexstr):
    return int(hexstr[4:6] + hexstr[0:2] + hexstr[2:4], 16)

out = {"errors": [], "assert_fails": []}
xl = win32com.client.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
pid = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
print("EXCEL PID", pid, flush=True)
out["pid"] = pid
try:
    wb = xl.Workbooks.Open(DST)
    ws = wb.Worksheets("相関図")
    before = ws.Shapes.Count
    old = ws.Shapes("edge_E09")
    old.Delete()
    pts = T.ROUTES["E09"]
    X0 = ws.Range("B11").Left
    Y0 = ws.Range("B11").Top
    fb = ws.Shapes.BuildFreeform(0, X0 + pts[0][0], Y0 + pts[0][1])
    for (px, py) in pts[1:]:
        fb.AddNodes(0, 0, X0 + px, Y0 + py)
    shp = fb.ConvertToShape()
    shp.Name = "edge_E09"
    shp.Fill.Visible = 0
    ln = shp.Line
    ln.ForeColor.RGB = rgb("000000")
    ln.Weight = 1.0
    ln.DashStyle = 4        # msoLineDash (E09=T3破線)
    ln.EndArrowheadStyle = 2
    ln.EndArrowheadLength = 2
    ln.EndArrowheadWidth = 2
    after = ws.Shapes.Count
    out["edge_E09"] = {"points": [list(p) for p in pts], "count_before": before, "count_after": after}
    if before != after:
        out["assert_fails"].append("shape count %d -> %d" % (before, after))
    # 新経路の始点がN03の縁上であること(A0相当の簡易確認)
    n03 = T.SHAPES["n03_ctrl"]
    sx, sy = pts[0]
    on_edge = (abs(sx - n03[2]) < 0.5 and n03[1] - 0.5 <= sy <= n03[3] + 0.5) or \
              (abs(sy - n03[3]) < 0.5 and n03[0] - 0.5 <= sx <= n03[2] + 0.5)
    out["origin_on_n03_edge"] = bool(on_edge)
    if not on_edge:
        out["assert_fails"].append("E09 origin (%s,%s) not on n03 edge %s" % (sx, sy, [round(v,1) for v in n03]))
    wb.Save()
    wb.Close(False)
    print("saved.", flush=True)
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
            out["errors"].append("killed residual %d" % pid)
    except Exception as e:
        out["errors"].append(("cleanup: %r" % e)[:80])

out["ok"] = not out["assert_fails"] and not out["errors"]
with open(RESULT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("ok:", out["ok"], "| assert:", out["assert_fails"], "| errors:", out["errors"])
