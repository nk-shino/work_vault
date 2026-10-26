# -*- coding: utf-8 -*-
"""相関図シートのPDF出力(書籍毎に独立COMセッション+リトライ)。"""
import sys, io, time, warnings
warnings.filterwarnings("ignore")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pythoncom, win32com.client, fitz

BOOKS = {
 "pana": r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\Pana-CIM管理手順書案_未承認.xlsx",
 "lnb":  r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\LNB管理手順書案_未承認.xlsx",
}
WORK = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\issue6263_work"

def export_one(tag, path):
    pythoncom.CoInitialize()
    xl = win32com.client.DispatchEx("Excel.Application")
    xl.Visible = False; xl.DisplayAlerts = False
    try:
        wb = xl.Workbooks.Open(path)
        try:
            wb.Worksheets("相関図").ExportAsFixedFormat(0, WORK + rf"\kankeezu_{tag}.pdf")
        finally:
            try:
                wb.Close(SaveChanges=False)
            except Exception:
                pass
    finally:
        try:
            xl.Quit()
        except Exception:
            pass
        pythoncom.CoUninitialize()

for tag, path in BOOKS.items():
    for attempt in range(1, 4):
        try:
            export_one(tag, path)
            print(f"[{tag}] exported")
            break
        except Exception as e:
            print(f"[{tag}] retry {attempt}: {e}")
            time.sleep(3)
    else:
        sys.exit(1)

for tag in BOOKS:
    doc = fitz.open(WORK + rf"\kankeezu_{tag}.pdf")
    p = doc[0]
    p.get_pixmap(dpi=120).save(WORK + rf"\kankeezu_{tag}.png")
    print(f"[{tag}] pages={doc.page_count} size={p.rect.width:.2f}x{p.rect.height:.2f}")
    doc.close()
doc = fitz.open(WORK + r"\kankeezu_pana.pdf")
p = doc[0]
def crop(name, x0, y0, x1, y1):
    p.get_pixmap(dpi=200, clip=fitz.Rect(x0, y0, x1, y1)).save(WORK + rf"\zoom_{name}.png")
crop("esxi",   45, 260, 260, 425)
crop("webzone", 35, 570, 515, 700)
crop("fa_e8",  240, 285, 515, 355)
crop("n1_backup", 240, 440, 515, 770)
print("zooms done")
