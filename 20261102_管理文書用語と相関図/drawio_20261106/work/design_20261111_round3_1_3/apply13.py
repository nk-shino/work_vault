"""Apply position/size-only moves to 相関図①/③ and read back the result.

Only Left/Top/Width/Height are written. Nothing else is touched.
Usage: python apply13.py <src.xlsx> <dst.xlsx> <moves.json> <readback.json>
"""
import json
import os
import shutil
import sys

import win32com.client as win32

FIELDS = {"Left": "Left", "Top": "Top", "Width": "Width", "Height": "Height"}


def main(src, dst, moves_path, readback_path):
    src, dst, moves_path, readback_path = (os.path.abspath(x) for x in
                                          (src, dst, moves_path, readback_path))
    moves = json.load(open(moves_path, encoding="utf-8"))
    shutil.copyfile(src, dst)
    app = win32.gencache.EnsureDispatch("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    readback = {}
    wb = None
    try:
        wb = app.Workbooks.Open(dst)
        for sheet, shapes in moves.items():
            ws = wb.Worksheets(sheet)
            readback[sheet] = {}
            for name, spec in shapes.items():
                try:
                    s = ws.Shapes(name)
                except Exception:
                    print("  MISSING", sheet, name)
                    readback[sheet][name] = {"error": "missing"}
                    continue
                before = {f: round(getattr(s, f), 3) for f in FIELDS}
                for field, value in spec.items():
                    if field not in FIELDS:
                        raise SystemExit("refusing unknown field: %s" % field)
                    setattr(s, field, float(value))
                after = {f: round(getattr(s, f), 3) for f in FIELDS}
                readback[sheet][name] = {"before": before, "after": after}
                flags = []
                for f in FIELDS:
                    want = spec.get(f)
                    if want is None:
                        continue
                    if abs(after[f] - float(want)) > 0.02:
                        flags.append("%s want %.2f got %.2f" % (f, float(want), after[f]))
                print("  %-13s %s" % (name, "OK" if not flags else "DRIFT: " + "; ".join(flags)))
        wb.Save()
    finally:
        if wb is not None:
            wb.Close(SaveChanges=False)
        app.Quit()
    with open(readback_path, "w", encoding="utf-8") as fh:
        json.dump(readback, fh, ensure_ascii=False, indent=1)
    print("saved", dst)
    print("readback", readback_path)


if __name__ == "__main__":
    main(*sys.argv[1:5])
