import sys, io, os, traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import pythoncom, win32com.client
BASE = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\corr23"
DST = os.path.join(BASE, "refix2")
BOOKS = {"pana": "Pana-CIM管理手順書案_未承認.xlsx", "lnb": "LNB管理手順書案_未承認.xlsx"}
pythoncom.CoInitialize()
xl = None
try:
    xl = win32com.client.DispatchEx("Excel.Application")
    xl.Visible = False; xl.DisplayAlerts = False
    for bk, fn in BOOKS.items():
        wb = xl.Workbooks.Open(os.path.join(DST, fn), ReadOnly=True)
        try:
            for tag, shname in (("p2", "相関図②"), ("p3", "相関図③")):
                out = os.path.join(DST, f"{bk}_{tag}_test.pdf")
                if os.path.exists(out): os.remove(out)
                wb.Worksheets(shname).ExportAsFixedFormat(0, out, 0, True, False)
                print("exported", bk, tag)
        finally:
            try: wb.Close(SaveChanges=False)
            except Exception as ex:
                if "0xE0000002" not in str(ex) and "-2147418111" not in str(ex): raise
except Exception:
    traceback.print_exc(); sys.exit(1)
finally:
    if xl is not None:
        try: xl.Quit()
        except Exception: pass
        xl = None
    pythoncom.CoUninitialize()

import fitz
NEED = ["EE01 サーバー間連携〔T1:-7-〕",
        "EE02 実装データの収集・上位送信",
        "EE08 稼働モニタ表示〔T1b·T1:-39-〕",
        "EE17 DB完全バックアップ(設定間隔·外部保管可)"]
ok_all = True
for bk in BOOKS:
    doc = fitz.open(os.path.join(DST, f"{bk}_p2_test.pdf"))
    txt = doc[0].get_text()
    for s in NEED:
        hit = s in txt
        ok_all &= hit
        print(("  OK  " if hit else "  MISS"), bk, repr(s))
    doc.close()
    doc = fitz.open(os.path.join(DST, f"{bk}_p3_test.pdf"))
    page = doc[0]
    # F1: N09付近のクロップ(N09の非表示行テキストでアンカー)
    hits = page.search_for("接続エッジは推定")
    if hits:
        r = hits[0]; clip = fitz.Rect(r.x0-120, r.y0-90, r.x1+140, r.y1+120)
        page.get_pixmap(matrix=fitz.Matrix(4,4), clip=clip).save(os.path.join(DST, f"{bk}_f1_n09.png"))
        print("  f1 crop saved", bk)
    # F2: 帯右縁×s3 のクロップ(dgsr領域の右側)
    hd = page.search_for("データ")
    if hd:
        r = hd[-1]; clip = fitz.Rect(r.x1-60, r.y0-140, r.x1+220, r.y1+320)
        page.get_pixmap(matrix=fitz.Matrix(4,4), clip=clip).save(os.path.join(DST, f"{bk}_f2_band.png"))
        print("  f2 crop saved", bk)
    doc.close()
print("PAGE_TEST_DONE ok_all=", ok_all)
