# -*- coding: utf-8 -*-
"""Stage C 検証: ブックをPDF出力し、キャプション文本のある頁を特定してPNG描画する。
用法: python stageC_export_check.py <ブック.xlsx> <出力.pdf> <PNG接頭辞>
"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BOOK = sys.argv[1]
PDF = sys.argv[2]
PREFIX = sys.argv[3]

import win32com.client as w

excel = w.DispatchEx("Excel.Application")
excel.Visible = False
excel.DisplayAlerts = False
try:
    wb = excel.Workbooks.Open(BOOK)
    wb.ExportAsFixedFormat(0, PDF)  # xlTypePDF, Quality=0(標準)
    try:
        wb.Close(False)
    except Exception:
        pass
finally:
    excel.Quit()
print("PDF exported:", PDF)

import fitz  # PyMuPDF

doc = fitz.open(PDF)
print("総頁数:", len(doc))
targets = ["図1 LNB構成情報画面", "図2 個別スイッチ画面", "図3 再起動系メニュー",
           "参考添付：DGS", "参考添付1", "参考添付2", "参考添付3"]
found = {}
for i in range(len(doc)):
    text = doc[i].get_text()
    for t in targets:
        if t in text and t not in found:
            found[t] = i + 1
for t in targets:
    print(t, "-> p", found.get(t, "未検出"))
# 見つかった頁と直前頁を描画(見開きで分断確認)
pages = sorted(set([p for p in found.values()] + [p - 1 for p in found.values() if p > 1]))
for p in pages:
    pix = doc[p - 1].get_pixmap(dpi=110)
    out = "%s_p%03d.png" % (PREFIX, p)
    pix.save(out)
    print("render:", out)
doc.close()
