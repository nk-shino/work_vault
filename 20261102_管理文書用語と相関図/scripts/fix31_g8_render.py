# -*- coding: utf-8 -*-
"""fix31_g8_render.py — 現行相関図シートをPDF化しPNGへラスタライズ(読み取り専用)"""
import os, sys
import win32com.client as win32

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAULT = os.path.join(BASE, "..", "..", "OneDrive - NK", "ドキュメント", "Work_Vault", "10_業務全般", "PanaCIM_LNB", "01_成果物")
BOOKS = {"pana": os.path.join(VAULT, "Pana-CIM管理手順書案_未承認.xlsx"),
         "lnb": os.path.join(VAULT, "LNB管理手順書案_未承認.xlsx")}
OUTDIR = os.path.join(BASE, "scripts", "tmp_g8_render")
os.makedirs(OUTDIR, exist_ok=True)

def main():
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    try:
        app.AutoSaveOn = False
    except Exception:
        pass
    try:
        for bk, path in BOOKS.items():
            wb = app.Workbooks.Open(path, UpdateLinks=0, ReadOnly=True)
            try:
                wb.Worksheets("相関図").ExportAsFixedFormat(
                    Type=0, Filename=os.path.join(OUTDIR, "cur_%s_相関図.pdf" % bk),
                    Quality=0, IncludeDocProperties=False, IgnorePrintAreas=False, OpenAfterPublish=False)
            finally:
                wb.Close(SaveChanges=False)
    finally:
        app.Quit()
    import fitz
    for bk in BOOKS:
        doc = fitz.open(os.path.join(OUTDIR, "cur_%s_相関図.pdf" % bk))
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2.2, 2.2))
        pix.save(os.path.join(OUTDIR, "cur_%s_相関図.png" % bk))
        print(bk, "pages=", len(doc), "size=", (pix.width, pix.height))
    print("DONE ->", OUTDIR)

if __name__ == "__main__":
    main()
