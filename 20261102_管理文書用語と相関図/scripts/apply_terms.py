# -*- coding: utf-8 -*-
"""用語シートへの追記適用(XML直編集·openpyxl不使用)。

- 編集対象は xl/worksheets/sheet3.xml(用語) と xl/sharedStrings.xml のみ
- 他の全メンバーは元のバイトを ZipInfo ごと(圧縮·日時·属性含む)そのまま書き写す
  → xl/drawings/* と xl/worksheets/_rels はバイト一致が保証される
- 行属性·セルスタイルは既存最終エントリ(C18/C17)と同一の形式
"""
import zipfile, shutil, hashlib, os, re, json, io
import xml.etree.ElementTree as ET

VAULT = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
TMP = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\20261102_terms"

PANA_TERMS = [
    "VMware：仮想化基盤の製品名。CIMC-SV は VMware 上の仮想マシンであり、VMware の管理画面には CIM-A PC から入る(第7章7-4 手順9)",
    "Red Hat Enterprise Linux(RHEL)：CIMC-SV のゲストOS。バージョン6・64ビット(第2章2-1)",
    "仮想マシン：仮想化基盤(ESXi)の上で動くマシン。CIMC-SV が該当し、PanaCIM のアプリケーションサーバー・コントローラーサーバーも ESXi 上の VM として運用されている(第2章2-1・相関図)",
    "データベース：Pana-CIM で「データベースユーティリティ」→「バックアップ」の対象になる領域。バックアップ場所の例は E:\\BackUP_DB(第5章5-1・付録A-1)",
    "データベース完全バックアップ(FULbak)：Pana-CIM のバックアップ取得時に表示される完了メッセージ「データベース完全バックアップに成功しました。」の語。ファイル名は PANACIM_<日付>_<時刻>_FULbak(第5章5-1 手順4・6・付録A-1)",
    "PanaCIM アプリケーションサーバー／コントローラーサーバー：公式構成図に示される2系統のサーバー(ESXi使用)。相関図では ESXi 上の VM「CIMC-SV」として運用とある。本書の管理対象との対応付けは要確認(付録A-2・第11章 No.25・相関図)",
    "Webクライアント：公式構成図に示される構成要素。自社での使用状況は要確認(付録A-2・第2章2-1)",
    "サービスコントローラー：PanaCIM 関連サービスの開始・停止・再起動を一元管理する画面。第7章7-5(仮実装・未承認)にベンダー取扱説明書(導入編 N7201A442J28 p213)から引用している",
    "サーバーマネージャー：CIM-A PC のログオン時に起動している管理画面。異常時再起動の手順8で閉じる(第7章7-4 手順8)",
    "Firefox：CIM-A PC で VMware の管理画面へ入るために使うソフト。異常時再起動の手順9で Firefoxアイコン→VMWareアイコンの順に選択する(第7章7-4 手順9)",
    "メンテナンスサーバー：相関図に登場するサーバー系。当サイトへの導入有無は未確認(相関図)",
    "無線スキャナー(PDA)：ライン毎に前側用/後側用がある携帯端末。部品照合は LNB 設定が前提(相関図)",
    "ナビゲータ：ESXiホスト画面で仮想マシンを操作するための表示。月次再起動の操作画面には ESXiホスト画面とナビゲータが表示される(第4章4-4)",
]

LNB_TERMS = [
    "HTTP：暗号化なしの通信方式。LNB の接続は HTTP(ポート8080)で、接続用ショートカットに利用者名とパスワードが埋め込まれている(§2-2・§13)",
    "ポート：通信の受け口の番号。LNB の接続先はポート 8080(§2-2)",
    "IPアドレス：ネットワーク上の機器に付く番号。LNB はライン別に 172.25.253.11/21/31、DGS は 172.25.253.10、ESXiホストは 172.25.253.45(§2-2)",
    "オクテット：IPアドレスを4つに区切った各部分。本書では第4オクテットが 11/21/31 と並び、ラインごとに10ずつ繰り上がる付番と見えるとしている(§2-2)",
    "Ping：ネットワーク上の機器に届くかを確認する機能。LWS の Pingチェック画面に上位システム(172.25.253.10)や基板バーコードスキャナ(192.168.0.1)が表示される(§12 No.36)",
    "URL：接続先のアドレス。LNB の接続 URL は /lws/Login.do で、/lws/ の経路を含む(§2-2)",
    "無線スキャナー：ラインで部品照合に使う携帯端末。LNB接続状態(無線スキャナーと LNB の接続状態)の表示対象で、使用には LNB設定の部品照合設定が必要(§4 Step1・付録A-1・付録A-2・§14)",
    "部品照合：無線スキャナーで部品を照合する機能。使用には LNB設定の部品照合設定が必要(付録A-2・§14)。自社での有効化状況は未確認(§12 No.28)",
    "FAパソコン：公式の NPMライン構成図に「LNB(FAパソコン)」と記載される PC。社内で LNB と呼ぶ対象と同じかは未確認(付録A-3・§12 No.29)",
    "ハイパーバイザ：物理サーバの上で仮想マシンを動かす基盤ソフト。相関図では ESXiホストを【サーバ(物理/ハイパーバイザ)】として示す(相関図)",
    "ジョブ：DGS で登録する処理の単位。現行の LNB 運用では、ジョブを消す前に過去ジョブへエクスポートし、必要時にインポートして戻す(§6・参考添付1〜3)",
    "LNB-PC：LWS 端末の PC。LWS の再起動ページに「LNB-PC電源OFF」「LNB-PCリブート」のボタンがある。LNB-PCリブートを PC自体の再起動とする対応付けは要確認(§12 No.30・37)",
    "稼働率データ：Pana-CIM が出力するライン別の稼働情報(HTML形式)。稼働率フォルダに保存され、期間・ロット一覧・仕損率[PPM]・1〜7台目の稼働情報を含む(§12 No.32)",
    "NPM：生産設備のマシン名に使われる呼称。LNB構成情報画面の L1 設備一覧では L1NPM-1〜7・SP70-1 と現れる。L2/L3 の同画面は未確認(§12 No.34)",
    "ブラウザ：LNB の操作画面(LWS)を開くソフト。点検に使う OS・ブラウザは要確認(§2-2・相関図)",
]

JOBS = [
    dict(path=VAULT + r"\Pana-CIM管理手順書案_未承認.xlsx", style="10",
         first_row=19, last_dim_row=18, terms=PANA_TERMS, tag="pana"),
    dict(path=VAULT + r"\LNB管理手順書案_未承認.xlsx", style="13",
         first_row=18, last_dim_row=17, terms=LNB_TERMS, tag="lnb"),
]

SHEET3 = "xl/worksheets/sheet3.xml"
SHARED = "xl/sharedStrings.xml"

def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def sha(b):
    return hashlib.sha256(b).hexdigest()

results = []
for job in JOBS:
    path = job["path"]
    tag = job["tag"]
    res = {"tag": tag, "file": os.path.basename(path)}
    assert os.path.exists(path), path

    # 0) 編集前コピー(検証用·temp)
    bak = os.path.join(TMP, os.path.basename(path) + ".pre_20261102.xlsx")
    shutil.copy2(path, bak)
    res["backup"] = bak

    # 1) 全メンバー読み込み
    zin = zipfile.ZipFile(path)
    members = [(info, zin.read(info.filename)) for info in zin.infolist()]
    zin.close()
    before = {name: sha(data) for name, data in ((i.filename, d) for i, d in members)}
    res["members_before"] = len(members)

    # 2) sharedStrings の追記
    ss_data = dict((i.filename, d) for i, d in members)[SHARED].decode("utf-8")
    m = re.search(r'count="(\d+)" uniqueCount="(\d+)"', ss_data)
    assert m, "sst header not found"
    count, uniq = int(m.group(1)), int(m.group(2))
    n = len(job["terms"])
    start_idx = uniq
    old_attr = 'count="%d" uniqueCount="%d"' % (count, uniq)
    new_attr = 'count="%d" uniqueCount="%d"' % (count + n, uniq + n)
    assert ss_data.count(old_attr) == 1
    ss_new = ss_data.replace(old_attr, new_attr, 1)
    new_sis = "".join("<si><t>%s</t></si>" % esc(t) for t in job["terms"])
    assert ss_new.count("</sst>") == 1
    ss_new = ss_new.replace("</sst>", new_sis + "</sst>", 1)
    ET.fromstring(ss_new)  # 整合性(パース可)

    # 3) 用語シートの行追加
    sx_data = dict((i.filename, d) for i, d in members)[SHEET3].decode("utf-8")
    dim_old = '<dimension ref="A1:AZ%d"/>' % job["last_dim_row"]
    dim_new = '<dimension ref="A1:AZ%d"/>' % (job["last_dim_row"] + n)
    assert sx_data.count(dim_old) == 1, dim_old
    sx_new = sx_data.replace(dim_old, dim_new, 1)
    rows = []
    for k, term in enumerate(job["terms"]):
        r = job["first_row"] + k
        rows.append(
            '<row r="%d" spans="3:3" ht="12.75" customHeight="1" x14ac:dyDescent="0.3">'
            '<c r="C%d" s="%s" t="s"><v>%d</v></c></row>' % (r, r, job["style"], start_idx + k))
    assert sx_new.count("</sheetData>") == 1
    sx_new = sx_new.replace("</sheetData>", "".join(rows) + "</sheetData>", 1)
    ET.fromstring(sx_new)  # 整合性(パース可)

    # 4) zip再構築(他メンバーは元バイト·元ZipInfoのまま)
    out_path = path + ".tmp_new"
    with zipfile.ZipFile(out_path, "w") as zout:
        for info, data in members:
            if info.filename == SHARED:
                data = ss_new.encode("utf-8")
            elif info.filename == SHEET3:
                data = sx_new.encode("utf-8")
            zout.writestr(info, data)
    os.replace(out_path, path)

    # 5) 即時再読みで差分確認
    z2 = zipfile.ZipFile(path)
    after = {name: sha(z2.read(name)) for name in z2.namelist()}
    z2.close()
    changed = sorted([nm for nm in before if before[nm] != after.get(nm)])
    missing = sorted([nm for nm in before if nm not in after])
    added = sorted([nm for nm in after if nm not in before])
    res["changed_members"] = changed
    res["missing_members"] = missing
    res["added_members"] = added
    res["drawings_unchanged"] = all(before[nm] == after[nm] for nm in before if nm.startswith("xl/drawings/"))
    res["ws_rels_unchanged"] = all(before[nm] == after[nm] for nm in before if nm.startswith("xl/worksheets/_rels"))
    res["new_string_indices"] = list(range(start_idx, start_idx + n))
    res["rows_added"] = ["C%d" % (job["first_row"] + k) for k in range(n)]
    results.append(res)

with open(os.path.join(TMP, "apply_result.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)
print("APPLY OK")
for r in results:
    print(r["tag"], "changed:", r["changed_members"], "drawings_ok:", r["drawings_unchanged"],
          "wsrels_ok:", r["ws_rels_unchanged"], "missing:", r["missing_members"], "added:", r["added_members"])
