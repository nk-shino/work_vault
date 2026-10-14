# -*- coding: utf-8 -*-
"""装飾スタイルの検証: フォント・サイズ・色が統一仕様どおりか。"""
import openpyxl
import os
import sys
from collections import Counter

BASE = os.path.dirname(os.path.abspath(__file__))
FILES = ["..\\PanaCIM管理手順書_草案.xlsx", "..\\LNB管理手順書_草案.xlsx"]
FONT = "游ゴシック"
ALLOWED_FILLS = {"00D9E1F2", "00FFF2CC", "00FCE4D6", "004472C4"}
ALLOWED_FONTCOLORS = {"00FFFFFF", "001F3864", "00595959", "00833C00", "00000000", "00808080", "000563C1", None}  # 808080=解決済み取消線/0563C1=ハイパーリンク

problems = []
for fname in FILES:
    wb = openpyxl.load_workbook(os.path.join(BASE, fname))
    fonts = Counter()
    fills = Counter()
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for c in row:
                if c.value is None and not (c.fill and c.fill.fgColor and c.fill.fgColor.rgb not in (None, "00000000")):
                    continue
                f = c.font
                try:
                    rgb = f.color.rgb if f.color else None
                except (AttributeError, TypeError, ValueError):
                    rgb = None
                if rgb is not None and not isinstance(rgb, str):
                    rgb = None  # theme色等の非str値は既定色扱い
                fonts[(f.name, f.size, f.bold, rgb)] += 1
                if c.fill and c.fill.patternType == "solid":
                    fills[c.fill.fgColor.rgb] += 1
    print(f"===== {fname} =====")
    print("fonts:")
    for k, v in fonts.most_common():
        print("  ", k, v)
        if k[0] not in (FONT, None) and v > 0 and k[0] != "Calibri":
            problems.append(f"{fname}: 想定外フォント {k[0]} ({v}セル)")
        if k[3] is not None and k[3] not in ALLOWED_FONTCOLORS and v > 0:
            problems.append(f"{fname}: 想定外文字色 {k[3]} ({v}セル)")
    print("fills:")
    for k, v in fills.most_common():
        print("  ", k, v)
        if k not in ALLOWED_FILLS:
            problems.append(f"{fname}: 想定外塗り {k} ({v}セル)")

print()
if problems:
    print(f"--- 装飾不整合 {len(problems)} 件 ---")
    for p in problems:
        print(" !!", p)
    sys.exit(1)
print("--- 装飾検証OK ---")
