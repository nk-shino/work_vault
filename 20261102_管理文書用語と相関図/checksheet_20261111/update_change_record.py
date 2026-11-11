# -*- coding: utf-8 -*-
"""Add the 2026-11-11 split entry to the change-record form."""
from pathlib import Path

import fitz
import win32com.client as win32

HERE = Path(__file__).resolve().parent
SRC = HERE / "word" / "NR6010T0201_work.doc"
OUT = HERE / "word" / "split" / "NR6010T0201_work.doc"
OUT.parent.mkdir(parents=True, exist_ok=True)

ROW = 20
VALUES = {
    1: "×",
    2: "2026年11月11日",
    3: "定期点検チェックシートを点検周期別の3ファイル（月次10件・年次10件・週次8件）に分割。"
       "各様式の項目は行頭左揃えに統一。判定基準・確認方法・証跡はLNB管理書§6-2へ分離",
    4: "3",
    5: "2026年11月11日",
}

OUT.write_bytes(SRC.read_bytes())
word = win32.DispatchEx("Word.Application")
word.Visible = False
word.DisplayAlerts = 0
doc = word.Documents.Open(str(OUT), False, False, False)
try:
    t = doc.Tables(1)
    for c, text in VALUES.items():
        t.Cell(ROW, c).Range.Text = text
    # the added row makes the trailing empty paragraph overflow onto page 2
    doc.Paragraphs(doc.Paragraphs.Count).Range.Delete()
    doc.SaveAs2(str(OUT), 0)
    pdf = OUT.with_suffix(".pdf")
    doc.ExportAsFixedFormat(str(pdf), 17)
finally:
    doc.Close(False)
    word.Quit()

d = fitz.open(str(pdf))
for i, page in enumerate(d, 1):
    pix = page.get_pixmap(dpi=150)
    pix.save(str(pdf.with_name(f"{pdf.stem}_p{i}.png")))
print("pages", len(d))
