# -*- coding: utf-8 -*-
"""適用後の検証（読み取りのみ）。

出力:
  - 5pt未満の矢印-図形ペアを「端点接続」と「線が図形内部に入る」に分類
  - 矢印同士・矩形の重なりを複数の定義で前後比較
  - 矢印グループ内の結合（角）の隙間
  - 内容の外形と用紙（A4横）の比較
  - 出力PDFの線分の結合確認
"""
import json
import math
import sys
from pathlib import Path

import pymupdf

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent.parent


def flat(shapes):
    out = []
    for s in shapes:
        out.append(s)
        out.extend(flat(s.get("children") or []))
    return out


def R(s):
    return (s["left"], s["top"], s["left"] + s["w"], s["top"] + s["h"])


def inside(p, r, tol=0.01):
    return r[0] + tol < p[0] < r[2] - tol and r[1] + tol < p[1] < r[3] - tol


def seg_points(p1, p2, n=80, margin=0.02):
    out = []
    for i in range(n + 1):
        t = margin + (1 - 2 * margin) * i / n
        out.append((p1[0] + (p2[0] - p1[0]) * t, p1[1] + (p2[1] - p1[1]) * t))
    return out


def seg_rect_gap(p1, p2, r):
    best = 1e9
    for x, y in seg_points(p1, p2):
        dx = max(r[0] - x, x - r[2], 0.0)
        dy = max(r[1] - y, y - r[3], 0.0)
        best = min(best, math.hypot(dx, dy))
    return best


def pt_rect_boundary_dist(p, r):
    dx = max(r[0] - p[0], p[0] - r[2], 0.0)
    dy = max(r[1] - p[1], p[1] - r[3], 0.0)
    return math.hypot(dx, dy)


def arrow_segments(shapes):
    """グループ内の子（線）を、親名をキーにした線分リストにする。"""
    units = {}
    for s in shapes:
        if s["name"].startswith("g2_e_") and s.get("children"):
            segs = []
            for c in s["children"]:
                if not c.get("connector"):
                    continue
                x0, y0 = c["left"], c["top"]
                x1, y1 = x0 + c["w"], y0 + c["h"]
                segs.append(((x0, y0), (x1, y1)))
            units[s["name"]] = segs
        elif s.get("connector"):
            x0, y0 = s["left"], s["top"]
            x1, y1 = x0 + s["w"], y0 + s["h"]
            units.setdefault(s["name"], []).append(((x0, y0), (x1, y1)))
    return units


def overlaps(sel, skip17=True, use_contains=True):
    def inter(a, b):
        x = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
        y = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
        return x * y

    def contains(o, i, tol=0.5):
        return o[0] - tol <= i[0] and o[1] - tol <= i[1] and o[2] + tol >= i[2] and o[3] + tol >= i[3]

    out = []
    for i, a in enumerate(sel):
        for b in sel[i + 1:]:
            if skip17 and a["type"] == 17 and b["type"] == 17:
                continue
            ar, br = R(a), R(b)
            if inter(ar, br) <= 0.5:
                continue
            if use_contains and (contains(ar, br) or contains(br, ar)):
                continue
            out.append((a["name"], b["name"]))
    return out


def classify(audit_path):
    d = json.loads(Path(audit_path).read_text(encoding="utf-8"))
    shapes = d["shapes"]
    allsh = flat(shapes)
    byname = {s["name"]: s for s in allsh}
    units = arrow_segments(shapes)

    rows = []
    for np_ in d["near"]:
        arrow, node = np_["arrow"], np_["node"]
        r = R(byname[node])
        segs = units.get(arrow, [])
        penetration = False
        hit = None
        for p1, p2 in segs:
            for x, y in seg_points(p1, p2):
                if inside((x, y), r):
                    penetration = True
                    hit = (p1, p2)
                    break
            if penetration:
                break
        if not penetration:
            # 端点がどれだけ辺に近いか
            best = None
            for p1, p2 in segs:
                for p in (p1, p2):
                    dd = pt_rect_boundary_dist(p, r)
                    if best is None or dd < best[0]:
                        best = (dd, p)
        rows.append({
            "arrow": arrow, "node": node, "dist": np_["dist"],
            "verdict": "線が内部に入る" if penetration else "端点接続",
            "segment": hit,
            "nearest_endpoint": None if penetration else (round(best[0], 3), [round(v, 2) for v in best[1]]),
        })
    return d, rows, units, byname, allsh


def main():
    _, rows, units, byname, allsh = classify(BASE / "audit_after.json")
    _, rows_b, units_b, byname_b, allsh_b = classify(BASE / "audit_before_recheck.json")

    print("== 5pt未満（矢印-図形）の分類 ==")
    for r in sorted(rows, key=lambda x: x["dist"]):
        ep = r["nearest_endpoint"]
        print("  %-12s -> %-10s %5.2fpt  %-8s endpoint_dist=%s" %
              (r["arrow"].replace("g2_e_", ""), r["node"], r["dist"], r["verdict"],
               "-" if ep is None else ep[0]))
    print("  件数 after=%d before=%d, 内部に入るもの=%d" %
          (len(rows), len(rows_b), sum(1 for r in rows if r["verdict"] != "端点接続")))

    print("\n== 矢印同士の5pt未満 ==")
    d = json.loads((BASE / "audit_after.json").read_text(encoding="utf-8"))
    print("  after:", d["arrow_near"])
    db = json.loads((BASE / "audit_before_recheck.json").read_text(encoding="utf-8"))
    print("  before:", db["arrow_near"])

    print("\n== 矩形の重なり（定義別・前後比較）==")
    defs = {
        "A: diagram_audit.py の出力": None,
        "B: 末端図形のみ(表・線を除く)": [s for s in allsh if not s.get("children")],
        "C: 全図形(線・エッジ名を除く)": [s for s in allsh if not s.get("children")
                                          and s["type"] != 9
                                          and not s["name"].startswith("g2_e_")],
    }
    for label, sel in defs.items():
        if sel is None:
            print("  %-28s before=%d after=%d" % (label, len(db["overlaps"]), len(d["overlaps"])))
            continue
        ob = overlaps([dict(s) for s in [x for x in allsh_b if x["name"] in {y["name"] for y in sel}]])
        oa = overlaps(sel)
        same = set(ob) == set(oa)
        print("  %-28s before=%d after=%d 同一集合=%s" % (label, len(ob), len(oa), same))

    print("\n== 矢印グループ内の結合（角）==")
    for g in ("g2_e_e18", "g2_e_e17", "g2_e_e02", "g2_e_e04"):
        segs = units[g]
        segs2 = units_b[g]
        def corners(ss):
            gaps = []
            for i, (a1, a2) in enumerate(ss):
                for j, (b1, b2) in enumerate(ss):
                    if i >= j:
                        continue
                    d_ = min(math.hypot(a1[0] - b1[0], a1[1] - b1[1]),
                             math.hypot(a1[0] - b2[0], a1[1] - b2[1]),
                             math.hypot(a2[0] - b1[0], a2[1] - b1[1]),
                             math.hypot(a2[0] - b2[0], a2[1] - b2[1]))
                    gaps.append(d_)
            return min(gaps) if gaps else 0.0, max(gaps) if gaps else 0.0
        mn, mx = corners(segs)
        mnb, mxb = corners(segs2)
        print("  %-12s before min/max=%5.2f/%6.2f  after min/max=%5.2f/%6.2f" % (g, mnb, mxb, mn, mx))

    print("\n== 内容の外形と用紙 ==")
    shapes = d["shapes"]
    left = min(R(s)[0] for s in shapes)
    top = min(R(s)[1] for s in shapes)
    right = max(R(s)[2] for s in shapes)
    bottom = max(R(s)[3] for s in shapes)
    print("  bbox L=%.2f T=%.2f R=%.2f B=%.2f" % (left, top, right, bottom))
    print("  用紙A4横 841.89x595.28 / 余白28.35 -> 右限813.54 下595.28")
    print("  右端の余裕=%.2f  下端の超過=%.2f" % (813.54 - right, bottom - 595.28))

    print("\n== 出力PDFの線分 ==")
    pdf = BASE / "render_after" / "相関図②.pdf"
    doc = pymupdf.open(str(pdf))
    p = doc[0]
    print("  pages=%d size=%.2fx%.2f" % (len(doc), p.rect.width, p.rect.height))
    segs = []
    for dr in p.get_drawings():
        for it in dr["items"]:
            if it[0] == "l":
                segs.append((round(it[1].x, 2), round(it[1].y, 2), round(it[2].x, 2), round(it[2].y, 2)))
    hs = [s for s in segs if abs(s[1] - s[3]) < 0.3 and abs(s[2] - s[0]) > 400]
    vs = [s for s in segs if abs(s[0] - s[2]) < 0.3 and abs(s[3] - s[1]) > 200]
    for s in sorted(hs, key=lambda s: s[1])[:4]:
        print("  H y=%.2f x=%.2f..%.2f" % (s[1], s[0], s[2]))
    for s in sorted(vs, key=lambda s: s[0])[:6]:
        print("  V x=%.2f y=%.2f..%.2f" % (s[0], s[1], s[3]))
    txt = p.get_text("text")
    for key in ("凡例：", "分類：", "略語：", "出典："):
        print("  文字 %s : %s" % (key, "あり" if key in txt else "なし"))


if __name__ == "__main__":
    main()
