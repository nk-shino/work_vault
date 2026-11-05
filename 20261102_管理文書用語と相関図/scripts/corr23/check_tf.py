# -*- coding: utf-8 -*-
"""変更ラベルのtf実数(mL/mR/boundW/boundH)を出力し、新幅での[d]フレーム余裕を検算する。"""
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
G = json.load(open(os.path.join(HERE, "geom_before.json"), encoding="utf-8"))

WANT = {
    "相関図②": {
        "g2_e_e01_l": 106, "g2_e_e02_l": 112, "g2_e_e04_l": 130, "g2_e_e08_l": 126,
        "g2_e_e15_l": 146, "g2_e_e16_l": 151, "g2_e_e17_l": 158, "g2_e_e18_l": 86,
        "g2_n17_txt": 110, "g2_bandhead": 460,
    },
    "相関図③": {
        "g3_e_e04_l": 180, "g3_e_e05_l": 120, "g3_e_e06_l": 102, "g3_e_e12_l": 118,
        "g3_bandhead": 195,
    },
}
for sn, wants in WANT.items():
    print("=" * 20, sn)
    tops = {s["name"]: s for s in G["pana"][sn]["shapes"]}
    for nm, neww in wants.items():
        s = tops.get(nm)
        if s is None:
            for t in tops.values():
                for c in t.get("children", []):
                    if c["name"] == nm:
                        s = c
        if s is None:
            print("  NOT FOUND", nm)
            continue
        tf = s.get("tf")
        if not tf:
            print("  %-14s tf=None" % nm)
            continue
        S = tf["mL"] + tf["mR"]
        aw_new = neww - S
        need = tf["boundW"] + 0.75
        ok = "OK " if aw_new >= need else "NG!"
        print("  %-14s old_w=%6.2f new_w=%3d mL=%.2f mR=%.2f S=%.2f bw=%7.2f bh=%6.2f aw_new=%7.2f need=%7.2f %s"
              % (nm, s["w"], neww, tf["mL"], tf["mR"], S, tf["boundW"], tf["boundH"], aw_new, need, ok))
print("DONE")
