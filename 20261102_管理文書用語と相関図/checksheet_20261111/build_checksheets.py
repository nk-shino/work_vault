# -*- coding: utf-8 -*-
"""週次・月次・年次のチェックシートを既存ブックの作業コピーに生成する。

使い方:
  python build_checksheets.py pana
  python build_checksheets.py lnb
  python build_checksheets.py pana lnb
"""
import json
import math
import shutil
import sys
from pathlib import Path

import fitz
import win32com.client as win32

ROOT = Path(__file__).resolve().parent
WORK = ROOT / "work"
RENDER = ROOT / "render"
ITEMS = json.loads((ROOT / "items.json").read_text(encoding="utf-8"))

XL_THIN = 2
XL_MEDIUM = -4138
XL_CENTER = -4108
XL_LEFT = -4131
XL_TOP = -4160
XL_LANDSCAPE = 2
XL_A4 = 9
XL_CONTINUOUS = 1
XL_NONE = -4142


def rgb(r, g, b):
    return r + g * 256 + b * 65536


HEADER_FILL = rgb(217, 225, 242)
SECTION_FILL = rgb(31, 78, 121)
WHITE = rgb(255, 255, 255)


def colname(n):
    s = ""
    while n > 0:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def text_units(text):
    """Excelの列幅(半角0基準)に換算した文字幅。全角は2、半角は1。"""
    return sum(2 if ord(ch) > 127 else 1 for ch in str(text))


def wrapped_lines(text, width):
    """列幅widthで折り返したときの行数。改行も考慮する。"""
    lines = 0
    for para in str(text).split("\n"):
        lines += max(1, math.ceil(text_units(para) / max(width, 1)))
    return max(lines, 1)


def item_row_height(item):
    """点検項目・確認方法・判定基準・備考の最大行数から行高を決める。"""
    text, _principle, method, criterion, _evidence, note = item
    lines = max(
        wrapped_lines(text, 34),
        wrapped_lines(method, 27),
        wrapped_lines(criterion, 24),
        wrapped_lines(note, 16),
    )
    return max(42, lines * 13.5 + 10)


def set_range(ws, addr, value=None, *, font=None, size=None, bold=None,
              fill=None, color=None, halign=None, valign=XL_TOP, wrap=None,
              border=None, border_color=None, indent=None):
    r = ws.Range(addr)
    if value is not None:
        r.Value = value
    if font is not None:
        r.Font.Name = font
    if size is not None:
        r.Font.Size = size
    if bold is not None:
        r.Font.Bold = bold
    if fill is not None:
        r.Interior.Color = fill
    if color is not None:
        r.Font.Color = color
    if halign is not None:
        r.HorizontalAlignment = halign
    if valign is not None:
        r.VerticalAlignment = valign
    if wrap is not None:
        r.WrapText = wrap
    if indent is not None:
        r.IndentLevel = indent
    if border is not None:
        for i in range(7, 13):  # xlEdgeLeft..xlInsideVertical
            try:
                r.Borders(i).LineStyle = 1  # xlContinuous
                r.Borders(i).Weight = border
                r.Borders(i).Color = border_color if border_color is not None else rgb(0, 0, 0)
            except Exception:
                pass
    return r


def merge(ws, addr, value=None, **kwargs):
    ws.Range(addr).Merge()
    return set_range(ws, addr, value, **kwargs)


def build_sheet(xl, wb, spec, system, template_name):
    name = spec["name"]
    # 再実行時に生成済みシートを消す（生成名のみ）
    for s in list(wb.Worksheets):
        if s.Name == name:
            s.Delete()
    tpl = wb.Worksheets(template_name)
    ws = wb.Worksheets.Add(After=tpl)
    ws.Name = name

    ws.Cells.Font.Name = "Meiryo UI"
    ws.Cells.Font.Size = 9
    ws.Cells.VerticalAlignment = XL_TOP

    widths = {"A": 5, "B": 34, "C": 6, "D": 27, "E": 24,
              "F": 10, "G": 14, "H": 9, "I": 9, "J": 16}
    for col, w in widths.items():
        ws.Columns(col).ColumnWidth = w

    ws.Rows("1:1").RowHeight = 6
    ws.Rows("2:2").RowHeight = 30
    ws.Rows("3:3").RowHeight = 24
    ws.Rows("4:4").RowHeight = 24
    ws.Rows("5:5").RowHeight = 8
    ws.Rows("6:6").RowHeight = 26
    ws.Rows("7:7").RowHeight = 22
    ws.Rows("8:8").RowHeight = 22
    ws.Rows("9:9").RowHeight = 30

    # 公式様式のヘッダー
    merge(ws, "A2:F2", "手 順 書", font="Meiryo UI", size=16,
          halign=XL_CENTER, valign=XL_CENTER, border=XL_MEDIUM)
    set_range(ws, "G2", "管理番号", font="Meiryo UI", size=9, fill=HEADER_FILL,
              halign=XL_CENTER, valign=XL_CENTER, wrap=True, border=XL_THIN)
    set_range(ws, "H2", "", border=XL_THIN)
    set_range(ws, "I2", "頁", font="Meiryo UI", size=9, fill=HEADER_FILL,
              halign=XL_CENTER, valign=XL_CENTER, border=XL_THIN)
    set_range(ws, "J2", "", border=XL_THIN)

    merge(ws, "A3:B3", "型 名", font="Meiryo UI", size=9, fill=HEADER_FILL,
          halign=XL_CENTER, valign=XL_CENTER, border=XL_THIN)
    merge(ws, "C3:F3", "", border=XL_THIN)
    merge(ws, "G3:H3", "工程番号", font="Meiryo UI", size=9, fill=HEADER_FILL,
          halign=XL_CENTER, valign=XL_CENTER, border=XL_THIN)
    merge(ws, "I3:J3", "－", font="Meiryo UI", size=9,
          halign=XL_CENTER, valign=XL_CENTER, border=XL_THIN)

    merge(ws, "A4:B4", "作業内容", font="Meiryo UI", size=9, fill=HEADER_FILL,
          halign=XL_CENTER, valign=XL_CENTER, border=XL_THIN)
    merge(ws, "C4:J4", spec["title"], font="Meiryo UI", size=9,
          halign=XL_LEFT, valign=XL_CENTER, border=XL_THIN)

    # セクション見出し
    merge(ws, "A6:J6", spec["title"], font="Meiryo UI", size=11, bold=True,
          fill=SECTION_FILL, color=WHITE, halign=XL_LEFT, valign=XL_CENTER,
          wrap=False, indent=1)
    ws.Rows("6:6").RowHeight = 26

    # 対象・実施情報
    merge(ws, "A7:J7", f"対象システム：{system}　対象期間：____年__月__日〜__月__日",
          font="Meiryo UI", size=9, halign=XL_LEFT, valign=XL_CENTER,
          border=XL_THIN)
    merge(ws, "A8:J8", "実施日：____年__月__日　実施者：____________　確認者：____________",
          font="Meiryo UI", size=9, halign=XL_LEFT, valign=XL_CENTER,
          border=XL_THIN)

    # 表ヘッダー
    headers = ["No.", "点検項目", "原則", "確認方法", "判定基準",
               "結果", "証跡・記録No.", "実施者", "確認者", "備考"]
    for i, h in enumerate(headers, 1):
        set_range(ws, f"{colname(i)}9", h, font="Meiryo UI", size=9, bold=True,
                  fill=HEADER_FILL, halign=XL_CENTER, valign=XL_CENTER,
                  wrap=True, border=XL_THIN)

    # 本体
    start = 10
    for idx, item in enumerate(spec["items"], 1):
        text, principle, method, criterion, evidence, note = item
        values = [idx, text, principle, method, criterion, "", evidence, "", "", note]
        r = start + idx - 1
        ws.Rows(r).RowHeight = item_row_height(item)
        for c, v in enumerate(values, 1):
            halign = XL_CENTER if c in (1, 3, 6, 8, 9) else XL_LEFT
            indent = 1 if halign == XL_LEFT else None
            set_range(ws, f"{colname(c)}{r}", v, font="Meiryo UI", size=9,
                      halign=halign, valign=XL_CENTER, wrap=True,
                      border=XL_THIN, indent=indent)

    last_item = start + len(spec["items"]) - 1
    r = last_item + 1

    # 原則の凡例
    merge(ws, f"A{r}:J{r}",
          "原則：1=予防・早期発見／2=自動化・継続性／3=客観性と標準化／4=多層防御とセキュリティ／5=3H（初めて・変更・久しぶり）",
          font="Meiryo UI", size=8, halign=XL_LEFT, valign=XL_CENTER, wrap=True)
    ws.Rows(r).RowHeight = 24
    r += 1
    merge(ws, f"A{r}:J{r}",
          "空欄のまま提出しない。未実施は「未実施」、該当なしは「該当なし」と記入する。結果は○／×だけでなく、数値または画面の文言を記録する。",
          font="Meiryo UI", size=8, halign=XL_LEFT, valign=XL_CENTER, wrap=True)
    ws.Rows(r).RowHeight = 24
    r += 2

    # 承認欄
    rows = [
        ("実施者", "確認者"),
        ("管理責任者", "承認日"),
    ]
    for left, right in rows:
        merge(ws, f"A{r}:B{r}", left, font="Meiryo UI", size=9, bold=True,
              fill=HEADER_FILL, halign=XL_CENTER, valign=XL_CENTER,
              border=XL_THIN)
        merge(ws, f"C{r}:E{r}", "", border=XL_THIN)
        merge(ws, f"F{r}:G{r}", right, font="Meiryo UI", size=9, bold=True,
              fill=HEADER_FILL, halign=XL_CENTER, valign=XL_CENTER,
              border=XL_THIN)
        merge(ws, f"H{r}:J{r}", "", border=XL_THIN)
        ws.Rows(r).RowHeight = 24
        r += 1
    last_row = r - 1

    # 印刷設定
    ps = ws.PageSetup
    ps.Orientation = XL_LANDSCAPE
    ps.PaperSize = XL_A4
    ps.Zoom = False
    ps.FitToPagesWide = 1
    ps.FitToPagesTall = False
    ps.LeftMargin = 36
    ps.RightMargin = 36
    ps.TopMargin = 36
    ps.BottomMargin = 42
    ps.HeaderMargin = 18
    ps.FooterMargin = 18
    ps.CenterHorizontally = True
    ps.PrintGridlines = False
    ps.PrintArea = f"$A$1:$J${last_row}"
    ps.PrintTitleRows = "$1:$9"
    ps.LeftFooter = '&"ＭＳ ゴシック,標準"　　　NR4030'
    ps.CenterFooter = '&"ＭＳ ゴシック,標準"様式 NR4030-0300-A3'
    ps.RightFooter = '&"ＭＳ ゴシック,標準"日本光電'
    try:
        ws.Tab.Color = SECTION_FILL
    except Exception:
        pass

    return ws.Name, last_row


def main():
    targets = sys.argv[1:] or ["pana", "lnb"]
    WORK.mkdir(exist_ok=True)
    RENDER.mkdir(exist_ok=True)
    xl = win32.DispatchEx("Excel.Application")
    xl.Visible = False
    xl.DisplayAlerts = False
    try:
        for key in targets:
            data = ITEMS[key]
            src = Path(data["book"])
            work = WORK / f"{key}_checksheet_work.xlsx"
            shutil.copy2(src, work)
            wb = xl.Workbooks.Open(str(work), UpdateLinks=0, ReadOnly=False,
                                   IgnoreReadOnlyRecommended=True)
            try:
                built = []
                for spec in data["sheets"]:
                    built.append(build_sheet(xl, wb, spec, data["system"],
                                             data["template"]))
                wb.Save()
                outdir = RENDER / key
                outdir.mkdir(exist_ok=True)
                for sheet_name, _ in built:
                    pdf = outdir / f"{sheet_name.replace('(', '_').replace(')', '')}.pdf"
                    wb.Worksheets(sheet_name).ExportAsFixedFormat(0, str(pdf))
                    doc = fitz.open(str(pdf))
                    pix = doc[0].get_pixmap(dpi=150)
                    png = pdf.with_suffix(".png")
                    pix.save(str(png))
                    print(key, sheet_name, "pages", doc.page_count,
                          "png", pix.width, pix.height)
                    doc.close()
            finally:
                wb.Close(True)
    finally:
        xl.Quit()


if __name__ == "__main__":
    main()
