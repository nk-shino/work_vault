# -*- coding: utf-8 -*-
"""LNB管理手順書案_未承認.xlsx 実測probe (読み取り専用·保存なし)
変更リスト_LNB冊_20261102.md の実装前に実測値を確定する。
出力: scripts/probe_lnb_out.json
"""
import os, sys, json, hashlib, traceback

WORK = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
XLSX = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\LNB管理手順書案_未承認.xlsx"
OUT = os.path.join(WORK, "scripts", "probe_lnb_out.json")
EXPECT_SHA = "67b8cc54df23db2b41b8d27fb85246d4b77528f12b62eca489a740e8dba1ce03"
CRED = "申し送り(認証情報)"  # 一切読まない(メタデータのみ)

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def addr_str(obj):
    return str(obj.Address).replace("$", "")

def shape_rec(sh):
    try:
        tlc, brc = sh.TopLeftCell, sh.BottomRightCell
        tl = f"{tlc.Address}" if tlc is not None else None
        br = f"{brc.Address}" if brc is not None else None
    except Exception:
        tl = br = None
    return {
        "name": str(sh.Name), "id": int(sh.ID), "type": int(sh.Type),
        "tl": tl, "br": br,
        "top": round(float(sh.Top), 1), "left": round(float(sh.Left), 1),
        "w": round(float(sh.Width), 1), "h": round(float(sh.Height), 1),
    }

def sheet_meta(ws):
    ps = ws.PageSetup
    ur = ws.UsedRange
    breaks = []
    try:
        for i in range(1, int(ws.HPageBreaks.Count) + 1):
            pb = ws.HPageBreaks.Item(i)
            try:
                row = int(pb.Location.Row)
            except Exception:
                row = None
            try:
                typ = int(pb.Type)
            except Exception:
                typ = None
            breaks.append({"row": row, "type": typ})
    except Exception as e:
        breaks = [{"error": str(e)}]
    d = {
        "name": str(ws.Name),
        "visible": int(ws.Visible),
        "usedrange": addr_str(ur),
        "used_rows": int(ur.Rows.Count), "used_cols": int(ur.Columns.Count),
        "shapes": int(ws.Shapes.Count),
        "hpagebreaks": breaks,
        "pagesetup": {
            "orientation": int(ps.Orientation),
            "paper": int(ps.PaperSize),
            "zoom": ps.Zoom, "fit_w": ps.FitToPagesWide, "fit_h": ps.FitToPagesTall,
            "print_area": str(ps.PrintArea), "title_rows": str(ps.PrintTitleRows),
            "first_page": ps.FirstPageNumber,
            "margins_pt": {k: round(float(getattr(ps, k)), 2) for k in
                           ("LeftMargin", "RightMargin", "TopMargin", "BottomMargin",
                            "HeaderMargin", "FooterMargin")},
            "right_header": str(ps.RightHeader), "center_footer": str(ps.CenterFooter),
            "left_footer": str(ps.LeftFooter), "right_footer": str(ps.RightFooter),
        },
    }
    return d

def main():
    s = sha256(XLSX)
    print("SHA:", s)
    if s != EXPECT_SHA:
        raise SystemExit(f"SHA mismatch: {s}")
    o = {"sha": s, "sheets": [], "errors": []}

    import win32com.client as win32
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    try:
        wb = app.Workbooks.Open(XLSX, UpdateLinks=0, ReadOnly=True)
        o["sheet_order"] = [str(sh.Name) for sh in wb.Worksheets]
        o["sheet_count"] = int(wb.Worksheets.Count)
        wsmap = {str(sh.Name): sh for sh in wb.Worksheets}

        # ---- 全シート共通メタ(認証情報はページ設定のみ·UsedRange等は触れない) ----
        for name in o["sheet_order"]:
            ws = wsmap[name]
            try:
                if name == CRED:
                    ps = ws.PageSetup
                    o["sheets"].append({"name": name, "visible": int(ws.Visible),
                                        "shapes": int(ws.Shapes.Count),
                                        "pagesetup_only": "credential sheet - no range read",
                                        "orientation": int(ps.Orientation),
                                        "first_page": ps.FirstPageNumber})
                    continue
                o["sheets"].append(sheet_meta(ws))
            except Exception as e:
                o["errors"].append(f"{name}: meta {e}")

        # ---- 表紙: 図形inventory + nullセル ----
        try:
            ws = wsmap["表紙"]
            o["表紙_shapes"] = [shape_rec(ws.Shapes.Item(i)) for i in range(1, int(ws.Shapes.Count) + 1)]
            o["表紙_x1_u12"] = {"X1": ws.Range("X1").Value, "U12": ws.Range("U12").Value}
            o["表紙_merges_n"] = int(ws.Range("A1:Y36").MergeCells) if ws.Range("A1:Y36").MergeCells is not None else 0
        except Exception as e:
            o["errors"].append(f"表紙: {e}")

        # ---- 目次: 列幅·行高·結合·値 ----
        try:
            ws = wsmap["目次"]
            o["目次_cols"] = {c: round(float(ws.Columns(c).ColumnWidth), 2) for c in ("A", "B", "C", "D", "J", "K", "AY", "AZ")}
            o["目次_rowh"] = {r: round(float(ws.Rows(r).RowHeight), 1) for r in range(6, 23)}
            mrg = {}
            for r in range(6, 23):
                for c in ("A", "B", "C", "J"):
                    cell = ws.Range(f"{c}{r}")
                    if cell.MergeCells:
                        mrg[f"{c}{r}"] = addr_str(cell.MergeArea)
            o["目次_merges"] = mrg
            o["目次_vals"] = {a: ws.Range(a).Value for a in
                              ("A8", "C8", "B8", "J10", "J15", "J17", "J19", "A22", "B22", "C21", "C22")}
        except Exception as e:
            o["errors"].append(f"目次: {e}")

        # ---- 構成と管理情報: 画像·帯幅·行高·変更前文言 ----
        try:
            ws = wsmap["構成と管理情報"]
            o["構成_pics"] = [shape_rec(ws.Shapes.Item(i)) for i in range(1, int(ws.Shapes.Count) + 1)]
            o["構成_band_pt"] = {"A_AZ": round(float(ws.Range("A1:AZ1").Width), 1),
                                 "C_AZ": round(float(ws.Range("C1:AZ1").Width), 1)}
            o["構成_cap_rowh"] = {r: round(float(ws.Rows(r).RowHeight), 1) for r in (55, 80, 101)}
            o["構成_vals"] = {a: ws.Range(a).Value for a in
                              ("C8", "C9", "C14", "C17", "C55", "C80", "C101", "A103", "C104")}
        except Exception as e:
            o["errors"].append(f"構成: {e}")

        # ---- バックアップ: 画像 ----
        try:
            ws = wsmap["バックアップ"]
            o["bk_pics"] = [shape_rec(ws.Shapes.Item(i)) for i in range(1, int(ws.Shapes.Count) + 1)]
            o["bk_vals"] = {a: ws.Range(a).Value for a in ("C15", "C16")}
        except Exception as e:
            o["errors"].append(f"バックアップ: {e}")

        # ---- 相関図: 図形外接(bbox) ----
        try:
            ws = wsmap["相関図"]
            recs = [shape_rec(ws.Shapes.Item(i)) for i in range(1, int(ws.Shapes.Count) + 1)]
            o["相関図_count"] = len(recs)
            if recs:
                l = min(r["left"] for r in recs); t = min(r["top"] for r in recs)
                r_ = max(r["left"] + r["w"] for r in recs); b = max(r["top"] + r["h"] for r in recs)
                o["相関図_bbox_pt"] = {"left": round(l, 1), "top": round(t, 1),
                                       "right": round(r_, 1), "bottom": round(b, 1)}
            o["相関図_band_pt"] = {"A_AZ": round(float(ws.Range("A1:AZ1").Width), 1),
                                   "A_CG": round(float(ws.Range("A1:CG1").Width), 1)}
        except Exception as e:
            o["errors"].append(f"相関図: {e}")

        # ---- 変更前文言の照合用(残りのシート) ----
        checks = {
            "定期管理": ["C9"],
            "復旧": ["C13"],
            "管理体制": ["C16"],
            "異常時の対応": ["C19"],
            "チェックシート(月次・異常時)": ["C12"],
            "引用と部品照合": ["C11"],
            "用語": ["C31"],
        }
        o["vals_pre"] = {}
        for name, cells in checks.items():
            try:
                ws = wsmap[name]
                o["vals_pre"][name] = {a: ws.Range(a).Value for a in cells}
            except Exception as e:
                o["errors"].append(f"{name}: vals {e}")

        # ---- 要確認事項一覧: 設定状況 ----
        try:
            ws = wsmap["要確認事項一覧"]
            ps = ws.PageSetup
            o["要確認_ps"] = {
                "used": addr_str(ws.UsedRange),
                "title_rows": str(ps.PrintTitleRows),
                "right_header": repr(str(ps.RightHeader)),
                "center_footer": repr(str(ps.CenterFooter)),
                "margins_pt": {k: round(float(getattr(ps, k)), 2) for k in
                               ("LeftMargin", "RightMargin", "TopMargin", "BottomMargin")},
                "C9_head": str(ws.Range("C9").Value)[:60],
                "C47_head": str(ws.Range("C47").Value)[:60],
                "rowh_1_10": {r: round(float(ws.Rows(r).RowHeight), 1) for r in range(1, 11)},
            }
        except Exception as e:
            o["errors"].append(f"要確認: {e}")

        wb.Close(SaveChanges=False)
    finally:
        app.Quit()

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(o, f, ensure_ascii=False, indent=1)
    print("ERRORS:", o["errors"])
    print("sheets:", o.get("sheet_count"), o.get("sheet_order"))
    print("DONE ->", OUT)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
