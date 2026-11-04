# -*- coding: utf-8 -*-
"""fix30_gpass_pana.py — 計画§9 G-pass: Pana-CIM冊への G1·G2·G5·G6·G7 適用(エントリ30)。

- G5: 未確認注記·評価語·括弧内相互参照を本文から除去し、要確認事項一覧へ集約((a)本文削除/(b)様式欄値消去/(c)出典メタ整理)。
- G2: チェックシート 8-1 に手順本文(バックアップ §5-1 手順4·6)から導出した項目を記入(捏造禁止·導出元を変更リストへ記録)。
- G6: チェックシートの日時欄ラベル(8-1 A7·8-2 C12·8-3 E23·8-4 A37)を消去。8-5 承認日は保持(承認成立の基本要素)。
- G7: 異常時 C28 の装飾記号「■」を除去(付録C20 の■は完全引用区間につき対象外)。
- 要確認事項一覧: 既存 No.4·11·18·19·25·27 へ追記+新規 No.29〜37(9項目·行37-45)+印刷範囲 AZ46。
- 不変: 完全引用区間(異常時C42〜C63·付録C9/C10/C14/C17/C20·7-5仮C12〜C18)·会議課題一覧·相関図_old·置換禁止表記。
- 後処理: 保存→全シート頁実測→幽霊0検定→FirstPageNumber再設定→冊PDF再構築(pypdf·頁数アサート)→SHA-256記録。
"""
import os, sys, json, math, shutil, hashlib, traceback

sys.stdout.reconfigure(encoding="utf-8")

WORK = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
XLSX = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\Pana-CIM管理手順書案_未承認.xlsx"
VAULT_PDF = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\Pana-CIM管理手順書案_未承認.pdf"
PAGES_DIR = os.path.join(WORK, "scripts", "tmp_pages30_pana")
BACKUP = os.path.join(WORK, "backup_20261102", "Pana-CIM管理手順書案_未承認_Gpass前_20261104.xlsx")
REPORT = os.path.join(WORK, "scripts", "fix30_gpass_pana_report.json")

ORDER = ["表紙", "目次", "用語", "構成と管理情報", "相関図", "相関図_old", "管理体制",
         "月次再起動", "バックアップ", "復旧", "異常時の対応", "チェックシート(月次・異常時)",
         "会議課題一覧(一時)", "付録 引用元と確認範囲", "要確認事項一覧", "7-5仮_サービス起動停止"]
IMG_SHEETS = ("月次再起動", "バックアップ", "異常時の対応", "7-5仮_サービス起動停止")
LIST_SHEET = "要確認事項一覧"
LIST_LAST_ROW = 36          # No.28 の行(複製テンプレート)
LIST_NEW_ROWS = 45          # 新規9項目の最終行
LIST_AREA = "$A$1:$AZ$46"
QUOTE_CELLS = ([(f"C{r}", "異常時の対応") for r in range(42, 64)]
               + [("C9", "付録 引用元と確認範囲"), ("C10", "付録 引用元と確認範囲"),
                  ("C14", "付録 引用元と確認範囲"), ("C17", "付録 引用元と確認範囲"),
                  ("C20", "付録 引用元と確認範囲")]
               + [(f"C{r}", "7-5仮_サービス起動停止") for r in range(12, 19)])
FORBID_STRINGS = {"windwos": "異常時の対応", "Route Editer": "用語"}

COLS = [chr(65 + i) for i in range(26)] + ["A" + chr(65 + i) for i in range(26)]

REP = {"sha_before": None, "sha_backup": None, "edits": [], "list_rows": [], "quote_ok": None,
       "counts": {}, "numbering": {}, "book_pages": None, "sha_after": None, "errors": []}


def act(msg):
    print("[act]", msg, flush=True)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def get_val(ws, addr):
    v = ws.Range(addr).Value
    return "" if v is None else str(v)


def px(w):
    return int(((256.0 * w + 18.0) / 256.0) * 7) + 5


def units(s):
    return sum(1.0 if ord(ch) > 0x2E80 else 0.5 for ch in s)


def calc_lines(text, width_pt, size):
    per = max(4.0, width_pt / size)
    n = 0
    for seg in str(text).split("\n"):
        n += max(1, math.ceil(units(seg) / per - 1e-9))
    return n


EDITS = []


def edit(ws, sheet, cell, g, new_text=None, removals=None, anchors=()):
    old = get_val(ws, cell)
    for a in anchors:
        assert a in old, f"[anchor] {sheet}!{cell} に「{a}」なし: {old[:60]}"
    t = old
    for (o, n) in (removals or []):
        assert o in t, f"[removal] {sheet}!{cell} に「{o}」なし"
        t = t.replace(o, n)
    if new_text is not None:
        t = new_text
    assert t != old, f"[nochange] {sheet}!{cell}"
    ws.Range(cell).Value = t
    EDITS.append({"sheet": sheet, "cell": cell, "g": g, "old": old, "new": t})


def edit_append(ws, sheet, cell, g, add, anchors=()):
    old = get_val(ws, cell)
    for a in anchors:
        assert a in old, f"[anchor] {sheet}!{cell}: {old[:60]}"
    t = old.rstrip() + add
    ws.Range(cell).Value = t
    EDITS.append({"sheet": sheet, "cell": cell, "g": g, "old": old, "new": t})


NEW_ITEMS = [
    "29：出典資料の文書番号·版·保管場所の特定／不具合別ログリスト_取得手順_Ｊ.pdf(§5)·サーバー再起動.pptx(§4)·相関図の出典符(T1〜T3)に掲げた資料",
    "30：IP·OS·表記の一次資料確認／CIMC-SV のゲストOS(RHEL 6)の版数·ESXiホスト画面の表記 IP·構成図表記の IP と OS·NPM·FA の略語の展開。本文の自動走査の試行はセキュリティガードの拒否により未実施(2026-11-04)",
    "31：Web 版アンドン／IP 172.25.253.42 は別系統。MonitorAndon2 との連携と Pana-CIM との関係／現行実施者",
    "32：稼働モニタの表示基盤／会話上は「稼働モニタ異常(Power BI)」。表示基盤が Power BI であるか／現行実施者",
    "33：メンテナンスサーバー／当サイトへの導入有無／現行実施者",
    "34：部品照合と LNB 設定の関係／相関図草案上の記載であり、参照の方向を含めて未確認／現行実施者",
    "35：月次再起動の OS 対応と影響範囲／本章の Windows 手順とゲストOS(RHEL 6)の OS 操作との対応·動作中に再起動を中断した場合の影響範囲／現行実施者、ベンダー",
    "36：7-5(仮)の採否／PanaCIM関連サービスの起動·停止·再起動の手順(ベンダー取扱説明書からの引用)を本書に正式採用するか／作成チーム、管理責任者",
    "37：点検の実施者·記録の確認者·文書の承認者／第3章の3行の確定／作成チーム、管理責任者",
]


def main():
    assert not os.path.exists(BACKUP), f"backup already exists: {BACKUP}"
    REP["sha_before"] = sha256(XLSX)
    shutil.copy2(XLSX, BACKUP)
    REP["sha_backup"] = sha256(BACKUP)
    act(f"BACKUP -> {BACKUP}")
    os.makedirs(PAGES_DIR, exist_ok=True)

    import win32com.client as win32
    try:
        from pypdf import PdfReader, PdfWriter
    except Exception:
        from PyPDF2 import PdfReader, PdfWriter
    import pymupdf

    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    wb = None
    try:
        wb = app.Workbooks.Open(XLSX, UpdateLinks=0, ReadOnly=False)
        try:
            wb.AutoSaveOn = False
        except Exception:
            pass
        wsmap = {sh.Name: sh for sh in wb.Worksheets}
        assert len(wsmap) == 16, f"sheet count {len(wsmap)}"
        assert set(ORDER) == set(wsmap), "ORDER mismatch"

        # ---------- Phase A: 引用区間のハッシュ捕捉 ----------
        qhash = {}
        for cell, sheet in QUOTE_CELLS:
            v = get_val(wsmap[sheet], cell)
            qhash[f"{sheet}!{cell}"] = hashlib.sha256(v.encode("utf-8")).hexdigest()
        REP["quote_before"] = qhash
        act(f"quote cells captured: {len(qhash)}")

        # ---------- Phase B1: 本文編集 ----------
        CK = "チェックシート(月次・異常時)"
        # --- G2: 8-1 の導出項目(根拠: バックアップ §5-1 手順4·6 = バックアップ!C13·C15) ---
        edit(wsmap[CK], CK, "C8", "G2",
             new_text="バックアップを実行し、完了メッセージ「データベース完全バックアップに成功しました。」を確認した：",
             anchors=("：",))
        edit(wsmap[CK], CK, "C9", "G2",
             new_text="保存先の FULbak ファイルを USB または SD カードへコピーし、コピー後に圧縮した：",
             anchors=("：",))
        # --- G6: 日時欄ラベル消去(8-5 承認日は保持) ---
        edit(wsmap[CK], CK, "A7", "G6", new_text="", anchors=("実施日",))
        edit(wsmap[CK], CK, "C12", "G6", new_text="", anchors=("実施日",))
        edit(wsmap[CK], CK, "E23", "G6", new_text="", anchors=("実施時刻",))
        edit(wsmap[CK], CK, "A37", "G6", new_text="", anchors=("発生時刻",))
        # --- G5: チェックシート注記(No.19へ集約) ---
        edit(wsmap[CK], CK, "C20", "G5a", new_text="",
             anchors=("随時再起動の記入欄",))

        # --- 7-5仮 C7 ---
        edit(wsmap["7-5仮_サービス起動停止"], "7-5仮_サービス起動停止", "C7", "G5a",
             removals=[("(第1回記録行22)", ""), ("本シートは仮実装(未承認)。", ""), ("会議(2026-10-28)", "会議")],
             anchors=("位置づけ：",))

        # --- バックアップ ---
        B = "バックアップ"
        edit(wsmap[B], B, "C7", "G5a",
             removals=[("稼働率フォルダに保存される Pana-CIM 出力の HTML が「実績帳票」のバックアップ対象に含まれるかは未確認(第11章 No.28 参照)。", ""),
                       ("での最終実行日時と成否の確認で最終実行日時と成否を確認する。", "で最終実行日時と成否を確認する。")],
             anchors=("バックアップ結果の確認は毎日",))
        edit(wsmap[B], B, "C9", "G5c",
             removals=[("文書番号・版・保管場所の特定は未確認。", "")],
             anchors=("不具合別ログリスト",))
        edit(wsmap[B], B, "C180", "G5a",
             removals=[("(第11章 No.11)", ""), ("原 PDF での表記照合は未実施。", "")],
             anchors=("保存先の表記について",))
        edit(wsmap[B], B, "C183", "G5b",
             removals=[("要確認。", "")], anchors=("命名規則：",))
        edit(wsmap[B], B, "C184", "G5b", new_text="外部媒体の種類と管理：", anchors=("外部媒体",))
        edit(wsmap[B], B, "C185", "G5b", new_text="保持する世代数と期間：", anchors=("世代数",))
        edit(wsmap[B], B, "C186", "G5b", new_text="取得者と取得時刻：", anchors=("取得者",))
        edit(wsmap[B], B, "C187", "G5b", new_text="成否を確認する担当者：", anchors=("成否を確認",))
        edit(wsmap[B], B, "C189", "G5a",
             removals=[("継続期間の照合は未実施", "")], anchors=("Eg-Pro",))

        # --- 復旧 ---
        F = "復旧"
        edit(wsmap[F], F, "C8", "G5b", new_text="実施条件：", anchors=("実施条件",))
        edit(wsmap[F], F, "C9", "G5b", new_text="手順：", anchors=("手順",))
        edit(wsmap[F], F, "C10", "G5b", new_text="確認の頻度：", anchors=("頻度",))
        edit(wsmap[F], F, "C11", "G5b", new_text="記録様式：", anchors=("様式",))
        edit(wsmap[F], F, "C13", "G5a", new_text="", anchors=("復旧試験",))

        # --- 月次再起動 ---
        M = "月次再起動"
        edit(wsmap[M], M, "C12", "G5a",
             removals=[("仮想マシンの OS 操作との対応は未確認。", ""),
                       ("ゲストOS の表記(RHEL 6)の一次資料確認は未実施。", "")],
             anchors=("対象：CIMC-SV",))
        edit(wsmap[M], M, "C14", "G5a",
             removals=[("Windows 更新後の扱いは要確認(RPA機では更新の翌日に再起動する決まりがあるが、Pana-CIM を同じ扱いとするかは未確定)。", "")],
             anchors=("随時再起動は従来どおり",))
        edit(wsmap[M], M, "C18", "G5a",
             removals=[("判断に用いる画面と、動作中とみなす表示は要確認", "")],
             anchors=("完了条件：動作していない",))
        edit(wsmap[M], M, "C19", "G5a",
             removals=[("中断した場合の影響範囲は要確認", "")], anchors=("注意点：",))
        edit(wsmap[M], M, "C27", "G5c",
             removals=[("文書番号・版・保管場所の特定は未確認。", "")], anchors=("サーバー再起動.pptx",))
        edit(wsmap[M], M, "C78", "G5a",
             removals=[("(保管先は未確定・要確認一覧 No.26)", "")], anchors=("本書に書かない",))
        edit(wsmap[M], M, "C80", "G5b", new_text="取り消し可否：", anchors=("取り消し可否",))
        edit(wsmap[M], M, "C81", "G5a",
             removals=[("(判定基準は要確認) ", "")], anchors=("ログインが完了し",))
        edit(wsmap[M], M, "C82", "G5a",
             removals=[("表記の IP アドレスの一次資料確認は未実施。", "")], anchors=("ESXiホスト画面",))
        edit(wsmap[M], M, "C84", "G5a",
             new_text="＊2026-10-13 時点で操作手順書 0494-912039(06)「PanaCIM」シートに異常時再起動の記載を確認済み。月次再起動の記載はなし。",
             anchors=("0494-912039",))
        edit(wsmap[M], M, "C88", "G5a",
             new_text="完了条件：通常時の表示と同じ状態に戻っていること", anchors=("完了条件",))
        edit(wsmap[M], M, "C92", "G5a",
             removals=[("改訂を確認する担当者と確認の時期は要確認。", "")], anchors=("追従：",))

        # --- 構成と管理情報 ---
        K = "構成と管理情報"
        edit(wsmap[K], K, "C11", "G5a",
             removals=[("MonitorAndon2 との連携と Pana-CIM との関係は未確認", "")], anchors=("表示系：",))
        edit(wsmap[K], K, "C12", "G5b", new_text="台数・設置場所：", anchors=("台数",))
        edit(wsmap[K], K, "C13", "G5b", new_text="バージョン：", anchors=("バージョン",))
        edit(wsmap[K], K, "C15", "G5a",
             new_text="＊公式資料(PanaCIM-EE 外部インターフェース N7201A522J17)には、PanaCIM アプリケーションサーバー/コントローラーサーバー(ESXi使用)、Webクライアント、LNB(FAパソコン)、NPM-DGS が構成図として示されている。本項は構成図の内容の要約であり、NPM・FA の略語の展開は推測で補わない。",
             anchors=("公式資料",))
        edit(wsmap[K], K, "C19", "G5a",
             removals=[("ZZZ-90000 へ登録できる図の形式は要確認。", "")], anchors=("作図の形式：",))

        # --- 用語 ---
        Y = "用語"
        edit(wsmap[Y], Y, "C9", "G5a",
             removals=[("言及されており、表示基盤が Power BI であるかは要確認", "言及されている。")],
             anchors=("稼働モニタ：",))
        edit(wsmap[Y], Y, "C12", "G5a",
             removals=[("OS の版数と表記の IP アドレスの一次資料確認は未実施。", "")],
             anchors=("CIMC-SV：",))
        edit(wsmap[Y], Y, "C13", "G5a", removals=[("(第7章7-4)", "")], anchors=("CIM-C PC",))
        edit(wsmap[Y], Y, "C17", "G5a", removals=[("(第7章7-4 手順14)", "")], anchors=("Route Editer",))
        edit(wsmap[Y], Y, "C18", "G5a",
             removals=[("。本書での位置づけは要確認", "。")], anchors=("DGS：",))
        edit(wsmap[Y], Y, "C19", "G5a", removals=[("(第7章7-4 手順9)", "")], anchors=("VMware：",))
        edit(wsmap[Y], Y, "C20", "G5a",
             removals=[("(第2章2-1)", ""), ("版数の一次資料確認は未実施。", "")],
             anchors=("Red Hat",))
        edit(wsmap[Y], Y, "C21", "G5a", removals=[("(第2章2-1・相関図)", "")], anchors=("仮想マシン：",))
        edit(wsmap[Y], Y, "C22", "G5a", removals=[("(第5章5-1・付録A-1)", "")], anchors=("データベース：",))
        edit(wsmap[Y], Y, "C23", "G5a", removals=[("(第5章5-1 手順4・6・付録A-1)", "")], anchors=("FULbak",))
        edit(wsmap[Y], Y, "C24", "G5a",
             removals=[("本書の管理対象との対応付けは要確認(付録A-2・第11章 No.25・相関図)", "")],
             anchors=("コントローラーサーバー：",))
        edit(wsmap[Y], Y, "C25", "G5a",
             new_text="Webクライアント：公式構成図に示される構成要素。", anchors=("Webクライアント",))
        edit(wsmap[Y], Y, "C26", "G5a",
             removals=[("第7章7-5(仮実装・未承認)に", "第7章7-5に")], anchors=("サービスコントローラー",))
        edit(wsmap[Y], Y, "C27", "G5a", removals=[("(第7章7-4 手順8)", "")], anchors=("サーバーマネージャー",))
        edit(wsmap[Y], Y, "C28", "G5a", removals=[("(第7章7-4 手順9)", "")], anchors=("Firefox",))
        edit(wsmap[Y], Y, "C29", "G5a",
             new_text="メンテナンスサーバー：相関図に登場するサーバー系。", anchors=("メンテナンスサーバー",))
        edit(wsmap[Y], Y, "C30", "G5a",
             new_text="無線スキャナー(PDA)：ライン毎に前側用/後側用がある携帯端末。", anchors=("無線スキャナー",))
        edit(wsmap[Y], Y, "C31", "G5a", removals=[("(第4章4-4)", "")], anchors=("ナビゲータ：",))

        # --- 異常時の対応 ---
        I = "異常時の対応"
        edit(wsmap[I], I, "C8", "G5a",
             removals=[("アンドン異常→再起動手順(第7章7-4)", "アンドン異常→再起動手順")],
             anchors=("記載する事象",))
        edit(wsmap[I], I, "C10", "G5b", new_text="色定義の表：", anchors=("色定義",))
        edit(wsmap[I], I, "C14", "G5b", new_text="最初の連絡先：", anchors=("最初の連絡先",))
        edit(wsmap[I], I, "C15", "G5b", new_text="連絡がつかない場合：", anchors=("連絡がつかない",))
        edit(wsmap[I], I, "C16", "G5b", new_text="その場で行ってよい対応：", anchors=("行ってよい対応",))
        edit(wsmap[I], I, "C17", "G5b", new_text="行ってはいけない対応：", anchors=("行ってはいけない",))
        edit(wsmap[I], I, "C18", "G5b", new_text="中断して連絡する条件：", anchors=("中断して連絡",))
        edit(wsmap[I], I, "C24", "G5a", new_text="", anchors=("フォームの所在",))
        # G7: 装飾記号(完全引用区間外·C42〜C63は区間内につき触れない)
        edit(wsmap[I], I, "C28", "G7",
             removals=[("発動条件：■生産時", "発動条件：生産時")], anchors=("発動条件：",))
        for r, img in [(131, "1"), (163, "3"), (177, "4"), (191, "5"), (206, "6"), (217, "7")]:
            edit(wsmap[I], I, f"C{r}", "G5a",
                 new_text=f"画像{img}", anchors=(f"画像{img}",))
        edit(wsmap[I], I, "C240", "G5a", new_text="画像8(認証情報は伏字)", anchors=("画像8",))
        edit(wsmap[I], I, "C258", "G5a", new_text="画像9", anchors=("画像9",))
        edit(wsmap[I], I, "C270", "G5a", new_text="画像10", anchors=("画像10",))
        edit(wsmap[I], I, "C280", "G5a", new_text="画像11", anchors=("画像11",))
        edit(wsmap[I], I, "C295", "G5a", new_text="画像12(認証情報は伏字)", anchors=("画像12",))
        edit(wsmap[I], I, "C307", "G5a", new_text="画像13", anchors=("画像13",))
        edit(wsmap[I], I, "C320", "G5a", new_text="画像14", anchors=("画像14",))

        # --- 管理体制 ---
        T = "管理体制"
        edit(wsmap[T], T, "C11", "G5b", new_text="点検の実施者：", anchors=("点検の実施者",))
        edit(wsmap[T], T, "C12", "G5b", new_text="記録の確認者：", anchors=("記録の確認者",))
        edit(wsmap[T], T, "C13", "G5b", new_text="文書の承認者：", anchors=("文書の承認者",))
        edit(wsmap[T], T, "C14", "G5a",
             removals=[("／要確認", "")], anchors=("停止の判断者",))
        edit(wsmap[T], T, "C17", "G5a",
             removals=[("(裏付け記録の照合は未了)", "")], anchors=("本人確認",))

        # --- 相関図 ---
        edit(wsmap["相関図"], "相関図", "A10", "G5a",
             removals=[("出典符に掲げた資料の文書番号・版・保管場所、および図中の IP アドレス・OS 表記の一次資料確認は未実施。", "")],
             anchors=("確定事項と推定事項",))

        # ---------- Phase B2: 要確認事項一覧 ----------
        L = wsmap[LIST_SHEET]
        edit_append(L, LIST_SHEET, "C12", "G5a", "月次再起動の完了条件(判断に用いる画面·動作中とみなす表示)を含む。", anchors=("4：点検の判定基準",))
        edit_append(L, LIST_SHEET, "C19", "G5a", "原 PDF での表記照合·参考例(Eg-Pro·nksv523)の暫定運用の継続期間の照合は未実施。", anchors=("11：バックアップ",))
        edit_append(L, LIST_SHEET, "C26", "G5a", "RPA機では更新の翌日に再起動する決まりがある。Pana-CIM を同じ扱いとするかは未確定。", anchors=("18：Windows更新後",))
        edit_append(L, LIST_SHEET, "C27", "G5a", "チェックシート(§8)には随時再起動の記入欄を設けていない。", anchors=("19：随時再起動",))
        edit_append(L, LIST_SHEET, "C33", "G5a", "Webクライアントの自社での使用状況·NPM·FA の略語の展開も未確認。", anchors=("25：公式資料の構成図",))
        edit_append(L, LIST_SHEET, "C35", "G5a", "裏付け記録の照合は未了。", anchors=("27：人名と割り当て",))

        for i, item in enumerate(NEW_ITEMS):
            r = LIST_LAST_ROW + 1 + i      # 37..45
            L.Rows(LIST_LAST_ROW).Copy()
            L.Rows(r).Insert()             # 直下行へテンプレート行の複製を挿入
            L.Range(f"C{r}").Value = item
            w = float(L.Range(f"C{r}").MergeArea.Width)
            n = calc_lines(item, w, 11.0)
            L.Rows(r).RowHeight = n * 15.0 + 4.1
            REP["list_rows"].append({"row": r, "lines": n, "height": round(n * 15.0 + 4.1, 2)})
            act(f"LIST row {r}: No.{29+i} lines={n} h={n*15.0+4.1:.2f}")
        L.PageSetup.PrintArea = LIST_AREA
        act(f"LIST print area -> {LIST_AREA}")

        assert all(e["sheet"] != "会議課題一覧(一時)" for e in EDITS), "会議課題一覧は不変"
        assert all(e["sheet"] != "相関図_old" for e in EDITS), "相関図_old は不変"
        act(f"edits applied: {len(EDITS)}")
        REP["edits"] = EDITS

        # ---------- 保存(pass1) ----------
        wb.Save()
        act("SAVED (pass1)")

        # ---------- Phase C: 頁実測·採番·冊PDF ----------
        def export_all():
            counts, blanks = {}, {}
            for name in ORDER:
                ws = wsmap[name]
                path = os.path.join(PAGES_DIR, f"{name}.pdf")
                ws.ExportAsFixedFormat(0, path, 0, True, False)
                counts[name] = len(PdfReader(path).pages)
            # 空頁検定(画像シートの画像bboxが様式下端をまたぐ頁)
            for name in IMG_SHEETS:
                doc = pymupdf.open(os.path.join(PAGES_DIR, f"{name}.pdf"))
                bad = []
                for pi in range(doc.page_count):
                    for inf in doc[pi].get_image_info():
                        b = inf["bbox"]
                        if b[3] > 786.0:
                            bad.append({"page": pi + 1, "y1": round(b[3], 1)})
                doc.close()
                if bad:
                    blanks[name] = bad
            return counts, blanks

        counts, blanks = export_all()
        REP["counts"] = counts
        act(f"PAGES: {counts}")
        assert not blanks, f"blank pages: {blanks}"

        page = 1
        for name in ORDER:
            n = counts[name]
            if name != "表紙":
                wsmap[name].PageSetup.FirstPageNumber = page
                REP["numbering"][name] = page
            page += n
        wb.Save()
        act(f"SAVED (pass2: numbering) {REP['numbering']}")

        counts2, blanks2 = export_all()
        assert counts2 == counts, f"pagination shifted: {counts2} vs {counts}"
        assert not blanks2, f"blank pages pass2: {blanks2}"
        act("PASS2 ok")

        writer = PdfWriter()
        for name in ORDER:
            for p in PdfReader(os.path.join(PAGES_DIR, f"{name}.pdf")).pages:
                writer.add_page(p)
        with open(VAULT_PDF, "wb") as f:
            writer.write(f)
        n = len(PdfReader(VAULT_PDF).pages)
        REP["book_pages"] = n
        assert n == sum(counts.values()), f"book {n} != sum {sum(counts.values())}"
        act(f"BOOK -> {VAULT_PDF} ({n}p)")

        # ---------- 引用区間の不変検証 ----------
        q2 = {}
        for cell, sheet in QUOTE_CELLS:
            v = get_val(wsmap[sheet], cell)
            q2[f"{sheet}!{cell}"] = hashlib.sha256(v.encode("utf-8")).hexdigest()
        REP["quote_ok"] = (q2 == REP["quote_before"])
        assert REP["quote_ok"], "quote cells changed!"
        act("QUOTE IMMUTABLE ok")

        wb.Close(SaveChanges=False)
        wb = None
    except Exception:
        if wb is not None:
            try:
                wb.Close(SaveChanges=False)
            except Exception:
                pass
        raise
    finally:
        app.Quit()

    REP["sha_after"] = sha256(XLSX)
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(REP, f, ensure_ascii=False, indent=1, default=str)
    print(f"DONE edits={len(EDITS)} book={REP['book_pages']}p sha={REP['sha_after'][:16]}...", flush=True)


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
