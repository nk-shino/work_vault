# -*- coding: utf-8 -*-
"""G-pass LNB冊: G1/G2/G3/G5/G6/G7 適用 + 認証情報一覧シート新設 + 目次挿入 + 採番 + 冊PDF.
G4(cred)は触らない: cred署名(値/罫線/行高/図形/ページ設定)の前後一致を検証する.
引用原文セル(C13/C16/C20)は1字も変更しない(前後一致を検証).
"""
import os, sys, json, math, shutil, hashlib, unicodedata, traceback
import warnings
warnings.filterwarnings("ignore")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VDIR = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
XLSX = os.path.join(VDIR, "LNB管理手順書案_未承認.xlsx")
VAULT_PDF = os.path.join(VDIR, "LNB管理手順書案_未承認.pdf")
BACKUP = os.path.join(BASE, "backup_20261102", "LNB管理手順書案_未承認_Gpass前_20261104.xlsx")
REPORT = os.path.join(BASE, "scripts", "fix30_gpass_lnb_report.json")
PAGES_DIR = os.path.join(BASE, "tmp_pages30_lnb")
TMPDIR = os.path.join(BASE, "backup_20261102")

PREV_SHEETS = ["表紙", "目次", "用語", "構成と管理情報", "相関図", "相関図_old", "管理体制",
               "日次点検", "定期管理", "バックアップ", "復旧", "異常時の対応",
               "チェックシート(日次)", "チェックシート(月次・異常時)", "会議課題一覧(一時)",
               "要確認事項一覧", "申し送り(認証情報)", "引用と部品照合"]
ORDER19 = ["表紙", "目次", "用語", "構成と管理情報", "相関図", "相関図_old", "管理体制",
           "日次点検", "定期管理", "バックアップ", "復旧", "異常時の対応",
           "チェックシート(日次)", "チェックシート(月次・異常時)", "会議課題一覧(一時)",
           "要確認事項一覧", "申し送り(認証情報)", "認証情報一覧", "引用と部品照合"]
CRED = "申し送り(認証情報)"
NEW = "認証情報一覧"
AUTO_SHEETS = ("表紙", CRED)  # FirstPageNumber を設定しない

REP = {"backup": {}, "edits": [], "appends": [], "new_rows": [], "toc_g3": {},
       "new_sheet": {}, "cred_verify": {}, "quote_verify": {}, "format_notes": [],
       "pages": {}, "numbering": {}, "book": {}}
WB = None
APP = None

def act(msg):
    print("[act] " + msg, flush=True)

def sha16(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()[:16]

def wide_len(s):
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in s)

def calc_lines(text, width_pt):
    cpl = max(10.0, width_pt / 5.5)
    n = 0
    for seg in str(text).split("\n"):
        n += max(1, math.ceil(wide_len(seg) / cpl))
    return n

def edit(ws, sheet, addr, g, value=None, removals=None, anchors=None, append=None):
    old = ws.Range(addr).Text
    if anchors:
        for a in anchors:
            assert a in old, f"anchor miss {sheet}!{addr}: {a!r} not in {old[:80]!r}"
    if append is not None:
        assert value is None and not removals, "append is exclusive"
        new = old + "\n" + append
    elif removals:
        new = old
        for o, r in removals:
            assert o in new, f"removal miss {sheet}!{addr}: {o[:40]!r}"
            new = new.replace(o, r)
    else:
        new = value
    ws.Range(addr).Value = new
    REP["edits"].append({"sheet": sheet, "cell": addr, "g": g, "old": old, "new": new})
    act(f"edit {sheet}!{addr} ({g}) len {len(old)} -> {len(new)}")

def clear(ws, sheet, addr, g, anchor=None):
    old = ws.Range(addr).Text
    if anchor:
        assert anchor in old, f"anchor miss {sheet}!{addr}: {anchor!r} not in {old[:80]!r}"
    ws.Range(addr).Value = ""
    REP["edits"].append({"sheet": sheet, "cell": addr, "g": g, "old": old, "new": ""})
    act(f"clear {sheet}!{addr} ({g})")

def cred_sig(ws):
    sig = {}
    rng = ws.Range("A1:AZ24")
    vals = rng.Value
    sig["values"] = [[("" if v is None else str(v)) for v in row] for row in vals]
    edges = []
    for r in range(1, 25):
        for c in range(1, 53):
            s = ""
            for e in (7, 8, 9, 10):
                s += "1" if ws.Cells(r, c).Borders(e).LineStyle != -4142 else "0"
            edges.append(s)
    sig["borders"] = edges
    sig["heights"] = [ws.Rows(r).RowHeight for r in range(1, 25)]
    shs = []
    for sh in ws.Shapes:
        shs.append([sh.Name, str(sh.TopLeftCell.Address), str(sh.BottomRightCell.Address),
                    round(sh.Width, 1), round(sh.Height, 1), round(sh.Left, 1), round(sh.Top, 1)])
    sig["shapes"] = shs
    ps = ws.PageSetup
    sig["page"] = [str(ps.PrintArea), ps.Orientation, ps.PaperSize, ps.FirstPageNumber,
                   round(ps.LeftMargin, 2), round(ps.RightMargin, 2), round(ps.TopMargin, 2),
                   round(ps.BottomMargin, 2), ps.CenterFooter, str(ps.PrintTitleRows)]
    return sig

def main():
    global WB, APP
    import win32com.client as win32
    from pypdf import PdfReader, PdfWriter
    import pythoncom
    pythoncom.CoInitialize()
    app = win32.DispatchEx("Excel.Application")
    APP = app
    app.Visible = False
    app.DisplayAlerts = False
    try:
        app.AutomationSecurity = 3
    except Exception:
        pass

    # ---------- Phase A: 読み取り検査 + バックアップ ----------
    assert sha16(XLSX), "xlsx missing"
    REP["backup"]["sha_before"] = sha16(XLSX)
    os.makedirs(os.path.dirname(BACKUP), exist_ok=True)
    if os.path.exists(BACKUP):
        assert sha16(BACKUP) == REP["backup"]["sha_before"], "backup sha mismatch (stale backup)"
        act(f"BACKUP ok (reuse): {BACKUP}")
    else:
        shutil.copy2(XLSX, BACKUP)
        assert sha16(BACKUP) == REP["backup"]["sha_before"], "backup sha mismatch"
        act(f"BACKUP -> {BACKUP}")

    wb = app.Workbooks.Open(XLSX, UpdateLinks=0, ReadOnly=True)
    names = [sh.Name for sh in wb.Worksheets]
    assert names == PREV_SHEETS, f"sheet order changed: {names}"
    wsmap = {sh.Name: sh for sh in wb.Worksheets}
    cred_before = cred_sig(wsmap[CRED])
    q = wsmap["引用と部品照合"]
    quote_cells = {}
    for a in ("C13", "C16", "C20"):
        quote_cells[a] = q.Range(a).Text
    assert all(quote_cells.values()), "quote cells empty?"
    REP["quote_verify"]["cells"] = sorted(quote_cells)
    wb.Close(SaveChanges=False)
    wb = None
    act("Phase A ok (order, cred sig, quote captured)")

    # ---------- Phase B: 編集 ----------
    wb = app.Workbooks.Open(XLSX, UpdateLinks=0, ReadOnly=False)
    WB = wb
    try:
        wb.AutoSaveOn = False
    except Exception:
        pass
    wsmap = {sh.Name: sh for sh in wb.Worksheets}
    q = wsmap["引用と部品照合"]  # Phase B の生きたオブジェクトを再取得

    # --- B0 目次 J注記消去(G5a) ---
    T = wsmap["目次"]
    clear(T, "目次", "J10", "G5a", anchor="点検項目は未確定")
    clear(T, "目次", "J15", "G5a", anchor="列名は仮")

    # --- B1 本文編集 ---
    CKD = wsmap["チェックシート(日次)"]
    clear(CKD, "チェックシート(日次)", "C7", "G5a", anchor="点検項目が未確定")
    edit(CKD, "チェックシート(日次)", "C13", "G2",
         value="1：LNB接続状態(無線スキャナーと LNB の接続状態)の表示を確認した：",
         anchors=("1：",))
    CKD.Range("C13").WrapText = False
    REP["format_notes"].append({"sheet": "チェックシート(日次)", "cell": "C13",
                                "change": "WrapText True->False(記入項目名の右オーバーフロー表示。周囲は罫線なし空セル)"})
    edit(CKD, "チェックシート(日次)", "C19", "G5a",
         removals=[("各ラインの欄：判定基準が未確定。確定するまで、", "各ラインの欄：判定基準が確定するまでの間は、")],
         anchors=("各ラインの欄",))
    clear(CKD, "チェックシート(日次)", "A12", "G6", anchor="日")

    CKM = wsmap["チェックシート(月次・異常時)"]
    clear(CKM, "チェックシート(月次・異常時)", "C7", "G5a", anchor="月次の作業があるか")
    clear(CKM, "チェックシート(月次・異常時)", "C8", "G6", anchor="実施日")
    edit(CKM, "チェックシート(月次・異常時)", "C12", "G5a",
         value="＊Pana-CIM と同日に実施する場合は、順序を記録すること。", anchors=("順序を記録",))
    clear(CKM, "チェックシート(月次・異常時)", "A14", "G6", anchor="時刻")
    edit(CKM, "チェックシート(月次・異常時)", "K14", "G6",
         value="連絡先", anchors=("連絡先/時刻",))
    clear(CKM, "チェックシート(月次・異常時)", "C21", "G6", anchor="実施日")

    TK = wsmap["定期管理"]
    edit(TK, "定期管理", "C7", "G5b", value="頻度区分：", anchors=("頻度区分",))
    edit(TK, "定期管理", "C8", "G5a",
         value="月次の有無：Pana-CIM は月次再起動を SMT点検日に実施している。", anchors=("月次の有無",))
    clear(TK, "定期管理", "C9", "G5a", anchor="順序の制約")

    BK = wsmap["バックアップ"]
    for a, v, an in (("C8", "正式な保存先：", "正式な保存先"), ("C9", "取得者：", "取得者"),
                     ("C10", "取得時刻：", "取得時刻"), ("C11", "世代数・保持期間：", "世代数"),
                     ("C12", "一括取得の可否：", "一括取得"), ("C13", "成否の確認者：", "成否の確認者")):
        edit(BK, "バックアップ", a, "G5b", value=v, anchors=(an,))
    edit(BK, "バックアップ", "C15", "G5a+G7",
         value="参考例：バックアップ障害の際に、成否を確認する担当が決まっていない状態が続き、暫定運用が長期化した例がある(Eg-Pro のサブサーバー同期·nksv523)。",
         anchors=("ここが埋まっていない",))
    edit(BK, "バックアップ", "C16", "G5a",
         removals=[("DB データ·LNB 設定·実績帳票を対象に含めるかは未確認。", ""),
                   ("取得目的は特定できていない(慣習として続いている)。", "")],
         anchors=("DGS を介した手作業",))
    edit(BK, "バックアップ", "C18", "G5c",
         removals=[("(出典：DGS_P2ジョブ作成シート。LNB のバックアップ手順との対応は未確認)", "(出典：DGS_P2ジョブ作成シート)")],
         anchors=("参考添付：",))
    for a, r_, an in (("C26", "r007", "参考添付1"), ("C39", "r016", "参考添付2"), ("C55", "r034", "参考添付3")):
        edit(BK, "バックアップ", a, "G5c",
             removals=[(f"(出典：DGS_P2ジョブ作成シート {r_}。対応：未確認)", f"(出典：DGS_P2ジョブ作成シート {r_})")],
             anchors=(an,))

    FK = wsmap["復旧"]
    for a, v in (("C8", "実施条件："), ("C9", "手順："), ("C10", "確認の頻度："), ("C11", "記録様式：")):
        edit(FK, "復旧", a, "G5b", value=v, anchors=(v[:-1],))
    edit(FK, "復旧", "C13", "G5a",
         removals=[("本手順に基づく復旧試験の実施記録は2026-10-14時点で未確認。", "")],
         anchors=("戻す試験で確認する",))

    NK = wsmap["日次点検"]
    clear(NK, "日次点検", "C7", "G5a", anchor="点検項目が未確定")
    edit(NK, "日次点検", "C27", "G5b", value="完了条件：", anchors=("完了条件",))
    edit(NK, "日次点検", "C29", "G5a",
         removals=[("自社の L1〜L3 に同じ表示があるかは未確認", "")], anchors=("注意点：出典は",))
    edit(NK, "日次点検", "C33", "G5a",
         removals=[("項目数も未確定。", "")], anchors=("方針：",))

    KS = wsmap["構成と管理情報"]
    edit(KS, "構成と管理情報", "C8", "G1+G5a",
         value="システム名：LNB(社内呼称)。製品資料上の名称は iLNB(統合ライン管理システム)であり、本書では同一のものとして扱う。",
         anchors=("システム名",))
    edit(KS, "構成と管理情報", "C9", "G1+G5a",
         value="ソフトウェア：LNB ソフト(製品資料上の名称は iLNB)。", anchors=("ソフトウェア",))
    edit(KS, "構成と管理情報", "C11", "G5b",
         removals=[("サーバ(名称・台数)：要確認。", "サーバ(名称・台数)：")], anchors=("サーバ(名称・台数)",))
    edit(KS, "構成と管理情報", "C12", "G5b",
         removals=[("端末(名称・設置場所)：要確認。", "端末(名称・設置場所)：")], anchors=("端末(名称・設置場所)",))
    edit(KS, "構成と管理情報", "C14", "G5a",
         removals=[("Pana-CIM のデータを参照する関係が相関図草案にあり、参照の方向を含めて未確認(§12 No.6 参照)。", ""),
                   ("実際の接続先とデータの向きは未確認", "")],
         anchors=("他システムとの連携",))
    edit(KS, "構成と管理情報", "C17", "G5a",
         removals=[("IP アドレスの一次資料(実機·構成資料)での確認は未実施。", "")],
         anchors=("保管庫内の資料から",))
    edit(KS, "構成と管理情報", "C23", "G5a",
         removals=[("L4以降が存在するかは要確認。", "")], anchors=("第4オクテット",))
    edit(KS, "構成と管理情報", "C25", "G5a",
         removals=[("。§13 参照", "。")], anchors=("通信：HTTP",))
    edit(KS, "構成と管理情報", "C27", "G5b", value="必要な権限：", anchors=("必要な権限",))
    edit(KS, "構成と管理情報", "C28", "G5a+G5b",
         value="認証情報の保管場所：現状はデスクトップのショートカットに埋め込まれている。",
         anchors=("認証情報の保管場所",))
    edit(KS, "構成と管理情報", "C29", "G5b", value="実施場所：", anchors=("実施場所",))
    edit(KS, "構成と管理情報", "C30", "G5b", value="実施端末の OS・ブラウザ：", anchors=("実施端末の OS",))
    edit(KS, "構成と管理情報", "C55", "G5a",
         removals=[("要確認34の実物。", ""),
                   ("画面内の細部の判読には限界があり、必要な部分の再取得(実機)は未了。", "画面内の細部の判読には限界がある。")],
         anchors=("図1",))
    edit(KS, "構成と管理情報", "C80", "G5a",
         removals=[("要確認36：", "")], anchors=("図2",))
    edit(KS, "構成と管理情報", "C101", "G5a",
         removals=[("要確認30の実物：", "")], anchors=("図3",))
    edit(KS, "構成と管理情報", "C104", "G5a",
         removals=[("図の配置と表示の承認は未了で、接続関係の実機での確認は未実施(§12 No.6 参照)。", "")],
         anchors=("参照：「相関図」シート",))

    YG = wsmap["用語"]
    edit(YG, "用語", "C8", "G5a",
         removals=[("対象とする。iLNB と同一であるとは断定しない", "対象とする。")],
         anchors=("LNB：Line Network Box",))
    edit(YG, "用語", "C9", "G1+G5a",
         value="iLNB：統合ライン管理システム。メーカー公開資料での製品名。本書では LNB と同一のものとして扱う。",
         anchors=("iLNB：",))
    edit(YG, "用語", "C10", "G5a",
         removals=[("。正式な呼称は要確認", "。")], anchors=("LWS：",))
    edit(YG, "用語", "C11", "G5b", removals=[("(§2-2)", "")], anchors=("L1 / L2 / L3",))
    edit(YG, "用語", "C12", "G1+G5a", value="E-Link：LNB が製品仕様として備える情報入出力の機構。", anchors=("E-Link",))
    edit(YG, "用語", "C13", "G1+G5a", value="GEM通信：設備と上位システムの間の標準的な通信規約。LNB が対応を表明している。", anchors=("GEM通信",))
    edit(YG, "用語", "C15", "G5a", removals=[("。本書での位置づけは要確認", "。")], anchors=("DGS：",))
    edit(YG, "用語", "C17", "G5a",
         removals=[("になりうる。ただし LNB の管理対象に含めるかは要確認", "になりうる。")], anchors=("CIMC-SV",))
    edit(YG, "用語", "C18", "G5b", removals=[("(§2-2・§13)", "")], anchors=("HTTP：",))
    edit(YG, "用語", "C19", "G5b", removals=[("(§2-2)", "")], anchors=("ポート：",))
    edit(YG, "用語", "C20", "G5b", removals=[("(§2-2)", "")], anchors=("IPアドレス：",))
    edit(YG, "用語", "C21", "G5b", removals=[("(§2-2)", "")], anchors=("オクテット：",))
    edit(YG, "用語", "C22", "G5b", removals=[("(§12 No.36)", "")], anchors=("Ping：",))
    edit(YG, "用語", "C23", "G5b", removals=[("(§2-2)", "")], anchors=("URL：",))
    edit(YG, "用語", "C24", "G5b", removals=[("(§4 Step1・付録A-1・付録A-2・§14)", "")], anchors=("無線スキャナー",))
    edit(YG, "用語", "C25", "G5a+G5b",
         removals=[("必要(付録A-2・§14)。自社での有効化状況は未確認(§12 No.28)", "必要。")], anchors=("部品照合",))
    edit(YG, "用語", "C26", "G5a",
         removals=[("PC。社内で LNB と呼ぶ対象と同じかは未確認(付録A-3・§12 No.29)", "PC。")], anchors=("FAパソコン",))
    edit(YG, "用語", "C28", "G5b", removals=[("(§6・参考添付1〜3)", "")], anchors=("ジョブ：",))
    edit(YG, "用語", "C29", "G5a",
         removals=[("ボタンがある。LNB-PCリブートを PC自体の再起動とする対応付けは要確認(§12 No.30・37)", "ボタンがある。")],
         anchors=("LNB-PC：",))
    edit(YG, "用語", "C30", "G5b", removals=[("(§12 No.32)", "")], anchors=("稼働率データ",))
    edit(YG, "用語", "C31", "G5a",
         removals=[("L1NPM-1〜7・SP70-1 と現れる。L2/L3 の同画面は未確認(§12 No.34)。表記は画面上の設備識別名であり、実機の型式との対応は未確認。",
                    "L1NPM-1〜7・SP70-1 と現れる。表記は画面上の設備識別名。")], anchors=("NPM：",))
    edit(YG, "用語", "C32", "G5a",
         removals=[("開くソフト。点検に使う OS・ブラウザは要確認(§2-2・相関図)", "開くソフト。")], anchors=("ブラウザ",))

    IJ = wsmap["異常時の対応"]
    clear(IJ, "異常時の対応", "C7", "G5a", anchor="アンドンの色定義")
    for a, v in (("C11", "異常を検知したときの最初の連絡先："), ("C12", "連絡がつかない場合の次の連絡先："),
                 ("C13", "実施者がその場で行ってよい対応："), ("C14", "実施者が行ってはいけない対応："),
                 ("C15", "点検を中断して連絡する条件："), ("C16", "点検中にサービスが停止した場合の応急処置："),
                 ("C17", "上記の参照先文書：")):
        edit(IJ, "異常時の対応", a, "G5b", value=v, anchors=(v[:-1],))
    clear(IJ, "異常時の対応", "C19", "G5a", anchor="結論に至っていない")
    for a, v in (("C23", "連絡先："), ("C24", "依頼方法(電話・メール・システム)："),
                 ("C25", "保守契約の有無と対応時間帯："), ("C26", "自社で対応する範囲："),
                 ("C27", "ベンダーへ依頼する範囲：")):
        edit(IJ, "異常時の対応", a, "G5b", value=v, anchors=(v[:-1],))

    KT = wsmap["管理体制"]
    for a, v in (("C10", "点検の実施者："), ("C11", "記録の確認者："), ("C12", "文書の承認者：")):
        edit(KT, "管理体制", a, "G5b", value=v, anchors=(v[:-1],))
    edit(KT, "管理体制", "C13", "G5a",
         removals=[("／要確認", "")], anchors=("権限者",))
    edit(KT, "管理体制", "C16", "G5a",
         removals=[("(裏付け記録の照合は未了)", "")], anchors=("人名と割り当て",))
    edit(KT, "管理体制", "C18", "G5a",
         removals=[("稼働中に実施できない項目の有無は要確認。", "")], anchors=("環境：",))

    IY = wsmap["引用と部品照合"]
    clear(IY, "引用と部品照合", "C8", "G5a", anchor="未確認：自社の L1〜L3")
    edit(IY, "引用と部品照合", "C11", "G5a",
         removals=[("引用原文と出典資料の該当頁·版の照合は未確認。", "")], anchors=("改変せずに載せる",))
    edit(IY, "引用と部品照合", "C21", "G5a",
         removals=[("社内で LNB と呼んでいる対象がこれと同じかは未確認。", "")], anchors=("限界：",))
    edit(IY, "引用と部品照合", "A6", "G3",
         value="15. 部品照合に関する参照", anchors=("14. 部品照合",))

    # --- B2 要確認事項一覧: 追記 + 新項目挿入 ---
    L = wsmap["要確認事項一覧"]
    APPENDS = [
        ("C9", "1：LNB と iLNB", "用語集·§2 の同一性注記は削除し、本書では LNB と同一のものとして扱う方針とした(2026-11-04)。"),
        ("C14", "6：実際の連携先", "参照の方向を含めて未確認(相関図草案上の記載)。接続関係の実機での確認も未実施。"),
        ("C19", "11：", "所要時間の目安と、LNB に月次の定期作業があるかも未確認(§5·§10-1)。"),
        ("C21", "13：点検項目", "§9 の日次チェックシートに公式資料由来の1項目を記入(2026-11-04)。列名が仮である旨の注記は削除。"),
        ("C26", "18：異常時", "会議で確認事項として挙げたまま結論に至っていない(2026-11-04 記録)。"),
        ("C27", "19：", "対象への包含(DB データ·LNB 設定·実績帳票)·取得目的·参考例(Eg-Pro·nksv523)の暫定運用の継続期間の照合も未確認。"),
        ("C35", "27：", "参照の方向·順序を誤った場合の影響も未確認。"),
        ("C42", "34：L1", "細部の再取得(実機)と表記·実機型式の対応も未了。"),
        ("C47", "39：人名", "裏付け記録の照合は未了。"),
    ]
    for addr, anchor, add in APPENDS:
        edit(L, "要確認事項一覧", addr, "G5a(一覧追記)", append=add, anchors=(anchor,))
        r = L.Range(addr).Row
        need = calc_lines(L.Range(addr).Text, L.Range(addr).MergeArea.Width)
        h = L.Rows(r).RowHeight
        if need * 15 + 4.1 > h + 0.01:
            L.Rows(r).RowHeight = round(need * 15 + 4.1, 2)
            act(f"list height {addr}: {h} -> {round(need*15+4.1,2)}")
    # No.20 は書換(頻度·実施記録を組込)
    edit(L, "要確認事項一覧", "C28", "G5a(一覧書換)",
         removals=[("／現行実施者", "／実施条件·頻度を含む。復旧試験の実施記録は未確認(2026-10-14時点)／現行実施者")],
         anchors=("20：復旧",))

    NEW_ITEMS = [
        "40：IP·OS·表記の一次資料確認／§2 の IP アドレス(172.25.253.10/11/21/31/45 等)·通信(HTTP·ポート8080)·ゲストOS 表記の一次資料(実機·構成資料)での確認。本文の自動走査の試行はセキュリティガードの拒否により未実施(2026-11-04)／現行実施者、ベンダー",
        "41：引用原文と出典資料の該当頁·版の照合／付録A(A-1〜A-3)の引用原文と出典 PDF の該当頁·版の突合／作成チーム",
        "42：参考添付(DGS_P2ジョブ作成シート)と LNB バックアップ手順の対応／§6 の参考添付1〜3·ジョブ設定画面が LNB のバックアップ手順のどこに対応するか／現行実施者",
        "43：LWS の正式な呼称／接続先 URL の経路名 /lws/·画面タイトル「Line Network Box」から推定。アプリケーションの正式名称の確定／現行実施者、ベンダー",
        "44：LNB 側のアンドン色定義／アンドンの色定義が LNB 側にあるか、Pana-CIM 側の定義を共用するか／管理責任者、現行実施者",
    ]
    LIST_LAST = 47
    for i, text in enumerate(NEW_ITEMS):
        r = LIST_LAST + 1 + i
        L.Rows(LIST_LAST).Copy()
        L.Rows(r).Insert()
        old = L.Range(f"C{r}").Text
        L.Range(f"C{r}").Value = text
        need = calc_lines(text, L.Range(f"C{r}").MergeArea.Width)
        L.Rows(r).RowHeight = round(need * 15 + 4.1, 2)
        REP["new_rows"].append({"row": r, "old_template_text": old, "text": text,
                                "height": L.Rows(r).RowHeight})
        act(f"LIST row {r}: No.{40+i} h={L.Rows(r).RowHeight}")
    L.PageSetup.PrintArea = "$A$1:$AZ$52"
    act("LIST print area -> $A$1:$AZ$52")

    # --- B3 チェックシート(日次): 年月行削除 ---
    assert "年月" in CKD.Range("C9").Text, "C9 not 年月 row?"
    CKD.Rows(9).Delete()
    CKD.PageSetup.PrintArea = "$A$1:$AZ$20"
    act("CKD row9 deleted, print area -> $A$1:$AZ$20")

    # --- B4 G3: 認証情報一覧シート新設 ---
    assert NEW not in [sh.Name for sh in wb.Worksheets]
    nw = wb.Worksheets.Add(After=wsmap[CRED])
    nw.Name = NEW
    for ci in range(1, 53):
        col = chr(64 + ci) if ci <= 26 else "A" + chr(64 + ci - 26)
        w = q.Columns(col).ColumnWidth
        if w:
            nw.Columns(col).ColumnWidth = w
    for r in range(1, 8):
        h = q.Rows(r).RowHeight
        if h:
            nw.Rows(r).RowHeight = h
    q.Range("A1:AZ4").Copy(Destination=nw.Range("A1"))
    nw.Range("G4").Value = "　認証情報一覧"
    q.Range("A6:AZ6").Copy(Destination=nw.Range("A6:AZ6"))
    nw.Range("A6").Value = "14. 認証情報一覧"
    q.Range("C7:AZ7").Copy(Destination=nw.Range("C7:AZ7"))
    nw.Range("C7").Value = "＊値は本書に記入しない。認証情報は別紙で管理し、記入は利用者が行う。"
    L.Range("A8").Copy()
    for a in ("A8", "C8", "E8", "G8", "I8", "K8"):
        nw.Range(a).PasteSpecial(Paste=-4122)  # xlPasteFormats
    for a, v in (("A8", "No"), ("C8", "設備"), ("E8", "項目"), ("G8", "アカウント"),
                 ("I8", "備考"), ("K8", "更新日")):
        nw.Range(a).Value = v
    nw.Rows(8).RowHeight = 19.05
    app.CutCopyMode = False
    for r in range(9, 19):
        for c1, c2 in (("A", "B"), ("C", "D"), ("E", "F"), ("G", "H"), ("I", "J")):
            nw.Range(f"{c1}{r}:{c2}{r}").Merge()
        nw.Rows(r).RowHeight = 19.05
    grid = nw.Range("A8:K18")
    grid.Borders.LineStyle = 1
    grid.Borders.Weight = 2
    ps = nw.PageSetup
    ps.Orientation = 1
    ps.PaperSize = 9
    ps.LeftMargin = app.InchesToPoints(0.87)
    ps.RightMargin = app.InchesToPoints(0.51)
    ps.TopMargin = app.InchesToPoints(0.59)
    ps.BottomMargin = app.InchesToPoints(0.79)
    ps.HeaderMargin = app.InchesToPoints(0.59)
    ps.FooterMargin = app.InchesToPoints(0.39)
    ps.CenterFooter = "様式 NR4030-0300-A3"
    ps.PrintTitleRows = "$1:$3"
    ps.PrintArea = "$A$1:$AZ$19"
    REP["new_sheet"] = {"name": NEW, "position": "after " + CRED, "print_area": "$A$1:$AZ$19",
                        "rows": {"band": 6, "note": 7, "header": 8, "entries": "9-18"},
                        "header": ["No", "設備", "項目", "アカウント", "備考", "更新日"]}
    act("NEW SHEET 認証情報一覧 built")

    # --- B5 目次 G3 行挿入 ---
    T.Rows(20).Insert(CopyOrigin=1)  # xlFormatFromRightOrBelow(下行=旧引用行から書式)
    if abs(T.Rows(20).RowHeight - 12.75) > 0.01:
        T.Rows(20).RowHeight = 12.75
    tJ = T.Range("J20:AZ20").Interior.ColorIndex
    if tJ != -4142:
        T.Range("J20:AZ20").Interior.ColorIndex = -4142
        REP["format_notes"].append({"sheet": "目次", "cell": "J20:AZ20", "change": "塗りを解除(挿入行の書式調整)"})
    assert T.Range("A21").Text == "14．", f"unexpected A21: {T.Range('A21').Text!r}"
    T.Range("A20").Value = "14．"
    T.Range("B20").Value = "認証情報一覧"
    T.Range("C20").Value = "14．"
    T.Range("A21").Value = "15．"
    T.Range("C21").Value = "15．"
    assert T.Range("C22").Text == "15．", f"unexpected C22: {T.Range('C22').Text!r}"
    T.Range("C22").Value = ""
    REP["toc_g3"] = {"insert_row": 20, "new": "14．認証情報一覧", "renumber": "引用と部品照合 14→15",
                     "orphan_cleared": "旧C21(15．)"}
    act("TOC row20 inserted, 引用 renumbered 15")

    # --- B6 検査 ---
    names2 = [sh.Name for sh in wb.Worksheets]
    assert names2 == ORDER19, f"final order mismatch: {names2}"
    assert len(names2) == 19
    wsmap = {sh.Name: sh for sh in wb.Worksheets}  # 新シートを含め再取得
    act("ORDER19 ok")

    # --- B7 cred/quote 不変検証 ---
    cred_after = cred_sig(wsmap[CRED])
    REP["cred_verify"]["ok"] = cred_after == cred_before
    if cred_after != cred_before:
        for k in cred_before:
            if cred_before[k] != cred_after[k]:
                act(f"CRED DIFF in {k}")
        raise AssertionError("cred sheet changed — G4 invariant violated")
    act("CRED INVARIANT ok (values/borders/heights/shapes/page)")
    for a in ("C13", "C16", "C20"):
        now = wsmap["引用と部品照合"].Range(a).Text
        assert now == quote_cells[a], f"quote cell {a} changed!"
    REP["quote_verify"]["ok"] = True
    act("QUOTE IMMUTABLE ok (C13/C16/C20)")

    wb.Save()
    act("SAVED (pass1)")

    # --- 採番 ---
    os.makedirs(PAGES_DIR, exist_ok=True)
    for f in os.listdir(PAGES_DIR):
        os.remove(os.path.join(PAGES_DIR, f))
    pages = {}
    for name in ORDER19:
        p = os.path.join(PAGES_DIR, f"{name}.pdf")
        wsmap[name].ExportAsFixedFormat(0, p, 0, True, False)
        pages[name] = len(PdfReader(p).pages)
        assert pages[name] >= 1, f"{name} 0 pages"
    REP["pages"] = pages
    act(f"PAGES: {pages}")

    acc = 1
    numbering = {}
    for name in ORDER19:
        if name in AUTO_SHEETS:
            acc += pages[name]
            continue
        wsmap[name].PageSetup.FirstPageNumber = acc
        numbering[name] = acc
        acc += pages[name]
    REP["numbering"] = numbering
    exp_new = 1 + pages["表紙"] + sum(pages[n] for n in ORDER19[1:16]) + pages[CRED]
    exp_q = exp_new + pages[NEW]
    assert numbering[NEW] == exp_new, f"{NEW} FPN {numbering[NEW]} != {exp_new}"
    assert numbering["引用と部品照合"] == exp_q, f"引用 FPN {numbering['引用と部品照合']} != {exp_q}"
    wb.Save()
    act(f"SAVED (pass2: numbering) {numbering}")

    for name in ORDER19:
        if name == CRED:
            continue
        p = os.path.join(PAGES_DIR, f"{name}.pdf")
        wsmap[name].ExportAsFixedFormat(0, p, 0, True, False)
        n = len(PdfReader(p).pages)
        assert n == pages[name], f"{name} pages changed {pages[name]} -> {n}"
    act("PASS2 ok (page counts stable)")

    # cred 不変の最終確認(保存後)
    cred_final = cred_sig(wsmap[CRED])
    assert cred_final == cred_before, "cred changed after save"

    # --- 冊PDF ---
    wb.ExportAsFixedFormat(0, VAULT_PDF, 0, True, False)
    bookrd = PdfReader(VAULT_PDF)
    book_pages = len(bookrd.pages)
    total = sum(pages.values())
    assert book_pages == total, f"book {book_pages} != {total}"
    offset = sum(pages[n] for n in ORDER19[:16])
    writer = PdfWriter()
    for name in ORDER19:
        if name == CRED:
            for i in range(offset, offset + pages[CRED]):
                writer.add_page(bookrd.pages[i])
        else:
            p = os.path.join(PAGES_DIR, f"{name}.pdf")
            for pg in PdfReader(p).pages:
                writer.add_page(pg)
    with open(VAULT_PDF, "wb") as f:
        writer.write(f)
    final_pages = len(PdfReader(VAULT_PDF).pages)
    assert final_pages == total, f"merged {final_pages} != {total}"
    REP["book"] = {"pages": final_pages, "path": VAULT_PDF,
                   "cred_spot": f"book pages {offset+1}-{offset+pages[CRED]}"}
    act(f"BOOK -> {VAULT_PDF} ({final_pages}p)")
    wb.Close(SaveChanges=False)
    WB = None
    app.Quit()
    APP = None
    REP["backup"]["sha_after"] = sha16(XLSX)
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(REP, f, ensure_ascii=False, indent=1)
    print(f"DONE edits={len(REP['edits'])} book={final_pages}p sha={REP['backup']['sha_after']} "
          f"g_counts={ {g: sum(1 for e in REP['edits'] if e['g'].startswith(g)) for g in ('G1','G2','G3','G5','G6','G7')} }", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        try:
            if WB is not None:
                WB.Close(SaveChanges=False)
            if APP is not None:
                APP.Quit()
        except Exception:
            pass
        sys.exit(1)
