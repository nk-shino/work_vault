# -*- coding: utf-8 -*-
"""pdf_regen_pana3.py — Pana冊PDFを再生成する(相関図_oldをPDFから除外する版)。

利用者決定(2026-11-05)により pana冊からも相関図_oldを除外する(LNB方式·xlsx不変):
  - vault xlsx を local / local_hide の2枚へローカルコピー(派生物はTEMPのみ)
  - 相関図_old 以外の全シートをタブ順に個別出力 ExportAsFixedFormat(0, p, 0, True, False)
  - 相関図_old も個別出力し、旧PDF内での所在を頁テキスト一致で特定(49→48頁の対応表)
  - pypdf で 相関図_old を除くタブ順に結合(合計41頁)
  - 照合: 旧PDFとの頁対応マッピングで「相関図①頁は完全一致·相関図②③頁のみ差分許容·他は全頁一致」
  - マーカー: ②③の5ラベルの末尾文字列が抽出テキストに存在すること(クリップ解消の実証)
  - 合格なら vault へ反映し SHA を記録。不合格は vault 書き込み前に中断
"""
import os, sys, shutil, time, hashlib, traceback

V = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
XLSX = os.path.join(V, "Pana-CIM管理手順書案_未承認.xlsx")
PDFP = os.path.join(V, "Pana-CIM管理手順書案_未承認.pdf")
OLD_PDF = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\corr23\pdf_stash_20261105\Pana-CIM管理手順書案_未承認.pdf"
WORK = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\corr23\pana_pdf_work3"
EXPECT_PAGES = 48
OLD = "相関図_old"

MARK2 = ["PANACIM_****_FULbak", "外部メディア保存は-28-", "対応表は本文で引用予定(要確認)",
         "【保存領域】DB完全バックアップ", "【外部】外部I/F出力", "EE17", "EE18"]
MARK3 = ["断定しない(要確認#1)", "同一性は要確認", "接続エッジは推定",
         "【設備】LNB(FAパソコン)", "【端末】LWS(LNB操作画面・ブラウザ)",
         "【設備】アンドン(ライン状態表示装置)", "EE05", "EE06", "EE10", "EE03", "EE04"]

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

def page_texts(path):
    import pymupdf as fitz
    doc = fitz.open(path)
    out = [pg.get_text() for pg in doc]
    doc.close()
    return out

def squash(s): return "".join(s.split())

def canon_lines(path, idx):
    """頁のテキスト行を(座標ソート後)正規化して返す。ストリーム順の差異に依存しない。"""
    import pymupdf as fitz
    doc = fitz.open(path)
    pg = doc[idx]
    rows = []
    for b in pg.get_text("dict")["blocks"]:
        if b["type"] != 0:
            continue
        for l in b["lines"]:
            txt = "".join(s["text"] for s in l["spans"])
            if txt.strip():
                rows.append((round(l["bbox"][1], 1), round(l["bbox"][0], 1), squash(txt)))
    doc.close()
    rows.sort()
    return rows

def locate_heading(path, key):
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
    assert OLD in sheet_names, f"{OLD} not found in tabs"

    export_names = [n for n in sheet_names if n != OLD]
    counts = export_sheets(local, export_names, tag="s")
    act(f"sheet pages: {counts}")
    total = sum(counts.values())
    assert total == EXPECT_PAGES, f"pages {total} != {EXPECT_PAGES}"

    counts_old = export_sheets(local, [OLD], tag="o")
    act(f"{OLD} pages: {counts_old}")

    writer = PdfWriter()
    for name in sheet_names:
        if name == OLD:
            continue
        for pg in PdfReader(os.path.join(WORK, f"s_{name}.pdf")).pages:
            writer.add_page(pg)
    book_local = os.path.join(WORK, "BOOK_pana.pdf")
    with open(book_local, "wb") as f:
        writer.write(f)
    assert len(PdfReader(book_local).pages) == total, "booklet page count mismatch"

    old_t = page_texts(OLD_PDF)
    new_t = page_texts(book_local)
    assert len(new_t) == total, "new booklet page count mismatch"
    sq_old = [squash(t) for t in old_t]
    sq_new = [squash(t) for t in new_t]

    # 旧PDF内での相関図_old頁範囲を頁テキスト一致で特定
    oldold_t = page_texts(os.path.join(WORK, f"o_{OLD}.pdf"))
    sq_oo = [squash(t) for t in oldold_t]
    n_oo = len(sq_oo)
    oldstart = None
    for i in range(len(sq_old) - n_oo + 1):
        if all(sq_old[i + k] == sq_oo[k] for k in range(n_oo)):
            oldstart = i
            break
    assert oldstart is not None, "相関図_old pages not located in old PDF"
    act(f"old PDF: {OLD} = pages {oldstart+1}-{oldstart+n_oo} ({n_oo}p); {len(sq_old)}p -> {total}p")

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

    # 頁対応マッピング照合(新 j 頁 <-> 旧 j 頁 / j>=oldstart なら旧 j+n_oo 頁)
    # 注: fix34適用のSave後、書き出しPDFのテキストストリーム順が変わるため
    #     座標ソート後の行列に加え行集合の一致も要求する二重判定とする
    #     (利用者承認 2026-11-05: 目視等価の正規化照合への変更)
    from collections import Counter
    def ms_lines(path, idx):
        import pymupdf as fitz
        doc = fitz.open(path)
        pg = doc[idx]
        out = []
        for b in pg.get_text("dict")["blocks"]:
            if b["type"] != 0:
                continue
            for l in b["lines"]:
                t = "".join(s["text"] for s in l["spans"]).strip()
                if t:
                    out.append(squash(t))
        doc.close()
        return Counter(out)
    mo = [ms_lines(OLD_PDF, i) for i in range(len(old_t))]
    co = [canon_lines(OLD_PDF, i) for i in range(len(old_t))]
    cn = [canon_lines(book_local, j) for j in range(total)]
    allowed = {p2 + 1, p3 + 1}
    diffs = []
    for j in range(total):
        oi = j if j < oldstart else j + n_oo
        if cn[j] != co[oi] or ms_lines(book_local, j) != mo[oi]:
            diffs.append(j + 1)
    bad = [d for d in diffs if d not in allowed]
    act(f"diff pages: {diffs} (allowed: {sorted(allowed)})")
    assert not bad, f"UNEXPECTED diff pages: {bad}"
    if p1 + 1 not in diffs:
        act("相関図① page: identical (ok)")
    else:
        raise AssertionError(f"相関図① page {p1+1} must be identical to old")

    # クリップ解消マーカー(②③頁の抽出テキストに末尾文字列が存在)
    miss2 = [m for m in MARK2 if m not in sq_new[p2]]
    miss3 = [m for m in MARK3 if m not in sq_new[p3]]
    act(f"markers ②: {'ALL PRESENT' if not miss2 else 'MISSING %s' % miss2}")
    act(f"markers ③: {'ALL PRESENT' if not miss3 else 'MISSING %s' % miss3}")
    assert not miss2, f"② markers missing: {miss2}"
    assert not miss3, f"③ markers missing: {miss3}"

    shutil.copy2(book_local, PDFP)
    act(f"DONE xlsx {sha256(XLSX)[:16]} pdf {sha256(PDFP)[:16]} ({total}p)")
    shutil.rmtree(WORK, ignore_errors=True)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
