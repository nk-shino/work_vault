"""Geometry analysis for 相関図①/③: label-vs-arrow crossings, arrow-vs-node penetration.

Reads the audit JSON (stable stored coordinates) and reports:
  A) arrow segments that pass through a label box  (line strikes through text)
  B) arrow segments that enter a node box interior (penetration beyond tolerance)
Usage: python analysis13.py <audit.json>
"""
import json
import sys


def rect(s):
    l, t, w, h = s["left"], s["top"], s["w"], s["h"]
    return (l, t, l + w, t + h)


def seg_rect(s):
    """A connector segment; width or height is 0 for an axis-aligned run."""
    l, t, w, h = s["left"], s["top"], s["w"], s["h"]
    return (min(l, l + w), min(t, t + h), max(l, l + w), max(t, t + h))


def inter(a, b):
    x0, y0 = max(a[0], b[0]), max(a[1], b[1])
    x1, y1 = min(a[2], b[2]), min(a[3], b[3])
    return (x1 - x0, y1 - y0) if (x1 > x0 and y1 > y0) else None


def main(path):
    d = json.load(open(path, encoding="utf-8"))
    arrows = d["arrows"]
    def walk(ss):
        for s in ss:
            yield s
            yield from walk(s.get("children") or [])
    allshapes = list(walk(d["shapes"]))
    labels = [s for s in allshapes
              if s["name"].endswith("_l") or s["name"].endswith("expl")
              or s["name"].endswith("_txt")]
    nodes = [s for s in d["nodes"] if s["name"].startswith(("g1_n", "g1_p", "g1_s", "g1_e_a", "g1_e_b", "g3_n", "g3_pcr", "g3_dgsr", "g3_band"))]
    print("sheet:", d["sheet"], " arrows:", len(arrows), " labels:", len(labels), " nodes:", len(nodes))

    print("\n--- A) label box crossed by an arrow segment (line through text)")
    hits = 0
    for lab in labels:
        lb = rect(lab)
        for seg in arrows:
            sb = seg_rect(seg)
            # expand the zero-width segment by the stroke half-width
            sb = (sb[0] - 0.4, sb[1] - 0.4, sb[2] + 0.4, sb[3] + 0.4)
            ov = inter(lb, sb)
            if ov and ov[0] > 0.2 and ov[1] > 0.2:
                hits += 1
                print("  %-13s <- %-14s (parent %-10s) overlap %.2f x %.2f pt"
                      % (lab["name"], seg["name"], seg.get("parent", "-"), ov[0], ov[1]))
    print("  total:", hits)

    print("\n--- B) arrow segment entering a node box interior")
    for seg in arrows:
        sb = seg_rect(seg)
        for nd in nodes:
            nb = rect(nd)
            if nd["name"] in ("g3_band", "g3_n07", "g3_n11"):
                pass
            ov = inter(nb, sb)
            if ov and ov[0] > 1.0 and ov[1] > 1.0:
                print("  %-14s in %-14s overlap %.2f x %.2f pt" % (seg["name"], nd["name"], ov[0], ov[1]))


if __name__ == "__main__":
    main(sys.argv[1])
