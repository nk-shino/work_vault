# -*- coding: utf-8 -*-
"""Redesign mock: minimal nodes + list separation (A4 landscape page + list page + compare)."""
import os
from PIL import Image, ImageDraw, ImageFont

DL = os.path.dirname(os.path.abspath(__file__))
ICONS = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図\icons"
OUTDIR = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
RENDER = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\corr_lnb_work\corr_lnb_stage5_p1.png"
JP = "C:/Windows/Fonts/meiryo.ttc"
S = 3.0  # px per pt

INK = (31, 31, 31)
GRAY = (89, 89, 89)
LINE = (0, 0, 0)
DASHGRAY = (128, 128, 128)

# ---- palette sampling from current render ----
def sample_palette():
    pal = {
        "srv_fill": (232, 225, 242), "srv_line": (128, 100, 162),
        "term_fill": (240, 245, 222), "term_line": (155, 187, 89),
        "eqp_fill": (245, 230, 216), "eqp_line": (160, 82, 70),
        "head_fill": (59, 59, 59),
    }
    try:
        im = Image.open(RENDER).convert("RGB")
        W, H = im.size
        def px(ptx, pty):
            return im.getpixel((min(W - 1, int(ptx / 842 * W)), min(H - 1, int(pty / 595 * H))))
        pal["srv_fill"] = px(116, 257)
        pal["term_fill"] = px(80, 397)
        pal["eqp_fill"] = px(125, 533)
        pal["head_fill"] = px(250, 195)
        print("sampled:", {k: v for k, v in pal.items()})
    except Exception as e:
        print("sample skipped:", e)
    return pal

PAL = sample_palette()
STYLE = {
    "srv":  (PAL["srv_fill"], PAL["srv_line"], 1.0, False),
    "term": (PAL["term_fill"], PAL["term_line"], 1.0, False),
    "eqp":  (PAL["eqp_fill"], PAL["eqp_line"], 2.25, False),
    "cont": (PAL["srv_fill"], PAL["srv_line"], 2.25, False),
    "est":  ((242, 242, 242), (128, 128, 128), 1.0, True),
    "ext":  ((255, 255, 255), (127, 127, 127), 1.0, False),
}

def jf(px_size, bold=False):
    if bold:
        return ImageFont.truetype("C:/Windows/Fonts/meiryoB.ttc", int(px_size), index=0)
    return ImageFont.truetype(JP, int(px_size), index=0)

def F(pt):
    return pt * S

class CV:
    """canvas wrapper with pt-based drawing"""
    def __init__(self, w_pt, h_pt):
        self.w_pt, self.h_pt = w_pt, h_pt
        self.im = Image.new("RGB", (int(w_pt * S), int(h_pt * S)), "white")
        self.d = ImageDraw.Draw(self.im)

    def poly(self, pts, fill=None, outline=None, width_pt=1.0):
        self.d.polygon([(F(x), F(y)) for x, y in pts], fill=fill, outline=outline, width=max(1, round(width_pt * S)))

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
            for q in p:  # round joints
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

    def tlen(self, s, size_pt):
        return self.d.textlength(s, font=jf(size_pt * S)) / S

ICON_CACHE = {}
def icon(key, size_pt):
    px = int(size_pt * S)
    if key not in ICON_CACHE or ICON_CACHE[key][0] != px:
        im = Image.open(os.path.join(ICONS, f"{key}.png")).convert("RGBA")
        im = im.resize((px, px), Image.LANCZOS)
        ICON_CACHE[key] = (px, im)
    return ICON_CACHE[key][1]

# ---------------- page A: diagram ----------------
OX, OY = 0.0, 0.0  # diagram origin (set by page_diagram)

def draw_node(cv, x, y, w, h, cls, num, icon_key, lines, fs=10.5, label_fs=None):
    x, y = x + OX, y + OY
    fill, line, bw, dashed = STYLE[cls]
    if dashed:
        cv.rect(x, y, w, h, fill=fill, outline=None)
        cv.line([(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)],
                fill=line, width_pt=bw, dash=(F(4) / S * 2.4, F(2.4) / S * 2.4))
    else:
        cv.rect(x, y, w, h, fill=fill, outline=line, width_pt=bw, radius=6)
    # icon
    if icon_key:
        isz = 13
        cv.im.paste(icon(icon_key, isz), (int(F(x + 6)), int(F(y + h / 2 - isz / 2))), icon(icon_key, isz))
        tx = x + 6 + isz + 5
    else:
        tx = x + 8
    # text lines
    lfs = label_fs or fs
    lh = lfs + 3.2
    total = len(lines) * lh
    ty = y + h / 2 - total / 2 + lh / 2
    for ln in lines:
        cv.text(tx, ty, ln, lfs, anchor="lm")
        ty += lh
    # number chip
    if num:
        cw = cv.tlen(num, 8) + 8
        ch = 12
        cv.rect(x - 1, y - ch / 2, cw, ch, fill="white", outline=GRAY, width_pt=0.75, radius=3)
        cv.text(x - 1 + cw / 2, y, num, 8, fill=(64, 64, 64), anchor="mm")

def edge_label(cv, x, y, s, size=9.0):
    cv.text(x, y, s, size, fill=(64, 64, 64), anchor="lm", halo=True)

def page_diagram():
    A4W, A4H = 842, 595
    cv = CV(A4W, A4H)
    d = cv.d
    # form frame (NR4030 simplified)
    cv.rect(20, 16, A4W - 40, 120, outline=(0, 0, 0), width_pt=1.2)
    cv.line([(20, 52), (A4W - 20, 52)], fill=(0, 0, 0), width_pt=0.8)
    cv.text(70, 34, "手 順 書", 18, anchor="mm")
    cv.rect(330, 22, 150, 26, outline=(0, 0, 0), width_pt=0.8)
    cv.text(340, 35, "管理番号", 10, anchor="lm")
    cv.rect(480, 22, 120, 26, outline=(0, 0, 0), width_pt=0.8)
    cv.text(490, 35, "頁", 10, anchor="lm")
    cv.rect(330, 48, 150, 30, outline=(0, 0, 0), width_pt=0.8)
    cv.text(340, 63, "工程番号", 10, anchor="lm")
    cv.rect(480, 48, 120, 30, outline=(0, 0, 0), width_pt=0.8)
    cv.text(540, 63, "−", 10, anchor="mm")
    cv.rect(20, 82, 120, 54, outline=(0, 0, 0), width_pt=0.8)
    cv.text(80, 109, "作業内容", 10.5, anchor="mm")
    cv.rect(140, 82, A4W - 160, 54, outline=(0, 0, 0), width_pt=0.8)
    cv.text(150, 109, "構成と管理情報", 10.5, anchor="lm")
    cv.text(30, A4H - 24, "NR4030", 9, fill=GRAY)
    cv.text(A4W / 2, A4H - 24, "様式 NR4030-0300-A3", 9, fill=GRAY, anchor="mm")
    cv.text(A4W - 60, A4H - 24, "日本光電", 9, fill=GRAY, anchor="rm")

    ox, oy = 40, 168  # diagram origin (pt)
    global OX, OY
    OX, OY = ox, oy
    def P(x, y):  # translate diagram pt -> page pt
        return ox + x, oy + y

    # pretext
    cv.text(40, 150, "2-3. 相関図(再設計案モック)", 11, anchor="lm")
    cv.text(240, 150, "確定した接続と推定(未確認)の接続を線種で区別して記載する。機器の詳細·接続の条件·出典は次頁「相関図リスト」の番号を参照すること。", 9, fill=(64, 64, 64), anchor="lm")

    # bands
    bx, by = P(0, 0)
    cv.rect(bx, by, 740, 210, outline=DASHGRAY, width_pt=1.0)
    cv.d.rectangle([bx + F(0.8), by + F(0.8), bx + F(739.2), by + F(209.2)], outline=DASHGRAY)
    # draw dashed band borders
    for pts in [[(0, 0), (740, 0), (740, 210), (0, 210), (0, 0)]]:
        pp = [P(*q) for q in pts]
        cv.line(pp, fill=DASHGRAY, width_pt=1.0, dash=(6, 3))
    cv.rect(bx + 6, by + 5, cv.d.textlength("PanaCIM管理側ネットワーク — 上位網", font=jf(11 * S, bold=True)) / S + 24, 18, fill=PAL["head_fill"])
    cv.text(bx + 12, by + 14, "PanaCIM管理側ネットワーク — 上位網", 11, fill="white", anchor="lm", font=jf(11 * S, bold=True))
    # band_b
    for pts in [[(0, 230), (740, 230), (740, 330), (0, 330), (0, 230)]]:
        cv.line([P(*q) for q in pts], fill=DASHGRAY, width_pt=1.0, dash=(6, 3))
    cv.rect(bx + 6, by + 307, cv.d.textlength("ライン設備側ネットワーク — 内部網", font=jf(11 * S, bold=True)) / S + 24, 18, fill=PAL["head_fill"])
    cv.text(bx + 12, by + 316, "ライン設備側ネットワーク — 内部網", 11, fill="white", anchor="lm", font=jf(11 * S, bold=True))

    # nodes (diagram pt coords)
    draw_node(cv, 10, 28, 326, 140, "cont", "N01", "n01_dns", ["【サーバ(物理)】ESXiホスト"])
    draw_node(cv, 22, 62, 292, 26, "srv", "N02", "n02_dataset", ["【サーバ(VM)】PanaCIMアプリケーションサーバー"], fs=10)
    draw_node(cv, 22, 94, 292, 26, "srv", "N03", "n02_dataset", ["【サーバ(VM)】PanaCIMコントローラーサーバー"], fs=10)
    draw_node(cv, 22, 126, 292, 26, "est", "N04", "n03_host", ["【サーバ】メンテナンスサーバー"], fs=9.5)
    draw_node(cv, 356, 30, 204, 42, "srv", "N06", "n04_device_hub", ["【上位システム】", "NPM-DGS"])
    draw_node(cv, 356, 80, 204, 34, "srv", "N19", "n01_dns", ["【サーバ(物理)】CIMA-SV"], fs=10)
    draw_node(cv, 356, 122, 204, 34, "term", "N15", "n09_computer", ["【端末】CIM-A PC"], fs=10)
    draw_node(cv, 356, 164, 204, 34, "term", "N16", "n09_computer", ["【端末】CIM-C PC"], fs=10)
    draw_node(cv, 566, 30, 166, 42, "eqp", "N17", "n06_database", ["【保存領域】", "DB完全バックアップ"], fs=10)
    draw_node(cv, 566, 80, 166, 42, "ext", "N18", "n05_output", ["【外部】", "外部I/F出力"], fs=10)
    draw_node(cv, 566, 130, 166, 42, "term", "N10", "n07_monitoring", ["【端末】稼働モニタ", "(Power BI)"], fs=10)
    draw_node(cv, 10, 200, 190, 40, "eqp", "N07", "n09_computer", ["【設備】LNB(FAパソコン)"], fs=10)
    draw_node(cv, 10, 256, 240, 40, "eqp", "N08", "n13_precision_manufacturing", ["【設備】NPM X/NPM/AMライン"], fs=10)
    draw_node(cv, 272, 256, 150, 40, "term", "N11", "n09_computer", ["【端末】LWS"], fs=10)
    draw_node(cv, 432, 256, 120, 40, "eqp", "N09", "n08_connected_tv", ["【設備】アンドン", "(状態表示)"], fs=9.5)
    draw_node(cv, 252, 302, 180, 24, "term", "N12", "n11_barcode_scanner", ["【端末】無線スキャナー(PDA)"], fs=8.5)
    draw_node(cv, 596, 230, 136, 40, "est", "N13", "n10_wifi", ["【設備】", "アクセスポイント"], fs=9.5)
    draw_node(cv, 596, 282, 136, 40, "est", "N14", "n12_tablet", ["【端末】Android", "タブレット"], fs=9.5)

    # edges: (pts, solid?, arrow_at_end, label, label_pos)
    def E(pts, solid=True, arrow=False, lab=None, labpos=None, tag=None, tagpos=None):
        p = [P(*q) for q in pts]
        if solid:
            cv.line(p, fill=LINE, width_pt=1.0)
        else:
            cv.line(p, fill=DASHGRAY, width_pt=1.0, dash=(5, 3))
        if arrow:
            (x1, y1), (x2, y2) = p[-2], p[-1]
            cv.arrow(x2, y2, x2 - x1, y2 - y1, fill=(LINE if solid else DASHGRAY))
        if lab:
            lx_, ly_ = P(*labpos)
            edge_label(cv, lx_, ly_, lab)
        if tag:
            tx_, ty_ = P(*tagpos)
            edge_label(cv, tx_, ty_, tag, size=8)

    E([(142, 88), (142, 94)], True, False, "E01 サーバー間連携", (150, 91))
    E([(356, 44), (344, 44), (344, 26), (150, 26), (150, 62)], True, True, "E02 実装データ収集·送信", (158, 56))
    E([(356, 58), (352, 58), (352, 226), (140, 226), (140, 256)], True, False, "E03 ラインデータ", (230, 221))
    E([(100, 200), (100, 178), (318, 178), (318, 70), (314, 70)], True, True, "E04 参照·照合/稼働データ", (30, 170))
    E([(60, 240), (60, 256)], True, False, "E05 装置網接続", (66, 247))
    E([(120, 256), (120, 240)], False, True, "E06 ノズル/リーダー", (140, 247))
    E([(560, 64), (563, 64), (563, 222), (206, 222), (200, 222)], True, False, "E07 ジョブ退避", (480, 214))
    E([(314, 80), (320, 80), (320, 151), (554, 151), (566, 151)], True, True, "E08 稼働モニタ表示", (330, 84))
    E([(314, 70), (332, 70), (332, 214), (520, 214), (520, 252)], False, True, "E09 表示内容の由来?", (358, 206))
    E([(200, 234), (424, 234), (424, 262), (432, 262)], False, False, "E10 接続形態未確認", (360, 240))
    E([(300, 256), (300, 248), (150, 248), (150, 240)], True, False, "E14 LNB操作画面", (170, 250))
    E([(432, 315), (570, 315), (570, 252), (596, 252)], False, False, "E12 無線(AP経由)", (436, 322))
    E([(650, 270), (650, 282)], False, True, "E13 無線", (658, 274))
    E([(356, 139), (340, 139), (340, 120), (336, 120)], True, True, None, None, "E15", (340, 108))
    E([(356, 181), (348, 181), (348, 132), (336, 132)], True, True, None, None, "E16", (337, 156))
    E([(300, 28), (300, 12), (646, 12), (646, 30)], True, True, "E17 DB完全バックアップ", (480, 20))
    E([(240, 62), (240, 16), (322, 16), (556, 16), (556, 99), (566, 99)], True, True, "E18 外部I/F", (420, 8))

    # legend strip
    ly = 516
    cv.text(40, ly, "凡例: ", 9, anchor="lm")
    cv.text(66, ly, "実線=確定した接続 / グレー破線=推定(未確認)の接続 / 破線帯=ネットワーク帯 / 矢頭=データの向きが確定 / 枠の破線=推定機器(当Site未確認) / N番号·E番号=相関図リストの項目番号", 9, fill=(64, 64, 64), anchor="lm")
    cv.text(40, ly + 16, "分類: ", 9, anchor="lm")
    lx = 66
    for name, cls in [("サーバ系", "srv"), ("端末系", "term"), ("設備系", "eqp"), ("推定", "est"), ("外部", "ext")]:
        fill, line, bw, dsh = STYLE[cls]
        cv.rect(lx, ly + 10.5, 16, 10, fill=fill, outline=line, width_pt=0.9, radius=2)
        cv.text(lx + 20, ly + 16, name, 9, anchor="lm")
        lx += 20 + cv.tlen(name, 9) + 14

    out = os.path.join(OUTDIR, "redesign_mock.png")
    cv.im.save(out)
    print("saved", out, cv.im.size)

# ---------------- page B: list ----------------
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

def page_list():
    A4W, A4H = 595, 842
    cv = CV(A4W, A4H)
    cv.text(28, 30, "2-4. 相関図リスト(1/2)— 機器ノード", 12, anchor="lm")
    cv.text(28, 48, "図の N番号と対応する。詳細(位置づけ·運用·出典·要確認)は本リストに収録する。凡例と出典符の定義は(2/2)·図は2-3参照。", 8.5, fill=(64, 64, 64), anchor="lm")
    cols = [(28, 30), (60, 150), (212, 268), (482, 85)]
    heads = ["番号", "名称(図の表記)", "詳細(図から移動)", "要確認"]
    y = 62
    for (cx, cw), hname in zip(cols, heads):
        cv.rect(cx, y, cw, 14, fill=(242, 242, 242), outline=(150, 150, 150), width_pt=0.6)
        cv.text(cx + 4, y + 7, hname, 9, anchor="lm")
    y += 14
    fs, lh = 8.5, 11
    for num, name, det, conf in NODE_ROWS:
        dl = wrap(cv, det, fs, cols[2][1] - 8)
        nl = wrap(cv, name, fs, cols[1][1] - 8)
        cl = wrap(cv, conf, fs, cols[3][1] - 8)
        rows = max(len(dl), len(nl), len(cl), 1)
        rh = rows * lh + 4
        if y + rh > A4H - 120:
            cv.text(28, y + 8, "(以下次頁)", 8.5, fill=(150, 150, 150), anchor="lm")
            print("LIST OVERFLOW at", num, "y=", y)
            break
        for (cx, cw), lines in zip(cols[1:], [nl, dl, cl]):
            ty = y + 2 + lh / 2
            for ln in lines:
                cv.text(cx + 4, ty, ln, fs, anchor="lm")
                ty += lh
        cv.text(cols[0][0] + 4, y + 2 + (rh - 4) / 2, num, fs, anchor="lm")
        cv.line([(28, y + rh), (A4W - 28, y + rh)], fill=(200, 200, 200), width_pt=0.5)
        y += rh
    # N05 operation note block
    y += 8
    cv.text(28, y, "運用注記(旧N05注記ボックスから移動·本文§2.1)", 9.5, anchor="lm")
    y += 14
    for i, p in enumerate(N05_PARAS, 1):
        for ln in wrap(cv, f"({i}) {p}", fs, A4W - 56):
            cv.text(28, y + 5, ln, fs, anchor="lm")
            y += lh
        y += 2
    # band rows
    y += 4
    cv.text(28, y, "帯(ネットワークセグメント)", 9.5, anchor="lm")
    y += 14
    for s in [
        "帯a: PanaCIM管理側ネットワーク — 上位網 192.168.30.xx / 当Site実測: 制限セグメント 172.25.253.0/24〔T1:-9-/-10-·T1b: ネットワークイメージ.pptx·2026-10-27〕",
        "帯b: ライン設備側ネットワーク — 内部網 192.168.10.xx/20.xx(DHCP)·LNB設備側 192.168.20.25〔T1:-9-/-10-〕",
    ]:
        for ln in wrap(cv, s, fs, A4W - 56):
            cv.text(28, y + 5, ln, fs, anchor="lm")
            y += lh
        y += 2
    cv.text(28, A4H - 40, "(2/2) に接続リスト(E01〜E18·E11は未描画)·出典符(T1/T1b/T2/T3)の定義を収録する。", 8.5, fill=(64, 64, 64), anchor="lm")
    cv.text(28, A4H - 24, "NR4030", 9, fill=GRAY)
    out = os.path.join(OUTDIR, "redesign_mock_list.png")
    cv.im.save(out)
    print("saved", out, cv.im.size, "bottom y(pt)=", round(y, 1))

# ---------------- compare ----------------
def page_compare():
    new = Image.open(os.path.join(OUTDIR, "redesign_mock.png"))
    try:
        old = Image.open(RENDER).convert("RGB")
    except Exception:
        print("compare skipped (no render)")
        return
    H = 1400
    def sc(im):
        w = int(im.width * H / im.height)
        return im.resize((w, H), Image.LANCZOS)
    new, old = sc(new), sc(old)
    gap, cap = 24, 46
    W = new.width + old.width + gap * 3
    sheet = Image.new("RGB", (W, H + cap + 10), "white")
    d = ImageDraw.Draw(sheet)
    f = jf(30)
    d.text((gap, 8), "現行(Stage 5·85%縮小·ラベル遠隔·備考入り)", font=jf(26), fill="black")
    d.text((gap + old.width + gap, 8), "再設計案(100%·最低限ノード+番号チップ·詳細はリスト)", font=jf(26), fill="black")
    sheet.paste(old, (gap, cap))
    sheet.paste(new, (gap + old.width + gap, cap))
    out = os.path.join(OUTDIR, "redesign_mock_compare.png")
    sheet.save(out)
    print("saved", out, sheet.size)

if __name__ == "__main__":
    page_diagram()
    page_list()
    page_compare()
