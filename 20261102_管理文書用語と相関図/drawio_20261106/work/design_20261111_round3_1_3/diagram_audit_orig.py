# -*- coding: utf-8 -*-
"""相関図シートのレイヤー・重なり・矢印間隔を監査する（読み取り専用）。

使い方:
  python diagram_audit.py <xlsx> <sheet_substring> <out_prefix>

出力:
  <out_prefix>.json  … 図形一覧（ZOrder/Type/座標/グループ子/テキスト）
  <out_prefix>.md    … 重なり・近接の監査結果（人が読む用）
"""
import json
import math
import sys
from pathlib import Path

import win32com.client as win32

CONTAINER_NAMES = {"g2_band", "g2_bandhead", "Group 1"}


def bbox(sh):
    return (float(sh.Left), float(sh.Top), float(sh.Width), float(sh.Height))


def right(b):
    return b[0] + b[2]


def bottom(b):
    return b[1] + b[3]


def inter_area(a, b):
    x = max(0.0, min(right(a), right(b)) - max(a[0], b[0]))
    y = max(0.0, min(bottom(a), bottom(b)) - max(a[1], b[1]))
    return x * y


def contains(outer, inner, tol=0.5):
    return (outer[0] - tol <= inner[0] and outer[1] - tol <= inner[1]
            and right(outer) + tol >= right(inner) and bottom(outer) + tol >= bottom(inner))


def gap(a, b):
    """矩形間の最短距離（重なりは0）。"""
    dx = max(a[0] - right(b), b[0] - right(a), 0.0)
    dy = max(a[1] - bottom(b), b[1] - bottom(a), 0.0)
    return math.hypot(dx, dy)


def seg_rect_dist(p1, p2, r):
    """線分と矩形の最短距離。"""
    x1, y1 = p1
    x2, y2 = p2
    # 線分が矩形と交差するなら0
    for t in [i / 80 for i in range(81)]:
        x = x1 + (x2 - x1) * t
        y = y1 + (y2 - y1) * t
        if r[0] <= x <= right(r) and r[1] <= y <= bottom(r):
            return 0.0
    d = min(
        math.hypot(x1 - r[0], y1 - r[1]),
        math.hypot(x2 - r[0], y2 - r[1]),
        math.hypot(x1 - right(r), y1 - r[1]),
        math.hypot(x2 - right(r), y2 - r[1]),
    )
    for t in [i / 80 for i in range(81)]:
        x = x1 + (x2 - x1) * t
        y = y1 + (y2 - y1) * t
        d = min(d, abs(x - r[0]), abs(x - right(r)), abs(y - r[1]), abs(y - bottom(r)))
    return d


def _pt_seg_dist(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    vx, vy = bx - ax, by - ay
    l2 = vx * vx + vy * vy
    if l2 == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * vx + (py - ay) * vy) / l2))
    return math.hypot(px - (ax + t * vx), py - (ay + t * vy))


def _seg_seg_dist(a1, a2, b1, b2):
    return min(
        _pt_seg_dist(a1, b1, b2),
        _pt_seg_dist(a2, b1, b2),
        _pt_seg_dist(b1, a1, a2),
        _pt_seg_dist(b2, a1, a2),
    )


def seg_rect_dist_interior(p1, p2, r, margin=0.06):
    """線分の内側区間（端点付近を除く）と矩形の最短距離。"""
    x1, y1 = p1
    x2, y2 = p2
    best = 1e9
    for i in range(81):
        t = margin + (1 - 2 * margin) * i / 80
        x = x1 + (x2 - x1) * t
        y = y1 + (y2 - y1) * t
        dx = max(r[0] - x, x - right(r), 0.0)
        dy = max(r[1] - y, y - bottom(r), 0.0)
        best = min(best, math.hypot(dx, dy))
        if best == 0:
            return 0.0
    return best


def rect_rect_dist(a, b):
    return gap(a, b)


def shape_text(sh):
    try:
        if sh.Type == 17 and sh.HasTable:
            tbl = sh.Table
            rows = []
            for rr in range(1, tbl.Rows.Count + 1):
                cells = []
                for cc in range(1, tbl.Columns.Count + 1):
                    try:
                        cells.append(tbl.Cell(rr, cc).Shape.TextFrame2.TextRange.Text)
                    except Exception:
                        cells.append("")
                rows.append(cells)
            return rows
        if sh.HasTextFrame:
            return sh.TextFrame2.TextRange.Text
    except Exception:
        pass
    return ""


def collect(sh, depth=0):
    d = {
        "name": str(sh.Name),
        "type": int(sh.Type),
        "z": int(sh.ZOrderPosition),
        "left": round(float(sh.Left), 2),
        "top": round(float(sh.Top), 2),
        "w": round(float(sh.Width), 2),
        "h": round(float(sh.Height), 2),
        "connector": bool(sh.Connector),
        "text": shape_text(sh),
    }
    if sh.Type == 6:
        try:
            items = sh.GroupItems
            d["children"] = [collect(items.Item(i + 1), depth + 1) for i in range(items.Count)]
        except Exception as exc:  # pragma: no cover
            d["child_error"] = str(exc)
    return d


def main():
    xlsx, needle, out_prefix = sys.argv[1], sys.argv[2], sys.argv[3]
    xl = win32.DispatchEx("Excel.Application")
    xl.Visible = False
    xl.DisplayAlerts = False
    try:
        wb = xl.Workbooks.Open(xlsx, UpdateLinks=0, ReadOnly=True)
        ws = next(s for s in wb.Worksheets if needle in s.Name)
        sheet_name = ws.Name
        shapes = [collect(ws.Shapes.Item(i + 1)) for i in range(ws.Shapes.Count)]
        wb.Close(False)
    finally:
        xl.Quit()

    # 整理: コンテナ（帯・凡例・ノードを内包するグループ）を除外した「要素」
    by_name = {s["name"]: s for s in shapes}
    elements = []
    for s in shapes:
        if s["name"] in CONTAINER_NAMES:
            continue
        # 帯の見出し等、他要素を内包するグループはコンテナ扱い
        contained = [o for o in shapes if o is not s and contains(
            (s["left"], s["top"], s["w"], s["h"]), (o["left"], o["top"], o["w"], o["h"]))
            and o["type"] != 9]
        if s["type"] == 6 and contained and not s["name"].startswith(("g2_e_", "g2_n")):
            continue
        elements.append(s)

    # ノード = グループ（エッジ除く）と単独ボックス
    nodes = [e for e in elements if not e["name"].startswith("g2_e_") and e["type"] in (1, 6)]
    arrows = []
    for s in elements:
        if s["connector"] or (s["name"].startswith("g2_e_") and s["type"] == 6):
            if s["type"] == 6 and "children" in s:
                for c in s["children"]:
                    arrows.append({**c, "parent": s["name"]})
            else:
                arrows.append({**s, "parent": None})
    labels = [e for e in elements if e["type"] == 17 and not any(
        contains((n["left"], n["top"], n["w"], n["h"]), (e["left"], e["top"], e["w"], e["h"]))
        for n in nodes)]

    overlaps = []
    for i, a in enumerate(elements):
        for b in elements[i + 1:]:
            if a["type"] == 17 and b["type"] == 17:
                continue
            ar = (a["left"], a["top"], a["w"], a["h"])
            br = (b["left"], b["top"], b["w"], b["h"])
            area = inter_area(ar, br)
            if area <= 0.5:
                continue
            if contains(ar, br) or contains(br, ar):
                continue
            if a["connector"] or b["connector"] or a["name"].startswith("g2_e_") or b["name"].startswith("g2_e_"):
                continue
            overlaps.append({
                "a": a["name"], "b": b["name"], "area": round(area, 2),
                "a_z": a["z"], "b_z": b["z"],
                "a_box": [round(v, 1) for v in ar], "b_box": [round(v, 1) for v in br],
            })

    # 矢印の線分を親グループ単位で収集
    arrow_units = {}
    for ar in arrows:
        segs = []
        if ar["connector"]:
            x1, y1 = ar["left"], ar["top"]
            x2, y2 = right((ar["left"], ar["top"], ar["w"], ar["h"])), bottom((ar["left"], ar["top"], ar["w"], ar["h"]))
            if ar["w"] == 0:
                segs.append(((x1, y1), (x1, y2)))
            elif ar["h"] == 0:
                segs.append(((x1, y1), (x2, y1)))
            else:
                segs.append(((x1, y1), (x2, y2)))
        if not segs:
            continue
        key = ar["parent"] or ar["name"]
        arrow_units.setdefault(key, []).extend(segs)

    def _interior_dist(p1, p2, r, margin_pt=3.0):
        length = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
        mt = min(0.25, margin_pt / length) if length > 0 else 0.25
        x1, y1 = p1
        x2, y2 = p2
        best = 1e9
        for i in range(61):
            t = mt + (1 - 2 * mt) * i / 60
            x = x1 + (x2 - x1) * t
            y = y1 + (y2 - y1) * t
            dx = max(r[0] - x, x - right(r), 0.0)
            dy = max(r[1] - y, y - bottom(r), 0.0)
            best = min(best, math.hypot(dx, dy))
            if best == 0:
                return 0.0
        return best

    # 矢印（内側区間）とノードの近接。端点付近は接続とみなし除外。
    near = []
    for key, segs in arrow_units.items():
        for n in nodes:
            r = (n["left"], n["top"], n["w"], n["h"])
            d = min(_interior_dist(p1, p2, r) for p1, p2 in segs)
            if d < 5:
                near.append({"arrow": key, "node": n["name"], "dist": round(d, 2),
                             "node_box": [round(v, 1) for v in r]})

    # 矢印同士の近接（共有端点は除外）
    arrow_near = []
    keys = list(arrow_units)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            best = 1e9
            shared = False
            for a1, a2 in arrow_units[a]:
                for b1, b2 in arrow_units[b]:
                    if min(math.hypot(a1[0] - b1[0], a1[1] - b1[1]),
                           math.hypot(a1[0] - b2[0], a1[1] - b2[1]),
                           math.hypot(a2[0] - b1[0], a2[1] - b1[1]),
                           math.hypot(a2[0] - b2[0], a2[1] - b2[1])) < 1.5:
                        shared = True
                    best = min(best, _seg_seg_dist(a1, a2, b1, b2))
            if best < 5 and not shared:
                arrow_near.append({"a": a, "b": b, "dist": round(best, 2)})

    # ラベルと矢印線の近接（2pt未満）
    label_near = []
    for lb in labels:
        lr = (lb["left"], lb["top"], lb["w"], lb["h"])
        for key, segs in arrow_units.items():
            d = min(seg_rect_dist(p1, p2, lr) for p1, p2 in segs)
            if d < 2:
                label_near.append({"label": lb["name"], "arrow": key, "dist": round(d, 2)})

    Path(out_prefix + ".json").write_text(json.dumps({
        "sheet": sheet_name, "shapes": shapes,
        "elements": [{k: v for k, v in e.items() if k != "children"} for e in elements],
        "nodes": [{k: v for k, v in n.items() if k != "children"} for n in nodes],
        "arrows": [{k: v for k, v in a.items() if k != "children"} for a in arrows],
        "labels": [{k: v for k, v in l.items() if k != "children"} for l in labels],
        "overlaps": overlaps, "near": near, "arrow_near": arrow_near, "label_near": label_near,
    }, ensure_ascii=False, indent=1), encoding="utf-8")

    lines = [f"# 監査: {sheet_name}", "", "## 要素（Z順）", "", "| Z | 名前 | 型 | 位置 | サイズ |", "|---:|---|---|---|---|"]
    for e in sorted(elements, key=lambda x: x["z"]):
        lines.append(f"| {e['z']} | {e['name']} | {e['type']} | ({e['left']:.1f}, {e['top']:.1f}) | {e['w']:.1f}x{e['h']:.1f} |")
    lines += ["", "## 矩形の重なり（コンテナ・端点接触を除く）", ""]
    if not overlaps:
        lines.append("なし")
    for o in sorted(overlaps, key=lambda x: -x["area"]):
        lines.append(f"- {o['a']} × {o['b']}: {o['area']:.1f}pt² (A z={o['a_z']}, B z={o['b_z']})")
    lines += ["", "## 矢印（内側区間）とノードの近接（5pt未満）", ""]
    if not near:
        lines.append("なし")
    for n in sorted(near, key=lambda x: x["dist"]):
        lines.append(f"- {n['arrow']} → {n['node']}: {n['dist']:.2f}pt")
    lines += ["", "## 矢印同士の近接（5pt未満・共有端点を除く）", ""]
    if not arrow_near:
        lines.append("なし")
    for n in sorted(arrow_near, key=lambda x: x["dist"]):
        lines.append(f"- {n['a']} ↔ {n['b']}: {n['dist']:.2f}pt")
    lines += ["", "## ラベルと矢印線の近接（2pt未満）", ""]
    if not label_near:
        lines.append("なし")
    for n in sorted(label_near, key=lambda x: x["dist"]):
        lines.append(f"- {n['label']} ↔ {n['arrow']}: {n['dist']:.2f}pt")
    Path(out_prefix + ".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote", out_prefix + ".json/.md", "elements", len(elements), "overlaps", len(overlaps),
          "near", len(near), "arrow_near", len(arrow_near), "label_near", len(label_near))


if __name__ == "__main__":
    main()
