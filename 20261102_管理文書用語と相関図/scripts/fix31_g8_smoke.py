# -*- coding: utf-8 -*-
"""fix31_g8_smoke.py — 描画プリミティブの動作点検(使い捨てブック·保存しない)。
各項目について OK/FAIL と例外型のみ出力する(文書内容は扱わない)。
"""
import sys, traceback
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import win32com.client as win32

def check(label, fn):
    try:
        fn()
        print(f"OK   {label}")
        return True
    except Exception as e:
        print(f"FAIL {label}: {type(e).__name__}: {e}")
        return False

app = win32.DispatchEx("Excel.Application")
app.Visible = False
app.DisplayAlerts = False
results = {}
try:
    wb = app.Workbooks.Add()
    ws = wb.Worksheets(1)

    def t_textbox():
        sh = ws.Shapes.AddTextbox(1, 10, 10, 200, 50)
        sh.Name = "t1"
        tf = sh.TextFrame2
        tf.WordWrap = True
        tf.AutoSize = 0
        tf.MarginLeft = 1.5
        tf.VerticalAnchor = 3
        tf.HorizontalAnchor = 1
        tf.TextRange.Text = "line1\rline2"
        results["sh"] = sh; results["tf"] = tf
    results["textbox"] = check("AddTextbox + TextFrame2 基本", t_textbox)

    def t_par_call():
        results["tf"].TextRange.Paragraphs(1)
    results["par_call"] = check("TextRange2.Paragraphs(1) 直接呼び", t_par_call)

    def t_par_item():
        results["tf"].TextRange.Paragraphs.Item(1)
    results["par_item"] = check("TextRange2.Paragraphs.Item(1)", t_par_item)

    def t_par_prop_then_item():
        p = results["tf"].TextRange.Paragraphs
        p.Item(1)
    results["par_prop_item"] = check("Paragraphs 取得→Item(1)", t_par_prop_prop := (lambda: None) or t_par_prop_item)

    def t_chars():
        results["tf"].TextRange.Characters(1, 3)
    results["chars"] = check("TextRange2.Characters(1,3)", t_chars)

    def t_font2():
        r = results["tf"].TextRange.Characters(1, 3)
        f = r.Font
        f.Name = "Meiryo UI"
        f.Size = 9
        f.Bold = True
        f.Fill.ForeColor.RGB = 0x1F1F1F
    results["font2"] = check("Font2 Name/Size/Bold/Fill", t_font2)

    def t_fareast():
        import pythoncom
        f = results["tf"].TextRange.Font
        ole = f._oleobj_
        dispid = ole.GetIDsOfNames(0, "NameFarEast")
        ole.Invoke(dispid, 0, pythoncom.DISPATCH_PROPERTYPUT, False, "Meiryo UI")
    results["fareast"] = check("Font2.NameFarEast via 生Invoke", t_fareast)

    def t_fareast_dynamic():
        f = results["tf"].TextRange.Font
        d = win32com.client.dynamic.Dispatch(f._oleobj_)
        d.NameFarEast = "Meiryo UI"
    results["fareast_dyn"] = check("Font2.NameFarEast via dynamic.Dispatch", t_fareast_dynamic)

    def t_insert_after():
        tr = results["tf"].TextRange
        r2 = tr.InsertAfter("\rline3")
        results["insert_ret"] = r2
    results["insert"] = check("TextRange2.InsertAfter", t_insert_after)

    def t_shape_rrect():
        sh = ws.Shapes.AddShape(5, 100, 100, 100, 40)
        sh.Name = "r1"
        sh.Fill.ForeColor.RGB = 0xF5E6ED
        sh.Line.ForeColor.RGB = 0xA35F7B
        sh.Line.Weight = 1.5
        sh.Line.DashStyle = 1
        sh.Shadow.Visible = False
        results["rrect"] = sh
    results["rrect"] = check("AddShape 角丸+書式", t_shape_rrect)

    def t_adj_ole():
        import pythoncom
        sh = results["rrect"]
        ole = sh.Adjustments._oleobj_
        dispid = ole.GetIDsOfNames(0, "Item")
        ole.Invoke(dispid, 0, pythoncom.DISPATCH_PROPERTYPUT, False, 1, 0.12)
    results["adj_ole"] = check("Adjustments.Item へ生Invokeで設定", t_adj_ole)

    def t_adj_read():
        v = results["rrect"].Adjustments(1)
        print(f"     Adjustments(1) readback = {v}")
    results["adj_read"] = check("Adjustments(1) 読み取り", t_adj_read)

    def t_line():
        ln = ws.Shapes.AddLine(10, 200, 200, 200)
        ln.Name = "l1"
        ln.Line.ForeColor.RGB = 0x000000
        ln.Line.Weight = 1.0
        ln.Line.DashStyle = 4
        ln.Line.EndArrowheadStyle = 2
        ln.Line.EndArrowheadLength = 2
        ln.Line.EndArrowheadWidth = 2
        results["line"] = ln
    results["line"] = check("AddLine + 矢頭 + 破線", t_line)

    def t_group():
        g = ws.Shapes.Range(["t1", "r1"]).Group()
        g.Name = "g1"
        results["grp"] = g
    results["group"] = check("Shapes.Range().Group()", t_group)

    def t_can():
        sh = ws.Shapes.AddShape(13, 300, 100, 14, 18)
        sh.Name = "can1"
    results["can"] = check("AddShape msoShapeCan=13", t_can)

    def t_display():
        sh = ws.Shapes.AddShape(43, 320, 100, 18, 15)
        sh.Name = "disp1"
    results["display"] = check("AddShape msoShapeFlowchartDisplay=43", t_display)

    def t_donut_adj():
        sh = ws.Shapes.AddShape(18, 350, 100, 16, 16)
        sh.Name = "donut1"
        import pythoncom
        ole = sh.Adjustments._oleobj_
        dispid = ole.GetIDsOfNames(0, "Item")
        ole.Invoke(dispid, 0, pythoncom.DISPATCH_PROPERTYPUT, False, 1, 0.18)
    results["donut"] = check("Donut + Adjustments", t_donut_adj)

    def t_hexa():
        sh = ws.Shapes.AddShape(10, 380, 100, 18, 15)
        sh.Name = "hex1"
    results["hexa"] = check("AddShape msoShapeHexagon=10", t_hexa)

    def t_penta():
        sh = ws.Shapes.AddShape(51, 410, 100, 18, 13)
        sh.Name = "pent1"
    results["penta"] = check("AddShape msoShapeRegularPentagon=51", t_penta)

    def t_cell_fareast():
        import pythoncom
        f = ws.Range("A1").Font
        f.Name = "Meiryo UI"
        ole = f._oleobj_
        dispid = ole.GetIDsOfNames(0, "NameFarEast")
        ole.Invoke(dispid, 0, pythoncom.DISPATCH_PROPERTYPUT, False, "Meiryo UI")
        ws.Range("A1").Value = "テスト"
        ws.Rows(1).RowHeight = 15.0
    results["cellfont"] = check("セル Font + NameFarEast + 行高", t_cell_fareast)

    def t_wrap_g4():
        ws.Range("G4").WrapText = True
        ws.Range("G4").Value = "　構成と管理情報\n対象読者: テスト"
    results["g4"] = check("G4 WrapText+2行値", t_wrap_g4)

    def t_pagsetup():
        ws.PageSetup.PrintArea = "$A$1:$P$60"
        ws.Range(ws.Cells(1, 1), ws.Cells(1, 16)).Width  # 実幅の読み取り
        _ = ws.Rows(3).RowHeight
    results["pagesetup"] = check("PrintArea + Range.Width 読み取り", t_pagsetup)

    def t_export():
        import os, tempfile
        p = os.path.join(tempfile.gettempdir(), "g8_smoke_sheet.pdf")
        ws.ExportAsFixedFormat(0, p, 0, True, False)
        os.remove(p)
    results["export"] = check("ExportAsFixedFormat(シート)", t_export)

    wb.Close(SaveChanges=False)
finally:
    app.Quit()

print("SMOKE DONE")
