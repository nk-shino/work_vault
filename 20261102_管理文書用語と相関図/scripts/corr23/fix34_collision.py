# -*- coding: utf-8 -*-
"""collision_check.py -- 相関図②③ 修正前衝突検査 (読み取り専用).

geom_after.json を primary とし、不足フィールドは次の読み取り専用手段で補完する:
  - 線の反転状態: Excel COM に取得属性がないためブックの drawingml XML を解読
  - コネクタ接続状態: COM の ConnectorFormat を読取
図形テキスト本文は読み出さない・出力しない (要素IDと種別のみ)。
fix31_g8_check.py の判定基準を拡張し、次の5分類で全要素ペアを点検する:
  a 図形同士の矩形交差 (エッジ・帯は対象外。一方が他方を内包する場合は許容)
  b 線分と図形ボックスの交差 (接続端点の埋め込みは除外。内包コンテナの箱は対象外)
  c ラベル・テキスト同士の重なり (凡例内の整列・同一要素内は除外)
  d テキストの図形からの切れ (ノード txt の box 外はみ出し・フレームあふれ)
  e 線同士の不要な交差 (直交ルーティングで回避できるもの・共線重複を含む)
出力: collision_report_fix34.json (冊×シート×分類の違反数と違反要素ペアのID一覧)
"""
import sys, io, os, json, math, re, copy, datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "geom_fix34.json")
OUT = os.path.join(HERE, "collision_report_fix34.json")

BOOKS = {
    "pana": (r"C:/Users/ss80751/OneDrive - NK/ドキュメント/Work_Vault"
             r"/10_業務全般/PanaCIM_LNB/01_成果物/Pana-CIM管理手順書案_未承認.xlsx"),
    "lnb": (r"C:/Users/ss80751/OneDrive - NK/ドキュメント/Work_Vault"
            r"/10_業務全般/PanaCIM_LNB/01_成果物/LNB管理手順書案_未承認.xlsx"),
}
SHEETS = ["相関図②", "相関図③"]
EXPECTED = 36

TOL_DRIFT = 0.75      # JSON と実測の許容ずれ pt
OV_MIN = 1.0          # 矩形交差の面積しきい値 pt^2
CONTAIN_TOL = 1.0     # 内包(コンテナ設計)判定の許容 pt
BOX_SHRINK = 1.0      # (b) ボックス内側判定で縁の接触を無視する量 pt
STUB = 3.0            # (b) 接続端点の埋め込み許容長 pt
TOUCH = 2.0           # (b)(e) 端点が矩形・交点に触れているとみなす距離 pt
COLL = 0.5            # 共線(縦/横)判定の許容 pt
RIDE_MIN = 2.0        # (b) ボックス縁に乗る長さのしきい値 pt
FRAME_TOL = 0.75      # (d) フレームあふれの許容 pt

NODE_TAILS = ("n01", "n02", "n03", "n04", "n05", "n06r", "n07", "n08", "n09", "n10",
              "n11", "n12", "n13", "n14", "n15", "n16", "n17", "n18", "n19", "p1",
              "p2", "s1", "s2", "ea", "eb", "liner", "pcr", "dgsr")
LEG_RE = re.compile(r"^g\d_leg\d+$")


def cls_of(nm, typ):
    if nm.endswith("_band"):
        return "band"
    if nm.endswith("_bandhead"):
        return "bandhead"
    if "_e_" in nm and nm.endswith("_l"):
        return "label"
    if "_e_" in nm:
        return "edge"
    if typ == 6:
        return "node"
    if typ == 17:
        return "legend" if LEG_RE.match(nm) else "label"
    return "other"


def R(d):
    return (float(d["l"]), float(d["t"]), float(d["w"]), float(d["h"]))


def fig_rects(d):
    """(a) 判定用の実描画矩形リスト。グループは子図形(実体)の矩形群を
    使う。グループ bbox はタグなどの飛び出しを含む空虚な包絡線であり、
    bbox 同士の重なりは実在しない衝突を報告するため (fix34 で e05_l と
    n08 グループで発生)。子図形同士の交差のみを実衝突とみなす。"""
    if d.get("type") == 6 and d.get("children"):
        return [R(c) for c in d["children"]]
    return [R(d)]


def ov_area(a, b):
    w = min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0])
    h = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
    return max(0.0, w) * max(0.0, h)


def contains(a, b, tol=CONTAIN_TOL):
    return (b[0] >= a[0] - tol and b[1] >= a[1] - tol
            and b[0] + b[2] <= a[0] + a[2] + tol and b[1] + b[3] <= a[1] + a[3] + tol)


def in_rect(p, r, expand=TOUCH):
    return (r[0] - expand <= p[0] <= r[0] + r[2] + expand
            and r[1] - expand <= p[1] <= r[1] + r[3] + expand)


def orient(seg):
    dx = abs(seg[1][0] - seg[0][0])
    dy = abs(seg[1][1] - seg[0][1])
    if dx <= COLL and dy <= COLL:
        return "p"
    if dx <= COLL:
        return "v"
    if dy <= COLL:
        return "h"
    return "d"


def seg_len(seg):
    return math.hypot(seg[1][0] - seg[0][0], seg[1][1] - seg[0][1])


def seg_in_rect(seg, r, shrink=BOX_SHRINK):
    """線分の矩形内側区間を Liang-Barsky で求める。戻り値 (t0,t1) or None。"""
    l, t = r[0] + shrink, r[1] + shrink
    w, h = r[2] - 2 * shrink, r[3] - 2 * shrink
    if w <= 0 or h <= 0:
        return None
    x0, y0 = seg[0]
    x1, y1 = seg[1]
    dx, dy = x1 - x0, y1 - y0
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x0 - l), (dx, l + w - x0), (-dy, y0 - t), (dy, t + h - y0)):
        if abs(p) < 1e-12:
            if q < 0:
                return None
        else:
            rr = q / p
            if p < 0:
                if rr > t1:
                    return None
                if rr > t0:
                    t0 = rr
            else:
                if rr < t0:
                    return None
                if rr < t1:
                    t1 = rr
    if t1 - t0 <= 1e-9:
        return None
    return (t0, t1)


def ride_interval(seg, r):
    """線分が矩形の縁に共線で乗っている区間を (u0,u1) で返す。なければ None。"""
    o = orient(seg)
    (x0, y0), (x1, y1) = seg
    l, t, w, h = r
    if o == "v":
        for ex in (l, l + w):
            if abs(x0 - ex) <= COLL and abs(x1 - ex) <= COLL:
                a0, a1 = max(min(y0, y1), t), min(max(y0, y1), t + h)
                if a1 - a0 > 1e-9:
                    u0, u1 = (a0 - y0) / (y1 - y0), (a1 - y0) / (y1 - y0)
                    return (min(u0, u1), max(u0, u1))
    elif o == "h":
        for ey in (t, t + h):
            if abs(y0 - ey) <= COLL and abs(y1 - ey) <= COLL:
                a0, a1 = max(min(x0, x1), l), min(max(x0, x1), l + w)
                if a1 - a0 > 1e-9:
                    u0, u1 = (a0 - x0) / (x1 - x0), (a1 - x0) / (x1 - x0)
                    return (min(u0, u1), max(u0, u1))
    return None


def stub_cut(seg, r):
    """矩形に端点が触れている側の埋め込み許容長の合計。"""
    c = 0.0
    if in_rect(seg[0], r, TOUCH):
        c += STUB
    if in_rect(seg[1], r, TOUCH):
        c += STUB
    return c


def seg_pair_violation(s1, s2):
    """異なる線分ペアの交差関係を判定する。戻り値 (kind, d1, d2) or None。"""
    o1, o2 = orient(s1), orient(s2)
    if o1 == "p" or o2 == "p":
        return None
    if o1 == "d" or o2 == "d":
        (px, py), (qx, qy) = s1
        (rx, ry), (sx, sy) = s2
        rvx, rvy = qx - px, qy - py
        rsx, rsy = sx - rx, sy - ry
        den = rvx * rsy - rvy * rsx
        if abs(den) < 1e-9:
            return None
        tt = ((rx - px) * rsy - (ry - py) * rsx) / den
        uu = ((rx - px) * rvy - (ry - py) * rvx) / den
        if -1e-9 <= tt <= 1 + 1e-9 and -1e-9 <= uu <= 1 + 1e-9:
            d1 = min(tt, 1 - tt) * seg_len(s1)
            d2 = min(uu, 1 - uu) * seg_len(s2)
            if d1 > TOUCH and d2 > TOUCH:
                return ("cross", round(d1, 1), round(d2, 1))
        return None
    if {o1, o2} == {"v", "h"}:
        v = s1 if o1 == "v" else s2
        hh = s2 if o1 == "v" else s1
        xv = v[0][0]
        yh = hh[0][1]
        vy0, vy1 = min(v[0][1], v[1][1]), max(v[0][1], v[1][1])
        hx0, hx1 = min(hh[0][0], hh[1][0]), max(hh[0][0], hh[1][0])
        if vy0 - 1e-9 <= yh <= vy1 + 1e-9 and hx0 - 1e-9 <= xv <= hx1 + 1e-9:
            d1 = min(abs(yh - v[0][1]), abs(yh - v[1][1]))
            d2 = min(abs(xv - hh[0][0]), abs(xv - hh[1][0]))
            if d1 > TOUCH and d2 > TOUCH:
                return ("cross", round(d1, 1), round(d2, 1))
        return None
    if o1 == "v" and o2 == "v" and abs(s1[0][0] - s2[0][0]) <= COLL:
        lo = max(min(s1[0][1], s1[1][1]), min(s2[0][1], s2[1][1]))
        hi = min(max(s1[0][1], s1[1][1]), max(s2[0][1], s2[1][1]))
        if hi - lo > TOUCH:
            return ("collinear", round(hi - lo, 1), None)
    if o1 == "h" and o2 == "h" and abs(s1[0][1] - s2[0][1]) <= COLL:
        lo = max(min(s1[0][0], s1[1][0]), min(s2[0][0], s2[1][0]))
        hi = min(max(s1[0][0], s1[1][0]), max(s2[0][0], s2[1][0]))
        if hi - lo > TOUCH:
            return ("collinear", round(hi - lo, 1), None)
    return None


def build_edges(tops, flip9, warn):
    """エッジ要素の線分リストを作る。segid = 要素ID または 要素ID.セグメント名。"""
    edges = {}
    for sh in tops:
        nm = sh["name"]
        if cls_of(nm, sh["type"]) != "edge":
            continue
        segs = []
        if int(sh["type"]) == 9:
            s = line_seg(sh, flip9.get(nm, (False, False)))
            if s:
                segs.append((nm, s))
        else:
            for c in sh.get("children", []):
                s = child_seg(c)
                if s:
                    segs.append((nm + "." + c["name"].split("_")[-1], s))
        if segs:
            edges[nm] = segs
    return edges


def line_seg(sh, flip):
    l, t, w, h = float(sh["l"]), float(sh["t"]), float(sh["w"]), float(sh["h"])
    fh, fv = flip
    if w <= COLL and h <= COLL:
        return None
    if w <= COLL:
        return ((l, t), (l, t + h))
    if h <= COLL:
        return ((l, t), (l + w, t))
    x0, x1 = (l + w, l) if fh else (l, l + w)
    y0, y1 = (t + h, t) if fv else (t, t + h)
    return ((x0, y0), (x1, y1))


def child_seg(c):
    l, t, w, h = float(c["l"]), float(c["t"]), float(c["w"]), float(c["h"])
    if w <= COLL and h <= COLL:
        return None
    if w <= COLL:
        return ((l, t), (l, t + h))
    if h <= COLL:
        return ((l, t), (l + w, t))
    return ((l, t), (l + w, t + h))  # 斜め子セグメント: 反転未読のため TL-BR 仮定


def build_texts(tops):
    """テキストを持つ矩形のリスト (id, rect, parent, kindlabel, tf)。"""
    texts = []
    for sh in tops:
        cls = cls_of(sh["name"], sh["type"])
        if sh.get("tf"):
            texts.append((sh["name"], R(sh), sh["name"], cls, sh["tf"]))
        if int(sh["type"]) == 6:
            for c in sh.get("children", []):
                if c.get("tf"):
                    if c["name"].endswith("_txt"):
                        k = "txt"
                    elif c["name"].endswith("_tag"):
                        k = "tag"
                    else:
                        k = "membertext"
                    texts.append((c["name"], R(c), sh["name"], k, c["tf"]))
    return texts


def check_a(tops):
    figs = [sh for sh in tops
            if cls_of(sh["name"], sh["type"]) not in ("band", "edge")]
    out = []
    for i in range(len(figs)):
        for j in range(i + 1, len(figs)):
            a, b = figs[i], figs[j]
            ca = cls_of(a["name"], a["type"])
            cb = cls_of(b["name"], b["type"])
            if ca == "legend" and cb == "legend":
                continue
            ra_list, rb_list = fig_rects(a), fig_rects(b)
            hit = None
            for ra in ra_list:
                for rb in rb_list:
                    if contains(ra, rb) or contains(rb, ra):
                        continue
                    ov = ov_area(ra, rb)
                    if ov <= OV_MIN:
                        continue
                    hit = ov
                    break
                if hit is not None:
                    break
            if hit is None:
                continue
            if a.get("tf") and b.get("tf"):
                continue  # テキスト同士は分類 c
            out.append({"kind": "-".join(sorted([ca, cb])), "a": a["name"], "b": b["name"]})
    return out


def check_c(texts):
    out = []
    for i in range(len(texts)):
        for j in range(i + 1, len(texts)):
            ida, ra, pa, ka, _ = texts[i]
            idb, rb, pb, kb, _ = texts[j]
            if pa == pb:
                continue
            if ka == "legend" and kb == "legend":
                continue  # 凡例内の整列は除外
            ov = ov_area(ra, rb)
            if ov > OV_MIN:
                out.append({"kind": "-".join(sorted([ka, kb])), "a": ida, "b": idb})
    return out


def check_b(edges, targets):
    out = []
    for eid, segs in edges.items():
        for sid, seg in segs:
            for tid, tr in targets:
                iv = seg_in_rect(seg, tr)
                if iv is not None:
                    inside = (iv[1] - iv[0]) * seg_len(seg)
                    rest = inside - stub_cut(seg, tr)
                    if rest > 0.5:
                        out.append({"kind": "cross", "a": sid, "b": tid, "len": round(rest, 1)})
                    continue
                ui = ride_interval(seg, tr)
                if ui is not None:
                    ride = (ui[1] - ui[0]) * seg_len(seg)
                    rest = ride - stub_cut(seg, tr)
                    if rest > 0.5:
                        out.append({"kind": "ride", "a": sid, "b": tid, "len": round(rest, 1)})
    return out


def check_e(edges):
    items = [(eid, sid, seg) for eid, segs in edges.items() for sid, seg in segs]
    out = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i][0] == items[j][0]:
                continue  # 同一エッジ内の継ぎ目は除外
            v = seg_pair_violation(items[i][2], items[j][2])
            if v:
                out.append({"kind": v[0], "a": items[i][1], "b": items[j][1],
                            "d": [v[1], v[2]] if v[0] == "cross" else [v[1]]})
    return out


def check_d(tops, texts):
    out = []
    for sh in tops:
        if cls_of(sh["name"], sh["type"]) != "node":
            continue
        kids = sh.get("children", [])
        box = next((c for c in kids if c["name"].endswith("_box")), None)
        txt = next((c for c in kids if c["name"].endswith("_txt")), None)
        if box is not None and txt is not None and not contains(R(box), R(txt), 2.0):
            out.append({"kind": "txt-out", "a": txt["name"], "b": box["name"]})
    for id_, r, parent, kind, tf in texts:
        aw = r[2] - tf["mL"] - tf["mR"]
        ah = r[3] - tf["mT"] - tf["mB"]
        if tf["boundW"] > aw + FRAME_TOL or tf["boundH"] > ah + FRAME_TOL:
            out.append({"kind": "frame", "a": id_, "b": parent,
                        "over": [round(tf["boundW"] - aw, 1), round(tf["boundH"] - ah, 1)]})
    return out


def container_nodes(tops):
    """他のノードグループを内包するノード (コンテナ設計) の名前集合。"""
    nodes = [sh for sh in tops if cls_of(sh["name"], sh["type"]) == "node"]
    cont = set()
    for a in nodes:
        ra = R(a)
        for b in nodes:
            if a["name"] == b["name"]:
                continue
            if contains(ra, R(b), 1.0):
                cont.add(a["name"])
                break
    return cont


def live_pass():
    """実ブックから図形数・実座標・線の反転・コネクタ接続を読む (読み取り専用)。

    反転属性は gen_py 型付きラッパで AttributeError になるため (corr23_probe.py と
    同一の事象)、動的ディスパッチ (遅延バインド) で読み直す。
    """
    import win32com.client as win32
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    try:
        app.ScreenUpdating = False
    except Exception:
        pass
    info = {}
    try:
        for bk, path in BOOKS.items():
            wb = app.Workbooks.Open(path, UpdateLinks=0, ReadOnly=True)
            bkd = {}
            for sn in SHEETS:
                ws = wb.Worksheets(sn)
                cnt = int(ws.Shapes.Count)
                tops, kids, flip9, conn = {}, {}, {}, {}
                objs = {}
                for i in range(1, cnt + 1):
                    sh = ws.Shapes(i)
                    nm = sh.Name
                    objs[nm] = sh
                    tops[nm] = (float(sh.Left), float(sh.Top), float(sh.Width), float(sh.Height))
                for nm, sh in objs.items():
                    t = int(sh.Type)
                    if t == 9:
                        # 反転状態は Excel COM に取得属性がないため XML 読み取りで補完する
                        try:
                            if bool(sh.Connector):
                                cf = sh.ConnectorFormat
                                bc = bool(cf.BeginConnected)
                                ec = bool(cf.EndConnected)
                                conn[nm] = [cf.BeginConnectedShape.Name if bc else None,
                                            cf.EndConnectedShape.Name if ec else None]
                        except Exception:
                            pass
                    elif t == 6:
                        gi = sh.GroupItems
                        kd = {}
                        for k in range(1, int(gi.Count) + 1):
                            m = gi.Item(k)
                            kd[m.Name] = (float(m.Left), float(m.Top), float(m.Width), float(m.Height))
                        kids[nm] = kd
                bkd[sn] = {"count": cnt, "tops": tops, "kids": kids,
                           "flip9": flip9, "conn": conn}
            wb.Close(SaveChanges=False)
            info[bk] = bkd
            print("live read:", bk, {sn: bkd[sn]["count"] for sn in SHEETS})
    finally:
        try:
            app.Quit()
        except Exception:
            pass
    return info


NS_MAIN = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
NS_SHEET = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
NS_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
NS_PKGREL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
NS_XDR = "{http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing}"


def _norm_part(base_dir, target):
    t = target
    if t.startswith("/"):
        return t.lstrip("/")
    parts = [p for p in (base_dir + "/" + t).split("/") if p not in ("", ".")]
    out = []
    for p in parts:
        if p == "..":
            if out:
                out.pop()
        else:
            out.append(p)
    return "/".join(out)


def read_flips_xml(path, sheets):
    """xlsx の drawingml からトップレベル図形の flipH/flipV を読む (読み取り専用)。

    Excel COM には図形の反転状態を取得する属性がないため、ブックの
    xl/drawings/drawingN.xml を直接解読する。テキスト本文は読まない。
    戻り値: {シート名: {図形名: (flipH, flipV)}}
    """
    import zipfile
    import xml.etree.ElementTree as ET
    out = {sn: {} for sn in sheets}
    with zipfile.ZipFile(path) as z:
        wbx = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        relmap = {e.get("Id"): e.get("Target") for e in rels}
        for sh in wbx.find(NS_SHEET + "sheets"):
            nm = sh.get("name")
            if nm not in out:
                continue
            rid = sh.get(NS_REL + "id")
            sheet_part = _norm_part("xl", relmap[rid])
            d = sheet_part.rsplit("/", 1)
            base_dir = d[0] if len(d) == 2 else "xl"
            rels_part = base_dir + "/_rels/" + (d[1] if len(d) == 2 else d[0]) + ".rels"
            drawing_part = None
            try:
                srels = ET.fromstring(z.read(rels_part))
            except KeyError:
                srels = []
            for e in srels:
                if e.get("Type", "").endswith("/drawing"):
                    drawing_part = _norm_part(base_dir, e.get("Target"))
            if not drawing_part:
                continue
            dx = ET.fromstring(z.read(drawing_part))
            for anchor in dx:
                objs = [k for k in anchor
                        if k.tag not in (NS_XDR + "from", NS_XDR + "to", NS_XDR + "ext",
                                         NS_XDR + "clientData")]
                if not objs:
                    continue
                obj = objs[0]
                if obj.tag == NS_XDR + "grpSp":
                    continue  # グループ子は正交セグメントのみで反転不要
                nv = obj.find(".//" + NS_XDR + "cNvPr")
                xfrm = obj.find(NS_XDR + "spPr/" + NS_MAIN + "xfrm")
                if nv is None or xfrm is None:
                    continue
                fh = xfrm.get("flipH") in ("1", "true")
                fv = xfrm.get("flipV") in ("1", "true")
                out[nm][nv.get("name")] = (fh, fv)
    return out


def build_model(src_sheet, lv):
    """JSON モデルを複製し、実測と TOL_DRIFT を超えるずれがあれば実測値へ補正する。"""
    model = copy.deepcopy(src_sheet)
    drift = []
    live_tops = lv["tops"]
    live_kids = lv["kids"]
    for sh in model["shapes"]:
        nm = sh["name"]
        if nm not in live_tops:
            drift.append({"name": nm, "why": "missing-live"})
            continue
        lt = live_tops[nm]
        for k, idx in (("l", 0), ("t", 1), ("w", 2), ("h", 3)):
            if abs(float(sh[k]) - lt[idx]) > TOL_DRIFT:
                drift.append({"name": nm, "field": k,
                              "json": float(sh[k]), "live": round(lt[idx], 2)})
                sh[k] = round(lt[idx], 2)
        if int(sh["type"]) == 6 and nm in live_kids:
            lk = live_kids[nm]
            for c in sh.get("children", []):
                if c["name"] in lk:
                    kl = lk[c["name"]]
                    for k, idx in (("l", 0), ("t", 1), ("w", 2), ("h", 3)):
                        if abs(float(c[k]) - kl[idx]) > TOL_DRIFT:
                            drift.append({"name": c["name"], "field": k,
                                          "json": float(c[k]), "live": round(kl[idx], 2)})
                            c[k] = round(kl[idx], 2)
    return model, drift


def sortkey(v):
    return (v.get("kind", ""), str(v.get("a", "")), str(v.get("b", "")))


def check_sheet(model, flips):
    tops = model["shapes"]
    warn = {"assumed_diag": 0}
    edges = build_edges(tops, flips, warn)
    containers = container_nodes(tops)
    targets = []
    excluded = []
    for sh in tops:
        cls = cls_of(sh["name"], sh["type"])
        if cls == "bandhead":
            targets.append((sh["name"], R(sh)))
        elif cls == "node":
            if sh["name"] in containers:
                # コンテナ箱: 内側ノードへの出入りは設計上の通過のため (b) 対象外
                for c in sh.get("children", []):
                    if c["name"].endswith("_box"):
                        excluded.append(c["name"])
                continue
            for c in sh.get("children", []):
                if c["name"].endswith("_box"):
                    targets.append((c["name"], R(c)))
    texts = build_texts(tops)
    cats = {
        "a": sorted(check_a(tops), key=sortkey),
        "b": sorted(check_b(edges, targets), key=sortkey),
        "c": sorted(check_c(texts), key=sortkey),
        "d": sorted(check_d(tops, texts), key=sortkey),
        "e": sorted(check_e(edges), key=sortkey),
    }
    return cats, warn, {"b_excluded_containers": excluded, "containers": sorted(containers)}


def main():
    with open(SRC, encoding="utf-8") as f:
        src = json.load(f)
    print("COM read (ReadOnly) start ...")
    live = live_pass()
    print("COM read done.")
    print("drawingml flip read (ReadOnly zip) ...")
    flips_xml = {bk: read_flips_xml(path, SHEETS) for bk, path in BOOKS.items()}
    print("drawingml flip read done.")

    rep = {
        "meta": {
            "script": "fix34_collision.py",
            "source": "geom_fix34.json",
            "mode": "post-fix34",
            "sheets": SHEETS,
            "generated": datetime.datetime.now().isoformat(timespec="seconds"),
            "note": "element IDs and kind labels only; no shape text",
        },
        "shape_count": {},
        "drift": {},
        "complement": {},
        "books": {},
        "totals": {"by_category": {k: 0 for k in "abcde"}, "grand": 0},
    }
    for bk in ("pana", "lnb"):
        rep["shape_count"][bk] = {}
        rep["drift"][bk] = {}
        rep["complement"][bk] = {}
        rep["books"][bk] = {}
        for sn in SHEETS:
            lv = live[bk][sn]
            json_cnt = len(src[bk][sn]["shapes"])
            ok = (json_cnt == EXPECTED and lv["count"] == EXPECTED and json_cnt == lv["count"])
            rep["shape_count"][bk][sn] = {"expected": EXPECTED, "json": json_cnt,
                                          "live": lv["count"], "ok": ok}
            model, drift = build_model(src[bk][sn], lv)
            rep["drift"][bk][sn] = drift
            conns = [{"shape": k, "begin": v[0], "end": v[1]}
                     for k, v in sorted(lv["conn"].items())]
            flips = flips_xml[bk][sn]
            rep["complement"][bk][sn] = {
                "flip_read": len(flips),
                "flip_source": "drawingml-xml",
                "flip": {k: list(v) for k, v in sorted(flips.items())},
                "connectors": conns,
            }
            cats, warn, extra = check_sheet(model, flips)
            total = sum(len(v) for v in cats.values())
            rep["books"][bk][sn] = {
                "by_category": {k: len(v) for k, v in cats.items()},
                "total": total,
                "b_excluded_containers": extra["b_excluded_containers"],
                "violations": cats,
            }
            if warn.get("assumed_diag"):
                rep["books"][bk][sn]["assumed_diag_segments"] = warn["assumed_diag"]
            for k in "abcde":
                rep["totals"]["by_category"][k] += len(cats[k])
            rep["totals"]["grand"] += total
            print("%s %s: a=%d b=%d c=%d d=%d e=%d total=%d (shapes json=%d live=%d drift=%d)" % (
                bk, sn, len(cats["a"]), len(cats["b"]), len(cats["c"]), len(cats["d"]),
                len(cats["e"]), total, json_cnt, lv["count"], len(drift)))
            for cat in "abcde":
                for v in cats[cat]:
                    print("   %s %s | a=%s b=%s%s" % (
                        cat, v["kind"], v.get("a", ""), v.get("b", ""),
                        (" len=%s" % v["len"]) if "len" in v else
                        ((" d=%s" % v["d"]) if "d" in v else "")))

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=1)
    print("TOTAL BY CATEGORY:", rep["totals"]["by_category"])
    print("GRAND TOTAL:", rep["totals"]["grand"])
    print("REPORT ->", OUT)
    print("CHECK DONE")


if __name__ == "__main__":
    main()
