# -*- coding: utf-8 -*-
"""probe_text.py — レンダPDFのテキストを座標付きで抽出し、断片頁·位置ずれを確定する。"""
import os
import sys
import pymupdf

OUT = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図\render_survey"

TARGETS = [
    ("Pana-CIM", "管理体制", [1]),
    ("Pana-CIM", "チェックシート(月次・異常時)", [1]),
    ("LNB", "チェックシート(月次・異常時)", [1]),
    ("LNB", "目次", [1]),
]


def main() -> None:
    for book, sheet, pages in TARGETS:
        pdf = os.path.join(OUT, book, sheet + ".pdf")
        doc = pymupdf.open(pdf)
        print(f"=== {book}/{sheet} ({doc.page_count}頁) ===")
        for pno in pages:
            if pno > doc.page_count:
                continue
            page = doc[pno - 1]
            print(f"--- p{pno} rect={page.rect} ---")
            for x0, y0, x1, y1, text, *_ in page.get_text("words"):
                print(f"  ({x0:6.1f},{y0:6.1f})-({x1:6.1f},{y1:6.1f}) {text}")
        doc.close()


if __name__ == "__main__":
    sys.exit(main())
