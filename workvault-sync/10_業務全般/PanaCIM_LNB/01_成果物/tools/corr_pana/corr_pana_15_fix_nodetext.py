# -*- coding: utf-8 -*-
"""corr_pana_15_fix_nodetext.py (v2) — Stage 4 欠陥修復の確定版。
欠陥(2026-10-28 レンダ目視で確定):
  1) Stage 4 style_text が備考8ptを適用せず全ノード11pt→箱から溢れる
  2) Stage 4 fit_text が空テキスト状態の BoundHeight を測り全数 fit:true(検証空振り)
  3) 帯見出し: band_a_head(200×30)に12pt+10pt×各1行が入らず5行、band_b_head(300×18)に
     12pt×70字が入らず3行 → 箱を拡幅し1行/段落に修復(tables.py SHAPES override 済み)
  4) E18ラベル(210,9)が拡幅後のband_a ink内に入る → (628,64,116,2)へ移動
修復手段:
  - ノード: 1行目11pt/備考8pt(推定ノードは全体404040)·行送り0.75→fit失敗時0.6
    段落書式は TextRange2.Paragraphs(start,len) が Excel 非対応のため旧 TextFrame.Characters で適用
  - 見出し: band_a a1 12pt太字白+a2 10pt灰 各1行(実ink下端>23.5なら a1→11pt)·
    band_b b1 8pt太字白 1行(2行化なら 7.5pt)·テキスト再代入でリフロー強制後に実測
  - label_E18 を (628,64,116,2) へ移動·サイズ変更
  - 保存後 corr_pana_15_validate.py を再実行し HARD=0 を要求 → PDF/PNG 再レンダ
"""
import json, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import win32com.client
import win32process

DST = os.path.join(HERE, "corr_dryrun_pana.xlsx")
TEXTS = json.load(open(os.path.join(HERE, "corr_pana_14_texts.json"), encoding="utf-8"))
RESULT = os.path.join(HERE, "corr_pana_15_fix_result.json")
PDF = os.path.join(HERE, "corr_pana_15_stage5.pdf")
PNG = os.path.join(HERE, "corr_pana_15_stage5_p1.png")

NAME2NID = {v: k for k, v in {
    "N01": "n01_esxi", "N02": "n02_app", "N03": "n03_ctrl", "N04": "n04_maint", "N05": "n05_note",
    "N06": "n06_dgs", "N07": "n07_lnb", "N08": "n08_line", "N09": "n09_andon", "N10": "n10_monitor",
    "N11": "n11_lws", "N12": "n12_pda", "N13": "n13_ap", "N14": "n14_tablet", "N15": "n15_cima_pc",
    "N16": "n16_cimc_pc", "N17": "n17_backup", "N18": "n18_extif", "N19": "n19_cima_sv"}.items()}
ESTIMATE = {"N04", "N13", "N14"}

out = {"ok": False, "pid": None, "nodes": {}, "heads": {}, "label_E18": {}, "validate": None,
       "assert_fails": [], "errors": []}

xl = win32com.client.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
out["pid"] = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
print("EXCEL PID", out["pid"], flush=True)

def rgb(hexstr):  # 全色がグレー系のため単純変換で十分
    return int(hexstr, 16)

def apply_paras(shp, para_texts, specs):
    """再代入→全体=最終段落→差分段落を旧 Characters で上書き→行送り0.75→実測。
    specs: [(size, hexcolor, bold), ...] 戻り値 (bound_h, space)"""
    tf2 = shp.TextFrame2
    rng = tf2.TextRange
    rng.Text = "\r".join(para_texts)  # 再代入でリフロー強制
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
    wb = xl.Workbooks.Open(DST)
    ws = wb.Worksheets("相関図")
    X0 = ws.Range("B11").Left
    Y0 = ws.Range("B11").Top

    # ---------- 見出し箱の拡幅(tables.py SHAPES override と一致させる) ----------
    ha = ws.Shapes("band_a_head")
    hb = ws.Shapes("band_b_head")
    ha.Width = 470.0
    hb.Left = X0 + 178.0   # N07(0,294,176,36)が旧配置x0-176に重なりb1前方を隠すためN07の右へ
    hb.Width = 248.0       # x178-426(E07縦線x430の手前4pt)
    out["heads"]["geometry"] = {
        "band_a_head": [round(ha.Left - X0, 1), round(ha.Top - Y0, 1), round(ha.Width, 1), round(ha.Height, 1)],
        "band_b_head": [round(hb.Left - X0, 1), round(hb.Top - Y0, 1), round(hb.Width, 1), round(hb.Height, 1)],
    }

    # ---------- ノード19: 1行目11pt/備考8pt ----------
    for name, nid in NAME2NID.items():
        try:
            shp = ws.Shapes(name)
            if nid == "N05":
                ts = list(TEXTS["n05"]); specs = [(8, "595959", False)] * len(ts)
                max_b = shp.Height - 2
            elif nid == "N19":
                ts = [TEXTS["n19"]["label"], TEXTS["n19"]["note"]]
                specs = [(11, "1F1F1F", False), (8, "595959", False)]
                max_b = shp.Height - 2
            else:
                c = "404040" if nid in ESTIMATE else "1F1F1F"
                cn = c if nid in ESTIMATE else "595959"
                ts = [TEXTS["nodes"][nid]["label"], TEXTS["nodes"][nid]["note"]]
                specs = [(11, c, False), (8, cn, False)]
                max_b = shp.Height - 2
            bh, sp, rng = fit_with_fallback(shp, ts, specs, max_b)
            if nid == "N17" and bh > shp.Height - 2:
                # 長いパス文字列で折返し増大 → ラベル11pt→10ptへ(備考8ptは維持)
                specs = [(10, "1F1F1F", False), (8, "595959", False)]
                bh, sp, rng = fit_with_fallback(shp, ts, specs, max_b)
                out["nodes"][name + "_fallback"] = "label 10pt"
            out["nodes"][name] = {"bound_h": bh, "h": round(shp.Height, 1), "space": sp,
                                  "fit": bh <= shp.Height - 2}
            if bh > shp.Height - 2:
                out["assert_fails"].append("node %s bound %.1f > %.1f" % (name, bh, shp.Height - 2))
        except Exception as e:
            out["errors"].append(("node %s: %r" % (name, e))[:140])

    # ---------- 帯見出し ----------
    try:
        # band_a: a1 12pt太字 + a2 10pt 各1行。実ink下端(=1+bound)は y25(E18レーン)未満。
        bh, sp, rng = fit_with_fallback(ha, [TEXTS["bands"]["a1"], TEXTS["bands"]["a2"]],
                                        [(12, "FFFFFF", True), (10, "D9D9D9", False)], 22.5)
        used_a1 = 12.0
        if 1.0 + bh > 23.5:  # a1 を 11pt へ落として再試行
            bh, sp, rng = fit_with_fallback(ha, [TEXTS["bands"]["a1"], TEXTS["bands"]["a2"]],
                                            [(11, "FFFFFF", True), (10, "D9D9D9", False)], 22.5)
            used_a1 = 11.0
        ink_btm = round(1.0 + bh, 2)
        out["heads"]["band_a_head"] = {"a1_pt": used_a1, "bound_h": bh, "bound_w": round(rng.BoundWidth, 1),
                                       "ink_bottom": ink_btm, "h": round(ha.Height, 1), "space": sp,
                                       "fit": ink_btm <= 24.5}
        if ink_btm > 24.5:
            out["assert_fails"].append("band_a_head ink bottom %.2f >= y25 lane -0.5" % ink_btm)
    except Exception as e:
        out["errors"].append(("band_a_head: %r" % e)[:140])
    try:
        # band_b: 題名部のみ 12pt太字白 1行(箱はN07の右 x178-426)。セグメント詳細はE05ラベル既載+Stage 6注記へ繰延。
        b1_title = "ライン設備側ネットワーク — 内部網"
        for fs in (12.0, 11.0, 10.0):
            bh, sp, rng = fit_with_fallback(hb, [b1_title], [(fs, "FFFFFF", True)], 13.0)
            if bh <= 13.0 and rng.BoundWidth <= 244.0:
                break
        hb.Top = Y0 + 315.0                  # ink下端をE07レーン(y330·ストローク上端329.625)から十分離す
        hb.TextFrame2.MarginTop = 0.5
        ink_btm = round(hb.Top - Y0 + hb.TextFrame2.MarginTop + bh, 2)
        out["heads"]["band_b_head"] = {"b1_pt": fs, "bound_h": bh, "bound_w": round(rng.BoundWidth, 1),
                                       "ink_bottom": ink_btm, "h": round(hb.Height, 1), "space": sp,
                                       "fit": bh <= 13.0 and rng.BoundWidth <= 244.0 and ink_btm <= 328.5}
        if bh > 13.0 or rng.BoundWidth > 244.0 or ink_btm > 328.5:
            out["assert_fails"].append("band_b_head b1 %.1fpt bound %.2f w %.1f ink_btm %.2f (要求: 1行·w<=244·ink<=328.5)"
                                       % (fs, bh, rng.BoundWidth, ink_btm))
    except Exception as e:
        out["errors"].append(("band_b_head: %r" % e)[:140])

    # ---------- E18ラベル移動 ----------
    try:
        lb = ws.Shapes("label_E18")
        lb.Left = X0 + 666.0
        lb.Top = Y0 + 314.0
        lb.Width = 82.0
        lb.Height = 34.2  # model_h(32.2) + 2
        out["label_E18"] = {"pos": [round(lb.Left - X0, 1), round(lb.Top - Y0, 1)],
                            "wh": [round(lb.Width, 1), round(lb.Height, 1)],
                            "text_head": lb.TextFrame2.TextRange.Text[:16]}
    except Exception as e:
        out["errors"].append(("label_E18: %r" % e)[:140])

    # ---------- 印刷範囲の下端拡張(行グリッドが図域より短く下端19.9ptが欠ける対策·行高は図形が歪むため触らない) ----------
    ps = ws.PageSetup
    before_pa = ps.PrintArea
    ps.PrintArea = "$A$1:$AY$60"
    out["print"] = {"before": before_pa, "after": ps.PrintArea,
                    "fig_bottom_abs": round(Y0 + 366.0, 1),
                    "row60_bottom_abs": round(ws.Rows(60).Top + ws.Rows(60).RowHeight, 1)}
    if ws.Rows(60).Top + ws.Rows(60).RowHeight < Y0 + 366.0:
        out["assert_fails"].append("print area row60 bottom < figure bottom")

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
            out["errors"].append("killed residual %d" % out["pid"])
    except Exception as e:
        out["errors"].append(("cleanup: %r" % e)[:80])

# ---------- バリデータ再実行 ----------
try:
    r = subprocess.run([sys.executable, os.path.join(HERE, "corr_pana_15_validate.py"), "--json"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    vj = json.load(open(os.path.join(HERE, "corr_pana_15_validate_result.json"), encoding="utf-8"))
    out["validate"] = {"hard": len(vj.get("hard", [])), "crossings": len(vj.get("crossings", [])),
                       "soft": len(vj.get("soft", [])), "rc": r.returncode}
    if vj.get("hard"):
        out["assert_fails"].append("validator HARD: %s" % json.dumps(vj["hard"], ensure_ascii=False)[:400])
except Exception as e:
    out["errors"].append(("validate: %r" % e)[:140])

# ---------- 再レンダ ----------
try:
    xl2 = win32com.client.DispatchEx("Excel.Application")
    xl2.Visible = False
    xl2.DisplayAlerts = False
    pid2 = win32process.GetWindowThreadProcessId(xl2.Hwnd)[1]
    try:
        wb2 = xl2.Workbooks.Open(DST, ReadOnly=True)
        wb2.Worksheets("相関図").ExportAsFixedFormat(0, PDF, 0, True, False)
        wb2.Close(False)
    finally:
        xl2.Quit()
        time.sleep(2)
        chk = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid2], capture_output=True, text=True)
        if "EXCEL" in chk.stdout.upper():
            subprocess.run(["taskkill", "/PID", str(pid2), "/F"], capture_output=True)
            out["errors"].append("killed residual %d" % pid2)
    import fitz
    doc = fitz.open(PDF)
    doc[0].get_pixmap(dpi=150).save(PNG)
    out["render"] = {"pdf": PDF, "png": PNG, "pdf_pages": doc.page_count}
    doc.close()
except Exception as e:
    out["errors"].append(("render: %r" % e)[:160])

out["ok"] = not out["assert_fails"] and not out["errors"]
with open(RESULT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("ok:", out["ok"])
print("assert_fails:", out["assert_fails"])
print("errors:", out["errors"])
print("validate:", out["validate"])
print("heads:", json.dumps({k: v for k, v in out["heads"].items() if k != "geometry"}, ensure_ascii=False))
print("label_E18:", out["label_E18"])
bad = {k: v for k, v in out["nodes"].items() if isinstance(v, dict) and not v.get("fit")}
print("node fit fails:", bad if bad else "none")
print("render:", out.get("render"))
