# -*- coding: utf-8 -*-
"""fix34_orig_geom.py — G10前原本(backup_20261102)の相関図③で
e05_l / E05 / E06 / n08 / n09 / E10_s0 の実座標を読み取り専用で出力する。
保存しない。テキスト本文は出力しない。
"""
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import win32com.client as win32

BK = r"C:/Users/ss80751/kohden-code-workspace/20261102_管理文書用語と相関図/backup_20261102"
BOOKS = {
    "pana_orig": os.path.join(BK, "Pana-CIM管理手順書案_未承認_G10前_20261104.xlsx"),
    "lnb_orig": os.path.join(BK, "LNB管理手順書案_未承認_G10前_20261104.xlsx"),
}
NAMES = {"g3_n08", "g3_n09", "g3_e_e05_l", "g3_e_E05", "g3_e_E06",
         "g3_e_e06_l", "g3_e_E10_s0", "g3_e_e05_l2"}


def r1(v):
    try:
        return round(float(v), 2)
    except Exception:
        return None


def walk(sh, out, depth=0):
    t = int(sh.Type)
    if t == 6:
        for i in range(1, sh.GroupItems.Count + 1):
            walk(sh.GroupItems.Item(i), out, depth + 1)
        return
    if sh.Name in NAMES:
        out.append({"name": sh.Name, "depth": depth, "type": t,
                    "l": r1(sh.Left), "t": r1(sh.Top),
                    "w": r1(sh.Width), "h": r1(sh.Height)})


def main():
    rep = {}
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    try:
        for bk, path in BOOKS.items():
            wb = app.Workbooks.Open(path, UpdateLinks=0, ReadOnly=True)
            out = []
            for i in range(1, wb.Worksheets.Count + 1):
                ws = wb.Worksheets(i)
                if ws.Name == "相関図③":
                    for j in range(1, ws.Shapes.Count + 1):
                        walk(ws.Shapes(j), out)
            wb.Close(SaveChanges=False)
            rep[bk] = sorted(out, key=lambda d: d["name"])
            print("==", bk)
            for d in rep[bk]:
                print("  %-14s type=%s l=%s t=%s w=%s h=%s depth=%s"
                      % (d["name"], d["type"], d["l"], d["t"], d["w"], d["h"], d["depth"]))
    finally:
        try:
            app.Quit()
        except Exception:
            pass
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fix34_orig_geom.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    print("PROBE DONE ->", out)


if __name__ == "__main__":
    main()
