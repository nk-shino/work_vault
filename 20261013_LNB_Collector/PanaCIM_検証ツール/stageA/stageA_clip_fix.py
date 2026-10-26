# -*- coding: utf-8 -*-
"""相関図のクリップ修正: Meiryo UI 行間(~1.75x)による 3 行テキストの欠落対策。
- cima/cimc: 高さ 38→60(3行分)
- n1: 高さ 56→74(5行分)
- z4 ゾーンラベル: 中央寄せ→右寄せ(e6/e7 の経路と重なるため)
- e3 ラベル: 2 行化(バックアップ出力／（FULbak）)
- e8 ラベル: 1 行分の幅に拡張(由来が欠落)"""
import sys, io, time, warnings
warnings.filterwarnings("ignore")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pythoncom, win32com.client

BOOKS = {
 "pana": r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\Pana-CIM管理手順書案_未承認.xlsx",
 "lnb":  r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\LNB管理手順書案_未承認.xlsx",
}
DVAL = None  # e3/e8 は JSON から取り直す
import json
WORK = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\issue6263_work"
_v = {v["id"]: v.get("val", "") for v in json.load(open(WORK + r"\kanzume_drawio.json", encoding="utf-8"))["第一層_全体相関図"]["v"]}
E3, E8 = _v["e3_lbl"], _v["e8_lbl"]

def rgb(h):
    h = h.lstrip("#")
    return int(h[0:2], 16) + int(h[2:4], 16) * 256 + int(h[4:6], 16) * 65536

def fix(path):
    pythoncom.CoInitialize()
    xl = win32com.client.DispatchEx("Excel.Application")
    xl.Visible = False; xl.DisplayAlerts = False
    try:
        wb = xl.Workbooks.Open(path)
        ws = wb.Worksheets("相関図")
        for nm in ("rel_n_cima", "rel_n_cimc"):
            s = ws.Shapes(nm)
            s.Height = 60
        ws.Shapes("rel_n_n1").Height = 74
        z4 = ws.Shapes("rel_z4")
        # Excel TextFrame2.HorizontalAnchor は右寄せ(3)非対応のため、
        # 左アンカー+段落右寄せで実現する
        z4.TextFrame2.HorizontalAnchor = 1
        z4.TextFrame2.TextRange.ParagraphFormat.Alignment = 3
        z4.TextFrame2.MarginLeft = 2
        z4.TextFrame2.MarginRight = 6
        # e3 ラベル: 2 行化
        lb3 = ws.Shapes("rel_l_e3")
        lb3.Top = 438; lb3.Left = 200; lb3.Width = 68; lb3.Height = 30
        tf = lb3.TextFrame2
        tf.WordWrap = -1; tf.AutoSize = 0
        tf.HorizontalAnchor = 1; tf.VerticalAnchor = 3
        tf.MarginLeft = 1; tf.MarginRight = 1; tf.MarginTop = 0; tf.MarginBottom = 0
        tr = tf.TextRange; tr.Text = E3
        f = tr.Font
        f.Name = "Meiryo UI"; f.NameFarEast = "Meiryo UI"; f.Size = 7.5; f.Bold = 0
        f.Fill.ForeColor.RGB = rgb("595959")
        # e8 ラベル: 幅拡張で 1 行化
        lb8 = ws.Shapes("rel_l_e8")
        lb8.Top = 300; lb8.Left = 322; lb8.Width = 118; lb8.Height = 22
        tf = lb8.TextFrame2
        tf.WordWrap = -1; tf.AutoSize = 0
        tf.HorizontalAnchor = 1; tf.VerticalAnchor = 3
        tf.MarginLeft = 1; tf.MarginRight = 1; tf.MarginTop = 0; tf.MarginBottom = 0
        tr = tf.TextRange; tr.Text = E8
        f = tr.Font
        f.Name = "Meiryo UI"; f.NameFarEast = "Meiryo UI"; f.Size = 7.5; f.Bold = 0
        f.Fill.ForeColor.RGB = rgb("595959")
        wb.Save()
        n = ws.Shapes.Count
    finally:
        wb.Close(SaveChanges=False)
        xl.Quit()
        pythoncom.CoUninitialize()
    return n

for tag, path in BOOKS.items():
    for attempt in range(1, 4):
        try:
            n = fix(path)
            print(f"[{tag}] shapes={n}")
            break
        except Exception as e:
            print(f"[{tag}] retry {attempt}: {e}")
            time.sleep(2)
    else:
        sys.exit(1)
print("RESULT: OK")
