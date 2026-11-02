# -*- coding: utf-8 -*-
"""crop_zoom.py — レンダPDFの指定領域を高DPIで切り出して目視確認する。"""
import os
import sys
import pymupdf

OUT = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図\render_survey"
PNG = os.path.join(OUT, "png")

# (book, sheet, page, clip_pt(x0,y0,x1,y1), dpi, name)
JOBS = [
    ("Pana-CIM", "相関図", 1, (0, 200, 500, 330), 200, "souzuzu_topleft"),
    ("Pana-CIM", "相関図", 1, (700, 200, 842, 470), 200, "souzuzu_right"),
    ("LNB", "目次", 1, (50, 140, 320, 380), 200, "mokuji_LNB_list"),
    ("LNB", "目次", 2, (40, 30, 220, 220), 200, "mokuji_LNB_p2frag"),
    ("LNB", "相関図", 1, (40, 125, 320, 165), 300, "souzuzu_LNB_heading"),
]


def main() -> None:
    for book, sheet, pno, clip, dpi, name in JOBS:
        pdf = os.path.join(OUT, book, sheet + ".pdf")
        doc = pymupdf.open(pdf)
        page = doc[pno - 1]
        rect = pymupdf.Rect(*clip)
        pix = page.get_pixmap(dpi=dpi, clip=rect)
        out = os.path.join(PNG, f"zoom_{name}.png")
        pix.save(out)
        print("WROTE", out)
        doc.close()


if __name__ == "__main__":
    main()
