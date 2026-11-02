# -*- coding: utf-8 -*-
"""Pana-CIM管理手順書案_未承認.xlsx 改修実装 (Excel COM / openpyxl保存禁止)
計画: 改修計画_管理手順書全文改修_20261102.md / 変更リスト_Pana-CIM冊_20261102.md
"""
import os, sys, json, math, hashlib, traceback, time

WORK = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
XLSX = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\Pana-CIM管理手順書案_未承認.xlsx"
VAULT_PDF_DIR = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
PAGES_DIR = os.path.join(WORK, "scripts", "tmp_pages")
REPORT = os.path.join(WORK, "scripts", "impl_report.json")
EXPECT_SHA = "7b41e825c5f73b46e041704b2e741e2c69fadd79a1508e6fc5e983b0277b1e52"

FONT = "Meiryo UI"
INK = 7949855        # RGB(31,78,121) 藍
CHAP_FILL = 16184006 # RGB(198,242,246)
SEC_FILL = 16184046  # RGB(238,242,246)
AKA = 3029680        # 朱(前例実測)
XL_LEFT, XL_CENTER, XL_TOP = -4131, -4108, -4160
XL_CONT, XL_THICK, XL_THIN, XL_NONE = 1, 4, 2, -4142
XL_EDGE_LEFT = 7
XL_MOVE = 2
PAGE_CAP = 841.9 - 42.52 - 56.69  # 742.7pt

REP = {"actions": [], "errors": [], "texts": [], "fc": None, "breaks": {},
       "orange": [], "deletes": {}, "pages": {}, "numbering": {}, "pdf": None}

def act(msg): REP["actions"].append(msg); print("[act]", msg, flush=True)

def px(w):
    return int(((256.0 * w + 18.0) / 256.0) * 7) + 5

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

COLS = [chr(65 + i) for i in range(26)] + ["A" + chr(65 + i) for i in range(26)]  # A..AZ

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

def addr_str(obj, *args):
    a = obj.Address
    if callable(a):
        a = a(*args) if args else a()
    return str(a).replace("$", "")

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
        ok = True
    elif kind == "repl":
        if all(a not in old for a, b in spec) and all(b in old for a, b in spec):
            REP["texts"].append({"cell": addr, "sheet": label, "status": "OK(already)"})
            return
        new = old
        for a, b in spec:
            if a not in new:
                REP["errors"].append(f"{label}: 期待文字列なし: {a[:30]}")
                ok = False
                new = None
                break
            new = new.replace(a, b, 1)
        ok = new is not None
    elif kind == "append":
        if spec[1] in old:
            REP["texts"].append({"cell": addr, "sheet": label, "status": "OK(already)"})
            return
        ok = old.endswith(spec[0]) if spec[0] else True
        new = old + spec[1]
    elif kind == "append_nl":
        if spec[1] in old:
            REP["texts"].append({"cell": addr, "sheet": label, "status": "OK(already)"})
            return
        ok = True
        new = old + "\n" + spec[1]
    elif kind == "clear":
        if old.strip() == "":
            REP["texts"].append({"cell": addr, "sheet": label, "status": "OK(already)"})
            return
        ok = True
        new = ""
    else:
        raise ValueError(kind)
    if not ok:
        REP["texts"].append({"cell": addr, "sheet": label, "status": "SKIP", "old": old[:120]})
        return
    if kind == "clear":
        try:
            ws.Range(addr).ClearContents()
        except Exception:
            ws.Range(addr).MergeArea.ClearContents()
    else:
        ws.Range(addr).Value = new
    REP["texts"].append({"cell": addr, "sheet": label, "status": "OK", "old": old[:160], "new": new[:160]})
    act(f"TEXT {label}.{addr}")

def placement_all(ws):
    n = 0
    for sh in ws.Shapes:
        sh.Placement = XL_MOVE
        n += 1
    return n

def collect_pics(ws):
    pics = []
    for sh in ws.Shapes:
        if sh.Type in (13, 10):  # picture / linked picture
            pics.append({"row": int(sh.TopLeftCell.Row), "h": float(sh.Height)})
    pics.sort(key=lambda d: d["row"])
    return pics

def page_walk(heights, last, breaks):
    """returns pages: list of (start_row, start_y)"""
    pages = []
    page_top = 0.0
    start_row = 1
    y = 0.0
    for r in range(1, last + 1):
        h = heights.get(r, 12.8)
        if r in breaks and r != 1:
            pages.append((start_row, page_top))
            page_top = y
            start_row = r
        elif y + h > page_top + PAGE_CAP and y > page_top:
            pages.append((start_row, page_top))
            page_top = y
            start_row = r
        y += h
    pages.append((start_row, page_top))
    return pages

def fix_pic_breaks(ws, heights, last, pics, tag):
    breaks = set()
    for _ in range(8):
        tops = {}
        y = 0.0
        for r in range(1, last + 2):
            tops[r] = y
            y += heights.get(r, 12.8)
        pages = page_walk(heights, last, breaks)
        changed = False
        for p in pics:
            ra = p["row"]
            if ra > last:
                continue
            top = tops[ra]
            pst = max((py for sr, py in pages if sr <= ra), default=0.0)
            if top + p["h"] > pst + PAGE_CAP - 1.0:
                breaks.add(ra)
                changed = True
        if not changed:
            break
    for r in sorted(breaks):
        ws.HPageBreaks.Add(ws.Range(f"A{r}"))
    REP["breaks"][tag] = sorted(breaks)
    act(f"BREAKS {tag}: {sorted(breaks)}")
    return breaks

def row_heights(ws, last):
    hs = {}
    for r in range(1, last + 1):
        hs[r] = float(ws.Rows[r].RowHeight)
    return hs

def main():
    os.makedirs(PAGES_DIR, exist_ok=True)
    s = sha256(XLSX)
    if s != EXPECT_SHA:
        raise SystemExit(f"SHA mismatch: {s}")
    act("SHA OK")

    import win32com.client as win32
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    try:
        wb = app.Workbooks.Open(XLSX, UpdateLinks=0, ReadOnly=False)
        try:
            wb.AutoSaveOn = False
        except Exception:
            pass
        wsmap = {sh.Name: sh for sh in wb.Worksheets}

        # ---------- 1. 文字列変更 ----------
        text_edit(wsmap["表紙"], "X1", "clear", None, "表紙")
        text_edit(wsmap["表紙"], "U12", "clear", None, "表紙")
        text_edit(wsmap["用語"], "C30", "replace_all",
                  "無線スキャナー(PDA)：ライン毎に前側用/後側用がある携帯端末。部品照合と LNB 設定の関係は相関図草案上の記載であり、参照の方向を含めて未確認(相関図)", "用語")
        text_edit(wsmap["構成と管理情報"], "C11", "append",
                  ("アンドン", "。Web 版アンドン(IP 172.25.253.42)は別系統であり、MonitorAndon2 との連携と Pana-CIM との関係は未確認"), "構成と管理情報")
        text_edit(wsmap["構成と管理情報"], "C15", "append",
                  ("", "本項は構成図の内容の要約であり、出典の該当頁の照合は未確認。NPM・FA の略語の展開は未確認で、推測で補わない。表記の IP アドレスと OS の一次資料確認は未実施。"), "構成と管理情報")
        text_edit(wsmap["月次再起動"], "C12", "replace_all",
                  "対象：CIMC-SV(VMware 上の仮想マシン・ゲストOS RHEL 6)。本章の手順は Windows の再起動操作であり、仮想マシンの OS 操作との対応は未確認。Windows の手順を Linux の手順へ置き換えない", "月次再起動")
        text_edit(wsmap["月次再起動"], "C14", "repl",
                  [("随時再起動は従来どおり残る。定期と随時の二本立てとなる。", "随時再起動は従来どおり行う。月次の定期再起動と随時再起動の両方を運用する。")], "月次再起動")
        text_edit(wsmap["月次再起動"], "C27", "repl",
                  [("(スライド1〜2)。原文は付録A-3。", "(スライド1〜2)。文書番号・版・保管場所の特定は未確認。原文は付録A-3。")], "月次再起動")
        text_edit(wsmap["異常時の対応"], "C8", "append_nl",
                  (None, "アンドン異常・稼働モニタ異常を再起動で扱う対応は会議で挙がった候補であり、7-4 の発動条件(「生産情報が取得できません。」)とは別に確認する"), "異常時の対応")
        text_edit(wsmap["異常時の対応"], "C29", "append",
                  ("本文への完全引用とする。", "保管場所の特定は未確認。"), "異常時の対応")
        text_edit(wsmap["バックアップ"], "C7", "replace_all",
                  "＊バックアップ結果の確認は毎日とする(2026-09-30 会議の決定)。取得頻度は端末ごとの手作業・一括取得・自動化を含めて検討中。対象は DB データ・ジョブデータ・LNB 設定・実績帳票。各対象を相互に代替するものとは扱わない。DGS で取得したものを Pana-CIM で保存する。日次点検(削除・再設置時に確認)での最終実行日時と成否の確認で最終実行日時と成否を確認する。", "バックアップ")
        text_edit(wsmap["バックアップ"], "C9", "repl",
                  [("(PDF通し11〜12頁)。原文は付録A-1。", "(PDF通し11〜12頁)。文書番号・版・保管場所の特定は未確認。原文は付録A-1。")], "バックアップ")
        text_edit(wsmap["バックアップ"], "C180", "append",
                  ("(第11章 No.11)。", "手順2の「タブ」は付録A-1 の原文では「タグ」。原 PDF での表記照合は未実施。"), "バックアップ")
        text_edit(wsmap["バックアップ"], "C189", "repl",
                  [("「成否を確認する担当が決まっていなかった」ことで長期化している。Eg-Pro のサブサーバー同期は1年以上、nksv523 は6月から暫定運用のまま。",
                    "成否を確認する担当が決まっていない状態が続き、暫定運用が長期化した例がある(Eg-Pro のサブサーバー同期・nksv523。継続期間の照合は未実施)。")], "バックアップ")
        text_edit(wsmap["復旧"], "C13", "repl",
                  [("※戻す試験を一度もしていない。", "※本手順に基づく復旧試験の実施記録は未確認(2026-10-14 確認時点)。")], "復旧")
        text_edit(wsmap["管理体制"], "C17", "repl",
                  [("本人確認で確定。", "本人確認に基づく(裏付け記録の照合は未了)。"),
                   ("本確認を正とする。", "本確認を正として扱う。")], "管理体制")
        text_edit(wsmap["付録 引用元と確認範囲"], "C7", "repl",
                  [("食い違いがあれば本付録を正とする。", "食い違いの有無は本付録を参照して照合する。"),
                   ("原文の認証情報は伏字にした。操作時は", "原文の認証情報は伏字にした。構成図の説明は図の内容の要約である。操作時は")], "付録")
        yk = wsmap["要確認事項一覧"]
        text_edit(yk, "C35", "replace_all",
                  "27：人名と割り当ての確認／2026-10-14 解決。管理責任者＝茂木（由）・倉林、副管理責任者＝石井・茂木（絵）と本人確認に基づき確定(第3章)。裏付け記録の照合は未了", "要確認事項一覧")
        strike = bool(yk.Range("C9").Font.Strikethrough)
        yk.Range("C35").Font.Strikethrough = strike
        act(f"STRIKE C35 <- C9 ({strike})")
        sk = wsmap["相関図"]
        text_edit(sk, "A10", "append",
                  ("推定事項の明示。", "出典符に掲げた資料の文書番号・版・保管場所、および図中の IP アドレス・OS 表記の一次資料確認は未実施。"), "相関図")

        # ---------- 2. 列幅 ----------
        DEF = {"A": 3, "B:AY": 1.0, "AZ": 2.22}
        set_widths(wsmap["目次"], {"A": 1, "B": 1, "C": 5, "D": 30, "E:I": 0.4, "J:AY": 0.3, "AZ": 2.22})
        for n in ("用語", "構成と管理情報", "月次再起動", "バックアップ", "復旧", "異常時の対応",
                  "要確認事項一覧", "付録 引用元と確認範囲", "7-5仮_サービス起動停止"):
            set_widths(wsmap[n], DEF)
        set_widths(wsmap["管理体制"], {"A": 3, "B": 1, "C": 3, "D": 1, "E": 7, "F:AY": 0.85, "AZ": 2.22})
        set_widths(wsmap["チェックシート(月次・異常時)"],
                   {"A": 6, "B": 0.5, "C": 30, "D": 0.5, "E": 6, "F": 0.5, "G": 6, "H": 0.5,
                    "I": 6, "J": 0.5, "K": 8, "L": 0.5, "M": 5, "N:AY": 0.3, "AZ": 2.22})
        set_widths(wsmap["会議課題一覧(一時)"],
                   {"A": 2, "B": 0.5, "C": 8, "D": 0.5, "E": 8, "F": 0.5, "G": 10, "H:AY": 0.6, "AZ": 2.22})
        act("WIDTHS set")

        # ---------- 3. 図形 Placement ----------
        for n in ("月次再起動", "バックアップ", "異常時の対応", "7-5仮_サービス起動停止", "相関図"):
            act(f"PLACEMENT {n}: {placement_all(wsmap[n])}")

        # ---------- 4. 行書式・行高 ----------
        def apply(ws, rows):
            for r, kind, *opt in rows:
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
                elif kind == "label1":
                    label_cell(ws, f"A{r}", wrap=False)
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
                elif kind == "body10":
                    body_style(ws, r, size=10.0)
                    row_h_body(ws, r, "C", "AZ", size=10.0, pitch=14.4)
                else:  # body
                    body_style(ws, r)
                    if get_val(ws, f"A{r}"):
                        a = ws.Range(f"A{r}")
                        font_of(a, 11.0)
                        a.WrapText = False
                        a.HorizontalAlignment = XL_LEFT
                        a.VerticalAlignment = XL_TOP
                    row_h_body(ws, r, "C", "AZ")

        # 目次
        m = wsmap["目次"]
        m.Range("D19:AZ19").Merge()
        m.Range("D19").WrapText = True
        m.Range("D19").VerticalAlignment = XL_TOP
        sz = float(m.Range("D19").Font.Size)
        m.Rows[19].RowHeight = calc_lines(get_val(m, "D19"), col_range_width_pt(m, "D", "AZ"), sz) * 14.4 + 4.1
        act("目次 r19")

        apply(wsmap["用語"], [(6, "chap"), (7, "labelc")] + [(r, "body") for r in range(8, 32)])
        apply(wsmap["構成と管理情報"],
              [(6, "chap"), (7, "labelc")] + [(r, "body") for r in range(8, 14)] +
              [(15, "body"), (16, "sec")] + [(r, "body") for r in range(17, 21)])
        apply(wsmap["管理体制"],
              [(6, "chap"), (7, "body"), (8, "label", ["A", "C", "E"], False, 19.1)] +
              [(r, "body") for r in range(9, 16)] + [(17, "body"), (18, "sec"), (19, "aka")])
        apply(wsmap["月次再起動"],
              [(6, "aka"), (7, "sec"), (8, "labelc")] + [(r, "body") for r in (9, 10, 11, 12, 14)] +
              [(15, "sec"), (16, "labelc"), (17, "body"), (18, "body"), (19, "body"),
               (21, "sec"), (22, "labelc"), (23, "body"), (24, "body"),
               (26, "sec"), (27, "body"), (28, "body"), (29, "body"), (30, "body"),
               (52, "body"), (75, "body"), (78, "aka"), (79, "labelc")] +
              [(r, "body") for r in (80, 81, 82, 84)] +
              [(85, "sec"), (86, "labelc"), (87, "body"), (88, "body"), (89, "body"),
               (91, "sec"), (92, "body")])
        apply(wsmap["バックアップ"],
              [(6, "chap"), (7, "body"), (9, "body")] + [(r, "body") for r in range(10, 16)] +
              [(r, "body") for r in (35, 57, 79, 101, 127, 153, 177)] +
              [(180, "aka"), (181, "sec"), (182, "labelc")] + [(r, "body") for r in range(183, 188)] +
              [(189, "aka")])
        apply(wsmap["復旧"], [(6, "chap")] + [(r, "body") for r in range(7, 12)] + [(13, "aka")])
        apply(wsmap["異常時の対応"],
              [(6, "chap"), (7, "body"), (8, "body"), (9, "body"), (10, "body"),
               (12, "sec")] + [(r, "body") for r in range(13, 19)] +
              [(20, "body"), (21, "sec"), (22, "body"), (23, "body"), (24, "body"),
               (26, "sec"), (27, "aka"), (28, "body"), (29, "body"), (30, "body"),
               (32, "title"), (33, "labelc"), (34, "body"), (35, "body"), (36, "body"),
               (37, "aka"), (38, "body"), (41, "title")] +
              [(r, "body") for r in range(42, 64)] +
              [(65, "label1"), (66, "body"), (67, "body"), (68, "body"), (69, "body"),
               (71, "title"), (116, "body")] +
              [(r, "body") for r in (131, 147, 163, 177, 191, 206, 217, 240, 258, 270, 280, 295, 307, 320)])
        ck = wsmap["チェックシート(月次・異常時)"]
        apply(ck,
              [(6, "sec"), (7, "label", ["A", "C", "E", "G", "I", "K", "M"], True, 34.0),
               (11, "sec"), (12, "label", ["A", "C", "E", "G", "I"], True, 34.0)] +
              [(r, "stmt") for r in range(13, 19)] +
              [(20, "body"), (21, "sec"), (22, "aka"),
               (23, "label", ["A", "C", "E", "G", "I", "K"], True, 34.0)] +
              [(r, "stmt") for r in range(24, 35)] +
              [(36, "sec"), (37, "label", ["A", "C", "E", "G", "I", "K"], True, 34.0),
               (42, "sec"), (43, "label", ["A", "C", "E", "G", "I"], True, 34.0)])
        apply(wsmap["会議課題一覧(一時)"],
              [(6, "title"), (7, "body10"), (8, "title"),
               (9, "label10", ["A", "C", "E", "G"])] +
              [(r, "body10") for r in range(10, 22)] +
              [(23, "title"), (24, "label10", ["A", "C", "E"])] +
              [(r, "body10") for r in range(25, 34)] +
              [(35, "title"), (36, "label10", ["A", "C", "E", "G"])] +
              [(r, "body10") for r in range(37, 42)])
        apply(wsmap["付録 引用元と確認範囲"],
              [(6, "chap"), (7, "body"), (8, "sec"), (9, "body"), (10, "body"), (11, "body"),
               (13, "sec"), (14, "body"), (16, "sec"), (17, "body"), (19, "sec"),
               (20, "body"), (21, "body"), (23, "chap")] +
              [(r, "body") for r in (24, 25, 26, 27)])
        apply(wsmap["要確認事項一覧"],
              [(6, "chap"), (7, "body"), (8, "label", ["A", "C", "E"], False, 19.1)] +
              [(r, "body") for r in range(9, 36)])
        apply(wsmap["7-5仮_サービス起動停止"],
              [(6, "title"), (7, "body"), (8, "body"), (9, "body"), (10, "body"),
               (11, "title"), (12, "body"), (14, "labelc"),
               (15, "body"), (16, "body"), (17, "body"), (18, "body"),
               (40, "body"), (48, "body"), (51, "title"),
               (52, "body"), (53, "body"), (54, "body"), (55, "body")])
        act("ROW STYLES applied")

        # ---------- 5. UsedRange 縮退 ----------
        def try_delete(ws, r1, r2, tag):
            rng = ws.Range(f"A{r1}:AZ{r2}")
            ok = True
            why = []
            v = rng.Value
            if v is not None:
                ok = False; why.append("value")
            mc = rng.MergeCells
            if mc:  # True or Null(混合)
                ok = False; why.append(f"merge={mc}")
            try:
                bl = all(rng.Borders(k).LineStyle == XL_NONE
                         for k in (7, 8, 9, 10, 11, 12))
            except Exception as e:
                bl = False; why.append(f"border-read:{e}")
            if not bl:
                ok = False; why.append("border")
            for sh in ws.Shapes:
                try:
                    if int(sh.BottomRightCell.Row) >= r1:
                        ok = False; why.append("shape")
                        break
                except Exception:
                    pass
            if ok:
                ws.Rows[f"{r1}:{r2}"].Delete()
                act(f"DELETE {tag} {r1}-{r2}")
            else:
                REP["errors"].append(f"DELETE SKIP {tag}: {why}")
            REP["deletes"][tag] = {"range": f"{r1}-{r2}", "ok": ok, "why": why}

        try_delete(wsmap["目次"], 21, 60, "目次")
        try_delete(wsmap["月次再起動"], 94, 179, "月次再起動")
        try_delete(wsmap["バックアップ"], 190, 222, "バックアップ")
        try_delete(wsmap["復旧"], 15, 335, "復旧")
        try_delete(wsmap["チェックシート(月次・異常時)"], 46, 78, "チェックシート")
        try_delete(wsmap["会議課題一覧(一時)"], 43, 528, "会議課題")
        try_delete(wsmap["付録 引用元と確認範囲"], 29, 204, "付録")
        try_delete(wsmap["要確認事項一覧"], 37, 142, "要確認")

        # ---------- 6. 図解: 改ページ・スケール ----------
        LAST = {"月次再起動": 93, "バックアップ": 190, "7-5仮_サービス起動停止": 56}
        for n, last in LAST.items():
            ws = wsmap[n]
            hs = row_heights(ws, last)
            pics = collect_pics(ws)
            fix_pic_breaks(ws, hs, last, pics, n)

        # 異常時: フローチャートブロック(r71題目+r72以降)→改ページ→必要時のみ縦縮小→画像改ページ
        ws = wsmap["異常時の対応"]
        hs = row_heights(ws, 321)
        y72 = sum(hs[r] for r in range(1, 72))
        fc_top, fc_bot = None, None
        for sh in ws.Shapes:
            try:
                if int(sh.Type) in (13, 10):  # 画像はフローチャートに含めない
                    continue
                r0 = int(sh.TopLeftCell.Row)
                r1_ = int(sh.BottomRightCell.Row)
            except Exception:
                continue
            if r0 >= 72 and r1_ <= 321:
                t = float(sh.Top); b = t + float(sh.Height)
                fc_top = t if fc_top is None else min(fc_top, t)
                fc_bot = b if fc_bot is None else max(fc_bot, b)
        pics = collect_pics(ws)
        if fc_bot is not None:
            block = fc_bot - fc_top
            pics = [{"row": 71, "h": hs.get(71, 12.8) + block}] + pics
            REP["fc"] = {"block_pt": round(block, 1)}
        fix_pic_breaks(ws, hs, 321, pics, "異常時の対応")
        if fc_bot is not None:
            # 改ページ後の実位置で頁内収まりを再確認し、溢れる場合のみ縮小
            breaks = set(REP["breaks"]["異常時の対応"])
            tops = {}
            y = 0.0
            for r in range(1, 322):
                tops[r] = y
                y += hs.get(r, 12.8)
            pages = page_walk(hs, 321, breaks)
            pst = max((py for sr, py in pages if sr <= 72), default=0.0)
            rel_bottom = (tops[72] - pst) + (fc_bot - fc_top)
            avail = PAGE_CAP - 1.0
            REP["fc"]["rel_bottom_pt"] = round(rel_bottom, 1)
            if rel_bottom > avail:
                sc = avail / (fc_bot - fc_top)
                shapes = []
                for sh in ws.Shapes:
                    try:
                        if int(sh.Type) in (13, 10):
                            continue
                        if int(sh.TopLeftCell.Row) >= 72 and int(sh.BottomRightCell.Row) <= 321:
                            shapes.append(sh)
                    except Exception:
                        pass
                shapes.sort(key=lambda s: float(s.Top))
                for sh in shapes:
                    t = float(sh.Top)
                    sh.Top = fc_top + (t - fc_top) * sc
                    sh.Height = float(sh.Height) * sc
                    sh.Width = float(sh.Width) * sc
                REP["fc"]["scale"] = round(sc, 3)
                act(f"FC SCALE {sc:.3f}")
            else:
                REP["fc"]["scale"] = 1.0
            act(f"FC block={REP['fc']['block_pt']}pt rel_bottom={REP['fc'].get('rel_bottom_pt')}pt scale={REP['fc']['scale']}")

        # ---------- 7. 印刷設定 ----------
        ML, MR, MT, MB, MH, MF = 62.36 / 72, 36.85 / 72, 42.52 / 72, 56.69 / 72, 42.52 / 72, 28.35 / 72
        FOOT = ('&"ＭＳ ゴシック,標準"　　NR4030', '&"ＭＳ ゴシック,標準"様式 NR4030-0300-A3', '&"ＭＳ ゴシック,標準"日本光電')
        AREAS = {
            "表紙": "$A$1:$Y$36", "目次": "$A$1:$AZ$20", "用語": "$A$1:$AZ$32",
            "構成と管理情報": "$A$1:$AZ$21", "管理体制": "$A$1:$AZ$20",
            "相関図": "$A$1:$CG$45", "月次再起動": "$A$1:$AZ$93", "バックアップ": "$A$1:$AZ$190",
            "復旧": "$A$1:$AZ$14", "異常時の対応": "$A$1:$AZ$321",
            "チェックシート(月次・異常時)": "$A$1:$AZ$45", "会議課題一覧(一時)": "$A$1:$AZ$42",
            "付録 引用元と確認範囲": "$A$1:$AZ$28", "要確認事項一覧": "$A$1:$AZ$36",
            "7-5仮_サービス起動停止": "$A$1:$AZ$56",
        }
        for name, ws in wsmap.items():
            if name == "相関図_old":
                continue
            ps = ws.PageSetup
            ps.PrintArea = AREAS[name]
            if name != "相関図":
                ps.LeftMargin = ML; ps.RightMargin = MR
                ps.TopMargin = MT; ps.BottomMargin = MB
                ps.HeaderMargin = MH; ps.FooterMargin = MF
            if name == "付録 引用元と確認範囲" or name == "7-5仮_サービス起動停止":
                ps.LeftFooter, ps.CenterFooter, ps.RightFooter = FOOT
                ps.RightHeader = "\n&P"
                ps.PrintTitleRows = "$1:$3"
            if name == "表紙":
                ps.Zoom = False; ps.FitToPagesWide = 1; ps.FitToPagesTall = 1
            if name == "相関図":
                ps.Zoom = False; ps.FitToPagesWide = 1; ps.FitToPagesTall = 1
            if name == "チェックシート(月次・異常時)":
                ps.Zoom = False; ps.FitToPagesWide = 1; ps.FitToPagesTall = False
        act("PAGESETUP applied")

        # ---------- 8. 橙色走査(M4) ----------
        for name, ws in wsmap.items():
            if name == "相関図_old":
                continue
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
                        rr, gg, bb = int(fc_) & 255, (int(fc_) >> 8) & 255, (int(fc_) >> 16) & 255
                        if rr >= 200 and 90 <= gg <= 190 and bb <= 90:
                            cell.Font.Color = AKA
                            REP["orange"].append({"sheet": name, "addr": addr_str(cell), "type": "font", "from": int(fc_)})
                    ic_ = cell.Interior.Color
                    if isinstance(ic_, (int, float)) and int(ic_) != 16777215:
                        rr, gg, bb = int(ic_) & 255, (int(ic_) >> 8) & 255, (int(ic_) >> 16) & 255
                        if rr >= 200 and 90 <= gg <= 190 and bb <= 90:
                            REP["orange"].append({"sheet": name, "addr": addr_str(cell), "type": "fill", "from": int(ic_)})
        act(f"ORANGE scan: {len(REP['orange'])} hits")

        # ---------- 9. 保存 ----------
        wb.Save()
        act("SAVED (pass1)")

        # ---------- 10. 頁数計測と頁番号 ----------
        PdfReader = None
        try:
            from pypdf import PdfReader
        except Exception:
            try:
                from PyPDF2 import PdfReader
            except Exception:
                from pdfminer.pdfpage import PDFPage
                class PdfReader:
                    def __init__(self, p):
                        with open(p, "rb") as f:
                            self.n = len(list(PDFPage.get_pages(f)))
                    def __len__(self):
                        return self.n
        sheets = list(wb.Worksheets)
        counts = {}
        for sh in sheets:
            p = os.path.join(PAGES_DIR, f"{sh.Name}.pdf")
            sh.ExportAsFixedFormat(0, p, 0, True, False)  # 第6引数(From)を渡さない
            counts[sh.Name] = len(PdfReader(p).pages)
        REP["pages"] = counts
        act(f"PAGES: {counts}")
        page = 1
        for sh in sheets:
            n = counts[sh.Name]
            if sh.Name != "表紙":
                sh.PageSetup.FirstPageNumber = page
                REP["numbering"][sh.Name] = page
            page += n
        wb.Save()
        act("SAVED (pass2: numbering)")

        # ---------- 11. 冊PDF ----------
        cands = [f for f in os.listdir(VAULT_PDF_DIR)
                 if f.lower().endswith(".pdf") and "Pana-CIM管理手順書案" in f]
        if cands:
            cands.sort(key=lambda f: os.path.getmtime(os.path.join(VAULT_PDF_DIR, f)), reverse=True)
            book = os.path.join(VAULT_PDF_DIR, cands[0])
        else:
            book = os.path.join(VAULT_PDF_DIR, "Pana-CIM管理手順書案_未承認.pdf")
        REP["pdf"] = book
        wb.ExportAsFixedFormat(0, book, 0, True, False)
        act(f"BOOK PDF -> {book} ({len(PdfReader(book).pages)} pages)")

        wb.Close(SaveChanges=False)
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
        with open(REPORT, "w", encoding="utf-8") as f:
            json.dump(REP, f, ensure_ascii=False, indent=1)
        sys.exit(1)
