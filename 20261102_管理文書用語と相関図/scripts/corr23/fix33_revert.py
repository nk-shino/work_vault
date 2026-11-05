import sys, io, os, traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import pythoncom, win32com.client
VAULT = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
BOOKS = {"pana": "Pana-CIM管理手順書案_未承認.xlsx", "lnb": "LNB管理手順書案_未承認.xlsx"}
pythoncom.CoInitialize()
xl = None
try:
    xl = win32com.client.DispatchEx("Excel.Application")
    xl.Visible = False; xl.DisplayAlerts = False
    for bk, fn in BOOKS.items():
        wb = xl.Workbooks.Open(os.path.join(VAULT, fn), ReadOnly=False)
        try:
            try: wb.AutoSaveOn = False
            except Exception: pass
            ws3 = wb.Worksheets("相関図③")
            grp = ws3.Shapes("g3_e_e03")
            # s1後退に伴う経路戻し(s3=736のF2修正は保持)
            grp.GroupItems("g3_e_e03_s0").Width = 27.0
            grp.GroupItems("g3_e_e03_s1").Left = 262.0
            s2c = grp.GroupItems("g3_e_e03_s2"); s2c.Left = 262.0; s2c.Width = 472.0
            assert abs(grp.GroupItems("g3_e_e03_s3").Left - 736.0) < 0.01
            exp = (("g3_e_e03_s0",(235.0,356.0,27.0,0.0)), ("g3_e_e03_s1",(262.0,356.0,0.0,129.0)),
                   ("g3_e_e03_s2",(262.0,485.0,472.0,0.0)), ("g3_e_e03_s3",(736.0,205.0,0.0,280.0)))
            for nm, e in exp:
                c = grp.GroupItems(nm)
                got = (round(c.Left,1), round(c.Top,1), round(c.Width,1), round(c.Height,1))
                assert all(abs(a-b) < 0.05 for a,b in zip(got, e)), f"{nm} {got}!={e}"
            wb.Save()
            print(f"reverted+saved {bk}")
        finally:
            try: wb.Close(SaveChanges=False)
            except Exception as ex:
                s = str(ex).lower()
                if "0xe0000002" not in s and "-2147418111" not in s: raise
                print(f"  close transient ({bk}) - save done")
except Exception:
    traceback.print_exc(); sys.exit(1)
finally:
    if xl is not None:
        try: xl.Quit()
        except Exception: pass
        xl = None
    pythoncom.CoUninitialize()
print("REVERT_DONE")
