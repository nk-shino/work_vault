# -*- coding: utf-8 -*-
"""rev-2監査指摘2(P3)の修正: Pana冊 要確認事項一覧!C35 の重複文
(裏付け記録の照合は未了 が連続2回)を1回へ削減する。
編集は Excel COM 短命インスタンス(AutoSaveOn=False)で対象セルのみ .Value 代入。
Range.Replace は使用しない(G9の退行対策)。OneDrive 排他は6回再試行で吸収。
メディアは保存前のバイトスナップショットと照合し、再圧縮を検出したらzipレベルで復元。
中間ファイルは TEMP 配下のみ。安全I/O: セルのテキスト内容はディスクと標準出力へ出力しない
(アドレス·数値·ブール·SHAのみ)。"""
import os, sys, json, shutil, hashlib, time, zipfile

sys.stdout.reconfigure(encoding="utf-8")

BASE = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
VDIR = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
XLSX = os.path.join(VDIR, "Pana-CIM管理手順書案_未承認.xlsx")
PDFP = os.path.join(VDIR, "Pana-CIM管理手順書案_未承認.pdf")
WORK = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\g10_rev2"
REP = os.path.join(BASE, "scripts", "fix34_g10_rev2_report.json")

SHEET = "要確認事項一覧"
CELL = "C35"
SINGLE = "裏付け記録の照合は未了"
DOUBLED = SINGLE + SINGLE

QUOTE = ([("異常時の対応", [f"C{r}" for r in range(42, 64)]),
          ("付録 引用元と確認範囲", ["C9", "C10", "C14", "C17", "C20"]),
          ("7-5仮_サービス起動停止", [f"C{r}" for r in range(12, 19)])])
EXPECT_PAGES = 49
EXPECT_SHEET_PAGES = 2

R = {"book": "pana", "kind": "rev2_c35_dedup", "phase": {}}


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


def snapshot_media(path):
    z = zipfile.ZipFile(path)
    out = {n: z.read(n) for n in z.namelist() if n.startswith("xl/media/")}
    z.close()
    return out


def restore_media(local_path, snap):
    after = {n: hashlib.sha256(b).hexdigest()[:16] for n, b in snapshot_media(local_path).items()}
    before = {n: hashlib.sha256(b).hexdigest()[:16] for n, b in snap.items()}
    changed = [n for n in before if n in after and after[n] != before[n]]
    added = [n for n in after if n not in before]
    removed = [n for n in before if n not in after]
    if not changed and not added and not removed:
        return changed, added, removed
    assert not added and not removed, f"media set changed: +{added} -{removed}"
    zin = zipfile.ZipFile(local_path)
    tmp_out = local_path + ".new"
    with zipfile.ZipFile(tmp_out, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = snap[item.filename] if item.filename in changed else zin.read(item.filename)
            zout.writestr(item, data)
    zin.close()
    os.replace(tmp_out, local_path)
    chk = {n: hashlib.sha256(b).hexdigest()[:16] for n, b in snapshot_media(local_path).items()}
    assert chk == before, "media restore failed"
    return changed, added, removed


def quote_hash(wb):
    h = hashlib.sha256()
    n = 0
    for sheet, cells in QUOTE:
        ws = wb.Worksheets(sheet)
        for a in cells:
            h.update(ws.Range(a).Text.encode("utf-8"))
            n += 1
    return h.hexdigest()[:16], n


def export_all(local_path, sheet_names, with_book=False, tag=""):
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
        if with_book:
            wb2.ExportAsFixedFormat(0, os.path.join(WORK, f"{tag}_BOOK.pdf"), 0, True, False)
        wb2.Close(SaveChanges=False)
    finally:
        try:
            app2.Quit()
        except Exception:
            pass
    return counts


os.makedirs(WORK, exist_ok=True)
import win32com.client as win32
from pypdf import PdfReader, PdfWriter

R["sha_before"] = sha256(XLSX)
local = os.path.join(WORK, "_rev2.xlsx")
copy_vault(XLSX, local)
media_snap = snapshot_media(local)
act(f"Phase 0 ok (sha_before {R['sha_before'][:16]}, media {len(media_snap)})")

# ---------- Phase A: 読み取り(C35事前状態·引用ハッシュ·頁数) ----------
app = win32.DispatchEx("Excel.Application")
app.Visible = False
app.DisplayAlerts = False
try:
    wb = app.Workbooks.Open(local, UpdateLinks=0, ReadOnly=True)
    sheet_names = [wb.Sheets(i).Name for i in range(1, wb.Sheets.Count + 1)]
    qh1, qn = quote_hash(wb)
    ws = wb.Worksheets(SHEET)
    v = ws.Range(CELL).MergeArea.Cells(1, 1).Value
    assert isinstance(v, str), "C35 not text"
    n_before = v.count(SINGLE)
    assert n_before == 2 and DOUBLED in v, f"unexpected pre-state (count={n_before})"
    wb.Close(SaveChanges=False)
finally:
    try:
        app.Quit()
    except Exception:
        pass
counts = export_all(local, sheet_names, tag="a")
R["phase"]["pre"] = {"quote_cells": qn, "c35_single_count": n_before, "pages": sum(counts.values())}
act(f"Phase A ok (quote {qn}, C35 count={n_before}, pages={sum(counts.values())}, {SHEET}={counts[SHEET]})")

# ---------- Phase B: 編集(.Value 代入·Replace 不使用) ----------
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
    c = ws.Range(CELL).MergeArea.Cells(1, 1)
    v = c.Value
    assert isinstance(v, str) and v.count(SINGLE) == 2 and DOUBLED in v
    v2 = v.replace(DOUBLED, SINGLE)
    assert v2.count(SINGLE) == 1, "dedup failed"
    assert len(v2) == len(v) - len(SINGLE), "unexpected length delta"
    c.Value = v2
    v3 = ws.Range(CELL).MergeArea.Cells(1, 1).Value
    assert isinstance(v3, str) and v3.count(SINGLE) == 1 and DOUBLED not in v3
    wb.Save()
    wb.Close(SaveChanges=False)
finally:
    try:
        app.Quit()
    except Exception:
        pass
changed, added, removed = restore_media(local, media_snap)
R["phase"]["edit"] = {"c35_single_count_after": 1, "media_restored": len(changed)}
act(f"Phase B ok (C35 dedup, media restored {len(changed)}, +{len(added)} -{len(removed)})")

# ---------- Phase C: 頁数·冊PDF·引用検証·メディア照合 ----------
counts2 = export_all(local, sheet_names, with_book=True, tag="b")
assert counts2 == counts, f"pagination shifted: {counts2} vs {counts}"
assert sum(counts2.values()) == EXPECT_PAGES, f"pages {sum(counts2.values())} != {EXPECT_PAGES}"
assert counts2[SHEET] == EXPECT_SHEET_PAGES, f"{SHEET} pages {counts2[SHEET]} != {EXPECT_SHEET_PAGES}"
writer = PdfWriter()
for name in sheet_names:
    for pg in PdfReader(os.path.join(WORK, f"b_{name}.pdf")).pages:
        writer.add_page(pg)
book_local = os.path.join(WORK, "BOOK_assembled.pdf")
with open(book_local, "wb") as f:
    writer.write(f)
total = len(PdfReader(book_local).pages)
assert total == EXPECT_PAGES, "book pages"

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
final_media = {n: hashlib.sha256(b).hexdigest()[:16] for n, b in snapshot_media(local).items()}
snap_map = {n: hashlib.sha256(b).hexdigest()[:16] for n, b in media_snap.items()}
assert final_media == snap_map, "media mismatch after restore"
R["pages"] = total
R["sheet_pages"] = counts2[SHEET]
R["media_count"] = len(final_media)
R["media_ok"] = True
R["quote_ok"] = True
act(f"Phase C ok (total={total}, {SHEET}={counts2[SHEET]}, quote ok, media {len(final_media)} ok)")

# ---------- 反映 ----------
copy_vault(local, XLSX)
copy_vault(book_local, PDFP)
try:
    os.remove(local)
except Exception:
    pass
R["sha_after"] = sha256(XLSX)
with open(REP, "w", encoding="utf-8") as f:
    json.dump(R, f, ensure_ascii=False, indent=1)
act(f"DONE pana sha {R['sha_after'][:16]} ({total}p)")
