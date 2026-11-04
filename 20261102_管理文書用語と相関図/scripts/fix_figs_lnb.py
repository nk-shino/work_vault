# -*- coding: utf-8 -*-
"""fix_figs_lnb.py — 構成と管理情報の図1〜図3のゴースト(外接検定違反)解消。

確立されたモデル (実測による):
- 印刷タイトル行 = $1:$3。画像の印刷位置 = 42.52 + (img_top − 頁先頭行Top)×z + H_t×z
- 頁のウィンドウ (浮動図形の描画判定) = [頁先頭行Top, 頁先頭行Top + 742.7/z] (シートpt)
- 行の収容上限 U = W − H_t
- 外接検定 (Pana基準): 全画像 bbox bottom ≤ 786pt (印刷座標)

方針 (構成と管理情報のみ·他シートは適合済み):
- 図1: Top を δ1 = W−S1+2 下げ、p1ウィンドウから完全クリア (ゴースト消滅)
- 図2: Top を δ2 = W−S2+2 下げ、p2ウィンドウから完全クリア (ゴースト消滅)
- 図3: Top を δ3 = 30 下げ、p3へのゴーストを頁内完全内包(不可視·検定適合)に留める
        (完全クリアには δ3≈357 が必要だが p4 が 2-3 節ブロックと共に溢れるため不採用)
- 帯行高を再設定し 図bottom ≤ キャプション行Top−2 と各頁スパン ≤ U を保証
- 改ページ(31/56/81)·採番·余白·他シートには触れない
"""
import io
import json
import os
import traceback

import pymupdf
import win32com.client as win32
from pypdf import PdfReader, PdfWriter

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XLSX = os.path.normpath(os.path.join(
    BASE, "..", "..", "OneDrive - NK", "ドキュメント", "Work_Vault",
    "10_業務全般", "PanaCIM_LNB", "01_成果物", "LNB管理手順書案_未承認.xlsx"))
VAULT_PDF = os.path.normpath(os.path.join(os.path.dirname(XLSX), "LNB管理手順書案_未承認.pdf"))
TMP = os.path.join(BASE, "scripts", "tmp_pages_lnb")

SHEET = "構成と管理情報"
ORDER17 = ["表紙", "目次", "用語", "構成と管理情報", "相関図", "相関図_old", "管理体制",
           "日次点検", "定期管理", "バックアップ", "復旧", "異常時の対応",
           "チェックシート(日次)", "チェックシート(月次・異常時)", "会議課題一覧(一時)",
           "要確認事項一覧", "引用と部品照合"]
EXPECT_COUNTS = {"表紙": 1, "目次": 1, "用語": 2, "構成と管理情報": 4, "相関図": 1,
                 "相関図_old": 1, "管理体制": 1, "日次点検": 1, "定期管理": 1,
                 "バックアップ": 4, "復旧": 1, "異常時の対応": 1, "チェックシート(日次)": 1,
                 "チェックシート(月次・異常時)": 1, "会議課題一覧(一時)": 2,
                 "要確認事項一覧": 2, "引用と部品照合": 1}
CANARY = 786.0
STYLE_BOTTOM = 114.0

REP = {"fig": {}, "verify": {}, "counts": {}, "book": {}, "errors": []}


def rows_sum(ws, r1, r2):
    return sum(float(ws.Rows(r).RowHeight) for r in range(r1, r2 + 1))


def find_pic(ws, tl_row):
    for sh in ws.Shapes:
        if sh.Type == 13 and sh.TopLeftCell.Row == tl_row:
            return sh
    raise RuntimeError(f"picture with TL row {tl_row} not found")


def set_band(ws, r1, r2, total):
    h = round(total / (r2 - r1 + 1), 2)
    for r in range(r1, r2 + 1):
        ws.Rows(r).RowHeight = h
    return h


def export_sheet(book, name, path):
    book.Worksheets(name).ExportAsFixedFormat(0, path, 0, True, False)


def main():
    # ================= Phase A: 図形修正 (COM) =================
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    wb = None
    try:
        wb = app.Workbooks.Open(XLSX, UpdateLinks=0, ReadOnly=False)
        app.Calculation = -4135
        ws = wb.Worksheets(SHEET)
        z = float(ws.PageSetup.Zoom) / 100.0
        W = 742.7 / z
        Ht = rows_sum(ws, 1, 3)
        U = W - Ht
        REP["fig"]["zoom"] = z
        REP["fig"]["W"] = round(W, 1)
        REP["fig"]["Ht"] = round(Ht, 1)
        REP["fig"]["U"] = round(U, 1)

        S1 = rows_sum(ws, 1, 30)
        top31 = float(ws.Range("A31").Top)
        f1 = find_pic(ws, 31)
        f2 = find_pic(ws, 56)
        f3 = find_pic(ws, 81)
        h1, h2, h3 = float(f1.Height), float(f2.Height), float(f3.Height)
        top56 = float(ws.Range("A56").Top)
        top81 = float(ws.Range("A81").Top)
        REP["fig"]["pre"] = {
            "S1": round(S1, 1), "top31": round(top31, 1),
            "f1_top": round(float(f1.Top), 1), "h1": round(h1, 1),
            "f2_top": round(float(f2.Top), 1), "h2": round(h2, 1),
            "f3_top": round(float(f3.Top), 1), "h3": round(h3, 1),
        }

        # --- 図1: 帯行高 → p1ウィンドウ完全クリア ---
        d1 = round(W - S1 + 2.0, 2)
        rh1 = set_band(ws, 31, 54, d1 + h1 + 4)
        S2 = rows_sum(ws, 31, 55)

        # --- 図2: 帯行高 → p2ウィンドウ完全クリア ---
        top56b = float(ws.Range("A56").Top)
        d2 = round(W - S2 + 2.0, 2)
        if d2 < 30:
            d2 = 30.0
        rh2 = set_band(ws, 56, 79, d2 + h2 + 4)
        S3 = rows_sum(ws, 56, 80)

        # --- 図3: 帯行高 → 頁内上部+前頁ゴースト完全内包 ---
        top81b = float(ws.Range("A81").Top)
        d3 = 30.0
        ghost_bottom = 42.52 + (top81b + d3 - top56b) * z + h3 * z
        while ghost_bottom > 784.0 and d3 > 0:
            d3 = round(d3 - 5.0, 2)
            ghost_bottom = 42.52 + (top81b + d3 - top56b) * z + h3 * z
        rh3 = set_band(ws, 81, 100, d3 + h3 + 6)
        S4 = rows_sum(ws, 81, 107)

        assert S2 <= U, f"p2 span {S2:.1f} > U {U:.1f}"
        assert S3 <= U, f"p3 span {S3:.1f} > U {U:.1f}"
        assert S4 <= U, f"p4 span {S4:.1f} > U {U:.1f}"
        br = sorted(int(b.Location.Row) for b in ws.HPageBreaks if b.Type == -4135)
        assert br == [31, 56, 81], f"breaks changed: {br}"

        # --- 図形配置 (行高変更後に最終確定·stretch戻し) ---
        f1.Top = top31 + d1
        f1.Height = h1
        f2.Top = top56b + d2
        f2.Height = h2
        f3.Top = top81b + d3
        f3.Height = h3

        REP["fig"]["post"] = {
            "d1": d1, "d2": d2, "d3": d3,
            "rh1": rh1, "rh2": rh2, "rh3": rh3,
            "S1": round(S1, 1), "S2": round(S2, 1), "S3": round(S3, 1), "S4": round(S4, 1),
            "f1_top": round(top31 + d1, 1), "f2_top": round(top56b + d2, 1),
            "f3_top": round(top81b + d3, 1),
            "ghost3_bottom_pt": round(ghost_bottom, 1),
        }
        wb.Save()
        print("[fix] figs applied + saved")

        # ================= Phase B: 17シート再出力 + 検定 =================
        os.makedirs(TMP, exist_ok=True)
        for name in ORDER17:
            export_sheet(wb, name, os.path.join(TMP, f"{name}.pdf"))
        wb.Close(SaveChanges=False)
    except Exception:
        REP["errors"].append("phase A/B failed")
        REP["errors"].append(traceback.format_exc())
        if wb is not None:
            try:
                wb.Close(SaveChanges=False)
            except Exception:
                pass
        with open(os.path.join(BASE, "scripts", "fix_figs_report.json"), "w", encoding="utf-8") as f:
            json.dump(REP, f, ensure_ascii=False, indent=1)
        raise
    finally:
        app.Quit()

    counts = {}
    violations = []
    for name in ORDER17:
        d = pymupdf.open(os.path.join(TMP, f"{name}.pdf"))
        counts[name] = d.page_count
        for pi in range(d.page_count):
            for info in d[pi].get_image_info():
                bb = info["bbox"]
                if bb[3] > CANARY:
                    violations.append([name, pi + 1, "canary", round(bb[3], 1)])
                if bb[1] < STYLE_BOTTOM:
                    violations.append([name, pi + 1, "style-overlap", round(bb[1], 1)])
        d.close()
    REP["counts"] = counts
    REP["verify"]["violations"] = violations
    mismatch = {k: [counts.get(k), EXPECT_COUNTS.get(k)] for k in set(counts) | set(EXPECT_COUNTS)
                if counts.get(k) != EXPECT_COUNTS.get(k)}
    if mismatch:
        REP["verify"]["count_mismatch"] = mismatch
    if violations or mismatch:
        with open(os.path.join(BASE, "scripts", "fix_figs_report.json"), "w", encoding="utf-8") as f:
            json.dump(REP, f, ensure_ascii=False, indent=1)
        raise RuntimeError(f"verify failed: {violations} mismatch={mismatch}")
    print("[fix] 17-sheet verify OK")

    # ================= Phase C: 冊出力→認証情報頁実測→結合→VAULT_PDF =================
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    wb = None
    book_path = os.path.join(TMP, "_book_tmp_lnb.pdf")
    try:
        wb = app.Workbooks.Open(XLSX, UpdateLinks=0, ReadOnly=False)
        app.Calculation = -4135
        wb.ExportAsFixedFormat(0, book_path, 0, True, False)
        book_pages = len(PdfReader(book_path).pages)
        sum17 = sum(counts.values())
        cred = book_pages - sum17
        assert cred >= 1, f"cred pages {cred}"
        offset = sum(counts[n] for n in ORDER17[:16])
        wq = wb.Worksheets("引用と部品照合")
        wq.PageSetup.FirstPageNumber = offset + cred + 1
        wb.Save()
        export_sheet(wb, "引用と部品照合", os.path.join(TMP, "引用と部品照合.pdf"))
        wb.Close(SaveChanges=False)
    except Exception:
        REP["errors"].append("phase C export failed")
        REP["errors"].append(traceback.format_exc())
        if wb is not None:
            try:
                wb.Close(SaveChanges=False)
            except Exception:
                pass
        with open(os.path.join(BASE, "scripts", "fix_figs_report.json"), "w", encoding="utf-8") as f:
            json.dump(REP, f, ensure_ascii=False, indent=1)
        raise
    finally:
        app.Quit()

    w = PdfWriter()
    for name in ORDER17[:16]:
        for p in PdfReader(os.path.join(TMP, f"{name}.pdf")).pages:
            w.add_page(p)
    rb = PdfReader(book_path)
    for i in range(offset, offset + cred):
        w.add_page(rb.pages[i])
    for p in PdfReader(os.path.join(TMP, "引用と部品照合.pdf")).pages:
        w.add_page(p)
    total = len(w.pages)
    assert total == book_pages, f"total {total} != book {book_pages}"
    tmp_out = VAULT_PDF + ".tmp"
    with open(tmp_out, "wb") as f:
        w.write(f)
    os.replace(tmp_out, VAULT_PDF)
    os.remove(book_path)
    REP["book"] = {"book_pages": book_pages, "cred": cred, "offset": offset, "total": total}
    print(f"[fix] merged {total}p (cred={cred}) -> vault")

    with open(os.path.join(BASE, "scripts", "fix_figs_report.json"), "w", encoding="utf-8") as f:
        json.dump(REP, f, ensure_ascii=False, indent=1)
    print("[fix] OK")


if __name__ == "__main__":
    main()
