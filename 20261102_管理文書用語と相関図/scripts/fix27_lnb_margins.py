# -*- coding: utf-8 -*-
"""fix27_lnb_margins.py — LNB冊 [F1] 余白の計画値への再設定 + 改ページ·採番·冊PDFの再構築。

- 対象15シートの余白を Application.InchesToPoints で再設定する
  (L0.87/R0.51/T0.59/B0.79/H0.59/F0.39 in = 62.64/36.72/42.48/56.88/42.48/28.08 pt)。
  相関図(0.394統一)·相関図_old·申し送り(認証情報)は不触。
- 保存→17シート個別出力→頁数·幽霊·空頁検定→FirstPageNumber 再設定→冊出力で
  申し送り頁数を実測→引用→引用採番→冊PDF再構築(個別17シート+認証情報頁スポット)。
- 申し送り(認証情報)シートの内容は参照しない(冊PDFへの出力は現行どおり)。
"""
import os, sys, json, math, traceback

WORK = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
XLSX = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\LNB管理手順書案_未承認.xlsx"
VAULT_PDF_DIR = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
PAGES_DIR = os.path.join(WORK, "scripts", "tmp_pages_lnb2")
REPORT = os.path.join(WORK, "scripts", "fix27_lnb_margins_report.json")

ORDER17 = ["表紙", "目次", "用語", "構成と管理情報", "相関図", "相関図_old", "管理体制",
           "日次点検", "定期管理", "バックアップ", "復旧", "異常時の対応",
           "チェックシート(日次)", "チェックシート(月次・異常時)", "会議課題一覧(一時)",
           "要確認事項一覧", "引用と部品照合"]
TARGET15 = [n for n in ORDER17 if n not in ("相関図", "相関図_old")]
PREV_COUNTS = {"表紙": 1, "目次": 1, "用語": 2, "構成と管理情報": 4, "相関図": 1, "相関図_old": 1,
               "管理体制": 1, "日次点検": 1, "定期管理": 1, "バックアップ": 4, "復旧": 1,
               "異常時の対応": 1, "チェックシート(日次)": 1, "チェックシート(月次・異常時)": 1,
               "会議課題一覧(一時)": 2, "要確認事項一覧": 2, "引用と部品照合": 1}
# 計画値(インチ) — InchesToPoints で設定する
MARGINS_IN = {"Left": 0.87, "Right": 0.51, "Top": 0.59, "Bottom": 0.79, "Header": 0.59, "Footer": 0.39}

REP = {"actions": [], "margins": {}, "counts": {}, "counts_pass2": {}, "blanks": {},
       "ghosts": {}, "numbering": {}, "cred_pages": None, "book_pages": None, "errors": []}

def act(msg):
    REP["actions"].append(msg)
    print("[act]", msg, flush=True)

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
    wb = None
    try:
        wb = app.Workbooks.Open(XLSX, UpdateLinks=0, ReadOnly=False)
        try:
            wb.AutoSaveOn = False
        except Exception:
            pass
        wsmap = {sh.Name: sh for sh in wb.Worksheets}
        assert len(wsmap) == 18, f"sheet count {len(wsmap)}"

        # ---------- 1. 余白の再設定(InchesToPoints) ----------
        for name in TARGET15:
            ps = wsmap[name].PageSetup
            before = {k: round(float(getattr(ps, k + "Margin")), 2) for k in MARGINS_IN}
            ps.LeftMargin = app.InchesToPoints(MARGINS_IN["Left"])
            ps.RightMargin = app.InchesToPoints(MARGINS_IN["Right"])
            ps.TopMargin = app.InchesToPoints(MARGINS_IN["Top"])
            ps.BottomMargin = app.InchesToPoints(MARGINS_IN["Bottom"])
            ps.HeaderMargin = app.InchesToPoints(MARGINS_IN["Header"])
            ps.FooterMargin = app.InchesToPoints(MARGINS_IN["Footer"])
            after = {k: round(float(getattr(ps, k + "Margin")), 2) for k in MARGINS_IN}
            REP["margins"][name] = {"before_pt": before, "after_pt": after,
                                    "after_in": {k: round(v / 72.0, 4) for k, v in after.items()}}
            act(f"MARGIN {name}: {before} -> {after}")
        # 相関図·相関図_old·申し送り は不触(実測のみ記録)
        for name in ("相関図", "相関図_old"):
            ps = wsmap[name].PageSetup
            REP["margins"][name] = {"untouched": True,
                                    "pt": {k: round(float(getattr(ps, k + "Margin")), 2) for k in MARGINS_IN}}
        wb.Save()
        act("SAVED (margins)")

        # ---------- 2. 出力→検定 ----------
        def export_all():
            counts, blanks = {}, {}
            for name in ORDER17:
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

        def ghosts_all():
            bad = {}
            for name in ORDER17:
                doc = pymupdf.open(os.path.join(PAGES_DIR, f"{name}.pdf"))
                bb = []
                for pi in range(doc.page_count):
                    for inf in doc[pi].get_image_info():
                        b = inf["bbox"]
                        if b[3] > 786.0 or b[1] < 40.0:
                            bb.append({"page": pi + 1, "y0": round(b[1], 1), "y1": round(b[3], 1)})
                doc.close()
                if bb:
                    bad[name] = bb
            return bad

        counts, blanks = export_all()
        REP["counts"] = counts
        REP["blanks"] = blanks
        act(f"PAGES: {counts}")
        act(f"BLANKS: {blanks}")
        assert not blanks, f"blank pages: {blanks}"
        if counts != PREV_COUNTS:
            act(f"WARN counts changed from impl_lnb: {PREV_COUNTS} -> {counts}")
        ghosts = ghosts_all()
        REP["ghosts"] = ghosts
        act(f"GHOSTS: {ghosts}")
        assert not ghosts, f"ghost images: {ghosts}"

        # ---------- 3. 採番 ----------
        page = 1
        for name in ORDER17[:16]:
            n = counts[name]
            if name != "表紙":
                wsmap[name].PageSetup.FirstPageNumber = page
                REP["numbering"][name] = page
            page += n
        wb.Save()
        act("SAVED (pass2: numbering 2-16)")

        # ---------- 4. 冊出力で申し送り頁数を実測 ----------
        vault_pdf = os.path.join(VAULT_PDF_DIR, "LNB管理手順書案_未承認.pdf")
        REP["pdf"] = vault_pdf
        wb.ExportAsFixedFormat(0, vault_pdf, 0, True, False)
        book_pages = len(PdfReader(vault_pdf).pages)
        cred_pages = book_pages - sum(counts.values())
        REP["book_pages"] = book_pages
        REP["cred_pages"] = cred_pages
        act(f"BOOK {vault_pdf}: {book_pages}p cred={cred_pages}p")
        assert cred_pages >= 1, f"cred_pages={cred_pages}"

        # ---------- 5. 引用の頁番号 ----------
        wsmap["引用と部品照合"].PageSetup.FirstPageNumber = page + cred_pages
        REP["numbering"]["引用と部品照合"] = page + cred_pages
        wb.Save()
        act(f"SAVED (pass3: 引用 FirstPageNumber={page + cred_pages})")

        # ---------- 6. 最終出力·検査 ----------
        counts2, blanks2 = export_all()
        REP["counts_pass2"] = counts2
        assert counts2 == counts, f"pagination shifted: {counts2} vs {counts}"
        assert not blanks2, f"blank pages: {blanks2}"
        ghosts2 = ghosts_all()
        assert not ghosts2, f"ghost images pass2: {ghosts2}"
        act("PASS2 ok (counts stable, ghosts 0)")

        # ---------- 7. 冊PDF再構築(個別17シート+認証情報頁スポット) ----------
        with open(vault_pdf, "rb") as f:
            book_bytes = f.read()
        bookrd = PdfReader(__import__("io").BytesIO(book_bytes))
        assert len(bookrd.pages) == book_pages
        offset = sum(counts[n] for n in ORDER17[:16])
        writer = PdfWriter()
        for name in ORDER17[:16]:
            for p in PdfReader(os.path.join(PAGES_DIR, f"{name}.pdf")).pages:
                writer.add_page(p)
        for i in range(offset, offset + cred_pages):
            writer.add_page(bookrd.pages[i])
        for p in PdfReader(os.path.join(PAGES_DIR, "引用と部品照合.pdf")).pages:
            writer.add_page(p)
        with open(vault_pdf, "wb") as f:
            writer.write(f)
        final_pages = len(PdfReader(vault_pdf).pages)
        assert final_pages == book_pages, f"merged {final_pages} != book {book_pages}"
        act(f"MERGED -> {vault_pdf} ({final_pages}p)")

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
        json.dump(REP, f, ensure_ascii=False, indent=1)
    print("DONE", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        try:
            with open(REPORT, "w", encoding="utf-8") as f:
                json.dump(REP, f, ensure_ascii=False, indent=1)
        except Exception:
            pass
        sys.exit(1)
