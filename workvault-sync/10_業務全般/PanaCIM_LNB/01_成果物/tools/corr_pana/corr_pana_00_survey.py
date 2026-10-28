# -*- coding: utf-8 -*-
"""Phase 0: 原本の相関図シートを読み取り専用で精査(一切書き換えない)。
取得物: ヘッダ部(R1-10)のセル値/結合/罫線/フォント、全34図形の詳細スタイル、ページ設定。
出力: corr_pana_survey.json"""
import sys, io, os, json, warnings
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
warnings.filterwarnings("ignore")
import pythoncom, win32com.client

WORK = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\issue6263_work"
ORIG = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\Pana-CIM管理手順書案_未承認.xlsx"
SHEET = "相関図"

def rgb(color):
    try:
        v = int(color) & 0xFFFFFF
        return f"#{v:06X}"
    except Exception:
        return None

def main():
    pythoncom.CoInitialize()
    before = set(os.popen('tasklist /FI "IMAGENAME eq EXCEL.EXE" /FO CSV /NH').read().split())
    xl = win32com.client.DispatchEx("Excel.Application")
    xl.Visible = False
    xl.DisplayAlerts = False
    try:
        wb = xl.Workbooks.Open(ORIG, UpdateLinks=0, ReadOnly=True)
        ws = wb.Worksheets(SHEET)
        info = {"sheets": [wb.Worksheets(i).Name for i in range(1, wb.Worksheets.Count + 1)]}

        # --- ヘッダ部セル(R1-R10, A-AZ) ---
        cells, merges = [], []
        for r in range(1, 11):
            rowvals = []
            for c in range(1, 53):
                cell = ws.Cells(r, c)
                v = cell.Value
                if v is not None:
                    f = cell.Font
                    rowvals.append({"a": f"{chr(64+c) if c<=26 else 'A'+chr(64+c-26)}{r}", "v": str(v)[:60],
                                    "fs": float(f.Size), "bold": bool(f.Bold),
                                    "merge": bool(cell.MergeCells)})
            cells.extend(rowvals)
        for r in range(1, 11):
            for c in range(1, 53):
                cell = ws.Cells(r, c)
                if cell.MergeCells:
                    ma = str(cell.MergeArea.Address)
                    if ma not in merges:
                        merges.append(ma)
        info["header_cells"] = cells
        info["header_merges"] = merges
        info["rowh_1_10"] = {r: round(float(ws.Rows(r).RowHeight), 1) for r in range(1, 11)}

        # --- 図形詳細 ---
        shapes = []
        for i in range(1, ws.Shapes.Count + 1):
            sh = ws.Shapes.Item(i)
            s = {"i": i, "name": sh.Name, "type": int(sh.Type),
                 "L": round(float(sh.Left), 1), "T": round(float(sh.Top), 1),
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
                tf = sh.TextFrame2
                s["text"] = tf.TextRange.Text.replace("\r", "⏎")[:120]
                s["font"] = tf.TextRange.Font.NameFarEast
                s["fsize"] = round(float(tf.TextRange.Font.Size), 1)
            except Exception:
                pass
            if int(sh.Type) == 9:  # connector
                try:
                    cb = sh.ConnectorFormat.BeginConnected
                    ce = sh.ConnectorFormat.EndConnected
                    s["conn"] = [cb, sh.ConnectorFormat.BeginConnectedShape.Name if cb else None,
                                 ce, sh.ConnectorFormat.EndConnectedShape.Name if ce else None]
                except Exception:
                    pass
            shapes.append(s)
        info["shapes"] = shapes
        with open(os.path.join(WORK, "corr_pana_survey.json"), "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=1)
        print(f"sheets={info['sheets']}")
        print(f"merges={merges}")
        print(f"header cells with values: {len(cells)}")
        for c in cells[:40]:
            print("  ", c)
        print(f"shapes: {len(shapes)}")
        wb.Close(SaveChanges=False)
    finally:
        xl.Quit()
        pythoncom.CoUninitialize()
    after = set(os.popen('tasklist /FI "IMAGENAME eq EXCEL.EXE" /FO CSV /NH').read().split())
    print("EXCEL new tokens:", len(after - before), "(user instances untouched)")

main()
