# -*- coding: utf-8 -*-
"""G9: Pana冊 月次再起動章 — pptx原形画像への差し替え(図1)とキャプション出典訂正(図2)。
安全I/O: セル/図形のテキスト内容をディスクと標準出力へ出力しない(数値·図形名·セル番地のみ)。
採番·PDF出力·検証は保存済みファイルのローカルコピーに対する短命インスタンスで実行する。
vault(OneDrive)への反映は copy_vault の再試行で同期排他を吸収する。"""
import os, sys, json, shutil, hashlib, time

sys.stdout.reconfigure(encoding="utf-8")

BASE = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
VDIR = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
XLSX = os.path.join(VDIR, "Pana-CIM管理手順書案_未承認.xlsx")
PDFP = os.path.join(VDIR, "Pana-CIM管理手順書案_未承認.pdf")
BACKUP = os.path.join(BASE, "backup_20261102", "Pana-CIM管理手順書案_未承認_G9前_20261104.xlsx")
PAGES = os.path.join(BASE, "scripts", "tmp_g9_pana")
IMG1 = os.path.join(BASE, "src_g9_pptx", "image1.PNG")   # pptx 原形 1385x1075px
REP = os.path.join(BASE, "scripts", "fix31_g9_pana_report.json")

SHEET = "月次再起動"
ORDER = ["目次", "用語", "構成と管理情報", "相関図①", "相関図②", "相関図③", "相関図_old",
         "管理体制", "月次再起動", "バックアップ", "復旧", "異常時の対応",
         "チェックシート(月次・異常時)", "会議課題一覧(一時)", "付録 引用元と確認範囲",
         "要確認事項一覧", "7-5仮_サービス起動停止"]
EXPECT_PAGES = 49
QUOTE = ([("異常時の対応", [f"C{r}" for r in range(42, 64)]),
          ("付録 引用元と確認範囲", ["C9", "C10", "C14", "C17", "C20"]),
          ("7-5仮_サービス起動停止", [f"C{r}" for r in range(12, 19)])])
# pptx 原形の画素寸法(比率維持リサイズに使用)
ORIG_W, ORIG_H = 1385, 1075
ORIG_SHA16 = {"img_1": "b0da9f9f517f1399", "img_2": "15ee5682287583e9"}

R = {"book": "pana", "phase": {}}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def act(m):
    print("[act]", m, flush=True)


def copy_vault(src, dst):
    """vault(OneDrive)の同期排他(WinError 32)を複数回の再試行で吸収する。"""
    last = None
    for i in range(6):
        try:
            shutil.copy2(src, dst)
            return
        except PermissionError as e:
            last = e
            time.sleep(3.0 * (i + 1))
    raise last


def save_report():
    with open(REP, "w", encoding="utf-8") as f:
        json.dump(R, f, ensure_ascii=False, indent=1)


# ---------------- Phase 0 ----------------
if not os.path.exists(BACKUP):
    copy_vault(XLSX, BACKUP)
    act(f"G9前バックアップ作成 sha={sha256(BACKUP)[:16]}")
sha_bak = sha256(BACKUP)
if sha256(XLSX) != sha_bak:
    act(f"restore from backup ({sha256(XLSX)[:12]} -> {sha_bak[:12]})")
    copy_vault(BACKUP, XLSX)
R["sha_before"] = sha256(XLSX)
os.makedirs(PAGES, exist_ok=True)
for f in os.listdir(PAGES):
    os.remove(os.path.join(PAGES, f))

import win32com.client as win32
from pypdf import PdfReader, PdfWriter

XL_PART = 2  # xlPart


def quote_hash(wb):
    import hashlib as _h
    h = _h.sha256()
    n = 0
    for sheet, cells in QUOTE:
        ws = wb.Worksheets(sheet)
        for a in cells:
            h.update(ws.Range(a).Text.encode("utf-8"))
            n += 1
    return h.hexdigest()[:16], n


# ---------------- Phase A: 読み取り(図形幾何·引用ハッシュ) ----------------
app = win32.DispatchEx("Excel.Application")
app.Visible = False
app.DisplayAlerts = False
try:
    wb = app.Workbooks.Open(XLSX, UpdateLinks=0, ReadOnly=True)
    qh1, qn = quote_hash(wb)
    R["quote_cells"] = qn
    ws = wb.Worksheets(SHEET)
    geo = {}
    for nm in ("img_1", "img_2"):
        sh = ws.Shapes(nm)
        geo[nm] = {"left": round(sh.Left, 1), "top": round(sh.Top, 1),
                   "width": round(sh.Width, 1), "height": round(sh.Height, 1)}
    R["phase"]["geometry_before"] = geo
    wb.Close(SaveChanges=False)
finally:
    app.Quit()
act(f"Phase A ok (quote {qn} cells, img_1 {geo['img_1']['width']}x{geo['img_1']['height']}pt)")

# ---------------- Phase B: 図1を原形へ差し替え·キャプション出典訂正 ----------------
app = win32.DispatchEx("Excel.Application")
app.Visible = False
app.DisplayAlerts = False
try:
    wb = app.Workbooks.Open(XLSX, UpdateLinks=0, ReadOnly=False)
    try:
        wb.AutoSaveOn = False
    except Exception:
        pass
    ws = wb.Worksheets(SHEET)
    old = ws.Shapes("img_1")
    L, T, W = old.Left, old.Top, old.Width
    H_new = round(min(W, 340.0) * ORIG_H / ORIG_W, 1)
    old.Delete()
    pic = ws.Shapes.AddPicture(IMG1, False, True, L, T, min(W, 340.0), H_new)
    pic.Name = "img_1"
    R["phase"]["img_1_replaced"] = {"left": round(L, 1), "top": round(T, 1),
                                    "width": round(min(W, 340.0), 1), "height": H_new,
                                    "source_px": [ORIG_W, ORIG_H]}
    # 図2キャプションの出典訂正(「図2」で始まるセルのみ·テキストは出力しない)
    fixed = 0
    for r in range(50, 90):
        c = ws.Range(f"C{r}")
        v = c.Text
        if isinstance(v, str) and v.startswith("図2") and "スライド1" in v:
            c.Replace("スライド1", "スライド2", XL_PART)
            fixed += 1
    R["phase"]["caption_fixed_cells"] = fixed
    assert fixed == 1, "figure2 caption not found"
    wb.Save()
    wb.Close(SaveChanges=False)
finally:
    app.Quit()
act(f"Phase B ok (img_1 -> original png, caption fixed {fixed} cell)")

# ---------------- Phase B2: 埋め込み画像を原形バイトへ置換(zip·COM不要) ----------------
# Excel の自動圧縮(220dpi相当)が Save 時に原形を再リサンプリングするため、
# 保存済み xlsx の該当メディアのバイトのみを原形 PNG と差し替える。
ORIG_BYTES = open(IMG1, "rb").read()
OLD_MEDIA_SHA16 = "e567ad35c851d251"  # 圧縮済み旧図1(1040x807)

local = os.path.join(PAGES, "_src.xlsx")
copy_vault(XLSX, local)

import zipfile, re

def locate_img1_media(zf):
    dxml = zf.read("xl/drawings/drawing5.xml").decode("utf-8")
    drels = zf.read("xl/drawings/_rels/drawing5.xml.rels").decode("utf-8")
    rmap = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="\.\./(media/[^"]+)"', drels))
    for two in re.finditer(r"<xdr:twoCellAnchor[^>]*>(.*?)</xdr:twoCellAnchor>", dxml, re.S):
        blk = two.group(1)
        nm = re.search(r'name="([^"]*)"', blk)
        e = re.search(r'r:embed="(rId\d+)"', blk)
        if nm and nm.group(1) == "img_1" and e:
            return "xl/" + rmap[e.group(1)]
    raise AssertionError("img_1 not found in drawing")

zin = zipfile.ZipFile(local)
mpath = locate_img1_media(zin)
cur = hashlib.sha256(zin.read(mpath)).hexdigest()[:16]
assert cur == OLD_MEDIA_SHA16, f"unexpected current media {mpath} {cur}"
# 共有参照の確認(他の drawing から同じメディアを参照していないこと)
shared = []
for n in zin.namelist():
    if re.match(r"xl/drawings/_rels/drawing\d+\.xml\.rels$", n) and "drawing5" not in n:
        rt = re.findall(r'Target="\.\./(media/[^"]+)"', zin.read(n).decode("utf-8"))
        for t in rt:
            if t == mpath.split("xl/")[1]:
                shared.append(n)
assert not shared, f"media shared with {shared}"
tmp_out = local + ".new"
with zipfile.ZipFile(tmp_out, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = ORIG_BYTES if item.filename == mpath else zin.read(item.filename)
        zout.writestr(item, data)
zin.close()
os.replace(tmp_out, local)
zin2 = zipfile.ZipFile(local)
chk = hashlib.sha256(zin2.read(mpath)).hexdigest()[:16]
zin2.close()
assert chk == hashlib.sha256(ORIG_BYTES).hexdigest()[:16], "zip replace failed"
R["phase"]["media_replace"] = {"path": mpath, "before": cur, "after": chk, "shared_refs": 0}
act(f"Phase B2 ok ({mpath} -> original bytes)")

# ---------------- Phase C: 頁実測·冊PDF·引用検証(短命インスタンス) ----------------
def export_all(local_path, with_book=False):
    app2 = win32.DispatchEx("Excel.Application")
    app2.Visible = False
    app2.DisplayAlerts = False
    try:
        wb2 = app2.Workbooks.Open(local_path, UpdateLinks=0, ReadOnly=True)
        counts = {}
        for name in ORDER:
            p = os.path.join(PAGES, f"{name}.pdf")
            for attempt in range(3):
                try:
                    wb2.Worksheets(name).ExportAsFixedFormat(0, p, 0, True, False)
                    break
                except Exception:
                    if attempt == 2:
                        raise
                    time.sleep(2.0)
            counts[name] = len(PdfReader(p).pages)
        if with_book:
            wb2.ExportAsFixedFormat(0, os.path.join(PAGES, "BOOK.pdf"), 0, True, False)
        wb2.Close(SaveChanges=False)
    finally:
        try:
            app2.Quit()
        except Exception:
            pass
    return counts


counts = export_all(local)
total = sum(counts.values())
R["pages"] = counts
R["total"] = total
act(f"PAGES total={total} ({SHEET}={counts[SHEET]})")

if total != EXPECT_PAGES:
    raise AssertionError(f"pages {total} != {EXPECT_PAGES}: numbering rework needed")

# 採番は既存設定のまま(頁数不変のため再設定しない)
counts2 = export_all(local, with_book=True)
assert counts2 == counts, f"pagination shifted: {counts2}"
act("PASS2 ok")

bookpdf_local = os.path.join(PAGES, "BOOK_local.pdf")
writer = PdfWriter()
for name in ORDER:
    for pg in PdfReader(os.path.join(PAGES, f"{name}.pdf")).pages:
        writer.add_page(pg)
with open(bookpdf_local, "wb") as f:
    writer.write(f)
assert len(PdfReader(bookpdf_local).pages) == total, "book pages"
copy_vault(bookpdf_local, PDFP)
act(f"BOOK -> {PDFP} ({total}p)")

# 引用区間の不変検証(短命インスタンス·メモリ内照合)
app4 = win32.DispatchEx("Excel.Application")
app4.Visible = False
app4.DisplayAlerts = False
try:
    wb4 = app4.Workbooks.Open(local, UpdateLinks=0, ReadOnly=True)
    qh3, qn3 = quote_hash(wb4)
    wb4.Close(SaveChanges=False)
finally:
    app4.Quit()
assert qh3 == qh1, "quote changed!"
R["quote_ok"] = True
act("quote verify ok")

copy_vault(local, XLSX)  # 最終状態を vault へ反映
try:
    os.remove(local)
except Exception:
    pass
R["sha_after"] = sha256(XLSX)

# ---------------- 埋め込み画像の原形照合(zip·COM不要) ----------------
import zipfile, re

z = zipfile.ZipFile(XLSX)
dxml = z.read("xl/drawings/drawing5.xml").decode("utf-8")
drels = z.read("xl/drawings/_rels/drawing5.xml.rels").decode("utf-8")
rmap = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="\.\./(media/[^"]+)"', drels))
emb = {}
for two in re.finditer(r"<xdr:twoCellAnchor[^>]*>(.*?)</xdr:twoCellAnchor>", dxml, re.S):
    blk = two.group(1)
    nm = re.search(r'name="([^"]*)"', blk)
    e = re.search(r'r:embed="(rId\d+)"', blk)
    if nm and e and nm.group(1) in ORIG_SHA16:
        mf = "xl/" + rmap[e.group(1)]
        emb[nm.group(1)] = hashlib.sha256(z.read(mf)).hexdigest()[:16]
R["media_sha16"] = emb
for nm, s in emb.items():
    assert s == ORIG_SHA16[nm], f"media mismatch for {nm}: {s}"
act(f"media sha ok {emb}")

save_report()
act(f"DONE pana sha {R['sha_after'][:16]}")
