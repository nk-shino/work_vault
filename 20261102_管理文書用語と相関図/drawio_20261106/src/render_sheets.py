# -*- coding: utf-8 -*-
"""指定ブックの複数シートをPDF/PNGに描画する（読み取り専用）。

使い方:
  python render_sheets.py <xlsx> <out_dir> <sheet1> [<sheet2> ...]
"""
import sys
from pathlib import Path

import fitz
import win32com.client as win32


def safe(name):
    return "".join(c if c not in '\\/:*?"<>|' else "_" for c in name)


def main():
    xlsx = sys.argv[1]
    out_dir = Path(sys.argv[2])
    sheets = sys.argv[3:]
    out_dir.mkdir(parents=True, exist_ok=True)
    xl = win32.DispatchEx("Excel.Application")
    xl.Visible = False
    xl.DisplayAlerts = False
    try:
        wb = xl.Workbooks.Open(xlsx, UpdateLinks=0, ReadOnly=True)
        for needle in sheets:
            ws = next(s for s in wb.Worksheets if needle == s.Name)
            pdf = out_dir / f"{safe(ws.Name)}.pdf"
            ws.ExportAsFixedFormat(0, str(pdf))
            doc = fitz.open(str(pdf))
            page = doc[0]
            pix = page.get_pixmap(dpi=150)
            png = out_dir / f"{safe(ws.Name)}.png"
            pix.save(str(png))
            print(ws.Name, "pages", doc.page_count, "png", pix.width, pix.height)
            doc.close()
        wb.Close(False)
    finally:
        xl.Quit()


if __name__ == "__main__":
    main()
