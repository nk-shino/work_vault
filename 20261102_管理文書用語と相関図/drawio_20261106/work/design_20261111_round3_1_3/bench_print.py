# -*- coding: utf-8 -*-
"""ページ設定の候補ごとに、横/縦の出力倍率・ページ数・文字の欠けを比較する。

倍率は「同じ図形の幅と高さ」で測る（幾何量のみ。文字の行頭余白やアセントに左右されない）。
  sx = PDF内の塗り矩形の幅 / 保存座標の幅
  sy = PDF内の塗り矩形の高さ / 保存座標の高さ
文字の欠けは、保存文字列の先頭行を起点に PDF の行を連結して照合する。

使い方:
  python bench_print.py <xlsx> <outdir> <label=pdfdir> [...]
"""
import json
import statistics
import sys
from pathlib import Path

import pymupdf
import win32com.client as win32

SHEETS = ["相関図①", "相関図②", "相関図③"]


def norm(s):
    return "".join(s.split())


def collect(path):
    """保存座標（Left/Top/Width/Height）と文字列を読む。"""
    xl = win32.DispatchEx("Excel.Application")
    xl.Visible = False
    xl.DisplayAlerts = False
    geo = {}
    texts = {}
    try:
        wb = xl.Workbooks.Open(path, UpdateLinks=0, ReadOnly=True)
        for sheet in SHEETS:
            ws = wb.Worksheets(sheet)
            g, t = [], []

            def walk(coll):
                for i in range(coll.Count):
                    sh = coll.Item(i + 1)
                    rec = {"name": str(sh.Name), "left": float(sh.Left), "top": float(sh.Top),
                           "w": float(sh.Width), "h": float(sh.Height)}
                    g.append(rec)
                    try:
                        txt = sh.TextFrame2.TextRange.Text
                    except Exception:
                        txt = ""
                    if txt.strip():
                        r2 = dict(rec)
                        r2["text"] = txt
                        t.append(r2)
                    if int(sh.Type) == 6:
                        walk(sh.GroupItems)

            walk(ws.Shapes)
            geo[sheet] = g
            texts[sheet] = t
        wb.Close(False)
    finally:
        xl.Quit()
    return geo, texts


def pdf_text_lines(path):
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
    pages = len(doc)
    first = doc[0].rect
    doc.close()
    return lines, pages, (round(first.width, 2), round(first.height, 2))


def pdf_rects(path):
    """塗りつぶし図形の外接矩形 (w, h) 一覧（PDF座標）。

    角丸矩形は 're' ではなく曲線で描かれるため、図形の外接矩形を使う。
    """
    doc = pymupdf.open(path)
    out = []
    for page in doc:
        for d in page.get_drawings():
            if d.get("fill") is None:
                continue
            r = d["rect"]
            if r.width >= 30 and r.height >= 10:
                out.append((r.width, r.height))
    doc.close()
    return sorted(set((round(w, 2), round(h, 2)) for w, h in out))


def scale_rects(shapes, rects):
    """保存座標の矩形と PDF の外接矩形を対応づけ、sx/sy を推定する。

    先に (sx, sy) を粗く格子探索して対応数が最大の点を求め、その対応で中央値を取る。
    """
    import numpy as np

    cand = [s for s in shapes if s["w"] >= 80 and s["h"] >= 25]
    if len(cand) < 3 or len(rects) < 3:
        return None, None, 0
    W = np.array([s["w"] for s in cand])
    H = np.array([s["h"] for s in cand])
    P = np.array(rects, dtype=float)          # (m, 2)

    grid = np.arange(0.60, 0.961, 0.01)
    best = (-1, 1e18, None, None)
    for sx in grid:
        ew = np.abs(W[:, None] * sx - P[None, :, 0])          # (n, m)
        for sy in grid:
            eh = np.abs(H[:, None] * sy - P[None, :, 1])
            d = ew + eh
            tol = np.maximum(1.5, 0.02 * np.maximum(W[:, None] * sx, H[:, None] * sy))
            hit = (d <= tol).any(axis=1)
            cnt = int(hit.sum())
            cost = float(d.min(axis=1).mean())
            if cnt > best[0] or (cnt == best[0] and cost < best[1]):
                best = (cnt, cost, sx, sy)
    cnt, _, sx, sy = best
    pairs = []
    for s in cand:
        ew, eh = s["w"] * sx, s["h"] * sy
        near = min(rects, key=lambda r: abs(r[0] - ew) + abs(r[1] - eh))
        tol = max(1.5, 0.02 * max(ew, eh))
        if abs(near[0] - ew) + abs(near[1] - eh) <= 2 * tol:
            pairs.append((near[0] / s["w"], near[1] / s["h"]))
    if len(pairs) < 3:
        return None, None, len(pairs)
    return (statistics.median(p[0] for p in pairs),
            statistics.median(p[1] for p in pairs), len(pairs))


def first_line(shape, lines):
    T = norm(shape["text"])
    best = None
    for l in lines:
        n = l["n"]
        if n and T.startswith(n) and (best is None or len(n) > len(best[1])):
            best = (l, n)
    return best[0] if best else None


def trace(shape, lines):
    T = norm(shape["text"])
    best = None
    for l in lines:
        n = l["n"]
        if n and T.startswith(n) and (best is None or len(n) > len(best[1])):
            best = (l, n)
    if best is None:
        return "先頭行なし", T, ""
    cur, used = best[0], best[1]
    while len(used) < len(T):
        remain = T[len(used):]
        cand = None
        for l in lines:
            if l is cur or not l["n"]:
                continue
            same = abs(l["y0"] - cur["y0"]) < 2.0 and -6.0 <= l["x0"] - cur["x1"] <= 8.0
            nxt = abs(l["x0"] - cur["x0"]) <= 6 and (cur["y1"] - 2.0 <= l["y0"] <= cur["y1"] + 8.0)
            if not (same or nxt):
                continue
            if remain.startswith(l["n"]) and (cand is None or len(l["n"]) > len(cand[1])):
                cand = (l, l["n"])
        if cand is None:
            break
        used += cand[1]
        cur = cand[0]
    return ("一致" if used == T else "欠け"), T, used


def main():
    xlsx, outdir = sys.argv[1], sys.argv[2]
    settings = [tuple(a.split("=", 1)) for a in sys.argv[3:]]
    geo, st = collect(xlsx)
    report = {}
    for label, d in settings:
        report[label] = {}
        for sheet in SHEETS:
            pdf = Path(d) / (sheet + ".pdf")
            if not pdf.exists():
                report[label][sheet] = {"error": "no pdf"}
                continue
            lines, pages, size = pdf_text_lines(str(pdf))
            rects = pdf_rects(str(pdf))
            sx, sy, nmat = scale_rects(geo[sheet], rects)
            bad = []
            for s in st[sheet]:
                stat, T, got = trace(s, lines)
                if stat != "一致":
                    bad.append({"name": s["name"], "status": stat, "missing": T[len(got):]})
            report[label][sheet] = {
                "page_size": size, "pages": pages,
                "sx": round(sx, 4) if sx else None,
                "sy": round(sy, 4) if sy else None,
                "ratio": round(sy / sx, 4) if sx and sy else None,
                "matched_rects": nmat,
                "shapes": len(st[sheet]), "missing": len(bad), "missing_list": bad,
            }
    out = Path(outdir) / "bench_print.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")

    print("| 設定 | シート | 用紙(pt) | sx | sy | sy/sx | 対応矩形 | ページ | 欠け |")
    print("|---|---|---|---|---|---|---|---|---|")
    for label, _ in settings:
        for sheet in SHEETS:
            r = report[label][sheet]
            if "error" in r:
                print("| %s | %s | - | - | - | - | - | - | - |" % (label, sheet))
                continue
            f = lambda v: ("%.4f" % v) if v else "-"
            print("| %s | %s | %.0fx%.0f | %s | %s | %s | %d | %d | %d/%d |" % (
                label, sheet, r["page_size"][0], r["page_size"][1],
                f(r["sx"]), f(r["sy"]), f(r["ratio"]), r["matched_rects"],
                r["pages"], r["missing"], r["shapes"]))
    print("wrote", out)


if __name__ == "__main__":
    main()
