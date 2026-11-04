# -*- coding: utf-8 -*-
"""fix31_g8_smoke3.py — AutoSize 委譲の動作点検(使い捨てブック·保存しない)。
TextFrame2.AutoSize=1 で Excel に高さを決めさせ、読み取れることを確認する。
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import win32com.client as win32

app = win32.DispatchEx("Excel.Application")
app.Visible = False
app.DisplayAlerts = False
try:
    wb = app.Workbooks.Add()
    ws = wb.Worksheets(1)

    # 1) 固定幅·長めテキスト(2段落) → AutoSize 後の高さ/幅
    tb = ws.Shapes.AddTextbox(1, 10, 10, 160, 12)
    tb.Name = "auto1"
    tf = tb.TextFrame2
    tf.WordWrap = True
    tf.AutoSize = 1
    tf.TextRange.Text = "3行に渡るほどの長めのテキストサンプルを投入して折返させる\r2段落目は短い"
    for i, sz in ((1, 9.5), (2, 8)):
        pr = tf.TextRange.Paragraphs.Item(i)
        pr.Font.Name = "Meiryo UI"
        pr.Font.Size = sz
        pr.Font.Fill.ForeColor.RGB = 0x222222
    print("after set: H=%.1f W=%.1f" % (tb.Height, tb.Width))
    tb.Height = 10  # 縮めてから AutoSize に再計算させる
    print("shrunk then read: H=%.1f" % tb.Height)

    # 2) 短い1行 → 高さが小さくなる
    tb2 = ws.Shapes.AddTextbox(1, 10, 120, 160, 12)
    tb2.Name = "auto2"
    tf2 = tb2.TextFrame2
    tf2.WordWrap = True
    tf2.AutoSize = 1
    tf2.TextRange.Text = "短い"
    tf2.TextRange.Font.Size = 8
    print("short: H=%.1f W=%.1f" % (tb2.Height, tb2.Width))

    # 3) AutoSize 後の Top 変更が保持されるか(再計算で Top が動かないか)
    tb.Top = 50
    print("repositioned Top=%.1f H=%.1f" % (tb.Top, tb.Height))

    # 4) 凡例想定: 幅700·長文1段落下限
    tb3 = ws.Shapes.AddTextbox(1, 10, 200, 700, 12)
    tb3.Name = "auto3"
    tf3 = tb3.TextFrame2
    tf3.WordWrap = True
    tf3.AutoSize = 1
    tf3.TextRange.Text = "凡例サンプル: 短め"
    tf3.TextRange.Font.Size = 7.5
    print("legend short: H=%.1f" % tb3.Height)

    # 5) グループ化後に AutoSize 済みメンバーの高さが維持されるか
    box = ws.Shapes.AddShape(5, 10, 300, 180, 40)
    box.Name = "b1"
    tb2.Top = 310
    g = ws.Shapes.Range(["b1", "auto2"]).Group()
    g.Name = "grp1"
    m = g.GroupItems.Item(2)
    print("grouped member H=%.1f (grp H=%.1f)" % (m.Height, g.Height))

    wb.Close(SaveChanges=False)
finally:
    app.Quit()
print("SMOKE3 DONE")
