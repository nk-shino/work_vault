# -*- coding: utf-8 -*-
"""fix_breaks3.py — PDF実測(xref二重描画)で画像跨ぎを検出しアンカー行に改ページを追加。"""
import os, json, traceback, sys

WORK = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
XLSX = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\Pana-CIM管理手順書案_未承認.xlsx"
VAULT_PDF = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\Pana-CIM管理手順書案_未承認.pdf"
PAGES_DIR = os.path.join(WORK, "scripts", "tmp_pages5")
REPORT = os.path.join(WORK, "scripts", "fixbreaks3_report.json")
REP = {"rounds": [], "trailing_delete": {}, "blank_pages": {}, "counts": {}, "numbering": {}, "book_pages": None}

ORDER = ["表紙", "目次", "用語", "構成と管理情報", "相関図", "相関図_old", "管理体制",
         "月次再起動", "バックアップ", "復旧", "異常時の対応", "チェックシート(月次・異常時)",
         "会議課題一覧(一時)", "付録 引用元と確認範囲", "要確認事項一覧", "7-5仮_サービス起動停止"]
PIC_SHEETS = {"月次再起動": 93, "バックアップ": 189, "異常時の対応": 321, "7-5仮_サービス起動停止": 56}

def blankish(c):
    return c is None or str(c).strip().replace("\u3000", "") == ""

def main():
    os.makedirs(PAGES_DIR, exist_ok=True)
    import win32com.client as win32
    import pymupdf
    try:
        from pypdf import PdfReader, PdfWriter
    except Exception:
        from PyPDF2 import PdfReader, PdfWriter
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    try:
        wb = app.Workbooks.Open(XLSX, UpdateLinks=0, ReadOnly=False)
        try:
            wb.AutoSaveOn = False
        except Exception:
            pass
        wsmap = {sh.Name: sh for sh in wb.Worksheets}

        def value_rows(ws, last):
            s = set()
            ur = ws.UsedRange
            vv = ur.Value
            r0 = ur.Row
            if isinstance(vv, tuple):
                for i, row in enumerate(vv):
                    if isinstance(row, tuple) and any(not blankish(c) for c in row):
                        s.add(r0 + i)
            return {r for r in s if r <= last}

        def manual_rows(ws):
            out = set()
            for i in range(1, ws.HPageBreaks.Count + 1):
                pb = ws.HPageBreaks.Item(i)
                try:
                    if int(pb.Type) == -4135:
                        out.add(int(pb.Location.Row))
                except Exception:
                    out.add(int(pb.Location.Row))
            return out

        def export_sheet(ws, path):
            ws.ExportAsFixedFormat(0, path, 0, True, False)
            return pymupdf.open(path)

        # ---- 跨ぎ検出とアンカー改ページ(最大5ラウンド) ----
        for rnd in range(1, 6):
            round_log = {}
            changed = False
            for name, last in PIC_SHEETS.items():
                ws = wsmap[name]
                path = os.path.join(PAGES_DIR, f"{name}.pdf")
                doc = export_sheet(ws, path)
                # タイトル帯の下端(pt)
                ps = ws.PageSetup
                tb = float(ps.TopMargin)
                tr = str(ps.PrintTitleRows or "")
                if ":" in tr:
                    a = "".join(ch for ch in tr.split(":")[0] if ch.isdigit())
                    b = "".join(ch for ch in tr.split(":")[1].split(",")[0] if ch.isdigit())
                    if a and b:
                        tb += sum(float(ws.Rows[r].RowHeight) for r in range(int(a), int(b) + 1))
                shapes = []
                for sh in ws.Shapes:
                    try:
                        if int(sh.Type) in (13, 10) and int(sh.TopLeftCell.Row) <= last:
                            shapes.append({"tlr": int(sh.TopLeftCell.Row), "top": float(sh.Top),
                                           "w": float(sh.Width), "h": float(sh.Height)})
                    except Exception:
                        pass
                shapes.sort(key=lambda s: s["top"])
                # xrefごとに全矩形を集計
                all_rects = {}  # xref -> [(pageidx, rect)]
                for pi in range(doc.page_count):
                    pg = doc[pi]
                    for im in pg.get_images(full=True):
                        xref = im[0]
                        for rect in pg.get_image_rects(xref):
                            all_rects.setdefault(xref, []).append((pi, rect))
                straddlers = {}  # xref -> pageidx(最初の侵入頁)
                for xref, lst in all_rects.items():
                    for pi, rect in lst:
                        if rect.y0 < tb - 2.0 or rect.y1 > 780.0:
                            straddlers[xref] = pi
                            break
                claimed = set()
                added = []
                for xref, pi in sorted(straddlers.items(), key=lambda kv: kv[1]):
                    rects = [r for _, r in all_rects[xref]]
                    W = max(r.width for r in rects)
                    H = max(r.y1 for r in rects) - min(r.y0 for r in rects)
                    # 幅·高さの一致で候補図を特定(処理順は頁順·未割当てを優先)
                    cands = [s for s in shapes if abs(s["w"] - W) < 10.0 and abs(s["h"] - H) < 12.0]
                    if not cands:
                        cands = [s for s in shapes if abs(s["w"] - W) < 10.0]
                    cands = [s for s in cands if id(s) not in claimed] or cands
                    if not cands:
                        round_log[f"{name}:xref{xref}"] = f"UNMATCHED(w{W:.0f}xh{H:.0f})"
                        continue
                    tgt = cands[0]
                    claimed.add(id(tgt))
                    R = tgt["tlr"]
                    if R not in manual_rows(ws) and R > 1:
                        ws.HPageBreaks.Add(ws.Range(f"A{R}"))
                        added.append(f"p{pi+1}:break@{R}(w{W:.0f}xh{H:.0f})")
                        changed = True
                    else:
                        added.append(f"p{pi+1}:already@{R}(w{W:.0f}xh{H:.0f})")
                if added:
                    round_log[name] = added
                doc.close()
            REP["rounds"].append(round_log)
            print(f"ROUND {rnd}: {round_log}", flush=True)
            if not changed:
                break
        if not REP["rounds"] or REP["rounds"][-1]:
            raise SystemExit("straddles remain after 5 rounds")

        # ---- 末尾空行の削除 ----
        for name, last in PIC_SHEETS.items():
            ws = wsmap[name]
            vrows = value_rows(ws, last)
            V = max(vrows) if vrows else last
            if V + 1 < last:
                r1, r2 = V + 1, last
                rng = ws.Range(f"A{r1}:AZ{r2}")
                v = rng.Value
                empty = True
                if isinstance(v, tuple):
                    for row in v:
                        if isinstance(row, tuple):
                            if any(not blankish(c) for c in row):
                                empty = False
                                break
                        elif not blankish(v):
                            empty = False
                            break
                elif not blankish(v):
                    empty = False
                bordered = any(rng.Borders(k).LineStyle != -4142 for k in (7, 8, 9, 10, 11, 12))
                shok = not any(int(s.BottomRightCell.Row) >= r1 for s in ws.Shapes)
                if empty and not bordered and shok:
                    ws.Rows[f"{r1}:{r2}"].Delete()
                    REP["trailing_delete"][name] = [r1, r2]
                    print(f"TRAILING DELETE {name} {r1}-{r2}", flush=True)

        # ---- 出力·空白頁チェック·頁番号·結合 ----
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

        wb.Save()
        print("SAVED pass1", flush=True)
        counts, blanks = export_all()
        REP["blank_pages"] = blanks
        REP["counts"] = counts
        print("PAGES:", counts, "BLANKS:", blanks, flush=True)
        if blanks:
            wb.Close(SaveChanges=False)
            raise SystemExit(f"blank pages remain: {blanks}")
        page = 1
        for name in ORDER:
            n = counts[name]
            if name != "表紙":
                wsmap[name].PageSetup.FirstPageNumber = page
                REP["numbering"][name] = page
            page += n
        wb.Save()
        print("SAVED pass2", flush=True)
        counts2, blanks2 = export_all()
        assert not blanks2 and counts2 == counts, f"pagination shifted: {counts2} / {blanks2}"
        wb.Close(SaveChanges=False)
    finally:
        app.Quit()

    writer = PdfWriter()
    for name in ORDER:
        rd = PdfReader(os.path.join(PAGES_DIR, f"{name}.pdf"))
        for p in rd.pages:
            writer.add_page(p)
    with open(VAULT_PDF, "wb") as f:
        writer.write(f)
    n = len(PdfReader(VAULT_PDF).pages)
    REP["book_pages"] = n
    assert n == sum(counts.values())
    print(f"BOOK {VAULT_PDF}: {n}p", flush=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(REP, f, ensure_ascii=False, indent=1, default=str)
    print("DONE", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        with open(REPORT, "w", encoding="utf-8") as f:
            json.dump(REP, f, ensure_ascii=False, indent=1, default=str)
        sys.exit(1)
