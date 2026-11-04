# -*- coding: utf-8 -*-
"""fix31_g8_probe3.py — エッジ(フリーフォーム)の頂点座標と矢頭スタイルを抽出(読み取り専用)"""
import json, os
import win32com.client as win32

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAULT = os.path.join(BASE, "..", "..", "OneDrive - NK", "ドキュメント", "Work_Vault", "10_業務全般", "PanaCIM_LNB", "01_成果物")
BOOKS = {"pana": os.path.join(VAULT, "Pana-CIM管理手順書案_未承認.xlsx"),
         "lnb": os.path.join(VAULT, "LNB管理手順書案_未承認.xlsx")}
OUT = os.path.join(BASE, "scripts", "fix31_g8_probe3_report.json")

ARROW = {1:"None", 2:"Triangle", 3:"Stealth", 4:"Diamond", 5:"Oval", 6:"Arrow", 7:"Tee"}

def main():
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    try:
        app.AutoSaveOn = False
    except Exception:
        pass
    rep = {}
    try:
        for bk, path in BOOKS.items():
            wb = app.Workbooks.Open(path, UpdateLinks=0, ReadOnly=True)
            try:
                ws = wb.Worksheets("相関図")
                edges = {}
                for sh in ws.Shapes:
                    if not sh.Name.startswith("edge_"):
                        continue
                    d = {"dash": sh.Line.DashStyle, "weight": round(sh.Line.Weight, 2)}
                    try:
                        d["begA"] = ARROW.get(sh.Line.BeginArrowheadStyle, sh.Line.BeginArrowheadStyle)
                        d["endA"] = ARROW.get(sh.Line.EndArrowheadStyle, sh.Line.EndArrowheadStyle)
                    except Exception:
                        pass
                    try:
                        n = sh.Nodes.Count
                        pts = []
                        for i in range(1, n + 1):
                            nd = sh.Nodes.Item(i)
                            raw = nd.Points
                            flat = []
                            def fl(x):
                                if isinstance(x, (int, float)):
                                    flat.append(round(float(x), 1))
                                else:
                                    for y in x:
                                        fl(y)
                            fl(raw)
                            pts.append(flat)
                        d["nodesCount"] = n
                        d["segs"] = pts
                    except Exception as e:
                        d["nodesErr"] = str(e)
                    edges[sh.Name] = d
                rep[bk] = edges
            finally:
                wb.Close(SaveChanges=False)
    finally:
        app.Quit()
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    for bk, edges in rep.items():
        print("==", bk)
        for name, d in edges.items():
            print(" ", name, "dash=", d["dash"], "beg=", d.get("begA"), "end=", d.get("endA"), "segs=", d.get("segs"))
    print("DONE ->", OUT)

if __name__ == "__main__":
    main()
