# -*- coding: utf-8 -*-
"""相関図の移動計画(JSON)を作業コピーに適用し、PDF/PNGを出力する。

使い方:
  python apply_moves.py <src_xlsx> <dst_xlsx> <moves.json> <out_dir>

moves.json 形式:
{
  "sheet": "相関図②",
  "moves": [
    {"shape": "g2_n02", "dx": 0, "dy": 6, "reason": "..."},
    {"shape": "g2_e_e17_s1", "left": 100, "top": 188},
    {"shape": "g2_n05", "w": 160, "h": 120}
  ]
}
"""
import json
import shutil
import sys
from pathlib import Path

import fitz
import win32com.client as win32


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


def main():
    src, dst, moves_path, out_dir = sys.argv[1:5]
    spec = json.loads(Path(moves_path).read_text(encoding="utf-8"))
    sheet_name = spec["sheet"]
    moves = spec["moves"]
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if Path(src).resolve() != Path(dst).resolve():
        shutil.copy2(src, dst)

    xl = win32.DispatchEx("Excel.Application")
    xl.Visible = False
    xl.DisplayAlerts = False
    applied, missing = [], []
    try:
        wb = xl.Workbooks.Open(dst, UpdateLinks=0, ReadOnly=False)
        ws = next(s for s in wb.Worksheets if s.Name == sheet_name)
        for mv in moves:
            sh = find_shape(ws.Shapes, mv["shape"])
            if sh is None:
                missing.append(mv["shape"])
                continue
            if "left" in mv:
                sh.Left = float(mv["left"])
            if "top" in mv:
                sh.Top = float(mv["top"])
            if "dx" in mv:
                sh.Left = float(sh.Left) + float(mv["dx"])
            if "dy" in mv:
                sh.Top = float(sh.Top) + float(mv["dy"])
            if "w" in mv:
                sh.Width = float(mv["w"])
            if "h" in mv:
                sh.Height = float(mv["h"])
            applied.append(mv["shape"])
        wb.Save()
        pdf = out_dir / f"{sheet_name}.pdf"
        ws.ExportAsFixedFormat(0, str(pdf))
        doc = fitz.open(str(pdf))
        pix = doc[0].get_pixmap(dpi=150)
        png = out_dir / f"{sheet_name}.png"
        pix.save(str(png))
        doc.close()
        wb.Close(False)
    finally:
        xl.Quit()
    print(json.dumps({"applied": len(applied), "missing": missing,
                      "png": str(out_dir / f"{sheet_name}.png")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
