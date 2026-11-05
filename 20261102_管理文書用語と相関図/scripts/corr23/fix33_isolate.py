import sys, io, os, shutil, traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import pythoncom, win32com.client
BASE = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\corr23"
SRC = os.path.join(BASE, "refix2", "Pana-CIM管理手順書案_未承認.xlsx")
VARS = {  # name: (width, height, reassert, wordwrap)
    "A185":  (185.0, None, False, None),
    "B168h40": (None, 40.0, False, None),
    "C185h40": (185.0, 40.0, False, None),
    "D168re": (None, None, True, None),
    "E176":  (176.0, None, False, None),
    "F168nw": (None, None, False, False),
}
pythoncom.CoInitialize()
xl = win32com.client.DispatchEx("Excel.Application")
xl.Visible = False; xl.DisplayAlerts = False
try:
    for tag, (w, h, re_, ww) in VARS.items():
        p = os.path.join(BASE, "refix2", f"iso_{tag}.xlsx")
        shutil.copy2(SRC, p)
        wb = xl.Workbooks.Open(p, ReadOnly=False)
        try:
            sh = wb.Worksheets("相関図②").Shapes("g2_e_e17_l")
            if w is not None: sh.Width = w
            if h is not None: sh.Height = h
            if re_: sh.TextFrame2.TextRange.Text = sh.TextFrame2.TextRange.Text
            if ww is not None: sh.TextFrame2.WordWrap = ww
            wb.Save()
        finally:
            try: wb.Close(SaveChanges=False)
            except Exception as ex:
                if "0xE0000002" not in str(ex) and "-2147418111" not in str(ex): raise
        # 頁出力
        wb2 = xl.Workbooks.Open(p, ReadOnly=True)
        try:
            out = os.path.join(BASE, "refix2", f"iso_{tag}.pdf")
            if os.path.exists(out): os.remove(out)
            wb2.Worksheets("相関図②").ExportAsFixedFormat(0, out, 0, True, False)
        finally:
            try: wb2.Close(SaveChanges=False)
            except Exception as ex:
                if "0xE0000002" not in str(ex) and "-2147418111" not in str(ex): raise
        print("done", tag)
finally:
    xl.Quit(); pythoncom.CoUninitialize()

import fitz
FULL = "EE17 DB完全バックアップ(設定間隔·外部保管可)"
for tag in VARS:
    doc = fitz.open(os.path.join(BASE, "refix2", f"iso_{tag}.pdf"))
    txt = doc[0].get_text()
    lines = [l for l in txt.splitlines() if "EE17" in l or l.strip() in ("可)", "可", ")", "可 )")]
    hit = FULL in txt.replace("\n", "")
    print(f"{tag:8s} full={'YES' if hit else 'no '} lines={lines!r}")
    doc.close()
print("ISOLATE_DONE")
