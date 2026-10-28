# -*- coding: utf-8 -*-
"""corr_pana_13_measure_text.py — テキスト収まりの実測(保存しない)
指定幅のテキストボックスを仮設置し TextFrame2.TextRange.BoundWidth/BoundHeight を測る。
対象: (A) ノードN02文(幅105pt·11/10pt) (B) X02全文(幅180pt·10pt) (C) ラベルE02(幅150pt·10pt) (D) N08文(幅135pt)
"""
import json, time, subprocess, os

HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(HERE, "corr_dryrun_pana.xlsx")
RESULT = os.path.join(HERE, "corr_pana_13_measure_result.json")
out = {"ok": False, "pid": None, "cases": {}, "errors": []}

import win32com.client
import win32process

CASES = [
    ("A_node_n02", 105.0, 11.0, 10.0,
     "【サーバ(VM)】PanaCIMアプリケーションサーバー",
     "当SiteはESXi上VM「CIMC-SV」として運用(PanaCIM(CIMA)環境·X02-⑪)"),
    ("B_x02_full", 180.0, 10.0, None,
     "①アンドンとLNB/PanaCIMの接続(T3·2026-10-27照査: 表示内容はPanaCIM/実装機由来と整合·直接経路は未発見) "
     "②ノズルデータ/リーダーデータのLNB経由経路(T3·2026-10-27照査: ノズル在庫は在庫台帳·DGS-SV固定化ファイルで管理·LNB経由の証跡なし) "
     "③再起動順序の詳細·LNBを含む全体順(T3·対象一覧はT1b確定) ④部品情報の流入元·経路(T2で流入は確認·経路は未確認) "
     "⑤無線AP·Androidタブレット·メンテナンスサーバーの当Site導入状況(T1構成機器のみで実確認なし) "
     "⑥LNB⇔PanaCIM間データの向き(関係図備考: 実機未確認) ⑦LWSと仕様説明書「LWSエディター」の同一性 "
     "⑧iLNBと社内LNBの同一性·iLNB対応網の当Site適用可否 ⑨E-Link·GEM通信の使用有無 "
     "⑩NPM-DGSの管理境界 ⑪CIMA-SVとCIMC-SVの環境名と製品構成の対応·本書管理範囲·両者の関係 "
     "⑫DGS-SVとNPM-DGSの同一性·DGS系ローカルネットワークの構成·N06の所属セグメント",
     None),
    ("C_label_e02", 150.0, 10.0, None,
     "実装データの収集·上位送信〔T1:-7-/-8-〕", None),
    ("D_node_n08", 135.0, 11.0, 10.0,
     "【設備】NPM X/NPM/AMライン(実装機)",
     "L1=NPM-1〜7·SP70-1(2026-10-14 LNB構成情報画面)"),
]

xl = win32com.client.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
out["pid"] = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
print("EXCEL PID", out["pid"], flush=True)

try:
    wb = xl.Workbooks.Open(DST)
    ws = wb.Worksheets("相関図")

    def measure(text, boxw, fs):
        shp = ws.Shapes.AddTextbox(1, 100.0, 100.0, boxw, 30.0)
        tf = shp.TextFrame2
        tf.WordWrap = -1
        tf.AutoSize = 0
        tf.MarginLeft = 2.0; tf.MarginRight = 2.0; tf.MarginTop = 1.0; tf.MarginBottom = 1.0
        rng = tf.TextRange
        rng.Text = text
        rng.Font.NameFarEast = "Meiryo UI"
        rng.Font.Name = "Meiryo UI"
        rng.Font.Size = fs
        bh = tf.TextRange.BoundHeight
        bw = tf.TextRange.BoundWidth
        shp.Delete()
        return bw, bh

    for name, boxw, fs1, fs2, t1, t2 in CASES:
        w1, h1 = measure(t1, boxw, fs1)
        entry = {"box_w": boxw, "p1_bound_w": round(w1, 1), "p1_bound_h": round(h1, 1)}
        if t2:
            w2, h2 = measure(t2, boxw, fs2 if fs2 else fs1)
            entry["p2_bound_h"] = round(h2, 1)
            entry["total_h"] = round(h1 + h2, 1)
        else:
            entry["total_h"] = round(h1, 1)
        out["cases"][name] = entry
        print(name, entry, flush=True)
    wb.Close(False)
    out["ok"] = True
finally:
    try:
        xl.Quit()
    except Exception as e:
        out["errors"].append("quit:" + repr(e)[:80])
    time.sleep(2)
    try:
        chk = subprocess.run(["tasklist", "/FI", "PID eq %d" % out["pid"]], capture_output=True, text=True)
        if "EXCEL" in chk.stdout.upper():
            subprocess.run(["taskkill", "/PID", str(out["pid"]), "/F"], capture_output=True)
            out["errors"].append("killed residual %d" % out["pid"])
    except Exception as e:
        out["errors"].append("cleanup:" + repr(e)[:80])

with open(RESULT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("ok:", out["ok"])
