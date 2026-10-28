# -*- coding: utf-8 -*-
"""corr_pana_14_bands_nodes.py — Stage 4: 様式行調整 + 帯2本+見出し2+ノード19 (案C′ addendum2 §4)
- 文言は spec/追補1 の本文から regex 抽出(手打ち禁止·ゲート1)
- 各図形は作成直後に BoundHeight <= 形高 を assert(ゲート2)·逸脱は幅拡張で再試行
- 行送り75%(SpaceWithin 0.75)·フォント: 1行目11pt/備考8pt/帯見出し12+10pt
"""
import json, os, re, sys, time, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
DST = os.path.join(HERE, "corr_dryrun_pana.xlsx")
MD_SPEC = os.path.join(HERE, "correlation_rebuild_spec.md")
MD_ADD1 = os.path.join(HERE, "correlation_rebuild_spec_addendum.md")
TEXTS_JSON = os.path.join(HERE, "corr_pana_14_texts.json")
RESULT = os.path.join(HERE, "corr_pana_14_result.json")

spec = open(MD_SPEC, encoding="utf-8").read()
add1 = open(MD_ADD1, encoding="utf-8").read()
slines = [l.rstrip() for l in spec.splitlines()]
alines = [l.rstrip() for l in add1.splitlines()]

# ---------- 文言抽出 ----------
def m1(pat, lines, flags=0):
    for ln in lines:
        mt = re.match(pat, ln, flags)
        if mt:
            return mt.groups()
    return None

# ノード表(spec §2)
nodes = {}
for ln in slines:
    mt = re.match(r"^\| (N\d+) \| (.+?) \| (.+?) \| (.+?) \| (.+?) \| (.+?) \|$", ln)
    if mt:
        nodes[mt.group(1)] = {"label": mt.group(2), "style": mt.group(4), "note": mt.group(6)}
# 追補1 §3.2 改訂(備考)
for ln in alines:
    mt = re.match(r"^\| (N\d+) 備考 \| (.+?) \| (.+?) \|$", ln)
    if mt:
        nid, new, _ = mt.groups()
        base = nodes[nid]["note"]
        if new.startswith("同上"):
            new = nodes["N02"]["note"] if "N02" in [k for k in nodes] else new
            # N03 の「同上」は N02 改訂文と同文
            if nid == "N03":
                new = nodes.get("N02", {}).get("_revised", nodes["N02"]["note"])
        elif "既存文+" in new:
            addpart = re.search(r"「(.+)」", new)
            new = base + (addpart.group(1) if addpart else "")
        nodes[nid]["note"] = new
        nodes[nid]["_revised"] = new
# N03 同上処理(N02の改訂後文を複製)
if "N03" in nodes and nodes["N03"]["note"].startswith("同上"):
    nodes["N03"]["note"] = nodes["N02"]["note"]
# N02 改訂が「同上」処理より後でないよう順序注意: N02行が先に来る(表順)ため上のループでN02が先に改訂される
# N05(spec §2.1 3段落 + 追補1 §3.2 1段落目置換)
n05p = []
in21 = False
for ln in slines:
    if ln.startswith("### 2.1"):
        in21 = True; continue
    if in21:
        if ln.startswith("> "):
            n05p.append(ln[2:].strip())
        elif n05p:
            break
n05p = [p for p in n05p if p]
for ln in alines:
    mt = re.match(r"^\| N05 注記 1段落目 \| (.+?) \| (.+?) \|$", ln)
    if mt:
        n05p[0] = mt.group(1)
# N19(追補1 §3.1)
n19_label = n19_note = None
for ln in alines:
    mt = re.match(r"^\| 図内表記\(1行目\) \| (.+?) \|$", ln)
    if mt: n19_label = mt.group(1)
    mt = re.match(r"^\| 備考\(2行目·10ptグレー\) \| (.+?) \|$", ln)
    if mt: n19_note = mt.group(1)
assert n19_label and n19_note, "N19 not found"
# 推定ノードは名称末尾に(要確認)追加(§2.2)
for nid in ("N04", "N13", "N14"):
    if "(要確認)" not in nodes[nid]["label"]:
        nodes[nid]["label"] = nodes[nid]["label"] + "(要確認)"
# エッジ(spec §3) — Stage15で使用
edges = {}
for ln in slines:
    mt = re.match(r"^\| (E\d+) \| (.+?) \| (.+?) \| (.+?) \| (.+?) \| (.+?) \|$", ln)
    if mt:
        edges[mt.group(1)] = {"fromto": mt.group(2), "label": mt.group(3), "kind": mt.group(4)}
# 帯見出し(spec §6.2 の「」内 + 追補1 §3.3 2行目)
band_a_l1 = band_b_l1 = None
for ln in slines:
    mt = re.match(r"^\| 帯A \| .+? 帯見出し小帯 B11:M13「(.+?)」 \|$", ln)
    if mt: band_a_l1 = mt.group(1)
    mt = re.match(r"^\| 帯B \| .+? 帯見出し小帯 B44:M46「(.+?)」 \|$", ln)
    if mt: band_b_l1 = mt.group(1)
band_a_l2 = None
mt = re.search(r"2行目\(追記·10pt·グレー白抜き\): 「(.+?)」", add1)
if mt: band_a_l2 = mt.group(1)
assert band_a_l1 and band_b_l1 and band_a_l2, "band head texts not found"
# 注記 X01〜X04
x01 = x02 = x03 = None
for ln in slines:
    mt = re.match(r"^\*\*X01 構成条件〔T1〕\*\*: (.+)$", ln)
    if mt: x01 = mt.group(1)
    mt = re.match(r"^\*\*X02 未確認事項[^*]*\*\*: (.+)$", ln)
    if mt: x02 = mt.group(1)
    mt = re.match(r"^\*\*X03 対象外·補足\*\*: (.+)$", ln)
    if mt: x03 = mt.group(1)
x04 = None
for idx, ln in enumerate(alines):
    mt = re.match(r"^\*\*X04 周辺システム連携〔[^*]+\*\*: (.+)$", ln)
    if mt:
        x04 = mt.group(1)
    elif re.match(r"^\*\*X04 周辺システム連携〔[^*]+\*\*: *$", ln):
        # タイトル行と本文が別行(addendum1 §3.6)
        for nxt in alines[idx + 1:]:
            if nxt.strip():
                x04 = nxt.strip()
                break
# X02 への追補(①②追記·⑪⑫追加)
a1t = a2t = x11 = x12 = None
for ln in alines:
    mt = re.match(r"^- X02-① 追記: 「(.+)」$", ln)
    if mt: a1t = mt.group(1)
    mt = re.match(r"^- X02-② 追記: 「(.+)」$", ln)
    if mt: a2t = mt.group(1)
    mt = re.match(r"^- \*\*X02-⑪\*\*: (.+)$", ln)
    if mt: x11 = mt.group(1)
    mt = re.match(r"^- \*\*X02-⑫\*\*: (.+)$", ln)
    if mt: x12 = mt.group(1)
assert all([x01, x02, x03, x04, a1t, a2t, x11, x12]), "X texts incomplete"
x02 = x02.replace("①アンドンとLNB/PanaCIMの接続(T3)", "①アンドンとLNB/PanaCIMの接続(T3)" + a1t, 1)
x02 = x02.replace("②ノズルデータ/リーダーデータのLNB経由経路(T3)", "②ノズルデータ/リーダーデータのLNB経由経路(T3)" + a2t, 1)
assert a1t in x02 and a2t in x02, "X02 revisions not applied"
x02 = x02.rstrip("。") + "。" + x11 + x12
# 凡例(spec §4 blockquote·追補1 §3.5 で対象外行置換)
legend_lines = []
in4 = False
for ln in slines:
    if ln.startswith("## 4."): in4 = True; continue
    if ln.startswith("## 5."): break
    if in4 and ln.startswith("> "):
        t = ln[2:].strip()
        if t: legend_lines.append(t)
legend_repl = None
for ln in alines:
    mt = re.match(r"^> (【対象外·線なし】.+)$", ln)
    if mt: legend_repl = mt.group(1)
assert legend_repl, "legend replacement not found"
legend_lines = [legend_repl if l.startswith("【対象外】") else l for l in legend_lines]
assert any(l.startswith("【対象外·線なし】") for l in legend_lines)

texts = {
    "nodes": {k: {"label": v["label"], "note": v["note"], "style": v["style"]} for k, v in nodes.items()},
    "n05": n05p, "n19": {"label": n19_label, "note": n19_note},
    "edges": edges,
    "bands": {"a1": band_a_l1, "a2": band_a_l2, "b1": band_b_l1},
    "x": {"X01": x01, "X02": x02, "X03": x03, "X04": x04},
    "legend": legend_lines,
}
with open(TEXTS_JSON, "w", encoding="utf-8") as f:
    json.dump(texts, f, ensure_ascii=False, indent=1)

# ---------- COM 構築 ----------
import win32com.client
import win32process
from win32com.client import constants

PALETTE = {
    "server":    {"fill": "DEEBF7", "line": "2E75B6", "w": 1.5,  "dash": False, "shape": 5},   # rounded rect
    "terminal":  {"fill": "FFF2CC", "line": "BF8F00", "w": 1.5,  "dash": False, "shape": 1},
    "equipment": {"fill": "E2EFDA", "line": "538135", "w": 2.25, "dash": False, "shape": 1},
    "estimate":  {"fill": "F2F2F2", "line": "7F7F7F", "w": 1.5,  "dash": True,  "shape": 1},
    "external":  {"fill": "FFFFFF", "line": "262626", "w": 1.5,  "dash": False, "shape": constants.msoShapeFlowchartTerminator if hasattr(constants, "msoShapeFlowchartTerminator") else 20},
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

# 配置 (pt·X0/Y0起点) — addendum2 §4 ゾーン
POS = {
    "band_a":      (0,   0,   750, 312),
    "band_a_head": (0,   0,   200, 30),
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
    "n08_line":    (0,   340, 220, 26),
    "n09_andon":   (430, 340, 220, 26),
}
WMAX = {"n01_esxi": 390, "n02_app": 200, "n03_ctrl": 195, "n04_maint": 160, "n06_dgs": 245,
        "n05_note": 260, "n19_cima_sv": 260, "n17_backup": 140, "n18_extif": 130,
        "n10_monitor": 175, "n15_cima_pc": 200, "n16_cimc_pc": 200, "n13_ap": 130, "n14_tablet": 130,
        "n12_pda": 200, "n11_lws": 230, "n07_lnb": 220, "n08_line": 260, "n09_andon": 260}

out = {"ok": False, "pid": None, "shapes": {}, "assert_adjust": {}, "errors": []}

xl = win32com.client.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
out["pid"] = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
print("EXCEL PID", out["pid"], flush=True)

def rgb(hexstr):
    return int(hexstr[4:6] + hexstr[2:4] + hexstr[0:2], 16)

def fit_text(shp, w_max_zone, tag):
    """BoundHeight assert: 逸脱時は幅を拡張して再試行(ゲート2)"""
    tf = shp.TextFrame2
    for attempt in range(4):
        bh = tf.TextRange.BoundHeight
        h = shp.Height
        if bh <= h - 2:
            return True, attempt
        if shp.Width < w_max_zone - 1:
            shp.Width = min(shp.Width + 12, w_max_zone)
        else:
            break
    return False, -1

try:
    wb = xl.Workbooks.Open(DST)
    ws = wb.Worksheets("相関図")
    X0 = ws.Range("B11").Left
    Y0 = ws.Range("B11").Top
    out["x0"] = X0; out["y0"] = Y0
    # 図域行高を 7.7pt へ(図域 369.6pt)
    ws.Rows("11:58").RowHeight = 7.7
    YB = ws.Range("B59").Top  # 頁2 上端(参考)

    def style_text(tf, fs1, fs2, color1="1F1F1F", color2="595959", bold1=False):
        rng = tf.TextRange
        rng.Font.NameFarEast = "Meiryo UI"; rng.Font.Name = "Meiryo UI"
        rng.Font.Size = fs1; rng.Font.Fill.ForeColor.RGB = rgb(color1)
        rng.Font.Bold = -1 if bold1 else 0
        pf = rng.ParagraphFormat
        pf.SpaceWithin = 0.75; pf.LineRuleWithin = -1
        pf.SpaceBefore = 0; pf.SpaceAfter = 0

    def add_shape(name, x, y, w, h, kind, anchor_mid=True):
        p = PALETTE[kind]
        shp = ws.Shapes.AddShape(p["shape"], X0 + x, Y0 + y, w, h)
        shp.Name = name
        shp.Fill.ForeColor.RGB = rgb(p["fill"])
        shp.Line.ForeColor.RGB = rgb(p["line"])
        shp.Line.Weight = p["w"]
        if p["dash"]:
            shp.Line.DashStyle = 4  # msoLineDash
        else:
            shp.Line.DashStyle = 1
        tf = shp.TextFrame2
        tf.WordWrap = -1; tf.AutoSize = 0
        tf.MarginLeft = 2; tf.MarginRight = 2; tf.MarginTop = 1; tf.MarginBottom = 1
        tf.VerticalAnchor = 3 if anchor_mid else 1  # middle / top
        return shp

    # 帯2本
    ba = add_shape("band_a", *POS["band_a"], "note")
    ba.Fill.Visible = 0  # 塗なし
    ba.Line.ForeColor.RGB = rgb("BFBFBF"); ba.Line.Weight = 0.75
    bb = add_shape("band_b", 0, 312, 750, 54, "note")
    bb.Fill.Visible = 0
    bb.Line.ForeColor.RGB = rgb("BFBFBF"); bb.Line.Weight = 0.75
    # 帯見出し
    ha = add_shape("band_a_head", *POS["band_a_head"], "note")
    ha.Fill.ForeColor.RGB = rgb("404040"); ha.Line.Visible = 0
    ha.TextFrame2.TextRange.Text = texts["bands"]["a1"] + "\r" + texts["bands"]["a2"]
    style_text(ha.TextFrame2, 12, 10, "FFFFFF", "D9D9D9", bold1=True)
    ok, att = fit_text(ha, 400, "band_a_head")
    out["shapes"]["band_a_head"] = {"x": ha.Left - X0, "y": ha.Top - Y0, "w": ha.Width, "h": ha.Height, "fit": ok}
    hb = add_shape("band_b_head", 0, 316, 300, 18, "note")
    hb.Fill.ForeColor.RGB = rgb("404040"); hb.Line.Visible = 0
    hb.TextFrame2.TextRange.Text = texts["bands"]["b1"]
    style_text(hb.TextFrame2, 12, 10, "FFFFFF", "D9D9D9", bold1=True)
    ok, att = fit_text(hb, 400, "band_b_head")
    out["shapes"]["band_b_head"] = {"x": hb.Left - X0, "y": hb.Top - Y0, "w": hb.Width, "h": hb.Height, "fit": ok}

    # ノード19
    fails = []
    for nid in ["N01", "N02", "N03", "N04", "N05", "N06", "N07", "N08", "N09", "N10",
                "N11", "N12", "N13", "N14", "N15", "N16", "N17", "N18", "N19"]:
        name = NAME_OF[nid]
        x, y, w, h = POS[name]
        kind = STYLE_OF[nid]
        shp = add_shape(name, x, y, w, h, kind, anchor_mid=(nid != "N01"))
        if nid == "N01":
            shp.TextFrame2.TextRange.Text = texts["nodes"][nid]["label"]
            style_text(shp.TextFrame2, 11, 8)
        elif nid == "N05":
            shp.TextFrame2.TextRange.Text = "\r".join(texts["n05"])
            style_text(shp.TextFrame2, 8, 8)  # 注記ボックス本文8pt(追補2 §3)
        elif nid == "N19":
            shp.TextFrame2.TextRange.Text = texts["n19"]["label"] + "\r" + texts["n19"]["note"]
            style_text(shp.TextFrame2, 11, 8)
        else:
            shp.TextFrame2.TextRange.Text = texts["nodes"][nid]["label"] + "\r" + texts["nodes"][nid]["note"]
            style_text(shp.TextFrame2, 11, 8)
        if nid in ("N04", "N13", "N14"):
            shp.TextFrame2.TextRange.Font.Fill.ForeColor.RGB = rgb("404040")
        ok, att = fit_text(shp, X0 + WMAX.get(name, w + 60) - X0 - x + X0 if False else WMAX.get(name, w + 40), name)
        out["shapes"][name] = {"x": round(shp.Left - X0, 1), "y": round(shp.Top - Y0, 1),
                               "w": round(shp.Width, 1), "h": round(shp.Height, 1), "fit": ok, "attempts": att}
        if not ok:
            fails.append(name)
    out["assert_fails"] = fails

    # Z順序: 帯→帯見出し→容器→ノード(作成順でband_aが最背面·以後順次前面) — 現状の作成順で帯が先のためOK
    wb.Save
    wb.Save()
    wb.Close(False)
    out["ok"] = len(fails) == 0
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
print("ok:", out["ok"], "assert_fails:", out.get("assert_fails"))
for k, v in out["shapes"].items():
    print(k, v)
if out["errors"]:
    print("errors:", out["errors"])
