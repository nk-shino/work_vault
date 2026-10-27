# -*- coding: utf-8 -*-
"""異常時の対応: img_1(行118)の手動改頁を解除し、導入行(行116)の前に移す"""
import io, sys, time, warnings
warnings.filterwarnings("ignore")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pythoncom, win32com.client

BOOK = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\Pana-CIM管理手順書案_未承認.xlsx"

def run():
    pythoncom.CoInitialize()
    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    try:
        wb = excel.Workbooks.Open(BOOK, 0)
        try:
            ws = wb.Worksheets("異常時の対応")
            ws.Activate()
            ws.Range("A118").PageBreak = 0        # xlNone: 手動改頁を消す
            ws.HPageBreaks.Add(ws.Range("A116"))  # 導入行から頁頭へ
            wb.Save()
            print("OK: break moved 118 -> 116")
        finally:
            try:
                wb.Close(SaveChanges=False)
            except Exception as e:
                print("WARN Close:", e)
    finally:
        try:
            excel.Quit()
        except Exception as e:
            print("WARN Quit:", e)
        pythoncom.CoUninitialize()

for attempt in range(1, 6):
    try:
        run()
        break
    except Exception as e:
        print(f"retry {attempt}: {e!r}")
        time.sleep(2)
else:
    sys.exit(1)
