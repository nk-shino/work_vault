# -*- coding: utf-8 -*-
"""fix31_g8_geoprobe.py — 図形幾何とPageSetupの数値取得(保存しない·テキスト非表示)。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import win32com.client as win32

BOOKS = {
    "pana": (r"C:/Users/ss80751/OneDrive - NK/ドキュメント/Work_Vault"
             r"/10_業務全般/PanaCIM_LNB/01_成果物/Pana-CIM管理手順書案_未承認.xlsx"),
    "lnb": (r"C:/Users/ss80751/OneDrive - NK/ドキュメント/Work_Vault"
            r"/10_業務全般/PanaCIM_LNB/01_成果物/LNB管理手順書案_未承認.xlsx"),
}

app = win32.DispatchEx("Excel.Application")
app.Visible = False
app.DisplayAlerts = False
try:
    for book, path in BOOKS.items():
        wb = app.Workbooks.Open(path, UpdateLinks=0, ReadOnly=True)
        for gname in ("相関図①", "相関図②", "相関図③"):
            ws = wb.Worksheets(gname)
            ps = ws.PageSetup
            print("%s %s: zoom=%s fitW=%s fitT=%s paper=%s mT=%.0f mB=%.0f" % (
                book, gname, ps.Zoom, ps.FitToPagesWide, ps.FitToPagesTall,
                ps.PaperSize, ps.TopMargin, ps.BottomMargin))
            for i in range(1, ws.Shapes.Count + 1):
                sh = ws.Shapes(i)
                nm = sh.Name
                if sh.Type == 6 and ("_n" in nm or nm.split("_")[-1] in
                                     ("p1", "p2", "s1", "s2", "ea", "eb", "liner")):
                    print("   %-14s L=%6.1f T=%6.1f W=%6.1f H=%6.1f" % (
                        nm, sh.Left, sh.Top, sh.Width, sh.Height))
                elif nm.endswith(("_leg0", "_leg1", "_leg2", "_leg3")):
                    print("   %-14s L=%6.1f T=%6.1f W=%6.1f H=%6.1f" % (
                        nm, sh.Left, sh.Top, sh.Width, sh.Height))
        wb.Close(SaveChanges=False)
finally:
    try:
        app.Quit()
    except Exception:
        pass
print("GEOPROBE DONE")
