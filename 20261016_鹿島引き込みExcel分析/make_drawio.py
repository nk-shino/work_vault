# -*- coding: utf-8 -*-
# drawio generator for 差分確認マクロver2.3a analysis
import json, sys, html
sys.stdout.reconfigure(encoding='utf-8')
OUT = r"C:\Users\ss80751\kohden-code-workspace\20261016_鹿島引き込みExcel分析\差分確認マクロ分析.drawio"

RUN_ID = "run-20261016-kashima-hikikomi-01"
REV = "R1"

W, H = 260, 72
GAPX, GAPY = 60, 90

# palette from spec design defaults
C_BG = "#FFFFFF"; C_TEXT = "#243447"; C_ACC = "#426A91"; C_WARN = "#A56A12"; C_CONF = "#B33A3A"
FILL = {"sheet": "#DAE8FC", "documented_entity": "#FFE6CC", "file": "#D5E8D4", "figure": "#E1D5E7"}
BORDER = {"sheet": "#6C8EBF", "documented_entity": "#D79B00", "file": "#82B366", "figure": "#9673A6"}

def esc(s):
    return html.escape(s, quote=True)

cells = []          # (id, value, attrs)
current_id = 100

def add(xml):
    cells.append(xml)

def node(nid, x, y, w, h, label, kind, extra=""):
    label_esc = esc(label)
    add(f'<mxCell id="{nid}" value="{label_esc}" style="rounded=1;whiteSpace=wrap;html=1;fillColor={FILL[kind]};strokeColor={BORDER[kind]};fontColor={C_TEXT};fontSize=12;align=center;verticalAlign=middle;{extra}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')

def note(nid, x, y, w, h, label, color=C_WARN):
    add(f'<mxCell id="{nid}" value="{esc(label)}" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#FFF2CC;strokeColor={color};fontColor={C_TEXT};fontSize=11;align=left;verticalAlign=top;spacing=6;" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')

def title(nid, label):
    add(f'<mxCell id="{nid}" value="{esc(label)}" style="text;html=1;fontSize=24;fontColor={C_TEXT};align=left;verticalAlign=middle;" vertex="1" parent="1"><mxGeometry x="40" y="20" width="1100" height="36" as="geometry"/></mxCell>')

def subtitle(nid, label):
    add(f'<mxCell id="{nid}" value="{esc(label)}" style="text;html=1;fontSize=13;fontColor=#666666;align=left;verticalAlign=middle;" vertex="1" parent="1"><mxGeometry x="40" y="58" width="1100" height="22" as="geometry"/></mxCell>')

def legend(x, y):
    items = [("sheet(シート)", "sheet"), ("file(ファイル)", "file"), ("documented_entity(連携先・VBA)", "documented_entity"), ("figure(リボン)", "figure")]
    ly = y
    add(f'<mxCell id="LEGEND" value="凡例" style="text;html=1;fontSize=12;fontStyle=1;fontColor={C_TEXT};" vertex="1" parent="1"><mxGeometry x="{x}" y="{ly}" width="200" height="20" as="geometry"/></mxCell>')
    for i, (lbl, kind) in enumerate(items):
        yy = ly + 26 + i * 30
        add(f'<mxCell id="LG{i}" value="" style="rounded=1;fillColor={FILL[kind]};strokeColor={BORDER[kind]};" vertex="1" parent="1"><mxGeometry x="{x}" y="{yy}" width="26" height="18" as="geometry"/></mxCell>')
        add(f'<mxCell id="LGt{i}" value="{esc(lbl)}" style="text;html=1;fontSize=11;fontColor={C_TEXT};align=left;" vertex="1" parent="1"><mxGeometry x="{x+34}" y="{yy}" width="220" height="18" as="geometry"/></mxCell>')
    add(f'<mxCell id="LEGs" value="" style="endArrow=block;html=1;strokeColor={C_ACC};" edge="1" parent="1"><mxGeometry relative="1" as="geometry"><mxPoint x="{x}" y="{ly+26+4*30+14}" as="sourcePoint"/><mxPoint x="{x+26}" y="{ly+26+4*30+14}" as="targetPoint"/></mxGeometry></mxCell>' )
    add(f'<mxCell id="LEGst" value="確認済みの参照・連携" style="text;html=1;fontSize=11;fontColor={C_TEXT};align=left;" vertex="1" parent="1"><mxGeometry x="{x+34}" y="{ly+26+4*30+5}" width="220" height="18" as="geometry"/></mxCell>')

def edge(eid, src, dst, label, style_extra="", dashed=False):
    d = ";dashed=1" if dashed else ""
    add(f'<mxCell id="{eid}" value="{esc(label)}" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor={C_ACC};strokeWidth=1.5;fontSize=11;fontColor={C_TEXT};labelBackgroundColor=#FFFFFF;{style_extra}{d}" edge="1" parent="1" source="{src}" target="{dst}"><mxGeometry relative="1" as="geometry"/></mxCell>')

# ============ page frames ============
def page_begin(pid, name):
    add(f'<diagram id="{pid}" name="{esc(name)}">')
    add('<mxGraphModel dx="1200" dy="800" grid="1" gridSize="8" page="1" pageWidth="1169" pageHeight="826" math="0" shadow="0"><root>')
    add('<mxCell id="0"/><mxCell id="1" parent="0"/>')

def page_end():
    add('</root></mxGraphModel></diagram>')

cells.clear()
add(f'<!-- run_id={RUN_ID} delivery_revision={REV} -->')

# ---------------- PG-01 overview ----------------
page_begin("PG-01", "1_全体構成と目的")
title("PG1-T", "差分確認マクロver2.3a.xlsm — 全体構成と目的")
subtitle("PG1-ST", f"実行ID {RUN_ID} / 納品版 {REV} / 2026-10-16 分析")

# center file node
node("PG1_OBJ01", 460, 200, 280, 60, "差分確認マクロver2.3a.xlsm", "file")
note("PG1_N1", 460, 280, 280, 96,
     "目的: BOSS(基板発注)とSMT(実装)の\n部品差分を指図単位で確認する。\n\n sabun.csv 取込 → 差分nシートで照合\n → NG行をシステムへ確認 → 計画nで完了記録", C_ACC)

# external
node("PG1_OBJ09", 60, 200, 220, 56, "sabun.csv\n\\\\nksv523\\...\\Job作成", "documented_entity")
node("PG1_OBJ10", 60, 330, 220, 56, "差分チェックシステム\nsashizu.cgi", "documented_entity")
node("PG1_OBJ11", 890, 200, 230, 56, "段取り予定.xlsx\n(SharePoint)", "documented_entity")
node("PG1_OBJ12", 890, 330, 230, 56, "JOB作成関連マクロ\n→TOOL.xlam", "documented_entity")
node("PG1_OBJ13", 890, 460, 230, 56, "差分確認手順書.xlsx", "documented_entity")
node("PG1_OBJ14", 60, 460, 220, 56, "nksv523版コピー\n(同一ブック)", "documented_entity")

edge("PG1_E1", "PG1_OBJ09", "PG1_OBJ01", "取込(既定パス)", "exitX=1;exitY=0.5;entryX=0;entryY=0.5;")
edge("PG1_E2", "PG1_OBJ11", "PG1_OBJ01", "ジョブ・指図転記(input)", "exitX=0;exitY=0.5;entryX=1;entryY=0.5;")
edge("PG1_E3", "PG1_OBJ01", "PG1_OBJ10", "NG行リンク(J列)", "exitX=0;exitY=0.75;entryX=1;entryY=0.5;", )
edge("PG1_E4", "PG1_OBJ01", "PG1_OBJ12", "差分チェックn.csv出力", "exitX=1;exitY=0.75;entryX=0;entryY=0.5;")
edge("PG1_E5", "PG1_OBJ13", "PG1_OBJ01", "運用手順を説明", "exitX=0;exitY=0.5;entryX=1;entryY=0.9;dashed=1")
edge("PG1_E6", "PG1_OBJ14", "PG1_OBJ01", "2拠点コピー(内容ほぼ一致)", "exitX=1;exitY=0.5;entryX=0;entryY=0.9;dashed=1;strokeColor=#B33A3A")

note("PG1_N2", 60, 620, 1060, 60,
     "内部構成: sabun(非表示・差分元) / BOM作成 / 差分1-6・計画1-6(対) / 差分x・計画x(複製元・非表示) / リボン「差分チェック」 / VBA 19モジュール。\n詳細は p2 シート構成、p3 連携の流れ、p4 不整合・未確認。", C_ACC)
legend(920, 540)
page_end()

# ---------------- PG-02 content structure ----------------
page_begin("PG-02", "2_シート構成とデータ内容")
title("PG2-T", "シート構成とデータ内容")
subtitle("PG2-ST", "16シート。差分n/計画n が番号対応ペア。数式は sabun シートを一意の参照先とする。")

# workbook container
add(f'<mxCell id="PG2_BOX" value="差分確認マクロver2.3a.xlsm (16シート)" style="rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor={C_TEXT};fontSize=13;fontStyle=1;verticalAlign=top;align=left;spacing=8;" vertex="1" parent="1"><mxGeometry x="40" y="100" width="820" height="640" as="geometry"/></mxCell>')

node("PG2_OBJ02", 70, 150, 250, 88, "sabun (非表示)\n差分元データ173行\n指図/担当/品目/PCB/台数/日付×3/タイプ/差分\nOK100 NG10 DONE16 空47", "sheet")
node("PG2_OBJ04", 70, 280, 250, 88, "差分1-6 (表示)\n指図別チェック表 100行\nB..J=INDEX(sabun!X,MATCH(A))\nD=PCB名整形(LET/REGEXREPLACE)", "sheet")
node("PG2_OBJ05", 70, 410, 250, 88, "計画1-6 (表示)\n指図完了記録 107行\nA=指図 B=完了日時\nC=「はい/いいえ」自動判定", "sheet")
node("PG2_OBJ06", 70, 540, 250, 88, "差分x / 計画x (非表示)\n複製元テンプレート\n7ジョブ超時に差分7..として複製", "sheet")
node("PG2_OBJ03", 400, 150, 220, 88, "BOM作成\nAsprova用 製造BOMテンプレ\n2ブロック(15行/28行)\n実装-1/実装-2/外観検査-1", "sheet")
node("PG2_OBJ07", 400, 280, 220, 60, "リボン「差分チェック」\nクリア/取込/S1-6/input/output", "figure")
node("PG2_OBJ08", 400, 400, 220, 98, "VBA 19モジュール\nModule1: 取込/出力/クリア/リンク\ntools: ペア辞書/テンプレ/書式\n指図入力: do_prepare\n各シート: 変更イベント", "documented_entity")

# status side notes
note("PG2_N1", 670, 150, 180, 88, "sabun タイプ内訳\nZP21=169 ZP56=2\nZP11=1 ZP12=1\n製造開始日 6/17-7/24", C_ACC)
note("PG2_N2", 670, 280, 180, 120, "計画シート C列判定\n(キャッシュ値)\n計画1: はい59/いいえ48\n計画2: 79/28  計画3: 74/33\n計画4: 72/35  計画5: 69/38\n計画6: 30/37", C_ACC)
note("PG2_N3", 670, 440, 180, 96, "条件付き書式(差分n J列)\nDONE=緑系 / NG=赤太字\nNG行にシステムへの\nハイパーリンク(保存時0件)", C_WARN)
note("PG2_N4", 400, 540, 450, 60, "BOM作成の注記「28秒以下は、28で入れる」/ サイクルタイム入力セル(E15=28, F15=面数)\n画像2枚: Asprova画面の操作例(製造BOMテーブル)", C_WARN)

edge("PG2_E9", "PG2_OBJ02", "PG2_OBJ04", "INDEX/MATCH", "exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
edge("PG2_E10", "PG2_OBJ02", "PG2_OBJ05", "C列判定", "exitX=0.5;exitY=1;entryX=0.5;entryY=0;dashed=1")
edge("PG2_E11", "PG2_OBJ04", "PG2_OBJ05", "番号対応ペア", "exitX=0.5;exitY=1;entryX=0.5;entryY=0;startArrow=block;startFill=1;")
edge("PG2_E12", "PG2_OBJ06", "PG2_OBJ04", "複製元", "exitX=0.5;exitY=0;entryX=0.5;entryY=1;dashed=1")
edge("PG2_E16", "PG2_OBJ07", "PG2_OBJ08", "onAction", "exitX=0.5;exitY=1;entryX=0.5;entryY=0;")

add(f'<mxCell id="PG2_E23_lbl" value="テンプレ2ブロック(1-15行/18-28行)" style="text;html=1;fontSize=10;fontColor={C_TEXT};" vertex="1" parent="1"><mxGeometry x="445" y="245" width="220" height="16" as="geometry"/></mxCell>')
page_end()

# ---------------- PG-03 relationships ----------------
page_begin("PG-03", "3_参照と連携の流れ")
title("PG3-T", "参照と連携の流れ")
subtitle("PG3-ST", "取込 → 照合 → 完了記録 → 出力。すべての数式参照は sabun シート経由。")

node("PG3_OBJ09", 60, 180, 230, 60, "sabun.csv\n(差分チェックシステム由来)", "documented_entity")
node("PG3_OBJ02", 360, 180, 240, 60, "sabunシート (S0_1)\n9列一括書込", "sheet")
node("PG3_OBJ04", 360, 330, 240, 76, "差分1-6シート\nA列=ジョブ名+指図\nB..J=INDEX/MATCH", "sheet")
node("PG3_OBJ05", 700, 330, 240, 76, "計画1-6シート\nA=指図 B=完了日時\nC=はい/いいえ", "sheet")
node("PG3_OBJ11", 60, 330, 230, 60, "段取り予定.xlsx\njob作成シート", "documented_entity")
node("PG3_OBJ08", 360, 500, 240, 76, "VBA\n差分NGにリンク貼る / S1_2再生成\ndo_prepare / output / SashizuClear", "documented_entity")
node("PG3_OBJ10", 700, 500, 240, 60, "差分チェックシステム\nsashizu.cgi", "documented_entity")
node("PG3_OBJ18", 700, 180, 240, 60, "差分チェックn.csv\n(ブック同フォルダへ出力)", "file")

edge("PG3_E8", "PG3_OBJ09", "PG3_OBJ02", "①差分データ取込\n(Asprova有無で既定パス切替)", "exitX=1;exitY=0.5;entryX=0;entryY=0.5;")
edge("PG3_E15", "PG3_OBJ11", "PG3_OBJ04", "②input: ジョブ名を正規表現選択→指図転記", "exitX=1;exitY=0.5;entryX=0;entryY=0.25;")
edge("PG3_E9", "PG3_OBJ02", "PG3_OBJ04", "③照合 INDEX/MATCH", "exitX=0.5;exitY=1;entryX=0.5;entryY=0;")
edge("PG3_E17", "PG3_OBJ08", "PG3_OBJ04", "NG行リンク再生成\nシート変更イベント", "exitX=0.5;exitY=0;entryX=0.5;entryY=1;")
edge("PG3_E10", "PG3_OBJ02", "PG3_OBJ05", "C列 判定参照", "exitX=0.25;exitY=1;entryX=0.25;entryY=0;dashed=1")
edge("PG3_E11", "PG3_OBJ04", "PG3_OBJ05", "④完了記録(ペア)", "exitX=1;exitY=0.5;entryX=0;entryY=0.5;startArrow=block;startFill=1;")
edge("PG3_E14", "PG3_OBJ04", "PG3_OBJ10", "⑤NG行をシステムで確認", "exitX=0.5;exitY=1;entryX=0.5;entryY=0;strokeColor=#A56A12")
edge("PG3_E18", "PG3_OBJ04", "PG3_OBJ18", "⑥output: CSV出力", "exitX=1;exitY=0.25;entryX=0.5;entryY=1;")

note("PG3_N1", 60, 620, 880, 92,
     "補足\n・BOM作成シートは独立(Asprova手動登録用テンプレート。画像で操作例を提示)。\n・計画シートのC列数式は、シート変更のたびにVBA(S1_2系)が A列が空になる行まで自動再書込する。\n・差分nと計画nのペアは tools.getDic() がシート名の番号で結合する。7ジョブ超時は 差分x/計画x を複製して拡張。", C_ACC)
page_end()

# ---------------- PG-04 issues ----------------
page_begin("PG-04", "4_不整合と未確認事項")
title("PG4-T", "不整合と未確認事項")
subtitle("PG4-ST", "ISS-01〜07。全て今回の直接確認に基づく。対応判断は対象ブックの管理者。")

rows = [
 ("ISS-01", "medium", "Work_Vault版とnksv523版で BOM作成!B15 が不一致(UR-4567 / UR-4658)。他のセル・VBAソースは一致。", "#B33A3A"),
 ("ISS-02", "info", "nksv523版の Module1 p-codeのみ相違(ソース同一)。保存環境差の可能性、動作差は未確認。", "#A56A12"),
 ("ISS-03", "info", "sabunシート(173行・6/30以前)と sabun.csv(200行・10/16)の指図集合が不一致。シートは取込時点のスナップショット。", "#A56A12"),
 ("ISS-04", "low", "差分1-5のJ列にNG6指図があるが、保存状態のハイパーリンクは0件(リンク付与マクロ未実行の状態で保存)。", "#A56A12"),
 ("ISS-05", "low", "計画2の230-264行D列に旧タイムスタンプ16件が残存(A列が空のためVBA消去対象外)。", "#A56A12"),
 ("ISS-06", "info", "名前定義 _xlpm.s が #NAME? で残存(LET引数名由来)。", "#A56A12"),
 ("ISS-07", "info", "段取り予定.xlsx・差分チェックシステムの実体は今回未確認(SharePoint/社内システムのため)。", "#A56A12"),
]
y = 110
for iid, sev, txt, col in rows:
    h = 64
    add(f'<mxCell id="PG4_{iid}" value="{esc(iid + "  [" + sev + "]")}" style="rounded=0;whiteSpace=wrap;html=1;fillColor={col};strokeColor=none;fontColor=#FFFFFF;fontSize=12;fontStyle=1;verticalAlign=middle;" vertex="1" parent="1"><mxGeometry x="60" y="{y}" width="110" height="{h}" as="geometry"/></mxCell>')
    add(f'<mxCell id="PG4_{iid}_t" value="{esc(txt)}" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#F5F5F5;strokeColor=#CCCCCC;fontColor={C_TEXT};fontSize=12;align=left;spacing=8;" vertex="1" parent="1"><mxGeometry x="170" y="{y}" width="950" height="{h}" as="geometry"/></mxCell>')
    y += h + 16

note("PG4_N1", 60, y + 10, 1060, 70,
     "未確認事項の扱い: 上記は「不存在」ではなく「今回の範囲で確認できなかった」ことを示す。\nマクロ実行・数式再計算・外部リンク更新は本分析では行っていない(安全則)。", C_CONF)
page_end()

xml = '<mxfile host="Electron" modified="2026-10-16T00:00:00.000Z" agent="analysis" version="24.0.0">' + "".join(cells) + "</mxfile>"
open(OUT, "w", encoding="utf-8").write(xml)
print("written:", OUT, len(xml), "bytes")
