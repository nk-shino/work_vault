# -*- coding: utf-8 -*-
"""verify_lnb.py — LNB改修の包括検証。

1. バックアップ(改修前)と最終版の「値」差分 → 承認済みT文字列セル(19セル)以外の値変化は不許可
   (申し送り(認証情報)シートは read_only モードで一切アクセスしない)
2. 構造: 手動改ページ·FirstPageNumber·余白·印刷タイトル行·印刷範囲·列幅·結合·帯色 の Spot 検査
3. 冊PDF: 32頁·認証情報6頁(27-32)は頁数のみ確認(レンダ·テキスト抽出なし)
4. 認証情報の個別出力物が存在しないこと
"""
import hashlib
import json
import os
import re
import sys

import openpyxl
from pypdf import PdfReader

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XLSX = os.path.normpath(os.path.join(
    BASE, "..", "..", "OneDrive - NK", "ドキュメント", "Work_Vault",
    "10_業務全般", "PanaCIM_LNB", "01_成果物", "LNB管理手順書案_未承認.xlsx"))
BK = os.path.join(BASE, "backup_20261102", "LNB管理手順書案_未承認_改修前.xlsx")
VAULT_PDF = os.path.normpath(os.path.join(os.path.dirname(XLSX), "LNB管理手順書案_未承認.pdf"))
TMP = os.path.join(BASE, "scripts", "tmp_pages_lnb")
PROBE_SHA = "67b8cc54df23db2b41b8d27fb85246d4b77528f12b62eca489a740e8dba1ce03"

CRED = "申し送り(認証情報)"
ORDER17 = ["表紙", "目次", "用語", "構成と管理情報", "相関図", "相関図_old", "管理体制",
           "日次点検", "定期管理", "バックアップ", "復旧", "異常時の対応",
           "チェックシート(日次)", "チェックシート(月次・異常時)", "会議課題一覧(一時)",
           "要確認事項一覧", "引用と部品照合"]
DELETED = {"目次": range(23, 61), "日次点検": range(34, 122), "定期管理": range(16, 134),
           "バックアップ": range(56, 60), "復旧": range(14, 336), "異常時の対応": range(30, 145),
           "チェックシート(日次)": range(22, 172), "チェックシート(月次・異常時)": range(31, 79),
           "会議課題一覧(一時)": range(42, 529), "要確認事項一覧": range(48, 205),
           "引用と部品照合": range(27, 314)}
FIRST_PAGE = {"目次": 2, "用語": 3, "構成と管理情報": 5, "相関図": 9, "相関図_old": 10,
              "管理体制": 11, "日次点検": 12, "定期管理": 13, "バックアップ": 14,
              "復旧": 18, "異常時の対応": 19, "チェックシート(日次)": 20,
              "チェックシート(月次・異常時)": 21, "会議課題一覧(一時)": 22,
              "要確認事項一覧": 24, "引用と部品照合": 32}
AREAS = {"表紙": "$A$1:$Y$36", "目次": "$A$1:$AZ$22", "用語": "$A$1:$AZ$32",
         "構成と管理情報": "$A$1:$AZ$107", "管理体制": "$A$1:$AZ$19",
         "日次点検": "$A$1:$AZ$33", "定期管理": "$A$1:$AZ$15", "バックアップ": "$A$1:$AZ$55",
         "復旧": "$A$1:$AZ$14", "異常時の対応": "$A$1:$AZ$29",
         "チェックシート(日次)": "$A$1:$AZ$21", "チェックシート(月次・異常時)": "$A$1:$AZ$30",
         "会議課題一覧(一時)": "$A$1:$AZ$41", "要確認事項一覧": "$A$1:$AZ$47",
         "引用と部品照合": "$A$1:$AZ$26",
         "相関図": "$A$1:$AZ$60",           # 図形外接で拡張 (fix_figs)
         "相関図_old": "$A$1:$AY$58"}       # 元印刷範囲を保持 (改変なし)
# 承認済みT文字列セル (impl_lnb.py の text_edit 19件·C11は2回追記で1セル)
OK_CELLS = {"表紙.X1", "表紙.U12",
            "構成と管理情報.C8", "構成と管理情報.C9", "構成と管理情報.C14",
            "構成と管理情報.C17", "構成と管理情報.C55", "構成と管理情報.C104",
            "目次.A8", "目次.C8", "用語.C31", "定期管理.C9",
            "バックアップ.C15", "バックアップ.C16", "復旧.C13", "管理体制.C16",
            "異常時の対応.C19", "チェックシート(月次・異常時).C12", "引用と部品照合.C11"}

RES = {"sha": {}, "value_diff": {}, "structure": [], "book": {}, "fail": []}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sheet_values(path, name):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        ws = wb[name]
        out = {}
        for r, row in enumerate(ws.iter_rows(min_row=1, max_row=ws.max_row,
                                             max_col=52, values_only=True), start=1):
            for c, v in enumerate(row, start=1):
                if v is not None and str(v) != "":
                    out[(r, c)] = str(v)
        return out, ws.max_row
    finally:
        wb.close()


def approved_cells():
    return set(OK_CELLS)


def bgr_to_rgb(n):
    b = "%06X" % n
    return b[4:6] + b[2:4] + b[0:2]


def main():
    # --- 0. バックアップの改変チェック ---
    bk_sha = sha256(BK)
    RES["sha"]["backup"] = bk_sha
    if bk_sha != PROBE_SHA:
        RES["fail"].append(f"backup sha mismatch: {bk_sha}")
    RES["sha"]["final_xlsx"] = sha256(XLSX)

    # --- 1. 値差分検査 (認証情報シートには触れない) ---
    ok_cells = approved_cells()
    RES["value_diff"]["approved_cells"] = sorted(ok_cells)
    for name in ORDER17:
        pre, pre_max = sheet_values(BK, name)
        post, post_max = sheet_values(XLSX, name)
        dead = set(DELETED.get(name, []))
        kept = [r for r in range(1, pre_max + 1) if r not in dead]
        problems = []
        if len(kept) != post_max:
            problems.append(f"row count: kept {len(kept)} vs post {post_max}")
        post_map = {}
        for (r, c), v in post.items():
            post_map.setdefault(r, {})[c] = v
        pre_map = {}
        for (r, c), v in pre.items():
            pre_map.setdefault(r, {})[c] = v
        diffs = []
        for i, pr in enumerate(kept):
            pr_vals = pre_map.get(pr, {})
            po_vals = post_map.get(i + 1, {})
            for c in set(pr_vals) | set(po_vals):
                a, b = pr_vals.get(c, ""), po_vals.get(c, "")
                if a != b:
                    diffs.append(f"r{i+1}c{c}: [{a[:40]}]->[{b[:40]}]")
        # 差分セルの Sheet.ColRow 表記が承認集合に無ければ不許可
        unapproved = []
        for d in diffs:
            mm = re.match(r"r(\d+)c(\d+):", d)
            row_i, col = int(mm.group(1)), int(mm.group(2))
            # post の実行番号 → openpyxl 列名
            colname = openpyxl.utils.get_column_letter(col)
            key = f"{name}.{colname}{row_i}"
            if key not in OK_CELLS:
                unapproved.append(f"{key} {d}")
        RES["value_diff"][name] = {"diffs": diffs, "unapproved": unapproved}
        if unapproved:
            RES["fail"].append(f"{name}: unapproved value diffs: {unapproved[:5]}")

    # --- 2. 構造検査 (通常ロード·認証情報には未アクセス) ---
    wb = openpyxl.load_workbook(XLSX, data_only=False)
    try:
        for name in ORDER17:
            ws = wb[name]
            # 手動改ページ (OOXML brk.id は 0-based → +1 で 1-based 行番号)
            brks = set()
            try:
                for b in ws.row_breaks.brk:
                    if b.man:
                        brks.add(b.id + 1)
            except Exception:
                pass
            expect_brk = {31, 56, 81} if name == "構成と管理情報" else (
                {18, 26, 39} if name == "バックアップ" else set())
            if brks != expect_brk:
                RES["fail"].append(f"{name}: breaks {sorted(brks)} != {sorted(expect_brk)}")
            # FirstPageNumber
            fpn = ws.page_setup.firstPageNumber
            if name in FIRST_PAGE and str(fpn) not in ("None", str(FIRST_PAGE[name])):
                RES["fail"].append(f"{name}: FirstPageNumber {fpn} != {FIRST_PAGE[name]}")
            # 余白 (pt→in)。相関図は原形保持 (28.35pt/14.17pt のまま)
            pm = ws.page_margins
            if name == "相関図":
                for attr, pt in (("left", 28.35), ("right", 28.35), ("top", 28.35),
                                 ("bottom", 28.35), ("header", 14.17), ("footer", 14.17)):
                    v = getattr(pm, attr)
                    if v is not None and abs(float(v) - pt / 72.0) > 0.01:
                        RES["fail"].append(f"{name}: margin {attr} {v} != {pt/72:.4f}")
            else:
                for attr, pt in (("left", 62.36), ("right", 36.85), ("top", 42.52),
                                 ("bottom", 56.69), ("header", 42.52), ("footer", 28.35)):
                    v = getattr(pm, attr)
                    if v is not None and abs(float(v) - pt / 72.0) > 0.01:
                        RES["fail"].append(f"{name}: margin {attr} {v} != {pt/72:.4f}")
            # 印刷タイトル行
            tr = str(ws.print_title_rows or "")
            if name in ("構成と管理情報", "バックアップ", "用語", "日次点検", "定期管理",
                        "復旧", "異常時の対応", "チェックシート(日次)",
                        "チェックシート(月次・異常時)", "会議課題一覧(一時)",
                        "要確認事項一覧", "引用と部品照合", "管理体制"):
                if tr != "$1:$3":
                    RES["fail"].append(f"{name}: title rows {tr} != $1:$3")
            # 印刷範囲
            pa = str(ws.print_area or "").replace("'", "")
            if name in AREAS and pa.split("!")[-1] != AREAS[name]:
                RES["fail"].append(f"{name}: print area {pa} != {AREAS[name]}")
        # 列幅 Spot
        spots = [("目次", "B", 30.0), ("目次", "C", 5.0), ("構成と管理情報", "B", 1.0),
                 ("管理体制", "E", 7.0), ("チェックシート(月次・異常時)", "C", 30.0),
                 ("会議課題一覧(一時)", "A", 2.0)]
        for name, col, expect in spots:
            v = wb[name].column_dimensions[col].width
            # セッション文字幅→ファイル文字幅の系統差 +0.78 を許容
            if v is None or abs(float(v) - expect) > 0.85:
                RES["fail"].append(f"{name}.{col} width {v} != {expect}")
        # 結合 Spot
        mg = {str(r) for r in wb["相関図"].merged_cells.ranges}
        for need in ("C7:AZ7", "C8:AZ8", "C9:AZ9", "C10:AZ10"):
            if need not in mg:
                RES["fail"].append(f"相関図 merge {need} missing")
        mg2 = {str(r) for r in wb["目次"].merged_cells.ranges}
        for need in ("J10:AZ10", "J15:AZ15", "J17:AZ17", "J19:AZ19"):
            if need not in mg2:
                RES["fail"].append(f"目次 merge {need} missing")
        # 帯塗り (BGR→RGB) と朱文字 Spot
        sys.path.insert(0, os.path.join(BASE, "scripts"))
        from impl_lnb import SEC_FILL, AKA, CHAP_FILL  # noqa
        def fill_of(sn, cell):
            f = wb[sn][cell].fill
            rgb = f.fgColor.rgb if f and f.fgColor else None
            return str(rgb)[-6:] if rgb else None
        def font_of(sn, cell):
            c = wb[sn][cell].font.color
            return str(c.rgb)[-6:] if c and c.rgb else None
        def left_border_of(sn, cell):
            e = wb[sn][cell].border.left
            return str(e.color.rgb)[-6:] if e and e.color and e.color.rgb else None
        for sn, cell, expect in (("構成と管理情報", "A6", SEC_FILL),
                                 ("構成と管理情報", "A16", SEC_FILL),
                                 ("用語", "A6", CHAP_FILL),
                                 ("引用と部品照合", "A6", CHAP_FILL)):
            v = fill_of(sn, cell)
            if v != bgr_to_rgb(expect):
                RES["fail"].append(f"{sn}.{cell} fill {v} != {bgr_to_rgb(expect)}")
            RES["structure"].append(f"{sn}.{cell} fill={v}")
        # 朱 = aka行の左罫線色 (aka_line: XL_EDGE_LEFT + AKA)
        for sn, cell in (("構成と管理情報", "A17"), ("構成と管理情報", "A23"),
                         ("復旧", "A13"), ("チェックシート(月次・異常時)", "A12")):
            v = left_border_of(sn, cell)
            if v != bgr_to_rgb(AKA):
                RES["fail"].append(f"{sn}.{cell} left-border {v} != {bgr_to_rgb(AKA)}")
            RES["structure"].append(f"{sn}.{cell} left-border={v}")
    finally:
        wb.close()

    # --- 3. 冊PDF ---
    r = PdfReader(VAULT_PDF)
    n = len(r.pages)
    RES["book"]["pages"] = n
    if n != 32:
        RES["fail"].append(f"book pages {n} != 32")
    counts = {"表紙": 1, "目次": 1, "用語": 2, "構成と管理情報": 4, "相関図": 1, "相関図_old": 1,
              "管理体制": 1, "日次点検": 1, "定期管理": 1, "バックアップ": 4, "復旧": 1,
              "異常時の対応": 1, "チェックシート(日次)": 1, "チェックシート(月次・異常時)": 1,
              "会議課題一覧(一時)": 2, "要確認事項一覧": 2, "引用と部品照合": 1}
    off16 = sum(counts[k] for k in ORDER17[:16])
    cred = n - sum(counts.values())
    RES["book"]["cred"] = cred
    if cred != 6:
        RES["fail"].append(f"cred pages {cred} != 6")
    if off16 + cred + 1 != 32:
        RES["fail"].append(f"引用 first page {off16+cred+1} != 32")

    # --- 4. 認証情報の個別出力物が無いこと ---
    stray = [f for f in os.listdir(TMP) if ("申し送り" in f or "認証" in f)]
    if stray:
        RES["fail"].append(f"cred artifacts in tmp: {stray}")

    with open(os.path.join(BASE, "scripts", "verify_lnb_report.json"), "w", encoding="utf-8") as f:
        json.dump(RES, f, ensure_ascii=False, indent=1)
    if RES["fail"]:
        print("FAIL:")
        for x in RES["fail"]:
            print(" -", x)
        sys.exit(1)
    print("VERIFY OK")
    print("sha final:", RES["sha"]["final_xlsx"][:16], "…")
    print("book:", RES["book"])


if __name__ == "__main__":
    main()
