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

視認性の原則(2026-10-14 改訂):
- 行高は「セルごとの実測折り返し行数」から決める。テーブル内の最も高いセルに合わせ、
  文字が切れる状態(下の行が見えない)を残さない
- テーブルは列数に応じて列幅を配分する(固定幅の使い回しではなく、
  1列目=項目(短)・最終列=本文(長)という内容の性質に合わせる)
- 目次はハイパーリンクで各シートへ飛べるようにし、各シートの型名セルから目次へ戻れる
- 折り返しの概算は Excel の実挙動に合わせ安全率を乗じる(禁則処理で早く折り返されるため)
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
LINK_FONT = Font(name=FONT_NAME, size=10, color="0563C1", underline="single")

WRAP_TOP = Alignment(wrap_text=True, vertical="top")
WRAP_CENTER = Alignment(wrap_text=True, vertical="center")
CENTER = Alignment(horizontal="center", vertical="center")

# 列幅配分: テーブルの列数ごとの「1列目,2列目,...」の幅(キャラクタ単位)
# 1列目は項目名(短め)、最終列は本文(長め)を受ける
COL_WIDTH_PLANS = {
    2: [26, 100],
    3: [8, 30, 88],
    4: [8, 24, 62, 32],
    5: [6, 18, 46, 36, 26],
    6: [6, 14, 34, 34, 28, 20],
    7: [6, 12, 28, 30, 28, 22, 16],
}
DEFAULT_BODY_WIDTHS = [32, 95, 18, 18, 18, 18, 18]  # 本文ブロック(h/note/warn)用

# 行高の係数: 10pt 游ゴシックの1行 = 13.5pt、+上下の余白4pt
LINE_PT = 13.5
PAD_PT = 4.0
# 折り返し概算の安全率: Excel の実折り返しは概算より早く増える(禁則処理・プロポーショナル)
WRAP_SAFETY = 1.06


def _text_width(text):
    """文字列の表示幅を半角=1・全角=2で概算する。"""
    return sum(2 if ord(ch) > 0x2E80 else 1 for ch in str(text))


def _wrapped_lines(text, width_chars):
    """指定幅(半角換算)に収まる折り返し行数を概算する。"""
    lines = 0
    for part in str(text).split("\n"):
        w = _text_width(part)
        lines += max(1, -(-w * WRAP_SAFETY // width_chars))
    return max(1, int(lines))


def _needed_height(text, width_chars, base=None, line_pt=LINE_PT, pad=PAD_PT):
    lines = _wrapped_lines(text, width_chars)
    need = lines * line_pt + pad
    if base:
        need = max(need, base)
    return round(need, 1)


def _row_height(text, width_chars, base=14):
    """概算の行数から行の高さを決める(旧API・内部で _needed_height に委譲)。"""
    return _needed_height(text, width_chars, base=base)


def _cell_span_width(ws, cell, widths):
    """マージ範囲の左上なら合計幅、単独セルなら自列幅。マージ範囲の非左上は None。"""
    for m in ws.merged_cells.ranges:
        if m.min_row <= cell.row <= m.max_row and m.min_col <= cell.column <= m.max_col:
            if m.min_row == cell.row and m.min_col == cell.column:
                return sum(widths[get_column_letter(cc)] for cc in range(m.min_col, m.max_col + 1))
            return None
    return widths[cell.column_letter]


def _fit_row_heights(ws, row_range, widths, line_pt=LINE_PT, pad=PAD_PT, base=None):
    """row_range 内の各行について、wrap 有効セルの実測から行高を決める。

    テーブル/ブロック共通の唯一の行高決定経路。「文字が切れる」状態を排除する。
    """
    for r in row_range:
        need = base or 14
        for c in ws[r]:
            if c.value is None:
                continue
            span = _cell_span_width(ws, c, widths)
            if span is None:
                continue
            need = max(need, _needed_height(c.value, max(8, span * 2), line_pt=line_pt, pad=pad))
        ws.row_dimensions[r].height = round(need, 1)


def _audit_fit(ws, widths, min_row=6):
    """行高不足の行を返す(検証用)。[(行, 実高, 必要高), ...]"""
    out = []
    need_by_row = {}
    for row in ws.iter_rows(min_row=min_row):
        for c in row:
            if c.value is None or not c.alignment or not c.alignment.wrap_text:
                continue
            span = _cell_span_width(ws, c, widths)
            if span is None:
                continue
            need = _needed_height(c.value, max(8, span * 2))
            need_by_row[c.row] = max(need_by_row.get(c.row, 0), need)
    for r, need in need_by_row.items():
        actual = ws.row_dimensions[r].height or 14
        if need > actual + 2:
            out.append((r, actual, need))
    return out


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
    # ハイパーリンク付き: 目次→各シート、各シート→目次 の両方向
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
    toc["B5"] = "項目名を選ぶと該当シートへ移動します。各シートの「目次へ」から戻れます。"
    toc["B5"].font = NOTE_FONT
    tr = 6
    n = 1
    sheet_names = [s[0] for s in sheets if s[0] != "改訂履歴"]
    for sheet in sheets:
        name = sheet[0]
        if name == "改訂履歴":
            continue
        c = toc.cell(tr, 1, f"{n}.")
        c.font = BODY_FONT
        c.alignment = Alignment(horizontal="right", vertical="center")
        c.border = BORDER
        c2 = toc.cell(tr, 2, name)
        c2.font = LINK_FONT
        c2.alignment = Alignment(vertical="center")
        c2.border = BORDER
        # シート名の引用符をエスケープしてハイパーリンク化
        c2.hyperlink = f"#'{name[:31].replace(chr(39), chr(39)*2)}'!A1"
        toc.row_dimensions[tr].height = 16
        tr += 1
        n += 1

    # ---- 本体シート ----
    for sheet in sheets:
        name, blocks = sheet[0], sheet[1]
        ws = wb.create_sheet(name[:31])
        ws.sheet_view.showGridLines = False
        body_widths = DEFAULT_BODY_WIDTHS
        for i, w in enumerate(body_widths, start=1):
            ws.column_dimensions[get_column_letter(i)].width = w

        ws["A1"] = "手 順 書"
        ws["A1"].font = SHEET_HDR_FONT
        for col in "ABCDEFG":
            ws[f"{col}1"].border = Border(bottom=Side(style="medium", color="1F3864"))
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
        # 目次へ戻るリンク(G3)
        ws["G3"] = "目次へ"
        ws["G3"].font = LINK_FONT
        ws["G3"].alignment = Alignment(horizontal="right", vertical="center")
        ws["G3"].hyperlink = "#目次!A1"

        # 印刷設定: A4横向き・1ページ幅
        ws.page_setup.orientation = "landscape"
        ws.page_setup.paperSize = 9  # A4
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_title_rows = "1:4"

        r = 6
        # 本文ブロック用の幅辞書(A〜G の合計が横1ページの基準)
        widths = {get_column_letter(i): body_widths[i - 1] for i in range(1, 8)}
        full_width_chars = sum(body_widths) * 2  # マージ A:G の半角換算幅
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
                # 備考は9ptのため行高の係数を下げる
                ws.row_dimensions[r].height = _needed_height(
                    block[1], full_width_chars, line_pt=12.5, base=15)
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
                ws.row_dimensions[r].height = _needed_height(block[1], full_width_chars, base=15)
                r += 1
            elif kind == "table":
                data = block[1]
                ncols = max(len(t) for t in data)
                r0 = r
                for trow in data:
                    for ci, val in enumerate(trow, start=1):
                        ws.cell(r, ci, val)
                    r += 1
                # 列幅をテーブルの列数に合わせて配分する(視認性の核)
                plan = COL_WIDTH_PLANS.get(ncols, [22] * ncols)
                tbl_widths = {}
                for ci in range(1, ncols + 1):
                    col = get_column_letter(ci)
                    ws.column_dimensions[col].width = plan[ci - 1]
                    tbl_widths[col] = plan[ci - 1]
                # 配分後の幅で行高を決める
                _fit_row_heights(ws, range(r0, r), tbl_widths, base=16)
            elif kind == "rows":
                data = block[1]
                ncols = max(len(t) for t in data)
                r0 = r
                for trow in data:
                    for ci, val in enumerate(trow, start=1):
                        ws.cell(r, ci, val)
                    r += 1
                plan = COL_WIDTH_PLANS.get(ncols, [22] * ncols)
                tbl_widths = {}
                for ci in range(1, ncols + 1):
                    col = get_column_letter(ci)
                    ws.column_dimensions[col].width = plan[ci - 1]
                    tbl_widths[col] = plan[ci - 1]
                _style_table(ws, r0, len(data), ncols, header=False, widths=tbl_widths)
                for rr in range(r0, r):
                    ws.cell(rr, 1).font = BODY_BOLD_FONT
            r += 1  # ブロック間の空行

        # シート単位の最終監査: まだ行高が足りない行があれば補正する
        residual = _audit_fit(ws, {get_column_letter(i): (ws.column_dimensions[get_column_letter(i)].width or 18)
                                   for i in range(1, 8)})
        for rr, actual, need in residual:
            ws.row_dimensions[rr].height = need

    wb.save(path)
    print("saved:", path)


def T(header, rows):
    """table with bold header row"""
    return ("table", [header] + rows, True)
