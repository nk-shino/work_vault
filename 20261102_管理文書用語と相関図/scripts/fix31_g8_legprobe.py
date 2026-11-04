# -*- coding: utf-8 -*-
"""fix31_g8_legprobe.py — 凡例の色付け失敗の原因特定(数値のみ出力·保存しない)。
各凡例行について、どの行(index)がどの例外クラスで失敗するかだけを報告する。
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import win32com.client as win32

XLSX = (r"C:/Users/ss80751/OneDrive - NK/ドキュメント/Work_Vault"
        r"/10_業務全般/PanaCIM_LNB/01_成果物/Pana-CIM管理手順書案_未承認.xlsx")

app = win32.DispatchEx("Excel.Application")
app.Visible = False
app.DisplayAlerts = False
try:
    wb = app.Workbooks.Open(XLSX, UpdateLinks=0, ReadOnly=True)
    ws = wb.Worksheets("相関図①")
    for i in range(4):
        sh = ws.Shapes("%s_leg%d" % ("g1", i))
        tr = sh.TextFrame2.TextRange
        txt = tr.Text
        marks = [j for j, chx in enumerate(txt) if chx in "■□"]
        print("leg%d: len=%d marks=%d" % (i, len(txt), len(marks)))
        for mi in marks:
            try:
                ch = tr.Characters.Item(mi + 1, 1)
                ch.Font.Fill.ForeColor.RGB = 0xFF0000  # 診断値(保存しない)
                print("  char@%d: A-direct OK" % (mi + 1))
            except Exception as e:
                print("  char@%d: A-direct %s" % (mi + 1, type(e).__name__))
        # 段階切り分け
        try:
            cs = tr.Characters
            print("  step1 Characters: %s" % type(cs).__name__)
        except Exception as e:
            cs = None
            print("  step1 Characters: %s" % type(e).__name__)
        if cs is not None:
            try:
                c1 = cs.Item(1)
                c1.Font.Fill.ForeColor.RGB = 0xFF0000
                print("  single-arg Item(1) color put: OK readback=%s" % hex(c1.Font.Fill.ForeColor.RGB))
            except Exception as e:
                print("  single-arg Item(1) color put: %s" % type(e).__name__)
    wb.Close(SaveChanges=False)
finally:
    try:
        app.Quit()
    except Exception:
        pass
print("LEGPROBE DONE")
