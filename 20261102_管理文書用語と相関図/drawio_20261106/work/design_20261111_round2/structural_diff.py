# -*- coding: utf-8 -*-
"""前後のxlsxを比較し、位置・サイズ以外に差がないことを確認する（読み取りのみ）。"""
import json
import sys

import win32com.client as win32


def dump(path, sheet):
    xl = win32.DispatchEx("Excel.Application")
    xl.Visible = False
    xl.DisplayAlerts = False
    out = {}
    try:
        wb = xl.Workbooks.Open(path, UpdateLinks=0, ReadOnly=True)
        ws = next(s for s in wb.Worksheets if s.Name == sheet)
        ps = ws.PageSetup
        out["pagesetup"] = {
            "orientation": int(ps.Orientation), "papersize": int(ps.PaperSize),
            "zoom": bool(ps.Zoom), "fitwide": int(ps.FitToPagesWide),
            "fittall": int(ps.FitToPagesTall), "printarea": str(ps.PrintArea),
            "leftmargin": round(float(ps.LeftMargin), 4), "rightmargin": round(float(ps.RightMargin), 4),
            "topmargin": round(float(ps.TopMargin), 4), "bottommargin": round(float(ps.BottomMargin), 4),
            "centerH": bool(ps.CenterHorizontally), "centerV": bool(ps.CenterVertically),
            "scale": int(ps.Zoom) if not ps.Zoom else None,
        }
        shapes = {}

        def collect(coll, prefix=""):
            for i in range(coll.Count):
                sh = coll.Item(i + 1)
                key = prefix + str(sh.Name)
                d = {
                    "type": int(sh.Type), "z": int(sh.ZOrderPosition),
                    "visible": int(sh.Visible),
                    "left": round(float(sh.Left), 2), "top": round(float(sh.Top), 2),
                    "w": round(float(sh.Width), 2), "h": round(float(sh.Height), 2),
                    "text": "",
                    "rot": round(float(sh.Rotation), 2) if hasattr(sh, "Rotation") else None,
                }
                try:
                    d["text"] = str(sh.TextFrame2.TextRange.Text)
                except Exception:
                    d["text"] = ""
                try:
                    d["fill"] = (int(sh.Fill.ForeColor.RGB), int(sh.Fill.Visible), int(sh.Fill.Transparency))
                except Exception:
                    d["fill"] = None
                try:
                    d["line"] = (int(sh.Line.ForeColor.RGB), int(sh.Line.Visible),
                                 round(float(sh.Line.Weight), 2), int(sh.Line.Transparency))
                except Exception:
                    d["line"] = None
                try:
                    d["dash"] = int(sh.Line.DashStyle)
                except Exception:
                    d["dash"] = None
                shapes[key] = d
                if int(sh.Type) == 6:
                    collect(sh.GroupItems, key + "/")
        collect(ws.Shapes)
        out["shapes"] = shapes
        wb.Close(False)
    finally:
        xl.Quit()
    return out


def main():
    a, b, sheet = sys.argv[1], sys.argv[2], sys.argv[3]
    A, B = dump(a, sheet), dump(b, sheet)
    print("PageSetup 同一:", A["pagesetup"] == B["pagesetup"])
    if A["pagesetup"] != B["pagesetup"]:
        for k in A["pagesetup"]:
            if A["pagesetup"][k] != B["pagesetup"][k]:
                print("  差:", k, A["pagesetup"][k], "->", B["pagesetup"][k])
    print("図形数:", len(A["shapes"]), "->", len(B["shapes"]))
    print("名前の集合が同一:", set(A["shapes"]) == set(B["shapes"]))
    onlyA = set(A["shapes"]) - set(B["shapes"])
    onlyB = set(B["shapes"]) - set(A["shapes"])
    if onlyA or onlyB:
        print("  削除:", onlyA, " 追加:", onlyB)
    moved, attrs = [], {}
    for k in A["shapes"]:
        if k not in B["shapes"]:
            continue
        sa, sb = A["shapes"][k], B["shapes"][k]
        if (sa["left"], sa["top"], sa["w"], sa["h"]) != (sb["left"], sb["top"], sb["w"], sb["h"]):
            moved.append(k)
        for f in ("type", "z", "visible", "text", "rot", "fill", "line", "dash"):
            if sa[f] != sb[f]:
                attrs.setdefault(f, []).append((k, sa[f], sb[f]))
    print("位置/サイズが変わった図形: %d" % len(moved))
    for k in sorted(moved):
        print("   ", k)
    print("位置・サイズ以外の差分:", {k: v for k, v in attrs.items()} if attrs else "なし")


if __name__ == "__main__":
    main()
