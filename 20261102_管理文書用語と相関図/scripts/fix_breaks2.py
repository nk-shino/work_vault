# -*- coding: utf-8 -*-
"""fix_breaks2.py — 実改ページ境界基準で画像跨ぎを解消し、空白頁の末尾空行を削除、冊PDF再生成。"""
import os, json, traceback, sys

WORK = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
XLSX = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\Pana-CIM管理手順書案_未承認.xlsx"
VAULT_PDF = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\Pana-CIM管理手順書案_未承認.pdf"
PAGES_DIR = os.path.join(WORK, "scripts", "tmp_pages4")
REPORT = os.path.join(WORK, "scripts", "fixbreaks2_report.json")
REP = {"units_fixed": {}, "trailing_delete": {}, "blank_pages": {}, "counts": {}, "numbering": {}, "book_pages": None}

ORDER = ["表紙", "目次", "用語", "構成と管理情報", "相関図", "相関図_old", "管理体制",
         "月次再起動", "バックアップ", "復旧", "異常時の対応", "チェックシート(月次・異常時)",
         "会議課題一覧(一時)", "付録 引用元と確認範囲", "要確認事項一覧", "7-5仮_サービス起動停止"]
LAST = {"月次再起動": 93, "バックアップ": 189, "異常時の対応": 321, "7-5仮_サービス起動停止": 56}

def main():
    os.makedirs(PAGES_DIR, exist_ok=True)
    import win32com.client as win32
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
                    if isinstance(row, tuple) and any(c is not None and str(c) != "" for c in row):
                        s.add(r0 + i)
            return {r for r in s if r <= last}

        def real_breaks(ws):
            out = []
            n = ws.HPageBreaks.Count
            for i in range(1, n + 1):
                pb = ws.HPageBreaks.Item(i)
                r = int(pb.Location.Row)
                try:
                    t = int(pb.Type)
                except Exception:
                    t = -4135
                out.append((r, t))
            return out

        for name, last in LAST.items():
            ws = wsmap[name]
            hs = {r: float(ws.Rows[r].RowHeight) for r in range(1, last + 1)}
            tops = {1: 0.0}
            for r in range(1, last + 1):
                tops[r + 1] = tops[r] + hs.get(r, 12.8)

            def row_of_y(yv):
                r = 1
                while r <= last and tops[r + 1] <= yv:
                    r += 1
                return min(r, last)

            vrows = value_rows(ws, last)
            units = []
            for sh in ws.Shapes:
                try:
                    t = int(sh.Type)
                    tlr = int(sh.TopLeftCell.Row)
                    if t in (13, 10) and tlr <= last:
                        units.append({"top": float(sh.Top), "bot": float(sh.Top) + float(sh.Height)})
                except Exception:
                    pass
            if name == "異常時の対応":
                fc = [s for s in ws.Shapes
                      if int(s.Type) not in (13, 10) and 72 <= int(s.TopLeftCell.Row) and int(s.BottomRightCell.Row) <= 321]
                if fc:
                    t = min(float(s.Top) for s in fc)
                    b = max(float(s.Top) + float(s.Height) for s in fc)
                    units.append({"top": t, "bot": b})
            fixed = []
            for _ in range(15):
                rb = real_breaks(ws)
                rows = [r for r, t in rb]
                man = {r: (t == -4135) for r, t in rb}
                bounds = [0.0] + [tops[r] for r in rows] + [1e9]
                changed = False
                for u in units:
                    i = max(idx for idx, b in enumerate(bounds) if b <= u["top"] + 0.5)
                    next_b = bounds[i + 1]
                    need_until = u["bot"]
                    cap = min((v for v in vrows if tops[v] >= u["bot"] - 2.0), default=None)
                    if cap is not None and 0 < tops[cap] - u["bot"] < 40.0:
                        need_until = max(need_until, tops[cap] + hs.get(cap, 12.8))
                    if need_until <= next_b - 2.0:
                        continue
                    r_b = rows[i] if i < len(rows) else None
                    if r_b is None or not man.get(r_b, False):
                        tgt = row_of_y(u["top"] + 0.5)
                        if tgt not in rows:
                            ws.HPageBreaks.Add(ws.Range(f"A{tgt}"))
                            fixed.append(f"auto→manual@{tgt}")
                            changed = True
                    else:
                        tgt = row_of_y(need_until + 2.0)
                        if tgt != r_b and tgt <= last:
                            idx = rows.index(r_b) + 1
                            ws.HPageBreaks.Item(idx).Delete()
                            if tgt not in rows:
                                ws.HPageBreaks.Add(ws.Range(f"A{tgt}"))
                            fixed.append(f"{r_b}→{tgt}")
                            changed = True
                    break  # 1パス1変更(境界を再読み込みして再評価)
                if not changed:
                    break
            REP["units_fixed"][name] = fixed
            if fixed:
                print(f"FIX {name}: {fixed}", flush=True)

            # 末尾空行の削除(空白頁の解消)
            V = max(vrows) if vrows else last
            if V + 1 < last:
                r1, r2 = V + 1, last
                rng = ws.Range(f"A{r1}:AZ{r2}")
                v = rng.Value
                empty = True
                if isinstance(v, tuple):
                    for row in v:
                        if isinstance(row, tuple):
                            if any(c is not None and str(c) != "" for c in row):
                                empty = False
                                break
                        elif v is not None and str(v) != "":
                            empty = False
                            break
                elif v is not None and str(v) != "":
                    empty = False
                bordered = any(rng.Borders(k).LineStyle != -4142 for k in (7, 8, 9, 10, 11, 12))
                shok = not any(int(s.BottomRightCell.Row) >= r1 for s in ws.Shapes)
                if empty and not bordered and shok:
                    ws.Rows[f"{r1}:{r2}"].Delete()
                    REP["trailing_delete"][name] = [r1, r2]
                    print(f"TRAILING DELETE {name} {r1}-{r2}", flush=True)

        wb.Save()
        print("SAVED pass1", flush=True)

        # 頁単位出力→空白頁検出
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

        counts, blanks = export_all()
        REP["blank_pages"] = blanks
        REP["counts"] = counts
        print("PAGES:", counts, "BLANKS:", blanks, flush=True)
        if blanks:
            wb.Close(SaveChanges=False)
            raise SystemExit(f"blank pages remain: {blanks}")

        # 頁番号設定→再出力
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
        assert not blanks2 and counts2 == counts, f"pagination shifted: {counts2} / blanks {blanks2}"
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
