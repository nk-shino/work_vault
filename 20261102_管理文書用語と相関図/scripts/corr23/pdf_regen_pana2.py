# -*- coding: utf-8 -*-
"""pdf_regen_pana2.py — Pana冊PDFを確定手順(シート個別出力+pypdf結合)で再生成する。

fix34_g10_rev2_pana.py の export_all 方式を忠実に再現する:
  - vault xlsx をローカルコピーし ReadOnly=True で開く
  - 全シートをタブ順に ExportAsFixedFormat(0, p, 0, True, False) (3回リトライ)
  - 頁数合計が49であることを確認
  - pypdf PdfWriter でタブ順に結合
  - 旧PDF(pdf_stash_20261105)と頁別テキスト照合:
      相関図①頁は完全一致、相関図②③頁のみ差分許容、他は全頁一致
  - 合格なら vault へ反映し SHA を記録
"""
import os, sys, shutil, time, hashlib, traceback

V = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
XLSX = os.path.join(V, "Pana-CIM管理手順書案_未承認.xlsx")
PDFP = os.path.join(V, "Pana-CIM管理手順書案_未承認.pdf")
OLD_PDF = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\corr23\pdf_stash_20261105\Pana-CIM管理手順書案_未承認.pdf"
WORK = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\corr23\pana_pdf_work2"
EXPECT_PAGES = 49

def act(msg): print(msg, flush=True)

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()

def export_all(local_path, sheet_names, tag):
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

def page_texts(path):
    import pymupdf as fitz
    doc = fitz.open(path)
    out = [pg.get_text() for pg in doc]
    doc.close()
    return out

def squash(s): return "".join(s.split())

def locate_heading(path, key):
    """見出しブロック(先頭が鍵語で始まるブロック)がある頁を返す(目次·本文中の言及は除外)。"""
    import pymupdf as fitz
    doc = fitz.open(path)
    hits = []
    for i, pg in enumerate(doc):
        for b in pg.get_text("blocks"):
            if squash(b[4]).startswith(key):
                hits.append(i)
                break
    doc.close()
    return hits

def main():
    os.makedirs(WORK, exist_ok=True)
    for f in os.listdir(WORK):
        os.remove(os.path.join(WORK, f))
    import win32com.client as win32  # noqa
    from pypdf import PdfReader, PdfWriter

    act(f"xlsx sha (post-fix): {sha256(XLSX)[:16]}")
    local = os.path.join(WORK, "_pana.xlsx")
    shutil.copy2(XLSX, local)

    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    try:
        wb = app.Workbooks.Open(local, UpdateLinks=0, ReadOnly=True)
        sheet_names = [wb.Sheets(i).Name for i in range(1, wb.Sheets.Count + 1)]
        wb.Close(SaveChanges=False)
    finally:
        try:
            app.Quit()
        except Exception:
            pass
    act(f"sheets({len(sheet_names)}): {sheet_names}")

    counts = export_all(local, sheet_names, tag="s")
    act(f"sheet pages: {counts}")
    total = sum(counts.values())
    assert total == EXPECT_PAGES, f"pages {total} != {EXPECT_PAGES}"

    writer = PdfWriter()
    for name in sheet_names:
        for pg in PdfReader(os.path.join(WORK, f"s_{name}.pdf")).pages:
            writer.add_page(pg)
    book_local = os.path.join(WORK, "BOOK_pana.pdf")
    with open(book_local, "wb") as f:
        writer.write(f)
    assert len(PdfReader(book_local).pages) == total, "booklet page count mismatch"

    old_t = page_texts(OLD_PDF)
    new_t = page_texts(book_local)
    assert len(old_t) == len(new_t) == total, f"page count old/new {len(old_t)}/{len(new_t)}"
    sq_old = [squash(t) for t in old_t]
    sq_new = [squash(t) for t in new_t]
    p1 = locate_heading(book_local, "2-2相関図①")
    p2 = locate_heading(book_local, "2-3相関図②")
    p3 = locate_heading(book_local, "2-4相関図③")
    assert p2 and p3, f"heading locate failed {p1} {p2} {p3}"
    p3 = max(p3)   # 末尾の節ほど後ろの頁
    cand2 = [c for c in p2 if c == p3 - 1] or [max(c for c in p2 if c < p3)]
    p2 = cand2[0]
    cand1 = [c for c in p1 if c == p2 - 1] or [max(c for c in p1 if c < p2)]
    p1 = cand1[0]
    act(f"pages: 相関図①={p1+1} ②={p2+1} ③={p3+1}")
    diff_pages = [i + 1 for i in range(total) if sq_old[i] != sq_new[i]]
    allowed = {p1 + 1, p2 + 1, p3 + 1}
    bad = [d for d in diff_pages if d not in allowed]
    act(f"diff pages: {diff_pages} (allowed: {sorted(allowed)})")
    assert not bad, f"UNEXPECTED diff pages: {bad}"
    if p1 + 1 not in diff_pages:
        act("相関図① page: identical (ok)")
    else:
        raise AssertionError(f"相関図① page {p1+1} must be identical to old (per-sheet export reproduces ground truth)")
    act(f"OK: only 相関図②③ pages differ ({[d for d in diff_pages]})")

    shutil.copy2(book_local, PDFP)
    act(f"DONE xlsx {sha256(XLSX)[:16]} pdf {sha256(PDFP)[:16]} ({total}p)")
    shutil.rmtree(WORK, ignore_errors=True)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
