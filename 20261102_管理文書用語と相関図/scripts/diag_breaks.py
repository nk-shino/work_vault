# -*- coding: utf-8 -*-
"""diag_breaks.py — 異常時の実境界と図形座標·跨ぎ判定値を読み取り専用でダンプ。"""
import json, sys

XLSX = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\Pana-CIM管理手順書案_未承認.xlsx"
OUT = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図\scripts\diag_breaks_out.json"

def main():
    import win32com.client as win32
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    try:
        wb = app.Workbooks.Open(XLSX, UpdateLinks=0, ReadOnly=True)
        out = {}
        for name, last in [("異常時の対応", 321), ("月次再起動", 93), ("バックアップ", 189)]:
            ws = wb.Worksheets(name)
            hs = {r: float(ws.Rows[r].RowHeight) for r in range(1, last + 1)}
            tops = {1: 0.0}
            for r in range(1, last + 1):
                tops[r + 1] = tops[r] + hs.get(r, 12.8)
            rb = []
            n = ws.HPageBreaks.Count
            for i in range(1, n + 1):
                pb = ws.HPageBreaks.Item(i)
                try:
                    t = int(pb.Type)
                except Exception:
                    t = -1
                rb.append([int(pb.Location.Row), t])
            pics = []
            for sh in ws.Shapes:
                try:
                    t = int(sh.Type)
                    if t in (13, 10):
                        pics.append({"tlr": int(sh.TopLeftCell.Row), "top": round(float(sh.Top), 2),
                                     "bot": round(float(sh.Top) + float(sh.Height), 2), "h": round(float(sh.Height), 2)})
                except Exception:
                    pass
            pics.sort(key=lambda p: p["top"])
            rows = [r for r, t in rb]
            bounds = [0.0] + [tops[r] for r in rows] + [1e9]
            verdicts = []
            for p in pics:
                i = max(idx for idx, b in enumerate(bounds) if b <= p["top"] + 0.5)
                verdicts.append({"tlr": p["tlr"], "seg_next_b": round(bounds[i + 1], 2),
                                 "gap": round(bounds[i + 1] - p["bot"], 2)})
            out[name] = {"breaks": rb, "tops_sample": {str(r): round(tops[r], 2) for r in (116, 129, 130, 131, 132, 133, 145) if r <= last},
                         "heights_sample": {str(r): hs.get(r) for r in (117, 118, 128, 129, 130, 131) if r <= last},
                         "pics": pics, "verdicts": verdicts}
        wb.Close(SaveChanges=False)
    finally:
        app.Quit()
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("WROTE", OUT)

if __name__ == "__main__":
    main()
