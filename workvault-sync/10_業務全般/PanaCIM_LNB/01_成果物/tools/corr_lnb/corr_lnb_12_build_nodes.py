# -*- coding: utf-8 -*-
"""corr_lnb_12_build_nodes.py — Stage B: 帯2本+見出し2+ノード19 をドライラン冊の新「相関図」へ構築。
入力: corr_lnb_10_tables.py(幾何権威·帯見出しoverride含む) + corr_lnb_00_texts.json(文言·PanaCIM Stage5確定を無変更で使用)
Pana-CIM Stage 4→5 の修復済み最終仕様を最初から適用する(corr_pana_15_fix_nodetext.py 相当を織り込み済み):
  - ノード: 1行目11pt(推定ノードは404040)/備考8pt(595959)·行送り0.75→fit失敗時0.6·N17のみラベル10ptフォールバック
  - band_a_head (0,0,470,30): a1 12pt太字白+a2 10pt灰 → 実ink下端>23.5ならa1 11pt
  - band_b_head (178,315,248,18): 題名部のみ 12→11→10pt太字白 1行·MarginTop 0.5
Assert: 各図形 BoundHeight ≤ 形高-2(実テキスト代入後に測る—Stage 4の空テキスト測定欠陥は再現しない)
出力: corr_lnb_12_result.json
"""
import json
import os
import sys
import time
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import corr_lnb_10_tables as T
import win32com.client
import win32process

WORK = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\corr_lnb_work"
DRY = os.path.join(WORK, "corr_dryrun_lnb.xlsx")
TEXTS = json.load(open(os.path.join(HERE, "corr_lnb_00_texts.json"), encoding="utf-8"))
RESULT = os.path.join(HERE, "corr_lnb_12_result.json")

PALETTE = {
    "server":    {"fill": "DEEBF7", "line": "2E75B6", "w": 1.5,  "dash": False, "shape": 5},
    "terminal":  {"fill": "FFF2CC", "line": "BF8F00", "w": 1.5,  "dash": False, "shape": 1},
    "equipment": {"fill": "E2EFDA", "line": "538135", "w": 2.25, "dash": False, "shape": 1},
    "estimate":  {"fill": "F2F2F2", "line": "7F7F7F", "w": 1.5,  "dash": True,  "shape": 1},
    "external":  {"fill": "FFFFFF", "line": "262626", "w": 1.5,  "dash": False, "shape": 20},
    "note":      {"fill": "FFFFFF", "line": "808080", "w": 0.75, "dash": False, "shape": 1},
    "container": {"fill": "DEEBF7", "line": "2E75B6", "w": 2.25, "dash": False, "shape": 5},
}
STYLE_OF = {"N01": "container", "N02": "server", "N03": "server", "N06": "server", "N19": "server",
            "N10": "terminal", "N11": "terminal", "N12": "terminal", "N15": "terminal", "N16": "terminal",
            "N07": "equipment", "N08": "equipment", "N09": "equipment", "N17": "equipment",
            "N04": "estimate", "N13": "estimate", "N14": "estimate", "N18": "external", "N05": "note"}
NAME_OF = {"N01": "n01_esxi", "N02": "n02_app", "N03": "n03_ctrl", "N04": "n04_maint", "N05": "n05_note",
           "N06": "n06_dgs", "N07": "n07_lnb", "N08": "n08_line", "N09": "n09_andon", "N10": "n10_monitor",
           "N11": "n11_lws", "N12": "n12_pda", "N13": "n13_ap", "N14": "n14_tablet", "N15": "n15_cima_pc",
           "N16": "n16_cimc_pc", "N17": "n17_backup", "N18": "n18_extif", "N19": "n19_cima_sv"}
ESTIMATE = {"N04", "N13", "N14"}

# 配置 (pt·B11起点) — corr_pana_14_result.json 凍結値(帯見出しはStage 5 override)
POS = {
    "band_a":      (0,   0,   750, 312),
    "band_a_head": (0,   0,   470, 30),
    "n01_esxi":    (0,   34,  390, 142),
    "n02_app":     (8,   52,  186, 50),
    "n03_ctrl":    (202, 52,  180, 50),
    "n04_maint":   (8,   108, 150, 40),
    "n06_dgs":     (164, 108, 218, 60),
    "n05_note":    (395, 34,  225, 84),
    "n19_cima_sv": (395, 124, 225, 26),
    "n17_backup":  (625, 34,  125, 53),
    "n18_extif":   (625, 93,  125, 50),
    "n10_monitor": (0,   192, 130, 50),
    "n15_cima_pc": (138, 192, 140, 40),
    "n16_cimc_pc": (286, 192, 140, 40),
    "n13_ap":      (434, 192, 110, 40),
    "n14_tablet":  (552, 192, 100, 40),
    "n12_pda":     (0,   250, 160, 36),
    "n11_lws":     (168, 250, 185, 36),
    "n07_lnb":     (0,   294, 176, 36),
    "band_b":      (0,   312, 750, 54),
    "band_b_head": (178, 315, 248, 18),
    "n08_line":    (0,   340, 220, 26),
    "n09_andon":   (430, 340, 220, 26),
}

out = {"ok": False, "pid": None, "shapes": {}, "heads": {}, "assert_fails": [], "errors": []}

xl = win32com.client.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
out["pid"] = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
print("EXCEL PID", out["pid"], flush=True)


def rgb(hexstr):
    return int(hexstr[4:6] + hexstr[0:2] + hexstr[2:4], 16)


def apply_paras(shp, para_texts, specs):
    """再代入→全体=最終段落→差分段落を旧 Characters で上書き→行送り0.75。戻り値 (rng, pf)"""
    tf2 = shp.TextFrame2
    rng = tf2.TextRange
    rng.Text = "\r".join(para_texts)
    rng.Font.NameFarEast = "Meiryo UI"; rng.Font.Name = "Meiryo UI"
    base = specs[-1]
    rng.Font.Size = base[0]
    rng.Font.Fill.ForeColor.RGB = rgb(base[1])
    rng.Font.Bold = -1 if base[2] else 0
    pos = 1
    tfo = shp.TextFrame  # 旧API: 段落範囲の書式はこれで行う
    for pt, spec in zip(para_texts, specs):
        if spec != base:
            f = tfo.Characters(pos, len(pt)).Font
            f.Size = spec[0]
            f.Color = rgb(spec[1])
            f.Bold = bool(spec[2])
        pos += len(pt) + 1
    pf = rng.ParagraphFormat
    pf.LineRuleWithin = -1
    pf.SpaceWithin = 0.75
    pf.SpaceBefore = 0; pf.SpaceAfter = 0
    return rng, pf


def fit_with_fallback(shp, para_texts, specs, max_bound):
    rng, pf = apply_paras(shp, para_texts, specs)
    bh = rng.BoundHeight
    if bh > max_bound:
        pf.SpaceWithin = 0.6
        bh = rng.BoundHeight
    return round(bh, 2), round(pf.SpaceWithin, 2), rng


try:
    wb = xl.Workbooks.Open(DRY)
    ws = wb.Worksheets("相関図")
    X0 = ws.Range("B11").Left
    Y0 = ws.Range("B11").Top
    out["anchor"] = [round(float(X0), 1), round(float(Y0), 1)]
    if ws.Shapes.Count != 0:
        out["assert_fails"].append("pre-build shapes %d != 0" % ws.Shapes.Count)

    def add_shape(name, x, y, w, h, kind, anchor_mid=True):
        p = PALETTE[kind]
        shp = ws.Shapes.AddShape(p["shape"], X0 + x, Y0 + y, w, h)
        shp.Name = name
        shp.Fill.ForeColor.RGB = rgb(p["fill"])
        shp.Line.ForeColor.RGB = rgb(p["line"])
        shp.Line.Weight = p["w"]
        shp.Line.DashStyle = 4 if p["dash"] else 1
        tf = shp.TextFrame2
        tf.WordWrap = -1; tf.AutoSize = 0
        tf.MarginLeft = 2; tf.MarginRight = 2; tf.MarginTop = 1; tf.MarginBottom = 1
        tf.VerticalAnchor = 3 if anchor_mid else 1
        return shp

    # ---------- 帯2本(最背面) ----------
    ba = add_shape("band_a", *POS["band_a"], "note")
    ba.Fill.Visible = 0
    ba.Line.ForeColor.RGB = rgb("BFBFBF"); ba.Line.Weight = 0.75
    bb = add_shape("band_b", *POS["band_b"], "note")
    bb.Fill.Visible = 0
    bb.Line.ForeColor.RGB = rgb("BFBFBF"); bb.Line.Weight = 0.75

    # ---------- 帯見出し2本 ----------
    ha = add_shape("band_a_head", *POS["band_a_head"], "note")
    ha.Fill.ForeColor.RGB = rgb("404040"); ha.Line.Visible = 0
    bh, sp, rng = fit_with_fallback(ha, [TEXTS["bands"]["a1"], TEXTS["bands"]["a2"]],
                                    [(12, "FFFFFF", True), (10, "D9D9D9", False)], 22.5)
    used_a1 = 12.0
    if 1.0 + bh > 23.5:
        bh, sp, rng = fit_with_fallback(ha, [TEXTS["bands"]["a1"], TEXTS["bands"]["a2"]],
                                        [(11, "FFFFFF", True), (10, "D9D9D9", False)], 22.5)
        used_a1 = 11.0
    ink_btm = round(1.0 + bh, 2)
    out["heads"]["band_a_head"] = {"a1_pt": used_a1, "bound_h": bh, "bound_w": round(rng.BoundWidth, 1),
                                   "ink_bottom": ink_btm, "space": sp, "fit": ink_btm <= 24.5}
    if ink_btm > 24.5:
        out["assert_fails"].append("band_a_head ink bottom %.2f >= y25 lane -0.5" % ink_btm)

    hb = add_shape("band_b_head", *POS["band_b_head"], "note")
    hb.Fill.ForeColor.RGB = rgb("404040"); hb.Line.Visible = 0
    b1_title = "ライン設備側ネットワーク — 内部網"
    fs = 12.0
    for fs in (12.0, 11.0, 10.0):
        bh, sp, rng = fit_with_fallback(hb, [b1_title], [(fs, "FFFFFF", True)], 13.0)
        if bh <= 13.0 and rng.BoundWidth <= 244.0:
            break
    hb.Top = Y0 + 315.0
    hb.TextFrame2.MarginTop = 0.5
    ink_btm = round(hb.Top - Y0 + hb.TextFrame2.MarginTop + bh, 2)
    out["heads"]["band_b_head"] = {"b1_pt": fs, "bound_h": bh, "bound_w": round(rng.BoundWidth, 1),
                                   "ink_bottom": ink_btm, "space": sp,
                                   "fit": bh <= 13.0 and rng.BoundWidth <= 244.0 and ink_btm <= 328.5}
    if not out["heads"]["band_b_head"]["fit"]:
        out["assert_fails"].append("band_b_head b1 %.1fpt bound %.2f w %.1f ink_btm %.2f"
                                   % (fs, bh, rng.BoundWidth, ink_btm))

    # ---------- ノード19 ----------
    for nid in ["N01", "N02", "N03", "N04", "N05", "N06", "N07", "N08", "N09", "N10",
                "N11", "N12", "N13", "N14", "N15", "N16", "N17", "N18", "N19"]:
        name = NAME_OF[nid]
        x, y, w, h = POS[name]
        shp = add_shape(name, x, y, w, h, STYLE_OF[nid], anchor_mid=(nid != "N01"))
        if nid == "N05":
            ts = list(TEXTS["n05"]); specs = [(8, "595959", False)] * len(ts)
        elif nid == "N19":
            ts = [TEXTS["n19"]["label"], TEXTS["n19"]["note"]]
            specs = [(11, "1F1F1F", False), (8, "595959", False)]
        else:
            c = "404040" if nid in ESTIMATE else "1F1F1F"
            cn = c if nid in ESTIMATE else "595959"
            ts = [TEXTS["nodes"][nid]["label"], TEXTS["nodes"][nid]["note"]]
            specs = [(11, c, False), (8, cn, False)]
        bh, sp, rng = fit_with_fallback(shp, ts, specs, shp.Height - 2)
        if nid == "N17" and bh > shp.Height - 2:
            specs = [(10, "1F1F1F", False), (8, "595959", False)]  # 長パスで折返増大→ラベル10pt
            bh, sp, rng = fit_with_fallback(shp, ts, specs, shp.Height - 2)
            out["shapes"][name + "_fallback"] = "label 10pt"
        fit = bh <= shp.Height - 2
        if not fit:
            out["assert_fails"].append("node %s bound %.1f > %.1f" % (name, bh, shp.Height - 2))
        out["shapes"][name] = {"x": round(shp.Left - X0, 1), "y": round(shp.Top - Y0, 1),
                               "w": round(shp.Width, 1), "h": round(shp.Height, 1),
                               "bound_h": bh, "space": sp, "fit": fit}

    out["count_after_nodes"] = ws.Shapes.Count
    if ws.Shapes.Count != 23:
        out["assert_fails"].append("shape count %d != 23 (band2+head2+node19)" % ws.Shapes.Count)

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
        chk = subprocess.run(["tasklist", "/FI", "PID eq %d" % out["pid"]], capture_output=True, text=True)
        if "EXCEL" in chk.stdout.upper():
            subprocess.run(["taskkill", "/PID", str(out["pid"]), "/F"], capture_output=True)
            out["cleanup"] = "killed residual %d" % out["pid"]
    except Exception as e:
        out["errors"].append(("cleanup: %r" % e)[:80])

out["ok"] = not out["assert_fails"] and not out["errors"]
with open(RESULT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("ok:", out["ok"])
print("assert:", out["assert_fails"])
print("errors:", out["errors"])
bad = {k: v for k, v in out["shapes"].items() if isinstance(v, dict) and not v.get("fit")}
print("node fit fails:", bad if bad else "none")
print("heads:", json.dumps(out["heads"], ensure_ascii=False))
