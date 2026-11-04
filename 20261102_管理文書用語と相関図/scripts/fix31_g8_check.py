# -*- coding: utf-8 -*-
"""fix31_g8_check.py — 相関図①②③の保存後幾何検査(数値·図形名·PASS/NG のみ出力)。
(a) 図形同士の bbox 重なり — エッジ·帯は対象外。一方が他方を完全に内包する場合は
    コンテナ設計(内包は許容)として除外。
(b) ノードグループは "_box" メンバーを持つこと(全ノードに外箱あり — 設計統一済み)。
    box/txt/icon/tag メンバーが box の内側にあること。
(c) PrintArea が全図形の外接範囲を覆うこと。
(d) 各シートの凡例 g{g}_leg1(分類色見本)のマーク数と色値。
テキスト本文は読み取らない(凡例の1字単位の色読み取りのみ)·保存しない。
"""
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import win32com.client as win32

BASE = os.path.dirname(os.path.abspath(__file__))
REPORT = os.path.join(BASE, "fix31_g8_check_report.json")
BOOKS = {
    "pana": (r"C:/Users/ss80751/OneDrive - NK/ドキュメント/Work_Vault"
             r"/10_業務全般/PanaCIM_LNB/01_成果物/Pana-CIM管理手順書案_未承認.xlsx"),
    "lnb": (r"C:/Users/ss80751/OneDrive - NK/ドキュメント/Work_Vault"
            r"/10_業務全般/PanaCIM_LNB/01_成果物/LNB管理手順書案_未承認.xlsx"),
}
LEG_COLORS = [0xA35F7B, 0x59BB9B, 0x3844A9, 0x808080, 0xBFBFBF]
TOL = 0.75  # pt


def bbox(sh):
    return (round(sh.Left, 1), round(sh.Top, 1), round(sh.Width, 1), round(sh.Height, 1))


def overlap(a, b):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    w = min(ax + aw, bx + bw) - max(ax, bx)
    h = min(ay + ah, by + bh) - max(ay, by)
    return max(0.0, w) * max(0.0, h)


def contains(a, b, tol=1.0):
    """a が b を内包する(コンテナ設計は許容)。"""
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return (bx >= ax - tol and by >= ay - tol
            and bx + bw <= ax + aw + tol and by + bh <= ay + ah + tol)


def is_edge(nm):
    return "_e_" in nm


def is_band(nm):
    return nm.endswith("_band") or nm.endswith("_bandhead")


NODE_TAILS = ("n01", "n02", "n03", "n04", "n05", "n06r", "n07", "n08", "n09", "n10", "n11",
              "n12", "n13", "n14", "n15", "n16", "n17", "n18", "n19", "p1", "p2", "s1", "s2",
              "ea", "eb", "liner", "pcr", "dgsr")


def members(grp):
    return {grp.GroupItems.Item(i).Name: grp.GroupItems.Item(i)
            for i in range(1, grp.GroupItems.Count + 1)}


def check_sheet(ws, g):
    R = {"shapes": ws.Shapes.Count, "violations": [], "nodes": {}}
    tops = {ws.Shapes(i).Name: ws.Shapes(i) for i in range(1, ws.Shapes.Count + 1)}
    names = list(tops)
    ps = ws.PageSetup
    R["pagesetup"] = {"fitW": ps.FitToPagesWide, "fitT": ps.FitToPagesTall, "paper": ps.PaperSize}
    # (a) 重なり — エッジ·帯を除外したペアのみ。内包ペアは許容
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            na, nb = names[i], names[j]
            if is_edge(na) or is_edge(nb) or is_band(na) or is_band(nb):
                continue
            ba, bb = bbox(tops[na]), bbox(tops[nb])
            ov = overlap(ba, bb)
            if ov > 1.0 and not (contains(ba, bb) or contains(bb, ba)):
                R["violations"].append(["a-overlap", na, nb, round(ov, 1)])
    # (b) ノード内部の収まり
    for nm, sh in tops.items():
        if sh.Type != 6 or is_edge(nm) or is_band(nm):
            continue
        tail = nm.split("_")[-1]
        if tail not in NODE_TAILS:
            continue
        mem = members(sh)
        R["nodes"][nm] = len(mem)
        boxk = [k for k in mem if k.endswith("_box")]
        if not boxk:
            R["violations"].append(["b-nobox", nm, "", 0])
            continue
        bx = bbox(mem[boxk[0]])
        for k in mem:
            if k.endswith(("_txt", "_icon", "_tag")):
                mb = bbox(mem[k])
                ok = overlap(bx, mb) > 0 or contains(bx, mb, TOL)
                if not ok and k.endswith("_tag"):
                    # 図①の設計: タグはbox直上に浮かせる見出し(仕様 tag x, box_y-16)。
                    # box直上24pt以内で水平方向に重なる場合は妥当とみなす。
                    above = (0 <= bx[1] - (mb[1] + mb[3]) <= 24
                             and min(bx[0] + bx[2], mb[0] + mb[2]) - max(bx[0], mb[0]) > 0)
                    ok = above
                if not ok:
                    R["violations"].append(["b-contain", nm, k, 0])
    # (c) PrintArea が全図形を覆うか
    pa = ws.PageSetup.PrintArea
    maxr = max(bbox(s)[0] + bbox(s)[2] for s in tops.values())
    maxb = max(bbox(s)[1] + bbox(s)[3] for s in tops.values())
    R["extent"] = [maxr, maxb]
    R["print_area"] = pa
    rng = ws.Range(pa.split(":")[1])
    edge_x = rng.Left + rng.Width
    edge_y = rng.Top + rng.Height
    if maxr > edge_x - 4 or maxb > edge_y - 4:
        R["violations"].append(["c-printarea", pa, round(maxr, 1), round(maxb, 1)])
    # (d) 分類凡例(色見本)の検証 — シートごとの g{g}_leg1
    lnm = "g%d_leg1" % g
    if lnm not in tops:
        R["violations"].append(["d-legend-missing", lnm, "", 0])
    else:
        tr = tops[lnm].TextFrame2.TextRange
        txt = tr.Text
        marks = [k for k, chx in enumerate(txt) if chx in "■□"]
        if len(marks) != len(LEG_COLORS):
            R["violations"].append(["d-legend-marks", lnm, len(marks), len(LEG_COLORS)])
        else:
            for k, col in zip(marks, LEG_COLORS):
                got = tr.Characters.Item(k + 1).Font.Fill.ForeColor.RGB
                if got != col:
                    R["violations"].append(["d-legend-color", lnm, k + 1, got])
    return R


def main():
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    REP = {}
    try:
        for book, path in BOOKS.items():
            wb = app.Workbooks.Open(path, UpdateLinks=0, ReadOnly=True)
            wbk = {}
            for gi, gname in ((1, "相関図①"), (2, "相関図②"), (3, "相関図③")):
                wbk[gname] = check_sheet(wb.Worksheets(gname), gi)
            wb.Close(SaveChanges=False)
            REP[book] = wbk
            for gname, r in wbk.items():
                print("%s %s: shapes=%d nodes=%d violations=%d print=%s extent=%.0fx%.0f" % (
                    book, gname, r["shapes"], len(r["nodes"]), len(r["violations"]),
                    r["print_area"], r["extent"][0], r["extent"][1]))
                for v in r["violations"][:12]:
                    print("   ", v)
    finally:
        try:
            app.Quit()
        except Exception:
            pass
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(REP, f, ensure_ascii=False, indent=1, default=str)
    total = sum(len(r["violations"]) for bk in REP.values() for r in bk.values())
    print("TOTAL VIOLATIONS:", total)
    print("CHECK DONE")


if __name__ == "__main__":
    main()
