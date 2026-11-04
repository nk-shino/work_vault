# -*- coding: utf-8 -*-
"""fix35_rev3_lnb.py — LNB冊 rev-3監査指摘の修正(エントリ40).

指摘1(P2): 要確認事項一覧 No.20(行28)の末尾が「2026-」で切れ続きが印字されない
           → 行高の調整のみ(セル文字列は変更しない)。
指摘2(利用者決定2026-11-04): 冊PDF再生成時に相関図_oldシートを印刷対象から外す
           (ワークブックの相関図_oldシート自体は不変·ページ設定も不変)。
指摘3: 認証情報一覧シートの印刷ヘッダーへ頁番号フィールド(&P)を追加
           (ページ設定レベルのみ·本文セルは一切読み取らない·変更しない)。
頁番号整合: 旧図除外で1頁減るため、相関図_oldより後のシートの FirstPageNumber を
           実測頁構成に合わせて調整(ページ設定レベル·申し送り(認証情報)は不触)。

方式: fix34_g10_rev2_pana.py の実績方式(TEMP作業コピー·メディアバイトスナップショット·
保存の都度メディア照合とzip復元·OneDrive排他6回再試行·短命COMインスタンス)。
セル文字列の変更は0件(Range.Replace 不使用·数式0ポリシー維持)。
安全I/O: セルのテキスト内容はディスクと標準出力へ出力しない(アドレス·数値·ブール·SHAのみ)。
認証情報を含むシート(申し送り(認証情報)·認証情報一覧)はページ設定の照会·設定のみで
セル値には触れない(ヘッダー文字列は &P の有無のブールのみ記録)。
"""
import os, sys, json, math, shutil, hashlib, time, zipfile

sys.stdout.reconfigure(encoding="utf-8")

BASE = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
VDIR = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
XLSX = os.path.join(VDIR, "LNB管理手順書案_未承認.xlsx")
PDFP = os.path.join(VDIR, "LNB管理手順書案_未承認.pdf")
WORK = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\rev3_lnb_work"
REP = os.path.join(BASE, "scripts", "fix35_rev3_lnb_report.json")

SHEET_YK = "要確認事項一覧"
ROW_FIX = 28            # No.20 の行
PITCH = 15.0            # 11pt 本文の行ピッチ(impl_lnb.py 実績値)
PAD = 4.1
SHEET_CRED_NEW = "認証信息一覧".replace("信息", "情報")   # &P を追加するシート(ページ設定のみ)
CRED = "申し送り(認証情報)"
OLD = "相関図_old"

ORDER_FULL = ["表紙", "目次", "用語", "構成と管理情報", "相関図①", "相関図②", "相関図③", OLD,
              "管理体制", "日次点検", "定期管理", "バックアップ", "復旧", "異常時の対応",
              "チェックシート(日次)", "チェックシート(月次・異常時)", "会議課題一覧(一時)",
              SHEET_YK, CRED, SHEET_CRED_NEW, "引用と部品照合"]
ORDER_NEW = [n for n in ORDER_FULL if n != OLD]   # 冊PDFの新構成(20シート)
EXPORT_SHEETS = [n for n in ORDER_NEW if n != CRED]  # 個別出力して頁数を数えるシート
AUTO = ("表紙", CRED)   # 番号を設定しないシート(表紙=番号なし·cred=自動)
QUOTE = [("引用と部品照合", ["C13", "C16", "C20"])]

R = {"book": "lnb", "kind": "rev3_audit_fixes", "phase": {}}


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


def media_map(src):
    if isinstance(src, dict):
        return {n: hashlib.sha256(b).hexdigest()[:16] for n, b in src.items()}
    return {n: hashlib.sha256(b).hexdigest()[:16] for n, b in snapshot_media(src).items()}


def restore_media(local_path, snap):
    after = media_map(local_path)
    before = media_map(snap)
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
    chk = media_map(local_path)
    assert chk == before, "media restore failed"
    return changed, added, removed


# ---------- impl_lnb.py 実績の行高計量(セル文字列はメモリ内のみ·出力しない) ----------
def units(s):
    return sum(1.0 if ord(ch) > 0x2E80 else 0.5 for ch in s)


def calc_lines(text, width_pt, size):
    per = max(4.0, width_pt / size)
    n = 0
    for seg in str(text).split("\n"):
        n += max(1, math.ceil(units(seg) / per - 1e-9))
    return n


def colw_px(w):
    return int(((256 * w + 18) / 256) * 7) + 5


def quote_hash(wb):
    h = hashlib.sha256()
    n = 0
    for sheet, cells in QUOTE:
        ws = wb.Worksheets(sheet)
        for a in cells:
            h.update(ws.Range(a).Text.encode("utf-8"))
            n += 1
    return h.hexdigest()[:16], n


def page_setup_inventory(wb):
    """FirstPageNumber と右ヘッダーを照会する。認証情報を含むシートのヘッダーは
    文字列を保持せず &P の有無(ブール)のみ記録する。"""
    inv = {}
    for i in range(1, wb.Worksheets.Count + 1):
        ws = wb.Worksheets(i)
        ps = ws.PageSetup
        fpn = ps.FirstPageNumber
        nm = ws.Name
        if "認証情報" in nm:
            inv[nm] = {"fpn": int(fpn) if fpn is not None else None,
                       "rh_has_P": "&P" in str(ps.RightHeader or "")}
        else:
            inv[nm] = {"fpn": int(fpn) if fpn is not None else None,
                       "rh": str(ps.RightHeader or "")}
    return inv


def export_sheets(local_path, sheet_names, tag, outdir=None):
    import win32com.client as win32
    from pypdf import PdfReader
    outdir = outdir or WORK
    app2 = win32.DispatchEx("Excel.Application")
    app2.Visible = False
    app2.DisplayAlerts = False
    try:
        wb2 = app2.Workbooks.Open(local_path, UpdateLinks=0, ReadOnly=True)
        counts = {}
        for name in sheet_names:
            p = os.path.join(outdir, f"{tag}_{name}.pdf")
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
    """相関図_old を非表示にした状態で冊エクスポートする(非表示はメモリ上のみ·保存しない)。"""
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


def open_rw(path):
    import win32com.client as win32
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    wb = app.Workbooks.Open(path, UpdateLinks=0, ReadOnly=False)
    try:
        wb.AutoSaveOn = False
    except Exception:
        pass
    return app, wb


def close_rw(app, wb):
    try:
        wb.Close(SaveChanges=False)
    except Exception:
        pass
    try:
        app.Quit()
    except Exception:
        pass


def set_fpn_with_retry(ws, fpn):
    for attempt in range(3):
        try:
            ws.PageSetup.FirstPageNumber = fpn
            return
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2.0)


def set_rh_with_retry(ws, value):
    for attempt in range(3):
        try:
            ws.PageSetup.RightHeader = value
            return
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2.0)


def main():
    os.makedirs(WORK, exist_ok=True)
    for f in os.listdir(WORK):
        os.remove(os.path.join(WORK, f))
    import win32com.client as win32  # noqa
    from pypdf import PdfReader, PdfWriter

    # ---------- Phase 0: 作業コピーとメディアスナップショット ----------
    R["sha_before"] = sha256(XLSX)
    assert R["sha_before"].startswith("89599282386ca21f"), "vault xlsx is not the audited revision"
    local = os.path.join(WORK, "_rev3.xlsx")
    copy_vault(XLSX, local)
    media_snap = snapshot_media(local)
    R["media_count"] = len(media_snap)
    act(f"Phase 0 ok (sha_before {R['sha_before'][:16]}, media {len(media_snap)})")

    # ---------- Phase A: 読み取り(行高·ページ設定·引用ハッシュ) ----------
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    try:
        wb = app.Workbooks.Open(local, UpdateLinks=0, ReadOnly=True)
        names = [wb.Sheets(i).Name for i in range(1, wb.Sheets.Count + 1)]
        assert names == ORDER_FULL, f"unexpected sheet order: {names}"
        ws = wb.Worksheets(SHEET_YK)
        marea = str(ws.Range(f"C{ROW_FIX}").MergeArea.Address).replace("$", "")
        assert marea.upper() == "C28:AZ28", f"unexpected merge area {marea}"
        cols = [chr(65 + i) if i < 26 else "A" + chr(65 + i - 26) for i in range(52)]
        i1, i2 = cols.index("C"), cols.index("AZ")
        width_pt = sum(colw_px(float(ws.Columns[cols[i]].ColumnWidth)) for i in range(i1, i2 + 1)) * 0.75
        yk = {}
        for r in (9, 22, 27, 28, 29):
            yk[r] = {"h": round(float(ws.Rows(r).RowHeight), 2)}
        v28 = ws.Range("C28").MergeArea.Cells(1, 1).Value
        assert isinstance(v28, str) and v28, "C28 empty"
        n28 = calc_lines(v28, width_pt, 11.0)
        yk[28].update({"units": units(v28), "width_pt": round(width_pt, 1),
                       "calc_lines": n28, "need_h": round(n28 * PITCH + PAD, 2)})
        for r in (9, 22):  # 参考(修正対象外の同傾向行·記録のみ)
            vr = ws.Range(f"C{r}").MergeArea.Cells(1, 1).Value
            if isinstance(vr, str) and vr:
                yk[r]["calc_lines"] = calc_lines(vr, width_pt, 11.0)
                yk[r]["need_h"] = round(yk[r]["calc_lines"] * PITCH + PAD, 2)
        breaks = []
        for hb in ws.HPageBreaks:
            breaks.append(int(hb.Location.Row))
        qh1, qn = quote_hash(wb)
        psi = page_setup_inventory(wb)
        R["phase"]["A"] = {
            "yk_rows": {str(k): v for k, v in yk.items()},
            "hpagebreaks_rows": breaks,
            "quote_cells": qn,
            "fpn_before": {k: v["fpn"] for k, v in psi.items()},
            "rh_before_noncred": {k: v["rh"] for k, v in psi.items() if "rh" in v},
            "rh_has_P_cred": {k: v.get("rh_has_P") for k, v in psi.items() if "認証情報" in k},
        }
        wb.Close(SaveChanges=False)
    finally:
        try:
            app.Quit()
        except Exception:
            pass
    act(f"Phase A ok (row28 h={yk[28]['h']} need={yk[28]['need_h']} lines={yk[28]['calc_lines']}, "
        f"breaks={breaks}, quote {qn})")

    # ---------- Phase B1: 行高の修正(表示レイアウトのみ·セル文字列は不変) ----------
    new_h = yk[28]["need_h"]
    assert new_h > yk[28]["h"], f"row28 height {yk[28]['h']} already >= need {new_h}"
    app, wb = open_rw(local)
    try:
        ws = wb.Worksheets(SHEET_YK)
        v_pre = ws.Range("C28").MergeArea.Cells(1, 1).Value
        assert isinstance(v_pre, str) and v_pre
        h_pre = round(float(ws.Rows(ROW_FIX).RowHeight), 2)
        ws.Rows(ROW_FIX).RowHeight = new_h
        h_post = round(float(ws.Rows(ROW_FIX).RowHeight), 2)
        v_post = ws.Range("C28").MergeArea.Cells(1, 1).Value
        # セル文字列が1字も変わっていないことの検証(メモリ内照合·出力なし)
        assert v_post == v_pre and h_post == new_h and h_pre == yk[28]["h"], "row28 edit verify failed"
        wb.Save()
    finally:
        close_rw(app, wb)
    changed, added, removed = restore_media(local, media_snap)
    R["phase"]["B1"] = {"row28_height": {"before": yk[28]["h"], "after": h_post},
                        "cell_text_unchanged": True, "media_restored": len(changed)}
    act(f"Phase B1 ok (row28 {yk[28]['h']} -> {h_post}, media restored {len(changed)})")

    # ---------- Phase B2: 頁数の実測(修正後の改ページ·credは冊出力から数える) ----------
    counts = export_sheets(local, EXPORT_SHEETS, tag="a")
    local_hide = os.path.join(WORK, "_rev3_hideold.xlsx")
    shutil.copy2(local, local_hide)
    book_full_a = os.path.join(WORK, "a_BOOK_hiddenold.pdf")
    export_book_hidden_old(local_hide, book_full_a)
    n_full = len(PdfReader(book_full_a).pages)
    cred_pages = n_full - sum(counts.values())
    assert cred_pages >= 1, f"cred pages calc {cred_pages} (full {n_full}, others {sum(counts.values())})"
    R["phase"]["B2"] = {"pages": counts, "full_hiddenold_pages": n_full, "cred_pages": cred_pages}
    act(f"Phase B2 ok (others {counts}, cred={cred_pages}, full={n_full})")

    # ---------- Phase B3: 採番の再設定(旧図除外後の実頁構成)+ 認証情報一覧の&P ----------
    acc = 1
    numbering = {}
    cnt = dict(counts)
    cnt[CRED] = cred_pages
    for name in ORDER_NEW:
        if name in AUTO:
            acc += cnt[name]
            continue
        numbering[name] = acc
        acc += cnt[name]
    total_new = sum(cnt[n] for n in ORDER_NEW)
    R["phase"]["B3"] = {"numbering_new": numbering, "total_booklet": total_new}
    act(f"Phase B3 numbering {numbering} total={total_new}")
    app, wb = open_rw(local)
    try:
        psi2 = page_setup_inventory(wb)
        fpn_apply = {}
        for name, fpn in numbering.items():
            cur = psi2[name]["fpn"]
            if cur != fpn:
                set_fpn_with_retry(wb.Worksheets(name), fpn)
                fpn_apply[name] = {"before": cur, "after": fpn}
        # 認証情報一覧: 右ヘッダーへ頁番号フィールドを追加(他シートと同一様式)
        rh_ref = psi2["引用と部品照合"].get("rh", "")
        assert "&P" in rh_ref, "reference header has no &P"
        assert not psi2[SHEET_CRED_NEW]["rh_has_P"], f"{SHEET_CRED_NEW} already has &P"
        ws_cn = wb.Worksheets(SHEET_CRED_NEW)
        set_rh_with_retry(ws_cn, rh_ref)
        rh_post = str(ws_cn.PageSetup.RightHeader or "")
        assert "&P" in rh_post, "header &P missing after set"
        # 本文セルには触れていないことの署名(使用範囲のアドレスのみ照会·値は読まない)
        used_addr = str(ws_cn.UsedRange.Address)
        wb.Save()
    finally:
        close_rw(app, wb)
    changed, added, removed = restore_media(local, media_snap)
    R["phase"]["B3_apply"] = {"fpn_changed": fpn_apply,
                              "cred_new_header_set": True,
                              "cred_new_usedrange_addr": used_addr,
                              "media_restored2": len(changed)}
    act(f"Phase B3 ok (fpn changed {len(fpn_apply)}, header set, media restored {len(changed)})")

    # ---------- Phase C1: 再実測(採番後の頁数不変の確認) ----------
    counts2 = export_sheets(local, EXPORT_SHEETS, tag="b")
    assert counts2 == counts, f"pagination shifted: {counts2} vs {counts}"
    shutil.copy2(local, local_hide)  # 採番後の状態で冊出力を取り直す
    book_full_b = os.path.join(WORK, "b_BOOK_hiddenold.pdf")
    export_book_hidden_old(local_hide, book_full_b)
    n_full_b = len(PdfReader(book_full_b).pages)
    cred_pages_b = n_full_b - sum(counts2.values())
    assert n_full_b == n_full and cred_pages_b == cred_pages, \
        f"full export shifted: {n_full_b}/{cred_pages_b} vs {n_full}/{cred_pages}"
    act("Phase C1 ok (pagination stable)")

    # ---------- Phase C2: 冊PDFの組み立て(相関図_old を除く·cred頁は冊出力から抽出) ----------
    offset = sum(counts2[n] for n in ORDER_NEW[:ORDER_NEW.index(CRED)])
    writer = PdfWriter()
    for name in ORDER_NEW:
        if name == CRED:
            for i in range(offset, offset + cred_pages):
                writer.add_page(PdfReader(book_full_b).pages[i])
        else:
            for pg in PdfReader(os.path.join(WORK, f"b_{name}.pdf")).pages:
                writer.add_page(pg)
    book_local = os.path.join(WORK, "BOOK_rev3.pdf")
    with open(book_local, "wb") as f:
        writer.write(f)
    total = len(PdfReader(book_local).pages)
    assert total == total_new, "booklet page count mismatch"
    R["phase"]["C2"] = {"booklet_pages": total, "cred_offset": offset + 1, "cred_pages": cred_pages}
    act(f"Phase C2 ok (booklet {total}p, cred at {offset + 1}-{offset + cred_pages})")

    # ---------- Phase C3: 引用区間の不変検証·ページ設定の不変検証·メディア最終照合 ----------
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    try:
        wb = app.Workbooks.Open(local, UpdateLinks=0, ReadOnly=True)
        qh3, _ = quote_hash(wb)
        assert qh3 == qh1, "quote changed!"
        psi3 = page_setup_inventory(wb)
        wb.Close(SaveChanges=False)
    finally:
        try:
            app.Quit()
        except Exception:
            pass
    assert psi3[OLD]["fpn"] == psi[OLD]["fpn"], "old sheet page setup changed"
    assert psi3[CRED]["fpn"] == psi[CRED]["fpn"], "cred page setup changed"
    assert psi3[SHEET_CRED_NEW].get("rh_has_P"), "cred-new header lost"
    final_media = media_map(local)
    snap_map = media_map(media_snap)
    assert final_media == snap_map, "media mismatch after restore"
    R["phase"]["C3"] = {"quote_ok": True, "old_fpn_unchanged": psi3[OLD]["fpn"],
                        "cred_fpn_unchanged": psi3[CRED]["fpn"], "media_ok": True}
    act("Phase C3 ok (quote ok, old/cred page setup unchanged, media ok)")

    # ---------- 反映 ----------
    copy_vault(local, XLSX)
    copy_vault(book_local, PDFP)
    R["sha_after_xlsx"] = sha256(XLSX)
    R["sha_after_pdf"] = sha256(PDFP)
    R["pages"] = total
    R["sheet_pages_new"] = {n: cnt[n] for n in ORDER_NEW}
    with open(REP, "w", encoding="utf-8") as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    act(f"DONE xlsx {R['sha_after_xlsx'][:16]} pdf {R['sha_after_pdf'][:16]} ({total}p)")


if __name__ == "__main__":
    main()
