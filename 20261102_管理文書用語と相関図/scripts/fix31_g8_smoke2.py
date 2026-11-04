# -*- coding: utf-8 -*-
"""fix31_g8_smoke2.py — 第2回プリミティブ点検(使い捨てブック·保存しない)。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import win32com.client as win32
import win32com.client.dynamic
import pythoncom

def check(label, fn):
    try:
        r = fn()
        print(f"OK   {label}" + (f" -> {r}" if r is not None else ""))
        return True
    except Exception as e:
        print(f"FAIL {label}: {type(e).__name__}: {e}")
        return False

app = win32.DispatchEx("Excel.Application")
app.Visible = False
app.DisplayAlerts = False
try:
    wb = app.Workbooks.Add()
    ws = wb.Worksheets(1)

    sh = ws.Shapes.AddTextbox(1, 10, 10, 260, 80)
    sh.Name = "t1"
    tf = sh.TextFrame2
    tf.WordWrap = True
    tf.TextRange.Text = "line1\rline2\rline3"

    def t_par_fmt():
        for i, (sz, col) in enumerate(((11, 0x111111), (9, 0x222222), (7, 0x333333)), start=1):
            pr = tf.TextRange.Paragraphs.Item(i)
            f = pr.Font
            f.Name = "Meiryo UI"
            f.Size = sz
            f.Bold = (i == 1)
            f.Fill.ForeColor.RGB = col
            ole = f._oleobj_
            dispid = ole.GetIDsOfNames(0, "NameFarEast")
            ole.Invoke(dispid, 0, pythoncom.DISPATCH_PROPERTYPUT, False, "Meiryo UI")
        return tf.TextRange.Font.Size
    check("段落ごと Paragraphs.Item + Font2 書式 + NameFarEast", t_par_fmt)

    def t_chars_item():
        tr = tf.TextRange
        txt = tr.Text
        marks = [j for j, ch in enumerate(txt) if ch in "ab"]
        out = []
        for m in marks:
            chx = tr.Characters.Item(m + 1, 1)
            chx.Font.Fill.ForeColor.RGB = 0xFF0000
            out.append(chx.Text)
        return out
    check("Characters.Item で1文字着色", t_chars_item)

    def t_setadj():
        sh2 = ws.Shapes.AddShape(5, 100, 200, 120, 40)
        sh2.Name = "r2"
        ole = sh2.Adjustments._oleobj_
        dispid = ole.GetIDsOfNames(0, "Item")
        ole.Invoke(dispid, 0, pythoncom.DISPATCH_PROPERTYPUT, False, 1, 0.12)
        return sh2.Adjustments(1)
    check("set_adj 方式(GetIDsOfNames Item→PUT) 設定+読み戻し", t_setadj)

    def t_setadj_dispid0():
        sh3 = ws.Shapes.AddShape(5, 240, 200, 120, 40)
        sh3.Name = "r3"
        ole = sh3.Adjustments._oleobj_
        ole.Invoke(0, 0, pythoncom.DISPATCH_PROPERTYPUT, False, 1, 0.3)
        return sh3.Adjustments(1)
    check("set_adj 方式(dispid=0 直指定) 設定+読み戻し", t_setadj_dispid0)

    def t_cellfont_dyn():
        f = ws.Range("A1").Font
        d = win32com.client.dynamic.Dispatch(f._oleobj_)
        d.NameFarEast = "Meiryo UI"
        return d.NameFarEast
    check("セル Font.NameFarEast via dynamic.Dispatch", t_cellfont_dyn)

    def t_cellfont_getids():
        f = ws.Range("A2").Font
        ole = f._oleobj_
        for nm in ("NameFarEast", "NameFarEast ", "_NameFarEast"):
            try:
                dispid = ole.GetIDsOfNames(0, nm)
                return f"{nm} -> dispid {dispid}"
            except Exception as e:
                last = f"{nm}: {type(e).__name__}"
        return "all failed: " + last
    check("セル Font GetIDsOfNames 候補走査", t_cellfont_getids)

    def t_cellfont_name_read():
        f = ws.Range("A1").Font
        return f.Name
    check("セル Font.Name 読み", t_cellfont_name_read)

    def t_row_insert():
        ws.Rows(2).Copy()
        ws.Rows(3).Insert()
        app.CutCopyMode = False
        return ws.Rows(3).RowHeight
    check("Rows.Copy + Rows.Insert 書式複製", t_row_insert)

    def t_row_insert_copyorigin():
        ws.Rows(9).Insert(CopyOrigin=1)
        ws.Rows(9).Insert(CopyOrigin=1)
        return "inserted 2"
    check("Rows.Insert(CopyOrigin=1)", t_row_insert_copyorigin)

    def t_fpn():
        ws.PageSetup.FirstPageNumber = 17
        ws.PageSetup.PrintArea = "$A$1:$P$55"
        return ws.PageSetup.FirstPageNumber
    check("PageSetup.FirstPageNumber 設定", t_fpn)

    def t_tag_anchor():
        sh4 = ws.Shapes.AddShape(5, 300, 10, 32, 13)
        sh4.Name = "tag1"
        t = sh4.TextFrame2
        t.WordWrap = False
        t.VerticalAnchor = 3
        t.HorizontalAnchor = 2
        t.TextRange.Text = "N01"
        f = t.TextRange.Font
        f.Name = "Meiryo UI"
        f.Size = 8
        return "ok"
    check("タグ形状 + TextFrame2 アンカー", t_tag_anchor)

    wb.Close(SaveChanges=False)
finally:
    app.Quit()

print("SMOKE2 DONE")
