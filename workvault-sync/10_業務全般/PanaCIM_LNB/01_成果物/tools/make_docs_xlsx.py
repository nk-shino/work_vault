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


def _style_table(ws, r0, nrows, ncols, header=True, widths=None):
    """テーブルへ罫線・フォント・行高を適用する。

    行高は _fit_row_heights(セル実測)で決める。widths は列→キャラクタ幅の辞書。
    """
    for rr in range(r0, r0 + nrows):
        for cc in range(1, ncols + 1):
            c = ws.cell(rr, cc)
            c.border = BORDER
            c.alignment = WRAP_TOP
            if header and rr == r0:
                c.fill = TABLE_HDR_FILL
                c.font = TABLE_HDR_FONT
                c.alignment = WRAP_CENTER
            else:
                c.font = BODY_FONT
    if widths is None:
        widths = {get_column_letter(cc): 24 for cc in range(1, ncols + 1)}
    _fit_row_heights(ws, range(r0, r0 + nrows), widths, base=16)
    # 空欄の行(記入スペース)は手書きを想定して最低 24pt を確保する
    for rr in range(r0 + 1, r0 + nrows):
        has_value = any(ws.cell(rr, cc).value for cc in range(1, ncols + 1))
        if not has_value and (ws.row_dimensions[rr].height or 0) < 24:
            ws.row_dimensions[rr].height = 24
    # 2列テーブル(項目/内容形式)は1列目をラベルとして太字にする
    if ncols == 2:
        for rr in range(r0 + 1, r0 + nrows):
            ws.cell(rr, 1).font = BODY_BOLD_FONT


RESOLVED_FONT = Font(name=FONT_NAME, size=10, color="808080", strike=True)


# =====================================================================
# NR4030 様式モード(0494-913473 実装プログラム手順(DGS) の形式を完全再現)
# 実測仕様(02_参照元/マウントプログラム(DGS)/様式分析 2026-10-14):
# - ヘッダー枠: A1:V2「手 順 書」/ W2:AB2「管理番号」/ AC2:AT2 値欄 /
#   AU2:AV2「頁」/ AW2:AZ2 値欄(印刷時フッタ&Pで付番) /
#   A3:F3「型   名」/ G3:V3 値欄 / W3:AB3「工程番号」/ AC3:AZ3「－」/
#   A4:F4「作業内容」/ G4:AZ4 題目(頭を全角スペース1字)
# - 枠罫線: 外周 medium・内側 thin(黒)
# - 行高: 行1=5.25pt/行2-4=33pt/本文=12.75pt
# - 列幅: A=1.9(番号頭出し)/AZ=3.3/中間=既定(8.09)/BA以降=1.9
# - フォント: Meiryo UI 16pt(A1)/10pt(枠・本文)
# - 向き: 縦向き A4・スケール指定なし・約55行/頁
# - 余白: 左0.87"/右0.51"/上0.59"/下0.79"
# - フッタ: 左「　　NR4030」/中央「様式 NR4030-0300-A3」/右「&P」+右上「日本光電」
# - 手動改ページ: 約55行ごと+「作業内容」ヘッダ(行4相当)を再掲
# =====================================================================

NR30_FONT_HDR = Font(name="Meiryo UI", size=16)
NR30_FONT = Font(name="Meiryo UI", size=10)
NR30_BORDER_NONE = Border()
NR30_M = Side(style="medium")
NR30_T = Side(style="thin")


def _nr30_border(l=None, r=None, t=None, b=None):
    return Border(left=l, right=r, top=t, bottom=b)


def _nr30_header(ws, topic):
    """NR4030 様式のヘッダー枠(A1:AZ4)を描く。topic=作業内容の題目。"""
    # 列幅(実測値)
    ws.column_dimensions["A"].width = 1.9
    ws.column_dimensions["AZ"].width = 3.3
    ws.column_dimensions["BA"].width = 1.9
    ws.column_dimensions["BB"].width = 1.9
    # 行高(実測値)
    ws.row_dimensions[1].height = 5.25
    for rr in (2, 3, 4):
        ws.row_dimensions[rr].height = 33.0
    # 結合
    for rng in ("A1:V2", "W2:AB2", "AC2:AT2", "AU2:AV2", "AW2:AZ2",
                "A3:F3", "G3:V3", "W3:AB3", "AC3:AZ3", "A4:F4", "G4:AZ4"):
        ws.merge_cells(rng)
    # 値と書式
    c = ws["A1"]; c.value = "手 順 書"; c.font = NR30_FONT_HDR
    c.alignment = Alignment(horizontal="center", vertical="top")
    for ref, val in (("W2", "管理番号"), ("AU2", "頁"),
                     ("A3", "型   名"), ("W3", "工程番号"),
                     ("AC3", "－"), ("A4", "作業内容")):
        c = ws[ref]; c.value = val; c.font = NR30_FONT
        c.alignment = CENTER
    c = ws["G4"]; c.value = "　" + topic; c.font = NR30_FONT
    c.alignment = Alignment(horizontal="left", vertical="center")
    # 枠罫線: 外周 medium・内側 thin(実測の罫線配置)
    # 行2(管理番号/頁の帯): 上=medium 下=thin、帯内は thin 区切り
    for col in range(23, 53):  # W..AZ
        cell = ws.cell(2, col)
        cell.border = _nr30_border(t=NR30_M, b=NR30_T,
                                   l=NR30_T if col > 23 else NR30_M,
                                   r=NR30_T if col < 52 else NR30_M)
    for col in range(1, 23):  # A..V(手順書タイトル帯)
        cell = ws.cell(2, col)
        cell.border = _nr30_border(t=NR30_M, b=NR30_T,
                                   l=NR30_M if col == 1 else NR30_T,
                                   r=NR30_T if col < 22 else NR30_M)
    # 行3(型名/工程番号): 上=medium(帯境) 下=thin
    for col in range(1, 53):
        cell = ws.cell(3, col)
        cell.border = _nr30_border(t=NR30_M, b=NR30_T,
                                   l=NR30_M if col == 1 else NR30_T,
                                   r=NR30_T if col < 52 else NR30_M)
    # 行4(作業内容/題目): 上=thin 下=medium(枠の締め)
    for col in range(1, 53):
        cell = ws.cell(4, col)
        cell.border = _nr30_border(t=NR30_T, b=NR30_M,
                                   l=NR30_M if col == 1 else NR30_T,
                                   r=NR30_T if col < 52 else NR30_M)
    # A1:V2 の帯枠
    for col in range(1, 23):
        ws.cell(1, col).border = _nr30_border(t=NR30_M,
                                              l=NR30_M if col == 1 else None,
                                              r=NR30_M if col == 22 else None)
    ws.cell(2, 1).border = _nr30_border(l=NR30_M, t=NR30_M, b=NR30_T)
    ws.cell(2, 22).border = _nr30_border(r=NR30_M, t=NR30_M, b=NR30_T)


def _nr30_page_setup(ws):
    """NR4030 様式の印刷設定(実測値)。"""
    ws.page_setup.orientation = "portrait"
    ws.page_setup.paperSize = 9
    ws.page_margins.left = 0.8661417322834646
    ws.page_margins.right = 0.5118110236220472
    ws.page_margins.top = 0.5905511811023623
    ws.page_margins.bottom = 0.7874015748031497
    ws.oddFooter.left.text = "　　NR4030"
    ws.oddFooter.center.text = "様式 NR4030-0300-A3"
    ws.oddFooter.right.text = "\n&P\n日本光電"
    ws.print_title_rows = "1:4"


def _nr30_body_row(ws, r, num, text_lines, note=None):
    """NR4030 様式の本文行: A列=手順番号「n．」、C列=本文、行高12.75pt。

    text_lines: 本文(文字列 or 文字列リスト=1手順の複数行)。
    note: 先頭に＊/※を付ける補足行の場合 True。
    """
    h = 12.75
    if num is not None:
        c = ws.cell(r, 1, f"{num}．")
        c.font = NR30_FONT
        c.alignment = Alignment(horizontal="left", vertical="center")
    if text_lines:
        if isinstance(text_lines, str):
            text_lines = [text_lines]
        for i, line in enumerate(text_lines):
            c = ws.cell(r + i, 3, line)
            c.font = NR30_FONT
            c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=False)
    for i in range(max(1, len(text_lines) if text_lines else 1)):
        ws.row_dimensions[r + i].height = h
    return r + max(1, len(text_lines) if text_lines else 1)


def _nr30_page_break(ws, r, topic):
    """約55行ごとの改ページ+継続ヘッダ(作業内容+題目)を再掲する。"""
    from openpyxl.worksheet.pagebreak import Break
    ws.row_breaks.append(Break(id=r - 1))
    # 継続ヘッダ: 行4相当(作業内容+題目)をコピー
    hr = r
    ws.cell(hr, 1, "作業内容").font = NR30_FONT
    ws.cell(hr, 1).alignment = CENTER
    ws.cell(hr, 7, "　" + topic).font = NR30_FONT
    ws.cell(hr, 7).alignment = Alignment(horizontal="left", vertical="center")
    for col in range(1, 53):
        cell = ws.cell(hr, col)
        cell.border = _nr30_border(t=NR30_M, b=NR30_M,
                                   l=NR30_M if col == 1 else NR30_T,
                                   r=NR30_T if col < 52 else NR30_M)
    ws.row_dimensions[hr].height = 33.0
    return hr + 2  # 本文はヘッダの1行あけから


def _mark_resolved_rows(ws, r0, nrows, ncols):
    """「解決」を含む行を取り消し線+灰色にする(解決済みの視認性)。

    削除はしない(消すと同じ調査をやり直すため、md 正本の運用に揃える)。
    判定はセル値に「解決」を含む行。ヘッダ行は対象外。
    """
    for rr in range(r0 + 1, r0 + nrows):
        vals = [str(ws.cell(rr, cc).value or "") for cc in range(1, ncols + 1)]
        if any("解決" in v for v in vals):
            for cc in range(1, ncols + 1):
                ws.cell(rr, cc).font = RESOLVED_FONT


def _build_nr30(wb, title, sheets, version, authors, team_leader, meeting_notes=None):
    """NR4030 様式モードの本体生成。

    - 表紙シート(改訂履歴を含む: P1 相当。0494-913473 P1 の構成を再現)
    - 目次シート(会議で削除決定の項目は「(削除)」付きで表示・リンクは保持)
    - 本文シート(P2 相当: ヘッダー枠+「n．」手順+約55行改ページ)
    meeting_notes: {シート名: 会議メモ文字列}。目次の当該行に注記を付ける。
    """
    import re

    # ---- 表紙(P1 相当: 手順書タイトル+承認欄+変更履歴) ----
    cover = wb.active
    cover.title = "表紙"
    cover.sheet_view.showGridLines = False
    _nr30_header(cover, title + "／" + "ＺＺＺ－９００００")
    _nr30_page_setup(cover)
    # P1 はヘッダー枠の下に文書情報を置く(P2 と同一の様式枠で開始)
    c = cover.cell(6, 3, "共通(操作)")
    c.font = NR30_FONT
    c = cover.cell(7, 3, title)
    c.font = Font(name="Meiryo UI", size=14)
    c = cover.cell(8, 3, "ＺＺＺ－９００００")
    c.font = NR30_FONT
    # 承認/検印/作成 欄(行10-15)
    cover.cell(10, 5, "承 　認").font = NR30_FONT
    cover.cell(10, 8, "検 　印").font = NR30_FONT
    cover.cell(10, 11, "作　 成").font = NR30_FONT
    cover.cell(12, 5, "承 認 日").font = NR30_FONT
    cover.cell(13, 5, "作 成 日").font = NR30_FONT
    cover.cell(12, 7, "－　　－").font = NR30_FONT
    cover.cell(13, 7, "－　　－").font = NR30_FONT
    cover.cell(14, 5, "初版枚数").font = NR30_FONT
    cover.cell(14, 7, "（本文シート数で確定）").font = NR30_FONT
    cover.cell(12, 11, "・".join(authors.split("、"))).font = NR30_FONT
    cover.merge_cells("K12:O12")
    # 変更履歴(行17以降: P1 の変更記号テーブルを再現)
    rev = None
    for name, blocks in sheets:
        if name == "改訂履歴":
            rev = blocks
            break
    hr = 17
    cover.cell(hr, 2, "変更履歴").font = NR30_FONT_HDR
    hr += 2
    hdr = ["変更記号", "適用年月日", "変更を指示した書類の管理No.", "内　　容", "承認日／承認者", "担 当"]
    for i, h in enumerate(hdr):
        c = cover.cell(hr, 2 + i * 3, h)
        c.font = NR30_FONT
        c.alignment = CENTER
        cover.merge_cells(start_row=hr, start_column=2 + i * 3, end_row=hr, end_column=4 + i * 3)
    ws_rows = []
    if rev:
        for b in rev:
            if b[0] == "table":
                ws_rows = b[1]
    for row in ws_rows[1:]:
        hr += 1
        # row = [版, 日付, 内容, 作成, 承認]
        vals = [row[0] + "×", row[1], "－", str(row[2])[:80], "未", row[3]]
        for i, v in enumerate(vals):
            c = cover.cell(hr, 2 + i * 3, v)
            c.font = NR30_FONT
            c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
            cover.merge_cells(start_row=hr, start_column=2 + i * 3, end_row=hr, end_column=4 + i * 3)
        cover.row_dimensions[hr].height = _needed_height(str(vals[3]), 40, line_pt=12.75, base=14)

    # ---- 目次 ----
    toc = wb.create_sheet("目次", 1)
    toc.sheet_view.showGridLines = False
    _nr30_header(toc, "目次")
    _nr30_page_setup(toc)
    tr = 6
    n = 1
    for name, blocks in sheets:
        if name == "改訂履歴":
            continue
        c = toc.cell(tr, 3, f"{n}．")
        c.font = NR30_FONT
        c.alignment = Alignment(horizontal="right", vertical="center")
        # 会議メモの反映: 削除決定は「(削除)」を表示、その他のメモは J 列に注記
        display = name
        note = None
        if meeting_notes and name in meeting_notes:
            note = meeting_notes[name]
            if "削除" in note and "WIP" not in note:
                display = name + "(削除)"
            elif "WIP" in note:
                display = name + "(WIP)"
        c2 = toc.cell(tr, 4, display)
        c2.font = Font(name="Meiryo UI", size=10, color="0563C1", underline="single")
        c2.hyperlink = f"#'{name[:31].replace(chr(39), chr(39)*2)}'!A1"
        if note:
            c3 = toc.cell(tr, 10, note)
            c3.font = NR30_FONT
            c3.alignment = Alignment(horizontal="left", vertical="center")
        toc.row_dimensions[tr].height = 12.75
        tr += 1
        n += 1

    # ---- 本文シート(P2 相当) ----
    for name, blocks in sheets:
        if name == "改訂履歴":
            continue
        ws = wb.create_sheet(name[:31])
        ws.sheet_view.showGridLines = False
        _nr30_header(ws, name)
        _nr30_page_setup(ws)
        r = 6
        for block in blocks:
            kind = block[0]
            if kind == "h":
                # 見出し: 番号付き(NR4030 では本文と同サイズ・区別は番号体系)
                c = ws.cell(r, 1, block[1])
                c.font = Font(name="Meiryo UI", size=10, bold=True)
                ws.row_dimensions[r].height = 12.75
                r += 1
            elif kind in ("note", "warn"):
                lines = str(block[1]).split("\n")
                for line in lines:
                    prefix = "" if line.startswith(("＊", "※")) else ("＊" if kind == "note" else "※")
                    c = ws.cell(r, 3, prefix + line)
                    c.font = NR30_FONT
                    ws.row_dimensions[r].height = 12.75
                    r += 1
            elif kind in ("table", "rows"):
                data = block[1]
                header_row = kind == "table"
                for ri, trow in enumerate(data):
                    if header_row and ri == 0:
                        # テーブルヘッダ: 太字
                        for ci, val in enumerate(trow):
                            c = ws.cell(r, 1 if ci == 0 else 1 + ci * 2, val)
                            c.font = Font(name="Meiryo UI", size=10, bold=True)
                            c.alignment = CENTER
                        ws.row_dimensions[r].height = 12.75
                        r += 1
                        continue
                    first = str(trow[0]) if trow else ""
                    m = re.match(r"^手順(\d+)$", first)
                    if m:
                        proc_no = int(m.group(1))
                        r = _nr30_body_row(ws, r, proc_no, [str(v) for v in trow[1:] if v])
                    else:
                        # 項目: 値 形式 → C列に「項目：値」
                        text = first + "：" + "／".join(str(v) for v in trow[1:] if v)
                        c = ws.cell(r, 3, text)
                        c.font = NR30_FONT
                        ws.row_dimensions[r].height = 12.75
                        r += 1
                r += 1  # テーブル間の空行
        # 約55行ごとの改ページ
        from openpyxl.worksheet.pagebreak import Break
        page_len = 0
        for rr in range(6, r + 1):
            page_len += 1
            if page_len >= 55:
                ws.row_breaks.append(Break(id=rr))
                page_len = 0


def build(path, title, sheets, revision, authors, team_leader, ref_format, version,
          toc_title=None, nr30=False, meeting_notes=None):
    """xlsx を生成する。

    nr30=True で NR4030 様式モード(0494-913473 の形式を完全再現)。
    meeting_notes: {シート名: 会議メモ} を目次へ反映(NR30 モードのみ)。
    """
    wb = openpyxl.Workbook()
    cover = wb.active
    cover.title = "表紙"

    if nr30:
        _build_nr30(wb, title, sheets, version, authors, team_leader, meeting_notes)
        wb.save(path)
        print("saved:", path)
        return

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
        # 列幅はシートごとに1度だけ決める(後続ブロックで上書きしない)。
        # 基準はシート内テーブルの最大列数。h/note/warn は A:G マージのため影響を受けない
        max_cols = 2
        for block in blocks:
            if block[0] in ('table', 'rows'):
                max_cols = max(max_cols, max(len(t) for t in block[1]))
        plan = COL_WIDTH_PLANS.get(max_cols, DEFAULT_BODY_WIDTHS[:max_cols])
        for i, w in enumerate(plan, start=1):
            ws.column_dimensions[get_column_letter(i)].width = w
        widths = {get_column_letter(i): plan[i - 1] for i in range(1, max_cols + 1)}
        body_widths = plan + [18] * (7 - len(plan)) if len(plan) < 7 else plan
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
                # 行高はシート共通の列幅で実測決定する
                _fit_row_heights(ws, range(r0, r), widths, base=16)
                # 空欄の行(記入スペース)は手書きを想定して最低 24pt を確保する
                for rr in range(r0 + 1, r):
                    has_value = any(ws.cell(rr, cc).value for cc in range(1, ncols + 1))
                    if not has_value and (ws.row_dimensions[rr].height or 0) < 24:
                        ws.row_dimensions[rr].height = 24
                # ヘッダの太字・白文字を適用(行高計算のあとで上書きしない)
                for cc in range(1, ncols + 1):
                    hc = ws.cell(r0, cc)
                    hc.fill = TABLE_HDR_FILL
                    hc.font = TABLE_HDR_FONT
                    hc.alignment = WRAP_CENTER
                # 解決済み行(「解決」を含む)を取り消し線+灰色に
                _mark_resolved_rows(ws, r0, len(data), ncols)
            elif kind == "rows":
                data = block[1]
                ncols = max(len(t) for t in data)
                r0 = r
                for trow in data:
                    for ci, val in enumerate(trow, start=1):
                        ws.cell(r, ci, val)
                    r += 1
                _style_table(ws, r0, len(data), ncols, header=False, widths=widths)
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
