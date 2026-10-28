# -*- coding: utf-8 -*-
"""corr_pana_15_tables.py — Stage 5 final candidate tables (2026-10-28, orchestrator).
Authority: corr_pana_14_result.json (geometry), corr_pana_14_texts.json (texts),
correlation_rebuild_spec.md des-2 §3 (edge semantics) + addendum2 (案C′, node freeze).
Resolutions vs route_input memo:
  E04 x428 vertical + y171 bridge + x162 descent (E08 yielded x162);
      E04 horizontal lane y314 (clears band_b_head text ink y316-328.4 by 2pt)
  E07 horizontal lane y330 (same A6 avoidance; endpoint on N07 bottom-right corner)
  E08 west exit (8,77)->(4,77)->(4,192)
  E09 P-1 adopted (user 2026-10-28, re-confirmed after crossing-count correction):
       origin N02->N03, x386 descent. Total crossings unchanged at 10 (E09-related 6,
       three edge pairs crossed twice); benefit is qualitative: no dashed-dashed
       crossing, no E15/E16 terminal-zone crossings, container-frame parallel gone
  E12 (140,250)->(140,234)->(464,234)->(464,232) (N10 pierce fixed)
  E05/E06 straight verticals x88/x100 (spec: parallel, offset)
  E10 descent x400 (clears E06 label corridor)
   E18 y-lane 25 (removes the 1.7pt E17 ink exception)
   E11 not drawn (no label slot — v3.1-mine decision kept)
   Head-box repair (2026-10-28): Stage 4 fit_text measured empty-text BoundHeight, so the
   head text never actually fit (render showed 12pt text wrapping to 3-5 lines out of
   18/30pt boxes). band_a_head widened w200->470 for a1 11pt bold + a2 10pt, one line each.
   band_b_head moved to (178,315,248,18): N07 (0,294,176,36) overlaps the old box position
   x0-176 and hid the first ~176pt of b1's text (node x head-box overlap was a validator
   blind spot). b1 is now the title part only ("ライン設備側ネットワーク — 内部網", 12pt bold,
   one line); the segment detail stays in texts.json b1 — LNB設備側 IP already in E05's
   label, the 192.168.10.xx/20.xx(DHCP) part deferred to Stage 6 notes. x426 keeps 4pt
   from E07's x430 vertical. E18 label moved (210,9)->(666,314,82,3): its old slot sits
   inside the widened band_a ink and band_a has no free window (machine-scanned); band_b
   right column chosen (A7 is position-based).
  East-mid label stack x440-652: E03(236)/E13(250.5)/E14(265)/E05(289.5) —
      E03 moved here (E02 ink collision at y174); hugs E03's own x656 vertical.
  East column x665-750: E15(152)/E09(192)/E10(246)/E16(273).
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "corr_pana_14_result.json"), encoding="utf-8") as f:
    _RESULT = json.load(f)

# name -> (x0, y0, x1, y1)  [pt, origin = B11 top-left]
SHAPES = {k: (float(v["x"]), float(v["y"]), float(v["x"]) + float(v["w"]), float(v["y"]) + float(v["h"]))
          for k, v in _RESULT["shapes"].items()}
# Head-box repair (2026-10-28, see docstring): overrides on the frozen Stage 4 geometry.
SHAPES["band_a_head"] = (0.0, 0.0, 470.0, 30.0)
SHAPES["band_b_head"] = (178.0, 315.0, 426.0, 333.0)
CONTAINER = "n01_esxi"          # background container: A1/A5 exempt (children still block)
BAND_HEADS = ("band_a_head", "band_b_head")
BAND_SPLIT_Y = 312.0            # band_a above, band_b below
FIG_RIGHT, FIG_BOTTOM = 750.0, 366.0

ROUTES = {
    "E01": [(194, 77), (202, 77)],
    "E02": [(300, 108), (300, 105), (185, 105), (185, 102)],
    "E03": [(382, 158), (656, 158), (656, 336), (200, 336), (200, 340)],
    "E04": [(176, 314), (428, 314), (428, 171), (162, 171), (162, 102)],
    "E05": [(88, 330), (88, 340)],
    "E06": [(100, 340), (100, 330)],
    "E07": [(382, 164), (430, 164), (430, 330), (176, 330)],
    "E08": [(8, 77), (4, 77), (4, 192)],
    # P-1 adopted (user approval 2026-10-28): origin N02->N03. (382,95) = N03's
    # bottom-right corner; x386 clears N06's right edge (382) by 4pt and N05's left
    # (395) by 9pt. Crossings 6 -> 5 (E03's y158 segment also crosses x386 — the
    # proposal memo counted 4; the validator's set below is authoritative).
    "E09": [(382, 95), (386, 95), (386, 190), (662, 190), (662, 353), (650, 353)],
    "E10": [(140, 330), (140, 332), (400, 332), (400, 353), (430, 353)],
    "E12": [(140, 250), (140, 234), (464, 234), (464, 232)],
    "E13": [(544, 212), (552, 212)],
    "E14": [(172, 286), (172, 294)],
    "E15": [(166, 192), (166, 176)],
    "E16": [(356, 192), (356, 176)],
    "E17": [(210, 34), (210, 30), (687.5, 30), (687.5, 34)],
    "E18": [(101, 52), (101, 32), (204, 32), (204, 25), (622, 25), (622, 118), (625, 118)],
}

ENDPOINTS = {  # edge -> (from_node, to_node) per spec §3
    "E01": ("n02_app", "n03_ctrl"), "E02": ("n06_dgs", "n02_app"),
    "E03": ("n06_dgs", "n08_line"), "E04": ("n07_lnb", "n02_app"),
    "E05": ("n07_lnb", "n08_line"), "E06": ("n08_line", "n07_lnb"),
    "E07": ("n06_dgs", "n07_lnb"), "E08": ("n02_app", "n10_monitor"),
    "E09": ("n03_ctrl", "n09_andon"), "E10": ("n07_lnb", "n09_andon"),
    "E12": ("n12_pda", "n13_ap"), "E13": ("n13_ap", "n14_tablet"),
    "E14": ("n11_lws", "n07_lnb"), "E15": ("n15_cima_pc", "n01_esxi"),
    "E16": ("n16_cimc_pc", "n01_esxi"), "E17": ("n01_esxi", "n17_backup"),
    "E18": ("n02_app", "n18_extif"),
}

NOT_DRAWN = {
    "E11": "ラベル用スロットなし(band_b x182-352 y288-312はE04ラベルと、x302-428 y296-308は1行幅不足)。"
           "route_input §2.4のv3.1-mine決定(未描画+逸脱報告)を維持。",
}

# id -> (x, y, w, lines): invisible box, TOP anchor, margin 0; ink h = 12.4 + 9.9*(lines-1)
LABELS = {
    "E01": (196, 37, 129, 1),
    "E02": (436, 162, 140, 2),
    "E03": (440, 236, 212, 1),
    "E04": (180, 288, 180, 2),
    "E05": (440, 289.5, 212, 2),
    "E06": (222, 340, 174, 2),
    "E07": (10, 150, 148, 2),
    "E08": (10, 175, 122, 1),
    "E09": (670, 192, 80, 4),
    "E10": (665, 246, 85, 2),
    "E12": (244, 236, 172, 1),
    "E13": (440, 250.5, 212, 1),
    "E14": (440, 265, 212, 2),
    "E15": (665, 152, 85, 3),
    "E16": (665, 273, 85, 3),
    "E17": (480, 0, 205, 2),
    # moved 2026-10-28: old slot (210,9) is inside the widened band_a_head ink. Machine
    # search found NO band_a slot for the full text (nodes N02-N06/N10/N12/N13-N19,
    # E03 y158 lane, E17 y30 lane, E07/E08/E12/E04 labels block every window); the right
    # column x622-750 and the y24-33 strip are also full. Placed in the band_b right
    # column stack instead (A7 is position-based): below E16's label ink (305.3),
    # right of E09's x662 vertical, clear of N09 (x1=650).
    "E18": (666, 314, 82, 3),
}

EXPECTED_CROSSINGS = [  # (x, y, edge_a, edge_b)  — P-1 adopted: total unchanged at 10 (E09-related 6)
    (386, 158, "E09", "E03"),
    (386, 164, "E09", "E07"),
    (386, 171, "E09", "E04"),
    (428, 190, "E04", "E09"),
    (430, 190, "E07", "E09"),
    (656, 190, "E03", "E09"),
    (428, 234, "E04", "E12"),
    (430, 234, "E07", "E12"),
    (400, 336, "E10", "E03"),
    (622, 30, "E17", "E18"),
]

DOC_EXCEPTIONS = []  # E17-E18 1.7pt exception resolved (E18 lane moved 24 -> 25)

DEVIATIONS = {
    "E09_origin_P1": "P-1採用(ユーザー承認2026-10-28·交差数の訂正を提示した上で再承認): E09起点をN02→N03へ変更(x386経由)。"
                     "エッジ意味表の変更を伴う(アンドン表示の由来をPanaCIMサーバー群に広げる解釈)·会議の確認事項X02-①と合わせて最終確認。"
                     "交差はE09関係6件(E03×E09が(386,158)と(656,190)·E04×E09が(386,171)と(428,190)·E07×E09が(386,164)と(430,190)·"
                     "いずれも同ペア2回の二重交差)·総数は旧案と同じ10件で削減効果はなし(案のメモの「6→4」はy158/y164区間の見落とし)。"
                     "採用根拠は定性改善: 破線同士の交差(E08×E09)の解消·E15/E16端末区での交差解消·N01容器枠併走(x2縦線)の解消。",
    "E04_E07_lane": "E04のy314レーンとE07のy330レーンはband_b_head文字ink(y316-328.4)の回避のため"
                    "帯境界直下に通した(それぞれ文字ink上端+2pt·下端+1.6ptの非重複)。E07終点はN07右下隅。",
    "E11_not_drawn": NOT_DRAWN["E11"],
    "remote_labels": "遠隔配置(逸脱報告): E02/E05/E06/E07/E10/E13/E14/E15/E16/E18(10枚)。E18は2026-10-28の"
                     "帯見出し拡幅で旧スロット(210,9)が消失し、帯a内に全文の空きが機械探索でも皆無だったため"
                     "帯b右列(y314-346)へ移動·遠隔化(約200pt)。近接: E01/E03/E04/E08/E09/E12/E17。",
    "label_stack": "東ラベル縦積み: E15(152-184)/E09(192-234)/E10(246-268)/E16(273-305) @x665-750、"
                   "E03(236-248)/E13(250-263)/E14(265-287)/E05(289-312) @x440-652(E03縦線x656の左側)。",
    "band_head_fit": "帯見出し箱修復(Stage 4欠陥): fit_textが空テキスト状態のBoundHeightを測り文字溢れを検出できなかった。"
                     "band_a_headをw200→470に拡幅しa1 11pt太字/a2 10ptを各1行に(a1は12ptから実ink下端23.3ptが"
                     "y25レーンに対し狭いため11ptに落とした)。band_b_headは旧配置(x0起点)ではN07(0,294,176,36)が"
                     "重なりb1の前方約176ptを隠した(ノード×見出し箱の重なりはA6/A7の検査対象外だった盲点)ため、"
                     "箱を(178,315,248,18)へ移動しb1は題名部「ライン設備側ネットワーク — 内部網」11pt太字1行のみ"
                     "(12ptは1行のboundが13pt超で11pt·band_a題名と同サイズ)。"
                     "セグメント詳細(LNB設備側192.168.20.25等)はE05ラベル既載·192.168.10.xx/20.xx(DHCP)はStage 6注記へ繰延"
                     "(texts.json b1が原案)。x426はE07縦線x430と4pt非重複·A6は重複ゼロ判定で適合。"
                     "E18ラベルを(210,9)→(666,314,82,3)へ移動(旧スロットは拡幅ink内·帯a内の空きは機械探索でも"
                     "皆無→帯b右列へ·遠隔化約200pt)。"
                     "実ink: band_a下端23.33(y25レーンと1.67pt)·band_b下端328.08(y330レーンのストローク上端329.625と1.5pt)。",
}
