# -*- coding: utf-8 -*-
"""fix_breaks4.py — 図のセル範囲(BRR)とキャプション行の直後に改ページを再構築し幽霊描画を解消。"""
import os, json, traceback, sys

WORK = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
XLSX = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\Pana-CIM管理手順書案_未承認.xlsx"
VAULT_PDF = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\Pana-CIM管理手順書案_未承認.pdf"
PAGES_DIR = os.path.join(WORK, "scripts", "tmp_pages6")
REPORT = os.path.join(WORK, "scripts", "fixbreaks4_report.json")
REP = {"setup": {}, "rounds": [], "trailing_delete": {}, "blank_pages": {}, "counts": {}, "numbering": {}, "book_pages": None}

ORDER = ["表紙", "目次", "用語", "構成と管理情報", "相関図", "相関図_old", "管理体制",
         "月次再起動", "バックアップ", "復旧", "異常時の対応", "チェックシート(月次・異常時)",
         "会議課題一覧(一時)", "付録 引用元と確認範囲", "要確認事項一覧", "7-5仮_サービス起動停止"]
# name -> (last, keep_breaks(領域開始), 画像領域の先頭行)
SHEETS = {"バックアップ": (189, [15], 16), "異常時の対応": (321, [71, 116], 117)}

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
            out = []
            for i in range(1, ws.HPageBreaks.Count + 1):
                pb = ws.HPageBreaks.Item(i)
                try:
                    if int(pb.Type) == -4135:
                        out.append(int(pb.Location.Row))
                except Exception:
                    out.append(int(pb.Location.Row))
            return out

        def title_bottom(ws, last):
            ps = ws.PageSetup
            tb = float(ps.TopMargin)
            tr = str(ps.PrintTitleRows or "")
            if ":" in tr:
                a = "".join(ch for ch in tr.split(":")[0] if ch.isdigit())
                b = "".join(ch for ch in tr.split(":")[1].split(",")[0] if ch.isdigit())
                if a and b:
                    tb += sum(float(ws.Rows[r].RowHeight) for r in range(int(a), int(b) + 1))
            return tb, str(ps.PrintTitleRows), round(float(ps.TopMargin), 1)

        def pics_of(ws, last):
            pics = []
            for sh in ws.Shapes:
                try:
                    if int(sh.Type) in (13, 10) and int(sh.TopLeftCell.Row) <= last:
                        pics.append({"tlr": int(sh.TopLeftCell.Row), "brr": int(sh.BottomRightCell.Row),
                                     "top": float(sh.Top), "bot": float(sh.Top) + float(sh.Height)})
                except Exception:
                    pass
            pics.sort(key=lambda p: p["top"])
            return pics

        # ---- 改ページ再構築 ----
        for name, (last, keeps, zone_from) in SHEETS.items():
            ws = wsmap[name]
            hs = {r: float(ws.Rows[r].RowHeight) for r in range(1, last + 1)}
            vrows = value_rows(ws, last)
            pics = pics_of(ws, last)
            tb, tr_str, tm = title_bottom(ws, last)
            REP["setup"][name] = {"titleRows": tr_str, "topMargin": tm, "titleBottom": round(tb, 1), "pics": len(pics)}
            # 領域内の旧手動改ページを削除
            for r in manual_rows(ws):
                if r >= zone_from:
                    idx = manual_rows(ws).index(r) + 1
                    ws.HPageBreaks.Item(idx).Delete()
            # 再構築: 各図の max(BRR, キャプション行)+1
            news = []
            cur = zone_from - 1
            for p in pics:
                cap = min((v for v in vrows if v > p["brr"] and v <= p["brr"] + 4), default=p["brr"])
                b = max(p["brr"], cap) + 1
                if b <= cur:
                    b = cur + 1
                news.append(b)
                cur = b
            for b in news:
                ws.HPageBreaks.Add(ws.Range(f"A{b}"))
            REP["rounds"].append({"build": dict(zip([p["tlr"] for p in pics], news))})
            print(f"BUILD {name}: {list(zip([p['tlr'] for p in pics], news))}", flush=True)

        # ---- 出力→幽霊検証(最大3ラウンド) ----
        def ghost_check(ws, path):
            doc = pymupdf.open(path)
            tb, _, _ = title_bottom(ws, 1)
            bad = []
            for pi in range(doc.page_count):
                for inf in doc[pi].get_image_info():
                    b = inf["bbox"]
                    if b[1] < tb - 2.0 or b[3] > 780.0:
                        bad.append((pi + 1, round(b[0], 0), round(b[1], 0), round(b[3], 0)))
            doc.close()
            return bad

        for rnd in range(3):
            allbad = {}
            for name in SHEETS:
                ws = wsmap[name]
                path = os.path.join(PAGES_DIR, f"{name}.pdf")
                ws.ExportAsFixedFormat(0, path, 0, True, False)
                bad = ghost_check(ws, path)
                if bad:
                    allbad[name] = bad
            REP["rounds"].append({k: v for k, v in allbad.items()})
            print(f"GHOSTCHECK round{rnd+1}: {allbad}", flush=True)
            if not allbad:
                break
            # 幽霊のある頁の直前の改ページを1行後ろへ
            for name, bad in allbad.items():
                ws = wsmap[name]
                for (pgn, x0, y0, y1) in bad:
                    mrows = sorted(manual_rows(ws))
                    cand = [r for r in mrows if r <= sum([]) or True]
                    # 頁pgnの開始改ページ = mrows[pgn-1](表紙分オフセットなし·シート単独PDF)
                    if pgn - 1 < len(mrows):
                        old = mrows[pgn - 1]
                        idx = mrows.index(old) + 1
                        ws.HPageBreaks.Item(idx).Delete()
                        ws.HPageBreaks.Add(ws.Range(f"A{old + 1}"))
                        print(f"SHIFT {name} break {old}->{old+1}", flush=True)
        else:
            pass
        if any(r for r in REP["rounds"][1:] if isinstance(r, dict) and any(isinstance(v, list) and v for v in r.values() if isinstance(v, list))):
            raise SystemExit("ghosts remain")

        # ---- 末尾空行の削除 ----
        for name, (last, keeps, zone_from) in SHEETS.items():
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
