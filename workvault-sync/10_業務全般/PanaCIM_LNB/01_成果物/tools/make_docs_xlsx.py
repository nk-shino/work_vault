# -*- coding: utf-8 -*-
"""草案のmdを、0494-912039(06)の様式に倣ったExcelへ落とし込む。

様式の再現ルール(既存xlsxより):
- シート1枚 = 1トピック
- A1「手 順 書」、行3 型名、行4 作業内容、本文は行6以降

装飾のベストプラクティス:
- フォント: 游ゴシック(Windows標準・可読性高)。欧米混在に備え theme フォントではなく明示指定
- サイズ: 本文10pt(業務文書の標準)、見出し11pt太字、表紙タイトル20pt
- 色: 4色のみで統一(彩度を抑えた業務配色)
  - 見出し: 濃紺文字 + 淡青地 D9E1F2
  - 注意: 黒太字 + 淡橙地 FCE4D6(赤系は「危険」の意味が強すぎるため注意レベルに抑える)
  - 備考: 濃灰文字 595959 + 淡黄地 FFF2CC
  - 表ヘッダ: 濃紺地 4472C4 + 白文字(参照性最優先)
- 枠線: 罫線は薄灰で統一し、線の強弱でなく塗りで構造を示す
- 印刷: A4横向き、1ページ幅に収める(現場での印刷運用を想定)
"""
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

FONT_NAME = "游ゴシック"

THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

HDR_FILL = PatternFill("solid", fgColor="D9E1F2")
HDR_FONT = Font(name=FONT_NAME, size=11, bold=True, color="1F3864")
NOTE_FILL = PatternFill("solid", fgColor="FFF2CC")
NOTE_FONT = Font(name=FONT_NAME, size=9, italic=True, color="595959")
WARN_FILL = PatternFill("solid", fgColor="FCE4D6")
WARN_FONT = Font(name=FONT_NAME, size=10, bold=True, color="833C00")
TABLE_HDR_FILL = PatternFill("solid", fgColor="4472C4")
TABLE_HDR_FONT = Font(name=FONT_NAME, size=10, bold=True, color="FFFFFF")
BODY_FONT = Font(name=FONT_NAME, size=10)
BODY_BOLD_FONT = Font(name=FONT_NAME, size=10, bold=True)
LABEL_FONT = Font(name=FONT_NAME, size=10, bold=True, color="1F3864")
TITLE_FONT = Font(name=FONT_NAME, size=20, bold=True, color="1F3864")
SHEET_HDR_FONT = Font(name=FONT_NAME, size=12, bold=True)

WRAP_TOP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center")


def _row_height(text, width_chars, base=14):
    """概算の行数から行の高さを決める。"""
    lines = 0
    for part in str(text).split("\n"):
        # 日本語は全角2文字扱いで概算
        w = sum(2 if ord(ch) > 0x2E80 else 1 for ch in part)
        lines += max(1, -(-w // width_chars))
    return max(base, 13.5 * lines + 3)


def _style_table(ws, r0, nrows, ncols, header=True):
    for rr in range(r0, r0 + nrows):
        for cc in range(1, ncols + 1):
            c = ws.cell(rr, cc)
            c.border = BORDER
            c.alignment = WRAP_TOP
            if header and rr == r0:
                c.fill = TABLE_HDR_FILL
                c.font = TABLE_HDR_FONT
                c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
            else:
                c.font = BODY_FONT
    if header:
        ws.row_dimensions[r0].height = _row_height(
            max((str(ws.cell(r0, cc).value or "") for cc in range(1, ncols + 1)), key=len),
            24, base=18)
        for rr in range(r0 + 1, r0 + nrows):
            longest = max((str(ws.cell(rr, cc).value or "") for cc in range(1, ncols + 1)), key=len)
            ws.row_dimensions[rr].height = _row_height(longest, 48)
        # 2列テーブル(項目/内容形式)は1列目をラベルとして太字にする
        if ncols == 2:
            for rr in range(r0 + 1, r0 + nrows):
                ws.cell(rr, 1).font = BODY_BOLD_FONT


def build(path, title, sheets, revision, authors, team_leader, ref_format, version,
          toc_title=None):
    wb = openpyxl.Workbook()
    cover = wb.active
    cover.title = "表紙"

    # ---- 表紙 ----
    cover.sheet_view.showGridLines = False
    cover.column_dimensions["A"].width = 26
    cover.column_dimensions["B"].width = 80
    cover["B2"] = "管 理 手 順 書"
    cover["B2"].font = TITLE_FONT
    cover["B2"].alignment = Alignment(horizontal="left", vertical="center")
    cover.row_dimensions[2].height = 40
    cover["B3"] = "(草案・未検証)"
    cover["B3"].font = Font(name=FONT_NAME, size=10, color="595959")
    rows = [
        ("文書名", title),
        ("文書番号", "ZZZ-90000(付番規則は要確認)"),
        ("版", version + "(草案・未検証)"),
        ("対象システム", title.split(" ")[0]),
        ("作成", authors),
        ("作成チームリーダー", team_leader),
        ("承認 / 検印", "要確認"),
        ("作成日 / 承認日", "要確認"),
        ("様式の参考", ref_format),
        ("文書状態", "草案・未検証。「要確認」は承認または実機確認が済んでいない事項を指す。"),
        ("認証情報", "本文に書かない。値は別紙管理とし、保管先のみを示す。"),
    ]
    r = 5
    for k, v in rows:
        kc = cover.cell(r, 1, k)
        kc.font = LABEL_FONT
        kc.fill = HDR_FILL
        kc.border = BORDER
        kc.alignment = WRAP_TOP
        vc = cover.cell(r, 2, v)
        vc.font = BODY_FONT
        vc.border = BORDER
        vc.alignment = WRAP_TOP
        cover.row_dimensions[r].height = _row_height(v, 76)
        r += 1

    # ---- 目次シート(既存様式に倣い、番号=シート対応で自動生成) ----
    toc = wb.create_sheet("目次", 1)
    toc.sheet_view.showGridLines = False
    toc.column_dimensions["A"].width = 8
    toc.column_dimensions["B"].width = 60
    toc["A1"] = "手 順 書"
    toc["A1"].font = SHEET_HDR_FONT
    toc["A3"] = "型   名"
    toc["A3"].font = BODY_BOLD_FONT
    toc["D3"] = "ZZZ-90000(仮)"
    toc["D3"].font = BODY_BOLD_FONT
    toc["A4"] = "作業内容"
    toc["A4"].font = BODY_BOLD_FONT
    toc["D4"] = "目次"
    toc["D4"].font = LABEL_FONT
    for cellref in ("A3", "A4", "D3", "D4"):
        toc[cellref].border = BORDER
        toc[cellref].fill = HDR_FILL
    tr = 6
    n = 1
    for sheet in sheets:
        name = sheet[0]
        if name == "改訂履歴":
            continue
        c = toc.cell(tr, 1, f"{n}.")
        c.font = BODY_FONT
        c.alignment = Alignment(horizontal="right", vertical="top")
        c2 = toc.cell(tr, 2, name)
        c2.font = BODY_FONT
        toc.cell(tr, 1).border = BORDER
        toc.cell(tr, 2).border = BORDER
        tr += 1
        n += 1

    # ---- 本体シート ----
    for sheet in sheets:
        name, blocks = sheet[0], sheet[1]
        ws = wb.create_sheet(name[:31])
        ws.sheet_view.showGridLines = False
        ws.column_dimensions["A"].width = 32
        ws.column_dimensions["B"].width = 95
        for col in "CDEFG":
            ws.column_dimensions[col].width = 18

        ws["A1"] = "手 順 書"
        ws["A1"].font = SHEET_HDR_FONT
        ws["A1"].border = Border(bottom=Side(style="medium", color="1F3864"))
        ws["D1"].border = Border(bottom=Side(style="medium", color="1F3864"))
        ws["E1"].border = Border(bottom=Side(style="medium", color="1F3864"))
        ws["F1"].border = Border(bottom=Side(style="medium", color="1F3864"))
        ws["G1"].border = Border(bottom=Side(style="medium", color="1F3864"))
        ws["A3"] = "型   名"
        ws["A3"].font = BODY_BOLD_FONT
        ws["D3"] = "ZZZ-90000(仮)"
        ws["D3"].font = BODY_BOLD_FONT
        ws["A4"] = "作業内容"
        ws["A4"].font = BODY_BOLD_FONT
        ws["D4"] = name
        ws["D4"].font = LABEL_FONT
        ws["A3"].fill = ws["A4"].fill = HDR_FILL
        ws["D3"].fill = ws["D4"].fill = HDR_FILL
        for cellref in ("A3", "A4", "D3", "D4"):
            ws[cellref].border = BORDER

        # 印刷設定: A4横向き・1ページ幅
        ws.page_setup.orientation = "landscape"
        ws.page_setup.paperSize = 9  # A4
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_title_rows = "1:4"

        r = 6
        for block in blocks:
            kind = block[0]
            if kind == "h":
                c = ws.cell(r, 1, block[1])
                c.font = HDR_FONT
                c.fill = HDR_FILL
                c.border = BORDER
                c2 = ws.cell(r, 2)
                c2.fill = HDR_FILL
                c2.border = BORDER
                ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=7)
                c.alignment = Alignment(vertical="center")
                ws.row_dimensions[r].height = 20
                r += 1
            elif kind == "note":
                c = ws.cell(r, 1, block[1])
                c.alignment = WRAP_TOP
                c.font = NOTE_FONT
                c.fill = NOTE_FILL
                c.border = BORDER
                for cc in range(2, 8):
                    ws.cell(r, cc).fill = NOTE_FILL
                    ws.cell(r, cc).border = BORDER
                ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=7)
                ws.row_dimensions[r].height = _row_height(block[1], 160, base=15)
                r += 1
            elif kind == "warn":
                c = ws.cell(r, 1, block[1])
                c.alignment = WRAP_TOP
                c.font = WARN_FONT
                c.fill = WARN_FILL
                c.border = BORDER
                for cc in range(2, 8):
                    ws.cell(r, cc).fill = WARN_FILL
                    ws.cell(r, cc).border = BORDER
                ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=7)
                ws.row_dimensions[r].height = _row_height(block[1], 150, base=15)
                r += 1
            elif kind == "table":
                data = block[1]
                ncols = max(len(t) for t in data)
                r0 = r
                for trow in data:
                    for ci, val in enumerate(trow, start=1):
                        ws.cell(r, ci, val)
                    r += 1
                _style_table(ws, r0, len(data), ncols, header=True)
            elif kind == "rows":
                data = block[1]
                r0 = r
                for trow in data:
                    for ci, val in enumerate(trow, start=1):
                        ws.cell(r, ci, val)
                    r += 1
                _style_table(ws, r0, len(data), max(len(t) for t in data), header=False)
                for rr in range(r0, r):
                    ws.cell(rr, 1).font = BODY_BOLD_FONT
            r += 1  # ブロック間の空行

    wb.save(path)
    print("saved:", path)


def T(header, rows):
    """table with bold header row"""
    return ("table", [header] + rows, True)
