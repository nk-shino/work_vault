# -*- coding: utf-8 -*-
"""n1(出典note)の高さを 92pt(6行分)へ拡張 — Meiryo UI 8pt の実行間 ~15pt で 5 行=75pt が 74pt に入らず
最終行「解決後に図解を拡充する方針」が行単位クリップされるため。"""
import sys, io, time, warnings
warnings.filterwarnings("ignore")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pythoncom, win32com.client

BOOKS = {
 "pana": r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\Pana-CIM管理手順書案_未承認.xlsx",
 "lnb":  r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\LNB管理手順書案_未承認.xlsx",
}

def fix(path):
    pythoncom.CoInitialize()
    xl = win32com.client.DispatchEx("Excel.Application")
    xl.Visible = False; xl.DisplayAlerts = False
    try:
        wb = xl.Workbooks.Open(path)
        try:
            ws = wb.Worksheets("相関図")
            ws.Shapes("rel_n_n1").Height = 92
            wb.Save()
            n = ws.Shapes.Count
        except Exception:
            try: wb.Close(SaveChanges=False)
            except Exception: pass
            raise
        try:
            wb.Close(SaveChanges=False)
        except Exception:
            pass
    finally:
        try: xl.Quit()
        except Exception: pass
        pythoncom.CoUninitialize()
    return n

for tag, path in BOOKS.items():
    for attempt in range(1, 4):
        try:
            print(f"[{tag}] shapes={fix(path)}")
            break
        except Exception as e:
            print(f"[{tag}] retry {attempt}: {e}")
            time.sleep(3)
    else:
        sys.exit(1)
print("RESULT: OK")
