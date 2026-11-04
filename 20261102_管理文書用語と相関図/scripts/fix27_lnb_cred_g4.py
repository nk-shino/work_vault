# -*- coding: utf-8 -*-
"""fix27_lnb_cred_g4.py — 計画§9 G4: 申し送り(認証情報)シートの空頁削除(エントリ28)。

- 空行(値·罫線·図形のいずれもない行)を検査付きで全削除し(計画G4原文どおり·
  ユーザー承認 2026-11-04)、印刷範囲を実態まで縮小する。下の行から順に削除し索引を安定させる。
- セルの値·罫線·図形·印刷設定(余白·ヘッダー·フッター·フィット)は変更しない。
  整合検証は「値の並び(行順)·罫線ブロックのサイズ列·図形の行位置」の一致で行う
  (行番号は空行削除によりシフトする)。
- 申し送りシートのセル値は一切出力しない(報告書は行番号と個数のみ)。
- cred 頁数を実測(一時PDFは Temp 配下で作成·計上後削除)→ 引用 FirstPageNumber 再設定
  →冊PDF再構築(個別16シート+cred頁スポット+引用)。
"""
import os, sys, json, traceback, hashlib

WORK = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
XLSX = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\LNB管理手順書案_未承認.xlsx"
VAULT_PDF = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\LNB管理手順書案_未承認.pdf"
PAGES_DIR = os.path.join(WORK, "scripts", "tmp_pages_lnb2")
REPORT = os.path.join(WORK, "scripts", "fix27_lnb_cred_g4_report.json")
TMPDIR = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code"
BACKUP = os.path.join(WORK, "backup_20261102", "LNB管理手順書案_未承認_G4前_20261104.xlsx")
CRED = "申し送り(認証情報)"
NCOLS = 52  # A..AZ

ORDER17 = ["表紙", "目次", "用語", "構成と管理情報", "相関図", "相関図_old", "管理体制",
           "日次点検", "定期管理", "バックアップ", "復旧", "異常時の対応",
           "チェックシート(日次)", "チェックシート(月次・異常時)", "会議課題一覧(一時)",
           "要確認事項一覧", "引用と部品照合"]
# fix27_lnb_margins.py 実測値(前回確定分)
PREV_COUNTS = {"表紙": 1, "目次": 1, "用語": 2, "構成と管理情報": 4, "相関図": 1, "相関図_old": 1,
               "管理体制": 1, "日次点検": 1, "定期管理": 1, "バックアップ": 4, "復旧": 1,
               "異常時の対応": 1, "チェックシート(日次)": 1, "チェックシート(月次・異常時)": 1,
               "会議課題一覧(一時)": 2, "要確認事項一覧": 2, "引用と部品照合": 1}
CRED_PAGES_BEFORE = 6

REP = {"actions": [], "probe": {}, "delete": {}, "verify": {}, "numbering": {},
       "book": {}, "sha": None, "errors": []}


def act(msg):
    REP["actions"].append(msg)
    print("[act]", msg, flush=True)


def count_values(ws, r):
    rng = ws.Range(ws.Cells(r, 1), ws.Cells(r, NCOLS))
    return int(ws.Application.WorksheetFunction.CountA(rng))


def row_has_border(ws, r):
    rng = ws.Range(ws.Cells(r, 1), ws.Cells(r, NCOLS))
    uncertain = False
    for b in (7, 8, 9, 10, 11):  # 左右上下+範囲内縦線
        try:
            ls = rng.Borders(b).LineStyle
        except Exception:
            uncertain = True
            break
        if ls is None:
            uncertain = True
            break
        if ls != -4142:  # xlNone
            return True
    if not uncertain:
        return False
    for c in range(1, NCOLS + 1):
        cell = ws.Cells(r, c)
        for b in (7, 8, 9, 10):
            try:
                ls = cell.Borders(b).LineStyle
            except Exception:
                continue
            if ls is not None and ls != -4142:
                return True
    return False


def border_signature(ws, r):
    """罫線行の署名: 各辺(左7·上8·下9·右10)について罫線のあるセル数(内容は出力しない)。"""
    sig = {}
    for b in (7, 8, 9, 10):
        n = 0
        for c in range(1, NCOLS + 1):
            try:
                ls = ws.Cells(r, c).Borders(b).LineStyle
            except Exception:
                continue
            if ls is not None and ls != -4142:
                n += 1
        sig[b] = n
    return sig


def shape_rows(ws):
    out = []
    for i in range(1, ws.Shapes.Count + 1):
        sh = ws.Shapes(i)
        out.append({"top": int(sh.TopLeftCell.Row), "bottom": int(sh.BottomRightCell.Row)})
    return out


def scan_rows(ws, r_from, r_to):
    """行番号と個数のみを返す(セル値は出力しない)。罫線行には署名(各辺の罫線セル数)を付す。"""
    vals, borders, sigs = {}, [], {}
    total = 0
    for r in range(r_from, r_to + 1):
        v = count_values(ws, r)
        if v:
            vals[r] = v
            total += v
        if row_has_border(ws, r):
            borders.append(r)
            sigs[r] = border_signature(ws, r)
    return {"value_rows": vals, "value_cells_total": total, "border_rows": borders, "border_sigs": sigs}


def group_blocks(rows):
    """連続行をブロックへ group 化: [57,58,59,111,112,113] -> [[57,58,59],[111,112,113]]"""
    blocks = []
    for r in sorted(rows):
        if blocks and r == blocks[-1][-1] + 1:
            blocks[-1].append(r)
        else:
            blocks.append([r])
    return blocks


def blocks_str(rows):
    return " ".join(f"{b[0]}-{b[-1]}" if len(b) > 1 else str(b[0]) for b in group_blocks(rows))


def sha16(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def main():
    probe_only = "--probe" in sys.argv
    os.makedirs(PAGES_DIR, exist_ok=True)
    os.makedirs(TMPDIR, exist_ok=True)
    import win32com.client as win32
    try:
        from pypdf import PdfReader, PdfWriter
    except Exception:
        from PyPDF2 import PdfReader, PdfWriter

    # ---------- Phase A: 読み取り専用プローブ ----------
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    wb = None
    try:
        wb = app.Workbooks.Open(XLSX, UpdateLinks=0, ReadOnly=True)
        ws = wb.Worksheets(CRED)
        wsmap_all = {sh.Name: sh for sh in wb.Worksheets}
        assert len(wsmap_all) == 18, f"sheet count {len(wsmap_all)}"
        ur = ws.UsedRange
        max_row = int(ur.Row + ur.Rows.Count) - 1
        pa_before = str(ws.PageSetup.PrintArea or "")
        REP["probe"]["used_range"] = str(ur.Address)
        REP["probe"]["max_row"] = max_row
        REP["probe"]["print_area_before"] = pa_before
        act(f"PROBE UsedRange={ur.Address} max_row={max_row} print_area={pa_before}")

        stats = scan_rows(ws, 1, max_row)
        REP["probe"].update(stats)
        REP["probe"]["shapes"] = shape_rows(ws)
        act(f"PROBE value_cells_total={stats['value_cells_total']} "
            f"value_rows={sorted(stats['value_rows'])} border_rows={stats['border_rows']} "
            f"shapes={len(REP['probe']['shapes'])}")
        if REP["probe"]["shapes"]:
            shape_max = max(s["bottom"] for s in REP["probe"]["shapes"])
        else:
            shape_max = 0
        r0 = max(max(stats["value_rows"]), max(stats["border_rows"]) if stats["border_rows"] else 0, shape_max)
        REP["probe"]["last_content_row"] = r0
        act(f"PROBE last_content_row={r0}")

        # F1適用状態の維持確認(fix27_lnb_margins_report.json の after_pt と突合)
        try:
            with open(os.path.join(WORK, "scripts", "fix27_lnb_margins_report.json"), encoding="utf-8") as f:
                prev = json.load(f)
            mism = []
            for name, rec in prev.get("margins", {}).items():
                if not isinstance(rec, dict) or rec.get("untouched") or "after_pt" not in rec:
                    continue
                cur = {k: round(float(getattr(wsmap_all[name].PageSetup, k + "Margin")), 2)
                       for k in rec["after_pt"]}
                if cur != rec["after_pt"]:
                    mism.append({"sheet": name, "expected": rec["after_pt"], "current": cur})
            REP["probe"]["margin_check"] = {"mismatches": mism, "ok": not mism}
            act(f"MARGIN CHECK vs fix27 report: {'OK' if not mism else 'MISMATCH ' + json.dumps(mism, ensure_ascii=False)}")
        except Exception as e:
            REP["probe"]["margin_check"] = {"error": str(e)}
            act(f"MARGIN CHECK skipped: {e}")

        if probe_only:
            act("PROBE-ONLY: no changes made")
            wb.Close(SaveChanges=False)
            wb = None
            with open(REPORT, "w", encoding="utf-8") as f:
                json.dump(REP, f, ensure_ascii=False, indent=1)
            print("DONE-PROBE", flush=True)
            return
        # バックアップの存在と一致を確認してから変更へ進む
        assert os.path.exists(BACKUP), f"backup missing: {BACKUP}"
        assert sha16(BACKUP) == sha16(XLSX), "backup sha mismatch"
        act(f"BACKUP ok: {BACKUP}")
        wb.Close(SaveChanges=False)
        wb = None

        # ---------- Phase B: 編集(読み書き) ----------
        wb = app.Workbooks.Open(XLSX, UpdateLinks=0, ReadOnly=False)
        try:
            wb.AutoSaveOn = False
        except Exception:
            pass
        ws = wb.Worksheets(CRED)

        # 再検査(変更直前の全行再スキャン)
        st_fresh = scan_rows(ws, 1, max_row)
        shapes_now = shape_rows(ws)
        assert st_fresh["value_cells_total"] == REP["probe"]["value_cells_total"], "value drift"
        assert st_fresh["border_rows"] == REP["probe"]["border_rows"], "border drift"
        assert shapes_now == REP["probe"]["shapes"], "shape drift"
        act("RECHECK ok (values/borders/shapes unchanged since probe)")

        # 空行 = 値0·罫線なし·図形の行範囲外
        shape_block = set()
        for s in shapes_now:
            shape_block.update(range(s["top"], s["bottom"] + 1))
        empty_rows = [r for r in range(1, max_row + 1)
                      if r not in st_fresh["value_rows"] and r not in st_fresh["border_rows"]
                      and r not in shape_block]
        REP["delete"]["empty_blocks"] = blocks_str(empty_rows)
        REP["delete"]["empty_count"] = len(empty_rows)
        act(f"EMPTY ROWS: {len(empty_rows)} rows ({REP['delete']['empty_blocks']})")

        # 下の行から順に削除(索引安定·Shift=上)
        for r in reversed(empty_rows):
            ws.Rows(r).Delete(-4162)
        act(f"DELETED {len(empty_rows)} empty rows")

        # 新実態の最終行
        kept = sorted(set(st_fresh["value_rows"]) | set(st_fresh["border_rows"]) | shape_block)
        new_r0 = len(kept)  # 全空行削除後、 kept 行は 1..len(kept) に圧縮される
        pa_after = f"$A$1:$AZ${new_r0}"
        ws.PageSetup.PrintArea = pa_after
        REP["delete"].update({"kept_rows_before": len(kept), "print_area_after": pa_after})
        act(f"PRINTAREA {pa_before or '(auto)'} -> {pa_after}")
        wb.Save()
        act("SAVED (G4 trim)")

        # ---------- 整合検査(値の並び·罫線署名の並び·図形の保全) ----------
        st3 = scan_rows(ws, 1, new_r0 + 5)  # 余裕をもって走査
        st3_rows = {r: v for r, v in st3["value_rows"].items() if r <= new_r0}
        st3_borders = [r for r in st3["border_rows"] if r <= new_r0]
        sh3 = shape_rows(ws)
        before_seq = [st_fresh["value_rows"][r] for r in sorted(st_fresh["value_rows"])]
        after_seq = [st3_rows[r] for r in sorted(st3_rows)]
        before_sigs = [st_fresh["border_sigs"][r] for r in st_fresh["border_rows"]]
        after_sigs = [st3["border_sigs"][r] for r in st3_borders]
        REP["verify"] = {
            "value_cells_total": sum(st3_rows.values()),
            "value_seq_before": before_seq, "value_seq_after": after_seq,
            "border_rows_before": st_fresh["border_rows"], "border_rows_after": st3_borders,
            "border_sigs_before": before_sigs, "border_sigs_after": after_sigs,
            "shapes_before": REP["probe"]["shapes"], "shapes_after": sh3,
        }
        # 不変量: 値セル数と行順の個数列·罫線行数と署名の並び(空行削除により行番号はシフト·
        # 隣接した罫線ブロックの合体はあり得るためブロック構造は不変量としない)
        ok_vals = (sum(st3_rows.values()) == REP["probe"]["value_cells_total"]) and (before_seq == after_seq)
        ok_borders = (len(st3_borders) == len(st_fresh["border_rows"])) and (after_sigs == before_sigs)
        ok_shapes = sh3 == REP["probe"]["shapes"]
        REP["verify"]["ok"] = bool(ok_vals and ok_borders and ok_shapes)
        act(f"VERIFY values={ok_vals} borders={ok_borders} shapes={ok_shapes}")
        assert REP["verify"]["ok"], f"integrity check failed: {json.dumps(REP['verify'], ensure_ascii=False)}"

        # ---------- cred 頁数実測(一時PDF·計上後削除) ----------
        cred_pdf = os.path.join(TMPDIR, "cred_g4_tmp.pdf")
        ws.ExportAsFixedFormat(0, cred_pdf, 0, True, False)
        cred_pages = len(PdfReader(cred_pdf).pages)
        os.remove(cred_pdf)
        REP["book"]["cred_pages"] = cred_pages
        act(f"CRED PAGES: {CRED_PAGES_BEFORE} -> {cred_pages} (temp pdf deleted)")

        # ---------- 引用の頁番号 ----------
        page = 1
        for name in ORDER17[:16]:
            page += PREV_COUNTS[name]
        wsmap = {sh.Name: sh for sh in wb.Worksheets}
        assert len(wsmap) == 18, f"sheet count {len(wsmap)}"
        wsmap["引用と部品照合"].PageSetup.FirstPageNumber = page + cred_pages
        REP["numbering"]["引用と部品照合"] = page + cred_pages
        wb.Save()
        act(f"SAVED (pass3: 引用 FirstPageNumber={page + cred_pages})")

        # ---------- 引用の再出力(印字頁番号の更新) ----------
        q_pdf = os.path.join(PAGES_DIR, "引用と部品照合.pdf")
        wsmap["引用と部品照合"].ExportAsFixedFormat(0, q_pdf, 0, True, False)
        q_pages = len(PdfReader(q_pdf).pages)
        assert q_pages == PREV_COUNTS["引用と部品照合"], f"引用 pages {q_pages}"
        act(f"RE-EXPORT 引用と部品照合.pdf ({q_pages}p)")

        # ---------- 冊PDF再構築 ----------
        wb.ExportAsFixedFormat(0, VAULT_PDF, 0, True, False)
        bookrd = PdfReader(VAULT_PDF)
        book_pages = len(bookrd.pages)
        # page=credの開始頁番号(=先頭16シートの頁数+1)のため冊頁数は (page-1)+cred+引用
        expect = (page - 1) + cred_pages + q_pages
        assert book_pages == expect, f"book {book_pages} != expect {expect}"
        offset = page - 1  # 先頭16シートの合計頁(0始まり)
        writer = PdfWriter()
        for name in ORDER17[:16]:
            p = os.path.join(PAGES_DIR, f"{name}.pdf")
            assert os.path.exists(p), f"missing {p}"
            for pg in PdfReader(p).pages:
                writer.add_page(pg)
        for i in range(offset, offset + cred_pages):
            writer.add_page(bookrd.pages[i])
        for pg in PdfReader(q_pdf).pages:
            writer.add_page(pg)
        with open(VAULT_PDF, "wb") as f:
            writer.write(f)
        final_pages = len(PdfReader(VAULT_PDF).pages)
        assert final_pages == expect, f"merged {final_pages} != {expect}"
        REP["book"]["pages"] = final_pages
        act(f"BOOK -> {VAULT_PDF} ({final_pages}p = style{page - 1} + cred{cred_pages} + 引用{q_pages})")

        wb.Close(SaveChanges=False)
        wb = None
    except Exception:
        if wb is not None:
            try:
                wb.Close(SaveChanges=False)
            except Exception:
                pass
        raise
    finally:
        app.Quit()

    REP["sha"] = sha16(XLSX)
    act(f"SHA {REP['sha']}")
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(REP, f, ensure_ascii=False, indent=1)
    print("DONE", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        try:
            with open(REPORT, "w", encoding="utf-8") as f:
                json.dump(REP, f, ensure_ascii=False, indent=1)
        except Exception:
            pass
        sys.exit(1)
