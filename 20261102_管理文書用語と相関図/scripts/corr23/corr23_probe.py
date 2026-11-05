# -*- coding: utf-8 -*-
"""corr23_probe.py — 相関図①②③の全図形幾何をCOM実測でJSONへ出力する。
テキスト本文は出力しない(名前·数値·スタイル属性のみ)。読み取り専用。
"""
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import win32com.client as win32

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geom_before.json")
BOOKS = {
    "pana": (r"C:/Users/ss80751/OneDrive - NK/ドキュメント/Work_Vault"
             r"/10_業務全般/PanaCIM_LNB/01_成果物/Pana-CIM管理手順書案_未承認.xlsx"),
    "lnb": (r"C:/Users/ss80751/OneDrive - NK/ドキュメント/Work_Vault"
            r"/10_業務全般/PanaCIM_LNB/01_成果物/LNB管理手順書案_未承認.xlsx"),
}
SHEETS = ["相関図①", "相関図②", "相関図③"]


def r1(v):
    return round(float(v), 2)


def shape_info(sh, depth=0):
    d = {
        "name": sh.Name,
        "type": int(sh.Type),
        "l": r1(sh.Left), "t": r1(sh.Top), "w": r1(sh.Width), "h": r1(sh.Height),
        "rot": r1(sh.Rotation),
    }
    if int(sh.Type) == 6:  # group
        kids = [sh.GroupItems.Item(i) for i in range(1, sh.GroupItems.Count + 1)]
        d["children"] = [shape_info(k, depth + 1) for k in kids]
    else:
        try:
            if int(sh.Type) == 9 or sh.ConnectorFormat is not None:
                pass
        except Exception:
            pass
        try:
            ln = sh.Line
            d["line"] = {
                "visible": bool(ln.Visible),
                "weight": r1(ln.Weight),
                "dash": int(ln.DashStyle),
                "rgb": int(ln.ForeColor.RGB) if ln.Visible else None,
                "arrowEnd": int(ln.EndArrowheadStyle),
                "arrowBegin": int(ln.BeginArrowheadStyle),
            }
        except Exception:
            pass
        try:
            d["flipH"] = bool(sh.FlipHorizontal)
            d["flipV"] = bool(sh.FlipVertical)
        except Exception:
            pass
        try:
            tf = sh.TextFrame2
            has_text = tf.HasText
            d["tf"] = None
            if has_text:
                tr = tf.TextRange
                d["tf"] = {
                    "autosize": int(tf.AutoSize),
                    "wrap": bool(tf.WordWrap),
                    "mL": r1(tf.MarginLeft), "mR": r1(tf.MarginRight),
                    "mT": r1(tf.MarginTop), "mB": r1(tf.MarginBottom),
                    "hAnchor": int(tf.HorizontalAnchor),
                    "vAnchor": int(tf.VerticalAnchor),
                    "boundW": r1(tr.BoundWidth),
                    "boundH": r1(tr.BoundHeight),
                    "paras": int(tr.Paragraphs.Count),
                }
        except Exception:
            d["tf"] = None
        try:
            d["fill"] = int(sh.Fill.ForeColor.RGB) if sh.Fill.Visible else None
        except Exception:
            d["fill"] = None
    return d


def main():
    rep = {}
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    try:
        for bk, path in BOOKS.items():
            wb = app.Workbooks.Open(path, UpdateLinks=0, ReadOnly=True)
            wbd = {}
            for sn in SHEETS:
                ws = wb.Worksheets(sn)
                sd = {"shapes": [], "pagesetup": {}}
                for i in range(1, ws.Shapes.Count + 1):
                    sd["shapes"].append(shape_info(ws.Shapes(i)))
                ps = ws.PageSetup
                sd["pagesetup"] = {
                    "printArea": ps.PrintArea,
                    "fitW": ps.FitToPagesWide, "fitT": ps.FitToPagesTall,
                    "paper": int(ps.PaperSize), "orient": int(ps.Orientation),
                }
                # 印字範囲の実セル範囲幾何
                pa = ps.PrintArea
                try:
                    rng = ws.Range(pa.split(":")[1])
                    sd["paRect"] = {"right": r1(rng.Left + rng.Width), "bottom": r1(rng.Top + rng.Height)}
                except Exception:
                    sd["paRect"] = None
                wbd[sn] = sd
            wb.Close(SaveChanges=False)
            rep[bk] = wbd
            print(bk, "probed", {sn: len(wbd[sn]["shapes"]) for sn in SHEETS})
    finally:
        try:
            app.Quit()
        except Exception:
            pass
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    print("PROBE DONE ->", OUT)


if __name__ == "__main__":
    main()
