# -*- coding: utf-8 -*-
"""corr_pana_15_build_edges.py — Stage 5: エッジ17本+ラベル17枚を corr_dryrun_pana.xlsx へ描画。
入力: corr_pana_15_tables.py(経路・ラベル・検証済み HARD=0) + corr_pana_14_texts.json(文言)
仕様: 線1pt黒·破線=E06/E09/E10/E12/E13·三角矢頭=E02/E06/E08/E09/E15/E16/E17/E18(From→To=終点)·
      BuildFreeform+msoEditingCorner·ラベル=不可視テキスト箱8pt·上端anchor·余白0·行送り9.9pt
Assert: 既存23→合計57·各エッジの線種/矢頭·各ラベル BoundHeight≤モデル+1·BoundWidth≤設計幅+0.5
出力: corr_pana_15_build_result.json + corr_pana_15_stage5.pdf + corr_pana_15_stage5_p1.png
"""
import json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import corr_pana_15_tables as T
import win32com.client
import win32process

DST = os.path.join(HERE, "corr_dryrun_pana.xlsx")
TEXTS = json.load(open(os.path.join(HERE, "corr_pana_14_texts.json"), encoding="utf-8"))
RESULT = os.path.join(HERE, "corr_pana_15_build_result.json")
PDF = os.path.join(HERE, "corr_pana_15_stage5.pdf")
PNG = os.path.join(HERE, "corr_pana_15_stage5_p1.png")

DASHED = {"E06", "E09", "E10", "E12", "E13"}
ARROW = {"E02", "E06", "E08", "E09", "E15", "E16", "E17", "E18"}
BASE_COUNT = 23
TOTAL = BASE_COUNT + 17 + 17

out = {"ok": False, "pid": None, "edges": {}, "labels": {}, "counts": {},
       "assert_fails": [], "fit_adjust": {}, "errors": []}

xl = win32com.client.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
out["pid"] = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
print("EXCEL PID", out["pid"], flush=True)

def rgb(hexstr):
    return int(hexstr[4:6] + hexstr[0:2] + hexstr[2:4], 16)

try:
    wb = xl.Workbooks.Open(DST)
    ws = wb.Worksheets("相関図")
    X0 = ws.Range("B11").Left
    Y0 = ws.Range("B11").Top
    assert ws.Shapes.Count == BASE_COUNT, \
        "existing shape count %d != %d" % (ws.Shapes.Count, BASE_COUNT)

    # ---------- エッジ17本 ----------
    for eid in sorted(T.ROUTES, key=lambda s: (len(s), s)):
        pts = T.ROUTES[eid]
        fb = ws.Shapes.BuildFreeform(0, X0 + pts[0][0], Y0 + pts[0][1])  # msoEditingCorner
        for (px, py) in pts[1:]:
            fb.AddNodes(0, 0, X0 + px, Y0 + py)  # msoSegmentLine, msoEditingCorner
        shp = fb.ConvertToShape()
        shp.Name = "edge_" + eid
        shp.Fill.Visible = 0
        ln = shp.Line
        ln.ForeColor.RGB = rgb("000000")
        ln.Weight = 1.0
        ln.DashStyle = 4 if eid in DASHED else 1  # msoLineDash / solid
        if eid in ARROW:
            ln.EndArrowheadStyle = 2       # msoArrowheadTriangle (終点=To側)
            ln.EndArrowheadLength = 2
            ln.EndArrowheadWidth = 2
        out["edges"][eid] = {"name": shp.Name, "points": len(pts),
                             "dash": eid in DASHED, "arrow": eid in ARROW}

    # ---------- ラベル17枚 ----------
    for lid in sorted(T.LABELS, key=lambda s: (len(s), s)):
        x, y, w, lines = T.LABELS[lid]
        model_h = 12.4 + 9.9 * (lines - 1)
        text = TEXTS["edges"][lid]["label"]
        shp = ws.Shapes.AddTextbox(1, X0 + x, Y0 + y, w, model_h + 2)
        shp.Name = "label_" + lid
        tf = shp.TextFrame2
        tf.WordWrap = -1
        tf.AutoSize = 0
        tf.MarginLeft = 0; tf.MarginRight = 0; tf.MarginTop = 0; tf.MarginBottom = 0
        tf.VerticalAnchor = 1  # top
        shp.Fill.Visible = 0
        shp.Line.Visible = 0
        rng = tf.TextRange
        rng.Text = text
        rng.Font.NameFarEast = "Meiryo UI"; rng.Font.Name = "Meiryo UI"
        rng.Font.Size = 8
        rng.Font.Fill.ForeColor.RGB = rgb("595959" if lid in DASHED else "262626")
        pf = rng.ParagraphFormat
        pf.LineRuleWithin = 0
        pf.SpaceWithin = 9.9
        pf.SpaceBefore = 0; pf.SpaceAfter = 0
        bh, bw = rng.BoundHeight, rng.BoundWidth
        fit_h = bh <= model_h + 1
        fit_w = bw <= w + 0.5
        if not (fit_h and fit_w):
            out["assert_fails"].append("label %s bound %.2fx%.2f vs %.2fx%.2f"
                                       % (lid, bw, bh, w, model_h))
        out["labels"][lid] = {"w": w, "lines_design": lines,
                              "bound_w": round(bw, 2), "bound_h": round(bh, 2),
                              "fit": bool(fit_h and fit_w)}

    out["counts"] = {"shapes": ws.Shapes.Count, "edges": len(out["edges"]),
                     "labels": len(out["labels"]), "expected_total": TOTAL}
    if ws.Shapes.Count != TOTAL:
        out["assert_fails"].append("shape count %d != %d" % (ws.Shapes.Count, TOTAL))

    # 線種・矢頭の読み戻し検証
    for eid in T.ROUTES:
        shp = ws.Shapes("edge_" + eid)
        d = shp.Line.DashStyle
        a = shp.Line.EndArrowheadStyle
        w = shp.Line.Weight
        ok = (abs(w - 1.0) < 0.01
              and (d == 4 if eid in DASHED else d == 1)
              and ((a == 2) if eid in ARROW else (a == 1)))  # msoArrowheadTriangle / msoArrowheadNone
        if not ok:
            out["assert_fails"].append("edge %s dash=%s arrow=%s w=%s" % (eid, d, a, w))

    wb.Save
    wb.Save()
    wb.Close(False)

    # ---------- レンダ ----------
    xl.Workbooks.Open(DST, ReadOnly=True)
    ws2 = xl.ActiveWorkbook.Worksheets("相関図")
    ws2.ExportAsFixedFormat(0, PDF, 0, True, False)  # xlTypePDF, xlQualityStandard
    xl.ActiveWorkbook.Close(False)
    out["render"] = {"pdf": PDF}
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

# PNG (p1)
try:
    import fitz
    doc = fitz.open(PDF)
    pg = doc[0]
    pix = pg.get_pixmap(dpi=150)
    pix.save(PNG)
    out["render"]["png"] = PNG
    out["render"]["pdf_pages"] = doc.page_count
    doc.close()
except Exception as e:
    out["errors"].append("png:" + repr(e)[:120])

out["ok"] = not out["assert_fails"]
with open(RESULT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("ok:", out["ok"], "counts:", out["counts"])
print("assert_fails:", out["assert_fails"])
bad = {k: v for k, v in out["labels"].items() if not v["fit"]}
print("label fit fails:", bad if bad else "none")
print("render:", out.get("render"))
if out["errors"]:
    print("errors:", out["errors"])
