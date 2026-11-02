# -*- coding: utf-8 -*-
"""COM probe 2: ラベル面の塗り·原本書式·表紙図形·画像寸法(読み取り専用·保存なし)."""
import json
import win32com.client as wc
import pythoncom

ORIG = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\Pana-CIM管理手順書案_未承認.xlsx"
APPL = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261029_管理手順書_5-7章_デザイン適用\管理手順書_5-7章_デザイン適用_20261029.xlsx"

out = {}

def rgb(v):
    try:
        v = int(v)
        return (v % 256, (v // 256) % 256, (v // 65536) % 256)
    except Exception:
        return None

def style(ws, addr):
    c = ws.Range(addr)
    f = c.Font
    b = c.Borders(7)
    r = {
        "addr": addr,
        "v": (str(c.Value)[:20] if c.Value is not None else None),
        "font": f.Name, "size": float(f.Size), "bold": bool(f.Bold),
        "fcolor": rgb(f.Color) if isinstance(f.Color, int) else f.Color,
        "fill": rgb(c.Interior.Color) if c.Interior.Pattern == 1 else None,
        "lb": ([int(b.LineStyle), rgb(int(b.Color)), int(b.Weight)] if b.LineStyle and int(b.LineStyle) != -4142 else None),
        "wrap": bool(c.WrapText), "ha": int(c.HorizontalAlignment),
        "merge": c.MergeArea.Address, "h": round(float(c.RowHeight), 2),
    }
    return r

def shapes(ws):
    res = []
    for sh in ws.Shapes:
        d = {"n": sh.Name, "t": int(sh.Type),
             "box": [round(float(sh.Left), 1), round(float(sh.Top), 1), round(float(sh.Width), 1), round(float(sh.Height), 1)]}
        try:
            if sh.TextFrame2.HasText:
                d["txt"] = sh.TextFrame2.TextRange.Text[:24].replace("\r", "/")
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
        # ---- applied: ラベル面·突合ヘッダの塗り ----
        wb = app.Workbooks.Open(APPL, UpdateLinks=0, ReadOnly=True)
        a = {}
        bk = wb.Worksheets("バックアップ")
        a["bk_r182"] = [style(bk, "A182"), style(bk, "C182")]
        a["bk_r183"] = [style(bk, "A183"), style(bk, "C183"), style(bk, "E183")]
        ab = wb.Worksheets("異常時の対応")
        a["ab_r32"] = [style(ab, "A32"), style(ab, "C32")]
        a["ab_r33"] = [style(ab, "A33"), style(ab, "C33")]
        a["ab_r71"] = [style(ab, "A71"), style(ab, "C71")]
        wb.Close(False)
        out["appl"] = a

        # ---- original ----
        wb = app.Workbooks.Open(ORIG, UpdateLinks=0, ReadOnly=True)
        o = {}
        for ws in wb.Worksheets:
            n = ws.Name
            if n in ("表紙", "相関図"):
                o[n + "_shapes"] = shapes(ws)
            if n == "表紙":
                o["表紙_rowh"] = {r: round(float(ws.Rows(r).RowHeight), 2) for r in range(1, 37)}
                o["表紙_cols"] = {ws.Cells(1, i).Address.split("$")[1]: round(float(ws.Cells(1, i).ColumnWidth), 2) for i in range(1, 26)}
                o["表紙_x1"] = [style(ws, "X1"), style(ws, "U12"), style(ws, "A14")]
                o["表紙_area"] = ws.PageSetup.PrintArea
            if n == "目次":
                o["目次_cols"] = {ws.Cells(1, i).Address.split("$")[1]: round(float(ws.Cells(1, i).ColumnWidth), 2) for i in [1, 2, 3, 4, 5, 10, 20, 52]}
                o["目次_styles"] = [style(ws, "C19"), style(ws, "D6"), style(ws, "J10")]
            if n == "用語":
                o["用語_styles"] = [style(ws, "A7"), style(ws, "C7"), style(ws, "C8")]
            if n == "構成と管理情報":
                o["構成_styles"] = [style(ws, "A7"), style(ws, "C8"), style(ws, "C15"), style(ws, "A16")]
            if n == "管理体制":
                o["体制_styles"] = [style(ws, "A8"), style(ws, "C8"), style(ws, "E8"), style(ws, "C9")]
            if n == "月次再起動":
                o["月次_styles"] = [style(ws, "A7"), style(ws, "C9"), style(ws, "A28"), style(ws, "C52")]
                o["月次_rowh"] = {r: round(float(ws.Rows(r).RowHeight), 2) for r in (6, 7, 9, 28, 52, 53, 75, 78)}
                o["月次_pics"] = shapes(ws)
            if n == "バックアップ":
                o["bk_orig"] = [style(ws, "A6"), style(ws, "C7"), style(ws, "C10"), style(ws, "A181")]
                o["bk_pics"] = shapes(ws)
                o["bk_rowh"] = {r: round(float(ws.Rows(r).RowHeight), 2) for r in (6, 7, 9, 10, 35, 180, 181, 182)}
            if n == "異常時の対応":
                o["ab_orig"] = [style(ws, "A6"), style(ws, "C7"), style(ws, "C42"), style(ws, "A71")]
                o["ab_pics"] = [{"n": s.Name, "t": int(s.Type), "box": [round(float(s.Left), 1), round(float(s.Top), 1), round(float(s.Width), 1), round(float(s.Height), 1)]} for s in ws.Shapes][:60]
            if n == "チェックシート(月次・異常時)":
                o["cs_cols"] = {ws.Cells(1, i).Address.split("$")[1]: round(float(ws.Cells(1, i).ColumnWidth), 2) for i in range(1, 15)}
                o["cs_styles"] = [style(ws, "A7"), style(ws, "C7"), style(ws, "M7"), style(ws, "C13")]
            if n == "会議課題一覧(一時)":
                o["kaigi_rowh_sample"] = {r: round(float(ws.Rows(r).RowHeight), 2) for r in (1, 41, 42, 43, 100, 528)}
            if n == "付録 引用元と確認範囲":
                o["furoku_styles"] = [style(ws, "A8"), style(ws, "C9"), style(ws, "C20")]
            if n == "要確認事項一覧":
                o["yk_styles"] = [style(ws, "A8"), style(ws, "C8"), style(ws, "E8"), style(ws, "C9"), style(ws, "C34")]
                o["yk_rows_after34"] = {r: round(float(ws.Rows(r).RowHeight), 2) for r in (35, 36, 40, 112)}
            if n == "7-5仮_サービス起動停止":
                o["kari_styles"] = [style(ws, "A6"), style(ws, "C7"), style(ws, "A14"), style(ws, "C15")]
                o["kari_pics"] = shapes(ws)
            if n == "復旧":
                o["fk_cols_after"] = {ws.Cells(1, i).Address.split("$")[1]: round(float(ws.Cells(1, i).ColumnWidth), 2) for i in (53, 60, 68)}
            if n == "相関図":
                mx_r = mx_b = 0
                for sh in ws.Shapes:
                    mx_r = max(mx_r, float(sh.Left) + float(sh.Width))
                    mx_b = max(mx_b, float(sh.Top) + float(sh.Height))
                o["相関図_shape_extent"] = [round(mx_r, 1), round(mx_b, 1)]
                o["相関図_rowh"] = {r: round(float(ws.Rows(r).RowHeight), 2) for r in range(1, 11)}
        wb.Close(False)
        out["orig"] = o
    finally:
        app.Quit()
        pythoncom.CoUninitialize()

main()
with open(r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図\scripts\probe2_out.json", "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1, default=str)
print("OK probe2")
