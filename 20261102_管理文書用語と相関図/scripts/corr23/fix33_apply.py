import sys, io, os, traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import pythoncom, win32com.client
VAULT = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
BOOKS = {"pana": "Pana-CIM管理手順書案_未承認.xlsx", "lnb": "LNB管理手順書案_未承認.xlsx"}
WIDTHS = {"g2_e_e01_l": 112.0, "g2_e_e02_l": 120.0, "g2_e_e08_l": 134.0, "g2_e_e17_l": 176.0}
pythoncom.CoInitialize()
xl = None
try:
    xl = win32com.client.DispatchEx("Excel.Application")
    xl.Visible = False; xl.DisplayAlerts = False
    for bk, fn in BOOKS.items():
        p = os.path.join(VAULT, fn)
        wb = xl.Workbooks.Open(p, ReadOnly=False)
        try:
            try: wb.AutoSaveOn = False
            except Exception: pass
            ws2 = wb.Worksheets("相関図②"); ws3 = wb.Worksheets("相関図③")
            for nm, w in WIDTHS.items():
                ws2.Shapes(nm).Width = w
            grp = ws3.Shapes("g3_e_e03")
            grp.GroupItems("g3_e_e03_s0").Width = 33.0
            grp.GroupItems("g3_e_e03_s1").Left = 268.0
            s2c = grp.GroupItems("g3_e_e03_s2"); s2c.Left = 268.0; s2c.Width = 468.0
            grp.GroupItems("g3_e_e03_s3").Left = 736.0
            # 読み戻し検証
            for nm, w in WIDTHS.items():
                got = ws2.Shapes(nm).Width
                assert abs(got - w) < 0.01, f"{nm} {got}!={w}"
            for nm, exp in (("g3_e_e03_s0",(235.0,356.0,33.0,0.0)), ("g3_e_e03_s1",(268.0,356.0,0.0,129.0)),
                            ("g3_e_e03_s2",(268.0,485.0,468.0,0.0)), ("g3_e_e03_s3",(736.0,205.0,0.0,280.0))):
                c = grp.GroupItems(nm)
                got = (round(c.Left,1), round(c.Top,1), round(c.Width,1), round(c.Height,1))
                assert all(abs(a-b) < 0.05 for a,b in zip(got, exp)), f"{nm} {got}!={exp}"
            wb.Save()
            print(f"applied+saved {bk}")
        finally:
            try: wb.Close(SaveChanges=False)
            except Exception as ex:
                if "0xE0000002" not in str(ex) and "-2147418111" not in str(ex): raise
                print(f"  close transient ({bk}) - save done")
except Exception:
    traceback.print_exc(); sys.exit(1)
finally:
    if xl is not None:
        try: xl.Quit()
        except Exception: pass
        xl = None
    pythoncom.CoUninitialize()
print("PHASE_A_DONE")
