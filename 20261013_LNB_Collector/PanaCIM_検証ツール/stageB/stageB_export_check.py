# -*- coding: utf-8 -*-
"""Stage B検証: Pana書籍を全頁PDF出力し、画像挿入4シートの頁をPNG化する"""
import os, io, sys, time, warnings
warnings.filterwarnings("ignore")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pythoncom, win32com.client

BOOK = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\Pana-CIM管理手順書案_未承認.xlsx"
OUT = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\issue6263_work\stageB_check.pdf"

def export():
    pythoncom.CoInitialize()
    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    try:
        wb = excel.Workbooks.Open(BOOK, 0, True)  # ReadOnly
        try:
            wb.ExportAsFixedFormat(0, OUT)  # xlTypePDF
        finally:
            try:
                wb.Close(SaveChanges=False)
            except Exception as e:
                print(f"WARN Close: {e}")
    finally:
        try:
            excel.Quit()
        except Exception as e:
            print(f"WARN Quit: {e}")
        pythoncom.CoUninitialize()

for attempt in range(1, 6):
    try:
        if os.path.exists(OUT):
            os.remove(OUT)
        export()
        break
    except Exception as e:
        print(f"retry {attempt}: {e}")
        time.sleep(2)
else:
    sys.exit(1)
print("PDF:", OUT, os.path.getsize(OUT) // 1024, "KB")

import pymupdf
doc = pymupdf.open(OUT)
print("pages:", len(doc))
markers = {
    "月次図1": "図1 手順1：スタート",
    "月次図2": "図2 手順2：理由コード",
    "バック図1": "図1(p11)",
    "バック図7": "図7(p12)",
    "7-5図1": "図1 手順1〜2",
    "7-5図2": "図2 手順3",
    "異常時導入": "参考画像(出典：操作手順書",
    "異常時画像8": "画像8(手順との対応：未確定・認証情報は伏字)",
    "異常時画像14": "画像14(手順との対応：未確定)",
}
found = {}
for i, page in enumerate(doc):
    t = page.get_text()
    for k, m in markers.items():
        if m in t and k not in found:
            found[k] = i + 1
print("markers:", found)
pages = sorted({p for p in found.values()})
for p in pages:
    pg = doc[p - 1]
    pix = pg.get_pixmap(dpi=110)
    fn = OUT.replace(".pdf", f"_p{p}.png")
    pix.save(fn)
    print("render:", os.path.basename(fn))
doc.close()
