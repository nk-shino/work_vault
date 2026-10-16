# -*- coding: utf-8 -*-
# 負荷計算の処理内容 drawio generator (3 process regions + formulas + glossary)
import html, sys
sys.stdout.reconfigure(encoding='utf-8')

OUT = r"C:\Users\ss80751\kohden-code-workspace\20261016_鹿島引き込みExcel分析\負荷計算の処理内容.drawio"

C_TEXT = "#243447"
# process colors
BLUE   = ("#DAE8FC", "#6C8EBF")   # 処理1 スロット容量
GREEN  = ("#D5E8D4", "#82B366")   # 処理2 時間負荷
PURPLE = ("#E1D5E7", "#9673A6")   # 処理3 Asprova
YELLOW = ("#FFF2CC", "#D6B656")   # データ源
GRAY   = ("#F5F5F5", "#999999")   # 出力
RED    = ("#F8CECC", "#B85450")   # 注意・未確認
TINT   = {"blue": "#F3F7FC", "green": "#F4FAF4", "purple": "#F9F4FA", "yellow": "#FEFBF0"}

def esc(s):
    return html.escape(s, quote=True)

def lbl(s):
    return esc(s).replace("\n", "&lt;br&gt;")

cells = []
def add(x):
    cells.append(x)

def node(nid, x, y, w, h, label, fill, stroke, fs=12, bold=False, extra=""):
    fb = "fontStyle=1;" if bold else ""
    add(f'<mxCell id="{nid}" value="{lbl(label)}" style="rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};fontColor={C_TEXT};fontSize={fs};{fb}{extra}" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')

def mono(nid, x, y, w, h, label, fill="#FFFFFF", stroke="#666666", fs=13):
    add(f'<mxCell id="{nid}" value="{lbl(label)}" style="rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};fontColor={C_TEXT};fontSize={fs};fontFamily=Courier New;align=left;spacing=10;verticalAlign=middle;" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')

def plain(nid, x, y, w, h, label, fs=11, align="left"):
    add(f'<mxCell id="{nid}" value="{lbl(label)}" style="text;html=1;fontSize={fs};fontColor={C_TEXT};align={align};verticalAlign=top;whiteSpace=wrap;spacing=2;" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')

def region(nid, x, y, w, h, header, tint, color, fs=15):
    add(f'<mxCell id="{nid}" value="" style="rounded=1;arcSize=3;whiteSpace=wrap;html=1;fillColor={tint};strokeColor={color};strokeWidth=2;dashed=0;verticalAlign=top;" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
    add(f'<mxCell id="{nid}_h" value="{lbl(header)}" style="rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor={color};strokeColor={color};fontColor=#FFFFFF;fontSize={fs};fontStyle=1;align=left;spacingLeft=14;verticalAlign=middle;" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="40" as="geometry"/></mxCell>')

def edge(eid, src, dst, label="", color="#666666", dashed=False, sw=1.5, fs=10):
    d = ";dashed=1" if dashed else ""
    add(f'<mxCell id="{eid}" value="{lbl(label)}" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;strokeColor={color};strokeWidth={sw};fontSize={fs};fontColor={C_TEXT};labelBackgroundColor=#FFFFFF;{d}" edge="1" parent="1" source="{src}" target="{dst}"><mxGeometry relative="1" as="geometry"/></mxCell>')

def gterm(nid, x, y, wterm, wtxt, term, desc, color):
    node(nid + "_t", x, y, wterm, 44, term, "#FFFFFF", color, fs=11, bold=True)
    plain(nid + "_d", x + wterm + 6, y, wtxt, 44, desc, fs=10)

def title(nid, label):
    plain(nid, 40, 18, 1090, 34, label, fs=22)

def subtitle(nid, label):
    plain(nid, 40, 54, 1090, 22, label, fs=12)

def srcnote(nid, x, y, w, label):
    add(f'<mxCell id="{nid}" value="{lbl(label)}" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#CCCCCC;fontColor=#666666;fontSize=10;align=left;spacing=6;verticalAlign=top;" vertex="1" parent="1"><mxGeometry x="{x}" y="{y}" width="{w}" height="52" as="geometry"/></mxCell>')

def page_begin(pid, name):
    add(f'<diagram id="{pid}" name="{esc(name)}">')
    add('<mxGraphModel dx="1200" dy="800" grid="1" gridSize="8" page="1" pageWidth="1169" pageHeight="826" math="0" shadow="0"><root>')
    add('<mxCell id="0"/><mxCell id="1" parent="0"/>')

def page_end():
    add('</root></mxGraphModel></diagram>')

add('<!-- 負荷計算の処理内容 / 2026-10-16 / 根拠: TOOL.xlam・BOSS計画.xlsm・差分確認マクロver2.3a.xlsm VBA復号 -->')

# ================= PG-01 全体像 =================
page_begin("LOAD-01", "1_全体像と色分け")
title("L1_T", "負荷計算の処理内容 — 全体像")
subtitle("L1_ST", "「ジョブ作成なら容量に収まる」は3系統の計算とAsprovaの割付け調整で成り立つ。色=処理の種別。数値は全てコード・ブックから確認済み。")

# data sources (yellow) left
node("L1_DGS", 40, 120, 240, 74, "DGS データ作成ジェエティタ\n実装条件作成(機種別CT・CPH)\n赤セル=ラインのネック機種", *YELLOW, fs=11)
node("L1_ACC", 40, 230, 240, 64, "部品リスト.accdb\negproBOM × PartList\n(nksv523\\Job作成)", *YELLOW, fs=11)
node("L1_MY", 40, 330, 240, 74, "MySQL nksv1359\nQCD.CycleTime_Points(CT実績)\nscheduled(数量・組取り数)", *YELLOW, fs=11)
node("L1_BOM", 40, 440, 240, 74, "差分確認マクロ BOM作成シート\nE=CT秒(28下限) N=sp O=効率\n→ Asprova製造BOMの元", *YELLOW, fs=11)

# middle processes
region("L1_R1", 350, 110, 330, 110, "処理1 スロット容量判定", TINT["blue"], BLUE[1])
mono("L1_F1", 366, 158, 298, 54, "Σフィーダーサイズ ≤ 390\n(90 + 300)", "#FFFFFF", BLUE[1], fs=12)

region("L1_R2", 350, 250, 330, 110, "処理2 時間負荷計算", TINT["green"], GREEN[1])
mono("L1_F2", 366, 298, 298, 54, "工数(h)=(数量×CT+600)\n÷3600 ÷0.7", "#FFFFFF", GREEN[1], fs=12)

region("L1_R3", 350, 390, 330, 110, "処理3 Asprova割付け", TINT["purple"], PURPLE[1])
mono("L1_F3", 366, 438, 298, 54, "作業時間=数量×sp÷製造効率\n+段取10m → カレンダー内へ", "#FFFFFF", PURPLE[1], fs=12)

node("L1_CSV", 40, 560, 240, 50, "DGS出力CSV\n(サイクルタイム/部品/フィーダー/ノズル)", *YELLOW, fs=10)

# outputs right (gray)
node("L1_O1", 780, 120, 320, 74, "空きスロット表示\n【ALL】x/390・3Noz x/90・Other x/300\nテーブル禁止推奨数 T(安全率0.8)", *GRAY, fs=11)
node("L1_O2", 780, 250, 320, 74, "計算シート(日付×グループ工数)\n+各グループ停止時間\n→ 日次の枠と照合", *GRAY, fs=11)
node("L1_O3", 780, 390, 320, 74, "Asprova ガントチャート\n資源カレンダー内に割付け\n入らない→順延・代替資源", *GRAY, fs=11)

edge("L1_E0", "L1_DGS", "L1_CSV", "CSV出力", "#666666")
edge("L1_E1", "L1_CSV", "L1_MY", "TOOL.xlamが\nMySQLへ登録", "#666666")
edge("L1_E2", "L1_ACC", "L1_R1", "フィーダーサイズ", BLUE[1])
edge("L1_E3", "L1_MY", "L1_R2", "最新10指図の\n実績平均CT", GREEN[1])
edge("L1_E4", "L1_BOM", "L1_R3", "sp・製造効率", PURPLE[1])
edge("L1_E5", "L1_R1", "L1_O1", "", BLUE[1])
edge("L1_E6", "L1_R2", "L1_O2", "", GREEN[1])
edge("L1_E7", "L1_R3", "L1_O3", "", PURPLE[1])

plain("L1_N1", 780, 480, 320, 90, "ポイント\n処理1は物理判定(部品×フィーダーサイズ)。処理2は時間判定(実績CT)。処理3は割付け調整。「超えない」は判定後の自動調整の結果。", fs=11)

# legend
plain("L1_LG0", 40, 640, 200, 20, "色分け凡例", fs=12)
lg = [("処理1 スロット容量判定", *BLUE), ("処理2 時間負荷計算", *GREEN), ("処理3 Asprova割付け", *PURPLE), ("データ源", *YELLOW), ("出力・結果", *GRAY), ("注意・未確認", *RED)]
for i, (t, f, s) in enumerate(lg):
    xx = 40 + (i % 3) * 200
    yy = 664 + (i // 3) * 30
    node(f"L1_LG{i}a", xx, yy, 24, 16, "", f, s, fs=8)
    plain(f"L1_LG{i}b", xx + 30, yy, 170, 18, t, fs=10)
page_end()

# ================= PG-02 処理1 =================
page_begin("LOAD-02", "2_処理1_スロット容量判定")
title("L2_T", "処理1 スロット容量判定 — 部品がフィーダーに載るか")
subtitle("L2_ST", "実行タイミング: ジョブ作成時(TOOL.xlam 部品確認ボタン)と BOSS取込時(BOSS計画.xlsm)。両方とも同一ロジック。")

region("L2_R", 40, 90, 1090, 600, "処理1 スロット容量判定", TINT["blue"], BLUE[1])

plain("L2_SH", 56, 146, 280, 22, "手順", fs=13)
steps = [
    "① 品目ごとに部品リスト.accdbから\n部品名・ノズル・フィーダーサイズを取得\n(egproBOM×PartList / 部品は重複なく1回)",
    "② ノズル欄に1000超の番号がある部品を\n3ノズルヘッド用として集計を分離",
    "③ フィーダーサイズを合計\n= 必要スロット数",
    "④ 上限と比較\n3ノズルヘッド用 90 / その他 300 / 合計 390",
    "⑤ 空きスロットを表示\n【ALL】x/390・3Noz x/90・Other x/300",
]
yy = 172
for i, s in enumerate(steps):
    node(f"L2_S{i}", 56, yy, 290, 66, s, "#FFFFFF", BLUE[1], fs=10, extra="align=left;spacing=6;")
    yy += 74

plain("L2_FH", 380, 146, 340, 22, "計算ロジック", fs=13)
mono("L2_F1", 380, 172, 340, 74, "必要スロット(3Nzl)\n  = Σフィーダーサイズ(ノズル>1000の部品)\n必要スロット(Other)\n  = Σフィーダーサイズ(上記以外)", "#FFFFFF", BLUE[1], fs=11)
mono("L2_F2", 380, 258, 340, 66, "判定: 3Nzl ≤ 90\n      Other ≤ 300\n      合計 ≤ 390", "#FFFFFF", BLUE[1], fs=11)
mono("L2_F3", 380, 336, 340, 96, "テーブル禁止推奨数 T:\n非共有スロット ≥ 150×0.8(=120) → T+1\n   以下 180/210/240/270 で同様に+1\n優先度: T8 > T6 > T4 > T2 > T10", "#FFFFFF", BLUE[1], fs=11)
plain("L2_FN", 380, 444, 340, 60, "Tは「他ジョブと共有しない部品」が増えたとき、使うべきでないテーブル数の推奨。スロット本体の合否判定には0.8は関与しない。", fs=10)

node("L2_DB", 380, 518, 340, 60, "照会先DB\n\\\\nksv523...\\Job作成\\部品リスト.accdb\negproBOM(品目→部品) × PartList(部品→サイズ)", *YELLOW, fs=10)
edge("L2_E9", "L2_DB", "L2_F1", "照会", BLUE[1])

plain("L2_GH", 760, 146, 360, 22, "計算ロジック内の言葉の説明", fs=13)
gt = [
    ("フィーダーサイズ", "部品1種が供給装置(フィーダー)で\n占める幅。PartListが保持"),
    ("ノズル番号>1000", "3ノズルヘッド機の専用部品の目印。\nこの番号で集計を分ける"),
    ("90 / 300 / 390", "スロット上限。3ノズルヘッド用90・\nその他300・合計390"),
    ("非共有スロット", "選択品目群が他ジョブと共有しない\n部品のスロット数(専用分)"),
    ("0.8", "テーブル禁止判定だけに使う安全率。\n150〜270に乗算した値と比較"),
]
yy = 172
for i, (t, d) in enumerate(gt):
    gterm(f"L2_G{i}", 760, yy, 110, 240, t, d, BLUE[1])
    yy += 52

node("L2_O", 56, 572, 290, 66, "結果の使われ方\nBOSS取込時は計算シートの「フリー容量」列へ書込。\n空きが負(オーバー)なら載せ替えが必要。", *GRAY, fs=10)

srcnote("L2_SRC", 56, 636, 1074, "出所: TOOL.xlam BuhinKakunin_ADO(tool_vba.txt:3759-3944・表示:3939-3942) / BOSS計画.xlsm Cal_Capa(vba_code_all.txt:573-663) / テーブル禁止判定 x=0.8(tool_vba.txt:3921-3927)")
page_end()

# ================= PG-03 処理2 =================
page_begin("LOAD-03", "3_処理2_時間負荷計算")
title("L3_T", "処理2 時間負荷計算 — その日の中に収まるか")
subtitle("L3_ST", "BOSS計画.xlsm chkTime / getBOSS_btn。サイクルタイムは実績平均(DGS最速値ではない)。")

region("L3_R", 40, 90, 1090, 600, "処理2 時間負荷計算", TINT["green"], GREEN[1])

plain("L3_FH", 56, 146, 560, 22, "計算ロジック(メイン)", fs=13)
mono("L3_F1", 56, 172, 560, 56, "工数(h) = ( ①数量 × ②CT + ③600秒 ) ÷ ④3600 ÷ ⑤0.7", "#FFFFFF", GREEN[1], fs=14)
mono("L3_F2", 56, 240, 560, 60, "⑤の方向に注意: ÷0.7 は工数を約1.43倍に膨らませる。\n×0.7(縮める)の実装はコード内に存在しない。", "#FFFFFF", RED[1], fs=11)

plain("L3_CH", 56, 312, 560, 22, "②CT(サイクルタイム)の決め方", fs=13)
node("L3_C1", 56, 338, 260, 60, "MySQL QCD.CycleTime_Points\nから品目×表裏ごとに\n最新10指図を取得", *YELLOW, fs=10)
node("L3_C2", 356, 338, 120, 60, "CT<28 →\n28に補正", *YELLOW, fs=10)
node("L3_C3", 496, 338, 120, 60, "表裏それぞれ\n平均", *YELLOW, fs=10)
node("L3_C4", 356, 410, 260, 44, "表+裏を合計=品目のCT", *YELLOW, fs=10)
edge("L3_E1", "L3_C1", "L3_C2", "", GREEN[1])
edge("L3_E2", "L3_C2", "L3_C3", "", GREEN[1])
edge("L3_E3", "L3_C3", "L3_C4", "", GREEN[1])

plain("L3_AH", 56, 468, 560, 22, "CTがDBに無い品目の代替ロジック", fs=13)
mono("L3_F3", 56, 494, 560, 96, "組取り数あり: 数量 ÷ 組取り数 × 56(量産)/75(試作) + 600\n組取り数なし: 数量 × 56(量産)/75(試作) + 600\nどちらも無い: 数量 × 28 + 600 → ★印でリストに残す", "#FFFFFF", GREEN[1], fs=11)

plain("L3_SH", 656, 146, 460, 22, "手順(集約まで)", fs=13)
sst = [
    "⑥ 品目ごとに工数を算出(上記ロジック)",
    "⑦ 計算シートに日付×グループで書込\n(フリー/L1-L3試作/TEC-5600/TEC-1000/送信機/AED)",
    "⑧ グループごとの停止時間と合算し\n日次の枠と照合",
    "※ 同じ数式が getBOSS_btn にも重複実装\n(ソース内に「超注意」の注記あり)",
]
yy = 172
for i, s in enumerate(sst):
    node(f"L3_S{i}", 656, yy, 460, 54, s, "#FFFFFF", GREEN[1], fs=10, extra="align=left;spacing=6;")
    yy += 62

plain("L3_GH", 656, 424, 460, 22, "計算ロジック内の言葉の説明", fs=13)
gt = [
    ("① 数量", "指図の生産台数(MySQL scheduled\nliveOrder.orderQty)"),
    ("② CT", "1台当たりの実績生産秒数。\n最新10指図の平均。DGS最速値ではない"),
    ("③ 600秒", "1指図あたりの段取時間(10分)。\n指図ごとに必ず加算"),
    ("④ 3600", "秒 → 時間への換算"),
    ("⑤ 0.7", "安全率。÷して約1.43倍に膨らませ、\n計画に余裕を持たせる方向"),
    ("組取り数", "1回の部品組取りで生産できる台数。\nMySQL scheduled.unitInfo.chldID"),
    ("28秒", "CTの下限。短すぎる実績値の補正。\n処理3のBOMシートと共通の規則"),
]
yy = 450
for i, (t, d) in enumerate(gt):
    gterm(f"L3_G{i}", 656, yy, 96, 358, t, d, GREEN[1])
    yy += 34

srcnote("L3_SRC", 56, 636, 1074, "出所: BOSS計画.xlsm chkTime(vba_code_all.txt:486-567・代替値56/75は502-504・★は544) / getBOSS_btn(:835-861) / パワークエリ(pq_extract/Formulas_Section1.m:4-7 ROW_NUMBER<=10・28補正)")
page_end()

# ================= PG-04 処理3 =================
page_begin("LOAD-04", "4_処理3_Asprova割付け")
title("L4_T", "処理3 Asprova割付け — 容量を超えない仕組み")
subtitle("L4_ST", "「超えない」は事前の合否判定ではなく、カレンダー内へ割付ける調整の結果。")

region("L4_R", 40, 90, 1090, 600, "処理3 Asprova割付け", TINT["purple"], PURPLE[1])

plain("L4_FH", 56, 146, 560, 22, "計算ロジック", fs=13)
mono("L4_F1", 56, 172, 560, 56, "作業時間 = ①数量 × ②sp ÷ ③製造効率 + ④段取10m", "#FFFFFF", PURPLE[1], fs=14)
mono("L4_F2", 56, 240, 560, 60, "②sp = CT ÷ 面数(表裏)\n   BOM作成シートN列 =($E$15/$F$15)&\"sp\" (単位 sp=秒/個)", "#FFFFFF", PURPLE[1], fs=11)
mono("L4_F3", 56, 312, 560, 60, "③製造効率 = UseBomInst_ProductionFactor\n   SMT 0.7 / 外観検査 0.5 → 0.7なら実時間の約1.43倍を計上", "#FFFFFF", PURPLE[1], fs=11)

plain("L4_WH", 56, 388, 560, 22, "割付けの流れ", fs=13)
node("L4_W1", 56, 414, 170, 66, "製造BOM\n(テーブル要素)\nBOMシートから手作業で追加", "#FFFFFF", PURPLE[1], fs=10)
node("L4_W2", 254, 414, 170, 66, "オーダー(指図)\n数量・期日", *YELLOW, fs=10)
node("L4_W3", 452, 414, 164, 66, "作業時間を計算\n(上記ロジック)", "#FFFFFF", PURPLE[1], fs=10)
node("L4_W4", 452, 508, 164, 66, "資源カレンダーの\n空きへ割付け", "#FFFFFF", PURPLE[1], fs=10)
node("L4_W5", 254, 508, 170, 66, "入らない場合\n順延 / 代替資源へ", *GRAY, fs=10)
edge("L4_E1", "L4_W1", "L4_W3", "", PURPLE[1])
edge("L4_E2", "L4_W2", "L4_W3", "", PURPLE[1])
edge("L4_E3", "L4_W3", "L4_W4", "", PURPLE[1])
edge("L4_E4", "L4_W4", "L4_W5", "収まらないとき", PURPLE[1], dashed=True)

plain("L4_N1", 56, 592, 560, 60, "BOM作成シートの共通規則: E列CTは28秒下限(13行目注記「28秒以下は、28で入れる」)。\n処理2のパワークエリと同じ28秒。CTの転記経路(手作業/リンク)は今回未確認。", fs=10)

plain("L4_GH", 656, 146, 460, 22, "計算ロジック内の言葉の説明", fs=13)
gt = [
    ("① 数量", "指図の生産台数"),
    ("② sp(秒/個)", "1個当たりの製造時間=CT÷面数。\n表裏2面ならCTを2で割る"),
    ("③ 製造効率", "Asprovaの生産効率。\n÷することで計画時間が膨らむ"),
    ("④ 段取10m", "作業の前に加算する段取10分\n(BOM作成シートM1=\"10m\")"),
    ("製造BOM", "Asprovaのテーブル要素。\n差分確認マクロBOM作成シートが元"),
    ("資源カレンダー", "装置ごとの稼働可能時間枠。\nここに入る範囲でしか作業を置かない"),
    ("順延・代替資源", "収まらない作業を後ろの日へずらす、\nまたは別の資源に割り替える調整"),
]
yy = 172
for i, (t, d) in enumerate(gt):
    gterm(f"L4_G{i}", 656, yy, 120, 334, t, d, PURPLE[1])
    yy += 60

srcnote("L4_SRC", 56, 636, 1074, "出所: 差分確認マクロ BOM作成シート O1=UseBomInst_ProductionFactor(0.7/0.5)・N1=($E$15/$F$15)&\"sp\"・M1=\"10m\"・E13注記 / Asprova製造BOM画面(image2.png: 製造35sp〜8sp)")
page_end()

# ================= PG-05 用語集と注意 =================
page_begin("LOAD-05", "5_共通用語と未確認事項")
title("L5_T", "共通用語と未確認事項")
subtitle("L5_ST", "3処理をまたいで使う言葉と、現時点で確認できていない点。")

region("L5_R1", 40, 90, 1090, 330, "共通の規則", TINT["yellow"], YELLOW[1])
common = [
    ("サイクルタイム 2系統", "実装技術課の管理: DGS最速値(設備最大性能)。\n生産1課の実績: MySQL最新10指図の平均。\n負荷計算に使うのは実績平均の方。両者の差が\nBSM-1700マスター検証の要点。"),
    ("28秒下限", "DGS実績が短すぎる場合の共通クリップ値。\nBOSS計画パワークエリ・BOM作成シートで同じ28秒。"),
    ("0.7 の方向", "コードは全て ÷0.7(工数を約1.43倍に膨らませる)。\n会議メモは「DGS最大値×安全係数」と記録。×方向は\n実装と一致しない。意図は関係者への確認が必要。"),
]
yy = 134
for i, (t, d) in enumerate(common):
    node(f"L5_C{i}a", 60, yy, 180, 86, t, "#FFFFFF", YELLOW[1], fs=11, bold=True)
    plain(f"L5_C{i}b", 252, yy, 850, 86, d, fs=11)
    yy += 96

region("L5_R2", 40, 440, 1090, 210, "未確認事項(今回の解析範囲で確認できなかった点)", TINT["yellow"], RED[1])
unk = [
    ("×0.7 の設計意図", "÷0.7が「余裕を持たせる」狙いか、別の意図(稼働率補正等)か。佐藤さん・実装技術課への確認が必要。"),
    ("BOMシートへのCT転記経路", "差分確認マクロBOM作成シートのE列CTが、MySQL実績平均とどう連結しているか(手作業/リンク)未確認。"),
    ("段取り予定.xlsx の実体", "SharePoint上のため今回未確認。ジョブ作成シートの容量確認処理はTOOL.xlam側の実装から推定。"),
]
yy = 486
for i, (t, d) in enumerate(unk):
    node(f"L5_U{i}a", 60, yy, 200, 52, t, "#FFFFFF", RED[1], fs=11, bold=True)
    plain(f"L5_U{i}b", 272, yy, 840, 52, d, fs=11)
    yy += 62

plain("L5_N1", 40, 668, 1090, 60, "数値・行番号の出所は 20261016_鹿島引き込みExcel分析/説明_負荷計算の処理内容.md §5 参照。\n元ファイル(各xlsm/xlam/accdb)は読み取り専用で解析し、変更はしていない。", fs=10)
page_end()

xml = '<mxfile host="Electron" modified="2026-10-16T00:00:00.000Z" agent="analysis" version="24.0.0">' + "".join(cells) + "</mxfile>"
open(OUT, "w", encoding="utf-8").write(xml)
print("written:", OUT, len(xml), "bytes")