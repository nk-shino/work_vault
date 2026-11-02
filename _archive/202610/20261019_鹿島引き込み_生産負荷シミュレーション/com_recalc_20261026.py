# -*- coding: utf-8 -*-
"""指示32 COM再計算: openpyxl編集後の数式キャッシュ復元 (ピボットrefreshは行わない)"""
import sys, os
import win32com.client as win32
import pythoncom

sys.stdout.reconfigure(encoding='utf-8')
X13 = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\boss_pivot13\比較グラフ_x1.3_original.xlsx"

pythoncom.CoInitialize()
xl = win32.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
try:
    wb = xl.Workbooks.Open(X13, UpdateLinks=0)
    xl.CalculateFullRebuild()
    wb.Save()
    wb.Close(SaveChanges=False)
    print("COM再計算・保存完了:", X13)
finally:
    xl.Quit()
    pythoncom.CoUninitialize()
