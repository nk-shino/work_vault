# -*- coding: utf-8 -*-
"""vendor_diagrams_build.py — PanaCIM-EE仕様説明書 2図の再編集可能Excel図形再構築(新規ファイル・ドラフト)。
対象: vendor_diagrams_panaEE.xlsx (新規・作業フォルダ内のみ)
  Sheet1 外部インターフェース構成 / Sheet2 ネットワーク構成例
内容の権威: 02_参照元/2026-10-27_PanaCIM-EE仕様説明書_優先ダイジェスト.md (A-2/A-3/F-3)
デザイン: correlation_rebuild_spec.md §7 パレット+WCAG AA / addendum2 案C′(帯見出し·8pt注記·行送り75%)
規約: 図名帯12pt太字·ノード10pt·注記8pt·出典符8pt #595959(最終文字列内)·線1pt黒(確定)/グレー破線(未確定)
     文字溢れは幅を変えず高さで吸収(fit_grow_height)·A4横1頁/図·余白8mm·認証情報の値は書かない
"""
import json, os, sys, time, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
XLSX = os.path.join(HERE, "vendor_diagrams_panaEE.xlsx")
PDF1 = os.path.join(HERE, "vendor_diagrams_s1_interface.pdf")
PDF2 = os.path.join(HERE, "vendor_diagrams_s2_network.pdf")
PNG1 = os.path.join(HERE, "vendor_diagrams_s1_interface.png")
PNG2 = os.path.join(HERE, "vendor_diagrams_s2_network.png")
RESULT = os.path.join(HERE, "vendor_diagrams_build_result.json")

out = {"ok": False, "pid": None, "sheets": {}, "fit_adjust": {}, "errors": [], "pdf": {}, "png": {}}

# ---------------- パレット (correlation_rebuild_spec.md §7 + WCAG AA) ----------------
def rgb(h):
    return int(h[4:6] + h[2:4] + h[0:2], 16)

PAL = {
    "server":    {"fill": "DEEBF7", "line": "2E75B6", "w": 1.5,  "dash": False, "shape": 5},   # 角丸長方形
    "terminal":  {"fill": "FFF2CC", "line": "BF8F00", "w": 1.5,  "dash": False, "shape": 1},
    "equipment": {"fill": "E2EFDA", "line": "538135", "w": 2.25, "dash": False, "shape": 1},
    "estimate":  {"fill": "F2F2F2", "line": "7F7F7F", "w": 1.5,  "dash": True,  "shape": 1},
    "external":  {"fill": "FFFFFF", "line": "262626", "w": 1.5,  "dash": False, "shape": 69},  # msoShapeFlowchartTerminator=ステジアム(20=Arc誤り)
    "band":      {"fill": None,     "line": "BFBFBF", "w": 0.75, "dash": False, "shape": 1},   # 帯本体 塗なし
    "bandhead":  {"fill": "404040", "line": None,     "w": 1.0,  "dash": False, "shape": 1},   # 帯見出し 白文字
    "note":      {"fill": "FFFFFF", "line": "808080", "w": 0.75, "dash": False, "shape": 1},
    "auxdash":   {"fill": None,     "line": "BFBFBF", "w": 0.75, "dash": True,  "shape": 1},
}

FONT = "Meiryo UI"

# ---------------- 文字列(ダイジェスト/仕様タスクの文言どおり·手入力はここに集約) ----------------
T_TAG_S1_FULL = "〔T1:PanaCIM-EE仕様説明書 A680-004624(00)·印刷-1-/-2-·印刷-43-〕"
T_TAG_S1_P49  = "〔T1:印刷-43-〕"
T_TAG_S1_P78  = "〔T1:印刷-1-/-2-〕"
T_TAG_S1_P11  = "〔T1:印刷-5-〕"
T_TAG_S2_FULL = "〔T1:PanaCIM-EE仕様説明書 A680-004624(00)·印刷-9-/-10-〕"
T_TAG_S2      = "〔T1:印刷-9-/-10-〕"

NOTE_S1 = ("※ベンダー仕様書の機能構成例。現場の実装(転送先・頻度・有効化状態)は本図で確定しない。\r"
           "※本図の転載は利用許諾範囲の確認が必要(ダイジェストE-2 #10)。\r"
           "※外部I/Fは元図(p.49)ではシステム枠右縁に跨る表現。本図では枠内に配置し接続線で境界への接続を示す。\r"
           + T_TAG_S1_FULL)
NOTE_S2 = ("※仕様書の構成例。現場のIP・配線・設置位置を確定しない。複数網への接続からルーティング機能やデータ転送方向を推定しない。\r"
           "※本図の転載は利用許諾範囲の確認が必要(ダイジェストE-2 #10)。\r" + T_TAG_S2_FULL)

# ---------------- COM ----------------
import win32com.client
import win32process

xl = win32com.client.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
out["pid"] = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
print("EXCEL PID", out["pid"], flush=True)

try:
    # ---- 新規ブック·シート2枚 ----
    wb = xl.Workbooks.Add()
    while wb.Sheets.Count < 2:
        wb.Sheets.Add()
    while wb.Sheets.Count > 2:
        wb.Sheets(wb.Sheets.Count).Delete()
    ws1 = wb.Worksheets(1)
    ws2 = wb.Worksheets(2)
    ws1.Name = "外部インターフェース構成"
    ws2.Name = "ネットワーク構成例"
    X0 = 0.0
    Y0 = 0.0

    def add_shape(ws, name, x, y, w, h, kind):
        p = PAL[kind]
        shp = ws.Shapes.AddShape(p["shape"], X0 + x, Y0 + y, w, h)
        shp.Name = name
        if p["fill"] is None:
            shp.Fill.Visible = 0
        else:
            shp.Fill.ForeColor.RGB = rgb(p["fill"])
        if p["line"] is None:
            shp.Line.Visible = 0
        else:
            shp.Line.ForeColor.RGB = rgb(p["line"])
            shp.Line.Weight = p["w"]
        shp.Line.DashStyle = 4 if p["dash"] else 1
        tf = shp.TextFrame2
        tf.WordWrap = -1
        tf.AutoSize = 0
        tf.MarginLeft = 2; tf.MarginRight = 2; tf.MarginTop = 1; tf.MarginBottom = 1
        tf.VerticalAnchor = 3
        return shp

    def add_line(ws, name, x1, y1, x2, y2, confirmed=True, arrow=False):
        ln = ws.Shapes.AddLine(X0 + x1, Y0 + y1, X0 + x2, Y0 + y2)
        ln.Name = name
        ln.Line.ForeColor.RGB = rgb("000000") if confirmed else rgb("7F7F7F")
        ln.Line.Weight = 1.0
        ln.Line.DashStyle = 1 if confirmed else 4
        if arrow:
            ln.Line.EndArrowheadStyle = 2  # msoArrowheadTriangle=塗り三角(実測: 1=None/2=塗り三角/6=楕円点)
            ln.Line.EndArrowheadLength = 2  # msoArrowheadLengthMedium
            ln.Line.EndArrowheadWidth = 2   # msoArrowheadWidthMedium
        return ln

    def line_spacing_pts(size):
        """行送り75%相当の SpaceWithin ポイント値(addendum2 §4·probe_linespace 実測)。
        LineRuleWithin=-1(比率)では SpaceWithin が無効化され行間が潰れるため
        先に LineRuleWithin=0(ポイント)へ切替してから設定する。"""
        return {12: 14.9, 10: 12.4, 8: 10.3}.get(int(size), round(size * 1.2375, 2))

    def style_text(tf, size, color="1F1F1F", bold=False, anchor=3):
        rng = tf.TextRange
        rng.Font.NameFarEast = FONT
        rng.Font.Name = FONT
        rng.Font.Size = size
        rng.Font.Fill.ForeColor.RGB = rgb(color)
        rng.Font.Bold = -1 if bold else 0
        pf = rng.ParagraphFormat
        pf.LineRuleWithin = 0                    # 先にポイント指定へ切替(順序重要)
        pf.SpaceWithin = line_spacing_pts(size)  # 行送り75%相当(実測 12→14.9/10→12.4/8→10.3pt)
        pf.SpaceBefore = 0; pf.SpaceAfter = 0
        tf.VerticalAnchor = anchor

    def style_chars(shp, start, length, size=None, color=None, bold=None):
        """文字単位の書式設定(動的ディスパッチでは classic TextFrame.Characters のみ動作確認済み)"""
        if length <= 0:
            return
        ch = shp.TextFrame.Characters(start, length)
        if size is not None:
            ch.Font.Size = size
        if color is not None:
            ch.Font.Color = rgb(color)
        if bold is not None:
            ch.Font.Bold = bold

    def style_tail_tag(shp, main_len):
        """末尾の出典符を8pt #595959 へ(最終文字列内·案C′/spec §3)"""
        txt = shp.TextFrame2.TextRange.Text
        if len(txt) <= main_len:
            return
        style_chars(shp, main_len + 1, len(txt) - main_len, size=8, color="595959", bold=False)

    def set_text2(shp, line1, line2=None, size1=10, size2=8, c1="1F1F1F", c2="595959",
                  bold1=False, anchor=3):
        """1行目【区分】名称(size1)/2行目以降 備考·IP(size2·グレー)。"""
        txt = line1 if line2 is None else line1 + "\r" + line2
        shp.TextFrame2.TextRange.Text = txt
        style_text(shp.TextFrame2, size1, c1, bold=bold1, anchor=anchor)
        if line2:
            style_chars(shp, len(line1) + 2, len(line2), size=size2, color=c2, bold=False)

    def fit_grow_height(shp, key):
        """文字溢れは高さで吸収(幅は変えない)— addendum2 §5 ゲート2の高さ版"""
        tf = shp.TextFrame2
        for _ in range(6):
            bh = tf.TextRange.BoundHeight
            h = shp.Height
            if bh <= h - 2:
                return True
            grow = (bh - (h - 2)) + 2
            shp.Height = h + grow
        return tf.TextRange.BoundHeight <= shp.Height - 2

    def rec(ws, shapes, shp, key, fit):
        shapes[key] = {"name": shp.Name, "l": round(shp.Left - X0, 1), "t": round(shp.Top - Y0, 1),
                       "w": round(shp.Width, 1), "h": round(shp.Height, 1), "fit": fit}
        if not fit:
            out["fit_adjust"][key] = shapes[key]["h"]

    def setup_print(ws, max_x, max_y):
        cw = ws.Columns(1).Width   # pt
        rh = ws.Rows(1).RowHeight  # pt
        ncol = int(max_x / cw) + 2
        nrow = int(max_y / rh) + 2
        if ncol > 60: ncol = 60
        if nrow > 90: nrow = 90
        addr = ws.Range(ws.Cells(1, 1), ws.Cells(nrow, ncol)).Address
        ps = ws.PageSetup
        ps.PrintArea = addr
        ps.Orientation = 2      # xlLandscape
        ps.PaperSize = 9        # xlPaperA4
        ps.Zoom = False
        ps.FitToPagesWide = 1
        ps.FitToPagesTall = 1
        m = 8 / 25.4 * 72.0     # 8mm
        ps.LeftMargin = m; ps.RightMargin = m; ps.TopMargin = m; ps.BottomMargin = m
        ps.HeaderMargin = 4 / 25.4 * 72.0; ps.FooterMargin = 4 / 25.4 * 72.0
        ps.CenterHorizontally = True
        return {"print_area": addr, "col_pt": round(cw, 2), "row_pt": round(rh, 2),
                "orientation": ps.Orientation, "paper": ps.PaperSize,
                "fit_w": ps.FitToPagesWide, "fit_h": ps.FitToPagesTall}

    # ================================================================
    # Sheet1 外部インターフェース構成
    # ================================================================
    s1 = {}
    shp = add_shape(ws1, "s1_title", 0, 0, 790, 44, "bandhead")
    t1 = "外部インターフェース構成"
    t2 = "PanaCIM-EEの機能構成と外部出力 — ベンダー仕様書の構成例をExcel図形で再構築"
    shp.TextFrame2.TextRange.Text = t1 + "\r" + t2
    style_text(shp.TextFrame2, 12, "FFFFFF", bold=True, anchor=3)
    style_chars(shp, len(t1) + 2, len(t2), size=10, color="D9D9D9", bold=False)
    rec(ws1, s1, shp, "s1_title", True)

    # コンテナ PanaCIM-EEシステム
    shp = add_shape(ws1, "s1_container", 250, 130, 320, 210, "server")
    shp.Line.Weight = 2.25
    set_text2(shp, "PanaCIM-EEシステム", T_TAG_S1_P78, anchor=1)
    rec(ws1, s1, shp, "s1_container", fit_grow_height(shp, "s1_container"))

    # モジュール小箱4 (【機能】·ダイジェストB/A-2·p.49図)
    mods = [
        ("s1_mod_zairyo", 262, 178, 140, 44, "【機能】材料管理(基本)"),
        ("s1_mod_trace", 410, 178, 128, 44, "【機能】トレーサビリティー"),
        ("s1_mod_kado", 262, 230, 140, 44, "【機能】稼働分析"),
        ("s1_mod_shogo", 410, 230, 128, 44, "【機能】材料照合"),
    ]
    for nm, x, y, w, h, t1 in mods:
        shp = add_shape(ws1, nm, x, y, w, h, "server")
        set_text2(shp, t1)
        rec(ws1, s1, shp, nm, fit_grow_height(shp, nm))

    # 外部インターフェース(ユーザー決定2026-10-28: システム枠の内側へ完全に収める·右縁から6pt内側)
    shp = add_shape(ws1, "s1_extif", 434, 284, 130, 44, "server")
    shp.Line.Weight = 2.25
    set_text2(shp, "【機能】外部インターフェース")
    rec(ws1, s1, shp, "s1_extif", fit_grow_height(shp, "s1_extif"))

    # 実装機(設備)
    shp = add_shape(ws1, "s1_jisso", 10, 233, 100, 44, "equipment")
    set_text2(shp, "【設備】実装機")
    rec(ws1, s1, shp, "s1_jisso", fit_grow_height(shp, "s1_jisso"))

    # 無線スキャナー(端末)
    shp = add_shape(ws1, "s1_musen", 430, 396, 130, 36, "terminal")
    set_text2(shp, "【端末】無線スキャナー")
    rec(ws1, s1, shp, "s1_musen", fit_grow_height(shp, "s1_musen"))

    # Webクライアント(補助箱·A-2 p.11)
    shp = add_shape(ws1, "s1_web", 300, 60, 140, 40, "terminal")
    set_text2(shp, "【端末】Webクライアント")
    rec(ws1, s1, shp, "s1_web", fit_grow_height(shp, "s1_web"))

    # 外部出力先3種(白ステジアム)
    outs = [
        ("s1_out_xml", 690, 140, 100, 40, "【外部】XMLファイル"),
        ("s1_out_socket", 690, 205, 100, 66, "【外部】Socketインターフェース(外部アプリケーション)"),
        ("s1_out_db", 690, 300, 100, 40, "【外部】外部データベース"),
    ]
    for nm, x, y, w, h, t1 in outs:
        shp = add_shape(ws1, nm, x, y, w, h, "external")
        set_text2(shp, t1)
        rec(ws1, s1, shp, nm, fit_grow_height(shp, nm))

    # 接続線(1pt黒·確定·矢頭=向き確定)
    add_line(ws1, "s1_ln_data", 110, 255, 250, 255, confirmed=True, arrow=True)
    # 無線スキャナー→材料照合: 外部I/F箱(434,284〜)を避ける経路へ再ルート(ユーザー決定2026-10-28)
    add_line(ws1, "s1_ln_musen", 435, 396, 423, 274, confirmed=True, arrow=True)
    add_line(ws1, "s1_ln_web", 370, 100, 370, 130, confirmed=True, arrow=True)
    # 外部I/F右縁(564)から出力先3種へ延長(枠内配置に伴う再ルート·ユーザー決定2026-10-28)
    add_line(ws1, "s1_ln_fan1", 564, 296, 690, 160, confirmed=True, arrow=True)
    add_line(ws1, "s1_ln_fan2", 564, 306, 690, 238, confirmed=True, arrow=True)
    add_line(ws1, "s1_ln_fan3", 564, 316, 690, 318, confirmed=True, arrow=True)

    # ラベル(線と独立·末尾に出典符8pt #595959)
    shp = add_shape(ws1, "s1_lbl_data", 112, 190, 136, 52, "note")
    t_main = "トレーサビリティーデータ\r設備ステータスデータ\r稼働実績データ"
    shp.TextFrame2.TextRange.Text = t_main + T_TAG_S1_P49
    style_text(shp.TextFrame2, 10, "262626")
    style_tail_tag(shp, len(t_main))
    rec(ws1, s1, shp, "s1_lbl_data", fit_grow_height(shp, "s1_lbl_data"))

    shp = add_shape(ws1, "s1_lbl_musen", 507, 344, 150, 32, "note")
    t_main = "アクセスポイント経由·無線"
    shp.TextFrame2.TextRange.Text = t_main + "\r" + T_TAG_S1_P49  # 出典符は独立行(行末折返しで分断されないように)
    style_text(shp.TextFrame2, 10, "262626")
    style_tail_tag(shp, len(t_main))
    rec(ws1, s1, shp, "s1_lbl_musen", fit_grow_height(shp, "s1_lbl_musen"))

    shp = add_shape(ws1, "s1_lbl_web", 380, 100, 175, 26, "note")
    t_main = "グラフ/レポート参照"
    shp.TextFrame2.TextRange.Text = t_main + T_TAG_S1_P11
    style_text(shp.TextFrame2, 10, "262626")
    style_tail_tag(shp, len(t_main))
    rec(ws1, s1, shp, "s1_lbl_web", fit_grow_height(shp, "s1_lbl_web"))

    # 出力可否表(小表·p.49·ダイジェストA-3の値どおり)
    shp = add_shape(ws1, "s1_tblcap", 10, 346, 246, 14, "note")
    t_main = "出力可否表(外部出力形式の制約)"
    shp.TextFrame2.TextRange.Text = t_main + T_TAG_S1_P49
    shp.Line.Visible = 0
    shp.Fill.Visible = 0
    style_text(shp.TextFrame2, 8, "404040", bold=True)
    style_tail_tag(shp, len(t_main))
    rec(ws1, s1, shp, "s1_tblcap", True)

    tbl_cols = [100, 42, 52, 52]
    tbl_rows = ["トレーサビリティー", "設備ステータス", "材料照合", "スクラップデータ", "生産基板データ"]
    tbl_marks = [["○", "○", "○"], ["○", "×", "×"], ["○", "×", "×"], ["○", "×", "×"], ["○", "×", "×"]]
    hdr = ["データカテゴリ", "XML", "DB(SQL)", "ソケット"]
    gx, gy, rh_ = 10, 362, 18
    for c in range(4):
        x = gx + sum(tbl_cols[:c])
        shp = add_shape(ws1, "s1_tbl_r0c%d" % c, x, gy, tbl_cols[c], rh_, "note")
        shp.TextFrame2.TextRange.Text = hdr[c]
        style_text(shp.TextFrame2, 8, "FFFFFF", bold=True)
        shp.TextFrame2.TextRange.ParagraphFormat.Alignment = 2 if c else 1
        shp.Fill.ForeColor.RGB = rgb("404040")
        shp.Line.ForeColor.RGB = rgb("BFBFBF"); shp.Line.Weight = 0.75
        rec(ws1, s1, shp, "s1_tbl_r0c%d" % c, True)
    for r in range(1, 6):
        for c in range(4):
            x = gx + sum(tbl_cols[:c])
            y = gy + rh_ * r
            shp = add_shape(ws1, "s1_tbl_r%dc%d" % (r, c), x, y, tbl_cols[c], rh_, "note")
            shp.TextFrame2.TextRange.Text = tbl_rows[r - 1] if c == 0 else tbl_marks[r - 1][c - 1]
            style_text(shp.TextFrame2, 8, "1F1F1F")
            shp.TextFrame2.TextRange.ParagraphFormat.Alignment = 2 if c else 1
            shp.Line.ForeColor.RGB = rgb("BFBFBF"); shp.Line.Weight = 0.75
            rec(ws1, s1, shp, "s1_tbl_r%dc%d" % (r, c), True)

    # 凡例(シート1)
    shp = add_shape(ws1, "s1_leg_panel", 270, 362, 150, 112, "note")
    shp.Line.ForeColor.RGB = rgb("BFBFBF")
    rec(ws1, s1, shp, "s1_leg_panel", True)
    shp = add_shape(ws1, "s1_leg_title", 276, 366, 138, 14, "note")
    shp.Line.Visible = 0; shp.Fill.Visible = 0
    shp.TextFrame2.TextRange.Text = "凡例"
    style_text(shp.TextFrame2, 8, "404040", bold=True)
    rec(ws1, s1, shp, "s1_leg_title", True)
    leg1 = [
        ("s1_leg_sw1", "server",    "青角丸=システム/モジュール"),
        ("s1_leg_sw2", "terminal",  "黄=端末(スキャナー/Web)"),
        ("s1_leg_sw3", "equipment", "緑太枠=設備(実装機)"),
        ("s1_leg_sw4", "external",  "白ステジアム=外部出力先"),
        ("s1_leg_sw5", None,        "黒実線矢=データフロー(確定)"),
    ]
    ly = 382
    for nm, kind, txt in leg1:
        if kind:
            sw = add_shape(ws1, nm, 276, ly + 2, 16, 11, kind)
            sw.TextFrame2.TextRange.Text = ""
            rec(ws1, s1, sw, nm, True)
        else:
            ln = add_line(ws1, nm + "_ln", 276, ly + 8, 292, ly + 8, confirmed=True, arrow=False)
            rec(ws1, s1, ln, nm + "_ln", True)
        shp = add_shape(ws1, nm + "_tx", 296, ly, 120, 16, "note")
        shp.Line.Visible = 0; shp.Fill.Visible = 0
        shp.TextFrame2.TextRange.Text = txt
        style_text(shp.TextFrame2, 8, "262626")
        rec(ws1, s1, shp, nm + "_tx", fit_grow_height(shp, nm + "_tx"))
        ly += 18

    # 注記(必須)
    shp = add_shape(ws1, "s1_note", 0, 480, 790, 48, "note")
    shp.TextFrame2.TextRange.Text = NOTE_S1
    style_text(shp.TextFrame2, 8, "404040", anchor=1)
    n_main = NOTE_S1.rfind("\r")
    style_chars(shp, n_main + 2, len(NOTE_S1) - n_main - 1, color="595959")
    rec(ws1, s1, shp, "s1_note", fit_grow_height(shp, "s1_note"))

    out["sheets"]["外部インターフェース構成"] = s1
    pr1 = setup_print(ws1, 800, 535)
    out.setdefault("print", {})["外部インターフェース構成"] = pr1

    # ================================================================
    # Sheet2 ネットワーク構成例
    # ================================================================
    s2 = {}
    shp = add_shape(ws2, "s2_title", 0, 0, 790, 44, "bandhead")
    t1 = "ネットワーク構成例"
    t2 = "PanaCIMのネットワーク構成例 — ベンダー仕様書掲載の例をExcel図形で再構築"
    shp.TextFrame2.TextRange.Text = t1 + "\r" + t2
    style_text(shp.TextFrame2, 12, "FFFFFF", bold=True, anchor=3)
    style_chars(shp, len(t1) + 2, len(t2), size=10, color="D9D9D9", bold=False)
    rec(ws2, s2, shp, "s2_title", True)

    # ライン別ネットワーク(内部網)の帯(ユーザー決定2026-10-28) — レーン/箱の背面に先に作成。
    # F-3にIP帯の記載がないため要確認ラベル付き。既存の内部網要素(LNB=設備側192.168.20.25·
    # NPM-DGS=装置側内部網DHCP)を含む範囲とし、PanaCIMサーバー(上位網·要確認)や
    # 外部網のノードとは重ならない位置に引く。帯の上端/左端/右端は上位網レーン(zone2)の
    # 枠線と一致させ、下端はLNB底辺(y=196)に一致 — 新たに見える線は下端の1本のみ。
    shp = add_shape(ws2, "s2_band_naibu", 0, 124, 560, 72, "band")
    rec(ws2, s2, shp, "s2_band_naibu", True)
    # 帯見出し: 既存の暗色帯見出し(260x32)は帯範囲内のNPM-DGS·zone2見出しと衝突するため、
    # 既存の小ラベル様式(8pt #595959·枠/塗なし)で帯見出し直下の空き領域に配置する。
    shp = add_shape(ws2, "s2_band_naibu_lbl", 152, 160, 113, 36, "note")
    shp.Line.Visible = 0; shp.Fill.Visible = 0
    shp.TextFrame2.TextRange.Text = "ライン別ネットワーク\r(内部網) — IP帯: 要確認\r(F-3に記載なし)"
    style_text(shp.TextFrame2, 8, "595959")
    rec(ws2, s2, shp, "s2_band_naibu_lbl", fit_grow_height(shp, "s2_band_naibu_lbl"))

    # 4網ゾーン(F-3に帯の明記がある4網のみ·帯本体=塗なし+BFBFBF)
    zones = [
        ("s2_zone1", 0, 54, 560, 70,  "お客様とのI/Fネットワーク", "192.168.60.xx — F-3: iLNB お客様基幹網"),
        ("s2_zone2", 0, 124, 560, 124, "パナソニック上位ネットワーク", "192.168.30.xx — F-3: 上位網·LNB上位側"),
        ("s2_zone3", 0, 248, 560, 80, "他社設備用ネットワーク", "192.168.40.xx — F-3: 他社設備File I/F網"),
        ("s2_zone4", 0, 328, 560, 80, "PLC制御ネットワーク", "192.168.50.xx — F-3: PLC制御I/F網"),
    ]
    for nm, x, y, w, h, t1, t2 in zones:
        shp = add_shape(ws2, nm, x, y, w, h, "band")
        rec(ws2, s2, shp, nm, True)
        hd = add_shape(ws2, nm + "_head", x, y, 260, 32, "bandhead")
        hd.TextFrame2.TextRange.Text = t1 + "\r" + t2
        style_text(hd.TextFrame2, 12, "FFFFFF", bold=True, anchor=3)
        style_chars(hd, len(t1) + 2, len(t2), size=10, color="D9D9D9", bold=False)
        rec(ws2, s2, hd, nm + "_head", fit_grow_height(hd, nm + "_head"))

    # レーン1補足注記
    shp = add_shape(ws2, "s2_note1", 430, 84, 125, 16, "note")
    shp.Line.Visible = 0; shp.Fill.Visible = 0
    shp.TextFrame2.TextRange.Text = "※F-3記載の機器のみ図示"
    style_text(shp.TextFrame2, 8, "595959")
    rec(ws2, s2, shp, "s2_note1", fit_grow_height(shp, "s2_note1"))

    # ノード(F-3記載分のみ)
    shp = add_shape(ws2, "s2_ilnb", 270, 62, 150, 262, "equipment")
    t2nd = ("お客様基幹網 192.168.60.xx\r上位網 192.168.30.xx\r"
            "他社設備File I/F網 192.168.40.xx\rPLC制御I/F網 192.168.50.xxを含む例は4網\r" + T_TAG_S2)
    set_text2(shp, "【設備】iLNB", t2nd)
    rec(ws2, s2, shp, "s2_ilnb", fit_grow_height(shp, "s2_ilnb"))

    shp = add_shape(ws2, "s2_npmdgs", 10, 162, 140, 48, "server")
    set_text2(shp, "【サーバ】NPM-DGS",
              "上位網接続·サーバーエリア配置(構成例)\r装置側内部網はDHCP表記")
    rec(ws2, s2, shp, "s2_npmdgs", fit_grow_height(shp, "s2_npmdgs"))

    shp = add_shape(ws2, "s2_lnb", 430, 134, 128, 62, "equipment")
    set_text2(shp, "【設備】LNB(FAパソコン)",
              "上位側 192.168.30.xx\r設備側 192.168.20.25\r(2網接続·デュアルホーム)")
    rec(ws2, s2, shp, "s2_lnb", fit_grow_height(shp, "s2_lnb"))

    shp = add_shape(ws2, "s2_panasv", 430, 200, 128, 44, "estimate")
    set_text2(shp, "【サーバ(配置例)】PanaCIMサーバー", "192.168.30.xx(上位網·要確認)")
    rec(ws2, s2, shp, "s2_panasv", fit_grow_height(shp, "s2_panasv"))

    shp = add_shape(ws2, "s2_nip", 10, 282, 130, 44, "terminal")
    set_text2(shp, "【端末】NIP(APC用PC)", "192.168.40.xx")
    rec(ws2, s2, shp, "s2_nip", fit_grow_height(shp, "s2_nip"))

    shp = add_shape(ws2, "s2_plcpc", 10, 362, 130, 44, "terminal")
    set_text2(shp, "【端末】PLC制御PC", "192.168.50.xx")
    rec(ws2, s2, shp, "s2_plcpc", fit_grow_height(shp, "s2_plcpc"))

    # 帯割当の記載なしエリア(修理ステーション·F-3に帯対応の記載なし)
    shp = add_shape(ws2, "s2_aux", 0, 408, 560, 54, "auxdash")
    rec(ws2, s2, shp, "s2_aux", True)
    shp = add_shape(ws2, "s2_auxlbl", 10, 412, 240, 16, "note")
    shp.Line.Visible = 0; shp.Fill.Visible = 0
    shp.TextFrame2.TextRange.Text = "帯割当の記載なし(F-3)の機器"
    style_text(shp.TextFrame2, 8, "595959", bold=True)
    rec(ws2, s2, shp, "s2_auxlbl", True)
    shp = add_shape(ws2, "s2_shuri", 270, 416, 150, 42, "terminal")
    set_text2(shp, "【端末】修理ステーション", "192.168.70.xx")
    rec(ws2, s2, shp, "s2_shuri", fit_grow_height(shp, "s2_shuri"))

    # 接続線: iLNB→PLC制御I/F網(4網接続の例·グレー破線=例として確定しない要素)
    add_line(ws2, "s2_ln_stub", 345, 324, 345, 350, confirmed=False, arrow=False)
    shp = add_shape(ws2, "s2_lbl_stub", 355, 326, 190, 34, "note")
    t_main = "PLC制御I/F網192.168.50.xxを含む例では4網接続"
    shp.TextFrame2.TextRange.Text = t_main + T_TAG_S2
    style_text(shp.TextFrame2, 8, "262626")
    style_tail_tag(shp, len(t_main))
    rec(ws2, s2, shp, "s2_lbl_stub", fit_grow_height(shp, "s2_lbl_stub"))

    # 凡例パネル(5種はF-3記載の名称どおり·帯はF-3に明記のある対応のみ)
    shp = add_shape(ws2, "s2_leg_panel", 570, 54, 220, 248, "note")
    shp.Line.ForeColor.RGB = rgb("BFBFBF")
    rec(ws2, s2, shp, "s2_leg_panel", True)
    shp = add_shape(ws2, "s2_leg_title", 578, 60, 204, 16, "note")
    shp.Line.Visible = 0; shp.Fill.Visible = 0
    shp.TextFrame2.TextRange.Text = "凡例 — ネットワークの読み方"
    style_text(shp.TextFrame2, 10, "404040", bold=True)
    rec(ws2, s2, shp, "s2_leg_title", True)
    leg2 = [
        ("s2_leg_n1", False, "お客様とのI/Fネットワーク", "帯 192.168.60.xx — F-3: お客様基幹網"),
        ("s2_leg_n2", False, "パナソニック上位ネットワーク", "帯 192.168.30.xx — F-3: 上位網"),
        ("s2_leg_n3", False, "パナソニックライン別ネットワーク(内部網)", "IP帯: 要確認(F-3に記載なし)"),
        ("s2_leg_n4", False, "他社設備用ネットワーク", "帯 192.168.40.xx — F-3: 他社設備File I/F網"),
        ("s2_leg_n5", False, "PLC制御ネットワーク", "帯 192.168.50.xx — F-3: PLC制御I/F網"),
    ]
    ly = 82
    for nm, dashed, t1, t2 in leg2:
        sw = add_shape(ws2, nm + "_sw", 578, ly + 4, 18, 12, "auxdash" if dashed else "band")
        if dashed:
            sw.Line.ForeColor.RGB = rgb("7F7F7F")
        sw.TextFrame2.TextRange.Text = ""
        rec(ws2, s2, sw, nm + "_sw", True)
        shp = add_shape(ws2, nm + "_tx", 602, ly, 180, 30, "note")
        shp.Line.Visible = 0; shp.Fill.Visible = 0
        shp.TextFrame2.TextRange.Text = t1 + "\r" + t2
        style_text(shp.TextFrame2, 8, "262626")
        style_chars(shp, len(t1) + 2, len(t2), color="595959")
        rec(ws2, s2, shp, nm + "_tx", fit_grow_height(shp, nm + "_tx"))
        ly += 34
    shp = add_shape(ws2, "s2_leg_key", 578, 252, 204, 44, "note")
    shp.Line.Visible = 0; shp.Fill.Visible = 0
    shp.TextFrame2.TextRange.Text = ("実線枠=F-3記載の機器(構成例)\r灰破線枠=配置例(要確認)\r"
                                     "帯配置=当該ネットワークへの接続\r灰破線=帯配置によらない接続例")
    style_text(shp.TextFrame2, 8, "404040")
    rec(ws2, s2, shp, "s2_leg_key", fit_grow_height(shp, "s2_leg_key"))
    shp = add_shape(ws2, "s2_leg_note", 570, 310, 220, 48, "note")
    shp.TextFrame2.TextRange.Text = ("※帯(IP帯)はF-3のiLNB接続記載による対応表示。"
                                     "ライン別ネットワーク(内部網)の帯はIP帯がF-3に記載がないため"
                                     "要確認ラベル付きで追加(ユーザー決定2026-10-28)。")
    style_text(shp.TextFrame2, 8, "595959", anchor=1)
    rec(ws2, s2, shp, "s2_leg_note", fit_grow_height(shp, "s2_leg_note"))

    # 注記(必須·F-3適用範囲)
    shp = add_shape(ws2, "s2_note", 0, 474, 790, 48, "note")
    shp.TextFrame2.TextRange.Text = NOTE_S2
    style_text(shp.TextFrame2, 8, "404040", anchor=1)
    n_main = NOTE_S2.rfind("\r")
    style_chars(shp, n_main + 2, len(NOTE_S2) - n_main - 1, color="595959")
    rec(ws2, s2, shp, "s2_note", fit_grow_height(shp, "s2_note"))

    out["sheets"]["ネットワーク構成例"] = s2
    pr2 = setup_print(ws2, 800, 530)
    out.setdefault("print", {})["ネットワーク構成例"] = pr2

    # ---- 保存·PDF出力 ----
    if os.path.exists(XLSX):
        os.remove(XLSX)
    wb.SaveAs(XLSX, 51)  # xlOpenXMLWorkbook
    out["xlsx"] = XLSX
    wb.Close(False)

    # PDF出力(改めて開いて各シートの印刷範囲をExportAsFixedFormat·省略可能引数は位置引数)
    wb2 = xl.Workbooks.Open(XLSX, 0, True)
    wb2.Worksheets(1).ExportAsFixedFormat(0, PDF1, 0, True, False, 1, 1, False)
    wb2.Worksheets(2).ExportAsFixedFormat(0, PDF2, 0, True, False, 1, 1, False)
    wb2.Close(False)
    out["pdf"] = {"外部インターフェース構成": PDF1, "ネットワーク構成例": PDF2}
    out["ok"] = True

finally:
    try:
        xl.Quit()
    except Exception as e:
        out["errors"].append("quit:" + repr(e)[:120])
    time.sleep(2)
    try:
        chk = subprocess.run(["tasklist", "/FI", "PID eq %d" % out["pid"]],
                             capture_output=True, text=True)
        if "EXCEL" in chk.stdout.upper():
            subprocess.run(["powershell", "-NoProfile", "-Command",
                            "Stop-Process -Id %d -Force" % out["pid"]], capture_output=True)
            out["errors"].append("stopped residual EXCEL PID %d (Stop-Process -Id)" % out["pid"])
    except Exception as e:
        out["errors"].append("cleanup:" + repr(e)[:120])

# ---- PNGレンダ(確認用·PyMuPDF) ----
try:
    import fitz
    for pdf, png, key in ((PDF1, PNG1, "外部インターフェース構成"),
                          (PDF2, PNG2, "ネットワーク構成例")):
        doc = fitz.open(pdf)
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        pix.save(png)
        out["png"][key] = {"png": png, "pages": doc.page_count, "size": [pix.width, pix.height]}
        doc.close()
except Exception as e:
    out["errors"].append("png:" + repr(e)[:160])

with open(RESULT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("ok:", out["ok"])
for k, v in out["sheets"].items():
    print(k, "shapes:", len(v))
print("fit_adjust:", out["fit_adjust"])
print("errors:", out["errors"])
