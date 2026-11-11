# -*- coding: utf-8 -*-
"""ページ設定だけを変更する（用紙・向き・余白・印刷範囲は維持）。

使い方:
  python set_pagesetup.py <xlsx> fit11
  python set_pagesetup.py <xlsx> zoom:80
  python set_pagesetup.py <xlsx> fitwide
"""
import os
import sys

import win32com.client as win32

SHEETS = ["相関図①", "相関図②", "相関図③"]


def main(path, mode):
    path = os.path.abspath(path)
    xl = win32.gencache.EnsureDispatch("Excel.Application")
    xl.Visible = False
    xl.DisplayAlerts = False
    wb = None
    try:
        wb = xl.Workbooks.Open(path)
        for sheet in SHEETS:
            ws = wb.Worksheets(sheet)
            ps = ws.PageSetup
            before = (ps.PaperSize, ps.Orientation, ps.PrintArea, ps.LeftMargin,
                      ps.TopMargin, ps.RightMargin, ps.BottomMargin)
            if mode == "fit11":
                ps.Zoom = False
                ps.FitToPagesWide = 1
                ps.FitToPagesTall = 1
            elif mode == "fitwide":
                ps.Zoom = False
                ps.FitToPagesWide = 1
                ps.FitToPagesTall = False
            elif mode.startswith("zoom:"):
                ps.FitToPagesWide = False
                ps.FitToPagesTall = False
                ps.Zoom = int(mode.split(":", 1)[1])
            else:
                raise SystemExit("unknown mode: " + mode)
            after = (ps.PaperSize, ps.Orientation, ps.PrintArea, ps.LeftMargin,
                     ps.TopMargin, ps.RightMargin, ps.BottomMargin)
            kept = "維持" if before == after else "変化 %s -> %s" % (before, after)
            print("  %-8s zoom=%s fitW=%s fitH=%s  用紙/向き/範囲/余白: %s" % (
                sheet, ps.Zoom, ps.FitToPagesWide, ps.FitToPagesTall, kept))
        wb.Save()
    finally:
        if wb is not None:
            wb.Close(SaveChanges=False)
        xl.Quit()
    print("saved", path, "mode", mode)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
