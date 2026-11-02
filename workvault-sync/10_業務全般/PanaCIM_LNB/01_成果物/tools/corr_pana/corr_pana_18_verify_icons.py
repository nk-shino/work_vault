# -*- coding: utf-8 -*-
"""corr_pana_18_verify_icons.py — Pana-CIM原本へのアイコン統合の読み戻し検証。
corr_lnb_15_verify_xlsx.py の V9(アイコン読み戻し)を Pana-CIM冊向けに独立させたもの。
検証項目:
  1 相関図の図形数=75(Stage5の57+アイコン18)·名前一覧(権威: corr_lnb_10_tables+icons_manifest)
  2 アイコン18個: 配置·サイズ·余白·フォント·行送りを corr_pana_17_icons_result.json と一致
  3 相関図_old が34図形(rel_*)で保全
  4 印刷設定(A4横·FitToPages 1×1·$A$1:$AY$60)·B11アンカー·n19のスポット文言
  5 用語シートの行数(参照記録·不触れ確認)
出力: corr_pana_18_verify_icons_result.json
"""
import hashlib
import json
import os
import sys
import time
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "corr_lnb"))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import corr_lnb_10_tables as T
import win32com.client
import win32process

VAULT = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
ORIG = os.path.join(VAULT, "Pana-CIM管理手順書案_未承認.xlsx")
ICON_RESULT = os.path.join(os.path.dirname(HERE), "corr_lnb", "corr_pana_17_icons_result.json")
RESULT = os.path.join(HERE, "corr_pana_18_verify_icons_result.json")

TOL = 0.6
NODE_NAMES = ["band_a", "band_b", "band_a_head", "band_b_head",
              "n01_esxi", "n02_app", "n03_ctrl", "n04_maint", "n05_note", "n06_dgs",
              "n07_lnb", "n08_line", "n09_andon", "n10_monitor", "n11_lws", "n12_pda",
              "n13_ap", "n14_tablet", "n15_cima_pc", "n16_cimc_pc", "n17_backup",
              "n18_extif", "n19_cima_sv"]
ICONS = json.load(open(os.path.join(os.path.dirname(HERE), "corr_lnb", "icons_manifest.json"), encoding="utf-8"))
IRES = json.load(open(ICON_RESULT, encoding="utf-8"))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


out = {"ok": False, "pid": None, "sha256": sha256(ORIG),
       "checks": {}, "assert_fails": [], "errors": [], "notes": []}
print("sha256:", out["sha256"][:16], "(適用前 0123260d… から変化していること=アイコン適用の証拠)", flush=True)

xl = win32com.client.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
out["pid"] = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
print("EXCEL PID", out["pid"], flush=True)
try:
    wb = xl.Workbooks.Open(ORIG, ReadOnly=True)
    names = [s.Name for s in wb.Sheets]
    out["checks"]["sheets"] = names
    if names[4:6] != ["相関図", "相関図_old"]:
        out["assert_fails"].append("sheet order: %s" % names[3:7])

    ws = wb.Worksheets("相関図")
    X0 = float(ws.Range("B11").Left)
    Y0 = float(ws.Range("B11").Top)
    out["checks"]["anchor_B11"] = [round(X0, 1), round(Y0, 1)]

    # 1 図形数·名前一覧
    n = ws.Shapes.Count
    got_names = sorted(ws.Shapes.Item(i).Name for i in range(1, n + 1))
    icon_names = ["icon_" + nd for nd in ICONS["nodes"]]
    exp_names = sorted(NODE_NAMES + icon_names
                       + ["edge_" + e for e in T.ROUTES] + ["label_" + l for l in T.LABELS])
    out["checks"]["shape_count"] = n
    if n != 75:
        out["assert_fails"].append("shape count %d != 75" % n)
    if got_names != exp_names:
        diff = set(got_names) ^ set(exp_names)
        out["assert_fails"].append("name set mismatch: %s" % sorted(diff)[:10])

    # 2 アイコン読み戻し
    icon_bad = []
    for node, rec in IRES["nodes"].items():
        nm = "icon_" + node
        if nm not in set(got_names):
            icon_bad.append("%s missing" % nm)
            continue
        pic = ws.Shapes(nm)
        got_rel = [round(float(pic.Left) - X0, 1), round(float(pic.Top) - Y0, 1)]
        got_sz = [round(float(pic.Width), 1), round(float(pic.Height), 1)]
        if any(abs(g - e) > TOL for g, e in zip(got_rel, rec["icon_rel"])):
            icon_bad.append("%s pos got %s exp %s" % (nm, got_rel, rec["icon_rel"]))
        if any(abs(g - e) > TOL for g, e in zip(got_sz, rec["icon_size"])):
            icon_bad.append("%s size got %s exp %s" % (nm, got_sz, rec["icon_size"]))
        nd_sh = ws.Shapes(node)
        tf2 = nd_sh.TextFrame2
        tfo = nd_sh.TextFrame
        ml = float(tf2.MarginLeft)
        if abs(ml - rec["margin"]) > 0.5:
            icon_bad.append("%s margin got %.1f exp %.1f" % (node, ml, rec["margin"]))
        raw = str(tf2.TextRange.Text).replace("\r\n", "\n").replace("\r", "\n")
        paras = [p for p in raw.split("\n")]
        while paras and paras[-1] == "":
            paras.pop()
        sizes_got = []
        p = 1
        for pt in paras:
            sizes_got.append(float(tfo.Characters(p, len(pt)).Font.Size))
            p += len(pt) + 1
        if len(sizes_got) != 2:
            icon_bad.append("%s paragraph count %d" % (node, len(sizes_got)))
        elif any(abs(g - e) > 0.11 for g, e in zip(sizes_got, [rec["label_pt"], rec["note_pt"]])):
            icon_bad.append("%s sizes got %s exp [%s, %s]"
                            % (node, sizes_got, rec["label_pt"], rec["note_pt"]))
        sp = float(tf2.TextRange.ParagraphFormat.SpaceWithin)
        if abs(sp - rec["space"]) > 0.011:
            icon_bad.append("%s space got %.2f exp %.2f" % (node, sp, rec["space"]))
    out["checks"]["icons"] = "ok %d/%d" % (len(IRES["nodes"]) - len(icon_bad), len(IRES["nodes"]))
    if icon_bad:
        out["assert_fails"].append("icons: " + "; ".join(icon_bad[:8]))

    # 3 相関図_old
    wso = wb.Worksheets("相関図_old")
    old_names = [wso.Shapes.Item(i).Name for i in range(1, wso.Shapes.Count + 1)]
    out["checks"]["old_shapes"] = {"count": len(old_names),
                                   "all_rel": all(s.startswith("rel_") for s in old_names)}
    if len(old_names) != 34 or not all(s.startswith("rel_") for s in old_names):
        out["assert_fails"].append("相関図_old retreat changed: %d" % len(old_names))

    # 4 印刷設定·スポット
    ps = ws.PageSetup
    pset = {"orientation": int(ps.Orientation), "fit_wide": int(ps.FitToPagesWide),
            "fit_tall": int(ps.FitToPagesTall), "print_area": ps.PrintArea}
    out["checks"]["pagesetup"] = pset
    if pset["orientation"] != 2 or pset["print_area"] != "$A$1:$AY$60":
        out["assert_fails"].append("pagesetup: %s" % pset)
    if "CIMA-SV" not in str(ws.Shapes("n19_cima_sv").TextFrame2.TextRange.Text):
        out["assert_fails"].append("n19 spot text NG")

    # 5 用語シート(参照記録)
    wsg = wb.Worksheets("用語")
    out["checks"]["用語_usedrange"] = {"rows": wsg.UsedRange.Rows.Count,
                                       "cols": wsg.UsedRange.Columns.Count}
    wb.Close(SaveChanges=False)
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
print("icons:", out["checks"].get("icons"))
print("assert:", out["assert_fails"])
print("errors:", out["errors"])
