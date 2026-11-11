# -*- coding: utf-8 -*-
"""テキストボックスの中身がPDFに全部出ているかを、座標に依存せず照合する。

方法:
  1. Excel から図形ごとの全文を取り出す。
  2. PDF の行のうち、図形の全文の「先頭部分」と一致する行を1行目とする。
  3. 1行目のすぐ下（同じ左端・次の行の高さ）にある行で、残りの文字列の
     先頭と一致するものを連結していく。
  4. 連結結果が全文と一致しなければ「欠け」として報告する。

使い方:
  python text_check.py <xlsx> <pdf> <sheet> [<out.json>]
"""
import json
import sys
from pathlib import Path

import pymupdf
import win32com.client as win32


def norm(s):
    return "".join(s.split())


def collect(path, sheet):
    xl = win32.DispatchEx("Excel.Application")
    xl.Visible = False
    xl.DisplayAlerts = False
    out = []
    try:
        wb = xl.Workbooks.Open(path, UpdateLinks=0, ReadOnly=True)
        ws = wb.Worksheets(sheet)

        def walk(coll):
            for i in range(coll.Count):
                sh = coll.Item(i + 1)
                try:
                    t = sh.TextFrame2.TextRange.Text
                except Exception:
                    t = ""
                if t.strip():
                    out.append({"name": str(sh.Name), "text": t,
                                "type": int(sh.Type),
                                "left": float(sh.Left), "top": float(sh.Top),
                                "w": float(sh.Width), "h": float(sh.Height)})
                if int(sh.Type) == 6:
                    walk(sh.GroupItems)

        walk(ws.Shapes)
        wb.Close(False)
    finally:
        xl.Quit()
    return out


def pdf_lines(path):
    doc = pymupdf.open(path)
    lines = []
    for page in doc:
        for b in page.get_text("dict")["blocks"]:
            if b["type"] != 0:
                continue
            for l in b["lines"]:
                txt = "".join(s["text"] for s in l["spans"])
                if txt.strip():
                    bb = l["bbox"]
                    lines.append({"text": txt, "n": norm(txt),
                                  "x0": bb[0], "y0": bb[1], "x1": bb[2], "y1": bb[3]})
    doc.close()
    return lines


def trace(shape, lines):
    T = norm(shape["text"])
    if not T:
        return None
    best = None
    for l in lines:
        n = l["n"]
        if n and T.startswith(n) and (best is None or len(n) > len(best[1])):
            best = (l, n)
    if best is None:
        return {"name": shape["name"], "status": "先頭行が見つからない", "text": T, "got": ""}
    cur, used = best[0], best[1]
    chain = [cur["text"]]
    while len(used) < len(T):
        remain = T[len(used):]
        cand = None
        for l in lines:
            if l is cur or not l["n"]:
                continue
            same_baseline = abs(l["y0"] - cur["y0"]) < 2.0 and -6.0 <= l["x0"] - cur["x1"] <= 8.0
            next_line = abs(l["x0"] - cur["x0"]) <= 6 and (cur["y1"] - 2.0 <= l["y0"] <= cur["y1"] + 8.0)
            if not (same_baseline or next_line):
                continue
            if remain.startswith(l["n"]) and (cand is None or len(l["n"]) > len(cand[1])):
                cand = (l, l["n"])
        if cand is None:
            break
        chain.append(cand[0]["text"])
        used += cand[1]
        cur = cand[0]
    ok = used == T
    return {"name": shape["name"], "status": "一致" if ok else "欠け",
            "text": T, "got": used, "missing": "" if ok else T[len(used):],
            "lines": chain}


def main():
    xlsx, pdf, sheet = sys.argv[1], sys.argv[2], sys.argv[3]
    out = sys.argv[4] if len(sys.argv) > 4 else None
    shapes = collect(xlsx, sheet)
    lines = pdf_lines(pdf)
    res = [trace(s, lines) for s in shapes]
    res = [r for r in res if r]
    bad = [r for r in res if r["status"] != "一致"]
    print("図形数 %d / 一致 %d / 欠け %d" % (len(res), len(res) - len(bad), len(bad)))
    for r in bad:
        print("  [%s] %-16s 欠け=%r" % (r["status"], r["name"], r.get("missing", "")))
        print("        全文=%r" % r["text"])
        print("        取得=%r" % r["got"])
    if out:
        Path(out).write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
