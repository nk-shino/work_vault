# -*- coding: utf-8 -*-
"""fix_boxes_lnb.py v3 — 様式ラベル箱の修復 + 幅方向フィット。

確定した実構造: W2:AB2=管理番号(ラベル)·W3:AB3=工程番号(ラベル)·
AU2:AV2=頁(ラベル)·AC2:AT2/AW2:AZ2/G3:V3/AC3:AZ3=値箱(空または内容)。
v1(全幅復元)·v2(値箱も増幅)は破棄。v3:
  1. §2の実装幅を6シートへ再適用 (v2の過剰幅を解消)
  2. ラベル3結合の構成列のみ文字幅を確保 (W..AB=1.0/列=72px, AU..AV=0.72/列=20px)
  3. 6シートに幅方向フィット (FitToPagesWide=1·Tall=0) を設定
     (均等縮小のため行折返し·行高·結合に影響しない)
  4. 保存→17シート再出力→頁数検定→冊32p→vault更新→openpyxl検定
"""
import json
import os
import re
import shutil

import openpyxl
import openpyxl.utils as u
import pypdf

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XLSX = os.path.normpath(os.path.join(
    BASE, "..", "..", "OneDrive - NK", "ドキュメント", "Work_Vault",
    "10_業務全般", "PanaCIM_LNB", "01_成果物", "LNB管理手順書案_未承認.xlsx"))
VAULT_PDF = os.path.normpath(os.path.join(
    BASE, "..", "..", "OneDrive - NK", "ドキュメント", "Work_Vault",
    "10_業務全般", "PanaCIM_LNB", "01_成果物", "LNB管理手順書案_未承認.pdf"))
TMP = os.path.join(BASE, "scripts", "tmp_pages_lnb")
os.makedirs(TMP, exist_ok=True)

ORDER17 = ["表紙", "目次", "用語", "構成と管理情報", "相関図", "相関図_old", "管理体制",
           "日次点検", "定期管理", "バックアップ", "復旧", "異常時の対応",
           "チェックシート(日次)", "チェックシート(月次・異常時)", "会議課題一覧(一時)",
           "要確認事項一覧", "引用と部品照合"]
SIX = ["目次", "管理体制", "チェックシート(日次)", "チェックシート(月次・異常時)",
       "会議課題一覧(一時)", "要確認事項一覧"]
EXPECT_PAGES = {"目次": 1, "管理体制": 1, "チェックシート(日次)": 1,
                "チェックシート(月次・異常時)": 1, "会議課題一覧(一時)": 2,
                "要確認事項一覧": 2}
IMPL_W = {
    "目次": {"A": 4, "B": 30, "C": 5, "D:I": 0.4, "J:AY": 0.3, "AZ": 2.22},
    "管理体制": {"A": 3, "B": 1, "C": 3, "D": 1, "E": 7, "F:AY": 0.85, "AZ": 2.22},
    "チェックシート(日次)": {"A": 7, "B": 0.5, "C": 8, "D": 0.5, "E": 8, "F": 0.5,
                      "G": 8, "H": 0.5, "I": 12, "J": 0.5, "K": 9, "L": 0.5,
                      "M": 9, "N:AY": 0.3, "AZ": 2.22},
    "チェックシート(月次・異常時)": {"A": 7, "B": 0.5, "C": 30, "D": 0.5, "E": 9, "F": 0.5,
                        "G": 8, "H": 0.5, "I": 10, "J": 0.5, "K": 9, "L": 0.5,
                        "M": 6, "N:AY": 0.3, "AZ": 2.22},
    "会議課題一覧(一時)": {"A": 2, "B": 0.5, "C": 8, "D": 0.5, "E": 8, "F": 0.5,
                    "G": 10, "H:AY": 0.6, "AZ": 2.22},
    "要確認事項一覧": {"A": 4, "B": 1, "C": 10, "D": 1, "E": 12, "F": 1, "G": 10,
                  "H:AY": 0.5, "AZ": 2.22},
}
LABEL_COLS = {"W2:AB2": 1.0, "AU2:AV2": 0.72}  # ラベル結合ごとの1列あたり文字幅


def fpx(w):
    return int(((256 * w + 18) / 256) * 7) + 5


def span(rng):
    a, b = rng.split(":")
    return (u.column_index_from_string(re.match(r"([A-Z]+)", a).group(1)),
            u.column_index_from_string(re.match(r"([A-Z]+)", b).group(1)))


def label_px(path, name):
    wb = openpyxl.load_workbook(path, read_only=False)
    try:
        ws = wb[name]
        wm = {}
        for cd in ws.column_dimensions.values():
            try:
                lo, hi, w = int(cd.min), int(cd.max), float(cd.width)
            except (TypeError, ValueError):
                continue
            if w:
                for c in range(lo, hi + 1):
                    wm[c] = w
        out = {}
        for rng in ("W2:AB2", "AU2:AV2"):
            lo, hi = span(rng)
            out[rng] = sum(fpx(wm.get(c, 8.38)) for c in range(lo, hi + 1))
        return out
    finally:
        wb.close()


# ---- Phase B: COM 適用·保存·出力 ----
import win32com.client

xl = win32com.client.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
xl.ScreenUpdating = False
book_pdf = os.path.join(TMP, "_book_full.pdf")
try:
    wbx = xl.Workbooks.Open(XLSX, UpdateLinks=0)
    for name in SIX:
        ws = wbx.Worksheets(name)
        # 1. §2幅を再適用 (v2の過剰幅を解消)
        for c in range(1, 53):
            ws.Columns(c).ColumnWidth = 8.38  # 既定 (下で上書き)
        for key, val in IMPL_W[name].items():
            lo, hi = span(key if ":" in key else f"{key}:{key}")
            for c in range(lo, hi + 1):
                ws.Columns(c).ColumnWidth = float(val)
        # 2. ラベル結合の列幅
        for rng, w in LABEL_COLS.items():
            lo, hi = span(rng)
            for c in range(lo, hi + 1):
                ws.Columns(c).ColumnWidth = float(w)
        # 3. 幅方向フィット
        ps = ws.PageSetup
        ps.Zoom = False
        ps.FitToPagesWide = 1
        ps.FitToPagesTall = False
    wbx.Save()
    for name in ORDER17:
        ws = wbx.Worksheets(name)
        ws.Activate()
        p = os.path.join(TMP, name + ".pdf")
        if os.path.exists(p):
            os.remove(p)
        ws.ExportAsFixedFormat(0, p)
    if os.path.exists(book_pdf):
        os.remove(book_pdf)
    wbx.ExportAsFixedFormat(0, book_pdf)
    wbx.Close(SaveChanges=False)
finally:
    xl.ScreenUpdating = True
    xl.Quit

# ---- Phase C: 頁数検定·統合·vault更新 ----
report = {"labels": {}, "pages": {}, "book": {}}
for name in SIX:
    n = len(pypdf.PdfReader(os.path.join(TMP, name + ".pdf")).pages)
    report["pages"][name] = n
    assert n == EXPECT_PAGES[name], f"{name}: {n}p != {EXPECT_PAGES[name]}p"

rb = pypdf.PdfReader(book_pdf)
nb = len(rb.pages)
assert nb == 32, f"book {nb}p != 32p"
report["book"]["pages"] = nb
writer = pypdf.PdfWriter()
for i in range(nb):
    writer.add_page(rb.pages[i])
out_pdf = os.path.join(TMP, "_merged_vault.pdf")
with open(out_pdf, "wb") as f:
    writer.write(f)
shutil.copyfile(out_pdf, VAULT_PDF)
report["book"]["vault_pdf_updated"] = True

# ---- Phase D: openpyxl 検定 (ラベル結合が文字幅を確保できたか) ----
ok_all = True
for name in SIX:
    got = label_px(XLSX, name)
    bad = {}
    if got["W2:AB2"] < 70:
        bad["W2:AB2"] = got["W2:AB2"]
    if got["AU2:AV2"] < 18:
        bad["AU2:AV2"] = got["AU2:AV2"]
    report["labels"][name] = {"px": got, "ok": not bad, "bad": bad}
    if bad:
        ok_all = False

report["all_labels_ok"] = ok_all
with open(os.path.join(BASE, "scripts", "fix_boxes_report.json"), "w",
          encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=1)
print(json.dumps(report, ensure_ascii=False, indent=1))
assert ok_all, "label restore failed"
print("FIX_BOXES_V3 OK")
