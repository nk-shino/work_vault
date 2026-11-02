# -*- coding: utf-8 -*-
"""判明した事実を Excel 1冊に集約する。
構成: 表紙/サマリ → 不整合・未確認一覧(対応状況列付き) → 根拠一覧 → 図(5ページPNG貼付) → 測定方法
根拠: 根拠_関係対応表.md + evidence/excel_facts.json (対象Excelの実測のみ)
"""
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as XLImage
from openpyxl.worksheet.table import Table, TableStyleInfo
import os, json

OUT = r"C:\Users\ss80751\kohden-code-workspace\20261015_DGS草案可視化\output\判明事実一覧_20261015.xlsx"
IMGDIR = r"C:\Users\ss80751\kohden-code-workspace\20261015_DGS草案可視化\output"

wb = openpyxl.Workbook()

# ---- 共通スタイル ----
F_TITLE = Font(name="Meiryo UI", size=16, bold=True, color="1F2937")
F_SUB = Font(name="Meiryo UI", size=10, color="6B7280")
F_H = Font(name="Meiryo UI", size=10, bold=True, color="FFFFFF")
F_B = Font(name="Meiryo UI", size=10)
F_BOLD = Font(name="Meiryo UI", size=10, bold=True)
FILL_H = PatternFill("solid", fgColor="374151")
FILL_WARN = PatternFill("solid", fgColor="FDE9E1")
FILL_GRAY = PatternFill("solid", fgColor="F3F4F6")
FILL_OK = PatternFill("solid", fgColor="E8F0E4")
THIN = Side(style="thin", color="B0B7C3")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")
WRAPC = Alignment(wrap_text=True, vertical="top", horizontal="center")

def set_header(ws, row, headers, widths):
    for i, (h, w) in enumerate(zip(headers, widths), 1):
        c = ws.cell(row, i, h)
        c.font = F_H; c.fill = FILL_H; c.border = BORDER
        c.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = ws.cell(row + 1, 1)

def put(ws, row, values, fill=None, bold_first=False):
    for i, v in enumerate(values, 1):
        c = ws.cell(row, i, v)
        c.font = F_BOLD if (bold_first and i == 1) else F_B
        c.border = BORDER; c.alignment = WRAP
        if fill: c.fill = fill

# ============================================================
# シート1: 表紙・サマリ
# ============================================================
ws = wb.active; ws.title = "表紙・サマリ"
ws.sheet_view.showGridLines = False
ws["B2"] = "分析済みExcel 4ファイル 判明事実一覧"; ws["B2"].font = F_TITLE
ws["B3"] = "対象: DGS実装プログラム手順書(P1/P2)・PanaCIM管理手順書草案(会議版)・LNB管理手順書草案(会議版)"
ws["B3"].font = F_SUB
ws["B4"] = "作成日: 2026-10-15 ／ 作成: Kohden Code ／ 根拠: 対象Excelの実測のみ(参照先資料は未確認)"; ws["B4"].font = F_SUB

rows = [
    ("1. 目的", "4ファイルの解析で判明した不整合・未確認事項(K-01〜K-14)と構造実測を1冊に集約し、修正対応の管理と会議共有に使う。"),
    ("2. 使い方", "「不整合・未確認一覧」の対応状況・担当・期限を更新して管理する。「根拠一覧」で図の各要素のExcel上の所在を確認できる。"),
    ("3. 根拠の制限", "記載は「Excel内に記載あり」の精度。実機・参照先(0494-912039(06)等)は未確認。認証情報の値は転記せずマスク表記。"),
    ("4. 集計", "矛盾あり 6件(K-01,02,03,07,13,14)／Excel内記載の確認 4件(K-04,08,10＋様式相違)／構造実測 2件(K-05,06)／未取得・未確認 3件(K-09,11,12)。"),
    ("5. 図", "「図」シートに構造関係図(drawio)の全5ページを貼付。編集可能な元ファイルは 分析済みExcel構造関係図.drawio。"),
]
r = 6
for k, v in rows:
    ws.cell(r, 2, k).font = F_BOLD
    c = ws.cell(r, 3, v); c.font = F_B; c.alignment = WRAP
    ws.merge_cells(start_row=r, start_column=3, end_row=r, end_column=9)
    ws.row_dimensions[r].height = 30
    r += 1
ws.column_dimensions["B"].width = 16
for col in "CDEFGHI": ws.column_dimensions[col].width = 14

# ============================================================
# シート2: 不整合・未確認一覧
# ============================================================
ws2 = wb.create_sheet("不整合・未確認一覧")
ws2.sheet_view.showGridLines = False
ws2["A1"] = "不整合・未確認事項(K-01〜K-14)"; ws2["A1"].font = F_TITLE
headers = ["ID", "区分", "内容", "対象ファイル", "根拠セル/シート", "状態", "対応状況", "担当", "期限", "備考"]
widths = [7, 12, 52, 30, 26, 16, 14, 10, 12, 24]
set_header(ws2, 3, headers, widths)

data = [
    ("K-01", "矛盾あり", "目次→「日次点検」のリンク切れ(実シート名は「日次点検(WIP)」)", "PanaCIM草案", "目次B10", "矛盾あり", "未対応", "", "", "目次側かシート名側かの統一要検討"),
    ("K-02", "矛盾あり", "目次→「記録と文書管理」のリンク切れ(実名「記録と文書管理(削除決定済み。)」)", "PanaCIM草案", "目次B15", "矛盾あり", "未対応", "", "", "削除決定済みシートへのリンク"),
    ("K-03", "矛盾あり", "目次→「チェックシート(日次)」のリンク先シートが存在しない(B1メモ「日時点検は不要」と整合するが目次・リンクが残存)", "PanaCIM草案", "目次B16", "矛盾あり", "未対応", "", "", ""),
    ("K-04", "注意", "DGS起動 A12 に利用者名・パスワードの平文記載(本資料ではマスク表記)", "DGS_P2", "DGS起動A12", "Excel内の記載を確認", "要判断", "", "", "両草案の表紙方針「本文に書かない・値は別紙管理」と対比"),
    ("K-05", "構造実測", "print_area設定は 3/34シートのみ(ダミーコード採番/指示書作成、その他/現場立ち合い)", "DGS_P2", "3シート実測", "構造を実測", "要判断", "", "", "未設定=印刷対象外ではない"),
    ("K-06", "構造実測", "草案2書の print_area=0件・fitToWidth指定なし", "PanaCIM/LNB草案", "全シート実測", "構造を実測", "要判断", "", "", "NR4030様式移行時の印刷設定"),
    ("K-07", "矛盾あり", "「記録と文書管理(削除決定済み。)」シートが残存(B1メモ「ページ自体不要。」+目次に(削除)表示)", "PanaCIM草案", "当該シートB1/目次", "矛盾あり", "未対応", "", "", "意図的併存(会議用)の可能性"),
    ("K-08", "確認", "型名欄「ZZZ-90000(仮)」=仮番運用(付番規則は両草案とも要確認の記載)", "両草案", "表紙r7付近", "Excel内の記載を確認", "未対応", "", "", ""),
    ("K-09", "未確認", "承認欄=要確認・改訂履歴の承認列=未", "両草案", "表紙/改訂履歴", "未取得・未確認", "未対応", "", "", ""),
    ("K-10", "注意", "LNB 申し送り(§15)に認証情報の実態記載(URL平文/HTTP/3ライン同一認証・値自体は本書にも未掲載)", "LNB草案", "申し送り(認証情報)r11-14", "Excel内の記載を確認", "要判断", "", "", "表紙方針と対比"),
    ("K-11", "未確認", "P1の罫線・フォント細部(xlrdで取得不能)", "DGS_P1", "―", "未取得・未確認", "未対応", "", "", "様式分析§9の記載どおり"),
    ("K-12", "未確認", "ZZZ-90000と0494-913473の付番関係", "DGS_P1/草案", "様式分析§9", "未取得・未確認", "未対応", "", "", ""),
    ("K-13", "矛盾あり", "フロー図Z列の➡先と実シート名の不一致(➡PCB編集、CSV出力 vs 実「PCB編集&出力」/➡指示書作成 vs 実「指示書作成、その他」)", "DGS_P2", "試作フローZ77,Z82/新製品Z17,Z42", "矛盾あり", "未対応", "", "", ""),
    ("K-14", "矛盾あり", "➡遷移は文字記載のみ(シート間ハイパーリンク0件実測)のため機械的な追跡は不可", "DGS_P2", "P2 hyperlink実測", "構造を実測", "要判断", "", "", ""),
]
FILL_BY_STATE = {"矛盾あり": FILL_WARN, "未取得・未確認": FILL_GRAY, "Excel内の記載を確認": FILL_OK, "構造を実測": FILL_OK}
r = 4
for row in data:
    put(ws2, r, row)
    ws2.cell(r, 6).fill = FILL_BY_STATE.get(row[5], None)
    ws2.row_dimensions[r].height = 28
    r += 1
last = r - 1
tab = Table(displayName="tbl_issues", ref=f"A3:J{last}")
tab.tableStyleInfo = TableStyleInfo(name="TableStyleLight1", showRowStripes=True)
ws2.add_table(tab)

# ============================================================
# シート3: 根拠一覧(構造実測)
# ============================================================
ws3 = wb.create_sheet("根拠一覧")
ws3.sheet_view.showGridLines = False
ws3["A1"] = "根拠一覧(構造実測・Excel内の記載)"; ws3["A1"].font = F_TITLE
headers3 = ["対象", "項目", "実測値", "測定方法/根拠"]
widths3 = [18, 40, 56, 34]
set_header(ws3, 3, headers3, widths3)
facts = json.load(open(r"C:\Users\ss80751\kohden-code-workspace\20261015_DGS草案可視化\evidence\excel_facts.json", encoding="utf-8"))
p2s = facts["P2"]["sheets"]; pc = facts["PanaCIM"]["sheets"]; ln = facts["LNB"]["sheets"]
rows3 = [
    ("DGS_P1", "シート構成", "1シート(付表1)・管理番号0494-913473・頁1/119・様式NR4030-0100-A3", "xlrd実測"),
    ("DGS_P1", "変更履歴", "変更記号01→02→03(全て書替)・総枚数93→118→119", "xlrd実測(付表1 r31-33)"),
    ("DGS_P2", "シート数", "34シート(はじめに1+フロー4+個別手順29)", "openpyxl実測"),
    ("DGS_P2", "図形・画像", f"図形82+コネクタ63(drawing XML)・画像448参照・media154ファイル(PNG147+JPEG7)", "zip/drawing XML実測"),
    ("DGS_P2", "数式", "15セル全て「=$G$4」(パーツ_マウンタ設定/パーツ_その他設定の題目再掲)", "openpyxl実測"),
    ("DGS_P2", "印刷設定", f"縦{sum(1 for s in p2s if s['orientation']!='landscape')}/横{sum(1 for s in p2s if s['orientation']=='landscape')}・print_area 3/34・rowBreaks 8シート・フッタ「様式 NR4030-0300-A3」", "openpyxl実測"),
    ("DGS_P2", "ハイパーリンク", "シート間0件(➡遷移は文字記載)", "zip/rels実測"),
    ("PanaCIM草案", "シート数", "16シート・版0.11(草案・未検証)・文書番号ZZZ-90000(仮)", "openpyxl実測"),
    ("PanaCIM草案", "目次リンク", "14本・うち切れ3件(B10/B15/B16)", "openpyxl実測"),
    ("PanaCIM草案", "会議メモ", "B1に6件(点検項目次回会議決定/月次内容次回/バックアップ確認/パスワードはリストで一元化/記録と文書管理不要/日次点検不要)", "openpyxl実測"),
    ("PanaCIM草案", "印刷設定", f"横向き{sum(1 for s in pc if s['landscape'])}/16・print_area 0件", "openpyxl実測"),
    ("LNB草案", "シート数", "19シート・版0.9(草案・未検証)", "openpyxl実測"),
    ("LNB草案", "目次リンク", "16本全て有効(切れ0)+各シートG3戻り", "openpyxl実測"),
    ("LNB草案", "期限表", "文書登録=2026-12-28(月)・トライアル開始=2027-01-05(火)", "openpyxl実測(記録と文書管理)"),
    ("LNB草案", "印刷設定", f"横向き{sum(1 for s in ln if s['landscape'])}/19・print_area 0件", "openpyxl実測"),
    ("共通", "認証情報の方針", "両草案の表紙に「認証情報=本文に書かない・値は別紙管理」の記載", "openpyxl実測(表紙r15付近)"),
]
r = 4
for row in rows3:
    put(ws3, r, row, bold_first=True)
    ws3.row_dimensions[r].height = 26
    r += 1

# ============================================================
# シート4-: 図貼付
# ============================================================
page_names = ["Page1_全体構成・目的", "Page2_シート内の内容構成", "Page3_ファイル・シート・項目の関係", "Page4_書式・図形・印刷", "Page5_不整合・未確認事項"]
for i, (png, title) in enumerate(zip(["p1.png","p2.png","p3.png","p4.png","p5.png"], page_names), 1):
    wsx = wb.create_sheet(f"図{i}_{title[:8]}")
    wsx.sheet_view.showGridLines = False
    wsx["A1"] = title; wsx["A1"].font = F_TITLE
    wsx["A2"] = "出典: 分析済みExcel構造関係図.drawio(編集可)・全ページ目視検査済み"; wsx["A2"].font = F_SUB
    img = XLImage(os.path.join(IMGDIR, png))
    scale = 1100 / img.width
    img.width = int(img.width * scale); img.height = int(img.height * scale)
    wsx.add_image(img, "A4")
    wsx.column_dimensions["A"].width = 2

# ============================================================
# シート: 測定方法
# ============================================================
ws5 = wb.create_sheet("測定方法")
ws5.sheet_view.showGridLines = False
ws5["A1"] = "測定方法・再現手順"; ws5["A1"].font = F_TITLE
rows5 = [
    ("実測ツール", "Python 3.13 + xlrd 2.0.2(.xls) + openpyxl 3.1.5(.xlsx) + zipfile(内部XML直読み)"),
    ("原本の扱い", "全て読み取り専用(Read Only)で開き変更なし"),
    ("再現スクリプト", "collect_facts.py(実測JSON取得)・make_drawio.py(drawio生成)"),
    ("実測JSON", "evidence/excel_facts.json(シート構成・リンク・印刷設定・数式・図形統計)"),
    ("図の検証", "静的検査(XML/重なり/はみ出し/端点)PASS・draw.io CLIで全ページPNG書き出し・AI視覚レビュー3回でPASS"),
    ("品質記録", "品質検証レポート.md(検証項目・判定・修正サイクル2回)"),
]
r = 3
for k, v in rows5:
    ws5.cell(r, 1, k).font = F_BOLD
    c = ws5.cell(r, 2, v); c.font = F_B; c.alignment = WRAP
    ws5.merge_cells(start_row=r, start_column=2, end_row=r, end_column=8)
    r += 1
ws5.column_dimensions["A"].width = 18

wb.save(OUT)
print("saved", OUT)
