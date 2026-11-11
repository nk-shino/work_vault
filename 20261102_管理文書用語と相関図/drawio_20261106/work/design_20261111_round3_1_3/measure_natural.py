"""Measure natural single-line width/height of clipped label shapes (throwaway copy)."""
import json
import os
import shutil
import sys

import win32com.client as win32

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "pana13_before.xlsx")
TMP = os.path.join(os.environ["TEMP"], "kohden-code", "pana13_measure.xlsx")

TARGETS = {
    "相関図③": [
        "g3_e_e03_l", "g3_e_e04_l", "g3_e_e05_l", "g3_e_e06_l", "g3_e_e07_l",
        "g3_e_e09_l", "g3_e_e10_l", "g3_e_e12_l", "g3_e_e13_l", "g3_e_e14_l",
        "g3_expl", "g3_n08_txt", "g3_n13_txt", "g3_n14_txt", "g3_pcr_txt",
        "g3_dgsr_txt", "g3_n12_txt",
    ],
    "相関図①": [
        "g1_e_e02_l", "g1_expl", "g1_e_e08_l", "g1_e_e04_l", "g1_p1_txt",
        "g1_s1_txt", "g1_ea_txt",
    ],
}


def main():
    os.makedirs(os.path.dirname(TMP), exist_ok=True)
    shutil.copyfile(SRC, TMP)
    app = win32.gencache.EnsureDispatch("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    out = {}
    wb = None
    try:
        wb = app.Workbooks.Open(TMP)
        for sheet, names in TARGETS.items():
            ws = wb.Worksheets(sheet)
            print("=====", sheet)
            for nm in names:
                try:
                    s = ws.Shapes(nm)
                except Exception:
                    print("  MISSING", nm)
                    continue
                tf = s.TextFrame2
                w0, h0 = s.Width, s.Height
                wrap, auto = tf.WordWrap, tf.AutoSize
                txt = tf.TextRange.Text.replace("\r", " | ")
                tf.WordWrap = 0
                tf.AutoSize = 1
                wn, hn = s.Width, s.Height
                tf.WordWrap = wrap
                tf.AutoSize = auto
                s.Width, s.Height = w0, h0
                need = wn + 3.0
                print("  %-12s W=%7.2f H=%6.2f -> natW=%7.2f natH=%5.2f "
                      "needW=%7.2f slack=%6.2f fs=%s"
                      % (nm, w0, h0, wn, hn, need, need - w0,
                         tf.TextRange.Font.Size))
                print("      %s" % txt)
                out[nm] = {
                    "W": round(w0, 2), "H": round(h0, 2),
                    "Wnat": round(wn, 2), "Hnat": round(hn, 2),
                    "needW": round(need, 2), "slack": round(need - w0, 2),
                }
    finally:
        if wb is not None:
            wb.Close(False)
        app.Quit()
    path = os.path.join(HERE, "natural_widths.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print("saved", path)


if __name__ == "__main__":
    sys.exit(main())
