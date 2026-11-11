# -*- coding: utf-8 -*-
"""移動計画を「現在のExcelが読み取る座標系」に換算して適用する。

背景:
  同じxlsxを同じ内容のまま開いても、Excelが返す Shape.Left/Top/W/H は
  設計時(2026-11-11 10:35)の測定値と一致しない（縦 +2.7%、横 -1.2%）。
  図形はセルにアンカーされているため、行高・列幅からptを再計算する際の
  環境差が座標に出る。計画の絶対値（例: 右端=598）をそのまま入れると、
  移動していない図形との関係（接触・角の結合）が数ptずれる。

方法:
  1. 設計時座標(old) → 現在座標(cur) の対応を、全図形の辺から校正曲線として作る。
  2. 計画の目標値(old)を校正曲線でcurへ写像する。
  3. cur目標を絶対値として書き込む。書き込んだ値は読み戻しでも一致する。

使い方:
  python apply_calibrated.py <src> <dst> <moves.json> <old_audit.json> <cur_audit.json> <out_dir>
"""
import json
import shutil
import sys
from pathlib import Path

import fitz
import win32com.client as win32


def flat(shapes):
    out = []
    for s in shapes:
        out.append(s)
        out.extend(flat(s.get("children") or []))
    return out


class Map1D:
    """単調な折れ線写像。校正点の外側は端の傾きで延長する。"""

    def __init__(self, pairs):
        pts = sorted(pairs)
        xs, ys = [], []
        for x, y in pts:
            if xs and abs(x - xs[-1]) < 1e-6:
                ys[-1] = (ys[-1] + y) / 2.0
            else:
                xs.append(x)
                ys.append(y)
        self.xs, self.ys = xs, ys

    def __call__(self, x):
        xs, ys = self.xs, self.ys
        if len(xs) == 1:
            return x + (ys[0] - xs[0])
        if x <= xs[0]:
            slope = (ys[1] - ys[0]) / (xs[1] - xs[0])
            return ys[0] + slope * (x - xs[0])
        if x >= xs[-1]:
            slope = (ys[-1] - ys[-2]) / (xs[-1] - xs[-2])
            return ys[-1] + slope * (x - xs[-1])
        lo, hi = 0, len(xs) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if xs[mid] <= x:
                lo = mid
            else:
                hi = mid
        t = (x - xs[lo]) / (xs[hi] - xs[lo])
        return ys[lo] + t * (ys[hi] - ys[lo])


def find_shape(shapes, name):
    for i in range(shapes.Count):
        sh = shapes.Item(i + 1)
        if str(sh.Name) == name:
            return sh
        if sh.Type == 6:
            try:
                found = find_shape(sh.GroupItems, name)
                if found is not None:
                    return found
            except Exception:
                pass
    return None


def plan_targets(moves, old_by_name):
    """計画JSONから設計時座標の目標矩形を作る（apply_movesと同じ順序）。"""
    out = {}
    for mv in moves:
        o = old_by_name[mv["shape"]]
        left, top = float(o["left"]), float(o["top"])
        w, h = float(o["w"]), float(o["h"])
        if "left" in mv:
            left = float(mv["left"])
        if "top" in mv:
            top = float(mv["top"])
        if "dx" in mv:
            left += float(mv["dx"])
        if "dy" in mv:
            top += float(mv["dy"])
        if "w" in mv:
            w = float(mv["w"])
        if "h" in mv:
            h = float(mv["h"])
        out[mv["shape"]] = (left, top, w, h)
    return out


def main():
    src, dst, moves_path, old_json, cur_json, out_dir = sys.argv[1:7]
    spec = json.loads(Path(moves_path).read_text(encoding="utf-8"))
    sheet_name = spec["sheet"]
    moves = spec["moves"]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    old = json.loads(Path(old_json).read_text(encoding="utf-8"))
    cur = json.loads(Path(cur_json).read_text(encoding="utf-8"))
    old_sh = {s["name"]: s for s in flat(old["shapes"])}
    cur_sh = {s["name"]: s for s in flat(cur["shapes"])}

    xp, yp = [], []
    for name, o in old_sh.items():
        c = cur_sh.get(name)
        if not c:
            continue
        xp.append((o["left"], c["left"]))
        xp.append((o["left"] + o["w"], c["left"] + c["w"]))
        yp.append((o["top"], c["top"]))
        yp.append((o["top"] + o["h"], c["top"] + c["h"]))
    mapx, mapy = Map1D(xp), Map1D(yp)

    targets_old = plan_targets(moves, old_sh)
    targets = {}
    for name, (l, t, w, h) in targets_old.items():
        x0, x1 = mapx(l), mapx(l + w)
        y0, y1 = mapy(t), mapy(t + h)
        targets[name] = (x0, y0, x1 - x0, y1 - y0)

    if Path(src).resolve() != Path(dst).resolve():
        shutil.copy2(src, dst)

    xl = win32.DispatchEx("Excel.Application")
    xl.Visible = False
    xl.DisplayAlerts = False
    applied, missing, residuals = [], [], []
    try:
        wb = xl.Workbooks.Open(dst, UpdateLinks=0, ReadOnly=False)
        ws = next(s for s in wb.Worksheets if s.Name == sheet_name)
        for mv in moves:
            name = mv["shape"]
            sh = find_shape(ws.Shapes, name)
            if sh is None:
                missing.append(name)
                continue
            L, T, W, H = targets[name]
            sh.Width = max(0.0, W)
            sh.Height = max(0.0, H)
            sh.Left = L
            sh.Top = T
            residuals.append((name, round(float(sh.Left) - L, 3), round(float(sh.Top) - T, 3),
                              round(float(sh.Width) - W, 3), round(float(sh.Height) - H, 3)))
            applied.append(name)
        wb.Save()
        pdf = out_dir / f"{sheet_name}.pdf"
        ws.ExportAsFixedFormat(0, str(pdf))
        doc = fitz.open(str(pdf))
        pix = doc[0].get_pixmap(dpi=150)
        pix.save(str(out_dir / f"{sheet_name}.png"))
        doc.close()
        wb.Close(False)
    finally:
        xl.Quit()

    worst = max((max(abs(v) for v in r[1:]) for r in residuals), default=0.0)
    print(json.dumps({
        "applied": len(applied), "missing": missing, "worst_residual_pt": worst,
        "residuals": [r for r in residuals if max(abs(v) for v in r[1:]) > 0.01],
    }, ensure_ascii=False))
    Path(out_dir / "targets.json").write_text(json.dumps(
        {k: [round(v, 3) for v in targets[k]] for k in targets}, ensure_ascii=False, indent=1),
        encoding="utf-8")


if __name__ == "__main__":
    main()
