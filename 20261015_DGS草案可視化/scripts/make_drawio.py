# -*- coding: utf-8 -*-
"""分析済み4Excelの構造・内容・関係を draw.io 形式で生成する(Page1-5)。修正サイクル1版。

設計基準:
- グリッド 10px / 図形内余白 12-16px / 図形間隔 24-40px / ページ余白 40px
- フォント Meiryo / タイトル 26px / 本文 13-14px / 注記 12px
- 役割色: 様式(DGS)=#D6E4F0(青系) / 草案(PanaCIM)=#DDEBD8(緑系) / 草案(LNB)=#EFE9DC(茶系)
          記録・一覧=#F5F5F5 / 不整合・注意=#FDE9E1(赤系) / 灰点線=未確認・参考
- 線: 直交(orthogonalEdgeStyle)・ネイティブ接続 / ラベルは白背景で可読確保
- 全箱の高さは文字行数から算出(13pt≒19px/行+16px余白)
"""
import html
import os

OUTPUT = r"C:\Users\ss80751\kohden-code-workspace\20261015_DGS草案可視化\output\分析済みExcel構造関係図.drawio"
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

F = "Meiryo"

def esc(s):
    return html.escape(str(s), quote=True)

class Page:
    def __init__(self, pid, name, title, subtitle):
        self.pid = pid
        self.name = name
        self.cells = []
        self.counter = 0
        self.title = title
        self.subtitle = subtitle

    def add(self, style, value, x, y, w, h, id_=None):
        self.counter += 1
        cid = id_ or f"{self.pid}_{self.counter:03d}"
        geo = f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry" />'
        self.cells.append(
            f'        <mxCell id="{cid}" value="{esc(value)}" style="{style}" vertex="1" parent="1">\n            {geo}\n        </mxCell>'
        )
        return cid

    def edge(self, src, dst, label="", style="", points=None):
        self.counter += 1
        cid = f"{self.pid}_{self.counter:03d}"
        pts = ""
        if points:
            pts = '<Array as="points">' + "".join(
                f'<mxPoint x="{px}" y="{py}" />' for px, py in points) + "</Array>"
        geo = f'<mxGeometry relative="1" as="geometry">{pts}</mxGeometry>'
        v = esc(label) if label else ""
        self.cells.append(
            f'        <mxCell id="{cid}" value="{v}" style="{style}" edge="1" parent="1" source="{src}" target="{dst}">\n            {geo}\n        </mxCell>'
        )
        return cid

    def xml(self):
        cells = "\n".join(self.cells)
        return (
            f'    <diagram id="{self.pid}" name="{esc(self.name)}">\n'
            f'      <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1654" pageHeight="1169" background="#ffffff" math="0" shadow="0">\n'
            f'        <root>\n'
            f'          <mxCell id="0" />\n'
            f'          <mxCell id="1" parent="0" />\n'
            f'{cells}\n'
            f'        </root>\n'
            f'      </mxGraphModel>\n'
            f'    </diagram>'
        )


# ---------- 共通スタイル ----------
ST_TITLE = f"text;html=1;fontFamily={F};fontSize=26;fontStyle=1;align=left;verticalAlign=middle;fontColor=#1F2937;"
ST_SUB = f"text;html=1;fontFamily={F};fontSize=12;align=left;verticalAlign=middle;fontColor=#6B7280;"
ST_LEGEND = f"rounded=1;whiteSpace=wrap;html=1;fontFamily={F};fontSize=12;align=left;spacingLeft=12;fillColor=#F8F9FA;strokeColor=#ADB5BD;fontColor=#495057;arcSize=4;"
ST_GROUP = (f"rounded=1;whiteSpace=wrap;html=1;fontFamily={F};fontSize=13;fontStyle=1;"
            "fillColor=none;verticalAlign=top;spacing=8;align=left;arcSize=3;")
ST_BAR = (f"rounded=0;whiteSpace=wrap;html=1;fontFamily={F};fontSize=14;fontStyle=1;"
          "fillColor=#EDF2F7;strokeColor=#374151;fontColor=#1F2937;align=left;spacingLeft=12;verticalAlign=middle;")

def box(fill, stroke="#5B6B7A", font=13, bold=0, dash=0):
    return (f"rounded=1;whiteSpace=wrap;html=1;fontFamily={F};fontSize={font};"
            f"fillColor={fill};strokeColor={stroke};fontColor=#1F2937;"
            f"arcSize=6;spacing=8;spacingLeft=12;align=left;verticalAlign=top;"
            + (f"fontStyle={bold};" if bold else "")
            + (f"dashed=1;" if dash else ""))

B_FILE   = box("#FFFFFF", "#1F2937", 14, 1)
B_STYLE  = box("#D6E4F0", "#3D6B99")
B_DOC    = box("#FFFFFF", "#3D6B99")
B_PANA   = box("#DDEBD8", "#4E7A43")
B_LNB    = box("#EFE9DC", "#8A6D3B")
B_LIST   = box("#F5F5F5", "#6B7280")
B_WARN   = box("#FDE9E1", "#B4552D")
B_GRAY   = box("#F3F4F6", "#9CA3AF", dash=1)
B_NOTE   = box("#FBFBF8", "#C9C4B4", 12)
B_HDR    = box("#FFFFFF", "#374151", 14, 1)

E_FLOW = (f"edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;fontFamily={F};fontSize=12;"
          "strokeColor=#3D6B99;strokeWidth=1.5;labelBackgroundColor=#FFFFFF;fontColor=#24466B;align=center;verticalAlign=middle;")
E_LINK = (f"edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;fontFamily={F};fontSize=12;"
          "strokeColor=#4E7A43;strokeWidth=1.5;labelBackgroundColor=#FFFFFF;fontColor=#3E6134;")
E_WARN = (f"edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;fontFamily={F};fontSize=12;"
          "strokeColor=#B4552D;strokeWidth=1.5;dashed=1;labelBackgroundColor=#FFFFFF;fontColor=#8C3F20;")
E_REF  = (f"edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;fontFamily={F};fontSize=12;"
          "strokeColor=#6B7280;strokeWidth=1.2;dashed=1;labelBackgroundColor=#FFFFFF;fontColor=#4B5563;")

def header(pg, title, sub, w=1654):
    pg.add(ST_TITLE, title, 40, 24, w - 80, 34, id_=f"{pg.pid}_title")
    pg.add(ST_SUB, sub, 40, 60, w - 80, 18, id_=f"{pg.pid}_sub")


# ============================================================
# Page 1: 全体構成・目的
# ============================================================
p1 = Page("p1", "1_全体構成・目的",
          "Page1 分析対象4ファイルの全体構成と目的",
          "対象: PanaCIM_LNB 配下の4ファイル(原本Read Only) ／ 出典: Excel内の記載と本日再実測(evidence/excel_facts.json)")
header(p1, p1.title, p1.subtitle)

p1.add(ST_GROUP + "strokeColor=#3D6B99;fontColor=#24466B;",
       "DGS 実装プログラム手順書（様式 NR4030 系）", 40, 110, 720, 370, id_="g_dgs")
p1.add(ST_GROUP + "strokeColor=#4E7A43;fontColor=#3E6134;",
       "管理手順書 草案（会議中に手を加えたもの）", 800, 110, 814, 370, id_="g_draft")

f_p1 = p1.add(B_FILE, "<b>0494-913473 実装プログラム手順(DGS)_P1.xls</b><br>役割: 表紙・変更履歴(付表1シート)<br>管理番号 0494-913473 ／ 頁 1/119<br>様式 NR4030-0100-A3 ／ 初版枚数 55枚", 60, 160, 340, 110, id_="F_P1")
f_p2 = p1.add(B_FILE, "<b>0494-913473 実装プログラム手順(DGS)_P2.xlsx</b><br>役割: 本文 34シート<br>はじめに1 ／ フロー図4 ／ 個別手順29<br>様式 NR4030-0300-A3(フッタ)", 420, 160, 320, 110, id_="F_P2")
f_pc = p1.add(B_FILE, "<b>PanaCIM管理手順書_草案(会議中に手を加えたもの).xlsx</b><br>文書名: Pana-CIM 管理手順書 ／ 版 0.11(草案・未検証)<br>16シート ／ 会議メモ(B1) 6件", 820, 160, 380, 110, id_="F_PC")
f_ln = p1.add(B_FILE, "<b>LNB管理手順書_草案(会議中に手を加えたもの).xlsx</b><br>文書名: LNB 管理手順書 ／ 版 0.9(草案・未検証)<br>19シート ／ 申し送り(認証情報)含む", 1220, 160, 374, 110, id_="F_LN")

p1.add(B_STYLE, "P1: 表紙+変更履歴<br>変更記号 01→02→03(書替)<br>総枚数 93→118→119", 60, 310, 160, 140, id_="P1_hist")
p1.add(B_DOC, "P2: 本文 34シート<br>① はじめに(目的/適用範囲)<br>② フロー図 4シート<br>③ 個別手順 29シート", 240, 310, 160, 140, id_="P2_body")
p1.add(B_DOC, "個別手順: 手順番号「1．」+<br>「します」文体+スクショ154枚<br>実パス掲載 14/34シート", 420, 310, 160, 140, id_="P2_proc")
p1.add(B_PANA, "本文 9シート<br>目次/改訂履歴/目的と適用範囲(削除)<br>/用語/構成と管理情報/管理体制<br>/日次点検(WIP)/月次再起動<br>/バックアップ/復旧/異常時の対応", 820, 310, 200, 140, id_="PC_body")
p1.add(B_LIST, "記録・一覧 7シート<br>チェックシート(月次・異常時)<br>/会議課題一覧(一時)<br>/要確認事項一覧", 1040, 310, 160, 140, id_="PC_list")
p1.add(B_LNB, "本文+定期管理<br>目次〜異常時の対応/定期管理<br>※PanaCIMに無い「定期管理」", 1220, 310, 180, 140, id_="LN_body")
p1.add(B_LNB, "LNB固有<br>申し送り(認証情報)<br>引用と部品照合<br>チェックシート(日次)", 1420, 310, 174, 140, id_="LN_solo")

p1.add(B_NOTE, "<b>共通の様式基盤</b>: 会議版草案の表紙は「様式の参考=操作手順書 0494-912039(06) 表紙(様式 NR4030-0100-A3)」と記載(DGS P1と同様式系)。型名欄は両草案とも「ZZZ-90000(仮)」で統一(仮番運用)。", 40, 520, 1000, 76, id_="N_style")
p1.add(B_WARN, "<b>要留意(マスク表記)</b>: DGS起動シート A12 に利用者名・パスワードの平文記載あり(本図ではマスク表記)。<br>両草案とも表紙に「認証情報=本文に書かない・値は別紙管理」と明記。", 1060, 520, 554, 76, id_="N_secret")

p1.edge("F_P1", "P1_hist", "含む", E_FLOW)
p1.edge("F_P2", "P2_body", "含む", E_FLOW)
p1.edge("F_P2", "P2_proc", "含む", E_FLOW, points=[(580, 296)])
p1.edge("F_PC", "PC_body", "含む", E_LINK)
p1.edge("F_PC", "PC_list", "含む", E_LINK, points=[(1175, 296)])
p1.edge("F_LN", "LN_body", "含む", E_LINK)
p1.edge("F_LN", "LN_solo", "含む", E_LINK, points=[(1535, 296)])

p1.add(B_NOTE, "詳細: Page2=シート内の内容構成 ／ Page3=ファイル・シート・項目の関係 ／ Page4=書式・図形・印刷 ／ Page5=不整合・未確認", 40, 630, 1574, 24, id_="N_nav")
p1.add(ST_LEGEND, "凡例: 青=DGS(様式系) ／ 緑=PanaCIM草案 ／ 茶=LNB草案 ／ 黒枠太線=ファイル ／ 灰=一覧・記録 ／ 赤=不整合・注意 ／ 点線=参照・未確認", 40, 680, 1574, 26, id_="L_1")

# ============================================================
# Page 2: シート内の内容構成
# ============================================================
p2 = Page("p2", "2_シート内の内容構成",
          "Page2 シート内の内容構成",
          "左=DGS手順書(P2) ／ 中=PanaCIM草案 ／ 右=LNB草案 ／ 行番号r・セル番地は実測")
header(p2, p2.title, p2.subtitle)

# --- DGS列(タイトルバー+カード) ---
p2.add(ST_BAR, "DGS_P2: はじめに(59行)", 40, 100, 320, 32, id_="DGS_intro")
p2.add(B_DOC, "r7【目的】SMTプログラム作成手順を示す。<br>r11【適用範囲】マウントデータから<br>SMTプログラム作成および関連作業", 52, 140, 296, 92, id_="DGS_intro2")
p2.add(ST_BAR, "DGS_P2: フロー図 4シート(図形主体)", 40, 248, 320, 32, id_="DGS_flow")
p2.add(B_DOC, "試作フロー(sp+cxn 17/16個)<br>設計変更_部品フロー(10/11)<br>設計変更_改版フロー(10/10)<br>新製品フロー(9/9)<br><br>分岐=「新しい基板？」+YES/NO<br>遷移先=Z列「➡シート名」併記", 52, 288, 296, 156, id_="DGS_flow2")
p2.add(ST_BAR, "DGS_P2: 個別手順 29シート", 40, 460, 320, 32, id_="DGS_proc")
p2.add(B_DOC, "手順番号「1．」全角読点+「します」文体<br>「」要素名・＊/※補足・完了条件<br>スクショ154枚を手順直下に1対1配置<br>例: マウントデータ作成 r6=手順1<br>     基板図番****-912345⇒912345_00", 52, 500, 296, 156, id_="DGS_proc2")
p2.add(ST_BAR, "DGS_P2: 指示書作成、その他(487行)", 40, 676, 320, 32, id_="DGS_mtx")
p2.add(B_DOC, "r9 試作フェーズ別 添付資料マトリクス<br>行=添付資料9種 / 列=5フェーズ<br>(維持改良M**/コンセプト試作C-**/<br>量産試作UT,UR/量産維持R**)<br>セル値=必須/不要/条件付き", 52, 716, 296, 152, id_="DGS_mtx2")
p2.add(ST_BAR, "DGS_P1: 変更履歴", 40, 884, 320, 32, id_="DGS_hist")
p2.add(B_DOC, "変更記号 01×→02×→03×(全て書替)<br>適用=089/定期見直し<br>総枚数 93→118→119", 52, 924, 296, 64, id_="DGS_hist2")

# --- PanaCIM列 ---
p2.add(ST_GROUP + "strokeColor=#4E7A43;fontColor=#3E6134;", "PanaCIM草案: 本文系", 400, 100, 400, 600, id_="PC_group1")
p2.add(B_PANA, "用語(§3)<br>語と意味の2列表", 412, 148, 184, 56, id_="PC_terms")
p2.add(B_PANA, "構成と管理情報(§4)<br>4-1管理対象: CIMC-SV/ESXi/<br>CIM-C PC/CIM-A PC/<br>稼働モニタ/アンドン<br>4-2相関図: 粒度の基準", 604, 148, 184, 134, id_="PC_struct")
p2.add(B_PANA, "管理体制(§5)<br>管理責任者=茂木（由）・倉林<br>副=石井・茂木（絵）<br>実施/確認/承認=要確認<br>5-1作業時の制約", 412, 212, 184, 116, id_="PC_org")
p2.add(B_PANA, "日次点検(WIP)(§6)<br>Step1稼働状態/Step2<br>バックアップ結果/Step3<br>保存領域<br>項目ごとに6点", 604, 290, 184, 96, id_="PC_daily")
p2.add(B_PANA, "月次再起動(§7)<br>7-1実施条件〜7-6<br>引用元追従<br>Step1〜4(4Step構造)", 412, 336, 184, 96, id_="PC_month")
p2.add(B_PANA, "バックアップ(§8)<br>8-1取得手順<br>8-2確定していないこと", 604, 394, 184, 76, id_="PC_bk")
p2.add(B_PANA, "復旧(§9) 14行・枠のみ<br>異常時の対応(§10)<br>10-1色定義/10-2中断と<br>連絡/10-3不具合の記録<br>10-4サーバー再起動", 412, 440, 184, 116, id_="PC_rec")
p2.add(B_PANA, "10-4: 第1段停止(1〜6)<br>/第2段起動(7〜14)<br>+原文突合表(r39-49)<br>全14手順一致・差分3点", 604, 478, 184, 96, id_="PC_rec2")
p2.add(B_WARN, "記録と文書管理(§11-12)<br>シート名に「削除決定済み。」<br>B1メモ「ページ自体不要。」<br>全項目=要確認", 412, 564, 184, 116, id_="PC_rec_doc")
p2.add(B_PANA, "チェックシート(月次・異常時)(§13)<br>13-2記録/13-3月次/13-4異常時<br>/13-5申し送り/13-6承認", 604, 582, 184, 96, id_="PC_chk")
p2.add(ST_GROUP + "strokeColor=#4E7A43;fontColor=#3E6134;", "PanaCIM草案: 記録・一覧系", 400, 730, 400, 150, id_="PC_group2")
p2.add(B_LIST, "会議課題一覧(一時)<br>A.9-30課題12件(達成度)<br>B.10-14決定9点<br>C.解決済み4件<br>「正本は管理書」の記載", 412, 770, 184, 108, id_="PC_issues")
p2.add(B_LIST, "要確認事項一覧<br>No.1〜26(解決済み2件)<br>r40「パスワードは<br>別データ。一元的に記載。」", 604, 770, 184, 108, id_="PC_todo")

# --- LNB列 ---
p2.add(ST_GROUP + "strokeColor=#8A6D3B;fontColor=#6E552E;", "LNB草案: 本文系", 840, 100, 400, 660, id_="LN_group1")
p2.add(B_LNB, "用語(§3)<br>LNB/iLNB/LWS/L1-L3<br>/E-Link/GEM/PLC<br>/DGS(要確認)/アンドン<br>/CIMC-SV", 852, 148, 184, 130, id_="LN_terms")
p2.add(B_LNB, "日次点検(§6)<br>「点検項目が未確定」<br>Step1 LNB接続状態(候補)<br>Step2以降=空欄", 1044, 148, 184, 116, id_="LN_daily")
p2.add(B_LNB, "定期管理(§7) 17行<br>バックアップ(§8) 18行<br>復旧(§9) 14行", 852, 286, 184, 92, id_="LN_reg")
p2.add(B_LNB, "異常時の対応(§10)<br>33行", 1044, 272, 184, 56, id_="LN_abn")
p2.add(B_WARN, "申し送り(認証情報)(§15)<br>4事実: URLにパスワード<br>/HTTP平文/3ライン同一認証<br>/保管庫同期<br>先に決めること 4項<br>(値自体は本書にも未掲載)", 852, 386, 184, 150, id_="LN_secret")
p2.add(B_LNB, "引用と部品照合(§16)<br>付録A 原文引用<br>A-1 LNB接続状態<br>A-2 部品照合<br>A-3 システム構成<br>「自社L1〜L3への適用は<br>未確認」", 1044, 336, 184, 150, id_="LN_quote")
p2.add(B_LNB, "記録と文書管理(§11-12)<br>全項目=要確認<br>期限表: 文書登録=<br>2026-12-28(月)<br>トライアル開始=<br>2027-01-05(火)", 852, 544, 184, 130, id_="LN_doc")
p2.add(B_LNB, "チェックシート(日次)(13-1)<br>「列名は仮」・L1/L2/L3列別<br>チェックシート(月次・<br>異常時)(13-2)", 1044, 494, 184, 130, id_="LN_chk")
p2.add(B_NOTE, "目次の注記なし・リンク16本全有効<br>※(削除)表示なし", 852, 690, 376, 60, id_="LN_note")
p2.add(ST_GROUP + "strokeColor=#8A6D3B;fontColor=#6E552E;", "LNB草案: 記録・一覧系", 840, 790, 400, 150, id_="LN_group2")
p2.add(B_LIST, "会議課題一覧(一時)<br>A.12件/B.9点<br>C.解決済み<br>「正本は各管理書」", 852, 830, 184, 108, id_="LN_issues")
p2.add(B_LIST, "要確認事項一覧 No.1〜20<br>「確認先」列あり<br>(現行実施者/ベンダー<br>/管理責任者)", 1044, 830, 184, 108, id_="LN_todo")

p2.add(ST_LEGEND, "凡例: 青=DGS ／ 緑=PanaCIM草案 ／ 茶=LNB草案 ／ 灰=一覧・記録 ／ 赤=不整合・注意(WIP・削除決定済み等の現状) ／ 行番号r・セル番地は実測", 40, 1010, 1574, 26, id_="L_2")

# ============================================================
# Page 3: ファイル・シート・項目の関係
# ============================================================
p3 = Page("p3", "3_ファイル・シート・項目の関係",
          "Page3 関係図",
          "関係は「記載上の関係」と「実リンク(ハイパーリンク)」を区別して描画")
header(p3, p3.title, p3.subtitle)

p3.add(B_HDR, "DGS_P1(表紙・変更履歴)", 40, 110, 260, 60, id_="R_P1")
p3.add(B_HDR, "DGS_P2(本文34シート)", 40, 240, 260, 60, id_="R_P2")
p3.add(B_DOC, "フロー図4シート<br>(Z列に「➡シート名」)", 40, 340, 260, 62, id_="R_flow")
p3.add(B_DOC, "個別手順29シート<br>(マウントデータ作成/PLM照合/<br>ジョブ作成/SD作成/<br>指示書作成、その他…)", 40, 432, 260, 84, id_="R_proc")
p3.add(B_DOC, "パーツ_マウンタ設定/<br>パーツ_その他設定", 40, 546, 260, 58, id_="R_parts")
p3.add(B_NOTE, "数式15セル: G59=$G$4 等<br>(題目再掲の数式参照)", 40, 634, 260, 54, id_="R_fx")

p3.edge("R_P1", "R_P2", "同一文書番号0494-913473・様式NR4030共通", E_FLOW)
p3.edge("R_flow", "R_proc", "Z列の➡記載(ハイパーリンクではない)", E_REF)

p3.add(B_HDR, "PanaCIM草案(版0.11)", 420, 110, 480, 60, id_="R_PC")
p3.add(B_PANA, "目次(14項目)", 420, 200, 220, 56, id_="R_toc")
p3.add(B_PANA, "異常時の対応(§10)<br>10-4=再起動手順(伏字)<br>+原文突合表(r39-49)", 700, 200, 200, 110, id_="R_abn")
p3.add(B_PANA, "月次再起動(§7)<br>Step1〜4", 420, 290, 220, 64, id_="R_month")
p3.add(B_PANA, "チェックシート(月次・異常時)<br>13-3月次=§7対応<br>13-4異常時=§10-4対応", 700, 340, 200, 96, id_="R_chk")
p3.add(B_LIST, "会議課題一覧(一時)<br>「正本は管理書」", 420, 460, 220, 70, id_="R_issues_pc")
p3.add(B_LIST, "要確認事項一覧<br>No.1〜26", 700, 460, 200, 70, id_="R_todo_pc")

p3.edge("R_toc", "R_month", "実リンク(有効11本)", E_LINK)
p3.edge("R_toc", "R_abn", "", E_LINK)
p3.edge("R_abn", "R_P2", "§10-4出典=0494-912039(06)", E_REF,
        points=[(660, 270), (360, 270)])

p3.add(B_HDR, "LNB草案(版0.9)", 940, 110, 480, 60, id_="R_LN")
p3.add(B_LNB, "目次(16項目・リンク16本全有効)", 940, 200, 220, 76, id_="R_toc_ln")
p3.add(B_LNB, "申し送り(認証情報)(§15)", 1180, 200, 220, 56, id_="R_secret_ln")
p3.add(B_LNB, "会議課題一覧(一時)<br>「正本は各管理書」", 940, 290, 220, 70, id_="R_issues_ln")
p3.add(B_LNB, "要確認事項一覧<br>No.17認証情報の保管場所<br>「§15を先に処理すること」", 1180, 290, 220, 96, id_="R_todo_ln")
p3.add(B_LNB, "引用と部品照合(§16)<br>付録A=公式資料の原文引用<br>「適用・設定状態は未確認」", 940, 400, 220, 96, id_="R_quote_ln")

p3.edge("R_toc_ln", "R_issues_ln", "", E_LINK)
p3.edge("R_toc_ln", "R_secret_ln", "", E_LINK)
p3.edge("R_secret_ln", "R_todo_ln", "§14 No.17を先に処理(文字参照)", E_REF)

p3.edge("R_issues_pc", "R_issues_ln", "併存(正本は管理書)", E_WARN,
        points=[(530, 560), (910, 560), (910, 325)])
p3.edge("R_todo_pc", "R_todo_ln", "管理書間で共通の未決項目", E_WARN,
        points=[(800, 590), (1440, 590), (1440, 330)])

p3.add(B_NOTE, "様式の基盤: 会議版草案の表紙に「様式の参考=操作手順書0494-912039(06)(様式 NR4030-0100-A3)」の記載(DGS P1と同様式系)", 420, 640, 600, 60, id_="R_style_note")
p3.edge("R_P1", "R_PC", "様式系の共通(NR4030-0100-A3)…Excel内の記載による関係", E_REF,
        points=[(170, 96), (660, 96)])

p3.add(ST_LEGEND, "凡例: 青実線=包含・同一文書 ／ 緑実線=ハイパーリンク(実測・移動で追従) ／ 灰点線=文字による参照(リンクではない) ／ 赤点線=矛盾・併存・未確定の関係", 40, 800, 1574, 26, id_="L_3")
p3.add(B_NOTE, "注意: フロー図Z列の「➡」はハイパーリンクではなく文字記載(実測: P2のシート間ハイパーリンク=0件)。線種はこれを反映。", 40, 840, 1574, 40, id_="N_ref")

# ============================================================
# Page 4: 書式・図形・印刷の構造
# ============================================================
p4 = Page("p4", "4_書式・図形・印刷",
          "Page4 書式・図形・印刷の構造(実測値のみ)",
          "測定: openpyxl(page_setup/row_breaks/print_area/oddFooter)・drawing XML(sp/cxnSp/pic)実測")
header(p4, p4.title, p4.subtitle)

p4.add(ST_GROUP + "strokeColor=#3D6B99;fontColor=#24466B;", "DGS_P2 様式(全34シート)", 40, 110, 500, 396, id_="S_dgs")
p4.add(B_STYLE, "ヘッダー枠: A1:V2「手 順 書」(結合)<br>W2管理番号(値空)・AU2頁(値はフッタ&P)<br>A3型名(AC3:AZ3=「－」)・A4作業内容+G4題目<br>外周medium・内側thin罫線<br>行高: r2-4=33pt/本文=12.8pt/r1=5.2pt<br>列幅A=1.9(手順番号用)", 52, 158, 476, 140, id_="S_dgs2")
p4.add(B_STYLE, "印刷: 縦向き33シート/横向き1(現場立ち合い)<br>スケール・fitToPage指定なし<br>余白 左0.87/右0.51/上0.59/下0.79(インチ)<br>フッタ: 左NR4030/中央様式 NR4030-0300-A3/右&P<br>約55行ごとにrowBreaks(8シート)+ヘッダ再掲", 52, 310, 476, 118, id_="S_dgs3")
p4.add(B_STYLE, "print_area設定: 3/34シートのみ<br>(ダミーコード採番/指示書作成、その他/現場立ち合い)<br>※未設定=印刷対象外ではない(設定未実施)", 52, 440, 476, 58, id_="S_dgs4")

p4.add(ST_GROUP + "strokeColor=#3D6B99;fontColor=#24466B;", "DGS_P2 図形・画像(実測)", 580, 110, 500, 200, id_="S_shape")
p4.add(B_STYLE, "図形82個+コネクタ63個(32 drawing)<br>→ フロー図4シートに集中<br>画像448参照・xl/media 154ファイル<br>(PNG147+JPEG7)<br>DGS起動の画像アンカー行(0基点): 6/12/30/33/54<br>=手順直下配置(r6手順1/r12手順2に対応)", 592, 158, 476, 140, id_="S_shape2")

p4.add(ST_GROUP + "strokeColor=#4E7A43;fontColor=#3E6134;", "草案2書の様式(PanaCIM16/LNB19シート)", 1120, 110, 494, 348, id_="S_draft")
p4.add(B_PANA, "簡易枠: A1「手 順 書」/A3型名/「ZZZ-90000(仮)」<br>/A4作業内容+D4シート題目/G3「目次へ」リンク<br>結合はA:G幅(対DGSのA:V幅)<br>列幅A=26.0(対DGS A=1.9)<br>罫線: 外周medium相当あり", 1132, 158, 470, 128, id_="S_draft2")
p4.add(B_PANA, "印刷: 横向き14/16シート(PanaCIM)・17/19(LNB)<br>fitToWidth指定なし・print_area=0件(両書)<br>フッタ: 様式番号なし(DGSと相違)", 1132, 298, 470, 84, id_="S_draft3")
p4.add(B_WARN, "DGSとは「向き・結合幅・列幅・フッタ」が相違<br>(NR4030様式への移行は別途作業中の領域)", 1132, 394, 470, 58, id_="S_draft4")

p4.add(ST_GROUP + "strokeColor=#374151;fontColor=#1F2937;", "表紙様式の比較(矢印=「様式の参考」の記載に基づく関係)", 40, 530, 1574, 220, id_="S_cover")
p4.add(B_STYLE, "DGS_P1(付表1)<br>管理番号0494-913473/頁1/119<br>承認/検印/作成(3欄)<br>承認日/作成日/初版枚数55<br>変更履歴: 変更記号+書替+総枚数<br>+承認日/承認者+担当", 52, 578, 480, 148, id_="S_cover1")
p4.add(B_PANA, "PanaCIM草案・表紙<br>文書名/文書番号=ZZZ-90000(仮)/版0.11<br>対象システム=Pana-CIM<br>作成=4名/リーダー<br>承認・検印=要確認/作成日・承認日=要確認<br>様式の参考=0494-912039(06)<br>文書状態=草案・未検証/認証情報=別紙管理", 560, 578, 480, 148, id_="S_cover2")
p4.add(B_LNB, "LNB草案・表紙<br>文書名/文書番号=ZZZ-90000(要確認)/版0.9<br>対象システム=LNB<br>作成=4名/リーダー<br>承認・検印=要確認<br>文書状態=草案・未検証/認証情報=別紙管理", 1080, 578, 480, 148, id_="S_cover3")
p4.edge("S_cover1", "S_cover2", "", E_REF)
p4.edge("S_cover1", "S_cover3", "", E_REF, points=[(300, 738), (1320, 738)])

p4.add(ST_GROUP + "strokeColor=#6B7280;fontColor=#374151;", "数式の実体(数式参照の関係)", 40, 780, 500, 150, id_="S_fx")
p4.add(B_NOTE, "DGS_P2で確認された数式は15セル全て「=$G$4」系<br>(パーツ_マウンタ設定 G59/G114/G169<br>パーツ_その他設定 G52/G106/G160/G214/G268/G322 等)<br>G4=題目(「パーツデータ作成ノウハウ（…）」)の再掲", 52, 828, 476, 96, id_="S_fx2")
p4.add(B_NOTE, "草案2書: 数式0件(全て値+ハイパーリンクのみ実測)", 580, 800, 500, 56, id_="S_fx3")

p4.add(ST_LEGEND, "凡例: 青=DGS様式 ／ 緑=PanaCIM草案 ／ 茶=LNB草案 ／ 灰=数式・注記 ／ 赤=相違・注意 ／ 数値は全て実測(測定方法は図上部に記載)", 40, 960, 1574, 26, id_="L_4")

# ============================================================
# Page 5: 不整合・未確認事項
# ============================================================
p5 = Page("p5", "5_不整合・未確認事項",
          "Page5 不整合・未確認事項(課題ID K-01〜K-14)",
          "対象: 本日実測で判明した問題のみ ／ 改善提案は含まない ／ 詳細は根拠_関係対応表.md")
header(p5, p5.title, p5.subtitle)

p5.add(ST_GROUP + "strokeColor=#4E7A43;fontColor=#3E6134;", "PanaCIM草案: 目次とシート名の不整合", 40, 110, 560, 300, id_="K_grp1")
p5.add(B_PANA, "目次 B10「日次点検(削除)」<br>リンク先='日次点検'!A1", 52, 158, 260, 56, id_="K_toc10")
p5.add(B_WARN, "実シート名=「日次点検(WIP)」<br>→ リンク切れ", 340, 158, 240, 56, id_="K_01")
p5.add(B_PANA, "目次 B15「記録と文書管理(削除)」<br>リンク先='記録と文書管理'", 52, 226, 260, 56, id_="K_toc15")
p5.add(B_WARN, "実名=「記録と文書管理<br>(削除決定済み。)」→ リンク切れ", 340, 226, 240, 56, id_="K_02")
p5.add(B_PANA, "目次 B16「チェックシート(日次)」<br>リンク先='チェックシート(日次)'", 52, 294, 260, 56, id_="K_toc16")
p5.add(B_WARN, "リンク先シートが存在しない<br>(B1メモ「日時点検は不要」と<br>整合するが目次・リンクが残存)", 340, 294, 240, 96, id_="K_03")

p5.edge("K_toc10", "K_01", "K-01", E_WARN)
p5.edge("K_toc15", "K_02", "K-02", E_WARN)
p5.edge("K_toc16", "K_03", "K-03", E_WARN)

p5.add(ST_GROUP + "strokeColor=#B4552D;fontColor=#8C3F20;", "削除決定と併存", 40, 440, 560, 110, id_="K_grp2")
p5.add(B_WARN, "「記録と文書管理(削除決定済み。)」シートが残存<br>B1メモ「ページ自体不要。」+ 目次に(削除)表示", 52, 488, 536, 52, id_="K_07")

p5.add(ST_GROUP + "strokeColor=#B4552D;fontColor=#8C3F20;", "認証情報の扱い", 640, 110, 460, 232, id_="K_grp3")
p5.add(B_WARN, "K-04: DGS起動 A12 に利用者名・<br>パスワードの平文記載<br>(本図ではマスク表記)", 652, 158, 200, 110, id_="K_04")
p5.add(B_WARN, "K-10: LNB 申し送り(§15)<br>URL平文/HTTP/3ライン同一<br>認証(値は本書にも未掲載)", 880, 158, 208, 110, id_="K_10")
p5.add(B_PANA, "両草案とも表紙に<br>「認証情報=本文に書かない・値は別紙管理」", 652, 280, 436, 52, id_="K_pol")

p5.edge("K_04", "K_pol", "", E_REF)
p5.edge("K_10", "K_pol", "", E_REF)

p5.add(ST_GROUP + "strokeColor=#B4552D;fontColor=#8C3F20;", "様式・印刷設定の相違", 640, 372, 460, 210, id_="K_grp4")
p5.add(B_WARN, "K-05: DGS_P2のprint_area設定 3/34シートのみ", 652, 420, 436, 36, id_="K_05")
p5.add(B_WARN, "K-06: 草案2書のprint_area=0件・fitToWidthなし", 652, 464, 436, 36, id_="K_06")
p5.add(B_WARN, "様式相違: 向き(縦vs横)/結合幅(A:V vs A:G)/<br>列幅(A=1.9 vs 26.0)/フッタ(様式番号有 vs 無)", 652, 508, 436, 60, id_="K_07b")

p5.add(ST_GROUP + "strokeColor=#B4552D;fontColor=#8C3F20;", "表記の不一致", 1140, 110, 474, 230, id_="K_grp5")
p5.add(B_WARN, "K-13: フロー図Z列の➡先と実シート名の不一致<br>➡「PCB編集、CSV出力」vs 実「PCB編集&出力」<br>➡「指示書作成」vs 実「指示書作成、その他」", 1152, 158, 450, 84, id_="K_13")
p5.add(B_WARN, "K-14: ➡遷移は文字記載のみ<br>(ハイパーリンク0件実測)のため<br>機械的な追跡は不可", 1152, 254, 450, 72, id_="K_14")

p5.add(ST_GROUP + "strokeColor=#9CA3AF;fontColor=#4B5563;", "未取得・未確認", 1140, 372, 474, 210, id_="K_grp6")
p5.add(B_GRAY, "K-08: 型名「ZZZ-90000(仮)」=仮番運用<br>(付番規則は両草案とも要確認の記載)", 1152, 420, 450, 56, id_="K_08")
p5.add(B_GRAY, "K-09: 承認欄=要確認/改訂履歴の承認列=未<br>K-11: P1の罫線・フォント細部(xlrd限界)<br>K-12: ZZZ-90000と0494-913473の関係", 1152, 488, 450, 84, id_="K_091112")

p5.add(B_NOTE, "全課題の根拠セル・確認状態の一覧は「根拠_関係対応表.md」を参照。K-01〜K-03/K-07/K-13/K-14=矛盾あり、K-04/K-08/K-10=Excel内記載の確認、K-05/K-06/K-14=構造の実測、K-09/K-11/K-12=未取得・未確認。", 40, 620, 1574, 56, id_="K_note")
p5.add(ST_LEGEND, "凡例: 赤=矛盾あり・注意 ／ 灰点線枠=未取得・未確認 ／ 緑=草案側の現状(対比用)", 40, 700, 1574, 26, id_="L_5")

# ---------- 保存 ----------
pages = [p1, p2, p3, p4, p5]
xml = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<mxfile host="Electron" modified="2026-10-15T00:00:00.000Z" agent="KohdenCode" version="32.4.1" type="device">\n'
    + "\n".join(pg.xml() for pg in pages)
    + '\n</mxfile>\n'
)
with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(xml)
print("saved", OUTPUT)
for pg in pages:
    print(pg.name, "cells:", pg.counter)
