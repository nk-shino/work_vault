# -*- coding: utf-8 -*-
"""fix_breaks.py — 旧手動改ページの全削除·UsedRange縮退·改ページ再計算·頁番号·冊PDF再生成。"""
import os, json, math, traceback, sys

WORK = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
XLSX = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\Pana-CIM管理手順書案_未承認.xlsx"
VAULT_PDF_DIR = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
PAGES_DIR = os.path.join(WORK, "scripts", "tmp_pages2")
REPORT = os.path.join(WORK, "scripts", "fixbreaks_report.json")

PAGE_H = 841.9 - 42.52 - 56.69  # 742.69
REP = {"deletes": {}, "breaks": {}, "blank": {}, "pages": {}, "numbering": {}, "postcheck": {}, "fc": {}}

COLS = [chr(65 + i) for i in range(26)] + [f"A{chr(65+i)}" for i in range(26)] + [f"B{chr(65+i)}" for i in range(26)]

def col_px(w):
    return int(((256.0 * w + 18.0) / 256.0) * 7) + 5

def main():
    os.makedirs(PAGES_DIR, exist_ok=True)
    import win32com.client as win32
    try:
        from pypdf import PdfReader
    except Exception:
        from PyPDF2 import PdfReader
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

        STYLED = ["目次", "用語", "構成と管理情報", "管理体制", "月次再起動", "バックアップ",
                  "復旧", "異常時の対応", "チェックシート(月次・異常時)", "会議課題一覧(一時)",
                  "付録 引用元と確認範囲", "要確認事項一覧", "7-5仮_サービス起動停止"]
        LAST = {"目次": 20, "用語": 32, "構成と管理情報": 21, "管理体制": 20,
                "月次再起動": 93, "バックアップ": 190, "復旧": 14, "異常時の対応": 321,
                "チェックシート(月次・異常時)": 45, "会議課題一覧(一時)": 42,
                "付録 引用元と確認範囲": 28, "要確認事項一覧": 36, "7-5仮_サービス起動停止": 56}
        DELETES = [("目次", 21, 60, "AZ"), ("月次再起動", 94, 179, "AZ"),
                   ("バックアップ", 190, 222, "AZ"), ("復旧", 15, 335, "BP"),
                   ("チェックシート(月次・異常時)", 46, 78, "AZ"), ("会議課題一覧(一時)", 43, 528, "BR"),
                   ("付録 引用元と確認範囲", 29, 204, "AZ"), ("要確認事項一覧", 37, 142, "AZ")]

        # ---- 1. 旧手動改ページ全削除 ----
        for name in STYLED:
            ws = wsmap[name]
            n = ws.HPageBreaks.Count
            for i in range(n, 0, -1):
                ws.HPageBreaks.Item(i).Delete()
            REP["breaks"][name + ":removed"] = n
        print("old breaks removed", flush=True)

        # ---- 2. UsedRange 縮退(修正アサーション) ----
        def range_empty(ws, r1, r2, maxcol):
            rng = ws.Range(f"A{r1}:{maxcol}{r2}")
            v = rng.Value
            if v is None:
                pass
            elif isinstance(v, tuple):
                for row in v:
                    if not isinstance(row, tuple):
                        if v is not None and str(v) != "":
                            return False, "value"
                        continue
                    for c in row:
                        if c is not None and str(c) != "":
                            return False, "value"
            else:
                if str(v) != "":
                    return False, "value"
            if rng.MergeCells:
                return False, "merge"
            for k in (7, 8, 9, 10, 11, 12):
                if rng.Borders(k).LineStyle != -4142:
                    return False, f"border{k}"
            return True, ""

        for name, r1, r2, maxcol in DELETES:
            ws = wsmap[name]
            ok, why = range_empty(ws, r1, r2, maxcol)
            if not ok:
                REP["deletes"][name] = {"ok": False, "why": why}
                print(f"DELETE SKIP {name}: {why}", flush=True)
                continue
            shok = True
            for sh in ws.Shapes:
                try:
                    if int(sh.BottomRightCell.Row) >= r1:
                        shok = False
                        break
                except Exception:
                    pass
            if not shok:
                REP["deletes"][name] = {"ok": False, "why": "shape"}
                print(f"DELETE SKIP {name}: shape", flush=True)
                continue
            ws.Rows[f"{r1}:{r2}"].Delete()
            REP["deletes"][name] = {"ok": True}
            print(f"DELETE {name} {r1}-{r2}", flush=True)

        # ---- 3. 改ページ再計算 ----
        def value_rows(ws, last):
            s = set()
            ur = ws.UsedRange
            vv = ur.Value
            r0 = ur.Row
            if isinstance(vv, tuple):
                for i, row in enumerate(vv):
                    if not isinstance(row, tuple):
                        continue
                    if any(c is not None and str(c) != "" for c in row):
                        s.add(r0 + i)
            return {r for r in s if r <= last}

        def shapes_abs(ws):
            out = []
            for sh in ws.Shapes:
                try:
                    out.append({"type": int(sh.Type), "tlr": int(sh.TopLeftCell.Row),
                                "top": float(sh.Top), "h": float(sh.Height),
                                "brr": int(sh.BottomRightCell.Row)})
                except Exception:
                    pass
            return out

        def titles_cap(ws, heights):
            try:
                t = ws.PageSetup.PrintTitleRows or ""
            except Exception:
                t = ""
            if "1" in t and "3" in t:
                return heights.get(1, 12.8) + heights.get(2, 12.8) + heights.get(3, 12.8)
            return 0.0

        def walk(heights, last, breaks, caps):
            pages = []
            y = 0.0
            page_top = 0.0
            start = 1
            for r in range(1, last + 1):
                h = heights.get(r, 12.8)
                if r in breaks and r != 1:
                    pages.append((start, page_top))
                    page_top = y
                    start = r
                elif y + h > page_top + caps and y > page_top:
                    pages.append((start, page_top))
                    page_top = y
                    start = r
                y += h
            pages.append((start, page_top))
            return pages

        for name in STYLED:
            ws = wsmap[name]
            last = LAST[name]
            hs = {r: float(ws.Rows[r].RowHeight) for r in range(1, last + 1)}
            caps = PAGE_H - titles_cap(ws, hs)
            tops = {1: 0.0}
            for r in range(1, last + 1):
                tops[r + 1] = tops[r] + hs.get(r, 12.8)
            vrows = value_rows(ws, last)
            shp = shapes_abs(ws)
            pics = [s for s in shp if s["type"] in (13, 10) and s["tlr"] <= last]
            units = []
            for p in pics:
                units.append({"top": p["top"], "bot": p["top"] + p["h"], "brk_row": None})
            # 異常時フローチャートを仮ユニットに追加
            if name == "異常時の対応":
                fc = [s for s in shp if s["type"] not in (13, 10) and 72 <= s["tlr"] and s["brr"] <= 321]
                if fc:
                    t = min(s["top"] for s in fc)
                    b = max(s["top"] + s["h"] for s in fc)
                    units.append({"top": t, "bot": b, "brk_row": 71})
                    REP["fc"] = {"top": round(t, 1), "bot": round(b, 1), "h": round(b - t, 1)}
            def row_of_y(yv):
                r = 1
                while r <= last and tops[r + 1] <= yv:
                    r += 1
                return min(r, last)
            breaks = set()
            for _ in range(10):
                pages = walk(hs, last, breaks, caps)
                need = set()
                for u in units:
                    sy = max((py for sr, py in pages if sr <= row_of_y(u["top"])), default=0.0)
                    end = sy + caps
                    if u["bot"] > end - 1.0:
                        need.add(u["brk_row"] or row_of_y(u["top"]))
                        continue
                    nxt = min((v for v in vrows if tops[v] >= u["bot"] - 2.0), default=None)
                    if nxt is not None and tops[nxt] + hs.get(nxt, 12.8) > end - 1.0:
                        need.add(u["brk_row"] or row_of_y(u["top"]))
                if not need:
                    break
                breaks |= need
            # 空白頁の解消(手動改ページ起因のみ)
            for _ in range(6):
                pages = walk(hs, last, breaks, caps)
                blank = None
                for i, (s, sy) in enumerate(pages):
                    e = (pages[i + 1][0] - 1) if i + 1 < len(pages) else last
                    ey = sy + caps
                    if any(s <= v <= e for v in vrows):
                        continue
                    hit = any(u["top"] < ey - 1 and u["bot"] > sy + 1 for u in units)
                    if hit:
                        continue
                    if s in breaks:
                        blank = s
                        break
                if blank is None:
                    break
                breaks.discard(blank)
            for r in sorted(breaks):
                ws.HPageBreaks.Add(ws.Range(f"A{r}"))
            REP["breaks"][name] = sorted(breaks)
            print(f"BREAKS {name}: {sorted(breaks)} (caps={caps:.1f})", flush=True)

        wb.Save()
        print("SAVED pass1", flush=True)

        # ---- 4. 頁数·頁番号·冊PDF ----
        sheets = list(wb.Worksheets)
        counts = {}
        for sh in sheets:
            p = os.path.join(PAGES_DIR, f"{sh.Name}.pdf")
            sh.ExportAsFixedFormat(0, p, 0, True, False)
            counts[sh.Name] = len(PdfReader(p).pages)
        REP["pages"] = counts
        print("PAGES:", counts, flush=True)
        page = 1
        for sh in sheets:
            n = counts[sh.Name]
            if sh.Name != "表紙":
                sh.PageSetup.FirstPageNumber = page
                REP["numbering"][sh.Name] = page
            page += n
        wb.Save()
        print("SAVED pass2", flush=True)

        cands = [f for f in os.listdir(VAULT_PDF_DIR)
                 if f.lower().endswith(".pdf") and "Pana-CIM管理手順書案" in f]
        cands.sort(key=lambda f: os.path.getmtime(os.path.join(VAULT_PDF_DIR, f)), reverse=True)
        book = os.path.join(VAULT_PDF_DIR, cands[0]) if cands else os.path.join(VAULT_PDF_DIR, "Pana-CIM管理手順書案_未承認.pdf")
        wb.ExportAsFixedFormat(0, book, 0, True, False)
        REP["book"] = book
        REP["book_pages"] = len(PdfReader(book).pages)
        print(f"BOOK {book}: {REP['book_pages']}p", flush=True)

        # ---- 5. 事後検証: 画像跨ぎ·空白頁(実改ページベース) ----
        for name in STYLED:
            ws = wsmap[name]
            last = LAST[name]
            hs = {r: float(ws.Rows[r].RowHeight) for r in range(1, last + 1)}
            caps = PAGE_H - titles_cap(ws, hs)
            tops = {1: 0.0}
            for r in range(1, last + 1):
                tops[r + 1] = tops[r] + hs.get(r, 12.8)
            real = sorted({int(ws.HPageBreaks.Item(i).Location.Row) for i in range(1, ws.HPageBreaks.Count + 1)})
            pages = walk(hs, last, set(real), caps)
            vrows = value_rows(ws, last)
            shp = shapes_abs(ws)
            issues = []
            for p in [s for s in shp if s["type"] in (13, 10)]:
                sy = max((py for sr, py in pages if tops[sr] <= p["top"] + 0.5), default=0.0)
                if p["top"] + p["h"] > sy + caps - 0.5:
                    issues.append(f"pic-straddle tlr={p['tlr']}")
            for i, (s, sy) in enumerate(pages):
                e = (pages[i + 1][0] - 1) if i + 1 < len(pages) else last
                ey = sy + caps
                if any(s <= v <= e for v in vrows):
                    continue
                if any(u["top"] < ey - 1 and u["top"] + u["h"] > sy + 1 for u in shp):
                    continue
                issues.append(f"blank-page rows {s}-{e}")
            REP["postcheck"][name] = {"real_breaks": real, "issues": issues}
            if issues:
                print(f"POSTCHECK {name}: {issues}", flush=True)
        wb.Close(SaveChanges=False)
    finally:
        app.Quit()
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(REP, f, ensure_ascii=False, indent=1)
    print("DONE", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        with open(REPORT, "w", encoding="utf-8") as f:
            json.dump(REP, f, ensure_ascii=False, indent=1)
        sys.exit(1)
