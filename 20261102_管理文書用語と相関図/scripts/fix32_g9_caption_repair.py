# -*- coding: utf-8 -*-
"""G9修復: 月次再起動シートのキャプション退行(C27·C52)をG8後状態へ復元する。
原因: 横長マージセル(C:AZ·52列)の一部セルへの Range.Replace が範囲外(シート内の
一致セル全体)に作用し、C27(スライド1〜2)とC52(図1キャプション)まで置換された。
対策: Range.Replace を一切使わず、メモリ内 str.replace + MergeArea 先頭セルへの
.Value 代入で復元する(C75 の意図した訂正スライド2は保持)。
安全I/O: セルのテキスト内容はディスクと標準出力へ出力しない(アドレス·ブール·数値のみ)。
採番·PDF出力·検証は保存済みローカルコピーへの短命インスタンスで実行する。"""
import os, sys, json, shutil, hashlib, time

sys.stdout.reconfigure(encoding="utf-8")

BASE = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
VDIR = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
XLSX = os.path.join(VDIR, "Pana-CIM管理手順書案_未承認.xlsx")
PDFP = os.path.join(VDIR, "Pana-CIM管理手順書案_未承認.pdf")
PAGES = os.path.join(BASE, "scripts", "tmp_g9_pana")
REP = os.path.join(BASE, "scripts", "fix32_g9_caption_repair_report.json")
IMG1 = os.path.join(BASE, "src_g9_pptx", "image1.PNG")
IMG2 = os.path.join(BASE, "src_g9_pptx", "image2.PNG")

SHEET = "月次再起動"
ORDER = ["目次", "用語", "構成と管理情報", "相関図①", "相関図②", "相関図③", "相関図_old",
         "管理体制", "月次再起動", "バックアップ", "復旧", "異常時の対応",
         "チェックシート(月次・異常時)", "会議課題一覧(一時)", "付録 引用元と確認範囲",
         "要確認事項一覧", "7-5仮_サービス起動停止"]
EXPECT_PAGES = 49
SHEET_PAGES = 3
QUOTE = ([("異常時の対応", [f"C{r}" for r in range(42, 64)]),
          ("付録 引用元と確認範囲", ["C9", "C10", "C14", "C17", "C20"]),
          ("7-5仮_サービス起動停止", [f"C{r}" for r in range(12, 19)])])
ORIG_SHA16 = {"img_1": "b0da9f9f517f1399", "img_2": "15ee5682287583e9"}

RESTORE = ["C27", "C52"]          # スライド2 -> スライド1 へ復元
KEEP = {"C75": (False, True)}     # 意図した訂正(スライド2)を保持
# 修復後のシート全体の期待状態(行, 列): (スライド1を含む, スライド2を含む)
EXPECT_SCAN = {(27, 3): (True, False), (52, 3): (True, False), (75, 3): (False, True)}

R = {"book": "pana", "kind": "caption_repair", "phase": {}}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def act(m):
    print("[act]", m, flush=True)


def copy_vault(src, dst):
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


os.makedirs(PAGES, exist_ok=True)
local = os.path.join(PAGES, "_repair.xlsx")
copy_vault(XLSX, local)
R["sha_vault_before"] = sha256(XLSX)

import win32com.client as win32
from pypdf import PdfReader, PdfWriter


def quote_hash(wb):
    h = hashlib.sha256()
    n = 0
    for sheet, cells in QUOTE:
        ws = wb.Worksheets(sheet)
        for a in cells:
            h.update(ws.Range(a).Text.encode("utf-8"))
            n += 1
    return h.hexdigest()[:16], n


def slide_flags(ws, addr):
    v = ws.Range(addr).Text
    if not isinstance(v, str):
        return None
    return ("スライド1" in v, "スライド2" in v)


# ---------------- Phase 1: 事前状態の裏付け·修復(.Value代入·Replace不使用) ----------------
app = win32.DispatchEx("Excel.Application")
app.Visible = False
app.DisplayAlerts = False
try:
    wb = app.Workbooks.Open(local, UpdateLinks=0, ReadOnly=False)
    try:
        wb.AutoSaveOn = False
    except Exception:
        pass
    ws = wb.Worksheets(SHEET)
    pre = {}
    for a in RESTORE:
        f = slide_flags(ws, a)
        assert f == (False, True), f"pre-state unexpected at {a}"
        c = ws.Range(a)
        t, v = c.Text, c.MergeArea.Cells(1, 1).Value
        assert isinstance(v, str) and t == v, f"text/value mismatch at {a}"
        pre[a] = {"text_is_value": True}
    for a, want in KEEP.items():
        assert slide_flags(ws, a) == want, f"keep pre-state unexpected at {a}"
    qh1, qn = quote_hash(wb)
    R["phase"]["pre_ok"] = True
    R["phase"]["quote_cells"] = qn

    for a in RESTORE:
        cell = ws.Range(a).MergeArea.Cells(1, 1)
        v = cell.Value
        assert isinstance(v, str)
        cell.Value = v.replace("スライド2", "スライド1")
    R["phase"]["restored_cells"] = RESTORE

    for a in RESTORE:
        assert slide_flags(ws, a) == (True, False), f"restore failed at {a}"
    for a, want in KEEP.items():
        assert slide_flags(ws, a) == want, f"keep changed at {a}"

    ur = ws.UsedRange
    nr, nc = ur.Rows.Count, ur.Columns.Count
    vals = ur.Value
    got = {}
    for i in range(nr):
        row = vals[i] if nr > 1 else (vals,)
        for j in range(nc):
            v = row[j]
            if isinstance(v, str) and "スライド" in v:
                got[(ur.Row + i, ur.Column + j)] = ("スライド1" in v, "スライド2" in v)
    assert got == EXPECT_SCAN, f"sheet scan mismatch: {sorted(got.items())}"
    R["phase"]["sheet_scan"] = {f"r{r}c{c}": b for (r, c), b in sorted(got.items())}
    wb.Save()
    wb.Close(SaveChanges=False)
finally:
    try:
        app.Quit()
    except Exception:
        pass
act(f"Phase 1 ok (restored {len(RESTORE)} cells, sheet scan as expected)")


# ---------------- Phase 2: 埋め込みメディアの原形照合(zip·COM不要) ----------------
import zipfile, re


def media_map(path):
    z = zipfile.ZipFile(path)
    dxml = z.read("xl/drawings/drawing5.xml").decode("utf-8")
    drels = z.read("xl/drawings/_rels/drawing5.xml.rels").decode("utf-8")
    rmap = dict(re.findall(r'Id="(rId\d+)"[^>]*Target="\.\./(media/[^"]+)"', drels))
    out = {}
    for two in re.finditer(r"<xdr:twoCellAnchor[^>]*>(.*?)</xdr:twoCellAnchor>", dxml, re.S):
        blk = two.group(1)
        nm = re.search(r'name="([^"]*)"', blk)
        e = re.search(r'r:embed="(rId\d+)"', blk)
        if nm and e and nm.group(1) in ORIG_SHA16:
            mp = "xl/" + rmap[e.group(1)]
            out[nm.group(1)] = (mp, hashlib.sha256(z.read(mp)).hexdigest()[:16])
    z.close()
    return out


mm = media_map(local)
R["phase"]["media_after_save"] = {k: v[1] for k, v in mm.items()}
bad = {k: v[0] for k, v in mm.items() if v[1] != ORIG_SHA16[k]}
if bad:
    act(f"media recompressed on save, zip-replacing: {sorted(bad)}")
    orig_bytes = {"img_1": open(IMG1, "rb").read(), "img_2": open(IMG2, "rb").read()}
    tmp_out = local + ".new"
    zin = zipfile.ZipFile(local)
    with zipfile.ZipFile(tmp_out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            key = next((k for k, p in bad.items() if p == item.filename), None)
            zout.writestr(item, orig_bytes[key] if key else zin.read(item.filename))
    zin.close()
    os.replace(tmp_out, local)
    mm = media_map(local)
    R["phase"]["media_zip_replaced"] = sorted(bad)
for k, v in mm.items():
    assert v[1] == ORIG_SHA16[k], f"media mismatch {k}: {v[1]}"
R["phase"]["media_final"] = {k: v[1] for k, v in mm.items()}
act(f"Phase 2 ok (media sha {mm['img_1'][1]}, {mm['img_2'][1]})")


# ---------------- Phase 3: 頁実測·冊PDF·引用検証(短命インスタンス) ----------------
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
assert total == EXPECT_PAGES, f"pages {total} != {EXPECT_PAGES}"
assert counts[SHEET] == SHEET_PAGES, f"{SHEET} pages {counts[SHEET]} != {SHEET_PAGES}"
counts2 = export_all(local, with_book=True)
assert counts2 == counts, "pagination shifted"
R["total_pages"] = total
R["sheet_pages"] = counts[SHEET]
act(f"Phase 3 export ok (total={total}, {SHEET}={counts[SHEET]})")

bookpdf_local = os.path.join(PAGES, "BOOK_repair.pdf")
writer = PdfWriter()
for name in ORDER:
    for pg in PdfReader(os.path.join(PAGES, f"{name}.pdf")).pages:
        writer.add_page(pg)
with open(bookpdf_local, "wb") as f:
    writer.write(f)
assert len(PdfReader(bookpdf_local).pages) == total, "book pages"

app4 = win32.DispatchEx("Excel.Application")
app4.Visible = False
app4.DisplayAlerts = False
try:
    wb4 = app4.Workbooks.Open(local, UpdateLinks=0, ReadOnly=True)
    qh3, _ = quote_hash(wb4)
    wb4.Close(SaveChanges=False)
finally:
    app4.Quit()
assert qh3 == qh1, "quote changed!"
R["quote_ok"] = True
act("quote verify ok (34 cells unchanged)")


# ---------------- Phase 4: vault へ反映 ----------------
copy_vault(local, XLSX)
copy_vault(bookpdf_local, PDFP)
try:
    os.remove(local)
except Exception:
    pass
R["sha_after"] = sha256(XLSX)
save_report()
act(f"DONE pana sha {R['sha_after'][:16]} (repair deployed)")
