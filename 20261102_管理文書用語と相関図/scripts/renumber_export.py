# -*- coding: utf-8 -*-
"""renumber_export.py — 頁単位PDF再出力·頁番号再設定·pypdf結合で冊PDFを確定させる。"""
import os, json, traceback, sys

WORK = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
XLSX = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\Pana-CIM管理手順書案_未承認.xlsx"
VAULT_PDF = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\Pana-CIM管理手順書案_未承認.pdf"
PAGES_DIR = os.path.join(WORK, "scripts", "tmp_pages3")
REPORT = os.path.join(WORK, "scripts", "renumber_report.json")
REP = {"counts": {}, "numbering": {}, "book": None, "book_pages": None}

ORDER = ["表紙", "目次", "用語", "構成と管理情報", "相関図", "相関図_old", "管理体制",
         "月次再起動", "バックアップ", "復旧", "異常時の対応", "チェックシート(月次・異常時)",
         "会議課題一覧(一時)", "付録 引用元と確認範囲", "要確認事項一覧", "7-5仮_サービス起動停止"]

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
        counts = {}
        for name in ORDER:
            sh = wsmap[name]
            p = os.path.join(PAGES_DIR, f"{name}.pdf")
            sh.ExportAsFixedFormat(0, p, 0, True, False)
            counts[name] = len(PdfReader(p).pages)
        REP["counts"] = counts
        print("PAGES:", counts, flush=True)
        page = 1
        for name in ORDER:
            n = counts[name]
            if name != "表紙":
                wsmap[name].PageSetup.FirstPageNumber = page
                REP["numbering"][name] = page
            page += n
        wb.Save()
        print("SAVED", flush=True)
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
    REP["book"] = VAULT_PDF
    REP["book_pages"] = len(PdfReader(VAULT_PDF).pages)
    assert REP["book_pages"] == sum(counts.values()), "book page mismatch"
    print(f"BOOK {VAULT_PDF}: {REP['book_pages']}p", flush=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(REP, f, ensure_ascii=False, indent=1)
    print("DONE", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
