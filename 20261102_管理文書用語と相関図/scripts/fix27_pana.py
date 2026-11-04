# -*- coding: utf-8 -*-
"""fix27_pana.py — Pana-CIM冊の是正(エントリ27 [F1]〜[F6])。

Phase A(読み取り専用): 余白·表紙図形·様式ラベル箱·対象セルの現状を実測し
  チェックシートのレンダ(PDF)を出力。
Phase B(変更): [F3]表紙図形20個削除 → [F1]余白をInchesToPointsで再設定(14シート) →
  [F2]IP·OS未確認注記4件 → [F4]稼働率HTMLの保留明示(C7追記+第11章 No.28新規行) →
  [F6]様式ラベル箱の修復(文字幅確保) → 保存。
Phase C(再構築): 改ページの幽霊検査と必要時の補正 → 空頁0検定 → FirstPageNumber再設定 →
  17シート個別PDF→pypdf結合で冊PDF(頁数一致アサート)。

不変: 相関図(0.394統一)·相関図_old·完全引用区間·置換禁止表記·会議記録文言·保留事項。
"""
import os, sys, json, math, traceback

WORK = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
XLSX = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\Pana-CIM管理手順書案_未承認.xlsx"
VAULT_PDF = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\Pana-CIM管理手順書案_未承認.pdf"
PAGES_DIR = os.path.join(WORK, "scripts", "tmp_pages8")
RENDER_DIR = os.path.join(WORK, "scripts", "fix27_render")
REPORT = os.path.join(WORK, "scripts", "fix27_pana_report.json")

ORDER = ["表紙", "目次", "用語", "構成と管理情報", "相関図", "相関図_old", "管理体制",
         "月次再起動", "バックアップ", "復旧", "異常時の対応", "チェックシート(月次・異常時)",
         "会議課題一覧(一時)", "付録 引用元と確認範囲", "要確認事項一覧", "7-5仮_サービス起動停止"]
MARGIN14 = [n for n in ORDER if n not in ("相関図", "相関図_old")]
MARGINS_IN = {"Left": 0.87, "Right": 0.51, "Top": 0.59, "Bottom": 0.79, "Header": 0.59, "Footer": 0.39}
PREV_COUNTS = {"表紙": 1, "目次": 1, "用語": 2, "構成と管理情報": 1, "相関図": 1, "相関図_old": 1,
               "管理体制": 1, "月次再起動": 3, "バックアップ": 8, "復旧": 1, "異常時の対応": 17,
               "チェックシート(月次・異常時)": 2, "会議課題一覧(一時)": 2, "付録 引用元と確認範囲": 2,
               "要確認事項一覧": 2, "7-5仮_サービス起動停止": 2}
IMG_SHEETS = ("月次再起動", "バックアップ", "異常時の対応", "7-5仮_サービス起動停止")

FONT = "Meiryo UI"
COLS = [chr(65 + i) for i in range(26)] + ["A" + chr(65 + i) for i in range(26)]  # A..AZ

REP = {"phaseA": {}, "actions": [], "texts": [], "margins": {}, "shapes": {}, "boxes": {},
       "breaks_kept": {}, "ghost_fix": {}, "counts": {}, "counts_pass2": {}, "blanks": {},
       "numbering": {}, "book_pages": None, "errors": []}

def act(msg):
    REP["actions"].append(msg)
    print("[act]", msg, flush=True)

def px(w):
    return int(((256.0 * w + 18.0) / 256.0) * 7) + 5

def col_range_width_pt(ws, c1, c2):
    i1, i2 = COLS.index(c1), COLS.index(c2)
    return sum(px(ws.Columns[COLS[i]].ColumnWidth) for i in range(i1, i2 + 1)) * 0.75

def units(s):
    return sum(1.0 if ord(ch) > 0x2E80 else 0.5 for ch in s)

def calc_lines(text, width_pt, size):
    per = max(4.0, width_pt / size)
    n = 0
    for seg in str(text).split("\n"):
        n += max(1, math.ceil(units(seg) / per - 1e-9))
    return n

def row_h_body(ws, r, c1, c2, size=11.0, pitch=15.0):
    v = ws.Range(f"{c1}{r}").Value
    if v is None or str(v) == "":
        return None
    w = col_range_width_pt(ws, c1, c2)
    n = calc_lines(v, w, size)
    ws.Rows[r].RowHeight = n * pitch + 4.1
    return n

def get_val(ws, addr):
    v = ws.Range(addr).Value
    return "" if v is None else str(v)

def read_margins(ws):
    ps = ws.PageSetup
    out = {}
    for k in ("Left", "Right", "Top", "Bottom", "Header", "Footer"):
        v = float(getattr(ps, k + "Margin"))
        out[k] = round(v, 2)
        out[k + "_in"] = round(v / 72.0, 4)
    return out

def label_box_info(ws):
    """様式行2·3のラベル結合箱の幅を実測(COM·pt→px)。"""
    out = {}
    for tag, addr in (("mgmt", "W2"), ("page", "AU2")):
        c = ws.Range(addr)
        merged = bool(c.MergeCells) if c.MergeCells != 0 else False
        try:
            area = c.MergeArea
            w_pt = float(area.Width)
            val = get_val(ws, addr)
        except Exception:
            w_pt, val, merged = float(c.Width), get_val(ws, addr), False
        out[tag] = {"addr": addr, "merged": merged, "width_pt": round(w_pt, 1),
                    "width_px": int(round(w_pt * 4.0 / 3.0)), "value": val}
    return out

def manual_breaks(ws):
    out = []
    for i in range(1, ws.HPageBreaks.Count + 1):
        pb = ws.HPageBreaks.Item(i)
        try:
            t = int(pb.Type)
        except Exception:
            t = -1
        out.append((int(pb.Location.Row), t))
    return sorted(r for r, t in out if t == -4135)

def main():
    os.makedirs(PAGES_DIR, exist_ok=True)
    os.makedirs(RENDER_DIR, exist_ok=True)
    import win32com.client as win32
    import pymupdf
    try:
        from pypdf import PdfReader, PdfWriter
    except Exception:
        from PyPDF2 import PdfReader, PdfWriter
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    wb = None
    try:
        # ================= Phase A: 実測(読み取り専用) =================
        wb = app.Workbooks.Open(XLSX, UpdateLinks=0, ReadOnly=True)
        wsmap = {sh.Name: sh for sh in wb.Worksheets}
        assert len(wsmap) == 16, f"sheet count {len(wsmap)}"

        A = REP["phaseA"]
        A["margins"] = {n: read_margins(wsmap[n]) for n in ORDER}
        shapes = []
        for sh in wsmap["表紙"].Shapes:
            shapes.append({"name": sh.Name, "type": int(sh.Type)})
        A["cover_shapes"] = shapes
        act(f"COVER SHAPES: {len(shapes)} -> {[s['name'] for s in shapes]}")
        A["boxes"] = {n: label_box_info(wsmap[n]) for n in ORDER}
        A["breaks"] = {n: manual_breaks(wsmap[n]) for n in ORDER}
        A["cell_values"] = {
            "月次再起動.C12": get_val(wsmap["月次再起動"], "C12"),
            "月次再起動.C82": get_val(wsmap["月次再起動"], "C82"),
            "用語.C12": get_val(wsmap["用語"], "C12"),
            "用語.C20": get_val(wsmap["用語"], "C20"),
            "バックアップ.C7": get_val(wsmap["バックアップ"], "C7"),
            "要確認事項一覧.C35": get_val(wsmap["要確認事項一覧"], "C35"),
            "要確認事項一覧.C36": get_val(wsmap["要確認事項一覧"], "C36"),
        }
        # チェックシートのレンダ(修正前)
        ck_pdf = os.path.join(RENDER_DIR, "チェックシート_before.pdf")
        wsmap["チェックシート(月次・異常時)"].ExportAsFixedFormat(0, ck_pdf, 0, True, False)
        doc = pymupdf.open(ck_pdf)
        pix = doc[0].get_pixmap(dpi=200, clip=pymupdf.Rect(0, 0, doc[0].rect.width, 300))
        pix.save(os.path.join(RENDER_DIR, "チェックシート_before_top.png"))
        doc.close()
        act("PHASE A done (checklist render saved)")
        wb.Close(SaveChanges=False)
        wb = None

        # ================= Phase B: 変更 =================
        wb = app.Workbooks.Open(XLSX, UpdateLinks=0, ReadOnly=False)
        try:
            wb.AutoSaveOn = False
        except Exception:
            pass
        wsmap = {sh.Name: sh for sh in wb.Worksheets}

        # ---- [F3] 表紙図形20個削除 ----
        shs = list(wsmap["表紙"].Shapes)
        names = sorted(s.Name for s in shs)
        assert len(shs) == 20, f"cover shapes {len(shs)} != 20"
        assert sum(1 for s in shs if s.Name.startswith("Group")) == 17
        assert "Freeform 104" in names and "Text Box 105" in names and "直線コネクタ 2" in names
        for s in shs:
            REP["shapes"].setdefault("deleted", []).append({"name": s.Name, "type": int(s.Type)})
            s.Delete()
        n_after = wsmap["表紙"].Shapes.Count
        REP["shapes"]["count_after"] = n_after
        assert n_after == 0, f"cover shapes after delete: {n_after}"
        act("F3 cover shapes deleted: 20 -> 0")

        # ---- [F1] 余白の再設定 ----
        for name in MARGIN14:
            ps = wsmap[name].PageSetup
            before = read_margins(wsmap[name])
            ps.LeftMargin = app.InchesToPoints(MARGINS_IN["Left"])
            ps.RightMargin = app.InchesToPoints(MARGINS_IN["Right"])
            ps.TopMargin = app.InchesToPoints(MARGINS_IN["Top"])
            ps.BottomMargin = app.InchesToPoints(MARGINS_IN["Bottom"])
            ps.HeaderMargin = app.InchesToPoints(MARGINS_IN["Header"])
            ps.FooterMargin = app.InchesToPoints(MARGINS_IN["Footer"])
            after = read_margins(wsmap[name])
            REP["margins"][name] = {"before_pt": {k: before[k] for k in MARGINS_IN},
                                    "after_pt": {k: after[k] for k in MARGINS_IN},
                                    "after_in": {k: round(after[k] / 72.0, 4) for k in MARGINS_IN}}
        for name in ("相関図", "相関図_old"):
            REP["margins"][name] = {"untouched": True, "pt": read_margins(wsmap[name])}
        act("F1 margins re-set via InchesToPoints (14 sheets)")

        # ---- [F2] IP·OS未確認注記(4件) ----
        def append_note(sheet, addr, expect_tail, note, tag):
            ws = wsmap[sheet]
            old = get_val(ws, addr)
            if note in old:
                REP["texts"].append({"tag": tag, "cell": f"{sheet}.{addr}", "status": "OK(already)"})
                return
            assert old.endswith(expect_tail), f"{tag}: tail mismatch: ...{old[-40:]!r}"
            new = old + note
            ws.Range(addr).Value = new
            n = row_h_body(ws, int(addr[1:]), "C", "AZ")
            REP["texts"].append({"tag": tag, "cell": f"{sheet}.{addr}", "status": "OK",
                                 "rows": n, "len": len(new)})
            act(f"F2 {tag} {sheet}.{addr} rows={n}")

        append_note("月次再起動", "C12", "Windows の手順を Linux の手順へ置き換えない",
                    "。ゲストOS の表記(RHEL 6)の一次資料確認は未実施。", "T20")
        append_note("月次再起動", "C82", "とナビゲータが表示される",
                    "。表記の IP アドレスの一次資料確認は未実施。", "T21")
        append_note("用語", "C12", "ノートPC右隣の白枠モニタに表示される",
                    "。OS の版数と表記の IP アドレスの一次資料確認は未実施。", "T22")
        append_note("用語", "C20", "バージョン6・64ビット(第2章2-1)",
                    "。版数の一次資料確認は未実施。", "T23")

        # ---- [F4] 稼働率HTMLとバックアップ対象の境界(保留明示) ----
        bk = wsmap["バックアップ"]
        old7 = get_val(bk, "C7")
        ins = "稼働率フォルダに保存される Pana-CIM 出力の HTML が「実績帳票」のバックアップ対象に含まれるかは未確認(第11章 No.28 参照)。"
        if ins not in old7:
            key = "対象は DB データ・ジョブデータ・LNB 設定・実績帳票。"
            assert key in old7, "F4: C7 anchor sentence not found"
            new7 = old7.replace(key, key + ins, 1)
            bk.Range("C7").Value = new7
            n = row_h_body(bk, 7, "C", "AZ")
            REP["texts"].append({"tag": "T24", "cell": "バックアップ.C7", "status": "OK", "rows": n})
            act(f"F4 T24 バックアップ.C7 rows={n}")
        else:
            REP["texts"].append({"tag": "T24", "cell": "バックアップ.C7", "status": "OK(already)"})
        yk = wsmap["要確認事項一覧"]
        v36 = get_val(yk, "C36")
        if v36 == "":
            newval = ("28：稼働率 HTML のバックアップ対象への包含／稼働率フォルダに保存される "
                      "Pana-CIM 出力の HTML が「実績帳票」のバックアップ対象に含まれるかは未確認。"
                      "含める・対象外の判断は未了")
            yk.Range("C36:AZ36").Merge()
            try:
                yk.Range("A35:AZ35").Copy()
                yk.Range("A36:AZ36").PasteSpecial(Paste=-4122)  # xlPasteFormats
                app.CutCopyMode = False
                REP["texts"].append({"tag": "T25-fmt", "cell": "要確認事項一覧.A36:AZ36",
                                     "status": "OK (formats from r35)"})
            except Exception as e:
                app.CutCopyMode = False
                REP["texts"].append({"tag": "T25-fmt", "cell": "要確認事項一覧.A36:AZ36",
                                     "status": f"WARN: {e}"})
                act(f"F4 T25 format copy WARN: {e}")
            c = yk.Range("C36")
            c.Font.Name = FONT
            c.Font.Size = 11.0
            c.Font.Bold = False
            c.Font.Strikethrough = False
            c.WrapText = True
            c.HorizontalAlignment = -4131
            c.VerticalAlignment = -4160
            yk.Range("C36").Value = newval
            n = row_h_body(yk, 36, "C", "AZ")
            yk.PageSetup.PrintArea = "$A$1:$AZ$37"
            REP["texts"].append({"tag": "T25", "cell": "要確認事項一覧.C36", "status": "OK",
                                 "rows": n, "print_area": "$A$1:$AZ$37"})
            act(f"F4 T25 要確認事項一覧.C36 rows={n} print_area -> $A$1:$AZ$37")
        else:
            REP["texts"].append({"tag": "T25", "cell": "要確認事項一覧.C36", "status": "OK(already)"})

        # ---- [F6] 様式ラベル箱の修復(文字幅確保) ----
        FIX_SHEETS = []
        for name in ORDER:
            if name in ("相関図", "相関図_old", "表紙"):
                continue  # 図解·表紙は列幅不触(実測のみ)
            b = label_box_info(wsmap[name])
            # ラベル値が空の箱(7-5仮など様式未確定シート)は修復対象外(視覚欠損がないため)
            need_w = b["mgmt"]["width_px"] < 70 and b["mgmt"]["value"] != ""
            need_p = b["page"]["width_px"] < 18 and b["page"]["value"] != ""
            if need_w or need_p:
                FIX_SHEETS.append(name)
        REP["boxes"]["fix_targets"] = FIX_SHEETS
        for name in FIX_SHEETS:
            ws = wsmap[name]
            for c in range(23, 29):  # W..AB
                ws.Columns[c].ColumnWidth = 1.0
            for c in range(47, 49):  # AU..AV
                ws.Columns[c].ColumnWidth = 0.72
            b2 = label_box_info(ws)
            REP["boxes"][name] = {"before": A["boxes"][name], "after": b2}
            act(f"F6 {name}: W2:AB2 {b['mgmt']['width_px']}px -> {b2['mgmt']['width_px']}px, "
                f"AU2:AV2 {b['page']['width_px']}px -> {b2['page']['width_px']}px")
        act(f"F6 fix targets: {FIX_SHEETS}")

        # ---- 幅方向の収まり検査(F6対象は必要時に幅フィット = LNB fix_boxes v3 方式) ----
        REP["boxes"]["width_check"] = {}
        for name in MARGIN14:
            ws = wsmap[name]
            ps = ws.PageSetup
            try:
                zoom = ps.Zoom
            except Exception:
                zoom = None
            fitted = (zoom is False) or (zoom == 0)
            pa = str(ps.PrintArea or "")
            right_col = "AZ"
            try:
                if pa and ":" in pa:
                    seg = pa.split(",")[0].split(":")[1]
                    right_col = "".join(ch for ch in seg if ch.isalpha()) or "AZ"
            except Exception:
                pass
            content_pt = float(ws.Range(f"A1:{right_col}1").Width)
            printable = 595.28 - float(ps.LeftMargin) - float(ps.RightMargin)
            over = content_pt > printable + 0.5
            entry = {"print_area": pa, "right_col": right_col, "content_pt": round(content_pt, 1),
                     "printable_pt": round(printable, 1), "fitted_before": bool(fitted), "over": bool(over)}
            if over and not fitted:
                if name in FIX_SHEETS:
                    ps.Zoom = False
                    ps.FitToPagesWide = 1
                    ps.FitToPagesTall = False
                    entry["action"] = "FIT applied (1 page wide, tall auto)"
                    act(f"WIDTHEFIT {name}: {entry['content_pt']}pt > {entry['printable_pt']}pt -> fit 1x auto")
                else:
                    entry["action"] = "OVERWIDTH (not a fix target - REVIEW)"
                    act(f"OVERWIDTH-WARN {name}: {entry['content_pt']}pt > {entry['printable_pt']}pt")
            REP["boxes"]["width_check"][name] = entry

        wb.Save()
        act("SAVED (pass1: F1-F6)")

        # ---- チェックシートのレンダ(修正後) ----
        ck_pdf = os.path.join(RENDER_DIR, "チェックシート_after.pdf")
        wsmap["チェックシート(月次・異常時)"].ExportAsFixedFormat(0, ck_pdf, 0, True, False)
        doc = pymupdf.open(ck_pdf)
        pix = doc[0].get_pixmap(dpi=200, clip=pymupdf.Rect(0, 0, doc[0].rect.width, 300))
        pix.save(os.path.join(RENDER_DIR, "チェックシート_after_top.png"))
        doc.close()

        # ================= Phase C: 改ページ·採番·冊PDF =================
        def export_all():
            counts, blanks = {}, {}
            for name in ORDER:
                sh = wsmap[name]
                p = os.path.join(PAGES_DIR, f"{name}.pdf")
                sh.ExportAsFixedFormat(0, p, 0, True, False)
                rd = PdfReader(p)
                counts[name] = len(rd.pages)
                bl = []
                for i, pg in enumerate(rd.pages):
                    txt = pg.extract_text() or ""
                    try:
                        im = len(pg.images)
                    except Exception:
                        im = 1
                    if len(txt) < 80 and im == 0:
                        bl.append(i + 1)
                if bl:
                    blanks[name] = bl
            return counts, blanks

        def page_starts(ws):
            brs = manual_breaks(ws)
            return [1] + brs

        def ghosts_of(ws, path, title_bottom):
            doc = pymupdf.open(path)
            bad = []
            for pi in range(doc.page_count):
                for inf in doc[pi].get_image_info():
                    b = inf["bbox"]
                    if b[1] < title_bottom - 2.0 or b[3] > 786.0:
                        bad.append({"page": pi + 1, "y0": round(b[1], 1), "y1": round(b[3], 1)})
            doc.close()
            return bad

        def title_bottom(ws):
            ps = ws.PageSetup
            tb = float(ps.TopMargin)
            tr = str(ps.PrintTitleRows or "")
            if ":" in tr:
                a = "".join(ch for ch in tr.split(":")[0] if ch.isdigit())
                b = "".join(ch for ch in tr.split(":")[1].split(",")[0] if ch.isdigit())
                if a and b:
                    tb += sum(float(ws.Rows[r].RowHeight) for r in range(int(a), int(b) + 1))
            return tb

        # 幽霊検査と補正(最大4ラウンド): 手動改ページ位置を1行後ろへシフト
        for rnd in range(4):
            allbad = {}
            for name in IMG_SHEETS:
                ws = wsmap[name]
                path = os.path.join(PAGES_DIR, f"{name}.pdf")
                ws.ExportAsFixedFormat(0, path, 0, True, False)
                bad = ghosts_of(ws, path, title_bottom(ws))
                if bad:
                    allbad[name] = bad
            REP["ghost_fix"].setdefault("rounds", []).append(allbad)
            act(f"GHOSTCHECK round{rnd+1}: {allbad}")
            if not allbad:
                break
            for name, bad in allbad.items():
                ws = wsmap[name]
                starts = page_starts(ws)
                shifted = []
                for g in bad:
                    pgn = g["page"]
                    if pgn - 1 < len(starts):
                        srow = starts[pgn - 1]
                        if srow in manual_breaks(ws):
                            for i in range(1, ws.HPageBreaks.Count + 1):
                                pb = ws.HPageBreaks.Item(i)
                                if int(pb.Location.Row) == srow and int(pb.Type) == -4135:
                                    pb.Delete()
                                    ws.HPageBreaks.Add(ws.Range(f"A{srow + 1}"))
                                    shifted.append(f"{srow}->{srow+1}")
                                    break
                        else:
                            # 自動改ページで切れている場合: 画像の先頭行へ手動改ページを追加
                            added = []
                            for sh in ws.Shapes:
                                try:
                                    if int(sh.Type) in (13, 10) and int(sh.TopLeftCell.Row) > srow:
                                        added.append(int(sh.TopLeftCell.Row))
                                except Exception:
                                    pass
                            if added:
                                r0 = min(added)
                                ws.HPageBreaks.Add(ws.Range(f"A{r0}"))
                                shifted.append(f"+break@{r0}")
                REP["ghost_fix"].setdefault("shifts", []).append({name: shifted})
                act(f"GHOSTFIX {name}: {shifted}")
        # 最終ラウンドの再検査
        final_ghosts = {}
        for name in IMG_SHEETS:
            ws = wsmap[name]
            path = os.path.join(PAGES_DIR, f"{name}.pdf")
            bad = ghosts_of(ws, path, title_bottom(ws))
            if bad:
                final_ghosts[name] = bad
        REP["ghost_fix"]["final"] = final_ghosts
        assert not final_ghosts, f"ghosts remain: {final_ghosts}"

        wb.Save()
        act("SAVED (pass2: breaks)")
        counts, blanks = export_all()
        REP["counts"] = counts
        REP["blanks"] = blanks
        act(f"PAGES: {counts}")
        act(f"BLANKS: {blanks}")
        if counts != PREV_COUNTS:
            act(f"WARN counts changed: {PREV_COUNTS} -> {counts}")
        assert not blanks, f"blank pages: {blanks}"

        # 採番
        page = 1
        for name in ORDER:
            n = counts[name]
            if name != "表紙":
                wsmap[name].PageSetup.FirstPageNumber = page
                REP["numbering"][name] = page
            page += n
        wb.Save()
        act(f"SAVED (pass3: numbering) {REP['numbering']}")

        counts2, blanks2 = export_all()
        REP["counts_pass2"] = counts2
        assert counts2 == counts, f"pagination shifted: {counts2} vs {counts}"
        assert not blanks2, f"blank pages pass2: {blanks2}"
        act("PASS2 ok")

        # 冊PDF = シート単位PDFのpypdf結合(ブック一括出力の頁落ち回避·§8前例)
        writer = PdfWriter()
        for name in ORDER:
            for p in PdfReader(os.path.join(PAGES_DIR, f"{name}.pdf")).pages:
                writer.add_page(p)
        with open(VAULT_PDF, "wb") as f:
            writer.write(f)
        n = len(PdfReader(VAULT_PDF).pages)
        REP["book_pages"] = n
        assert n == sum(counts.values()), f"book {n} != sum {sum(counts.values())}"
        act(f"BOOK -> {VAULT_PDF} ({n}p)")

        wb.Close(SaveChanges=False)
        wb = None
    except Exception:
        if wb is not None:
            try:
                wb.Close(SaveChanges=False)
            except Exception:
                pass
        raise
    finally:
        app.Quit()

    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(REP, f, ensure_ascii=False, indent=1, default=str)
    print("DONE", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        try:
            REP["errors"].append(traceback.format_exc())
            with open(REPORT, "w", encoding="utf-8") as f:
                json.dump(REP, f, ensure_ascii=False, indent=1, default=str)
        except Exception:
            pass
        sys.exit(1)
