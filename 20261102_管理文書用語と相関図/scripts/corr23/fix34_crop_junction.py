# -*- coding: utf-8 -*-
"""fix34_crop_junction.py — 現行vaultの相関図③をPDF出力し、
EE05ラベル下端×N08_box上端の接合部を高倍率cropする(読み取り専用·TEMP出力)。
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import win32com.client as win32

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = r"C:/Users/ss80751/OneDrive - NK/ドキュメント/Work_Vault/10_業務全般/PanaCIM_LNB/01_成果物"
BOOKS = {
    "pana": os.path.join(VAULT, "Pana-CIM管理手順書案_未承認.xlsx"),
    "lnb": os.path.join(VAULT, "LNB管理手順書案_未承認.xlsx"),
}
ZOOM = 6.0


def main():
    import pymupdf as fitz
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    pdfs = {}
    try:
        for bk, path in BOOKS.items():
            wb = app.Workbooks.Open(path, UpdateLinks=0, ReadOnly=True)
            pdf = os.path.join(HERE, "tmp_fix34_%s_3.pdf" % bk)
            wb.Worksheets("相関図③").ExportAsFixedFormat(0, pdf)
            wb.Close(SaveChanges=False)
            pdfs[bk] = pdf
            print("exported", bk)
    finally:
        try:
            app.Quit()
        except Exception:
            pass
    for bk, pdf in pdfs.items():
        doc = fitz.open(pdf)
        page = doc[0]
        hits = page.search_for("EE05")
        print(bk, "EE05 hits:", [tuple(round(v, 1) for v in r) for r in hits])
        if not hits:
            doc.close()
            continue
        # ラベルbboxの下端周辺を広めにcrop(左右はタグ~box右縁、上下は線上端~box内)
        r = hits[0]
        clip = fitz.Rect(r.x0 - 30, r.y0 - 40, r.x1 + 60, r.y1 + 60)
        pix = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM), clip=clip)
        png = os.path.join(HERE, "dbg_fix34_%s_3_junction.png" % bk)
        pix.save(png)
        print("saved", os.path.basename(png), pix.width, "x", pix.height)
        # 参考用: N08 ノード題 materia の位置も出す
        for probe in ("LWS", "アンドン", "LNB"):
            h2 = page.search_for(probe)
            if h2:
                print("  probe %-6s ->" % probe, [tuple(round(v, 1) for v in x) for x in h2[:3]])
        doc.close()
    print("CROP DONE")


if __name__ == "__main__":
    main()
