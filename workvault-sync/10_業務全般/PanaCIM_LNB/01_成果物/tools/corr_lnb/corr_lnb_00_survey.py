# -*- coding: utf-8 -*-
"""corr_lnb_00_survey.py — LNB管理手順書案_未承認.xlsx を読み取り専用で精査(一切書き換えない)。
取得物:
  - シート一覧(相関図_old 既存の有無·用語シートの確認)
  - 相関図シート: 全図形一覧(rel_* 34個想定)·ページ設定·B11アンカー·行高·ヘッダ部セル
  - 構成と管理情報シート: セル値全件(apply段階の文言更新箇所の洗い出し用)
  - vault原本のSHA256(読み取り前後で不変であることの証跡)
出力: <temp>/corr_lnb_survey.json (UTF-8)
"""
import hashlib
import json
import os
import sys
import time
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\corr_lnb_work"
VAULT = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
ORIG = os.path.join(VAULT, "LNB管理手順書案_未承認.xlsx")
OUT = os.path.join(WORK, "corr_lnb_survey.json")

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.makedirs(WORK, exist_ok=True)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def rgb(color):
    try:
        v = int(color) & 0xFFFFFF
        return "#%06X" % v
    except Exception:
        return None


def main():
    h_before = sha256(ORIG)
    import win32com.client
    import win32process

    xl = win32com.client.DispatchEx("Excel.Application")
    xl.Visible = False
    xl.DisplayAlerts = False
    pid = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
    info = {"orig": ORIG, "sha256_before": h_before, "pid": pid, "errors": []}
    try:
        wb = xl.Workbooks.Open(ORIG, UpdateLinks=0, ReadOnly=True)
        info["sheets"] = [wb.Worksheets(i).Name for i in range(1, wb.Worksheets.Count + 1)]
        info["has_相関図_old"] = "相関図_old" in info["sheets"]

        # ---------- 相関図シート ----------
        ws = wb.Worksheets("相関図")
        shapes = []
        for i in range(1, ws.Shapes.Count + 1):
            sh = ws.Shapes.Item(i)
            s = {"i": i, "name": sh.Name, "type": int(sh.Type),
                 "L": round(float(sh.Left) - float(ws.Range("B11").Left), 1),
                 "T": round(float(sh.Top) - float(ws.Range("B11").Top), 1),
                 "W": round(float(sh.Width), 1), "H": round(float(sh.Height), 1)}
            try:
                s["fill"] = rgb(sh.Fill.ForeColor.RGB) if sh.Fill.Type != 5 else "none"
            except Exception:
                s["fill"] = None
            try:
                s["line"] = rgb(sh.Line.ForeColor.RGB)
                s["linew"] = round(float(sh.Line.Weight), 2)
                s["dash"] = int(sh.Line.DashStyle)
            except Exception:
                pass
            try:
                t = sh.TextFrame2.TextRange.Text
                s["text"] = t.replace("\r", "⏎")[:100]
            except Exception:
                pass
            shapes.append(s)
        info["corr_shapes"] = shapes
        info["corr_shape_count"] = len(shapes)
        ps = ws.PageSetup
        info["corr_pagesetup"] = {
            "orientation": int(ps.Orientation), "zoom": ps.Zoom,
            "fit_wide": ps.FitToPagesWide, "fit_tall": ps.FitToPagesTall,
            "print_area": ps.PrintArea, "paper_size": int(ps.PaperSize),
            "margins": [round(float(getattr(ps, m)), 1) for m in
                        ("LeftMargin", "RightMargin", "TopMargin", "BottomMargin")],
        }
        info["anchor_B11"] = {"left": round(float(ws.Range("B11").Left), 1),
                              "top": round(float(ws.Range("B11").Top), 1)}
        info["rowh_1_15"] = {r: round(float(ws.Rows(r).RowHeight), 1) for r in range(1, 16)}
        # 列幅サンプル(A..F)
        info["colw_a_f"] = {c: round(float(ws.Columns(c).ColumnWidth), 2) for c in range(1, 7)}
        # ヘッダ部セル(行1-12, A..AZ)
        def colname(c):
            n = ""
            while c > 0:
                c, r = divmod(c - 1, 26)
                n = chr(65 + r) + n
            return n

        cells = []
        for r in range(1, 13):
            for c in range(1, 53):
                cell = ws.Cells(r, c)
                v = cell.Value
                if v is not None:
                    cells.append({"a": "%s%d" % (colname(c), r), "v": str(v)[:80],
                                  "fs": round(float(cell.Font.Size), 1), "bold": bool(cell.Font.Bold)})
        info["corr_header_cells"] = cells

        # ---------- 構成と管理情報シート ----------
        for sname in info["sheets"]:
            if "構成" in sname and "管理" in sname:
                wsi = wb.Worksheets(sname)
                vals = []
                ur = wsi.UsedRange
                rows, cols = ur.Rows.Count, ur.Columns.Count
                r0, c0 = ur.Row, ur.Column
                for r in range(r0, min(r0 + rows, r0 + 120)):
                    for c in range(c0, min(c0 + cols, c0 + 12)):
                        v = wsi.Cells(r, c).Value
                        if v is not None and str(v).strip():
                            vals.append({"a": "%s%d" % (colname(c), r), "v": str(v)[:200]})
                info["kanri_sheet"] = {"name": sname, "values": vals}
                break

        wb.Close(SaveChanges=False)
    finally:
        try:
            xl.Quit()
        except Exception as e:
            info["errors"].append("quit:%r" % e)
        time.sleep(2)
        try:
            chk = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid],
                                 capture_output=True, text=True)
            if "EXCEL" in chk.stdout.upper():
                subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
                info["errors"].append("killed residual %d" % pid)
        except Exception as e:
            info["errors"].append("cleanup:%r" % e)
    info["sha256_after"] = sha256(ORIG)
    info["orig_unchanged"] = info["sha256_before"] == info["sha256_after"]
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=1)
    print("ok:", not info["errors"], "sheets:", len(info["sheets"]),
          "corr_shapes:", info["corr_shape_count"], "orig_unchanged:", info["orig_unchanged"])


main()
