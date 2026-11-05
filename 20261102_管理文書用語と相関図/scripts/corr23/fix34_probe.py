# -*- coding: utf-8 -*-
"""fix34_probe.py — クリップ5ラベル(N07·N11·N09·N17·N18)の現状実測。
vault正本を読み取り専用で開き、対象図形の全文·幾何·TextFrame設定を出力する。
併せて LNB 全シートのフッター文字列と Pana のシート名一覧を出す。保存しない。
"""
import sys, io, os, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import win32com.client as win32

VAULT = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
BOOKS = {
    "pana": os.path.join(VAULT, "Pana-CIM管理手順書案_未承認.xlsx"),
    "lnb": os.path.join(VAULT, "LNB管理手順書案_未承認.xlsx"),
}
MARKERS = {
    "N17": "BackUP_DB",
    "N18": "XML/DB",
    "N07": "断定しない",
    "N11": "LWSエディター",
    "N09": "アンドン",
}
TARGET_SHEETS = ["相関図②", "相関図③"]


def r1(v):
    try:
        return round(float(v), 2)
    except Exception:
        return None


def walk(sh, out, depth=0):
    t = int(sh.Type)
    if t == 6:  # group
        for i in range(1, sh.GroupItems.Count + 1):
            walk(sh.GroupItems.Item(i), out, depth + 1)
        return
    try:
        tf = sh.TextFrame2
        if not tf.HasText:
            return
        text = tf.TextRange.Text
    except Exception:
        return
    hit = None
    for tag, mk in MARKERS.items():
        if mk in text:
            hit = tag
            break
    if hit is None:
        return
    rec = {
        "tag": hit, "name": sh.Name, "type": t, "depth": depth,
        "l": r1(sh.Left), "t": r1(sh.Top), "w": r1(sh.Width), "h": r1(sh.Height),
        "text": text,
        "paras": int(tf.TextRange.Paragraphs.Count),
        "wrap": bool(tf.WordWrap), "autosize": int(tf.AutoSize),
        "mL": r1(tf.MarginLeft), "mR": r1(tf.MarginRight),
        "mT": r1(tf.MarginTop), "mB": r1(tf.MarginBottom),
        "hAnchor": int(tf.HorizontalAnchor), "vAnchor": int(tf.VerticalAnchor),
        "boundW": r1(tf.TextRange.BoundWidth), "boundH": r1(tf.TextRange.BoundHeight),
    }
    try:
        f = tf.TextRange.Font
        rec["font"] = {"name": f.Name, "size": r1(f.Size), "fill": int(f.Fill.ForeColor.RGB)}
    except Exception:
        rec["font"] = None
    try:
        rec["lineW"] = r1(sh.Line.Weight)
    except Exception:
        pass
    out.append(rec)


def main():
    rep = {}
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    try:
        for bk, path in BOOKS.items():
            wb = app.Workbooks.Open(path, UpdateLinks=0, ReadOnly=True)
            d = {"clips": [], "sheets": []}
            for sn in TARGET_SHEETS:
                ws = wb.Worksheets(sn)
                for i in range(1, ws.Shapes.Count + 1):
                    walk(ws.Shapes(i), d["clips"])
            for i in range(1, wb.Worksheets.Count + 1):
                ws = wb.Worksheets(i)
                ps = ws.PageSetup
                d["sheets"].append({
                    "name": ws.Name, "vis": int(ws.Visible),
                    "lf": ps.LeftFooter, "cf": ps.CenterFooter, "rf": ps.RightFooter,
                })
            wb.Close(SaveChanges=False)
            rep[bk] = d
            print(bk, "clips:", len(d["clips"]), "sheets:", len(d["sheets"]))
    finally:
        try:
            app.Quit()
        except Exception:
            pass
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fix34_probe.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    for bk, d in rep.items():
        print("==", bk)
        for c in d["clips"]:
            print(f"  [{c['tag']}] {c['name']} l={c['l']} t={c['t']} w={c['w']} h={c['h']} "
                  f"wrap={c['wrap']} paras={c['paras']} boundW={c['boundW']} boundH={c['boundH']} "
                  f"font={c['font']['size'] if c['font'] else '?'}")
            print("      text:", repr(c["text"][:120]))
    print("PROBE DONE ->", out)


if __name__ == "__main__":
    main()
