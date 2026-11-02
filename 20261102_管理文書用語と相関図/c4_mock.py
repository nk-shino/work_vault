# -*- coding: utf-8 -*-
"""C4-style redesign mock: 3 diagrams (context / mgmt internals / line internals) + list 2p.
C4 rules applied: title+audience+scope per diagram, legend, element kind prefix + one-line duty,
concrete labels on every line, one-way arrows, abbreviation notes."""
import os
from PIL import Image, ImageDraw, ImageFont

DL = os.path.dirname(os.path.abspath(__file__))
ICONS = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図\icons"
OUTDIR = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
JP = "C:/Windows/Fonts/meiryo.ttc"
S = 3.0

INK = (31, 31, 31)
GRAY = (89, 89, 89)
LINE = (0, 0, 0)
DASHGRAY = (128, 128, 128)

PAL = {
    "srv_fill": (235, 222, 247), "srv_line": (128, 100, 162),
    "term_fill": (255, 255, 255), "term_line": (155, 187, 89),
    "eqp_fill": (255, 255, 255), "eqp_line": (160, 82, 70),
    "head_fill": (64, 64, 64),
}
STYLE = {
    "srv":  (PAL["srv_fill"], PAL["srv_line"], 1.0, False),
    "term": (PAL["term_fill"], PAL["term_line"], 1.0, False),
    "eqp":  (PAL["eqp_fill"], PAL["eqp_line"], 2.25, False),
    "cont": (PAL["srv_fill"], PAL["srv_line"], 2.25, False),
    "est":  ((242, 242, 242), (128, 128, 128), 1.0, True),
    "ext":  ((255, 255, 255), (127, 127, 127), 1.0, False),
    "person": ((232, 232, 232), (89, 89, 89), 1.25, False),
    "sys":  (PAL["srv_fill"], PAL["srv_line"], 2.0, False),
    "xref": ((255, 255, 255), (150, 150, 150), 1.0, "x"),
}

def jf(px_size, bold=False):
    if bold:
        return ImageFont.truetype("C:/Windows/Fonts/meiryoB.ttc", int(px_size), index=0)
    return ImageFont.truetype(JP, int(px_size), index=0)

def F(pt):
    return pt * S

class CV:
    def __init__(self, w_pt, h_pt):
        self.w_pt, self.h_pt = w_pt, h_pt
        self.im = Image.new("RGB", (int(w_pt * S), int(h_pt * S)), "white")
        self.d = ImageDraw.Draw(self.im)

    def rect(self, x, y, w, h, fill=None, outline=None, width_pt=1.0, radius=0):
        box = [F(x), F(y), F(x + w), F(y + h)]
        if radius:
            self.d.rounded_rectangle(box, radius=F(radius), fill=fill, outline=outline, width=max(1, round(width_pt * S)))
        else:
            self.d.rectangle(box, fill=fill, outline=outline, width=max(1, round(width_pt * S)))

    def line(self, pts, fill=None, width_pt=1.0, dash=None):
        p = [(F(x), F(y)) for x, y in pts]
        if not dash:
            self.d.line(p, fill=fill, width=max(1, round(width_pt * S)))
            for q in p:
                r = width_pt * S / 2
                self.d.ellipse([q[0] - r, q[1] - r, q[0] + r, q[1] + r], fill=fill)
        else:
            dashlen, gaplen = dash
            for (x1, y1), (x2, y2) in zip(p, p[1:]):
                seg = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                if seg == 0:
                    continue
                n = int(seg // (dashlen + gaplen)) + 1
                for i in range(n):
                    t0 = i * (dashlen + gaplen) / seg
                    t1 = min(1.0, (i * (dashlen + gaplen) + dashlen) / seg)
                    if t0 >= 1:
                        break
                    self.d.line([x1 + (x2 - x1) * t0, y1 + (y2 - y1) * t0,
                                 x1 + (x2 - x1) * t1, y1 + (y2 - y1) * t1], fill=fill, width=max(1, round(width_pt * S)))

    def arrow(self, x, y, dx, dy, size_pt=5.0, fill=None):
        size = F(size_pt)
        x, y = F(x), F(y)
        if dx == 0 and dy == 0:
            return
        n = ((dx ** 2 + dy ** 2) ** 0.5)
        ux, uy = dx / n, dy / n
        tip = (x + ux * size, y + uy * size)
        left = (x - uy * size * 0.6, y + ux * size * 0.6)
        right = (x + uy * size * 0.6, y - ux * size * 0.6)
        self.d.polygon([tip, left, right], fill=fill)

    def text(self, x, y, s, size_pt, fill=INK, anchor="la", font=None, halo=False):
        f = font or jf(size_pt * S)
        pos = (F(x), F(y))
        if halo:
            bb = self.d.textbbox(pos, s, font=f, anchor=anchor)
            pad = 2
            self.d.rectangle([bb[0] - pad, bb[1] - pad, bb[2] + pad, bb[3] + pad], fill="white")
        self.d.text(pos, s, font=f, fill=fill, anchor=anchor)

    def tlen(self, s, size_pt, bold=False):
        return self.d.textlength(s, font=jf(size_pt * S, bold)) / S

ICON_CACHE = {}
def icon(key, size_pt):
    px = int(size_pt * S)
    if key not in ICON_CACHE or ICON_CACHE[key][0] != px:
        im = Image.open(os.path.join(ICONS, f"{key}.png")).convert("RGBA")
        im = im.resize((px, px), Image.LANCZOS)
        ICON_CACHE[key] = (px, im)
    return ICON_CACHE[key][1]

OX, OY = 0.0, 0.0
CHECKS = []  # (page, kind, owner, x0, y0, x1, y1)  kind: node/cbord/label/ntext/chip/icon/seg/arr
LABELQ = []  # (cv, x, y, text, size)  エッジラベル待ち行列(ノード描画後に最前面で描画)
ARRQ = []    # (eid, tip, x0, y0, x1, y1)  矢頭待ち行列(ノード登録後に所有ノードを確定)
EXEMPT_EIDS = {frozenset(("N07", "band_b"))}  # LNBの帯境界跨りは設計意図

def reg(page, kind, owner, x0, y0, x1, y1):
    CHECKS.append((page, kind, owner, x0, y0, x1, y1))

def reg_cbord(page, owner, x0, y0, x1, y1, t=1.5):
    reg(page, "cbord", owner + ":t", x0, y0, x1, y0 + t)
    reg(page, "cbord", owner + ":b", x0, y1 - t, x1, y1)
    reg(page, "cbord", owner + ":l", x0, y0, x0 + t, y1)
    reg(page, "cbord", owner + ":r", x1 - t, y0, x1, y1)

def eid_of(owner):
    if isinstance(owner, tuple):
        return owner[0]
    return str(owner).split(":")[0]

def text_rect(cv, x, y, s, size_pt, bold=False, anchor="la", pad=0.5):
    bb = cv.d.textbbox((F(x), F(y)), s, font=jf(size_pt * S, bold), anchor=anchor)
    return ((bb[0] - pad * S) / S, (bb[1] - pad * S) / S, (bb[2] + pad * S) / S, (bb[3] + pad * S) / S)

def find_node_owner(page, px, py):
    best, ba = None, None
    for (p, k, o, x0, y0, x1, y1) in CHECKS:
        if p != page or k != "node":
            continue
        if x0 - 2 <= px <= x1 + 2 and y0 - 2 <= py <= y1 + 2:
            a = (x1 - x0) * (y1 - y0)
            if ba is None or a < ba:
                best, ba = o, a
    return best

def fmt_owner(kind, owner):
    if kind == "seg":
        return "seg:" + str(owner[0])
    if kind == "arr":
        return "arr:" + str(owner[0])
    return f"{kind}:{owner}"

def draw_node(cv, x, y, w, h, cls, num, icon_key, name, duty=None, fs=10.5, dfs=8.5):
    x, y = x + OX, y + OY
    oid = num or name[:8]
    fill, line, bw, dashed = STYLE[cls]
    if dashed == "x":
        cv.rect(x, y, w, h, fill=fill, outline=None)
        cv.line([(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)], fill=line, width_pt=bw, dash=(4, 2.5))
    elif dashed:
        cv.rect(x, y, w, h, fill=fill, outline=None)
        cv.line([(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)], fill=line, width_pt=bw, dash=(4, 2.4))
    else:
        cv.rect(x, y, w, h, fill=fill, outline=line, width_pt=bw, radius=6)
    tx = x + 8
    if icon_key:
        isz = 13
        cv.im.paste(icon(icon_key, isz), (int(F(x + 6)), int(F(y + 8))), icon(icon_key, isz))
        tx = x + 6 + isz + 5
        reg(PAGE, "icon", oid, x + 6, y + 8, x + 6 + isz, y + 8 + isz)
    nfs = fs
    cv.text(tx, y + 7, name, nfs, anchor="la", font=jf(nfs * S, True))
    reg(PAGE, "ntext", oid, *text_rect(cv, tx, y + 7, name, nfs, bold=True))
    lines_used = 1
    if duty:
        cv.text(tx, y + 7 + nfs + 2.5, duty, dfs, anchor="la", fill=(96, 96, 96))
        reg(PAGE, "ntext", oid, *text_rect(cv, tx, y + 7 + nfs + 2.5, duty, dfs))
        lines_used = 2
    if num:
        cw = cv.tlen(num, 9) + 8
        ch = 13
        cv.rect(x - 1, y - ch / 2, cw, ch, fill="white", outline=GRAY, width_pt=0.75, radius=3)
        cv.text(x - 1 + cw / 2, y, num, 9, fill=(64, 64, 64), anchor="mm")
        reg(PAGE, "chip", oid, x - 1, y - ch / 2, x - 1 + cw, y + ch / 2)
    reg(PAGE, "node", oid, x, y, x + w, y + h)

def elabel(cv, x, y, s, size=9.5, page_reg=True):
    x, y = x + OX, y + OY
    cv.text(x, y, s, size, fill=(64, 64, 64), anchor="mm", halo=True)
    if page_reg:
        w = cv.tlen(s, size) + 2.0
        reg(PAGE, "label", s, x - w / 2, y - size * 0.75, x + w / 2, y + size * 0.75)

def edge(cv, pts, solid=True, arrow=False, lab=None, labpos=None, tag=None, tagpos=None):
    p = [(OX + q[0], OY + q[1]) for q in pts]
    eid = lab or tag or ("edge#%d" % len(CHECKS))
    if solid:
        cv.line(p, fill=LINE, width_pt=1.0)
    else:
        cv.line(p, fill=DASHGRAY, width_pt=1.0, dash=(5, 3))
    for (xa, ya), (xb, yb) in zip(p, p[1:]):
        reg(PAGE, "seg", (eid, xa, ya, xb, yb),
            min(xa, xb) - 0.6, min(ya, yb) - 0.6, max(xa, xb) + 0.6, max(ya, yb) + 0.6)
    if arrow:
        (x1, y1), (x2, y2) = p[-2], p[-1]
        cv.arrow(x2, y2, x2 - x1, y2 - y1, fill=(LINE if solid else DASHGRAY))
        n = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5 or 1.0
        ux, uy = (x2 - x1) / n, (y2 - y1) / n
        tip = (x2 + ux * 5.0, y2 + uy * 5.0)
        tri = [tip, (x2 - uy * 3.0, y2 + ux * 3.0), (x2 + uy * 3.0, y2 - ux * 3.0)]
        # 矢頭の所有ノードはノード描画後に確定するため待ち行列へ(基準②の描画順対応)
        ARRQ.append((eid, tip,
            min(q[0] for q in tri) - 0.4, min(q[1] for q in tri) - 0.4,
            max(q[0] for q in tri) + 0.4, max(q[1] for q in tri) + 0.4))
    if lab:
        LABELQ.append((cv, labpos[0], labpos[1], lab, 9.5))
    if tag:
        LABELQ.append((cv, tagpos[0], tagpos[1], tag, 8.5))

def flush_labels():
    # ノード描画後に呼ぶ: 矢頭の所有ノードを確定して登録し、エッジラベルを最前面に描画する
    while ARRQ:
        eid, tip, x0, y0, x1, y1 = ARRQ.pop(0)
        reg(PAGE, "arr", (eid, find_node_owner(PAGE, tip[0], tip[1])), x0, y0, x1, y1)
    while LABELQ:
        cv, x, y, s, size = LABELQ.pop(0)
        elabel(cv, x, y, s, size=size)

def form_header(cv, A4W, sec_title, audience, scope, page_label=None):
    cv.rect(20, 16, A4W - 40, 120, outline=(0, 0, 0), width_pt=1.2)
    cv.line([(20, 52), (A4W - 20, 52)], fill=(0, 0, 0), width_pt=0.8)
    cv.text(70, 34, "手 順 書", 18, anchor="mm")
    cv.rect(330, 22, 150, 26, outline=(0, 0, 0), width_pt=0.8)
    cv.text(340, 35, "管理番号", 10, anchor="lm")
    cv.rect(480, 22, 120, 26, outline=(0, 0, 0), width_pt=0.8)
    cv.text(490, 35, "頁", 10, anchor="lm")
    if page_label:
        cv.text(540, 35, page_label, 10, anchor="mm")
    cv.rect(330, 48, 150, 30, outline=(0, 0, 0), width_pt=0.8)
    cv.text(340, 63, "工程番号", 10, anchor="lm")
    cv.rect(480, 48, 120, 30, outline=(0, 0, 0), width_pt=0.8)
    cv.text(540, 63, "−", 10, anchor="mm")
    cv.rect(20, 82, 120, 54, outline=(0, 0, 0), width_pt=0.8)
    cv.text(80, 109, "作業内容", 10.5, anchor="mm")
    cv.rect(140, 82, A4W - 160, 54, outline=(0, 0, 0), width_pt=0.8)
    cv.text(150, 94, "構成と管理情報", 10.5, anchor="lm")
    cv.text(150, 112, audience, 9, fill=(64, 64, 64), anchor="lm")
    cv.text(30, A4H - 24, "NR4030", 9, fill=GRAY)
    cv.text(A4W / 2, A4H - 24, "様式 NR4030-0300-A3", 9, fill=GRAY, anchor="mm")
    cv.text(A4W - 60, A4H - 24, "日本光電", 9, fill=GRAY, anchor="rm")
    reg(PAGE, "ntext", "footer:l", *text_rect(cv, 30, A4H - 24, "NR4030", 9, anchor="la"))
    reg(PAGE, "ntext", "footer:c", *text_rect(cv, A4W / 2, A4H - 24, "様式 NR4030-0300-A3", 9, anchor="mm"))
    reg(PAGE, "ntext", "footer:r", *text_rect(cv, A4W - 60, A4H - 24, "日本光電", 9, anchor="rm"))

def legend(cv, A4W, y):
    t1 = "実線=確定した接続 / グレー破線=推定(未確認)の接続 / 矢頭=データの向きが確定(一方向で表記) / 枠の破線=推定機器(当Site未確認) / 灰色破線枠=別図参照"
    t3 = "略語: VM=仮想マシン / LWS=LNB操作画面(ブラウザ) / PDA=無線スキャナー端末 / FA=生産設備用パソコン / LNB=Line Network Box / NPM·AM=実装機の機種名"
    cv.text(40, y, "凡例: ", 9, anchor="lm")
    cv.text(66, y, t1, 9, fill=(64, 64, 64), anchor="lm")
    cv.text(40, y + 16, "分類: ", 9, anchor="lm")
    lx = 66
    for name, cls in [("サーバ系", "srv"), ("端末系", "term"), ("設備系", "eqp"), ("推定", "est"), ("外部·参照", "ext")]:
        fill, line, bw, dashed = STYLE[cls]
        cv.rect(lx, y + 10.5, 16, 10, fill=fill, outline=line, width_pt=0.9, radius=2)
        cv.text(lx + 20, y + 16, name, 9, anchor="lm")
        lx += 20 + cv.tlen(name, 9) + 14
    cv.text(40, y + 32, t3, 9, fill=(64, 64, 64), anchor="lm")
    r1 = text_rect(cv, 66, y, t1, 9, anchor="lm")
    reg(PAGE, "ntext", "legend:1", 35, r1[1], r1[2], r1[3])
    reg(PAGE, "ntext", "legend:2", 35, y + 10, lx, y + 22)
    reg(PAGE, "ntext", "legend:3", *text_rect(cv, 40, y + 32, t3, 9, anchor="lm"))

A4W, A4H = 842, 595
PAGE = "?"

def page_context():
    global PAGE, OX, OY
    PAGE = "ctx"
    cv = CV(A4W, A4H)
    form_header(cv, A4W, "a", "対象読者: 全員(技術詳細は図②·図③とリスト)", "この図に含めないもの: サーバー·装置の内部構成·IP·VM実名(図②③·リスト参照)", "2-3")
    cv.text(40, 146, "相関図① 全体の関わり(案)", 12, anchor="lm", font=jf(12 * S, True))
    reg(PAGE, "ntext", "title", *text_rect(cv, 40, 146, "相関図① 全体の関わり(案)", 12, bold=True, anchor="lm"))
    cv.text(250, 162, "本手順書の管理対象(図②③)と外部システム·作業者の関わりのみを示す。C4モデルのシステムコンテキスト図に相当。", 9, fill=(64, 64, 64), anchor="lm")
    cv.text(250, 176, "S1·S2=システム単位の呼び名(収録機器はリスト(1/2)冒頭の対応表)。E-a·E-b=別図参照の機器(N06·N18)。", 9, fill=(64, 64, 64), anchor="lm")
    reg(PAGE, "ntext", "subtitle:1", *text_rect(cv, 250, 162, "本手順書の管理対象(図②③)と外部システム·作業者の関わりのみを示す。C4モデルのシステムコンテキスト図に相当。", 9, anchor="lm"))
    reg(PAGE, "ntext", "subtitle:2", *text_rect(cv, 250, 176, "S1·S2=システム単位の呼び名(収録機器はリスト(1/2)冒頭の対応表)。E-a·E-b=別図参照の機器(N06·N18)。", 9, anchor="lm"))
    OX, OY = 40, 182
    # 描画順: エッジ → ノード → エッジラベル(基準②: ラベル隠れの防止)
    edge(cv, [(177, 50), (275, 50)], True, True, "保守·再起動を実施", (230, 40))
    edge(cv, [(177, 280), (275, 280)], True, True, "操作·照合を実施", (230, 270))
    edge(cv, [(395, 253), (395, 95)], True, True, "E04 参照·照合/稼働データ", (480, 170))
    edge(cv, [(623, 50), (495, 50)], True, True, "E02 実装データの収集·送信", (555, 40))
    edge(cv, [(487, 65), (600, 65), (600, 157), (615, 157)], True, True, "E18 外部I/F出力", (630, 108))
    edge(cv, [(487, 80), (585, 80), (585, 280), (615, 280)], True, True, "E08 稼働モニタ表示", (591, 200))
    edge(cv, [(767, 50), (786, 50), (786, 330), (395, 330), (395, 325)], True, False, "E03 ラインデータ", (600, 322))
    draw_node(cv, 20, 20, 160, 60, "person", None, None, "【人】管理者", "保守·再起動作業を実施")
    draw_node(cv, 20, 250, 160, 60, "person", None, None, "【人】作業者", "LNB操作·部品照合を実施")
    draw_node(cv, 280, 20, 210, 70, "sys", "S1", None, "【システム】PanaCIM環境", "実績管理·各種出力(内部は図②)")
    draw_node(cv, 280, 250, 210, 70, "sys", "S2", None, "【システム】ライン設備(LNB·NPM)", "実装作業·状態表示(内部は図③)")
    draw_node(cv, 620, 20, 150, 60, "ext", "E-a", None, "【上位システム】NPM-DGS", "IP 172.25.253.10(リストN06)", fs=10, dfs=8)
    draw_node(cv, 620, 130, 150, 55, "ext", "E-b", None, "【外部】外部I/F出力", "XML/DB/ソケット")
    draw_node(cv, 620, 250, 158, 60, "term", "N10", None, "【端末】稼働モニタ(Power BI)", "稼働を表示(図②参照)", fs=9.5, dfs=8)
    flush_labels()
    legend(cv, A4W, 523)
    out = os.path.join(OUTDIR, "c4_mock_1_context.png")
    cv.im.save(out)
    print("saved", out, cv.im.size)

def page_mgmt():
    global PAGE, OX, OY
    PAGE = "mgmt"
    cv = CV(A4W, A4H)
    form_header(cv, A4W, "b", "対象読者: 保守·管理者", "この図に含めないもの: 装置側の内部(図③)·VMの運用詳細(リスト)", "2-3")
    cv.text(40, 146, "相関図② PanaCIM管理側の内部(案)", 12, anchor="lm", font=jf(12 * S, True))
    cv.text(320, 163, "PanaCIM環境のサーバー·端末と、データの退避·出力先を示す。C4モデルのコンテナ図に相当。確定している技術情報のみ記載。", 9, fill=(64, 64, 64), anchor="lm")
    reg(PAGE, "ntext", "title", *text_rect(cv, 40, 146, "相関図② PanaCIM管理側の内部(案)", 12, bold=True, anchor="lm"))
    reg(PAGE, "ntext", "subtitle:1", *text_rect(cv, 320, 163, "PanaCIM環境のサーバー·端末と、データの退避·出力先を示す。C4モデルのコンテナ図に相当。確定している技術情報のみ記載。", 9, anchor="lm"))
    OX, OY = 40, 182
    # band a
    bx, by = OX, OY
    cv.rect(bx, by, 762, 330, outline=DASHGRAY, width_pt=1.0)
    cv.line([(bx, by), (bx + F(762), by + F(0)), (bx + F(762), by + F(330)), (bx, by + F(330)), (bx, by)], fill=DASHGRAY, width_pt=1.0, dash=(6, 3))
    reg_cbord(PAGE, "band_a", bx, by, bx + 762, by + 330)
    cv.rect(bx + 6, by + 5, cv.tlen("PanaCIM管理側ネットワーク — 上位網", 11, True) + 24, 18, fill=PAL["head_fill"])
    cv.text(bx + 12, by + 14, "PanaCIM管理側ネットワーク — 上位網", 11, fill="white", anchor="lm", font=jf(11 * S, True))
    reg(PAGE, "ntext", "band_a:title", *text_rect(cv, bx + 12, by + 14, "PanaCIM管理側ネットワーク — 上位網", 11, bold=True, anchor="lm"))
    # N01 container
    cv.rect(OX + 12, OY + 50, 300, 230, fill=(247, 242, 252), outline=PAL["srv_line"], width_pt=2.25, radius=6)
    cv.text(OX + 22, OY + 58, "【サーバ(物理)】ESXiホスト(N01)", 9, anchor="lm", fill=(96, 96, 96))
    reg(PAGE, "ntext", "N01:title", *text_rect(cv, OX + 22, OY + 58, "【サーバ(物理)】ESXiホスト(N01)", 9, anchor="lm"))
    reg(PAGE, "node", "N01", OX + 12, OY + 50, OX + 312, OY + 280)
    reg_cbord(PAGE, "N01", OX + 12, OY + 50, OX + 312, OY + 280)
    # 描画順: 帯·コンテナ → エッジ → ノード → エッジラベル(基準②)
    edge(cv, [(159, 119), (159, 143)], True, False, "E01 サーバー間連携", (172, 131))
    edge(cv, [(563, 256), (528, 256), (528, 92), (301, 92)], True, True, "E02 実装データ収集·送信", (400, 92))
    edge(cv, [(219, 308), (332, 308), (332, 104), (301, 104)], True, True, "E04 参照·照合/稼働データ", (285, 308))
    edge(cv, [(245, 77), (245, 18), (600, 18), (600, 45)], True, True, "E08 稼働モニタ表示", (620, 30))
    edge(cv, [(269, 77), (269, 42), (540, 42), (540, 206), (555, 206)], True, True, "E18 外部I/F", (490, 110))
    edge(cv, [(257, 49), (257, 30), (552, 30), (552, 140), (555, 140)], True, True, "E17 DB完全バックアップ", (360, 30))
    edge(cv, [(440, 199), (440, 181)], True, True, "E15 VMware管理画面", (440, 186))
    edge(cv, [(440, 283), (440, 249)], True, True, "E16 Route Editer", (440, 272))
    draw_node(cv, 26, 74, 270, 48, "srv", "N02", "n02_dataset", "【サーバ(VM)】PanaCIMアプリケーションサーバー", "実装データの受け口·各種出力の起点", fs=9.5, dfs=8)
    draw_node(cv, 26, 140, 270, 46, "srv", "N03", "n02_dataset", "【サーバ(VM)】PanaCIMコントローラーサーバー", "N02と同一VM(CIMC-SV)で運用", fs=9.5, dfs=8)
    draw_node(cv, 26, 196, 270, 44, "est", "N04", "n03_host", "【サーバ】メンテナンスサーバー", "当Site導入有無は未確認", fs=9.5, dfs=8)
    draw_node(cv, 350, 128, 165, 48, "srv", "N19", "n01_dns", "【サーバ(物理)】CIMA-SV", "別系統のPanaCIM(CIMC)環境", fs=10, dfs=8)
    draw_node(cv, 350, 196, 165, 48, "term", "N15", "n09_computer", "【端末】CIM-A PC", "VMware管理画面入口·再起動対象", fs=10, dfs=8)
    draw_node(cv, 350, 280, 165, 44, "term", "N16", "n09_computer", "【端末】CIM-C PC", "異常時再起動の最初に停止", fs=10, dfs=8)
    draw_node(cv, 560, 50, 180, 48, "term", "N10", "n07_monitoring", "【端末】稼働モニタ(Power BI)", "稼働を表示", fs=10, dfs=8)
    draw_node(cv, 560, 116, 180, 48, "cont", "N17", "n06_database", "【保存領域】DB完全バックアップ", "退避先 E:\\BackUP_DB", fs=10, dfs=8)
    draw_node(cv, 560, 182, 180, 48, "ext", "N18", "n05_output", "【外部】外部I/F出力", "XML/DB/ソケット", fs=10, dfs=8)
    draw_node(cv, 560, 248, 180, 44, "xref", None, None, "NPM-DGS(上位システム)", "図①·リストN06参照", fs=10, dfs=8)
    draw_node(cv, 12, 292, 210, 32, "xref", None, None, "ライン設備(LNB·NPM)", "図③参照", fs=10, dfs=8)
    flush_labels()
    legend(cv, A4W, 523)
    out = os.path.join(OUTDIR, "c4_mock_2_mgmt.png")
    cv.im.save(out)
    print("saved", out, cv.im.size)

def page_line():
    global PAGE, OX, OY
    PAGE = "line"
    cv = CV(A4W, A4H)
    form_header(cv, A4W, "c", "対象読者: 作業者·保守", "この図に含めないもの: サーバー側の内部(図②)·無線の詳細(リスト)", "2-3")
    cv.text(40, 146, "相関図③ ライン設備側の内部(案)", 12, anchor="lm", font=jf(12 * S, True))
    cv.text(300, 163, "ライン設備の装置·端末と、LNBを中心としたデータの流れを示す。C4モデルのコンテナ図に相当。推定の接続は破線。", 9, fill=(64, 64, 64), anchor="lm")
    reg(PAGE, "ntext", "title", *text_rect(cv, 40, 146, "相関図③ ライン設備側の内部(案)", 12, bold=True, anchor="lm"))
    reg(PAGE, "ntext", "subtitle:1", *text_rect(cv, 300, 163, "ライン設備の装置·端末と、LNBを中心としたデータの流れを示す。C4モデルのコンテナ図に相当。推定の接続は破線。", 9, anchor="lm"))
    OX, OY = 40, 182
    # band b
    bx, by = OX, OY
    cv.rect(bx, by + 72, 762, 258, outline=DASHGRAY, width_pt=1.0)
    cv.line([(bx, by + F(72)), (bx + F(762), by + F(72)), (bx + F(762), by + F(330)), (bx, by + F(330)), (bx, by + F(72))], fill=DASHGRAY, width_pt=1.0, dash=(6, 3))
    reg_cbord(PAGE, "band_b", bx, by + 72, bx + 762, by + 330)
    btitle = "ライン設備側ネットワーク — 内部網"
    btw = cv.tlen(btitle, 11, True) + 24
    cv.rect(bx + 762 - 12 - btw, by + 77, btw, 18, fill=PAL["head_fill"])
    cv.text(bx + 762 - 12, by + 86, btitle, 11, fill="white", anchor="rm", font=jf(11 * S, True))
    reg(PAGE, "ntext", "band_b:title", *text_rect(cv, bx + 762 - 12, by + 86, btitle, 11, bold=True, anchor="rm"))
    # 描画順: 帯 → エッジ → ノード → エッジラベル(基準②)
    edge(cv, [(100, 55), (100, 39)], True, True, "E04 参照·照合/稼働データ", (210, 43))
    edge(cv, [(660, 31), (660, 44), (776, 44), (776, 134), (324, 134), (324, 164), (305, 164)], True, False, "E03 ラインデータ", (650, 130))
    edge(cv, [(15, 17), (8, 17), (8, 254), (55, 254)], False, True, "E09 表示内容の由来?", (86, 209))
    edge(cv, [(257, 88), (312, 88), (312, 254), (237, 254)], False, False, "E10 接続形態未確認", (290, 254))
    edge(cv, [(120, 97), (120, 143)], True, False, "E05 装置網接続", (120, 130))
    edge(cv, [(200, 143), (200, 105)], True, True, "E06 ノズル/リーダー", (200, 112))
    edge(cv, [(380, 89), (380, 76), (265, 76)], True, False, "E14 LNB操作画面", (330, 63))
    edge(cv, [(517, 252), (563, 252)], False, False, None, None, "E12", (540, 244))
    edge(cv, [(635, 233), (635, 193)], False, False, None, None, "E13", (641, 207))
    draw_node(cv, 12, 0, 220, 34, "xref", None, None, "PanaCIM環境", "図②参照", fs=10, dfs=8)
    draw_node(cv, 560, 0, 200, 34, "xref", None, None, "NPM-DGS(上位システム)", "図①②参照", fs=10, dfs=8)
    draw_node(cv, 60, 52, 200, 48, "eqp", "N07", "n09_computer", "【設備】LNB(FAパソコン)", "ライン制御·帯境界跨り(太枠)", fs=10, dfs=8)
    draw_node(cv, 60, 140, 240, 48, "eqp", "N08", "n13_precision_manufacturing", "【設備】NPM X/NPM/AMライン(実装機)", "L1=NPM-1〜7·SP70-1", fs=10, dfs=8)
    draw_node(cv, 350, 86, 150, 44, "term", "N11", "n09_computer", "【端末】LWS", "LNB操作画面(ブラウザ)", fs=10, dfs=8)
    draw_node(cv, 60, 230, 180, 48, "eqp", "N09", "n08_connected_tv", "【設備】アンドン(状態表示)", "接続は推定", fs=10, dfs=8)
    draw_node(cv, 340, 230, 180, 44, "term", "N12", "n11_barcode_scanner", "【端末】無線スキャナー(PDA)", "部品照合·ライン毎に前側/後側", fs=10, dfs=8)
    draw_node(cv, 560, 146, 150, 44, "est", "N14", "n12_tablet", "【端末】Androidタブレット", "当Site導入状況は未確認", fs=9.5, dfs=8)
    draw_node(cv, 560, 230, 150, 44, "est", "N13", "n10_wifi", "【設備】アクセスポイント", "当Site設置状況は未確認", fs=9.5, dfs=8)
    flush_labels()
    legend(cv, A4W, 523)
    out = os.path.join(OUTDIR, "c4_mock_3_line.png")
    cv.im.save(out)
    print("saved", out, cv.im.size)

FAIL_PAIRS = {frozenset(p) for p in [
    ("label", "label"), ("label", "node"), ("label", "ntext"), ("label", "chip"), ("label", "icon"),
    ("label", "cbord"), ("label", "seg"), ("label", "arr"),
    ("ntext", "ntext"), ("ntext", "chip"), ("ntext", "icon"), ("ntext", "seg"), ("ntext", "arr"), ("ntext", "cbord"),
    ("chip", "chip"), ("chip", "icon"), ("chip", "seg"), ("chip", "arr"), ("chip", "cbord"),
    ("node", "cbord"),
    ("icon", "icon"), ("icon", "seg"), ("icon", "arr"), ("icon", "cbord"),
    ("arr", "arr"), ("arr", "seg"), ("arr", "cbord"),
    ("cbord", "cbord"),
]}

def _rects_overlap(r1, r2, m=0.5):
    return r1[0] < r2[2] - m and r1[2] > r2[0] + m and r1[1] < r2[3] - m and r1[3] > r2[1] + m

def _inside(a, b, tol=1.0):
    return a[0] >= b[0] - tol and a[1] >= b[1] - tol and a[2] <= b[2] + tol and a[3] <= b[3] + tol

def _cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

def _proper_cross(p1, p2, p3, p4):
    return (_cross(p1, p2, p3) * _cross(p1, p2, p4) < 0 and
            _cross(p3, p4, p1) * _cross(p3, p4, p2) < 0)

def run_checks():
    print("---- overlap check: border/arrow/text/icon ----")
    bad = info = 0
    items = CHECKS
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            p1, k1, o1, r1 = items[i][0], items[i][1], items[i][2], items[i][3:]
            p2, k2, o2, r2 = items[j][0], items[j][1], items[j][2], items[j][3:]
            if p1 != p2:
                continue
            key = frozenset((k1, k2))
            e1, e2 = eid_of(o1), eid_of(o2)
            ov = _rects_overlap(r1, r2)
            if not ov:
                continue
            if key == {"seg", "seg"}:
                s1, s2 = o1[1:], o2[1:]
                if _proper_cross(s1[:2], s1[2:], s2[:2], s2[2:]):
                    print(f"CROSSING [{p1}] {e1} x {e2} (線と線の交差·許容)")
                    info += 1
                continue
            if key == {"node", "node"}:
                if not (_inside(r1, r2, 0.5) or _inside(r2, r1, 0.5)):
                    print(f"OVERLAP [{p1}] node:{o1} x node:{o2}")
                    bad += 1
                continue
            if key == {"ntext", "node"} or key == {"label", "node"}:
                # ノード内に収まっている文字はOK(内部ラベル·自身の名前等)、枠に掛かるのはNG
                if k1 in ("ntext", "label"):
                    inner, outer, oname = r1, r2, o1
                else:
                    inner, outer, oname = r2, r1, o2
                if not _inside(inner, outer, 1.0):
                    print(f"OVERLAP [{p1}] {k1}:{oname} x node:{o2 if k1 in ('ntext','label') else o1} (枠に掛かる文字)")
                    bad += 1
                continue
            if key == {"chip", "node"}:
                cpr = r1 if k1 == "chip" else r2
                ndr = r2 if k1 == "chip" else r1
                if _inside(cpr, ndr, 1.0) or e1 == e2:  # コンテナ内収納 or 自ノード枠跨り(意図仕様)
                    continue
                print(f"OVERLAP [{p1}] chip:{o1 if k1=='chip' else o2} x node:{o2 if k1=='chip' else o1}")
                bad += 1
                continue
            if key == {"node", "icon"}:
                icr = r1 if k1 == "icon" else r2
                ndr = r2 if k1 == "icon" else r1
                if not _inside(icr, ndr, 1.0):  # コンテナ内収納はOK、枠に掛かるのはNG
                    print(f"OVERLAP [{p1}] icon:{o1 if k1=='icon' else o2} x node:{o2 if k1=='icon' else o1}")
                    bad += 1
                continue
            if e1 == e2 or frozenset((e1, e2)) in EXEMPT_EIDS:
                continue
            if key == {"node", "seg"}:
                seg = o1 if k1 == "seg" else o2
                node = r2 if k1 == "seg" else r1
                xa, ya, xb, yb = seg[1], seg[2], seg[3], seg[4]
                near = lambda px, py: node[0] - 1.5 <= px <= node[2] + 1.5 and node[1] - 1.5 <= py <= node[3] + 1.5
                if near(xa, ya) or near(xb, yb):
                    continue
                print(f"OVERLAP [{p1}] node:{o2 if k1=='seg' else o1} x {fmt_owner('seg', seg)} (節点を貫通する線)")
                bad += 1
                continue
            if key == {"node", "arr"}:
                arr = o1 if k1 == "arr" else o2
                arrr = r1 if k1 == "arr" else r2
                nod = o2 if k1 == "arr" else o1
                nodr = r2 if k1 == "arr" else r1
                if arr[1] == nod or (arr[1] is not None and _inside(arrr, nodr, 1.0)):
                    continue
                print(f"OVERLAP [{p1}] node:{nod} x arr:{arr[0]} (対象外ノードへの矢頭)")
                bad += 1
                continue
            if key in FAIL_PAIRS:
                print(f"OVERLAP [{p1}] {fmt_owner(k1, o1)} x {fmt_owner(k2, o2)}")
                bad += 1
    print(f"check done: {bad} overlaps, {info} crossing(s·許容)")

NODE_ROWS = [
    ("N01", "【サーバ(物理)】ESXiホスト", "IP 172.25.253.45。N02〜N04を収める容器(枠2.25pt)。", "—"),
    ("N02", "【サーバ(VM)】PanaCIMアプリケーションサーバー", "当SiteはESXi上VM「CIMC-SV」として運用(PanaCIM(CIMA)環境·X02-⑪)。", "環境と製品構成の対応(X02-⑪)"),
    ("N03", "【サーバ(VM)】PanaCIMコントローラーサーバー", "N02と同じ(当Siteは「CIMC-SV」として運用·X02-⑪)。", "同上"),
    ("N04", "【サーバ】メンテナンスサーバー", "当Site導入有無は未確認。", "当Site導入有無(X02-⑤)"),
    ("N06", "【上位システム】NPM-DGS", "IP 172.25.253.10。複数台接続可(-8-)。物理位置は要確認(現行踏襲)。管理境界はLNB管理書§14 No.8の前提タスク。DGS-SV(\\\\DGS-SV\\share_dgs_data)との同一性はX02-⑫。nksv569停止時に接続不能の記録あり(詳細要確認)。", "物理位置·管理境界(X02-⑩/⑫)·DGS-SV同一性"),
    ("N07", "【設備】LNB(FAパソコン)", "LNB冊は「L1〜L3」を追記(§8)。iLNBと同一とは断定しない(要確認#1)。帯境界跨り(太枠2.25pt)。", "iLNB同一性(要確認#1·X02-⑧)"),
    ("N08", "【設備】NPM X/NPM/AMライン(実装機)", "L1=NPM-1〜7·SP70-1(2026-10-14 LNB構成情報画面)。", "—"),
    ("N09", "【設備】アンドン(状態表示)", "ノードは確定。接続エッジは推定(T3)。", "—"),
    ("N10", "【端末】稼働モニタ(Power BI)", "稼働モニタークライアント設置条件は注記X01(-8-)。", "—"),
    ("N11", "【端末】LWS", "LNB操作画面(ブラウザ)。T1の「LWSエディター」(-9-/-10-)との同一性は要確認。", "LWSエディター同一性(X02-⑦)"),
    ("N12", "【端末】無線スキャナー(PDA)", "ライン毎に前側用/後側用(-9-)。部品照合はLNB設定前提(A-2)。", "—"),
    ("N13", "【設備】アクセスポイント", "当Site設置状況は未確認。無線AP。", "当Site設置状況(X02-⑤)"),
    ("N14", "【端末】Androidタブレット", "当Site導入状況は未確認。", "当Site導入状況(X02-⑤)"),
    ("N15", "【端末】CIM-A PC", "VMware管理画面入口。異常時再起動対象。", "—"),
    ("N16", "【端末】CIM-C PC", "異常時再起動の最初に停止。Route Editer起動が最後(7-4 手順14)。", "—"),
    ("N17", "【保存領域】DB完全バックアップ", "保存先 E:\\BackUP_DB\\PANACIM_****_FULbak。外部メディア保存は-28-。", "—"),
    ("N18", "【外部】外部I/F出力", "XML/DB/ソケット。対応表は本文で引用予定(要確認)。", "対応表の引用(要確認)"),
    ("N19", "【サーバ(物理)】CIMA-SV", "172.25.253.42·ラック左7番目·PanaCIM(CIMC)環境·X02-⑪。存在·所在は2026-10-27照査で確定。", "管理範囲·CIMC-SVとの関係(X02-⑩)"),
]
N05_PARAS = [
    "当Site運用: PanaCIM(CIMA)環境は ESXi(172.25.253.45)上のVM「CIMC-SV」(RedHat·RHEL 6 64bit)として稼働。別系統の PanaCIM(CIMC)環境サーバー「CIMA-SV」(172.25.253.42·物理)の存在を確認(2026-10-27照査·X02-⑪)。",
    "再起動の対象 — 月次: CIMC-SV / 異常時: CIM-C PC·CIM-A PC·ESXi·CIMC-SV(0494-912039(06)·管理書第3章)。",
    "再起動順序の詳細(LNBとの全体順)は未確定 → 注記X02-③。",
]
EDGE_ROWS = [
    ("E01", "サーバー間連携(N02—N03)", "確定"),
    ("E02", "実装データの収集·送信(NPM-DGS→N02)", "確定"),
    ("E03", "ラインデータ(NPM-DGS→N08)", "確定(向きは現行図に矢頭なし)"),
    ("E04", "参照·照合/稼働データ(N07→N02)", "確定"),
    ("E05", "装置網接続(N07—N08)", "確定"),
    ("E06", "ノズル/リーダー(N08→N07)", "確定"),
    ("E07", "ジョブ退避(保存領域N17関係)", "確定(現行図)·接続先の組合せは要確認のため図には未描画"),
    ("E08", "稼働モニタ表示(N02→N10)", "確定"),
    ("E09", "表示内容の由来?(→N09)", "推定(T3)·起点は会議で変更済み(P-1)"),
    ("E10", "接続形態未確認(N07—N09)", "推定"),
    ("E11", "(未描画)", "会議確認事項X02-①の持ち越し"),
    ("E12", "無線(AP経由)(N12—N13)", "推定"),
    ("E13", "無線(N13—N14)", "推定"),
    ("E14", "LNB操作画面(N11—N07)", "確定"),
    ("E15", "CIM-A PC→CIMA-SV", "確定"),
    ("E16", "CIM-C PC→CIMA-SV", "確定"),
    ("E17", "DB完全バックアップ(N01→N17)", "確定"),
    ("E18", "外部I/F(N02→N18)", "確定"),
]

def wrap(cv, s, size_pt, width_pt):
    lines, cur = [], ""
    for ch in s:
        if cv.tlen(cur + ch, size_pt) > width_pt:
            lines.append(cur)
            cur = ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines

def page_list1():
    cv = CV(595, 842)
    PH = 842  # 縦置きA4の高さ(グローバルA4H=595は横置き図面用のため使わない)
    cv.text(28, 30, "相関図リスト(1/2)— 機器(案)", 12, anchor="lm", font=jf(12 * S, True))
    cv.text(28, 48, "図①〜③の N番号·E番号と対応する。凡例と略語は各図頁を参照。", 8.5, fill=(64, 64, 64), anchor="lm")
    cv.text(28, 58, "図①の記号とN番号の対応: S1=N01〜N04·N15〜N17·N19 / S2=N07〜N09·N11〜N14", 8.5, fill=(64, 64, 64), anchor="lm")
    cv.text(28, 70, "E-a=N06 / E-b=N18 / 稼働モニタはN10(図①にも単独表示)", 8.5, fill=(64, 64, 64), anchor="lm")
    cols = [(28, 30), (60, 150), (212, 268), (482, 85)]
    heads = ["番号", "名称(図の表記)", "詳細(位置づけ·運用·出典)", "要確認"]
    y = 88
    for (cx, cw), hname in zip(cols, heads):
        cv.rect(cx, y, cw, 14, fill=(242, 242, 242), outline=(150, 150, 150), width_pt=0.6)
        cv.text(cx + 4, y + 7, hname, 9, anchor="lm")
    y += 14
    fs, lh = 9.0, 11.4
    for num, name, det, conf in NODE_ROWS:
        dl = wrap(cv, det, fs, cols[2][1] - 8)
        nl = wrap(cv, name, fs, cols[1][1] - 8)
        cl = wrap(cv, conf, fs, cols[3][1] - 8)
        rows = max(len(dl), len(nl), len(cl), 1)
        rh = rows * lh + 4
        if y + rh > PH - 60:
            print("LIST1 OVERFLOW at", num, "y=", y)
            break
        for (cx, cw), lines in zip(cols[1:], [nl, dl, cl]):
            ty = y + 2 + lh / 2
            for ln in lines:
                cv.text(cx + 4, ty, ln, fs, anchor="lm")
                ty += lh
        cv.text(cols[0][0] + 4, y + 2 + (rh - 4) / 2, num, fs, anchor="lm")
        cv.line([(28, y + rh), (595 - 28, y + rh)], fill=(200, 200, 200), width_pt=0.5)
        y += rh
    y += 8
    cv.text(28, y, "運用注記(旧N05注記ボックスから移動·本文§2.1)", 9.5, anchor="lm")
    y += 14
    for i, p in enumerate(N05_PARAS, 1):
        for ln in wrap(cv, f"({i}) {p}", fs, 595 - 56):
            cv.text(28, y + 5, ln, fs, anchor="lm")
            y += lh
        y += 2
    cv.text(28, PH - 40, "接続(E番号)·帯·出典符の定義は(2/2)。", 8.5, fill=(64, 64, 64), anchor="lm")
    cv.text(28, PH - 24, "NR4030", 9, fill=GRAY)
    out = os.path.join(OUTDIR, "c4_mock_list1.png")
    cv.im.save(out)
    print("saved", out, cv.im.size, "bottom y(pt)=", round(y, 1))

def page_list2():
    cv = CV(595, 842)
    PH = 842
    cv.text(28, 30, "相関図リスト(2/2)— 接続と出典(案)", 12, anchor="lm", font=jf(12 * S, True))
    cv.text(28, 48, "E番号は図①〜③の線ラベルと対応する。確定度の意味は各図頁の凡例、帯(ネットワークセグメント)と出典符の定義は後半を参照。", 8.5, fill=(64, 64, 64), anchor="lm")
    cols = [(28, 30), (60, 230), (292, 275)]
    heads = ["番号", "接続(図のラベル)", "確定度·備考"]
    y = 62
    for (cx, cw), hname in zip(cols, heads):
        cv.rect(cx, y, cw, 14, fill=(242, 242, 242), outline=(150, 150, 150), width_pt=0.6)
        cv.text(cx + 4, y + 7, hname, 9, anchor="lm")
    y += 14
    fs, lh = 9.0, 11.4
    for num, conn, conf in EDGE_ROWS:
        cl = wrap(cv, conf, fs, cols[2][1] - 8)
        nl = wrap(cv, conn, fs, cols[1][1] - 8)
        rows = max(len(cl), len(nl), 1)
        rh = rows * lh + 4
        if y + rh > PH - 170:
            print("LIST2 OVERFLOW at", num, "y=", y)
            break
        for (cx, cw), lines in zip(cols[1:], [nl, cl]):
            ty = y + 2 + lh / 2
            for ln in lines:
                cv.text(cx + 4, ty, ln, fs, anchor="lm")
                ty += lh
        cv.text(cols[0][0] + 4, y + 2 + (rh - 4) / 2, num, fs, anchor="lm")
        cv.line([(28, y + rh), (595 - 28, y + rh)], fill=(200, 200, 200), width_pt=0.5)
        y += rh
    y += 10
    cv.text(28, y, "帯(ネットワークセグメント)", 9.5, anchor="lm")
    y += 14
    for s in [
        "帯a: PanaCIM管理側ネットワーク — 上位網 192.168.30.xx / 当Site実測: 制限セグメント 172.25.253.0/24〔T1:-9-/-10-·T1b: ネットワークイメージ.pptx·2026-10-27〕",
        "帯b: ライン設備側ネットワーク — 内部網 192.168.10.xx/20.xx(DHCP)·LNB設備側 192.168.20.25〔T1:-9-/-10-〕",
    ]:
        for ln in wrap(cv, s, fs, 595 - 56):
            cv.text(28, y + 5, ln, fs, anchor="lm")
            y += lh
        y += 2
    y += 6
    cv.text(28, y, "出典符の定義", 9.5, anchor="lm")
    y += 14
    for s in [
        "頁参照(-8-等): 管理書本文の頁·節番号。LNB管理書は「§」表記。冊名の明記は実装時に統一する(評5指摘)。",
        "T1b: ネットワークイメージ.pptx(2026-10-27) / T3: 現行相関図(Stage5)の記載。",
        "X02-○○: 確認事項台帳の項目番号。台帳の本文収録と対応表の位置は実装時に規定する。",
        "N05: 番号を欠番とし、内容は(1/2)の運用注記に移動した。",
        "iLNB: メーカー公開資料上の統合ライン管理システム。LNB(=Line Network Box)との同一性は未確認(X02-⑧)。",
        "A-2·P-1·T1: リストの備考で使う出典ラベル。対応する出典元の一覧は実装時に対応表へ統合する(要確認)。",
    ]:
        for ln in wrap(cv, s, fs, 595 - 56):
            cv.text(28, y + 5, ln, fs, anchor="lm")
            y += lh
        y += 2
    cv.text(28, PH - 24, "NR4030", 9, fill=GRAY)
    out = os.path.join(OUTDIR, "c4_mock_list2.png")
    cv.im.save(out)
    print("saved", out, cv.im.size, "bottom y(pt)=", round(y, 1))

if __name__ == "__main__":
    page_context()
    page_mgmt()
    page_line()
    run_checks()
    page_list1()
    page_list2()
