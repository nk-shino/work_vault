# -*- coding: utf-8 -*-
"""pdf_regen_lnb2.py — LNB冊PDFを確定手順(シート個別出力+cred頁スポット抽出)で再生成する。

fix35_rev3_lnb.py の Phase C1/C2 方式を忠実に再現する:
  - vault xlsx を2枚ローカルコピー(local / local_hide)
  - EXPORT_SHEETS(相関図_old·申し送り(認証情報)以外)を個別出力
    ReadOnly=True·ExportAsFixedFormat(0, p, 0, True, False)·3回リトライ
  - local_hide 上で相関図_old をメモリ上のみ非表示にして冊エクスポート(保存しない)
  - cred頁数 = 冊出力頁数 − 個別出力頁数合計、offset = cred以前の頁数合計
  - pypdf PdfWriter で ORDER_NEW 順に結合(cred頁のみ冊出力から抽出)
  - 検証: 頁数31·相関図_old漏出0·相関図①頁は旧PDFと完全一致·
          差分は相関図②③頁のみ
  - 合格なら vault へ反映し SHA を記録
"""
import os, sys, shutil, time, hashlib, traceback

V = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
XLSX = os.path.join(V, "LNB管理手順書案_未承認.xlsx")
PDFP = os.path.join(V, "LNB管理手順書案_未承認.pdf")
OLD_PDF = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\corr23\pdf_stash_20261105\LNB管理手順書案_未承認.pdf"
WORK = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\corr23\lnb_pdf_work2"
EXPECT_PAGES = 31

CRED = "申し送り(認証情報)"
OLD = "相関図_old"
ORDER_FULL = ["表紙", "目次", "用語", "構成と管理情報", "相関図①", "相関図②", "相関図③", OLD,
              "管理体制", "日次点検", "定期管理", "バックアップ", "復旧", "異常時の対応",
              "チェックシート(日次)", "チェックシート(月次・異常時)", "会議課題一覧(一時)",
              "要確認事項一覧", CRED, "認証情報一覧", "引用と部品照合"]
ORDER_NEW = [n for n in ORDER_FULL if n != OLD]
EXPORT_SHEETS = [n for n in ORDER_NEW if n != CRED]
OLD_MARK = "確定事項のみ記載"   # 相関図_old 固有の見出し語(漏出検出用)

def act(msg): print(msg, flush=True)

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def export_sheets(local_path, sheet_names, tag):
    import win32com.client as win32
    from pypdf import PdfReader
    app2 = win32.DispatchEx("Excel.Application")
    app2.Visible = False
    app2.DisplayAlerts = False
    try:
        wb2 = app2.Workbooks.Open(local_path, UpdateLinks=0, ReadOnly=True)
        counts = {}
        for name in sheet_names:
            p = os.path.join(WORK, f"{tag}_{name}.pdf")
            for attempt in range(3):
                try:
                    wb2.Worksheets(name).ExportAsFixedFormat(0, p, 0, True, False)
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    time.sleep(2.0)
            counts[name] = len(PdfReader(p).pages)
        wb2.Close(SaveChanges=False)
    finally:
        try:
            app2.Quit()
        except Exception:
            pass
    return counts

def export_book_hidden_old(local_hide_path, out_pdf):
    import win32com.client as win32
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    try:
        wb = app.Workbooks.Open(local_hide_path, UpdateLinks=0, ReadOnly=False)
        wb.Worksheets(OLD).Visible = 0  # xlSheetHidden(このコピーは保存しない)
        wb.ExportAsFixedFormat(0, out_pdf, 0, True, False)
        wb.Close(SaveChanges=False)
    finally:
        try:
            app.Quit()
        except Exception:
            pass

def page_texts(path):
    import pymupdf as fitz
    doc = fitz.open(path)
    out = [pg.get_text() for pg in doc]
    doc.close()
    return out

def squash(s): return "".join(s.split())

def locate_heading(texts, key):
    return [i for i, t in enumerate(texts) if key in squash(t)]

def main():
    os.makedirs(WORK, exist_ok=True)
    for f in os.listdir(WORK):
        os.remove(os.path.join(WORK, f))
    import win32com.client as win32  # noqa
    from pypdf import PdfReader, PdfWriter

    act(f"xlsx sha (post-fix): {sha256(XLSX)[:16]}")
    local = os.path.join(WORK, "_lnb.xlsx")
    local_hide = os.path.join(WORK, "_lnb_hide.xlsx")
    shutil.copy2(XLSX, local)
    shutil.copy2(XLSX, local_hide)

    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    try:
        wb = app.Workbooks.Open(local, UpdateLinks=0, ReadOnly=True)
        names = [wb.Sheets(i).Name for i in range(1, wb.Sheets.Count + 1)]
        wb.Close(SaveChanges=False)
    finally:
        try:
            app.Quit()
        except Exception:
            pass
    assert names == ORDER_FULL, f"unexpected sheet order: {names}"
    act(f"sheets({len(names)}): ok")

    counts = export_sheets(local, EXPORT_SHEETS, tag="s")
    act(f"sheet pages: {counts}")
    book_full = os.path.join(WORK, "BOOK_hiddenold.pdf")
    export_book_hidden_old(local_hide, book_full)
    n_full = len(PdfReader(book_full).pages)
    cred_pages = n_full - sum(counts.values())
    offset = sum(counts[n] for n in ORDER_NEW[:ORDER_NEW.index(CRED)])
    act(f"book(hid old) {n_full}p, cred pages={cred_pages} at {offset+1}")
    assert 1 <= cred_pages <= 3, f"unexpected cred pages: {cred_pages}"

    writer = PdfWriter()
    for name in ORDER_NEW:
        if name == CRED:
            for i in range(offset, offset + cred_pages):
                writer.add_page(PdfReader(book_full).pages[i])
        else:
            for pg in PdfReader(os.path.join(WORK, f"s_{name}.pdf")).pages:
                writer.add_page(pg)
    book_local = os.path.join(WORK, "BOOK_lnb.pdf")
    with open(book_local, "wb") as f:
        writer.write(f)
    total = len(PdfReader(book_local).pages)
    assert total == EXPECT_PAGES, f"booklet pages {total} != {EXPECT_PAGES}"

    new_t = page_texts(book_local)
    sq_new = [squash(t) for t in new_t]
    leak = [i + 1 for i, t in enumerate(sq_new) if OLD_MARK in t]
    assert not leak, f"相関図_old leak at pages: {leak}"
    act("相関図_old leak: 0")

    old_t = page_texts(OLD_PDF)
    sq_old = [squash(t) for t in old_t]
    assert len(sq_old) == total, f"old pdf pages {len(sq_old)} != {total}"
    p1 = locate_heading(new_t, "2-3相関図①")
    p2 = locate_heading(new_t, "2-4相関図②")
    p3 = locate_heading(new_t, "2-5相関図③")
    assert p2 and p3, f"heading locate failed {p1} {p2} {p3}"
    p3 = max(p3)   # 末尾の節ほど後ろの頁
    cand2 = [c for c in p2 if c == p3 - 1] or [max(c for c in p2 if c < p3)]
    p2 = cand2[0]
    cand1 = [c for c in p1 if c == p2 - 1] or [max(c for c in p1 if c < p2)]
    p1 = cand1[0]
    act(f"pages: 相関図①={p1+1} ②={p2+1} ③={p3+1}")
    diff_pages = [i + 1 for i in range(total) if sq_old[i] != sq_new[i]]
    allowed = {p2 + 1, p3 + 1}
    bad = [d for d in diff_pages if d not in allowed]
    act(f"diff pages: {diff_pages} (allowed: {sorted(allowed)})")
    assert not bad, f"UNEXPECTED diff pages: {bad}"
    if p1 + 1 in diff_pages:
        raise AssertionError(f"相関図① page {p1+1} must be identical to old")
    act("相関図① page: identical (ok)")

    shutil.copy2(book_local, PDFP)
    act(f"DONE xlsx {sha256(XLSX)[:16]} pdf {sha256(PDFP)[:16]} ({total}p)")
    shutil.rmtree(WORK, ignore_errors=True)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
