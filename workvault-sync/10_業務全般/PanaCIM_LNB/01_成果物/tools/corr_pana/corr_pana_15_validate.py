# -*- coding: utf-8 -*-
"""corr_pana_15_validate.py — Stage 5 geometry validator (A0-A8 + SOFT).

Authority:
  corr_pana_14_result.json  node/band geometry (via corr_pana_15_tables.py)
  corr_pana_15_tables.py    routes / labels / expected crossings
Rules (corr_pana_15_route_input.md §3):
  A0  every edge endpoint lies on its semantic node border (±0.5pt)
  A1  no edge segment enters a node interior (n01_esxi container exempt; children block)
  A2  measured H×V crossing set == expected list (±1pt)
  A3  label ink × any edge segment distance >= 2pt (DOC_EXCEPTIONS exempt)
  A4  label ink × label ink distance >= 2pt
  A5  label ink × node bbox overlap == 0 (container exempt)
  A6  edge × band-head TEXT ink overlap == 0 (ink = top-anchored, margin 0,
      line count derived from head box height; tag rects are inside nodes -> covered by A1)
  A7  label ink inside its band (split y=312); band_b labels clear band_b_head box
  A8  all ink within 750 x 366
SOFT: parallel edge gaps < 2pt, remote labels (>30pt from own route),
      E09 x2 vs N01 container border, band-boundary hugging.

Usage: python corr_pana_15_validate.py [--json]
Exit code 1 when HARD violations remain.
"""
import json
import math
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import corr_pana_15_tables as T  # noqa: E402

TOL = 0.5    # A0 endpoint tolerance / A1 interior shrink
GAP = 2.0    # A3/A4 minimum clearance
PT = 1.0     # A2 crossing coordinate tolerance

HARD = []
SOFT = []


def hard(code, subj, detail):
    HARD.append({"code": code, "subject": subj, "detail": detail})


def soft(code, subj, detail):
    SOFT.append({"code": code, "subject": subj, "detail": detail})


def ink_h(lines):
    return 12.4 + 9.9 * (lines - 1)


# ---------------------------------------------------------------- segments
def segs_of(route):
    out = []
    for (ax, ay), (bx, by) in zip(route, route[1:]):
        if abs(ax - bx) < 1e-9:
            out.append(("V", ax, min(ay, by), max(ay, by)))
        elif abs(ay - by) < 1e-9:
            out.append(("H", ay, min(ax, bx), max(ax, bx)))
        else:
            out.append(("D", ax, ay, bx, by))
    return out


SEGS = {e: segs_of(r) for e, r in T.ROUTES.items()}

for e, sl in SEGS.items():
    for s in sl:
        if s[0] == "D":
            hard("A1", e, "diagonal segment %s" % (s,))

# ---------------------------------------------------------------- A0
def on_border(px, py, rect):
    x0, y0, x1, y1 = rect
    if (abs(px - x0) <= TOL or abs(px - x1) <= TOL) and (y0 - TOL <= py <= y1 + TOL):
        return True
    if (abs(py - y0) <= TOL or abs(py - y1) <= TOL) and (x0 - TOL <= px <= x1 + TOL):
        return True
    return False


for e, (na, nb) in T.ENDPOINTS.items():
    r = T.ROUTES[e]
    if not on_border(r[0][0], r[0][1], T.SHAPES[na]):
        hard("A0", e, "start %s not on %s %s" % (r[0], na, T.SHAPES[na]))
    if not on_border(r[-1][0], r[-1][1], T.SHAPES[nb]):
        hard("A0", e, "end %s not on %s %s" % (r[-1], nb, T.SHAPES[nb]))

# ---------------------------------------------------------------- A1
# (band heads are not nodes: edge x head BOX is legal, only the TEXT ink
#  is protected — that is A6's job)
for e, sl in SEGS.items():
    for s in sl:
        if s[0] == "D":
            continue
        for nname, (x0, y0, x1, y1) in T.SHAPES.items():
            if nname == T.CONTAINER or nname in T.BAND_HEADS:
                continue
            ix0, iy0, ix1, iy1 = x0 + TOL, y0 + TOL, x1 - TOL, y1 - TOL
            if s[0] == "H":
                y, xa, xb = s[1], s[2], s[3]
                if iy0 < y < iy1 and xb > ix0 and xa < ix1:
                    hard("A1", e, "H y=%s x[%s,%s] pierces %s" % (y, xa, xb, nname))
            else:
                x, ya, yb = s[1], s[2], s[3]
                if ix0 < x < ix1 and yb > iy0 and ya < iy1:
                    hard("A1", e, "V x=%s y[%s,%s] pierces %s" % (x, ya, yb, nname))

# ---------------------------------------------------------------- A2
measured = []
flat = [(e, s) for e, sl in SEGS.items() for s in sl]
for i in range(len(flat)):
    ea, sa = flat[i]
    for j in range(i + 1, len(flat)):
        eb, sb = flat[j]
        if ea == eb:
            continue
        if sa[0] == "H" and sb[0] == "V":
            hy, xa, xb = sa[1], sa[2], sa[3]
            vx, ya, yb = sb[1], sb[2], sb[3]
            if xa - 1e-9 <= vx <= xb + 1e-9 and ya - 1e-9 <= hy <= yb + 1e-9:
                measured.append((vx, hy, ea, eb))
        elif sa[0] == "V" and sb[0] == "H":
            vx, ya, yb = sa[1], sa[2], sa[3]
            hy, xa, xb = sb[1], sb[2], sb[3]
            if xa - 1e-9 <= vx <= xb + 1e-9 and ya - 1e-9 <= hy <= yb + 1e-9:
                measured.append((vx, hy, ea, eb))

used = [False] * len(measured)
for (ex, ey, ea, eb) in T.EXPECTED_CROSSINGS:
    hit = -1
    for k, (mx, my, ma, mb) in enumerate(measured):
        if not used[k] and {ma, mb} == {ea, eb} \
                and abs(mx - ex) <= PT and abs(my - ey) <= PT:
            hit = k
            break
    if hit < 0:
        hard("A2", "%sx%s" % (ea, eb), "expected (%s,%s) not measured" % (ex, ey))
    else:
        used[hit] = True
for k, (mx, my, ma, mb) in enumerate(measured):
    if not used[k]:
        hard("A2", "%sx%s" % (ma, mb), "unexpected crossing at (%s,%s)" % (mx, my))

# ---------------------------------------------------------------- labels
INK = {lid: (x, y, x + w, y + ink_h(n)) for lid, (x, y, w, n) in T.LABELS.items()}

# A3 label ink x edge segments
for lid, (rx0, ry0, rx1, ry1) in INK.items():
    for e, sl in SEGS.items():
        for s in sl:
            if s[0] == "D":
                continue
            if (lid, e) in getattr(T, "DOC_EXCEPTIONS", []):
                continue
            if s[0] == "H":
                sy, sx0, sx1 = s[1], s[2], s[3]
                dx = max(0.0, rx0 - sx1, sx0 - rx1)
                dy = max(0.0, ry0 - sy, sy - ry1)
            else:
                sx, sy0, sy1 = s[1], s[2], s[3]
                dx = max(0.0, rx0 - sx, sx - rx1)
                dy = max(0.0, ry0 - sy1, sy0 - ry1)
            d = math.hypot(dx, dy)
            if d < GAP - 1e-9:
                hard("A3", lid, "ink(%s,%s,%s,%s) x %s seg %s dist=%.2f"
                     % (rx0, ry0, rx1, ry1, e, s, d))

# A4 label x label
ids = sorted(INK)
for i in range(len(ids)):
    for j in range(i + 1, len(ids)):
        a, b = INK[ids[i]], INK[ids[j]]
        dx = max(0.0, a[0] - b[2], b[0] - a[2])
        dy = max(0.0, a[1] - b[3], b[1] - a[3])
        d = math.hypot(dx, dy)
        if d < GAP - 1e-9:
            hard("A4", "%sx%s" % (ids[i], ids[j]),
                 "dist=%.2f inks %s / %s" % (d, a, b))

# A5 label x node
for lid, (rx0, ry0, rx1, ry1) in INK.items():
    for nname, (x0, y0, x1, y1) in T.SHAPES.items():
        if nname == T.CONTAINER:
            continue
        if rx0 < x1 and x0 < rx1 and ry0 < y1 and y0 < ry1:
            hard("A5", lid, "ink(%s,%s,%s,%s) overlaps %s (%s,%s,%s,%s)"
                 % (rx0, ry0, rx1, ry1, nname, x0, y0, x1, y1))

# A6 edge x band-head text ink (non-overlap; top-anchored, margin 0)
def head_lines(h):
    return max(1, int((h - 12.4) / 9.9 + 1e-9) + 1)


HEAD_INK = {}
for hname in T.BAND_HEADS:
    x0, y0, x1, _ = T.SHAPES[hname]
    HEAD_INK[hname] = (x0, y0, x1, y0 + ink_h(head_lines(T.SHAPES[hname][3] - y0)))

for e, sl in SEGS.items():
    for s in sl:
        if s[0] == "D":
            continue
        for hname, (hx0, hy0, hx1, hy1) in HEAD_INK.items():
            if s[0] == "H":
                y, xa, xb = s[1], s[2], s[3]
                if hy0 < y < hy1 and xb > hx0 and xa < hx1:
                    hard("A6", e, "H y=%s x[%s,%s] crosses %s text ink (%s,%s,%s,%s)"
                         % (y, xa, xb, hname, hx0, hy0, hx1, hy1))
            else:
                x, ya, yb = s[1], s[2], s[3]
                if hx0 < x < hx1 and yb > hy0 and ya < hy1:
                    hard("A6", e, "V x=%s y[%s,%s] crosses %s text ink (%s,%s,%s,%s)"
                         % (x, ya, yb, hname, hx0, hy0, hx1, hy1))

# A7 labels inside their band; band_b labels clear band_b_head box
for lid, (rx0, ry0, rx1, ry1) in INK.items():
    if ry0 < T.BAND_SPLIT_Y:
        if not (0 <= ry0 and ry1 <= T.BAND_SPLIT_Y):
            hard("A7", lid, "ink %s leaves band_a (y0-%s)" % (INK[lid], T.BAND_SPLIT_Y))
    else:
        if not (T.BAND_SPLIT_Y <= ry0 and ry1 <= T.FIG_BOTTOM):
            hard("A7", lid, "ink %s leaves band_b (y%s-%s)"
                 % (INK[lid], T.BAND_SPLIT_Y, T.FIG_BOTTOM))
        bx0, by0, bx1, by1 = T.SHAPES["band_b_head"]
        if rx0 < bx1 and bx0 < rx1 and ry0 < by1 and by0 < ry1:
            hard("A7", lid, "ink interferes band_b_head box (%s,%s,%s,%s)"
                 % (bx0, by0, bx1, by1))

# A8 everything within the figure
for lid, rect in INK.items():
    if rect[0] < 0 or rect[1] < 0 or rect[2] > T.FIG_RIGHT + 1e-9 \
            or rect[3] > T.FIG_BOTTOM + 1e-9:
        hard("A8", lid, "ink %s outside %sx%s" % (rect, T.FIG_RIGHT, T.FIG_BOTTOM))
for e, sl in SEGS.items():
    for s in sl:
        if s[0] == "H":
            y, xa, xb = s[1], s[2], s[3]
            if not (0 <= xa and xb <= T.FIG_RIGHT and 0 <= y <= T.FIG_BOTTOM):
                hard("A8", e, "H seg %s outside figure" % (s,))
        else:
            x, ya, yb = s[1], s[2], s[3]
            if not (0 <= ya and yb <= T.FIG_BOTTOM and 0 <= x <= T.FIG_RIGHT):
                hard("A8", e, "V seg %s outside figure" % (s,))

# ---------------------------------------------------------------- SOFT
# S1 parallel edge gap < 2pt (same orientation, overlapping span)
for i in range(len(flat)):
    ea, sa = flat[i]
    for j in range(i + 1, len(flat)):
        eb, sb = flat[j]
        if ea == eb or sa[0] != sb[0] or sa[0] == "D":
            continue
        if sa[0] == "V":
            gap = abs(sb[1] - sa[1])
            lo, hi = max(sa[2], sb[2]), min(sa[3], sb[3])
        else:
            gap = abs(sb[1] - sa[1])
            lo, hi = max(sa[2], sb[2]), min(sa[3], sb[3])
        if 1e-9 < gap < GAP and hi > lo:
            soft("S1-parallel", "%s/%s" % (ea, eb),
                 "%s lines gap=%.2f over [%s,%s]" % (sa[0], gap, lo, hi))

# S2 remote labels (>30pt from own route)
def label_route_dist(lid):
    rx0, ry0, rx1, ry1 = INK[lid]
    best = None
    for s in SEGS[lid]:
        if s[0] == "H":
            sy, sx0, sx1 = s[1], s[2], s[3]
            dx = max(0.0, rx0 - sx1, sx0 - rx1)
            dy = max(0.0, ry0 - sy, sy - ry1)
        else:
            sx, sy0, sy1 = s[1], s[2], s[3]
            dx = max(0.0, rx0 - sx, sx - rx1)
            dy = max(0.0, ry0 - sy1, sy0 - ry1)
        d = math.hypot(dx, dy)
        best = d if best is None else min(best, d)
    return best


remote = []
for lid in sorted(INK):
    d = label_route_dist(lid)
    if d is not None and d > 30:
        remote.append("%s(%.0fpt)" % (lid, d))
        soft("S2-remote", lid, "label %.0fpt from own route" % d)

# S3 documented visual notes
soft("S3-border", "E09", "x2 vertical runs ~0.9pt inside N01 container border "
                         "(2.25pt frame centered x0) — documented deviation")
for lid, (rx0, ry0, rx1, ry1) in INK.items():
    if abs(ry1 - T.BAND_SPLIT_Y) < GAP:
        soft("S4-bandhug", lid, "ink bottom %.1f hugs band split y=%s"
             % (ry1, T.BAND_SPLIT_Y))

# ---------------------------------------------------------------- output
result = {
    "hard": HARD,
    "soft": SOFT,
    "crossings_measured": len(measured),
    "crossings_expected": len(T.EXPECTED_CROSSINGS),
    "remote_labels": remote,
    "pass": len(HARD) == 0,
}
out_path = os.path.join(HERE, "corr_pana_15_validate_result.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)

if "--json" in sys.argv:
    print(json.dumps(result, ensure_ascii=False, indent=1))
else:
    print("HARD violations: %d" % len(HARD))
    for v in HARD:
        print("  [%s] %s: %s" % (v["code"], v["subject"], v["detail"]))
    print("SOFT notes: %d" % len(SOFT))
    for v in SOFT:
        print("  [%s] %s: %s" % (v["code"], v["subject"], v["detail"]))
    print("crossings: measured=%d expected=%d"
          % (len(measured), len(T.EXPECTED_CROSSINGS)))
    print("result -> %s" % out_path)
    print("PASS" if not HARD else "FAIL")

sys.exit(0 if not HARD else 1)
