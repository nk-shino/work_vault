# -*- coding: utf-8 -*-
"""media_pdf_regen.py — ①xlsx内メディアの無変更照合 ②冊PDFの再生成(頁数アサート)。

手順:
 1. 正本PDFを TEMP へ退避 (失敗時の復元用)。
 2. 正本PDFの現SHA16が原本記録値と一致することを確認 (ここまで未変更の証拠)。
 3. xlsx と 修正前バックアップ の xl/media/* を照合 (埋め込み画像の無変更)。
 4. 両冊を ReadOnly で開き、冊PDFを正本パスへ上書き出力。
 5. 頁数アサート (Pana=49 / LNB=31)。NGなら退避から復元。
 6. 新PDFのSHA16を出力。
"""
import sys, io, os, hashlib, shutil, zipfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import win32com.client as win32
import pymupdf as fitz

HERE = os.path.dirname(os.path.abspath(__file__))
VAULT = (r"C:/Users/ss80751/OneDrive - NK/ドキュメント/Work_Vault"
         r"/10_業務全般/PanaCIM_LNB/01_成果物")
BACKUP = (r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
          r"\backup_20261102")
STASH = os.path.join(HERE, "pdf_stash_20261105")

BOOKS = {
    "pana": {"xlsx": os.path.join(VAULT, "Pana-CIM管理手順書案_未承認.xlsx"),
             "pdf": os.path.join(VAULT, "Pana-CIM管理手順書案_未承認.pdf"),
             "pages": 49},
    "lnb": {"xlsx": os.path.join(VAULT, "LNB管理手順書案_未承認.xlsx"),
            "pdf": os.path.join(VAULT, "LNB管理手順書案_未承認.pdf"),
            "pages": 31},
}
PDF_SHA_ORIG = {"pana": "C7CE0E167B3A0305", "lnb": "FB0A3F34813EF2BB"}


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest().upper()[:16]


def media_map(p):
    out = {}
    with zipfile.ZipFile(p) as z:
        for n in z.namelist():
            if n.startswith("xl/media/"):
                out[n] = hashlib.sha256(z.read(n)).hexdigest()
    return out


def main():
    os.makedirs(STASH, exist_ok=True)
    # 2) 現PDFが原本と一致すること
    for bk, d in BOOKS.items():
        h = sha16(d["pdf"])
        ok = "OK" if h == PDF_SHA_ORIG[bk] else "MISMATCH(expect %s)" % PDF_SHA_ORIG[bk]
        print("pdf-before %s %s %s" % (h, ok, bk))
        if h != PDF_SHA_ORIG[bk]:
            raise RuntimeError("original PDF SHA mismatch: %s" % bk)
    # 3) xlsx埋め込みメディアの無変更
    for bk, d in BOOKS.items():
        stem = os.path.basename(d["xlsx"])[:-len(".xlsx")]
        b = os.path.join(BACKUP, stem + "_相関図23前_20261105.xlsx")
        if not os.path.exists(b):
            cand = [f for f in os.listdir(BACKUP) if f.startswith(("Pana", "LNB"))]
            raise RuntimeError("backup not found for %s; backups=%s" % (bk, cand))
        m_live, m_bak = media_map(d["xlsx"]), media_map(b)
        if m_live != m_bak:
            diff = {k for k in set(m_live) | set(m_bak) if m_live.get(k) != m_bak.get(k)}
            raise RuntimeError("media changed: %s -> %s" % (bk, sorted(diff)))
        print("media identical (%d files): %s" % (len(m_live), bk))
    # 1) PDF退避
    for bk, d in BOOKS.items():
        shutil.copy2(d["pdf"], os.path.join(STASH, os.path.basename(d["pdf"])))
        print("stashed:", os.path.basename(d["pdf"]))
    # 4-5) 再生成と頁数アサート
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    failed = []
    OUTTMP = os.path.join(HERE, "pdf_out")
    os.makedirs(OUTTMP, exist_ok=True)
    try:
        for bk, d in BOOKS.items():
            tmppdf = os.path.join(OUTTMP, os.path.basename(d["pdf"]))
            wb = app.Workbooks.Open(d["xlsx"], UpdateLinks=0, ReadOnly=True)
            try:
                wb.ExportAsFixedFormat(0, tmppdf, 0, False, False)
            finally:
                try:
                    wb.Close(SaveChanges=False)
                except Exception:
                    pass
            doc = fitz.open(tmppdf)
            n = doc.page_count
            doc.close()
            ok = (n == d["pages"])
            print("pdf-regen %s pages=%d expect=%d %s" % (bk, n, d["pages"], "OK" if ok else "NG"))
            if not ok:
                failed.append(bk)
                continue
            shutil.copy2(tmppdf, d["pdf"])
            print("copied to vault:", os.path.basename(d["pdf"]))
    finally:
        try:
            app.Quit()
        except Exception:
            pass
    if failed:
        for bk in failed:
            shutil.copy2(os.path.join(STASH, os.path.basename(BOOKS[bk]["pdf"])), BOOKS[bk]["pdf"])
            print("restored from stash:", bk)
        raise RuntimeError("page count NG, restored: %s" % failed)
    # 6) 新SHA
    for bk, d in BOOKS.items():
        print("pdf-after %s %s" % (sha16(d["pdf"]), bk))
    for bk, d in BOOKS.items():
        print("xlsx-after %s %s" % (sha16(d["xlsx"]), bk))
    print("MEDIA+PDF REGEN DONE")


if __name__ == "__main__":
    main()
