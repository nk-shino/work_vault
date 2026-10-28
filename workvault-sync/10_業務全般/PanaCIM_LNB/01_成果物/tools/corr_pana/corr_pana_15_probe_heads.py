# -*- coding: utf-8 -*-
"""corr_pana_15_probe_heads.py — 実測プローブ(保存なし)。
1) band_a_head / band_b_head の実テキストink(BoundHeight/BoundWidth・余白)を測定
2) Stage 5 ラベル17枚を設計幅で仮組みし、改行数(BoundHeight)と幅溢れ(BoundWidth)を測定
   - 8pt・Meiryo UI・LineRuleWithin=0 + SpaceWithin=9.9pt・余白0・上端anchor
3) 既存シェイプ数の確認(23 expected)
結果は stdout と corr_pana_15_probe_result.json へ。ワークブックは保存しない。
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

out = {"ok": False, "pid": None, "heads": {}, "labels": {}, "shape_count": None, "errors": []}

xl = win32com.client.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
out["pid"] = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
print("EXCEL PID", out["pid"], flush=True)

def rgb(hexstr):
    return int(hexstr[4:6] + hexstr[2:4] + hexstr[0:2], 16)

try:
    wb = xl.Workbooks.Open(DST, ReadOnly=True)
    ws = wb.Worksheets("相関図")
    X0 = ws.Range("B11").Left
    Y0 = ws.Range("B11").Top
    out["shape_count"] = ws.Shapes.Count

    for hn in ("band_a_head", "band_b_head"):
        shp = ws.Shapes(hn)
        tf = shp.TextFrame2
        tr = tf.TextRange
        out["heads"][hn] = {
            "x": round(shp.Left - X0, 1), "y": round(shp.Top - Y0, 1),
            "w": round(shp.Width, 1), "h": round(shp.Height, 1),
            "margin_top": round(tf.MarginTop, 2), "margin_left": round(tf.MarginLeft, 2),
            "bound_h": round(tr.BoundHeight, 2), "bound_w": round(tr.BoundWidth, 2),
            "font_size": round(tr.Font.Size, 1),
            "ink_bottom_rel": round((shp.Top - Y0) + tf.MarginTop + tr.BoundHeight, 2),
            "text_head": tr.Text[:28],
        }

    def style_label(shp, text):
        tf = shp.TextFrame2
        tf.WordWrap = -1
        tf.AutoSize = 0
        tf.MarginLeft = 0; tf.MarginRight = 0; tf.MarginTop = 0; tf.MarginBottom = 0
        tf.VerticalAnchor = 1  # top
        rng = tf.TextRange
        rng.Text = text
        rng.Font.NameFarEast = "Meiryo UI"; rng.Font.Name = "Meiryo UI"
        rng.Font.Size = 8
        rng.Font.Fill.ForeColor.RGB = rgb("262626")
        pf = rng.ParagraphFormat
        pf.LineRuleWithin = 0
        pf.SpaceWithin = 9.9
        pf.SpaceBefore = 0; pf.SpaceAfter = 0
        return tf

    for lid in sorted(T.LABELS, key=lambda s: (len(s), s)):
        x, y, w, lines = T.LABELS[lid]
        text = TEXTS["edges"][lid]["label"]
        shp = ws.Shapes.AddTextbox(1, X0 + x, Y0 + y, w, 12.4 + 9.9 * (lines - 1))
        tf = style_label(shp, text)
        tr = tf.TextRange
        model_h = 12.4 + 9.9 * (lines - 1)
        out["labels"][lid] = {
            "w_design": w, "lines_design": lines, "model_h": round(model_h, 2),
            "bound_h": round(tr.BoundHeight, 2), "bound_w": round(tr.BoundWidth, 2),
            "wrapped_lines": round(tr.BoundHeight / 9.9, 2),
            "overflow_h": round(tr.BoundHeight - model_h, 2),
            "overflow_w": round(tr.BoundWidth - w, 2),
        }
        shp.Delete

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

with open(os.path.join(HERE, "corr_pana_15_probe_result.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
