# -*- coding: utf-8 -*-
"""pdf_regen_lnb3.py — LNB冊PDFを確定手順で再生成する(fix34対応版)。

pdf_regen_lnb2.py と同じ手順に、fix34 分の検証を追加する:
  - クリップ解消マーカー(②③頁の末尾文字列が抽出テキストに存在)
  - 認証情報一覧のフッター3欄が描画されていること(左 NR4030·中央 様式…·右 日本光電)
  - 認証情報一覧の頁差分はフッター領域のみ(本文は旧PDFと一致)
  - 差分許容頁 = 相関図②③ + 認証情報一覧の頁
合格なら vault へ反映し SHA を記録。不合格は vault 書き込み前に中断。
"""
import os, sys, shutil, time, hashlib, traceback

V = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
XLSX = os.path.join(V, "LNB管理手順書案_未承認.xlsx")
PDFP = os.path.join(V, "LNB管理手順書案_未承認.pdf")
OLD_PDF = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\corr23\pdf_stash_20261105\LNB管理手順書案_未承認.pdf"
WORK = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\corr23\lnb_pdf_work3"
EXPECT_PAGES = 31

CRED = "申し送り(認証情報)"
OLD = "相関図_old"
CREDLIST = "認証情報一覧"
ORDER_FULL = ["表紙", "目次", "用語", "構成と管理情報", "相関図①", "相関図②", "相関図③", OLD,
              "管理体制", "日次点検", "定期管理", "バックアップ", "復旧", "異常時の対応",
              "チェックシート(日次)", "チェックシート(月次・異常時)", "会議課題一覧(一時)",
              "要確認事項一覧", CRED, CREDLIST, "引用と部品照合"]
ORDER_NEW = [n for n in ORDER_FULL if n != OLD]
EXPORT_SHEETS = [n for n in ORDER_NEW if n != CRED]
OLD_MARK = "確定事項のみ記載"   # 相関図_old 固有の見出し語(漏出検出用)

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

def body_and_footer(path, idx, bottom=60.0):
    """頁を(フッター領域を除く本文の正規化行, フッター領域の行リスト)に分解する。"""
    import pymupdf as fitz
    doc = fitz.open(path)
    pg = doc[idx]
    h = pg.rect.height
    body, foot = [], []
    for b in pg.get_text("dict")["blocks"]:
        if b["type"] != 0:
            continue
        for l in b["lines"]:
            txt = "".join(s["text"] for s in l["spans"])
            if not txt.strip():
                continue
            (foot if l["bbox"][1] > h - bottom else body).append(
                (round(l["bbox"][1], 1), round(l["bbox"][0], 1), squash(txt)))
    doc.close()
    body.sort()
    return body, [t for _, _, t in sorted(foot)]

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

    n_cl = counts[CREDLIST]
    cl_start = offset + cred_pages          # 0-based booklet position of 認証情報一覧
    allowed = {p2 + 1, p3 + 1} | set(range(cl_start + 1, cl_start + n_cl + 1))
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
    mo = [ms_lines(OLD_PDF, i) for i in range(total)]
    co = [canon_lines(OLD_PDF, i) for i in range(total)]
    cn = [canon_lines(book_local, j) for j in range(total)]
    diff_pages = [i + 1 for i in range(total) if cn[i] != co[i] or ms_lines(book_local, i) != mo[i]]
    bad = [d for d in diff_pages if d not in allowed]
    act(f"diff pages: {diff_pages} (allowed: {sorted(allowed)})")
    assert not bad, f"UNEXPECTED diff pages: {bad}"
    if p1 + 1 in diff_pages:
        raise AssertionError(f"相関図① page {p1+1} must be identical to old")
    act("相関図① page: identical (ok)")

    # 認証情報一覧: 差分はフッター領域のみ(本文は旧PDFと一致)
    for k in range(n_cl):
        j = cl_start + k
        ob, of = body_and_footer(OLD_PDF, j)
        nb, nf = body_and_footer(book_local, j)
        assert ob == nb, f"認証情報一覧 booklet p{j+1}: body text differs (footer-only diff expected)"
        join_f = " | ".join(nf)
        assert "NR4030" in nf or any(t == "NR4030" for t in nf), f"p{j+1}: left footer NR4030 missing (footer lines: {nf})"
        assert any("様式" in t for t in nf), f"p{j+1}: center footer missing (footer lines: {nf})"
        assert any("日本光電" in t for t in nf), f"p{j+1}: right footer missing (footer lines: {nf})"
        act(f"認証情報一覧 p{j+1}: body identical, footer lines: {join_f}")

    # クリップ解消マーカー
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
