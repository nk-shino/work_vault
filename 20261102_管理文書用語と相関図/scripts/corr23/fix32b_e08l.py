# -*- coding: utf-8 -*-
"""fix32b_e08l.py — g2_e_e08_l の Left を設計値 402 へ (両冊·最小修正)。

fix32_corr23.py で e08_l は t/w のみ設定し Left を旧値(598)のまま残したため、
n18_txt(x626..) と重なった。設計は (402, 416.5, 128) — x402..530。
"""
import sys, os, time
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from collision_check import read_flips_xml  # noqa: F401  (stdout utf-8 wrap)

import win32com.client as win32

BOOKS = {
    "lnb": (r"C:/Users/ss80751/OneDrive - NK/ドキュメント/Work_Vault"
            r"/10_業務全般/PanaCIM_LNB/01_成果物/LNB管理手順書案_未承認.xlsx"),
}  # pana は13:00:34に保存済み(Left=402)のため対象外
S2 = "相関図②"


def open_book(app, path):
    last = None
    for i in range(6):
        try:
            return app.Workbooks.Open(path, UpdateLinks=0, ReadOnly=False)
        except Exception as e:
            last = e
            print("  open retry %d: %s" % (i + 1, str(e)[:120]))
            time.sleep(3)
    raise RuntimeError("cannot open %s: %s" % (path, last))


for bk, path in BOOKS.items():
    print("== %s" % bk)
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    try:
        try:
            app.ScreenUpdating = False
        except Exception:
            pass
        wb = open_book(app, path)
        try:
            wb.AutoSaveOn = False
        except Exception:
            pass
        ws = wb.Worksheets(S2)
        sh = ws.Shapes("g2_e_e08_l")
        sh.Left = 402.0
        drift = abs(float(sh.Left) - 402.0)
        print("  g2_e_e08_l Left -> %.2f (drift %.2f)" % (float(sh.Left), drift))
        if drift > 0.75:
            raise RuntimeError("drift too large for %s" % bk)
        wb.Save()
        wb.Close(SaveChanges=False)
        print("  saved.")
    finally:
        try:
            app.Quit()
        except Exception:
            pass
print("FIX32B DONE")
