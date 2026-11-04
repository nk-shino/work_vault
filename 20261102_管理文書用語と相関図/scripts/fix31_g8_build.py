# -*- coding: utf-8 -*-
"""fix31_g8_build.py — 計画§9 G8: 相関図全面リデザイン(エントリ31の指示·エントリ32で記録).

両冊の「相関図」シートを 3視点(相関図①全体の関わり / ②PanaCIM管理側の内部 / ③ライン設備側の内部)
へ再構築する。内容は現行シートから全件収穫して引き継ぎ(削減·追加なし·適応は変更リストに記録)、
スタイルは承認モック(c4_mock_1/2/3)どおり。

前提:
- G8前バックアップ backup_20261102/*_G8前_20261104.xlsx が正。実行前に正本へ復元してから適用する(再実行安全)。
- Pana冊は利用者により表紙シート削除済み(2026-11-04 13:05·意図的確認済み)→ 採番は目次=1から。
- 相関図_old·cred系(申し送り(認証情報))·引用原文セルは不変(検証する)。
出力: scripts/fix31_g8_build_report.json (図形数·頁数·採番·SHA。シート本文の値は書かない)
"""
import os, sys, json, math, shutil, hashlib, traceback, time

sys.stdout.reconfigure(encoding="utf-8")

BASE = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
VDIR = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
BOOKS = {
    "pana": {
        "xlsx": os.path.join(VDIR, "Pana-CIM管理手順書案_未承認.xlsx"),
        "pdf": os.path.join(VDIR, "Pana-CIM管理手順書案_未承認.pdf"),
        "backup": os.path.join(BASE, "backup_20261102", "Pana-CIM管理手順書案_未承認_G8前_20261104.xlsx"),
        "order": ["目次", "用語", "構成と管理情報", "相関図①", "相関図②", "相関図③", "相関図_old",
                  "管理体制", "月次再起動", "バックアップ", "復旧", "異常時の対応",
                  "チェックシート(月次・異常時)", "会議課題一覧(一時)", "付録 引用元と確認範囲",
                  "要確認事項一覧", "7-5仮_サービス起動停止"],
        "auto": (), "expect_pages": 49, "lastcol": "CG",
        "quote": ([("異常時の対応", [f"C{r}" for r in range(42, 64)]),
                   ("付録 引用元と確認範囲", ["C9", "C10", "C14", "C17", "C20"]),
                   ("7-5仮_サービス起動停止", [f"C{r}" for r in range(12, 19)])]),
    },
    "lnb": {
        "xlsx": os.path.join(VDIR, "LNB管理手順書案_未承認.xlsx"),
        "pdf": os.path.join(VDIR, "LNB管理手順書案_未承認.xlsx".replace(".xlsx", ".pdf")),
        "backup": os.path.join(BASE, "backup_20261102", "LNB管理手順書案_未承認_G8前_20261104.xlsx"),
        "order": ["表紙", "目次", "用語", "構成と管理情報", "相関図①", "相関図②", "相関図③", "相関図_old",
                  "管理体制", "日次点検", "定期管理", "バックアップ", "復旧", "異常時の対応",
                  "チェックシート(日次)", "チェックシート(月次・異常時)", "会議課題一覧(一時)",
                  "要確認事項一覧", "申し送り(認証情報)", "認証情報一覧", "引用と部品照合"],
        "auto": ("表紙", "申し送り(認証情報)"), "expect_pages": 32, "lastcol": "AZ",
        "quote": ([("引用と部品照合", ["C13", "C16", "C20"])]),
    },
}
PAGES = os.path.join(BASE, "scripts", "tmp_g8_pages")
REPORT = os.path.join(BASE, "scripts", "fix31_g8_build_report.json")
FORBID = ["windwos", "Route Editer", "LNB再起動", "LNB-PCリブート", "LNB-PC電源OFF"]

REP = {"books": {}, "errors": []}

# ---------------- palette / fonts ----------------
C = {
    "server_f": 0xF5E6ED, "server_l": 0xA35F7B,   # BGR: 紫 fill EDE6F5 / line 7B5FA3
    "term_l": 0x59BB9B,                            # 緑 9BBB59
    "eq_l": 0x3844A9,                              # 赤茶 A94438
    "est_f": 0xF2F2F2, "est_l": 0x969696,
    "ref_l": 0x969696,
    "band_l": 0xBFBFBF, "head_f": 0x404040,
    "person_f": 0xE8E8E8, "person_l": 0x808080,
    "ink": 0x1F1F1F, "sub": 0x5F5F5F, "lbl": 0x404040, "icon": 0x595959,
}
FONT = "Meiryo UI"
RRECT, RECT, OVAL = 5, 1, 9
CAN, DONUT, HEXA, PENTA, DISPLAY = 13, 18, 10, 51, 43

def rgb(v):  # 0xBBGGRR long -> (r,g,b)
    return ((v) & 0xFF, ((v) >> 8) & 0xFF, ((v) >> 16) & 0xFF)

def act(msg):
    print("[act]", msg, flush=True)

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def close_wb(wb):
    """Close を堅牢に(0xE0000002 等の一時的 COM エラーを無視·保存済みなら損失なし)。"""
    try:
        wb.Close(SaveChanges=False)
    except Exception as e:
        act(f"close_wb ignored: {type(e).__name__}")

def units(s):
    raise RuntimeError("text measurement is forbidden by the safe-I/O rules")

# ---------------- layout spec (pt, sheet coords) ----------------
# 注: テキストの収まりは Excel の TextFrame2.AutoSize に委譲する(文字列を実測しない)。
LEGEND = [
    "凡例: 実線=確定した接続 / グレー破線=推定(未確認)の接続 / 矢頭=データの向きが確定(一方向で表記) / 枠の破線=推定機器(当Site未確認) / 灰色破線枠=別図参照",
    "分類: ■サーバ系　■端末系　■設備系　■推定　□外部·参照",
    "略語: VM=仮想マシン / LWS=LNB操作画面(ブラウザ) / PDA=無線スキャナー端末 / FA=生産設備用パソコン / LNB=Line Network Box / NPM·AM=実装機の機種名",
    "出典符: T1=PanaCIM-EE仕様説明書 A680-004624(00) / T1b=社内確定資料·実機確認 / T2=現場確認済み運用 / T3=会議ホワイトボード(2026-10-14·証跡ではない)",
]
LEGEND_COLORS = [None, [0xA35F7B, 0x59BB9B, 0x3844A9, 0x808080, None], None, None]

EXPL_1 = ("本手順書の管理対象(図②③)と外部システム·作業者の関わりのみを示す。C4モデルのシステムコンテキスト図に相当。\n"
          "S1·S2=システム単位の呼び名(収録機器は図②·図③)。E-a·E-b=別図参照の機器(N06·N18)。")
EXPL_2 = "PanaCIM環境のサーバー·端末と、データの退避·出力先を示す。C4モデルのコンテナ図に相当。確定している技術情報のみ記載。"
EXPL_3 = "ライン設備の装置·端末と、LNBを中心としたデータの流れを示す。C4モデルのコンテナ図に相当。推定の接続は破線。"

def sheet_spec(kind, T):  # T = harvested texts dict
    """kind: 1/2/3 -> dict of nodes/edges/labels/band/refs"""
    S = {"nodes": [], "edges": [], "labels": [], "band": None, "title": "", "expl": "", "stacks": []}
    tag = lambda x, y, t: {"tag": [x, y, 32 if len(t) > 2 else 26, 13, t]}
    if kind == 1:
        S["title"] = T["title1"]; S["expl"] = EXPL_1
        S["nodes"] = [
            {"id": "p1", "box": [40, 150, 170, 54], "style": "person", "icon": None,
             "text": "【人】管理者\n保守·再起動作業を実施"},
            {"id": "s1", "box": [300, 150, 220, 70], "style": "server", "icon": None,
             "text": "【システム】PanaCIM環境\n実績管理·各種出力(内部は図②)", **tag(300, 134, "S1")},
            {"id": "ea", "box": [640, 150, 120, 64], "style": "ref", "icon": None,
             "text": "【上位システム】NPM-DGS\nIP 172.25.253.10(図②·N06参照)", **tag(640, 134, "E-a")},
            {"id": "eb", "box": [640, 255, 120, 60], "style": "ref", "icon": None,
             "text": "【外部】外部I/F出力\nXML/DB/ソケット", **tag(640, 239, "E-b")},
            {"id": "p2", "box": [40, 365, 170, 54], "style": "person", "icon": None,
             "text": "【人】作業者\nLNB操作·部品照合を実施"},
            {"id": "s2", "box": [330, 355, 240, 70], "style": "server", "icon": None,
             "text": "【システム】ライン設備(LNB·NPM)\n実装作業·状態表示(内部は図③)", **tag(330, 339, "S2")},
            {"id": "n10", "box": [640, 365, 120, 60], "style": "term", "icon": None,
             "text": "【端末】稼働モニタ(Power BI)\n稼働を表示(図②参照)", **tag(640, 349, "N10")},
        ]
        S["edges"] = [
            {"id": "pa", "pts": [(210, 177), (300, 177)], "arrow": True, "label": ["保守·再起動を実施", 218, 160, 80, 11]},
            {"id": "pb", "pts": [(210, 392), (330, 392)], "arrow": True, "label": ["操作·照合を実施", 218, 373, 76, 11]},
            {"id": "e02", "pts": [(640, 182), (520, 182)], "arrow": True, "label": ["E02 実装データの収集·上位送信", 525, 156, 110, 22]},
            {"id": "e18", "pts": [(520, 205), (612, 205), (612, 285), (640, 285)], "arrow": True, "label": ["E18 外部I/F出力", 620, 222, 80, 11]},
            {"id": "e08", "pts": [(460, 220), (460, 330), (620, 330), (620, 395), (640, 395)], "arrow": True, "label": ["E08 稼働モニタ表示", 628, 340, 90, 11]},
            {"id": "e04", "pts": [(430, 355), (430, 220)], "arrow": False, "label": ["E04 参照·照合/稼働データ", 302, 258, 122, 11]},
            {"id": "e03", "pts": [(450, 425), (450, 455), (740, 455)], "arrow": False, "label": ["E03 ラインデータ", 470, 437, 80, 11]},
        ]
    elif kind == 2:
        S["title"] = T["title2"]; S["expl"] = EXPL_2
        S["band"] = {"box": [18, 150, 724, 326], "head": [18, 150, 460, 28, T["band_a_head"]]}
        S["nodes"] = [
            {"id": "n01", "box": [40, 196, 340, 150], "style": "container", "icon": None,
             "text": T["n01_full"]},
            {"id": "n02", "box": [58, 224, 310, 36], "style": "server", "icon": "server",
             "text": T["n02"], **tag(56, 218, "N02")},
            {"id": "n03", "box": [58, 273, 310, 38], "style": "server", "icon": "server",
             "text": T["n03"], **tag(56, 267, "N03")},
            {"id": "n04", "box": [58, 317, 310, 28], "style": "est", "icon": "server",
             "text": T["n04"], **tag(56, 314, "N04")},
            {"id": "n19", "box": [400, 196, 190, 42], "style": "server", "icon": "server",
             "text": T["n19"], **tag(398, 188, "N19")},
            {"id": "n05", "box": [400, 248, 160, 86], "style": "note", "icon": None, "text": T["n05_note"]},
            {"id": "n10", "box": [600, 196, 140, 54], "style": "term", "icon": "monitor",
             "text": T["n10"], **tag(598, 188, "N10")},
            {"id": "n17", "box": [600, 268, 140, 52], "style": "server", "icon": "db",
             "text": T["n17"], **tag(598, 260, "N17")},
            {"id": "n18", "box": [600, 334, 140, 52], "style": "ext", "icon": "ext",
             "text": T["n18"], **tag(598, 326, "N18")},
            {"id": "n15", "box": [40, 376, 160, 39], "style": "term", "icon": "pc",
             "text": T["n15"]},
            {"id": "n16", "box": [210, 376, 160, 49], "style": "term", "icon": "pc",
             "text": T["n16"]},
            {"id": "n06r", "box": [40, 417, 160, 55], "style": "ref", "icon": None, "text": T["n06"]},
            {"id": "liner", "box": [210, 432, 160, 30], "style": "ref", "icon": None,
             "text": "ライン設備(LNB·NPM)\n図③参照"},
        ]
        # 積み重ね列(実測高から動的配置 — AutoSize の伸びで重なりが起きないようにする)
        S["stacks"] = [
            {"y0": 196, "gap": 16, "ids": ["n10", "n17", "n18"]},
            {"y0": 376, "gap": 6, "ids": ["n15", "n06r"]},
            {"y0": 376, "gap": 6, "ids": ["n16", "liner"]},
        ]
        S["edges"] = [
            {"id": "e01", "pts": [(210, 260), (210, 273)], "arrow": False, "label": [T["L_E01"], 216, 261.5, 130, 11]},
            {"id": "e02", "pts": [(200, 465), (388, 465), (388, 236), (368, 236)], "arrow": True,
             "label": [T["L_E02"], 402, 398, 130, 22]},
            {"id": "e04", "pts": [(370, 447), (396, 447), (396, 254), (368, 254)], "arrow": False,
             "label": [T["L_E04"], 402, 366, 130, 28]},
            # 終端は積み重ねノードの左辺中央へアンカー("@nid:c" = 中心y)
            {"id": "e08", "pts": [(368, 246), (600, "@n10:c")], "arrow": True, "label": [T["L_E08"], 598, 172, 132, 11]},
            {"id": "e15", "pts": [(120, 376), (120, "@n01:b")], "arrow": True, "label": [T["L_E15"], 44, "@n01:b+3", 150, 18]},
            {"id": "e16", "pts": [(290, 376), (290, "@n01:b")], "arrow": True, "label": [T["L_E16"], 214, "@n01:b+3", 150, 18]},
            {"id": "e17", "pts": [(60, 196), (60, 183), (590, 183), (590, "@n17:c"), (600, "@n17:c")], "arrow": True,
             "label": [T["L_E17"], 490, 160, 180, 19]},
            {"id": "e18", "pts": [(100, 228), (100, 189), (578, 189), (578, "@n18:c"), (600, "@n18:c")], "arrow": True,
             "label": [T["L_E18"], 486, 336, 88, 19]},
        ]
    else:
        S["title"] = T["title3"]; S["expl"] = EXPL_3
        S["band"] = {"box": [18, 225, 724, 237], "head": [492, 225, 250, 22, T["band_b_head"]]}
        S["nodes"] = [
            {"id": "n07", "box": [40, 240, 200, 52], "style": "eq_thick", "icon": "pc",
             "text": T["n07"], **tag(38, 228, "N07")},
            {"id": "n11", "box": [330, 240, 185, 46], "style": "term", "icon": "pc",
             "text": T["n11"], **tag(328, 228, "N11")},
            {"id": "n08", "box": [40, 330, 195, 58], "style": "eq", "icon": "hexa",
             "text": T["n08"], **tag(38, 318, "N08")},
            {"id": "n09", "box": [40, 420, 220, 40], "style": "eq", "icon": "andon",
             "text": T["n09"], **tag(38, 408, "N09")},
            {"id": "n12", "box": [300, 420, 200, 40], "style": "term", "icon": "pda",
             "text": T["n12"], **tag(298, 408, "N12")},
            {"id": "n13", "box": [540, 416, 110, 44], "style": "est", "icon": "ap",
             "text": T["n13"], **tag(538, 404, "N13")},
            {"id": "n14", "box": [575, 296, 140, 48], "style": "est", "icon": "tablet",
             "text": T["n14"], **tag(573, 284, "N14")},
            {"id": "pcr", "box": [15, 165, 250, 40], "style": "ref", "icon": None,
             "text": "PanaCIM環境\n図②参照"},
            {"id": "dgsr", "box": [595, 165, 145, 40], "style": "ref", "icon": None,
             "text": "NPM-DGS(上位システム)\n図①②参照"},
        ]
        S["edges"] = [
            # e03 は帯head(492-742, 225-247)を避け、帯の右外(x=750)を通って dgsr 右辺へ
            {"id": "e03", "pts": [(235, 356), (750, 356), (750, 185), (740, 185)], "arrow": False,
             "label": [T["L_E03"], 300, 334, 110, 19]},
            {"id": "e04", "pts": [(150, 388), (150, 394), (26, 394), (26, 213), (100, 213), (100, 205)], "arrow": False,
             "label": [T["L_E04"], 15, 206, 180, 17]},
            {"id": "e05", "pts": [(100, 292), (100, 330)], "arrow": False, "label": [T["L_E05"], 104, 296, 120, 28]},
            {"id": "e06", "pts": [(115, 330), (115, 292)], "arrow": True, "dash": True, "label": [T["L_E06"], 248, 290, 104, 28]},
            {"id": "e07", "pts": [(620, 205), (620, 212), (200, 212), (200, 240)], "arrow": False,
             "label": [T["L_E07"], 300, 190, 150, 19]},
            {"id": "e09", "pts": [(265, 185), (525, 185), (525, 410), (150, 410), (150, 420)], "arrow": True, "dash": True,
             "label": [T["L_E09"], 566, 250, 100, 28]},
            {"id": "e10", "pts": [(236, 292), (236, 320), (282, 320), (282, 440), (260, 440)], "arrow": False, "dash": True,
             "label": [T["L_E10"], 288, 366, 76, 19]},
            {"id": "e12", "pts": [(500, 440), (540, 440)], "arrow": False, "dash": True, "label": [T["L_E12"], 404, 388, 118, 19]},
            {"id": "e13", "pts": [(612, 344), (612, 416)], "arrow": False, "dash": True, "label": [T["L_E13"], 618, 370, 95, 19]},
            {"id": "e14", "pts": [(240, 280), (330, 280)], "arrow": False, "label": [T["L_E14"], 244, 244, 82, 28]},
        ]
    return S

NODE_STYLE = {
    "server":   dict(fill=C["server_f"], line=C["server_l"], w=1.5, dash=1),
    "container":dict(fill=C["server_f"], line=C["server_l"], w=2.25, dash=1),
    "term":     dict(fill=0xFFFFFF, line=C["term_l"], w=1.5, dash=1),
    "eq":       dict(fill=0xFFFFFF, line=C["eq_l"], w=1.5, dash=1),
    "eq_thick": dict(fill=0xFFFFFF, line=C["eq_l"], w=3.0, dash=1),
    "est":      dict(fill=C["est_f"], line=C["est_l"], w=1.5, dash=4),
    "ref":      dict(fill=0xFFFFFF, line=C["ref_l"], w=1.0, dash=4),
    "note":     dict(fill=0xFFFFFF, line=0x8C8C8C, w=0.75, dash=1),
    "ext":      dict(fill=0xFFFFFF, line=0x808080, w=1.5, dash=1),
    "person":   dict(fill=C["person_f"], line=C["person_l"], w=1.5, dash=1),
}

# ---------------- harvest ----------------
HARVEST_NODES = ["band_a_head", "band_b_head", "n01_esxi", "n02_app", "n03_ctrl", "n04_maint", "n05_note",
                 "n06_dgs", "n07_lnb", "n08_line", "n09_andon", "n10_monitor", "n11_lws",
                 "n12_pda", "n13_ap", "n14_tablet", "n15_cima_pc", "n16_cimc_pc",
                 "n17_backup", "n18_extif", "n19_cima_sv"]
HARVEST_LABELS = ["E01", "E02", "E03", "E04", "E05", "E06", "E07", "E08", "E09", "E10",
                  "E12", "E13", "E14", "E15", "E16", "E17", "E18"]

def harvest(ws, book):
    """現行相関図シートから図形テキストとセル値をメモリへ収穫する(永続化しない)。"""
    T = {}
    shapes = {sh.Name: sh for sh in ws.Shapes}
    assert len(shapes) == 75, f"shape count {len(shapes)}"
    for nm in HARVEST_NODES:
        assert nm in shapes, f"missing {nm}"
        T[nm] = shapes[nm].TextFrame2.TextRange.Text
    for e in HARVEST_LABELS:
        T["L_" + e] = "E%s %s" % (e, shapes["label_" + e].TextFrame2.TextRange.Text)
    # sheet_spec 側の短縮キーへの別名
    for short, full in (("n02", "n02_app"), ("n03", "n03_ctrl"), ("n04", "n04_maint"),
                        ("n06", "n06_dgs"), ("n07", "n07_lnb"), ("n08", "n08_line"),
                        ("n09", "n09_andon"), ("n10", "n10_monitor"), ("n11", "n11_lws"),
                        ("n12", "n12_pda"), ("n13", "n13_ap"), ("n14", "n14_tablet"),
                        ("n15", "n15_cima_pc"), ("n16", "n16_cimc_pc"), ("n17", "n17_backup"),
                        ("n18", "n18_extif"), ("n19", "n19_cima_sv")):
        T[short] = T[full]
    # バンドhead短文(③用): band_b_head の1行目
    T["band_b_head"] = T["band_b_head"].split("\n")[0].strip()
    # コンテナ見出し(現行 n01 の2行をそのまま保持·書き換えなし)
    n01_lines = T["n01_esxi"].split("\n")
    assert len(n01_lines) == 2, "n01 lines"
    assert "N02" in n01_lines[1] and "N04" in n01_lines[1], "n01 line2 refs"
    T["n01_full"] = T["n01_esxi"]
    # クリア後に詰める行(旧説明セルの行)
    T["shrink"] = [(9, 10)] if book == "pana" else [(7, 10)]
    # セル
    if book == "pana":
        assert "相関図" in str(ws.Range("A9").Value), "A9 anchor"
        T["title1"] = "2-2 相関図① 全体の関わり"
        T["title2"] = "2-3 相関図② PanaCIM管理側の内部"
        T["title3"] = "2-4 相関図③ ライン設備側の内部"
        T["clear"] = ["A9", "A10"]
        T["tcell"] = "A5"
    else:
        assert "相関図" in str(ws.Range("A6").Value), "A6 anchor"
        T["title1"] = "2-3 相関図① 全体の関わり"
        T["title2"] = "2-4 相関図② PanaCIM管理側の内部"
        T["title3"] = "2-5 相関図③ ライン設備側の内部"
        T["clear"] = ["A6", "C7", "C8", "C9", "C10"]
        T["tcell"] = "A6"
    return T

# ---------------- drawing helpers ----------------
def set_adj(sh, idx, val):
    """Adjustments の要素設定(インデックス付きプロパティ)。失敗時は既定値のまま(Report に集計)。"""
    try:
        import pythoncom
        ole = sh.Adjustments._oleobj_
        dispid = ole.GetIDsOfNames(0, "Item")
        ole.Invoke(dispid, 0, pythoncom.DISPATCH_PROPERTYPUT, False, idx, val)
        return True
    except Exception:
        set_adj.fail += 1
        return False

set_adj.fail = 0

def set_fareast(font_obj, name):
    """gen_py が put マップから外す NameFarEast を生 IDispatch で設定する。"""
    try:
        import pythoncom
        ole = font_obj._oleobj_
        dispid = ole.GetIDsOfNames(0, "NameFarEast")
        ole.Invoke(dispid, 0, pythoncom.DISPATCH_PROPERTYPUT, False, name)
        return True
    except Exception:
        set_fareast.fail += 1
        return False

set_fareast.fail = 0

def set_font(rng, size, bold, color, name=FONT):
    f = rng.Font
    f.Name = name
    set_fareast(f, name)
    f.Size = size
    f.Bold = bold
    f.Fill.ForeColor.RGB = color

def add_text(ws, name, l, t, w, paras, align=1):
    """高さは Excel の AutoSize に委譲するテキストボックス。paras: [(text, size, bold, color)]。
    上端揃えで作成し、必要なら呼び出し側が Height を読んで Top を再配置する。"""
    sh = ws.Shapes.AddTextbox(1, l, t, w, 12)
    sh.Name = name
    sh.Fill.Visible = False
    sh.Line.Visible = False
    tf = sh.TextFrame2
    tf.WordWrap = True
    tf.MarginLeft = tf.MarginRight = 1.5
    tf.MarginTop = tf.MarginBottom = 0.5
    tf.VerticalAnchor = 1
    tf.HorizontalAnchor = align
    tf.TextRange.Text = "\r".join(p[0] for p in paras)
    for i, (txt, size, bold, color) in enumerate(paras, start=1):
        pr = tf.TextRange.Paragraphs.Item(i)
        set_font(pr, size, bold, color)
    tf.AutoSize = 1  # msoAutoSizeShapeToFitText — Excel が高さを決める
    return sh

def add_box(ws, name, l, t, w, h, style, rounded=True):
    sh = ws.Shapes.AddShape(RRECT if rounded else RECT, l, t, w, h)
    sh.Name = name
    if rounded:
        set_adj(sh, 1, 0.12)
    st = NODE_STYLE[style]
    sh.Fill.ForeColor.RGB = st["fill"]
    sh.Fill.Visible = True
    sh.Line.ForeColor.RGB = st["line"]
    sh.Line.Weight = st["w"]
    sh.Line.DashStyle = st["dash"]
    sh.Shadow.Visible = False
    return sh

def add_tag(ws, name, l, t, w, h, text):
    sh = ws.Shapes.AddShape(RRECT, l, t, w, h)
    sh.Name = name
    set_adj(sh, 1, 0.35)
    sh.Fill.ForeColor.RGB = 0xFFFFFF
    sh.Line.ForeColor.RGB = 0x808080
    sh.Line.Weight = 0.75
    sh.Shadow.Visible = False
    tf = sh.TextFrame2
    tf.WordWrap = False
    tf.MarginLeft = tf.MarginRight = tf.MarginTop = tf.MarginBottom = 0
    tf.VerticalAnchor = 3
    tf.HorizontalAnchor = 2
    tf.TextRange.Text = text
    set_font(tf.TextRange, 8, False, C["lbl"])
    return sh

def add_icon(ws, name, kind, l, t):
    """約18ptの濃灰アイコン。戻り値は shape のリスト(グループ化する)。"""
    col = C["icon"]
    parts = []
    def sv(nm, shp, x, y, w, h):
        s = ws.Shapes.AddShape(shp, x, y, w, h)
        s.Name = nm
        s.Fill.ForeColor.RGB = col
        s.Fill.Visible = True
        s.Line.Visible = False
        s.Shadow.Visible = False
        parts.append(s)
        return s
    if kind == "server":
        sv(name + "_a", RECT, l, t, 18, 16)
        for i in range(3):
            b = ws.Shapes.AddShape(RECT, l + 2, t + 3 + i * 4.5, 14, 1.6)
            b.Name = "%s_b%d" % (name, i)
            b.Fill.ForeColor.RGB = 0xFFFFFF
            b.Line.Visible = False
            parts.append(b)
    elif kind == "db":
        sv(name + "_a", CAN, l + 2, t, 14, 18)
    elif kind in ("pc", "monitor", "tablet", "pda"):
        w = 18 if kind in ("pc", "monitor") else 13
        sv(name + "_a", DISPLAY, l + (18 - w) / 2.0, t + 1, w, 15)
        base = ws.Shapes.AddShape(RECT, l + (18 - min(10, w)) / 2.0, t + 16.5, min(10, w), 1.8)
        base.Name = name + "_b"
        base.Fill.ForeColor.RGB = col
        base.Line.Visible = False
        parts.append(base)
    elif kind == "ap":
        sv(name + "_a", DONUT, l + 1, t + 1, 16, 16)
        set_adj(parts[-1], 1, 0.18)
    elif kind == "hexa":
        sv(name + "_a", HEXA, l, t + 1, 18, 15)
    elif kind == "andon":
        sv(name + "_a", RECT, l + 2, t, 14, 10)
        sv(name + "_b", RECT, l + 8, t + 10, 2.4, 6)
        sv(name + "_c", RECT, l + 4, t + 16, 10, 2)
    elif kind == "ext":
        sv(name + "_a", PENTA, l, t + 2, 18, 13)
    else:
        raise ValueError(kind)
    if len(parts) == 1:
        return parts, parts[0]
    grp = ws.Shapes.Range([p.Name for p in parts]).Group()
    grp.Name = name
    return parts, grp

def add_edge(ws, name, pts, arrow, dash):
    # 単一セグメントはグループ化しない(Group は 2 個以上が必要)
    def style(ln, last):
        ln.Line.ForeColor.RGB = 0x000000
        ln.Line.Weight = 1.0
        ln.Line.DashStyle = 4 if dash else 1
        if arrow and last:
            ln.Line.EndArrowheadStyle = 2
            ln.Line.EndArrowheadLength = 2
            ln.Line.EndArrowheadWidth = 2
    if len(pts) == 2:
        (x1, y1), (x2, y2) = pts
        ln = ws.Shapes.AddLine(x1, y1, x2, y2)
        ln.Name = name
        style(ln, True)
        return ln
    names = []
    for i in range(len(pts) - 1):
        (x1, y1), (x2, y2) = pts[i], pts[i + 1]
        ln = ws.Shapes.AddLine(x1, y1, x2, y2)
        ln.Name = "%s_s%d" % (name, i)
        style(ln, i == len(pts) - 2)
        names.append(ln.Name)
    grp = ws.Shapes.Range(names).Group()
    grp.Name = name
    return grp

def build_sheet(ws, g, S, harvest_texts):
    """シートへ 3視点図を構築する。g は 1/2/3。"""
    pfx = "g%d" % g
    counts = {"nodes": 0, "edges": 0, "labels": 0, "icons": 0, "other": 0}
    # タイトルセル(行高を 15 に広げて 10.5pt が切れないようにする)
    # 注: Excel の COM Font は NameFarEast を持たない(VBA 拡張のため)→ 名称のみ設定し、
    #     和文はシート既定の FarEast フォントで描画される(変更リストに記録)
    tc = harvest_texts["tcell"]
    ws.Range(tc).Value = S["title"]
    ws.Rows(int(tc[1:])).RowHeight = 15.0
    ftc = ws.Range(tc).Font
    ftc.Name = FONT
    ftc.Size = 10.5
    ftc.Bold = True
    # G4 対象読者
    readers = {1: "全員(技術詳細は図②·図③)", 2: "保守·管理者", 3: "作業者·保守"}[g]
    ws.Range("G4").WrapText = True
    ws.Range("G4").Value = "　構成と管理情報\n対象読者: " + readers
    # 説明文(①のみ2行) — 高さは AutoSize に委譲
    expl_lines = S["expl"].split("\n")
    ex_paras = [(x, 7.5, False, C["sub"]) for x in expl_lines]
    add_text(ws, pfx + "_expl", 280, 104.5, 485, ex_paras)
    counts["other"] += 1
    # バンド
    if S["band"]:
        b = S["band"]
        bd = ws.Shapes.AddShape(RECT, b["box"][0], b["box"][1], b["box"][2], b["box"][3])
        bd.Name = pfx + "_band"
        bd.Fill.ForeColor.RGB = 0xFFFFFF
        bd.Line.ForeColor.RGB = C["band_l"]
        bd.Line.Weight = 0.75
        bd.Line.DashStyle = 1
        bd.Shadow.Visible = False
        hx, hy, hw, hh, htxt = b["head"]
        hd = ws.Shapes.AddShape(RECT, hx, hy, hw, hh)
        hd.Name = pfx + "_bandhead"
        hd.Fill.ForeColor.RGB = C["head_f"]
        hd.Line.Visible = False
        hd.Shadow.Visible = False
        tf = hd.TextFrame2
        tf.WordWrap = True
        tf.MarginLeft = tf.MarginRight = 4
        tf.MarginTop = tf.MarginBottom = 1
        tf.VerticalAnchor = 3
        tf.HorizontalAnchor = 1 if g == 2 else 2
        tf.TextRange.Text = htxt
        set_font(tf.TextRange, 8, True, 0xFFFFFF)
        counts["other"] += 2
    # ノード(テキスト収まりは Excel の AutoSize に委譲·文字列は測らない)
    def node_paras(nd):
        lines = nd["text"].split("\n")
        paras = [(lines[0], 9.5 if g > 1 else 9, True, C["ink"])]
        for sub in lines[1:]:
            paras.append((sub, 8, False, C["sub"]))
        if nd["id"] == "n05":
            paras = [(x, 6.5, False, C["ink"] if i == 0 else C["sub"]) for i, x in enumerate(lines)]
        if nd["id"] == "n06r":
            paras = [(lines[0], 7.5, True, C["ink"])] + [(x, 6.5, False, C["sub"]) for x in lines[1:]]
        if nd["id"] == "n01":
            paras = [(lines[0], 9.5, True, C["ink"])] + [(x, 8, False, C["sub"]) for x in lines[1:]]
        if nd["id"] in ("liner", "pcr", "dgsr"):
            paras = [(lines[0], 9, True, C["ink"]), (lines[1], 7.5, False, C["sub"])]
        return paras

    # 1) 事前計測: 仮設置(y=-500)して AutoSize の高さを読み取り、すぐ削除する
    meas = {}
    for nd in S["nodes"]:
        l, t, w, h = nd["box"]
        tx_l = l + (26 if nd.get("icon") else 7)
        tx_w = w - (32 if nd.get("icon") else 14)
        tmp = add_text(ws, "_measure", tx_l, -500, tx_w, node_paras(nd))
        meas[nd["id"]] = tmp.Height
        tmp.Delete()
    # 2) 箱の高さ確定(仕様を下限に本文+余白)
    box_h = {nd["id"]: max(nd["box"][3], meas[nd["id"]] + 6) for nd in S["nodes"]}
    # 3) 積み重ね列の最終Top(実測高で積む — タグの頭出し8ptを含め16pt間隔を既定にする)
    top = {nd["id"]: nd["box"][1] for nd in S["nodes"]}
    for st in S.get("stacks", []):
        y = st["y0"]
        for nid in st["ids"]:
            top[nid] = y
            y += box_h[nid] + st["gap"]
    # 4) コンテナは子ノードの実底に追従(はみ出し防止)
    for nd in S["nodes"]:
        if nd["style"] == "container":
            cl, ct, cw, ch = nd["box"]
            inner = [o for o in S["nodes"] if o is not nd
                     and o["box"][0] >= cl and o["box"][1] >= ct
                     and o["box"][0] + o["box"][2] <= cl + cw + 0.5
                     and o["box"][1] + o["box"][3] <= ct + ch + 0.5]
            if inner:
                need = max(top[o["id"]] + box_h[o["id"]] for o in inner)
                box_h[nd["id"]] = max(ch, meas[nd["id"]] + 6, need + 8 - ct)
    for nd in S["nodes"]:
        if box_h[nd["id"]] > nd["box"][3]:
            counts.setdefault("grew", []).append([g, nd["id"], nd["box"][3], round(box_h[nd["id"]], 1)])
    # 5) 幾何登録(エッジ·ラベルのアンカー解決に使う)
    geo = {nd["id"]: (nd["box"][0], top[nd["id"]], nd["box"][2], box_h[nd["id"]]) for nd in S["nodes"]}

    def resolve_val(v):
        """数値は通し、"@nid:c"(中心y)·"@nid:b+n"(底+n)は実幾何へ解決する。"""
        if not isinstance(v, str) or not v.startswith("@"):
            return v
        body = v[1:]
        off = 0.0
        if "+" in body:
            body, off_s = body.split("+", 1)
            off = float(off_s)
        nid, part = body.split(":")
        gl, gt, gw, gh = geo[nid]
        if part == "c":
            return gt + gh / 2.0 + off
        if part == "b":
            return gt + gh + off
        raise ValueError("unknown anchor: %s" % v)

    for nd in S["nodes"]:
        nid = pfx + "_" + nd["id"]
        l, t, w, h = geo[nd["id"]]
        parts = []
        # ノード箱を最背面に先に作る
        box = add_box(ws, nid + "_box", l, t, w, h, nd["style"])
        parts.append(box)
        if nd.get("icon"):
            _, ic = add_icon(ws, nid + "_icon", nd["icon"], l + 5, t + 4)
            parts.append(ic)
            counts["icons"] += 1
        # テキストボックスは AutoSize 済みの高さで中央配置(コンテナ見出しは上端固定)
        txt = add_text(ws, nid + "_txt", l + (26 if nd.get("icon") else 7),
                       t + 3, w - (32 if nd.get("icon") else 14), node_paras(nd))
        if nd["id"] == "n01":
            txt.Top = t + 3
        else:
            txt.Top = t + (h - meas[nd["id"]]) / 2.0
        parts.append(txt)
        if nd.get("tag"):
            tgy = nd["tag"][1] + (t - nd["box"][1])  # 積み重ねで動いた分だけタグも追従
            tg = add_tag(ws, nid + "_tag", nd["tag"][0], tgy, nd["tag"][2], nd["tag"][3], nd["tag"][4])
            parts.append(tg)
        grp = ws.Shapes.Range([p.Name for p in parts]).Group()
        grp.Name = nid
        counts["nodes"] += 1
    # エッジ+ラベル(アンカー解決後の幾何で作成)
    for ed in S["edges"]:
        eid = pfx + "_e_" + ed["id"]
        pts = [(resolve_val(x), resolve_val(y)) for (x, y) in ed["pts"]]
        add_edge(ws, eid, pts, ed["arrow"], ed.get("dash", False))
        counts["edges"] += 1
        lbl, lx, ly2, lw, lh2 = ed["label"]
        ly2 = resolve_val(ly2)
        # 高さは AutoSize に委譲(仕様の lh2 は下限としてのみ扱わない·上端揃えで配置)
        shl = add_text(ws, eid + "_l", lx, ly2, lw, [(lbl, 7.5 if g > 1 else 8, False, C["lbl"])])
        if shl.Height < lh2:
            shl.Top = ly2 + (lh2 - shl.Height) / 2.0  # 仕様帯の中央に置く(幾何のみ)
        counts["labels"] += 1
    # 凡例(4項目·共通·開始yは全図形の実底+8と仕様の大きい方 — AutoSize で積む)
    maxb = 0.0
    for i in range(1, ws.Shapes.Count + 1):
        shx = ws.Shapes(i)
        maxb = max(maxb, shx.Top + shx.Height)
    ly = max(488 if g == 2 else 472, maxb + 8)
    for i, line in enumerate(LEGEND):
        sh = add_text(ws, "%s_leg%d" % (pfx, i), 40, ly, 700, [(line, 7.5, False, C["lbl"])])
        if LEGEND_COLORS[i]:
            try:
                tr = sh.TextFrame2.TextRange
                txt = tr.Text
                marks = [j for j, chx in enumerate(txt) if chx in "■□"]
                for ci, col in enumerate(LEGEND_COLORS[i]):
                    if ci >= len(marks):
                        break
                    ch = tr.Characters.Item(marks[ci] + 1)  # 単一引数形式(2引数は TypeError)
                    if col is None:  # □外部·参照 は灰塗りで区別
                        ch.Font.Fill.ForeColor.RGB = 0xBFBFBF
                    else:
                        ch.Font.Fill.ForeColor.RGB = col
            except Exception:
                counts.setdefault("legend_color_fail", 0)
                counts["legend_color_fail"] += 1
        counts["other"] += 1
        ly += sh.Height + 3
    return counts

def delete_all_shapes(ws):
    for i in range(ws.Shapes.Count, 0, -1):
        ws.Shapes(i).Delete()

def compute_print_area(ws, lastcol):
    maxr, maxb = 0.0, 0.0
    for sh in ws.Shapes:
        maxr = max(maxr, sh.Left + sh.Width)
        maxb = max(maxb, sh.Top + sh.Height)
    # 列(実幅の累積で判定·近似計算を使わない)
    ci = 1
    while ci < 120 and ws.Range(ws.Cells(1, 1), ws.Cells(1, ci)).Width < maxr + 10:
        ci += 1
    colL = col_letter(ci)
    # 行(実セル座標の累積で判定 — 既定行高の想定値を使わない)
    ri = 1
    while ri < 300 and ws.Cells(ri, 1).Top + ws.Cells(ri, 1).Height < maxb + 8:
        ri += 1
    area = "$A$1:$%s$%d" % (colL, ri)
    ws.PageSetup.PrintArea = area
    return area, round(maxr, 1), round(maxb, 1)

def col_letter(i):
    s = ""
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s

# ---------------- main per book ----------------
def copy_vault(src, dst):
    """vault(OneDrive)は同期エンジンが一時的に排他ロックを持つことがある(WinError 32)。
    複数回の再試行で吸収する。"""
    last = None
    for i in range(6):
        try:
            shutil.copy2(src, dst)
            return
        except PermissionError as e:
            last = e
            time.sleep(3.0 * (i + 1))
    raise last

def process(app, book, cfg):
    R = {"name": book}
    XLSX, BACKUP = cfg["xlsx"], cfg["backup"]
    # Phase 0: 正本を G8前バックアップと一致させてから開始(再実行安全)
    sha_now = sha256(XLSX)
    sha_bak = sha256(BACKUP)
    if sha_now != sha_bak:
        act(f"{book}: restore from backup ({sha_now[:12]} -> {sha_bak[:12]})")
        copy_vault(BACKUP, XLSX)
    R["sha_before"] = sha256(XLSX)
    assert R["sha_before"] == sha_bak, "restore failed"
    os.makedirs(PAGES, exist_ok=True)
    for f in os.listdir(PAGES):
        os.remove(os.path.join(PAGES, f))

    import win32com.client as win32
    from pypdf import PdfReader, PdfWriter

    # Phase A: 読み取り(不変シグネチャ)
    wb = app.Workbooks.Open(XLSX, UpdateLinks=0, ReadOnly=True)
    names = [sh.Name for sh in wb.Worksheets]
    if book == "pana":
        assert "表紙" not in names and names[0] == "目次", f"unexpected order: {names}"
        assert names == ["目次", "用語", "構成と管理情報", "相関図", "相関図_old", "管理体制",
                         "月次再起動", "バックアップ", "復旧", "異常時の対応",
                         "チェックシート(月次・異常時)", "会議課題一覧(一時)", "付録 引用元と確認範囲",
                         "要確認事項一覧", "7-5仮_サービス起動停止"], names
    else:
        assert names == ["表紙", "目次", "用語", "構成と管理情報", "相関図", "相関図_old", "管理体制",
                         "日次点検", "定期管理", "バックアップ", "復旧", "異常時の対応",
                         "チェックシート(日次)", "チェックシート(月次・異常時)", "会議課題一覧(一時)",
                         "要確認事項一覧", "申し送り(認証情報)", "認証情報一覧", "引用と部品照合"], names
    wsmap = {sh.Name: sh for sh in wb.Worksheets}
    qhash = {}
    for sheet, cells in cfg["quote"]:
        for a in cells:
            qhash[f"{sheet}!{a}"] = wsmap[sheet].Range(a).Text
    # 空セルは許容(不変性の照合が目的)。件数のみ報告する
    R["quote_empty"] = sorted(k for k, v in qhash.items() if not v)
    # 構成の挿入点確認
    K = wsmap["構成と管理情報"]
    if book == "pana":
        k_anchor = (16, str(K.Range("A16").Value), 21, str(K.Range("A21").Value))
    else:
        k_anchor = (103, str(K.Range("A103").Value), 108, str(K.Range("A108").Value))
    close_wb(wb)
    # 引用セルの本文は Report に書かない(鍵と空セルの位置のみ)
    R["quote_cells"] = sorted(qhash.keys())
    R["kousei_anchor"] = {"row": k_anchor[0], "has": "相関図" in k_anchor[1],
                          "next_row": k_anchor[2], "next_has_value": bool(k_anchor[3])}
    act(f"{book}: Phase A ok (quote {len(qhash)}, kousei A{k_anchor[0]}, next A{k_anchor[2]})")

    # Phase B: 編集
    wb = app.Workbooks.Open(XLSX, UpdateLinks=0, ReadOnly=False)
    try:
        wb.AutoSaveOn = False
    except Exception:
        pass
    wsmap = {sh.Name: sh for sh in wb.Worksheets}
    src = wsmap["相関図"]
    T = harvest(src, book)
    counts_all = {}
    # 改名+複製(Copy(After=X) の直後、新シートは X.Index+1 の位置に現れる)
    src.Name = "相関図①"
    sheets = {"①": src}
    for g, nm in ((2, "相関図②"), (3, "相関図③")):
        after = wb.Worksheets("相関図①") if g == 2 else wb.Worksheets("相関図②")
        src.Copy(After=after)
        new = wb.Worksheets(after.Index + 1)
        new.Name = nm
        sheets["①②③"[g - 1]] = new
    names_b = [sh.Name for sh in wb.Worksheets]
    i1, i2, i3, iold = names_b.index("相関図①"), names_b.index("相関図②"), names_b.index("相関図③"), names_b.index("相関図_old")
    assert i2 == i1 + 1 and i3 == i2 + 1 and iold == i3 + 1, f"order: {names_b}"
    act(f"{book}: sheets renamed/copied")

    for g, key in ((1, "①"), (2, "②"), (3, "③")):
        ws = sheets[key]
        S = sheet_spec(g, T)
        delete_all_shapes(ws)
        for a in T["clear"]:
            ws.Range(a).Value = ""
        for r0, r1 in T["shrink"]:  # 空になった説明セル行を本文行と同じ高さへ
            for rr in range(r0, r1 + 1):
                ws.Rows(rr).RowHeight = 7.7
        c = build_sheet(ws, g, S, T)
        area, mx, my = compute_print_area(ws, cfg["lastcol"])
        c["print_area"] = area
        c["extent"] = [mx, my]
        counts_all[key] = c
        c_term = {k: (len(v) if isinstance(v, list) else v) for k, v in c.items()}
        act(f"{book}: sheet{key} built {c_term}")
    R["counts"] = counts_all
    R["adj_fail"] = set_adj.fail  # 丸角設定の失敗数(既定値で代替される)
    set_adj.fail = 0
    R["fareast_fail"] = set_fareast.fail  # FarEast フォント設定の失敗数
    set_fareast.fail = 0

    # 目次
    TO = wsmap["目次"]
    if book == "pana":
        assert str(TO.Range("D8").Value) == "相関図", "toc D8"
        TO.Rows(9).Insert(CopyOrigin=1)
        TO.Rows(9).Insert(CopyOrigin=1)
        for r, (no, nm) in ((8, ("2-2", "相関図①")), (9, ("2-3", "相関図②")), (10, ("2-4", "相関図③"))):
            TO.Range(f"C{r}").Value = no
            TO.Range(f"D{r}").Value = nm
            TO.Rows(r).RowHeight = 12.8
        assert str(TO.Range("C11").Value).startswith("3"), "toc shift"
        R["toc"] = {"rows": [8, 9, 10], "renumber_shift": "rows>=9 shifted +2"}
    else:
        assert str(TO.Range("B8").Value) == "相関図", "toc B8"
        TO.Rows(9).Insert(CopyOrigin=1)
        TO.Rows(9).Insert(CopyOrigin=1)
        for r, (no, nm) in ((8, ("2-3", "相関図①")), (9, ("2-4", "相関図②")), (10, ("2-5", "相関図③"))):
            TO.Range(f"A{r}").Value = no
            TO.Range(f"B{r}").Value = nm
            TO.Range(f"C{r}").Value = no
            TO.Rows(r).RowHeight = 12.8
        assert str(TO.Range("A11").Value).startswith("3"), "toc shift"
        R["toc"] = {"rows": [8, 9, 10], "renumber_shift": "rows>=9 shifted +2"}

    # 構成と管理情報
    K = wsmap["構成と管理情報"]
    if book == "pana":
        assert "相関図" in str(K.Range("A16").Value)
        K.Range("A16").Value = "2-2 相関図① 全体の関わり"
        old_c20 = str(K.Range("C20").Value)
        new_c20 = old_c20.replace("「相関図」シートを参照",
                                  "「相関図①」「相関図②」「相関図③」シートを参照")
        assert new_c20 != old_c20, "C20 replace no-op"
        K.Range("C20").Value = new_c20
        old_c19 = str(K.Range("C19").Value)
        new_c19 = old_c19.replace("テキストボックス・コネクタ", "テキストボックス・直線・オートシェイプ")
        assert new_c19 != old_c19, "C19 replace no-op"
        K.Range("C19").Value = new_c19
        for r, (a, c) in ((21, ("2-3 相関図② PanaCIM管理側の内部",
                                "配置：「相関図②」シートを参照。管理対象(サーバ·端末·保存領域)とデータの退避·出力先を示す。")),
                          (22, ("2-4 相関図③ ライン設備側の内部",
                                "配置：「相関図③」シートを参照。ライン設備の装置·端末と、LNBを中心としたデータの流れを示す。"))):
            K.Rows(20).Copy()
            K.Rows(r).Insert()
            K.Range(f"A{r}").Value = a
            K.Range(f"B{r}").Value = ""
            K.Range(f"C{r}").Value = c
            K.Range(f"C{r}").WrapText = True  # 高さはコピー行のままで Excel に委譲(実測しない)
        R["kousei"] = {"renamed": "A16", "updated": ["C19", "C20"], "inserted": [21, 22]}
    else:
        assert "相関図" in str(K.Range("A103").Value)
        K.Range("A103").Value = "2-3 相関図① 全体の関わり"
        old_c104 = str(K.Range("C104").Value)
        new_c104 = old_c104.replace("「相関図」シートを参照",
                                    "「相関図①」「相関図②」「相関図③」シートを参照")
        assert new_c104 != old_c104, "C104 replace no-op"
        K.Range("C104").Value = new_c104
        old_c106 = str(K.Range("C106").Value)
        new_c106 = old_c106.replace("テキストボックス・フリーフォーム直線・ラベル",
                                    "テキストボックス・直線・オートシェイプ・ラベル")
        assert new_c106 != old_c106, "C106 replace no-op"
        K.Range("C106").Value = new_c106
        old_c107 = str(K.Range("C107").Value)
        new_c107 = old_c107.replace("「相関図」シートを参照",
                                    "「相関図①」「相関図②」「相関図③」シートを参照")
        assert new_c107 != old_c107, "C107 replace no-op"
        K.Range("C107").Value = new_c107
        for r, (a, c) in ((108, ("2-4 相関図② PanaCIM管理側の内部",
                                 "配置：「相関図②」シートを参照。管理対象(サーバ·端末·保存領域)とデータの退避·出力先を示す。")),
                          (109, ("2-5 相関図③ ライン設備側の内部",
                                 "配置：「相関図③」シートを参照。ライン設備の装置·端末と、LNBを中心としたデータの流れを示す。"))):
            K.Rows(107).Copy()
            K.Rows(r).Insert()
            K.Range(f"A{r}").Value = a
            K.Range(f"B{r}").Value = ""
            K.Range(f"C{r}").Value = c
            K.Range(f"C{r}").WrapText = True  # 高さはコピー行のままで Excel に委譲(実測しない)
        R["kousei"] = {"renamed": "A103", "updated": ["C104", "C106", "C107"], "inserted": [108, 109]}

    # 不変検証(保存前)
    wsmap2 = {sh.Name: sh for sh in wb.Worksheets}
    q2 = {}
    for sheet, cells in cfg["quote"]:
        for a in cells:
            q2[f"{sheet}!{a}"] = wsmap2[sheet].Range(a).Text
    assert q2 == qhash, "quote changed during build!"
    if "相関図_old" in wsmap2:
        assert wsmap2["相関図_old"].Shapes.Count == 34, "old shapes changed"
    wb.Save()
    act(f"{book}: SAVED pass1")

    # Phase C: 頁実測→採番→冊PDF — すべて保存済みファイルのローカルコピーに対する
    # 短命インスタンスで実行する(長時間生存インスタンスの PageSetup/Export は
    # 0x800a01a8 で不安定化する実害があるため)。編集インスタンスはここで役目を終える。
    close_wb(wb)
    order = cfg["order"]
    local = os.path.join(PAGES, f"_src_{book}.xlsx")
    copy_vault(XLSX, local)

    def export_all(local_path, with_book=False):
        import win32com.client as win32
        app2 = win32.DispatchEx("Excel.Application")
        app2.Visible = False
        app2.DisplayAlerts = False
        try:
            wb2 = app2.Workbooks.Open(local_path, UpdateLinks=0, ReadOnly=True)
            counts = {}
            for name in order:
                p = os.path.join(PAGES, f"{book}_{name}.pdf")
                for attempt in range(3):
                    try:
                        wb2.Worksheets(name).ExportAsFixedFormat(0, p, 0, True, False)
                        break
                    except Exception:
                        if attempt == 2:
                            raise
                        time.sleep(2.0)
                counts[name] = len(PdfReader(p).pages)
            if with_book:
                bp = os.path.join(PAGES, f"{book}_BOOK.pdf")
                wb2.ExportAsFixedFormat(0, bp, 0, True, False)
            wb2.Close(SaveChanges=False)
        finally:
            try:
                app2.Quit()
            except Exception:
                pass
        return counts

    counts = export_all(local)
    R["pages"] = counts
    total = sum(counts.values())
    act(f"{book}: PAGES {counts} total={total}")
    assert total == cfg["expect_pages"], f"pages {total} != {cfg['expect_pages']}"

    # 採番(別の短命インスタンスで保存済みローカルコピーに書込み·保存)
    acc = 1
    numbering = {}
    for name in order:
        if name in cfg["auto"]:
            acc += counts[name]
            continue
        numbering[name] = acc
        acc += counts[name]
    R["numbering"] = numbering
    if book == "lnb":
        cred = "申し送り(認証情報)"
        exp_new = (1 + counts["表紙"] + counts[cred]
                   + sum(counts[n] for n in order[1:order.index(cred)]))
        assert numbering["認証情報一覧"] == exp_new, "cred FPN"
    import win32com.client as win32
    app3 = win32.DispatchEx("Excel.Application")
    app3.Visible = False
    app3.DisplayAlerts = False
    try:
        wb3 = app3.Workbooks.Open(local, UpdateLinks=0, ReadOnly=False)
        try:
            wb3.AutoSaveOn = False
        except Exception:
            pass
        for name, fpn in numbering.items():
            for attempt in range(3):
                try:
                    wb3.Worksheets(name).PageSetup.FirstPageNumber = fpn
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    time.sleep(2.0)
        wb3.Save()
        wb3.Close(SaveChanges=False)
    finally:
        try:
            app3.Quit()
        except Exception:
            pass
    act(f"{book}: SAVED pass2 (numbering)")

    counts2 = export_all(local, with_book=True)
    assert counts2 == counts, f"pagination shifted: {counts2}"
    act(f"{book}: PASS2 ok")

    # 冊PDF (cred(auto)頁は冊エクスポートから補完)
    bookpdf = os.path.join(PAGES, f"{book}_BOOK.pdf")
    bookrd = PdfReader(bookpdf)
    assert len(bookrd.pages) == total, "book pages"
    writer = PdfWriter()
    if book == "lnb":
        cred = "申し送り(認証情報)"
        offset = sum(counts[n] for n in order[:order.index(cred)])
        for name in order:
            if name == cred:
                for i in range(offset, offset + counts[cred]):
                    writer.add_page(bookrd.pages[i])
            else:
                for pg in PdfReader(os.path.join(PAGES, f"{book}_{name}.pdf")).pages:
                    writer.add_page(pg)
    else:
        for name in order:
            for pg in PdfReader(os.path.join(PAGES, f"{book}_{name}.pdf")).pages:
                writer.add_page(pg)
    bookpdf_local = os.path.join(PAGES, f"{book}_BOOK_local.pdf")
    with open(bookpdf_local, "wb") as f:
        writer.write(f)
    assert len(PdfReader(bookpdf_local).pages) == total, "vault pdf"
    copy_vault(bookpdf_local, cfg["pdf"])
    act(f"{book}: BOOK -> {cfg['pdf']} ({total}p)")

    # 最終不変検証(別の短命インスタンスでローカルコピーを読み取り·メモリ内で照合)
    app4 = win32.DispatchEx("Excel.Application")
    app4.Visible = False
    app4.DisplayAlerts = False
    try:
        wb4 = app4.Workbooks.Open(local, UpdateLinks=0, ReadOnly=True)
        q3 = {}
        wsm = {sh.Name: sh for sh in wb4.Worksheets}
        for sheet, cells in cfg["quote"]:
            for a in cells:
                q3[f"{sheet}!{a}"] = wsm[sheet].Range(a).Text
        assert q3 == qhash, "quote changed after save!"
        if book == "lnb":
            assert "申し送り(認証情報)" in wsm  # cred シートの存在確認のみ
        wb4.Close(SaveChanges=False)
    finally:
        try:
            app4.Quit()
        except Exception:
            pass
    copy_vault(local, XLSX)  # 採番済みの最終状態を vault へ反映
    try:
        os.remove(local)
    except Exception:
        pass
    R["sha_after"] = sha256(XLSX)
    R["quote_ok"] = True
    return R

def main():
    import win32com.client as win32
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    app.AskToUpdateLinks = False
    try:
        app.AutomationSecurity = 3
    except Exception:
        pass
    try:
        app.AutoSaveOn = False
    except Exception:
        pass
    try:
        for book in ("pana", "lnb"):
            REP["books"][book] = process(app, book, BOOKS[book])
    finally:
        app.Quit()
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(REP, f, ensure_ascii=False, indent=1, default=str)
    for b, r in REP["books"].items():
        print(b, "pages", sum(r["pages"].values()), "sha", r["sha_after"][:16], flush=True)
    print("DONE", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        REP["errors"].append(traceback.format_exc())
        try:
            with open(REPORT, "w", encoding="utf-8") as f:
                json.dump(REP, f, ensure_ascii=False, indent=1, default=str)
        except Exception:
            pass
        sys.exit(1)
