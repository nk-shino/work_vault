# -*- coding: utf-8 -*-
"""probe_boxes_lnb.py — 様式ブロック(行1-3)の結合箱幅を改修前/後で比較 (openpyxl·読み取り専用)。

v2: <col min max> の範囲定義を min..max に展開して列幅マップを作成する。
"""
import json
import os

import openpyxl

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XLSX = os.path.normpath(os.path.join(
    BASE, "..", "..", "OneDrive - NK", "ドキュメント", "Work_Vault",
    "10_業務全般", "PanaCIM_LNB", "01_成果物", "LNB管理手順書案_未承認.xlsx"))
BK = os.path.join(BASE, "backup_20261102", "LNB管理手順書案_未承認_改修前.xlsx")
ORDER17 = ["表紙", "目次", "用語", "構成と管理情報", "相関図", "相関図_old", "管理体制",
           "日次点検", "定期管理", "バックアップ", "復旧", "異常時の対応",
           "チェックシート(日次)", "チェックシート(月次・異常時)", "会議課題一覧(一時)",
           "要確認事項一覧", "引用と部品照合"]
DEFAULT_W = 8.38  # openpyxl の表示既定 (幅未定義列)


def width_map(ws):
    m = {}
    for cd in ws.column_dimensions.values():
        try:
            lo, hi, w = int(cd.min), int(cd.max), float(cd.width)
        except (TypeError, ValueError):
            continue
        if w:
            for c in range(lo, hi + 1):
                m[c] = w
    return m


def file_px(w):
    return int(w * 7) + 5


def box_widths(path, name):
    wb = openpyxl.load_workbook(path, read_only=False)
    try:
        ws = wb[name]
        wm = width_map(ws)
        out = []
        for rng in ws.merged_cells.ranges:
            if rng.min_row >= 1 and rng.max_row <= 3:
                w = 0.0
                missing = []
                for c in range(rng.min_col, rng.max_col + 1):
                    if c in wm:
                        w += wm[c]
                    else:
                        w += DEFAULT_W
                        missing.append(c)
                out.append({"range": str(rng), "px": round(file_px(w)),
                            "chars": round(w, 2),
                            "cols": f"{openpyxl.utils.get_column_letter(rng.min_col)}.."
                                    f"{openpyxl.utils.get_column_letter(rng.max_col)}",
                            "missing": len(missing)})
        return out
    finally:
        wb.close()


rep = {}
for name in ORDER17:
    pre = box_widths(BK, name)
    post = box_widths(XLSX, name)
    premap = {b["range"]: b for b in pre}
    rows = []
    for b in post:
        p = premap.get(b["range"])
        if p and b["px"] < p["px"] - 2:
            rows.append({"range": b["range"], "cols": b["cols"], "missing": b["missing"],
                         "pre_px": p["px"], "post_px": b["px"],
                         "pre_chars": p["chars"], "post_chars": b["chars"]})
    if rows:
        rep[name] = rows

print(json.dumps(rep, ensure_ascii=False, indent=1))
with open(os.path.join(BASE, "scripts", "probe_boxes_out.json"), "w", encoding="utf-8") as f:
    json.dump(rep, f, ensure_ascii=False, indent=1)
