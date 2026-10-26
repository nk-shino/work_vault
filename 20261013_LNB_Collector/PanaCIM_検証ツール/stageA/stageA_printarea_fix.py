# -*- coding: utf-8 -*-
"""相関図の印刷範囲を $A$1:$AY$58 へ拡張する(n1 下端 778pt が旧範囲の下端 747pt を
超えており PDF 出力で印刷範囲により切り取られていたため。行 56-58 は空)。
PageSetup アクセスは segfont 対策で SET のみ・書籍毎に独立セッション+リトライ。"""
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
            ws.PageSetup.PrintArea = "$A$1:$AY$58"
            wb.Save()
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

for tag, path in BOOKS.items():
    for attempt in range(1, 4):
        try:
            fix(path)
            print(f"[{tag}] print area -> $A$1:$AY$58")
            break
        except Exception as e:
            print(f"[{tag}] retry {attempt}: {e}")
            time.sleep(3)
    else:
        sys.exit(1)
print("RESULT: OK")
