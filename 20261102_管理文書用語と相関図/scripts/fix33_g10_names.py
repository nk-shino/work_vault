# -*- coding: utf-8 -*-
"""G10: 管理者·監督者等の個人名を役職語彙へ置換(両冊)。
適用範囲(利用者承認 2026-11-04): A 管理体制の役割割当+B 役割割当の解決記録+C 作業分担の
担当記載。同席者を指す記載(管理体制3-1·月次4-3 Step 2)も削除対象(回答: 削除)。
D(出典帰属·所在パス)は現状維持(7-5仮C9·用語C8)。
置換は Range.Replace を使わず、メモリ内の文字列置換+MergeArea 先頭セルへの .Value 代入で
行う(G9のマージセル退行対策)。保存後にメディアの再圧縮を検出した場合は zip レベルで
バイトを復元する。安全I/O: セル·図形のテキストをディスクと標準出力へ出力しない
(アドレス·数値·図形名·ブールのみ)。"""
import os, sys, json, shutil, hashlib, time, zipfile, re

sys.stdout.reconfigure(encoding="utf-8")

BASE = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
VDIR = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
PAGES = os.path.join(BASE, "scripts", "tmp_g10_names")
REP = os.path.join(BASE, "scripts", "fix33_g10_names_report.json")

QUOTE_PANA = ([("異常時の対応", [f"C{r}" for r in range(42, 64)]),
               ("付録 引用元と確認範囲", ["C9", "C10", "C14", "C17", "C20"]),
               ("7-5仮_サービス起動停止", [f"C{r}" for r in range(12, 19)])])
QUOTE_LNB = [("引用と部品照合", ["C13", "C16", "C20"])]

# 役割語彙への置換対(旧部分文字列 -> 新部分文字列)。旧文は各セルの実測(ダンプ)から採取。
SAME_MOCHIGI_KURABAYASHI = ("確保できない場合は茂木(由)または倉林に声をかける",
                            "確保できない場合は管理責任者に声をかける")
ROLES_CONFIRMED = ("管理責任者＝茂木（由）・倉林、副管理責任者＝石井・茂木（絵）と確定(本人確認)",
                   "管理責任者·副管理責任者の各担当を本人確認に基づき確定")
NINSHOU_NOTE = [("＊人名と割り当ては 2026-10-14、篠原のグループによる本人確認に基づく。",
                 "＊割り当ては 2026-10-14 の本人確認に基づく。"),
                ("会議記録 §12 の「副管理責任者を倉林さんとし」は",
                 "会議記録 §12 の記載は")]
DOC_TEAM_CELL = ("文書作成：篠原、大塚、茂木（絵）、竹渕（リーダー 茂木（絵）・スケジュール管理担当）",
                 "文書作成：（リーダー·スケジュール管理担当を含む）")

EDITS_PANA = [
    ("管理体制", "C7", [("起案は篠原が担当する", "起案は文書作成担当が行う"),
                        ("チーム(篠原、大塚、茂木(絵)、竹渕)は", "文書作成チームは")]),
    ("管理体制", "C9", [("管理責任者：茂木（由）、倉林（2名体制）", "管理責任者：（2名体制）")]),
    ("管理体制", "C10", [("副管理責任者：石井、茂木（絵）（2名体制）", "副管理責任者：（2名体制）")]),
    ("管理体制", "C15", [DOC_TEAM_CELL]),
    ("管理体制", "C17", NINSHOU_NOTE),
    ("管理体制", "C19", [SAME_MOCHIGI_KURABAYASHI]),
    ("月次再起動", "C23", [SAME_MOCHIGI_KURABAYASHI]),
    ("要確認事項一覧", "C11", [("起案は篠原が担当(第3章)", "起案は文書作成担当が行う(第3章)")]),
    ("要確認事項一覧", "C20", [("調査・整理は篠原が実施し", "調査・整理は文書作成担当が実施し")]),
    ("要確認事項一覧", "C35", [("管理責任者＝茂木（由）・倉林、副管理責任者＝石井・茂木（絵）と本人確認に基づき確定(第3章)",
                                "管理責任者·副管理責任者の各担当を本人確認に基づき確定(第3章)")]),
    ("会議課題一覧(一時)", "C10", [("確認方法: 篠原が現行実施者に聞き取り", "確認方法: 文書作成担当が現行実施者に聞き取り")]),
    ("会議課題一覧(一時)", "C15", [("聞き取りは篠原が実施", "聞き取りは文書作成担当が実施")]),
    ("会議課題一覧(一時)", "C16", [("確認先の候補挙げは篠原が実施", "確認先の候補挙げは文書作成担当が実施")]),
    ("会議課題一覧(一時)", "C17", [("調査・整理は篠原が実施し", "調査・整理は文書作成担当が実施し")]),
    ("会議課題一覧(一時)", "C39", [ROLES_CONFIRMED]),
    ("会議課題一覧(一時)", "C40", [("大塚さんへの確認依頼は取り下げ", "関係先への確認依頼は取り下げ")]),
]

EDITS_LNB = [
    ("管理体制", "C8", [("管理責任者：茂木（由）、倉林（2名体制）", "管理責任者：（2名体制）")]),
    ("管理体制", "C9", [("副管理責任者：石井、茂木（絵）（2名体制）", "副管理責任者：（2名体制）")]),
    ("管理体制", "C14", [DOC_TEAM_CELL]),
    ("管理体制", "C16", NINSHOU_NOTE),
    ("バックアップ", "C16", [("確認担当: 篠原、大塚、茂木。", "確認担当: 文書作成チーム。")]),
    ("会議課題一覧(一時)", "C10", [("確認方法: 篠原が現行実施者に聞き取り", "確認方法: 文書作成担当が現行実施者に聞き取り")]),
    ("会議課題一覧(一時)", "C15", [("聞き取りは篠原が実施", "聞き取りは文書作成担当が実施")]),
    ("会議課題一覧(一時)", "C16", [("確認先の候補挙げは篠原が実施", "確認先の候補挙げは文書作成担当が実施")]),
    ("会議課題一覧(一時)", "C17", [("調査・整理は篠原が実施し", "調査・整理は文書作成担当が実施し")]),
    ("会議課題一覧(一時)", "C39", [ROLES_CONFIRMED]),
    ("会議課題一覧(一時)", "C40", [("大塚さんへの確認依頼は取り下げ", "関係先への確認依頼は取り下げ")]),
    ("要確認事項一覧", "C40", [("実物確認(篠原)", "実物確認(文書作成担当)")]),
    ("要確認事項一覧", "C47", [("同名は茂木（絵）＝絵美さん（当グループ・スケジュール管理担当）／茂木（由）＝由美子さん（相手グループ）。管理責任者＝茂木（由）・倉林、副管理責任者＝石井・茂木（絵）と確定（§3）。",
                                "同名の2名を識別し（当グループ·相手グループ·スケジュール管理担当の別を含む）、管理責任者·副管理責任者の各担当を確定（§3）。"),
                               ("会議記録 §12 の「副管理責任者を倉林さんとし」は", "会議記録 §12 の記載は"),
                               ("／篠原のグループによる本人確認", "／本人確認を実施")]),
]

BOOKS = {
    "pana": {"xlsx": os.path.join(VDIR, "Pana-CIM管理手順書案_未承認.xlsx"),
             "pdfp": os.path.join(VDIR, "Pana-CIM管理手順書案_未承認.pdf"),
             "backup": os.path.join(BASE, "backup_20261102", "Pana-CIM管理手順書案_未承認_G10前_20261104.xlsx"),
             "quote": QUOTE_PANA, "edits": EDITS_PANA,
             "allowed": {("7-5仮_サービス起動停止", "$C$9")}, "expect_cells": 16},
    "lnb": {"xlsx": os.path.join(VDIR, "LNB管理手順書案_未承認.xlsx"),
            "pdfp": os.path.join(VDIR, "LNB管理手順書案_未承認.pdf"),
            "backup": os.path.join(BASE, "backup_20261102", "LNB管理手順書案_未承認_G10前_20261104.xlsx"),
            "quote": QUOTE_LNB, "edits": EDITS_LNB,
            "allowed": {("用語", "$C$8")}, "expect_cells": 13},
}

NAMES = ["篠原", "大塚", "茂木", "倉林", "石井", "竹渕", "佐藤", "絵美", "由美子"]

R = {"kind": "g10_names", "books": {}}


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


os.makedirs(PAGES, exist_ok=True)

import win32com.client as win32
from pypdf import PdfReader, PdfWriter


def quote_hash(wb, quote):
    h = hashlib.sha256()
    n = 0
    for sheet, cells in quote:
        ws = wb.Worksheets(sheet)
        for a in cells:
            h.update(ws.Range(a).Text.encode("utf-8"))
            n += 1
    return h.hexdigest()[:16], n


def scan_names(wb):
    """セル(使用範囲)と図形テキストをメモリ内で走査し、氏名を含む場所のアドレスのみ返す。"""
    cells, shapes = set(), {}
    for si in range(1, wb.Sheets.Count + 1):
        ws = wb.Sheets(si)
        ur = ws.UsedRange
        nr, nc = ur.Rows.Count, ur.Columns.Count
        if nr > 0 and nc > 0:
            vals = ur.Value
            for i in range(nr):
                row = vals[i] if nr > 1 else (vals,)
                for j in range(nc):
                    v = row[j]
                    if isinstance(v, str) and any(n in v for n in NAMES):
                        cells.add((ws.Name, ws.Cells(ur.Row + i, ur.Column + j).Address))
        cnt = 0
        for sh in ws.Shapes:
            try:
                if sh.TextFrame2.HasText:
                    t = sh.TextFrame2.TextRange.Text
                    if isinstance(t, str) and any(n in t for n in NAMES):
                        cnt += 1
            except Exception:
                pass
        if cnt:
            shapes[ws.Name] = cnt
    return cells, shapes


def export_all(local_path, sheet_names, with_book=False, tag=""):
    app2 = win32.DispatchEx("Excel.Application")
    app2.Visible = False
    app2.DisplayAlerts = False
    try:
        wb2 = app2.Workbooks.Open(local_path, UpdateLinks=0, ReadOnly=True)
        counts = {}
        for name in sheet_names:
            p = os.path.join(PAGES, f"{tag}_{name}.pdf")
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
            wb2.ExportAsFixedFormat(0, os.path.join(PAGES, f"{tag}_BOOK.pdf"), 0, True, False)
        wb2.Close(SaveChanges=False)
    finally:
        try:
            app2.Quit()
        except Exception:
            pass
    return counts


def media_map(path):
    z = zipfile.ZipFile(path)
    out = {}
    for n in z.namelist():
        if n.startswith("xl/media/"):
            out[n] = hashlib.sha256(z.read(n)).hexdigest()[:16]
    z.close()
    return out


def snapshot_media(path):
    """全メディアのバイトをメモリ内へ保持する(保存前の原形の復元元)。"""
    z = zipfile.ZipFile(path)
    out = {n: z.read(n) for n in z.namelist() if n.startswith("xl/media/")}
    z.close()
    return out


def restore_media(local_path, snap):
    """保存で再圧縮されたメディアのバイトを保存前の内容へ戻す。"""
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


for key, B in BOOKS.items():
    act(f"===== {key} =====")
    XLSX, PDFP = B["xlsx"], B["pdfp"]
    R["books"][key] = {"sha_before": sha256(XLSX)}
    if not os.path.exists(B["backup"]):
        copy_vault(XLSX, B["backup"])
        act(f"G10前バックアップ作成 sha={sha256(B['backup'])[:16]}")
    assert sha256(B["backup"]) == R["books"][key]["sha_before"], "backup mismatch"

    local = os.path.join(PAGES, f"_{key}.xlsx")
    copy_vault(XLSX, local)

    # ---------- Phase A: 読み取り(頁数·引用ハッシュ·氏名走査·編集対象の裏付け) ----------
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    try:
        wb = app.Workbooks.Open(local, UpdateLinks=0, ReadOnly=True)
        sheet_names = [wb.Sheets(i).Name for i in range(1, wb.Sheets.Count + 1)]
        qh1, qn = quote_hash(wb, B["quote"])
        pre_cells, pre_shapes = scan_names(wb)
        for sheet, addr, pairs in B["edits"]:
            v = wb.Worksheets(sheet).Range(addr).MergeArea.Cells(1, 1).Value
            assert isinstance(v, str), f"target not text: {sheet}!{addr}"
            for old, _new in pairs:
                assert old in v, f"old substring missing: {sheet}!{addr}"
        wb.Close(SaveChanges=False)
    finally:
        try:
            app.Quit()
        except Exception:
            pass
    counts = export_all(local, sheet_names, tag=f"{key}a")
    media_snap = snapshot_media(local)
    R["books"][key].update({"sheets": len(sheet_names), "quote_cells": qn,
                            "pre_name_cells": sorted(f"{s}{a}" for s, a in pre_cells),
                            "pre_name_shapes": pre_shapes})
    act(f"Phase A ok (sheets={len(sheet_names)}, quote {qn}, pre name cells={len(pre_cells)}, shapes={sum(pre_shapes.values())})")

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
        n_edits = 0
        for sheet, addr, pairs in B["edits"]:
            c = wb.Worksheets(sheet).Range(addr).MergeArea.Cells(1, 1)
            v = c.Value
            assert isinstance(v, str)
            for old, new in pairs:
                assert old in v, f"old missing at edit: {sheet}!{addr}"
                v = v.replace(old, new)
            assert not any(n in v for n in NAMES), f"name remains: {sheet}!{addr}"
            c.Value = v
            n_edits += 1
        assert n_edits == B["expect_cells"], f"edit count {n_edits} != {B['expect_cells']}"
        wb.Save()
        wb.Close(SaveChanges=False)
    finally:
        try:
            app.Quit()
        except Exception:
            pass
    changed, added, removed = restore_media(local, media_snap)
    act(f"Phase B ok (edits {n_edits} cells, media restored {len(changed)}, +{len(added)} -{len(removed)})")

    # ---------- Phase C: 頁数·冊PDF·引用検証·氏名残存チェック ----------
    counts2 = export_all(local, sheet_names, with_book=True, tag=f"{key}b")
    assert counts2 == counts, f"pagination shifted: {counts2} vs {counts}"
    writer = PdfWriter()
    for name in sheet_names:
        for pg in PdfReader(os.path.join(PAGES, f"{key}b_{name}.pdf")).pages:
            writer.add_page(pg)
    book_local = os.path.join(PAGES, f"{key}_BOOK_assembled.pdf")
    with open(book_local, "wb") as f:
        writer.write(f)
    total = len(PdfReader(book_local).pages)
    assert total == sum(counts.values()), "book pages"

    app4 = win32.DispatchEx("Excel.Application")
    app4.Visible = False
    app4.DisplayAlerts = False
    try:
        wb4 = app4.Workbooks.Open(local, UpdateLinks=0, ReadOnly=True)
        qh3, _ = quote_hash(wb4, B["quote"])
        post_cells, post_shapes = scan_names(wb4)
        wb4.Close(SaveChanges=False)
    finally:
        app4.Quit()
    assert qh3 == qh1, "quote changed!"
    allowed = {(s, a) for (s, a) in B["allowed"]}
    extra = {(s, a) for (s, a) in post_cells if (s, a) not in allowed}
    assert not extra, f"unexpected name cells remain: {sorted(extra)}"
    assert post_shapes == pre_shapes, f"shape names changed: {post_shapes}"
    R["books"][key].update({"edits": n_edits, "total_pages": total,
                            "post_name_cells": sorted(f"{s}{a}" for s, a in post_cells),
                            "post_name_shapes": post_shapes,
                            "quote_ok": True, "media_restored": len(changed)})
    act(f"Phase C ok (total={total}, quote ok, name cells -> allowed {len(post_cells)}, shapes {sum(post_shapes.values())})")

    # ---------- 反映 ----------
    copy_vault(local, XLSX)
    copy_vault(book_local, PDFP)
    try:
        os.remove(local)
    except Exception:
        pass
    R["books"][key]["sha_after"] = sha256(XLSX)
    act(f"DONE {key} sha {R['books'][key]['sha_after'][:16]} ({total}p)")

with open(REP, "w", encoding="utf-8") as f:
    json.dump(R, f, ensure_ascii=False, indent=1)
act("ALL DONE")
