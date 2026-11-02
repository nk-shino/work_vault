# -*- coding: utf-8 -*-
"""COM probe: 原本Pana冊 + 前例適用ファイルのレイアウト実測(読み取り専用・保存なし)."""
import json, sys
import win32com.client as wc
import pythoncom

ORIG = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\Pana-CIM管理手順書案_未承認.xlsx"
APPL = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261029_管理手順書_5-7章_デザイン適用\管理手順書_5-7章_デザイン適用_20261029.xlsx"

out = {}

def col_info(ws, last_col_letter="AZ"):
    widths = {}
    for ci in range(1, 53):
        c = ws.Cells(1, ci)
        letter = c.Address.split("$")[1] if "$" in c.Address else c.Address
        widths[letter] = round(float(c.ColumnWidth), 3)
    return widths

def sheet_print(ws):
    ps = ws.PageSetup
    return {
        "orientation": ps.Orientation, "paper": ps.PaperSize,
        "fit": ps.Zoom == False, "fitW": ps.FitToPagesWide, "fitH": ps.FitToPagesTall,
        "zoom": ps.Zoom,
        "margins": [round(float(x), 4) for x in (ps.LeftMargin, ps.RightMargin, ps.TopMargin, ps.BottomMargin, ps.HeaderMargin, ps.FooterMargin)],
        "print_area": ps.PrintArea, "print_title_rows": ps.PrintTitleRows,
        "first_page": ps.FirstPageNumber,
        "footer_L": ps.LeftFooter, "footer_C": ps.CenterFooter, "footer_R": ps.RightFooter,
        "header_L": ps.LeftHeader, "header_C": ps.CenterHeader, "header_R": ps.RightHeader,
        "center_h": bool(ps.CenterHorizontally), "center_v": bool(ps.CenterVertically),
    }

def merges_below(ws, last_row=400):
    res = []
    for m in ws.UsedRange.MergeCells and [] or []:
        pass
    try:
        n = ws.UsedRange.MergeArea is not None
    except Exception:
        pass
    # iterate MergeCells via SpecialCells is unreliable; use ws.Range.MergeCells loop over known areas
    return res

def used_and_merges(ws):
    ur = ws.UsedRange
    info = {"used_row": ur.Row, "used_col": ur.Column, "rows": ur.Rows.Count, "cols": ur.Columns.Count}
    # merged ranges: loop cells is slow; use MergeCells on UsedRange? Instead scan via rng.MergeArea of row starts
    return info

def row_heights(ws, rows):
    return {r: round(float(ws.Rows(r).RowHeight), 2) for r in rows}

def cell_style(ws, addr):
    c = ws.Range(addr)
    f = c.Font
    b = c.Borders(7)  # xlEdgeLeft
    return {
        "addr": addr, "value": (str(c.Value)[:24] if c.Value is not None else None),
        "font": f.Name, "size": float(f.Size), "bold": bool(f.Bold),
        "color": int(f.Color) if f.Color is not None and isinstance(f.Color, int) else f.Color,
        "interior": int(c.Interior.Color) if c.Interior.ColorIndex != -4142 else None,
        "pattern": int(c.Interior.Pattern),
        "left_border": (b.LineStyle, int(b.Color), b.Weight) if b.LineStyle and b.LineStyle != -4142 else None,
        "wrap": bool(c.WrapText), "ha": int(c.HorizontalAlignment), "va": int(c.VerticalAlignment),
        "merge_area": c.MergeArea.Address,
        "row_h": round(float(c.RowHeight), 2),
    }

def shapes_of(ws, limit=40):
    res = []
    for i, sh in enumerate(ws.Shapes):
        if i >= limit:
            res.append({"_truncated": True}); break
        d = {"name": sh.Name, "type": int(sh.Type),
             "l": round(float(sh.Left), 1), "t": round(float(sh.Top), 1),
             "w": round(float(sh.Width), 1), "h": round(float(sh.Height), 1)}
        try:
            if sh.TextFrame2.HasText:
                d["text"] = sh.TextFrame2.TextRange.Text[:30].replace("\r", "\\r")
        except Exception:
            pass
        res.append(d)
    return res

def main():
    pythoncom.CoInitialize()
    app = wc.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    try:
        # ---- original ----
        wb = app.Workbooks.Open(ORIG, UpdateLinks=0, ReadOnly=True)
        orig = {"sheets": {}}
        for ws in wb.Worksheets:
            name = ws.Name
            d = {"print": sheet_print(ws), "used": used_and_merges(ws)}
            if name not in ("相関図", "相関図_old", "表紙"):
                d["cols"] = col_info(ws)
                d["row_h"] = row_heights(ws, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
                d["style_samples"] = [
                    cell_style(ws, "A6"), cell_style(ws, "C8"), cell_style(ws, "A1"),
                ]
            if name == "表紙":
                d["shapes"] = shapes_of(ws, 40)
                d["row_h_all"] = row_heights(ws, list(range(1, 37)))
            if name == "相関図":
                d["shapes_n"] = ws.Shapes.Count
                d["row_h_all"] = row_heights(ws, list(range(1, 12)))
            if name in ("月次再起動", "バックアップ", "異常時の対応", "7-5仮_サービス起動停止"):
                # image placements
                pics = []
                for sh in ws.Shapes:
                    if sh.Type == 13:  # msoPicture
                        pics.append({"name": sh.Name, "w": round(float(sh.Width), 1), "h": round(float(sh.Height), 1),
                                     "t": round(float(sh.Top), 1)})
                d["pics"] = pics
            orig["sheets"][name] = d
        wb.Close(False)
        out["orig"] = orig

        # ---- applied (前例) ----
        wb = app.Workbooks.Open(APPL, UpdateLinks=0, ReadOnly=True)
        appl = {"sheets": {}}
        for ws in wb.Worksheets:
            name = ws.Name
            d = {"print": sheet_print(ws), "cols": col_info(ws)}
            d["style_samples"] = [
                cell_style(ws, "A6"), cell_style(ws, "C10"), cell_style(ws, "A7"),
                cell_style(ws, "C180"), cell_style(ws, "A181"),
            ]
            # 章帯/ラベル面/注記線の色見本: バックアップ A181(章帯?), C182(ラベル面?), C180(朱線)
            if name == "異常時の対応":
                d["pics"] = [{"name": sh.Name, "type": int(sh.Type), "w": round(float(sh.Width), 1), "h": round(float(sh.Height), 1)} for sh in ws.Shapes][:60]
                d["row_h"] = row_heights(ws, [41, 42, 43, 71, 72, 73, 74, 75])
            if name == "バックアップ":
                d["row_h"] = row_heights(ws, [6, 7, 9, 10, 11, 35, 180, 181, 182, 183])
            if name == "復旧":
                d["row_h"] = row_heights(ws, [6, 7, 8, 13, 14])
            appl["sheets"][name] = d
        wb.Close(False)
        out["appl"] = appl
    finally:
        app.Quit()
        pythoncom.CoUninitialize()

main()

with open(r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図\scripts\probe_layout_out.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=str)
print("OK - written probe_layout_out.json")
