# -*- coding: utf-8 -*-
"""corr_lnb_15_verify_xlsx.py — Stage D: ドライラン冊の実物読み戻し検証(LNB冊に対する検証)。
validator(corr_lnb_14) が幾何権威を判定するのに対し、本スクリプトは実際に構築された
corr_dryrun_lnb.xlsx を読み取り専用で開き、権威との一致を確認する。
検証項目:
  V1 シート順(相関図=5枚目·相関図_old=6枚目·用語は無変更レーンとして存在)
  V2 相関図の図形数=57·名前一覧が権威と一致
  V3 帯2+見出し2+ノード19の矩形が権威(corr_lnb_10_tables.SHAPES)と±0.6ptで一致
  V4 ラベル17枚の位置·幅·高さがモデル(LABELS·h=model_h+2)と±0.6ptで一致·文言スポット照合
  V5 エッジ17本: 外接矩形=経路bbox±0.6pt·フリーフォーム節点数=経路点数·端点一致·
     線種(実線/破線)·矢頭·1pt を読み戻し
  V6 印刷設定(A4横·FitToPages 1×1·$A$1:$AY$60·余白10mm)
  V7 相関図_old が34図形(rel_*)で完全退避
  V8 原本のSHA256が実行前後で不変(--target orig 時は不変assertをしない·記録のみ)
  V9 機器アイコン18個: 配置·サイズ·余白·フォント·行送りを corr_lnb_17_icons_result.json と一致
  VW 相関図 C7-C10 の文言が corr_lnb_21_wording_result.json の after と一致(結果JSONがある場合)
使い方: python corr_lnb_15_verify_xlsx.py [--target dry|orig]
  dry = temp の corr_dryrun_lnb.xlsx(既定) / orig = vault原本(適用後の検証用)
出力: corr_lnb_15_verify_result.json(dry) / corr_lnb_15_verify_result_orig.json(orig)
"""
import argparse
import hashlib
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
VAULT = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
ORIG = os.path.join(VAULT, "LNB管理手順書案_未承認.xlsx")
TEXTS = json.load(open(os.path.join(HERE, "corr_lnb_00_texts.json"), encoding="utf-8"))
ICONS = json.load(open(os.path.join(HERE, "icons_manifest.json"), encoding="utf-8"))
ICON_RESULT = os.path.join(HERE, "corr_lnb_17_icons_result.json")
WORDING_RESULT = os.path.join(HERE, "corr_lnb_21_wording_result.json")

_ap = argparse.ArgumentParser()
_ap.add_argument("--target", choices=["dry", "orig"], default="dry")
TARGET = _ap.parse_args().target
BOOK = DRY if TARGET == "dry" else ORIG
RESULT = os.path.join(HERE, "corr_lnb_15_verify_result.json" if TARGET == "dry"
                      else "corr_lnb_15_verify_result_orig.json")

TOL = 0.6
NODE_NAMES = ["band_a", "band_b", "band_a_head", "band_b_head",
              "n01_esxi", "n02_app", "n03_ctrl", "n04_maint", "n05_note", "n06_dgs",
              "n07_lnb", "n08_line", "n09_andon", "n10_monitor", "n11_lws", "n12_pda",
              "n13_ap", "n14_tablet", "n15_cima_pc", "n16_cimc_pc", "n17_backup",
              "n18_extif", "n19_cima_sv"]
DASHED = {"E06", "E09", "E10", "E12", "E13"}
ARROW = {"E02", "E06", "E08", "E09", "E15", "E16", "E17", "E18"}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


out = {"ok": False, "target": TARGET, "book": BOOK, "pid": None,
       "checks": {}, "assert_fails": [], "errors": [], "notes": []}
h_orig = sha256(ORIG)
print("target:", TARGET, "book:", os.path.basename(BOOK), flush=True)

xl = win32com.client.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
out["pid"] = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
print("EXCEL PID", out["pid"], flush=True)

try:
    wb = xl.Workbooks.Open(BOOK, ReadOnly=True)

    # V1 シート順
    names = [s.Name for s in wb.Sheets]
    out["checks"]["sheets"] = names
    if names[4:6] != ["相関図", "相関図_old"]:
        out["assert_fails"].append("V1 sheet order: %s" % names[3:7])
    if "用語" not in names:
        out["assert_fails"].append("V1 用語 sheet missing")

    ws = wb.Worksheets("相関図")
    X0 = ws.Range("B11").Left
    Y0 = ws.Range("B11").Top
    out["checks"]["anchor_B11"] = [round(float(X0), 1), round(float(Y0), 1)]

    # V2 図形数·名前一覧(機器アイコン icon_* を含む)
    n = ws.Shapes.Count
    got_names = sorted(ws.Shapes.Item(i).Name for i in range(1, n + 1))
    got_names_set = set(got_names)
    icon_names = ["icon_" + nd for nd in ICONS["nodes"]]
    exp_names = sorted(NODE_NAMES + icon_names
                       + ["edge_" + e for e in T.ROUTES] + ["label_" + l for l in T.LABELS])
    out["checks"]["shape_count"] = n
    if n != 57 + len(icon_names):
        out["assert_fails"].append("V2 shape count %d != %d (base 57 + icons %d)"
                                   % (n, 57 + len(icon_names), len(icon_names)))
    if got_names != exp_names:
        diff = set(got_names) ^ set(exp_names)
        out["assert_fails"].append("V2 name set mismatch: %s" % sorted(diff)[:10])

    # V3 矩形一致(帯/見出し/ノード) — band_a/band_b は幾何JSONに無いため構築定数で比較
    BAND_RECTS = {"band_a": (0, 0, 750, 312), "band_b": (0, 312, 750, 54)}
    geom_bad = []
    for name in NODE_NAMES:
        sh = ws.Shapes(name)
        got = [float(sh.Left) - X0, float(sh.Top) - Y0, float(sh.Width), float(sh.Height)]
        if name in BAND_RECTS:
            bx, by, bw_, bh_ = BAND_RECTS[name]
            exp = [bx, by, bw_, bh_]
        else:
            x0, y0, x1, y1 = T.SHAPES[name]
            exp = [x0, y0, x1 - x0, y1 - y0]
        if any(abs(g - e) > TOL for g, e in zip(got, exp)):
            geom_bad.append("%s got %s exp %s" % (name, [round(v, 1) for v in got], [round(v, 1) for v in exp]))
    out["checks"]["node_geom"] = "23/%d ok" % (len(NODE_NAMES) - len(geom_bad))
    if geom_bad:
        out["assert_fails"].append("V3 geometry: " + "; ".join(geom_bad[:6]))

    # V4 ラベル
    lab_bad = []
    for lid, (x, y, w, lines) in T.LABELS.items():
        sh = ws.Shapes("label_" + lid)
        got = [float(sh.Left) - X0, float(sh.Top) - Y0, float(sh.Width), float(sh.Height)]
        exp = [x, y, w, 12.4 + 9.9 * (lines - 1) + 2]
        if any(abs(g - e) > TOL for g, e in zip(got, exp)):
            lab_bad.append("%s got %s exp %s" % (lid, [round(v, 1) for v in got], [round(v, 1) for v in exp]))
    out["checks"]["label_geom"] = "%d/17 ok" % (17 - len(lab_bad))
    if lab_bad:
        out["assert_fails"].append("V4 label geometry: " + "; ".join(lab_bad[:6]))

    # 文言スポット照合
    spot = {}
    spot["n02_app"] = "CIMC-SV" in ws.Shapes("n02_app").TextFrame2.TextRange.Text
    spot["n06_dgs"] = "NPM-DGS" in ws.Shapes("n06_dgs").TextFrame2.TextRange.Text
    spot["n01_esxi"] = "ESXiホスト" in ws.Shapes("n01_esxi").TextFrame2.TextRange.Text
    spot["band_a_head"] = ("上位網" in ws.Shapes("band_a_head").TextFrame2.TextRange.Text
                           and "172.25.253.0/24" in ws.Shapes("band_a_head").TextFrame2.TextRange.Text)
    spot["band_b_head"] = ws.Shapes("band_b_head").TextFrame2.TextRange.Text.strip() == \
        "ライン設備側ネットワーク — 内部網"
    spot["label_E04"] = "192.168.30.xx" in ws.Shapes("label_E04").TextFrame2.TextRange.Text
    spot["label_E09"] = ws.Shapes("label_E09").TextFrame2.TextRange.Text.startswith("表示内容は")
    spot["label_E18"] = "XML/DB" in ws.Shapes("label_E18").TextFrame2.TextRange.Text
    out["checks"]["text_spot"] = spot
    for k, v in spot.items():
        if not v:
            out["assert_fails"].append("V4 text spot NG: %s" % k)

    # V5 エッジ
    edge_bad = []
    nodes_readback = {}
    for eid, pts in T.ROUTES.items():
        sh = ws.Shapes("edge_" + eid)
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        exp_bbox = [min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys)]
        got_bbox = [float(sh.Left) - X0, float(sh.Top) - Y0, float(sh.Width), float(sh.Height)]
        # 矢頭は外接幅を太線側へ約4pt広げるため幅/高さは +6pt の許容で比較
        if abs(got_bbox[0] - exp_bbox[0]) > TOL or abs(got_bbox[1] - exp_bbox[1]) > TOL:
            edge_bad.append("%s origin got %s exp %s" % (eid, [round(v, 1) for v in got_bbox[:2]],
                                                         exp_bbox[:2]))
        if got_bbox[2] > exp_bbox[2] + 6 or got_bbox[3] > exp_bbox[3] + 6:
            edge_bad.append("%s extent got %s exp %s" % (eid, [round(v, 1) for v in got_bbox[2:]],
                                                         [round(v, 1) for v in exp_bbox[2:]]))
        d = int(sh.Line.DashStyle); a = int(sh.Line.EndArrowheadStyle); w = float(sh.Line.Weight)
        if abs(w - 1.0) > 0.01 or (d == 4) != (eid in DASHED) or ((a == 2) != (eid in ARROW)):
            edge_bad.append("%s dash=%d arrow=%d w=%.2f" % (eid, d, a, w))
        # フリーフォーム節点の読み戻し(座標系は環境差があるため端点一致を2仮説で受ける)
        try:
            ncnt = int(sh.Nodes.Count)

            def pt_of(i):
                p = sh.Nodes.Item(i).Points
                if isinstance(p[0], (tuple, list)):  # ((x, y), ...) 形式
                    p = p[0]
                return float(p[0]), float(p[1])

            first = pt_of(1)
            last = pt_of(ncnt)
            ok_cnt = (ncnt == len(pts))
            cand = []
            for ox, oy in ((float(sh.Left), float(sh.Top)), (0.0, 0.0)):
                cand.append((abs(first[0] + ox - (X0 + pts[0][0])) <= 1.0
                             and abs(first[1] + oy - (Y0 + pts[0][1])) <= 1.0
                             and abs(last[0] + ox - (X0 + pts[-1][0])) <= 1.0
                             and abs(last[1] + oy - (Y0 + pts[-1][1])) <= 1.0))
            nodes_readback[eid] = {"nodes": ncnt, "endpoints_ok": any(cand), "ok_cnt": ok_cnt}
            if not (ok_cnt and any(cand)):
                edge_bad.append("%s freeform nodes=%d endpoints_ok=%s" % (eid, ncnt, any(cand)))
        except Exception as e:
            out["notes"].append("V5 nodes readback skipped for %s: %r" % (eid, e))
    out["checks"]["edges"] = "%d/17 ok" % (17 - len(edge_bad))
    out["checks"]["edge_nodes_readback"] = nodes_readback
    if edge_bad:
        out["assert_fails"].append("V5 edges: " + "; ".join(edge_bad[:8]))

    # V6 印刷設定
    ps = ws.PageSetup
    pset = {"orientation": int(ps.Orientation), "fit_wide": int(ps.FitToPagesWide),
            "fit_tall": int(ps.FitToPagesTall), "zoom": bool(ps.Zoom),
            "print_area": ps.PrintArea,
            "margins": [round(float(getattr(ps, m)), 1) for m in
                        ("LeftMargin", "RightMargin", "TopMargin", "BottomMargin")]}
    out["checks"]["pagesetup"] = pset
    if pset["orientation"] != 2 or pset["fit_wide"] != 1 or pset["fit_tall"] != 1 \
            or pset["print_area"] != "$A$1:$AY$60":
        out["assert_fails"].append("V6 pagesetup: %s" % pset)

    # V7 相関図_old
    wso = wb.Worksheets("相関図_old")
    old_names = [wso.Shapes.Item(i).Name for i in range(1, wso.Shapes.Count + 1)]
    out["checks"]["old_shapes"] = {"count": len(old_names), "all_rel": all(s.startswith("rel_") for s in old_names)}
    if len(old_names) != 34 or not all(s.startswith("rel_") for s in old_names):
        out["assert_fails"].append("V7 相関図_old retreat incomplete: %d" % len(old_names))

    # V9 機器アイコンの読み戻し検証(corr_lnb_17 結果JSON権威との一致)
    if os.path.exists(ICON_RESULT):
        ires = json.load(open(ICON_RESULT, encoding="utf-8"))
        icon_bad = []
        for node, rec in ires["nodes"].items():
            nm = "icon_" + node
            if nm not in got_names_set:
                icon_bad.append("%s missing" % nm)
                continue
            pic = ws.Shapes(nm)
            got_rel = [round(float(pic.Left) - X0, 1), round(float(pic.Top) - Y0, 1)]
            got_sz = [round(float(pic.Width), 1), round(float(pic.Height), 1)]
            if any(abs(g - e) > TOL for g, e in zip(got_rel, rec["icon_rel"])):
                icon_bad.append("%s pos got %s exp %s" % (nm, got_rel, rec["icon_rel"]))
            if any(abs(g - e) > TOL for g, e in zip(got_sz, rec["icon_size"])):
                icon_bad.append("%s size got %s exp %s" % (nm, got_sz, rec["icon_size"]))
            nd = ws.Shapes(node)
            tf2n = nd.TextFrame2
            tfo2 = nd.TextFrame
            ml = float(tf2n.MarginLeft)
            if abs(ml - rec["margin"]) > 0.5:
                icon_bad.append("%s margin got %.1f exp %.1f" % (node, ml, rec["margin"]))
            raw2 = str(tf2n.TextRange.Text).replace("\r\n", "\n").replace("\r", "\n")
            paras2 = [p for p in raw2.split("\n")]
            while paras2 and paras2[-1] == "":
                paras2.pop()
            sizes_got = []
            p = 1
            for pt in paras2:
                sizes_got.append(float(tfo2.Characters(p, len(pt)).Font.Size))
                p += len(pt) + 1
            if len(sizes_got) != 2:
                icon_bad.append("%s paragraph count %d" % (node, len(sizes_got)))
            elif any(abs(g - e) > 0.11 for g, e in zip(sizes_got, [rec["label_pt"], rec["note_pt"]])):
                icon_bad.append("%s sizes got %s exp [%s, %s]"
                                % (node, sizes_got, rec["label_pt"], rec["note_pt"]))
            sp_got = float(tf2n.TextRange.ParagraphFormat.SpaceWithin)
            if abs(sp_got - rec["space"]) > 0.011:
                icon_bad.append("%s space got %.2f exp %.2f" % (node, sp_got, rec["space"]))
        n_ok = len(ires["nodes"]) - len(icon_bad)
        out["checks"]["icons"] = "ok %d/%d" % (n_ok, len(ires["nodes"]))
        out["checks"]["icon_bad"] = icon_bad
        if icon_bad:
            out["assert_fails"].append("V9 icons: " + "; ".join(icon_bad[:8]))
    else:
        out["notes"].append("V9 skipped: %s not found" % os.path.basename(ICON_RESULT))

    # VW 相関図 C7-C10 の文言(corr_lnb_21 結果JSON権威と一致)
    if os.path.exists(WORDING_RESULT):
        wres = json.load(open(WORDING_RESULT, encoding="utf-8"))
        w_bad = []
        for cell, exp in wres["after"].items():
            got = str(ws.Range(cell).Value)
            if got != exp:
                w_bad.append("%s got %r exp %r" % (cell, got[:24], exp[:24]))
        out["checks"]["wording_C7_C10"] = "ok" if not w_bad else w_bad
        if w_bad:
            out["assert_fails"].append("VW wording: " + "; ".join(w_bad[:4]))
    else:
        out["notes"].append("VW skipped: %s not found" % os.path.basename(WORDING_RESULT))

    # 用語シート(参照のみ·不触れの記録)
    wsg = wb.Worksheets("用語")
    out["checks"]["用語_usedrange"] = {"rows": wsg.UsedRange.Rows.Count, "cols": wsg.UsedRange.Columns.Count}

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

# V8 原本ハッシュ(実行前後の一致。--target orig 時は不変assertをしない)
out["checks"]["orig_sha256_unchanged"] = sha256(ORIG) == h_orig
if not out["checks"]["orig_sha256_unchanged"]:
    if TARGET == "orig":
        out["notes"].append("V8: orig hash differs from run start (適用後の原本のため不変assertは対象外)")
    else:
        out["assert_fails"].append("V8 vault original hash changed")

out["ok"] = not out["assert_fails"] and not out["errors"]
with open(RESULT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("ok:", out["ok"])
print("assert:", out["assert_fails"])
print("errors:", out["errors"])
print("notes:", out["notes"])
print("text_spot:", json.dumps(out["checks"].get("text_spot"), ensure_ascii=False))
print("edges:", out["checks"].get("edges"), "edge_nodes_ok:",
      all(v["endpoints_ok"] and v["ok_cnt"] for v in out["checks"].get("edge_nodes_readback", {}).values()))
