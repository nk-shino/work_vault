# -*- coding: utf-8 -*-
"""LNB管理手順書案_未承認.xlsx 改修実装 (Excel COM / openpyxl保存禁止)
計画: 改修計画_管理手順書全文改修_20261102.md / 変更リスト_LNB冊_20261102.md
Pana冊(impl_pana.py)準拠。相違点:
- 余白はポイント直指定(COMのPageSetup余白はポイント単位。Pana冊の÷72は誤り)
- 申し送り(認証情報)シートは完全スキップ(値参照·個別出力·書式変更すべて禁止)
- 冊PDFは17シート個別出力+冊出力の認証情報頁をスポット結合
"""
import os, io, sys, json, math, hashlib, traceback

WORK = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
XLSX = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\LNB管理手順書案_未承認.xlsx"
VAULT_PDF_DIR = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
PAGES_DIR = os.path.join(WORK, "scripts", "tmp_pages_lnb")
REPORT = os.path.join(WORK, "scripts", "impl_lnb_report.json")
EXPECT_SHA = "67b8cc54df23db2b41b8d27fb85246d4b77528f12b62eca489a740e8dba1ce03"
CRED = "申し送り(認証情報)"

FONT = "Meiryo UI"
INK = 7949855        # RGB(31,78,121) 藍
CHAP_FILL = 16184006 # RGB(198,242,246)
SEC_FILL = 16184046  # RGB(238,242,246)
AKA = 3029680        # 朱 RGB(176,58,46) 前例実測(Pana冊と同一)
XL_LEFT, XL_CENTER, XL_TOP = -4131, -4108, -4160
XL_CONT, XL_THICK, XL_THIN, XL_NONE = 1, 4, 2, -4142
XL_EDGE_LEFT = 7
XL_MOVE = 2
PAGE_CAP = 841.9 - 42.52 - 56.69  # 742.7pt
# 余白: ポイント直指定(62.36/36.85/42.52/56.69/42.52/28.35)
ML, MR, MT, MB, MH, MF = 62.36, 36.85, 42.52, 56.69, 42.52, 28.35
FOOT = ('&"ＭＳ ゴシック,標準"　　NR4030', '&"ＭＳ ゴシック,標準"様式 NR4030-0300-A3', '&"ＭＳ ゴシック,標準"日本光電')

ORDER17 = ["表紙", "目次", "用語", "構成と管理情報", "相関図", "相関図_old", "管理体制",
           "日次点検", "定期管理", "バックアップ", "復旧", "異常時の対応",
           "チェックシート(日次)", "チェックシート(月次・異常時)", "会議課題一覧(一時)",
           "要確認事項一覧", "引用と部品照合"]

REP = {"actions": [], "errors": [], "texts": [], "breaks": {}, "deletes": {},
       "shapes_del": [], "pics": {}, "pa": {}, "orange": [], "kaigi_extras": [],
       "counts": {}, "numbering": {}, "cred_pages": None, "book_pages": None,
       "pdf": None, "ghosts": {}, "blanks": {}}

def act(msg): REP["actions"].append(msg); print("[act]", msg, flush=True)

def blankish(c):
    return c is None or str(c).strip().replace("\u3000", "") == ""

def px(w):
    return int(((256.0 * w + 18.0) / 256.0) * 7) + 5

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

COLS = [chr(65 + i) for i in range(26)] + ["A" + chr(65 + i) for i in range(26)] + \
       ["B" + chr(65 + i) for i in range(26)]  # A..BZ

def col_range_width_pt(ws, c1, c2):
    i1, i2 = COLS.index(c1), COLS.index(c2)
    return sum(px(ws.Columns[COLS[i]].ColumnWidth) for i in range(i1, i2 + 1)) * 0.75

def units(s):
    return sum(1.0 if ord(ch) > 0x2E80 else 0.5 for ch in s)

def calc_lines(text, width_pt, size):
    per = max(4.0, width_pt / size)
    n = 0
    for seg in str(text).split("\n"):
        n += max(1, math.ceil(units(seg) / per - 1e-9))
    return n

def set_widths(ws, spec):
    for key, w in spec.items():
        k = key if ":" in key else f"{key}:{key}"
        ws.Range(k).ColumnWidth = w

def font_of(rng, size, bold=False, color=None):
    rng.Font.Name = FONT
    rng.Font.Size = size
    rng.Font.Bold = bold
    if color is not None:
        rng.Font.Color = color

def addr_str(obj):
    return str(obj.Address).replace("$", "")

def ensure_merge(ws, want, tl_addr):
    tl = ws.Range(tl_addr)
    if tl.MergeCells:
        area = addr_str(tl.MergeArea)
        if area != want:
            tl.MergeArea.UnMerge()
            ws.Range(want).Merge()
    else:
        ws.Range(want).Merge()

def body_style(ws, r, c1="C", c2="AZ", size=11.0):
    want = f"{c1}{r}:{c2}{r}"
    ensure_merge(ws, want, f"{c1}{r}")
    rng = ws.Range(f"{c1}{r}:{c2}{r}")
    font_of(rng, size)
    rng.WrapText = True
    rng.HorizontalAlignment = XL_LEFT
    rng.VerticalAlignment = XL_TOP

def band_style(ws, r, fill):
    ensure_merge(ws, f"A{r}:AZ{r}", f"A{r}")
    rng = ws.Range(f"A{r}:AZ{r}")
    font_of(rng, 12.0, bold=True, color=INK)
    rng.WrapText = True
    rng.HorizontalAlignment = XL_LEFT
    rng.VerticalAlignment = XL_CENTER
    rng.Interior.Color = fill
    b = ws.Range(f"A{r}").Borders(XL_EDGE_LEFT)
    b.LineStyle = XL_CONT
    b.Weight = XL_THICK
    b.Color = INK
    v = str(ws.Range(f"A{r}").Value or "")
    w = col_range_width_pt(ws, "A", "AZ")
    ws.Rows[r].RowHeight = calc_lines(v, w, 12.0) * 16.2 + 4.1

def label_cell(ws, addr, wrap=False, center=True):
    c = ws.Range(addr)
    font_of(c, 11.0, bold=True)
    c.WrapText = wrap
    c.HorizontalAlignment = XL_CENTER if center else XL_LEFT
    c.VerticalAlignment = XL_CENTER
    c.Interior.Color = SEC_FILL

def row_h_body(ws, r, c1, c2, size=11.0, pitch=15.0):
    v = ws.Range(f"{c1}{r}").Value
    if v is None or str(v) == "":
        return None
    w = col_range_width_pt(ws, c1, c2)
    n = calc_lines(v, w, size)
    ws.Rows[r].RowHeight = n * pitch + 4.1
    return n

def aka_line(ws, r):
    b = ws.Range(f"A{r}").Borders(XL_EDGE_LEFT)
    b.LineStyle = XL_CONT
    b.Weight = XL_THIN
    b.Color = AKA

def get_val(ws, addr):
    v = ws.Range(addr).Value
    return "" if v is None else str(v)

def text_edit(ws, addr, kind, spec, label):
    old = get_val(ws, addr)
    if kind == "replace_all":
        if old == spec:
            REP["texts"].append({"cell": addr, "sheet": label, "status": "OK(already)"})
            return
        new = spec
    elif kind == "repl":
        if all(a not in old for a, b in spec) and all(b in old for a, b in spec):
            REP["texts"].append({"cell": addr, "sheet": label, "status": "OK(already)"})
            return
        new = old
        for a, b in spec:
            if a not in new:
                REP["errors"].append(f"{label}.{addr}: 期待文字列なし: {a[:40]}")
                raise SystemExit(f"TEXT FAIL {label}.{addr}: {a[:40]}")
            new = new.replace(a, b, 1)
    elif kind == "append":
        if spec[1] in old:
            REP["texts"].append({"cell": addr, "sheet": label, "status": "OK(already)"})
            return
        if spec[0] and not old.endswith(spec[0]):
            REP["errors"].append(f"{label}.{addr}: 末尾不一致: {old[-40:]}")
            raise SystemExit(f"TEXT FAIL {label}.{addr} endswith")
        new = old + spec[1]
    elif kind == "clear":
        if old.strip() == "":
            REP["texts"].append({"cell": addr, "sheet": label, "status": "OK(already)"})
            return
        new = ""
    else:
        raise ValueError(kind)
    if kind == "clear":
        try:
            ws.Range(addr).ClearContents()
        except Exception:
            ws.Range(addr).MergeArea.ClearContents()
    else:
        ws.Range(addr).Value = new
    REP["texts"].append({"cell": addr, "sheet": label, "status": "OK", "old": old[:160], "new": str(new)[:160]})
    act(f"TEXT {label}.{addr}")

def placement_all(ws):
    n = 0
    for sh in ws.Shapes:
        sh.Placement = XL_MOVE
        n += 1
    return n

def all_breaks(ws):
    out = []
    try:
        cnt = ws.HPageBreaks.Count
    except Exception:
        return out
    for i in range(1, cnt + 1):
        pb = ws.HPageBreaks.Item(i)
        try:
            t = int(pb.Type)
        except Exception:
            t = -1
        try:
            r = int(pb.Location.Row)
        except Exception:
            continue
        out.append((r, t))
    return sorted(out)

def delete_manual_breaks(ws, tag):
    removed = []
    for r, t in all_breaks(ws):
        if t == -4135:
            for i in range(1, ws.HPageBreaks.Count + 1):
                pb = ws.HPageBreaks.Item(i)
                if int(pb.Location.Row) == r:
                    try:
                        pb.Delete()
                        removed.append(r)
                    except Exception:
                        pass
                    break
    REP["breaks"][f"removed:{tag}"] = removed
    if removed:
        act(f"BREAKS removed {tag}: {removed}")
    return removed

def try_delete(ws, r1, r2, tag, colend="AZ"):
    rng = ws.Range(f"A{r1}:{colend}{r2}")
    ok = True
    why = []
    v = rng.Value
    if v is not None:
        if isinstance(v, tuple):
            for row in v:
                if isinstance(row, tuple):
                    if any(not blankish(c) for c in row):
                        ok = False; why.append("value"); break
                elif not blankish(v):
                    ok = False; why.append("value"); break
        elif not blankish(v):
            ok = False; why.append("value")
    mc = rng.MergeCells
    if mc:  # True or Null(混合)
        ok = False; why.append(f"merge={mc}")
    try:
        bl = all(rng.Borders(k).LineStyle == XL_NONE for k in (7, 8, 9, 10, 11, 12))
    except Exception as e:
        bl = False; why.append(f"border-read:{e}")
    if not bl:
        ok = False; why.append("border")
    for sh in ws.Shapes:
        try:
            if int(sh.BottomRightCell.Row) >= r1:
                ok = False; why.append("shape"); break
        except Exception:
            pass
    if ok:
        ws.Rows[f"{r1}:{r2}"].Delete()
        act(f"DELETE {tag} {r1}-{r2}")
    else:
        REP["errors"].append(f"DELETE SKIP {tag}: {why}")
    REP["deletes"][tag] = {"range": f"{r1}-{colend}{r2}", "ok": ok, "why": why}
    return ok

def extras_in_row(ws, r):
    """C:AZ の C 列以外の値を返す(結合保護ガード)"""
    vv = ws.Range(f"C{r}:AZ{r}").Value
    row = vv[0] if isinstance(vv, tuple) and vv and isinstance(vv[0], tuple) else vv
    if not isinstance(row, tuple):
        row = (row,)
    return [(COLS[2 + j], v) for j, v in enumerate(row) if j > 0 and not blankish(v)]

def main():
    os.makedirs(PAGES_DIR, exist_ok=True)
    s = sha256(XLSX)
    if s != EXPECT_SHA:
        raise SystemExit(f"SHA mismatch: {s}")
    act("SHA OK")

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
        assert len(wsmap) == 18, f"sheet count {len(wsmap)}"
        assert CRED in wsmap

        # ---------- 1. 文字列変更 T01-T19 ----------
        text_edit(wsmap["表紙"], "X1", "clear", None, "表紙")
        text_edit(wsmap["表紙"], "U12", "clear", None, "表紙")
        text_edit(wsmap["構成と管理情報"], "C8", "replace_all",
                  "システム名：LNB(社内呼称)。iLNB(統合ライン管理システム)は製品資料上の名称であり、社内の LNB と同一かは未確認(§12 No.1 参照)", "構成と管理情報")
        text_edit(wsmap["構成と管理情報"], "C9", "replace_all",
                  "ソフトウェア：LNB ソフト(製品資料上の名称は iLNB·同一性は未確認)", "構成と管理情報")
        text_edit(wsmap["構成と管理情報"], "C14", "repl",
                  [("他システムとの連携：Pana-CIM のデータを参照。",
                    "他システムとの連携：Pana-CIM のデータを参照する関係が相関図草案にあり、参照の方向を含めて未確認(§12 No.6 参照)。")], "構成と管理情報")
        text_edit(wsmap["構成と管理情報"], "C17", "append",
                  ("読み取った。", "IP アドレスの一次資料(実機·構成資料)での確認は未実施。"), "構成と管理情報")
        text_edit(wsmap["構成と管理情報"], "C104", "repl",
                  [("(Stage 5·2026-10-28確定)", "(Stage 5·2026-10-28確定·2026-11-02 本書へ複製)"),
                   ("図では引いてあるが実機で未確認。", "図では引いてある。図の配置と表示の承認は未了で、接続関係の実機での確認は未実施(§12 No.6 参照)。")], "構成と管理情報")
        text_edit(wsmap["構成と管理情報"], "C55", "append",
                  ("伏字)", " 画像は1バンド幅へ拡大して配置する。画面内の細部の判読には限界があり、必要な部分の再取得(実機)は未了。"), "構成と管理情報")
        text_edit(wsmap["目次"], "A8", "repl", [("2-2", "2-3")], "目次")
        text_edit(wsmap["目次"], "C8", "repl", [("2-2", "2-3")], "目次")
        text_edit(wsmap["定期管理"], "C9", "replace_all",
                  "順序の制約：LNB が Pana-CIM のデータを参照する関係は相関図草案上の記載であり、参照の方向を含めて未確認(§12 No.27 参照)。順序を誤った場合の影響も確認されていない。", "定期管理")
        text_edit(wsmap["バックアップ"], "C15", "repl",
                  [("Pana-CIM と Eg-Pro では、バックアップ障害が2件とも「成否を確認する担当が決まっていなかった」ことで長期化している(Eg-Pro のサブサーバー同期は1年以上、nksv523 は6月から暫定運用のまま)。",
                    "バックアップ障害の際に、成否を確認する担当が決まっていない状態が続き、暫定運用が長期化した例がある(Eg-Pro のサブサーバー同期·nksv523。継続期間の照合は未実施)。")], "バックアップ")
        text_edit(wsmap["バックアップ"], "C16", "repl",
                  [("インポートして戻す。", "インポートして戻す。対象はジョブデータ(DGS のエクスポート)。DB データ·LNB 設定·実績帳票を対象に含めるかは未確認。")], "バックアップ")
        text_edit(wsmap["復旧"], "C13", "replace_all",
                  "※バックアップが復旧に使えるかは、戻す試験で確認する。本手順に基づく復旧試験の実施記録は2026-10-14時点で未確認。§6 が確定したら、戻す試験を実施してから本章を確定する。", "復旧")
        text_edit(wsmap["管理体制"], "C16", "repl",
                  [("本人確認で確定。", "本人確認に基づく(裏付け記録の照合は未了)。"),
                   ("本確認を正とする。", "本確認を正として扱う。")], "管理体制")
        text_edit(wsmap["異常時の対応"], "C19", "append",
                  ("結論に至っていない。", "(§12 No.18·20 参照)"), "異常時の対応")
        text_edit(wsmap["チェックシート(月次・異常時)"], "C12", "replace_all",
                  "＊Pana-CIM と同日に実施する場合は、順序を記録すること。LNB が Pana-CIM のデータを参照する関係は相関図草案上の記載であり、参照の方向を含めて未確認(§12 No.27 参照)。順序が結果に影響するかは確認されていない。", "チェックシート(月次・異常時)")
        text_edit(wsmap["引用と部品照合"], "C11", "repl",
                  [("食い違いがあれば本付録を正とする。", "食い違いの有無は本付録を参照して照合する。")], "引用と部品照合")
        text_edit(wsmap["引用と部品照合"], "C11", "append",
                  ("照合する。", "引用原文と出典資料の該当頁·版の照合は未確認。"), "引用と部品照合")
        text_edit(wsmap["用語"], "C31", "append",
                  ("(§12 No.34)", "。表記は画面上の設備識別名であり、実機の型式との対応は未確認。"), "用語")

        # ---------- 2. 手動改ページの解除 ----------
        for name in ("構成と管理情報", "定期管理", "バックアップ", "会議課題一覧(一時)"):
            delete_manual_breaks(wsmap[name], name)

        # ---------- 3. UsedRange 縮退 ----------
        try_delete(wsmap["目次"], 23, 60, "目次")
        try_delete(wsmap["日次点検"], 34, 121, "日次点検")
        try_delete(wsmap["定期管理"], 16, 133, "定期管理")
        try_delete(wsmap["バックアップ"], 56, 59, "バックアップ")
        try_delete(wsmap["復旧"], 14, 335, "復旧", colend="BP")
        try_delete(wsmap["異常時の対応"], 30, 144, "異常時の対応")
        try_delete(wsmap["チェックシート(日次)"], 22, 171, "チェックシート(日次)")
        if not try_delete(wsmap["チェックシート(月次・異常時)"], 31, 78, "チェックシート(月次・異常時)"):
            try_delete(wsmap["チェックシート(月次・異常時)"], 31, 74, "チェックシート(月次・異常時):fallback74")
        try_delete(wsmap["会議課題一覧(一時)"], 42, 528, "会議課題", colend="BR")
        try_delete(wsmap["要確認事項一覧"], 48, 204, "要確認")
        try_delete(wsmap["引用と部品照合"], 27, 313, "引用")

        # ---------- 4. 列幅 ----------
        DEF = {"A": 3, "B:AY": 1.0, "AZ": 2.22}
        for n in ("用語", "構成と管理情報", "日次点検", "定期管理", "バックアップ",
                  "復旧", "異常時の対応", "引用と部品照合"):
            set_widths(wsmap[n], DEF)
        set_widths(wsmap["目次"], {"A": 4, "B": 30, "C": 5, "D:I": 0.4, "J:AY": 0.3, "AZ": 2.22})
        set_widths(wsmap["管理体制"], {"A": 3, "B": 1, "C": 3, "D": 1, "E": 7, "F:AY": 0.85, "AZ": 2.22})
        set_widths(wsmap["チェックシート(日次)"],
                   {"A": 7, "B": 0.5, "C": 8, "D": 0.5, "E": 8, "F": 0.5, "G": 8, "H": 0.5,
                    "I": 12, "J": 0.5, "K": 9, "L": 0.5, "M": 9, "N:AY": 0.3, "AZ": 2.22})
        set_widths(wsmap["チェックシート(月次・異常時)"],
                   {"A": 7, "B": 0.5, "C": 30, "D": 0.5, "E": 9, "F": 0.5, "G": 8, "H": 0.5,
                    "I": 10, "J": 0.5, "K": 9, "L": 0.5, "M": 6, "N:AY": 0.3, "AZ": 2.22})
        set_widths(wsmap["会議課題一覧(一時)"],
                   {"A": 2, "B": 0.5, "C": 8, "D": 0.5, "E": 8, "F": 0.5, "G": 10, "H:AY": 0.6, "AZ": 2.22})
        set_widths(wsmap["要確認事項一覧"],
                   {"A": 4, "B": 1, "C": 10, "D": 1, "E": 12, "F": 1, "G": 10, "H:AY": 0.5, "AZ": 2.22})
        act("WIDTHS set")

        # ---------- 5. 図形 Placement ----------
        for n in ("構成と管理情報", "バックアップ", "相関図"):
            act(f"PLACEMENT {n}: {placement_all(wsmap[n])}")

        # ---------- 6. 行書式・行高 ----------
        def apply(ws, rows, label):
            for item in rows:
                r, kind = item[0], item[1]
                opt = item[2:]
                if kind == "chap":
                    band_style(ws, r, CHAP_FILL)
                elif kind == "sec":
                    band_style(ws, r, SEC_FILL)
                elif kind == "labelc":
                    label_cell(ws, f"A{r}", wrap=False)
                    body_style(ws, r)
                    ws.Range(f"C{r}").Font.Bold = True
                    ws.Range(f"C{r}").Font.Size = 11.0
                    ws.Range(f"C{r}").Font.Name = FONT
                    ws.Rows[r].RowHeight = 19.1
                elif kind == "label":
                    cols = opt[0]
                    wrap = opt[1] if len(opt) > 1 else False
                    for c in cols:
                        label_cell(ws, f"{c}{r}", wrap=wrap)
                    ws.Rows[r].RowHeight = opt[2] if len(opt) > 2 else 19.1
                elif kind == "label10":
                    for c in opt[0]:
                        c_ = ws.Range(f"{c}{r}")
                        font_of(c_, 10.0, bold=True)
                        c_.WrapText = False
                        c_.HorizontalAlignment = XL_CENTER
                        c_.VerticalAlignment = XL_CENTER
                        c_.Interior.Color = SEC_FILL
                    ws.Rows[r].RowHeight = 19.1
                elif kind == "title":
                    ensure_merge(ws, f"A{r}:AZ{r}", f"A{r}")
                    rng = ws.Range(f"A{r}:AZ{r}")
                    font_of(rng, 11.0, bold=True)
                    rng.WrapText = True
                    rng.HorizontalAlignment = XL_LEFT
                    rng.VerticalAlignment = XL_CENTER
                    v = get_val(ws, f"A{r}")
                    ws.Rows[r].RowHeight = calc_lines(v, col_range_width_pt(ws, "A", "AZ"), 11.0) * 15.0 + 4.1
                elif kind == "aka":
                    ex = extras_in_row(ws, r)
                    if ex:
                        raise SystemExit(f"GUARD {label} r{r} aka: C列以外に値 {ex[:3]}")
                    body_style(ws, r)
                    aka_line(ws, r)
                    row_h_body(ws, r, "C", "AZ")
                elif kind == "stmt":
                    c = ws.Range(f"C{r}")
                    font_of(c, 11.0)
                    c.WrapText = True
                    c.HorizontalAlignment = XL_LEFT
                    c.VerticalAlignment = XL_TOP
                    row_h_body(ws, r, "C", "C")
                elif kind == "body10g":
                    ex = extras_in_row(ws, r)
                    if ex:
                        REP["kaigi_extras"].append({"row": r, "extras": [c for c, _ in ex][:6]})
                        c = ws.Range(f"C{r}")
                        font_of(c, 10.0)
                        c.WrapText = True
                        c.HorizontalAlignment = XL_LEFT
                        c.VerticalAlignment = XL_TOP
                        row_h_body(ws, r, "C", "C", size=10.0, pitch=14.4)
                    else:
                        body_style(ws, r, size=10.0)
                        row_h_body(ws, r, "C", "AZ", size=10.0, pitch=14.4)
                else:  # body
                    ex = extras_in_row(ws, r)
                    if ex:
                        raise SystemExit(f"GUARD {label} r{r} body: C列以外に値 {ex[:3]}")
                    body_style(ws, r)
                    if get_val(ws, f"A{r}"):
                        a = ws.Range(f"A{r}")
                        font_of(a, 11.0)
                        a.WrapText = False
                        a.HorizontalAlignment = XL_LEFT
                        a.VerticalAlignment = XL_TOP
                    row_h_body(ws, r, "C", "AZ")

        # 目次: 注記の結合と折返し(書式は現状維持·題目打ち切り解消)
        m = wsmap["目次"]
        for r in (10, 15, 17, 19):
            ensure_merge(m, f"J{r}:AZ{r}", f"J{r}")
            rng = m.Range(f"J{r}:AZ{r}")
            rng.WrapText = True
            rng.VerticalAlignment = XL_TOP
            sz = float(m.Range(f"J{r}").Font.Size)
            m.Rows[r].RowHeight = calc_lines(get_val(m, f"J{r}"), col_range_width_pt(m, "J", "AZ"), sz) * 14.4 + 4.1
        b22 = m.Range("B22")
        b22.WrapText = True
        b22.VerticalAlignment = XL_TOP
        sz22 = float(b22.Font.Size)
        m.Rows[22].RowHeight = calc_lines(get_val(m, "B22"), col_range_width_pt(m, "B", "B"), sz22) * 14.4 + 4.1
        act("目次 note rows")

        apply(wsmap["用語"], [(6, "chap"), (7, "labelc")] + [(r, "body") for r in range(8, 33)], "用語")
        apply(wsmap["構成と管理情報"],
              [(6, "sec"), (7, "labelc")] + [(r, "body") for r in range(8, 15)] +
              [(16, "sec"), (17, "aka"), (18, "label", ["A", "C", "E"])] +
              [(r, "body") for r in (19, 20, 21)] +
              [(23, "aka"), (24, "label", ["A", "C"])] +
              [(r, "body") for r in range(25, 31)] +
              [(55, "body"), (80, "body"), (101, "body"), (103, "sec")] +
              [(r, "body") for r in range(104, 108)], "構成と管理情報")
        # 相関図: r7-r10 を C:AZ 結合+折返し+行高(A:AZではC列の値が失われるため C 起点_dump実測)
        sk = wsmap["相関図"]
        for r in (7, 8, 9, 10):
            ensure_merge(sk, f"C{r}:AZ{r}", f"C{r}")
            rng = sk.Range(f"C{r}:AZ{r}")
            font_of(rng, 11.0)
            rng.WrapText = True
            rng.HorizontalAlignment = XL_LEFT
            rng.VerticalAlignment = XL_TOP
            row_h_body(sk, r, "C", "AZ")
        act("相関図 r7-10")
        apply(wsmap["管理体制"],
              [(6, "chap"), (7, "label", ["A", "C", "E"])] +
              [(r, "body") for r in range(8, 15)] +
              [(16, "aka"), (17, "sec")] + [(r, "body") for r in (18, 19)], "管理体制")
        apply(wsmap["日次点検"],
              [(6, "chap"), (7, "aka"), (8, "sec"), (9, "body"), (10, "label", ["A", "C"])] +
              [(r, "body") for r in range(11, 17)] +
              [(18, "sec")] + [(r, "body") for r in (19, 20)] +
              [(22, "sec"), (23, "aka"), (24, "label", ["A", "C"])] +
              [(r, "body") for r in range(25, 30)] +
              [(31, "aka"), (32, "sec"), (33, "body")], "日次点検")
        apply(wsmap["定期管理"],
              [(6, "chap")] + [(r, "body") for r in (7, 8, 9)] +
              [(11, "sec")] + [(r, "body") for r in range(12, 16)], "定期管理")
        apply(wsmap["バックアップ"],
              [(6, "chap"), (7, "labelc")] + [(r, "body") for r in range(8, 14)] +
              [(15, "aka"), (16, "body")] +
              [(r, "body") for r in (18, 26, 39, 55)], "バックアップ")
        apply(wsmap["復旧"],
              [(6, "chap"), (7, "labelc")] + [(r, "body") for r in range(8, 12)] +
              [(13, "aka")], "復旧")
        apply(wsmap["異常時の対応"],
              [(6, "sec"), (7, "aka"), (9, "sec"), (10, "label", ["A", "C"])] +
              [(r, "body") for r in range(11, 18)] +
              [(19, "aka"), (20, "sec"), (21, "label", ["A", "C"])] +
              [(r, "body") for r in range(22, 28)] +
              [(29, "aka")], "異常時の対応")
        apply(wsmap["チェックシート(日次)"],
              [(6, "chap"), (7, "aka")] + [(r, "body") for r in (8, 9, 10)] +
              [(12, "label", ["A", "C", "E", "G", "I", "K", "M"])] +
              [(r, "stmt") for r in (13, 14, 15)] +
              [(17, "aka"), (18, "sec")] + [(r, "body") for r in (19, 20, 21)], "チェックシート(日次)")
        apply(wsmap["チェックシート(月次・異常時)"],
              [(6, "sec"), (7, "aka"), (8, "label", ["A", "C", "E", "G", "I"], True, 34.0)] +
              [(r, "stmt") for r in (9, 10)] +
              [(12, "aka"), (13, "sec"), (14, "label", ["A", "C", "E", "G", "I", "K", "M"], True, 34.0)] +
              [(r, "stmt") for r in (15, 16)] +
              [(18, "aka"), (19, "sec"), (20, "aka"), (21, "label", ["A", "C", "E", "G", "I", "K"], True, 34.0)] +
              [(r, "stmt") for r in (22, 23, 24)] +
              [(26, "sec"), (27, "aka"), (28, "label", ["A", "C", "E", "G", "I"], True, 34.0)] +
              [(r, "stmt") for r in (29, 30)], "チェックシート(月次・異常時)")
        apply(wsmap["会議課題一覧(一時)"],
              [(6, "title"), (7, "body10g"), (8, "title"), (9, "label10", ["A", "C", "E", "G"])] +
              [(r, "body10g") for r in range(10, 22)] +
              [(23, "title"), (24, "label10", ["A", "C", "E"])] +
              [(r, "body10g") for r in range(25, 34)] +
              [(35, "title"), (36, "label10", ["A", "C", "E", "G"])] +
              [(r, "body10g") for r in range(37, 42)], "会議課題一覧(一時)")
        apply(wsmap["要確認事項一覧"],
              [(6, "chap"), (7, "aka"), (8, "label", ["A", "C", "E", "G"])] +
              [(r, "body") for r in range(9, 48)], "要確認事項一覧")
        apply(wsmap["引用と部品照合"],
              [(6, "chap")] + [(r, "body") for r in (7, 8)] +
              [(10, "sec"), (11, "aka"), (12, "sec"), (13, "body")] +
              [(15, "sec")] + [(16, "body")] + [(18, "body"), (19, "sec")] +
              [(r, "body") for r in (20, 21)] +
              [(23, "sec")] + [(r, "body") for r in (24, 25, 26)], "引用と部品照合")
        act("ROW STYLES applied")

        # ---------- 7. 構成と管理情報: 図1の1バンド幅拡大+行高·図3のアンカー移動 ----------
        kc = wsmap["構成と管理情報"]
        fig1 = fig3 = None
        for sh in kc.Shapes:
            try:
                if int(sh.Type) == 13:
                    r0 = int(sh.TopLeftCell.Row)
                    if r0 == 31:
                        fig1 = sh
                    elif r0 == 80:
                        fig3 = sh
            except Exception:
                pass
        assert fig1 is not None and fig3 is not None, "構成の画像が見つからない"
        old_w, old_h = float(fig1.Width), float(fig1.Height)
        band_w = float(kc.Range("C31:AZ31").Width)
        sc = band_w / old_w
        new_h = old_h * sc
        fig1.Width = band_w
        fig1.Height = new_h
        fig1.Left = float(kc.Range("C31").Left)
        rh = math.ceil((new_h + 2.0) * 10.0 / 24.0) / 10.0
        for r in range(31, 55):
            kc.Rows[r].RowHeight = rh
        # 図3: アンカー C80(図2キャプション行と同一行)→ C81 へ移動(最小調整·キャプション分離防止)
        fig3.Top = float(kc.Range("C81").Top)
        fig3.Left = float(kc.Range("C81").Left)
        REP["pics"]["構成と管理情報"] = {
            "fig1": {"old_w": round(old_w, 1), "old_h": round(old_h, 1),
                     "new_w": round(band_w, 1), "new_h": round(new_h, 1), "scale": round(sc, 3)},
            "rows31_54_rowh": rh, "fig3_anchor": "C80->C81"}
        act(f"FIG1 scale={sc:.3f} new_h={new_h:.1f} rows31-54={rh}pt FIG3->C81")

        # ---------- 8. 改ページの再構築 ----------
        for name, rows in (("構成と管理情報", [31, 56, 81]), ("バックアップ", [18, 26, 39])):
            ws = wsmap[name]
            for r in rows:
                ws.HPageBreaks.Add(ws.Range(f"A{r}"))
            REP["breaks"][name] = rows
            act(f"BREAKS {name}: {rows}")

        # ---------- 9. 印刷設定 ----------
        AREAS = {
            "表紙": "$A$1:$Y$36", "目次": "$A$1:$AZ$22", "用語": "$A$1:$AZ$32",
            "構成と管理情報": "$A$1:$AZ$107", "管理体制": "$A$1:$AZ$19",
            "日次点検": "$A$1:$AZ$33", "定期管理": "$A$1:$AZ$15", "バックアップ": "$A$1:$AZ$55",
            "復旧": "$A$1:$AZ$14", "異常時の対応": "$A$1:$AZ$29",
            "チェックシート(日次)": "$A$1:$AZ$21", "チェックシート(月次・異常時)": "$A$1:$AZ$30",
            "会議課題一覧(一時)": "$A$1:$AZ$41", "要確認事項一覧": "$A$1:$AZ$47",
            "引用と部品照合": "$A$1:$AZ$26",
        }
        for name in ORDER17:
            ws = wsmap[name]
            ps = ws.PageSetup
            if name in AREAS:
                ps.PrintArea = AREAS[name]
                REP["pa"][name] = AREAS[name]
            if name != "相関図":
                ps.LeftMargin = ML; ps.RightMargin = MR
                ps.TopMargin = MT; ps.BottomMargin = MB
                ps.HeaderMargin = MH; ps.FooterMargin = MF
            if name == "要確認事項一覧":
                ps.LeftFooter, ps.CenterFooter, ps.RightFooter = FOOT
                ps.RightHeader = "\n&P"
                ps.PrintTitleRows = "$1:$3"
            if name == "表紙":
                ps.Zoom = False; ps.FitToPagesWide = 1; ps.FitToPagesTall = 1
            if name == "相関図":
                ps.Zoom = False; ps.FitToPagesWide = 1; ps.FitToPagesTall = 1
            if name in ("チェックシート(日次)", "チェックシート(月次・異常時)", "要確認事項一覧"):
                ps.Zoom = False; ps.FitToPagesWide = 1; ps.FitToPagesTall = False
        # 相関図: 印刷範囲が図形外接を包含するかを実測で検査し、不足時のみ拡張
        sk = wsmap["相関図"]
        bl = bt = float("inf")
        br = bb = float("-inf")
        for sh in sk.Shapes:
            l_ = float(sh.Left); t_ = float(sh.Top)
            bl = min(bl, l_); bt = min(bt, t_)
            br = max(br, l_ + float(sh.Width)); bb = max(bb, t_ + float(sh.Height))
        ay_right = 0.0
        for cl in COLS[:51]:  # A..AY
            ay_right += px(sk.Columns[cl].ColumnWidth) * 0.75
        row60_bottom = sum(float(sk.Rows[r].RowHeight) for r in range(1, 61))
        REP["pics"]["相関図_bbox"] = {"left": round(bl, 1), "top": round(bt, 1),
                                      "right": round(br, 1), "bottom": round(bb, 1)}
        if br > ay_right - 0.5 or bb > row60_bottom - 0.5:
            acc = 0.0; pa_col = "AZ"
            for cl in COLS[:52]:
                acc += px(sk.Columns[cl].ColumnWidth) * 0.75
                if acc >= br + 1.0:
                    pa_col = cl; break
            accy = 0.0; pa_row = 80
            for r in range(1, 81):
                accy += float(sk.Rows[r].RowHeight)
                if accy >= bb + 1.0:
                    pa_row = r; break
            newpa = f"$A$1:${pa_col}${max(pa_row, 60)}"
            sk.PageSetup.PrintArea = newpa
            REP["pa"]["相関図"] = newpa
            act(f"相関図 PA extended -> {newpa}")
        else:
            REP["pa"]["相関図"] = "$A$1:$AY$60(維持)"
            act(f"相関図 PA keep $A$1:$AY$60 (bbox r={br:.1f}<={ay_right:.1f}, b={bb:.1f}<={row60_bottom:.1f})")
        act("PAGESETUP applied")

        # ---------- 10. 橙色走査(M4) ----------
        for name in ORDER17:
            if name == "相関図_old":
                continue
            ws = wsmap[name]
            ur = ws.UsedRange
            try:
                vals = ur.Value
            except Exception:
                continue
            if not isinstance(vals, tuple):
                continue
            r0 = ur.Row; c0 = ur.Column
            for i, row in enumerate(vals):
                if not isinstance(row, tuple):
                    continue
                for j, v in enumerate(row):
                    if v is None or str(v) == "":
                        continue
                    cell = ws.Cells(r0 + i, c0 + j)
                    fc_ = cell.Font.Color
                    if isinstance(fc_, (int, float)):
                        rr, gg, bbb = int(fc_) & 255, (int(fc_) >> 8) & 255, (int(fc_) >> 16) & 255
                        if rr >= 200 and 90 <= gg <= 190 and bbb <= 90:
                            cell.Font.Color = AKA
                            REP["orange"].append({"sheet": name, "addr": addr_str(cell), "type": "font", "from": int(fc_)})
                    ic_ = cell.Interior.Color
                    if isinstance(ic_, (int, float)) and int(ic_) != 16777215:
                        rr, gg, bbb = int(ic_) & 255, (int(ic_) >> 8) & 255, (int(ic_) >> 16) & 255
                        if rr >= 200 and 90 <= gg <= 190 and bbb <= 90:
                            REP["orange"].append({"sheet": name, "addr": addr_str(cell), "type": "fill", "from": int(ic_)})
        act(f"ORANGE scan: {len(REP['orange'])} hits")

        # ---------- 11. 保存 ----------
        wb.Save()
        act("SAVED (pass1)")

        # ---------- 12. 頁数計測 → 採番 ----------
        def export_all17():
            counts, blanks = {}, {}
            for name in ORDER17:
                sh = wsmap[name]
                p = os.path.join(PAGES_DIR, f"{name}.pdf")
                sh.ExportAsFixedFormat(0, p, 0, True, False)
                rd = PdfReader(p)
                counts[name] = len(rd.pages)
                bl = []
                for i, pg in enumerate(rd.pages):
                    txt = pg.extract_text() or ""
                    try:
                        im = len(pg.images)
                    except Exception:
                        im = 1
                    if len(txt) < 80 and im == 0:
                        bl.append(i + 1)
                if bl:
                    blanks[name] = bl
            return counts, blanks

        counts, blanks = export_all17()
        REP["counts"] = counts
        REP["blanks"] = {"pass1": blanks}
        act(f"PAGES: {counts} BLANKS: {blanks}")
        assert not blanks, f"blank pages: {blanks}"

        page = 1
        for name in ORDER17[:16]:  # 表紙..要確認事項一覧
            n = counts[name]
            if name != "表紙":
                wsmap[name].PageSetup.FirstPageNumber = page
                REP["numbering"][name] = page
            page += n
        wb.Save()
        act("SAVED (pass2: numbering 2-16)")

        # ---------- 13. 冊出力で申し送り頁数を実測 ----------
        cands = [f for f in os.listdir(VAULT_PDF_DIR)
                 if f.lower().endswith(".pdf") and "LNB管理手順書案" in f]
        if cands:
            cands.sort(key=lambda f: os.path.getmtime(os.path.join(VAULT_PDF_DIR, f)), reverse=True)
            vault_pdf = os.path.join(VAULT_PDF_DIR, cands[0])
        else:
            vault_pdf = os.path.join(VAULT_PDF_DIR, "LNB管理手順書案_未承認.pdf")
        REP["pdf"] = vault_pdf
        wb.ExportAsFixedFormat(0, vault_pdf, 0, True, False)
        book_pages = len(PdfReader(vault_pdf).pages)
        cred_pages = book_pages - sum(counts.values())
        REP["book_pages"] = book_pages
        REP["cred_pages"] = cred_pages
        act(f"BOOK {vault_pdf}: {book_pages}p cred={cred_pages}p")
        assert cred_pages >= 1, f"cred_pages={cred_pages}"
        assert book_pages == sum(counts.values()) + cred_pages

        # ---------- 14. 引用の頁番号 ----------
        wsmap["引用と部品照合"].PageSetup.FirstPageNumber = page + cred_pages
        REP["numbering"]["引用と部品照合"] = page + cred_pages
        wb.Save()
        act(f"SAVED (pass3: 引用 FirstPageNumber={page + cred_pages})")

        # ---------- 15. 最終出力·検査 ----------
        counts2, blanks2 = export_all17()
        assert counts2 == counts, f"pagination shifted: {counts2}"
        assert not blanks2, f"blank pages: {blanks2}"
        REP["blanks"]["pass2"] = blanks2
        # 幽霊検査(画像の頁下端はみ出し) — 構成と管理情報·バックアップ
        for name in ("構成と管理情報", "バックアップ"):
            doc = pymupdf.open(os.path.join(PAGES_DIR, f"{name}.pdf"))
            bad = []
            for pi in range(doc.page_count):
                for inf in doc[pi].get_image_info():
                    b = inf["bbox"]
                    if b[3] > 786.0:
                        bad.append((pi + 1, round(b[1], 1), round(b[3], 1)))
            doc.close()
            REP["ghosts"][name] = bad
            assert not bad, f"ghost images {name}: {bad}"
        act("GHOSTCHECK ok")

        wb.ExportAsFixedFormat(0, vault_pdf, 0, True, False)
        book_pages2 = len(PdfReader(vault_pdf).pages)
        assert book_pages2 == book_pages, f"book pages shifted: {book_pages2}"
        act(f"BOOK re-export: {book_pages2}p")

        # ---------- 16. 冊PDF再構築(個別17シート+認証情報頁スポット) ----------
        with open(vault_pdf, "rb") as f:
            book_bytes = f.read()
        bookrd = PdfReader(io.BytesIO(book_bytes))
        assert len(bookrd.pages) == book_pages
        offset = sum(counts[n] for n in ORDER17[:16])
        writer = PdfWriter()
        for name in ORDER17[:16]:
            for p in PdfReader(os.path.join(PAGES_DIR, f"{name}.pdf")).pages:
                writer.add_page(p)
        for i in range(offset, offset + cred_pages):
            writer.add_page(bookrd.pages[i])
        for p in PdfReader(os.path.join(PAGES_DIR, "引用と部品照合.pdf")).pages:
            writer.add_page(p)
        with open(vault_pdf, "wb") as f:
            writer.write(f)
        final_pages = len(PdfReader(vault_pdf).pages)
        assert final_pages == book_pages, f"merged {final_pages} != book {book_pages}"
        act(f"MERGED -> {vault_pdf} ({final_pages}p)")

        wb.Close(SaveChanges=False)
    except Exception:
        if wb is not None:
            try:
                wb.Close(SaveChanges=False)
            except Exception:
                pass
        raise
    finally:
        app.Quit()

    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(REP, f, ensure_ascii=False, indent=1)
    print("DONE", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        try:
            with open(REPORT, "w", encoding="utf-8") as f:
                json.dump(REP, f, ensure_ascii=False, indent=1)
        except Exception:
            pass
        sys.exit(1)
