# -*- coding: utf-8 -*-
"""Stage A: 両案に「相関図」シートを追加し、目次と 2-2/2-3 の本文を更新する。
出典: PanaCIM_LNB_確実構成図.drawio (第一層_全体相関図) — 確定事項のみ移植。
- シートは 構成と管理情報 のコピー(様式ヘッダ・余白・列幅を継承)の上に構築する
- 図形はネイティブ図形(ユーザー決定 2026-10-23): 矩形/角丸/直線/テキストボックス
- レイアウトは A4 縦 1 頁(可視幅 520.9pt・可視高さ 767pt)に収める
"""
import sys, io, time, json, warnings
warnings.filterwarnings("ignore")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pythoncom, win32com.client

WORK = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\issue6263_work"
BOOKS = {
    "pana": r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\Pana-CIM管理手順書案_未承認.xlsx",
    "lnb":  r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\LNB管理手順書案_未承認.xlsx",
}
DRAWIO = json.load(open(WORK + r"\kanzume_drawio.json", encoding="utf-8"))["第一層_全体相関図"]
DVAL = {v["id"]: v.get("val", "") for v in DRAWIO["v"]}

X0, T0 = 40.0, 168.0          # 図形原点(ヘッダ5行+メモ3行の下・印刷範囲 A..Z 内)
ROWH = 12.8

def rgb(hexstr):
    h = hexstr.lstrip("#")
    return int(h[0:2], 16) + int(h[2:4], 16) * 256 + int(h[4:6], 16) * 65536

# rel 座標 (x, y, w, h)
ZONES = [
    ("z1", "製造現場",        (0,   0, 225,  70)),
    ("z2", "サーバー環境",    (0,  82, 225, 180)),
    ("z3", "表示系",          (237, 0, 233, 140)),
    ("z4", "操作・連携（FA）", (237,152, 233,110)),
    ("z5", "保存領域",        (237,274, 233,110)),
    ("z6", "操作・連携（Web）",(0, 396, 470, 110)),
]
NODES = [  # (id, text, rel, fill, fontsize, anchor_top)
    ("mounter", DVAL["mounter"], (10,  15, 205,  40), "DFF0D8", 9.0, False),
    ("esxi",    DVAL["esxi"],    (10, 100, 205, 150), "E9ECEF", 8.0, True),
    ("appctrl", DVAL["appctrl"], (20, 128, 185,  48), "D9EAF7", 8.5, False),
    ("note",    DVAL["cimc_sv_note"], (20, 184, 185, 54), "FDEDEC", 8.0, False),
    ("monitor", DVAL["monitor"], (247, 22, 213,  42), "D9EAF7", 8.5, False),
    ("andon",   DVAL["andon"],   (247, 76, 213,  48), "D9EAF7", 8.0, False),
    ("lnb",     DVAL["lnb"],     (247,172, 108,  38), "FFF2CC", 8.0, False),
    ("dgs",     DVAL["dgs"],     (363,172, 106,  38), "FFF2CC", 8.0, False),
    ("backup",  DVAL["backup"],  (247,298, 213,  54), "D5E8D4", 8.0, False),
    ("cima",    DVAL["cima"],    (12, 416, 110,  38), "FFF2CC", 8.0, False),
    ("cimc",    DVAL["cimc"],    (130,416, 110,  38), "FFF2CC", 8.0, False),
    ("n1",      DVAL["n1"],      (0, 518, 470,  56), "FEF9E7", 8.0, False),
]
# 辺: (名, x1,y1,x2,y2, 色, ラベル, ラベルrel, ラベル幅) — 矢先は (x2,y2) 側
EDGES = [
    ("e1", 156,170, 156,243, "2E7D32", DVAL["e1_lbl"], (162,196), 60),
    ("e2", 249,251, 291,158, "2E75B6", DVAL["e2_lbl"], (250,181), 40),
    ("e3", 249,287, 291,440, "82B366", DVAL["e3_lbl"], (200,392), 68),
    ("e4", 111,531, 117,365, "D6B656", DVAL["e4_lbl"], (76,478),  36),
    ("e5", 229,531, 195,365, "D6B656", DVAL["e5_lbl"], (240,478), 22),
    ("e6", 345,287, 249,281, "8A6D0B", DVAL["e6_lbl"], (300,270), 44),
    ("e7", 460,287, 249,270, "8A6D0B", DVAL["e7_lbl"], (368,265), 22),
    ("e8", 397,239, 249,259, "2E75B6", DVAL["e8_lbl"], (322,252), 92),
]

def set_text(sh, text, size, bold=False, color="000000", top=False, left=False):
    tf = sh.TextFrame2
    tf.WordWrap = -1          # msoTrue
    tf.AutoSize = 0           # msoAutoSizeNone
    tf.HorizontalAnchor = 1 if left else 2   # msoAnchorNone / msoAnchorCenter
    tf.VerticalAnchor = 1 if top else 3     # msoAnchorTop / msoAnchorMiddle
    tf.MarginLeft = 2; tf.MarginRight = 2; tf.MarginTop = 1; tf.MarginBottom = 1
    tr = tf.TextRange
    tr.Text = text
    f = tr.Font
    f.Name = "Meiryo UI"; f.NameFarEast = "Meiryo UI"
    f.Size = size; f.Bold = -1 if bold else 0
    f.Fill.ForeColor.RGB = rgb(color)

def build(wb, sec_title, notes):
    src = wb.Worksheets("構成と管理情報")
    assert src.Shapes.Count == 0, "コピー元に図形がある"
    src.Copy(None, src)                      # After:=src — 直後に挿入
    ws = wb.Worksheets(src.Index + 1)
    ws.Name = "相関図"
    for sh in list(ws.Shapes):
        sh.Delete()
    ws.Rows("6:80").Delete()
    ws.Rows("6:70").RowHeight = ROWH
    ws.Cells(6, 1).Value = sec_title
    c = ws.Cells(6, 1)
    c.Font.Bold = True; c.Font.Name = "Meiryo UI"; c.Font.Size = 10
    for i, t in enumerate(notes):
        ws.Cells(7 + i, 3).Value = t
        ws.Cells(7 + i, 3).Font.Name = "Meiryo UI"
        ws.Cells(7 + i, 3).Font.Size = 9
    # 塗り枠(背面) → ノード → 辺 → ラベル の順で追加
    for zid, ztxt, (x, y, w, h) in ZONES:
        sh = ws.Shapes.AddShape(1, X0 + x, T0 + y, w, h)
        sh.Name = "rel_" + zid
        sh.Fill.ForeColor.RGB = rgb("F8F9FA")
        sh.Fill.Transparency = 0.0
        sh.Line.ForeColor.RGB = rgb("BFBFBF")
        sh.Line.Weight = 0.75
        set_text(sh, ztxt, 8.0, bold=True, color="595959", top=True, left=True)
        sh.TextFrame.MarginLeft = 4; sh.TextFrame.MarginTop = 2
    for nid, txt, (x, y, w, h), fill, fs, top in NODES:
        sh = ws.Shapes.AddShape(5 if not top else 1, X0 + x, T0 + y, w, h)
        sh.Name = "rel_n_" + nid
        sh.Fill.ForeColor.RGB = rgb(fill)
        sh.Line.ForeColor.RGB = rgb("595959")
        sh.Line.Weight = 0.75
        set_text(sh, txt, fs, top=top)
    for nm, x1, y1, x2, y2, col, lbl, (lx, ly), lw in EDGES:
        ln = ws.Shapes.AddLine(X0 + x1, T0 + y1, X0 + x2, T0 + y2)
        ln.Name = "rel_" + nm
        ln.Line.ForeColor.RGB = rgb(col)
        ln.Line.Weight = 1.25
        ln.Line.EndArrowheadStyle = 2      # 三角
        tb = ws.Shapes.AddTextbox(1, X0 + lx, T0 + ly, lw, 11)
        tb.Name = "rel_l_" + nm
        tb.Fill.Visible = 0
        tb.Line.Visible = 0
        set_text(tb, lbl, 7.5, color="595959", left=True)
    ws.Rows("56:70").Delete()               # 行高設定の残りを掃除(図形は r55 以内)
    ws.PageSetup.PrintArea = "$A$1:$Z$55"
    return ws

def edit_book(xl, key, path):
    wb = xl.Workbooks.Open(path)
    try:
        if key == "pana":
            mt = wb.Worksheets("目次")
            mt.Rows(7).Copy()
            mt.Rows(8).Insert()
            xl.CutCopyMode = False
            mt.Cells(8, 3).Value = "2-2"
            mt.Cells(8, 4).Value = "相関図"
            kg = wb.Worksheets("構成と管理情報")
            kg.Cells(19, 3).Value = ("作図の形式：本書では Excel の図形(テキストボックス・コネクタ)で作図する。"
                                     "ZZZ-90000 へ登録できる図の形式は要確認。")
            kg.Cells(20, 3).Value = ("配置：「相関図」シートを参照。元坯:PanaCIM_LNB_確実構成図.drawio(第一層)。")
            notes = [DVAL["subtitle"], DVAL["legend1"],
                     "配置：A4 縦 1 頁。事象別の図(アンドン・稼働モニタ異常／月次再起動／異常時再起動)は "
                     "PanaCIM_LNB_確実構成図.drawio に残置。"]
            ws = build(wb, "2-2 相関図", notes)
        else:
            mt = wb.Worksheets("目次")
            mt.Rows(7).Copy()
            mt.Rows(8).Insert()
            xl.CutCopyMode = False
            mt.Cells(8, 1).Value = "2-2"
            mt.Cells(8, 2).Value = "相関図"
            mt.Cells(8, 3).Value = "2-2"
            kg = wb.Worksheets("構成と管理情報")
            kg.Cells(33, 3).Value = ("参照：「相関図」シートを参照。元坯:PanaCIM_LNB_確実構成図.drawio(第一層)。"
                                     "LNB の箱と Pana-CIM の箱の間のデータの向きは、図では引いてあるが実機で未確認。")
            kg.Cells(35, 3).Value = "作図の形式：本書では Excel の図形(テキストボックス・コネクタ)で作図する。"
            kg.Cells(36, 3).Value = "配置：「相関図」シートを参照。"
            notes = [DVAL["subtitle"], DVAL["legend1"],
                     "配置：A4 縦 1 頁。事象別の図(アンドン・稼働モニタ異常／月次再起動／異常時再起動)は "
                     "PanaCIM_LNB_確実構成図.drawio に残置。"]
            ws = build(wb, "2-3. 相関図", notes)
        wb.Save()
        n = ws.Shapes.Count
        ur = ws.UsedRange
        print(f"[{key}] 相関図シート作成: shapes={n} used={ur.Address}")
    finally:
        wb.Close(SaveChanges=False)

def run():
    pythoncom.CoInitialize()
    xl = win32com.client.DispatchEx("Excel.Application")
    xl.Visible = False; xl.DisplayAlerts = False
    try:
        for key, path in BOOKS.items():
            edit_book(xl, key, path)
    finally:
        xl.Quit()
        pythoncom.CoUninitialize()

for attempt in range(1, 4):
    try:
        run()
        print("RESULT: OK")
        break
    except Exception as e:
        print(f"retry {attempt}: {e}")
        time.sleep(2)
else:
    sys.exit(1)
