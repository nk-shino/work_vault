# -*- coding: utf-8 -*-
"""相関図のエッジ8本+ラベル8個をノード実測位置に合わせて再構築する。
ノード座標(T0=168/X0=40 適用後の実測)に整合させる。既存 rel_e*/rel_l_* は削除。"""
import sys, io, time, json, warnings
warnings.filterwarnings("ignore")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pythoncom, win32com.client

WORK = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\issue6263_work"
BOOKS = {
 "pana": r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\Pana-CIM管理手順書案_未承認.xlsx",
 "lnb":  r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\LNB管理手順書案_未承認.xlsx",
}
DVAL = {v["id"]: v.get("val", "") for v in json.load(open(WORK + r"\kanzume_drawio.json", encoding="utf-8"))["第一層_全体相関図"]["v"]}

def rgb(h):
    h = h.lstrip("#")
    return int(h[0:2], 16) + int(h[2:4], 16) * 256 + int(h[4:6], 16) * 65536

# (名, x1,y1,x2,y2, 線色, ラベル, lx,ly,lw) — 矢先は (x2,y2)。座標は絶対pt
EDGES = [
    ("e1", 152.5,223, 152.5,296, "2E7D32", DVAL["e1_lbl"], 158,250, 60),
    ("e2", 245,298, 287,211, "2E75B6", DVAL["e2_lbl"], 222,250, 40),
    ("e3", 245,342, 287,493, "82B366", DVAL["e3_lbl"], 200,445, 68),
    ("e4", 107,584, 117,418, "D6B656", DVAL["e4_lbl"], 72,528, 36),
    ("e5", 225,584, 195,418, "D6B656", DVAL["e5_lbl"], 240,531, 22),
    ("e6", 341,340, 245,330, "8A6D0B", DVAL["e6_lbl"], 362,320, 44),
    ("e7", 456,340, 245,318, "8A6D0B", DVAL["e7_lbl"], 410,326, 22),
    ("e8", 393.5,292, 245,306, "2E75B6", DVAL["e8_lbl"], 322,305, 92),
]

def set_text(sh, text, size, color="595959"):
    tf = sh.TextFrame2
    tf.WordWrap = -1
    tf.AutoSize = 0
    tf.HorizontalAnchor = 1
    tf.VerticalAnchor = 3
    tf.MarginLeft = 1; tf.MarginRight = 1; tf.MarginTop = 0; tf.MarginBottom = 0
    tr = tf.TextRange
    tr.Text = text
    f = tr.Font
    f.Name = "Meiryo UI"; f.NameFarEast = "Meiryo UI"
    f.Size = size; f.Bold = 0
    f.Fill.ForeColor.RGB = rgb(color)

def fix(path):
    pythoncom.CoInitialize()
    xl = win32com.client.DispatchEx("Excel.Application")
    xl.Visible = False; xl.DisplayAlerts = False
    try:
        wb = xl.Workbooks.Open(path)
        ws = wb.Worksheets("相関図")
        for nm in list(ws.Shapes.Name if False else [s.Name for s in ws.Shapes]):
            if nm.startswith("rel_e") or nm.startswith("rel_l_"):
                ws.Shapes(nm).Delete()
        for nm, x1, y1, x2, y2, col, lbl, lx, ly, lw in EDGES:
            ln = ws.Shapes.AddLine(x1, y1, x2, y2)
            ln.Name = "rel_" + nm
            ln.Line.ForeColor.RGB = rgb(col)
            ln.Line.Weight = 1.25
            ln.Line.EndArrowheadStyle = 2
            tb = ws.Shapes.AddTextbox(1, lx, ly, lw, 11)
            tb.Name = "rel_l_" + nm
            tb.Fill.Visible = 0
            tb.Line.Visible = 0
            set_text(tb, lbl, 7.5)
        # z4 のゾーンラベルは右寄せ(e7 の経路と重ならないように)
        z4 = ws.Shapes("rel_z4")
        z4.TextFrame2.HorizontalAnchor = 2   # msoAnchorCenter — 右端に寄せて配置
        z4.TextFrame2.MarginRight = 6
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
