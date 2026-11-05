import sys, io, os, shutil, traceback
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import pythoncom, win32com.client
BASE = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\corr23"
SRC = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
DST = os.path.join(BASE, "refix2")
BOOKS = {"pana": ("Pana-CIM管理手順書案_未承認.xlsx", "相関図②", "相関図③"),
         "lnb":  ("LNB管理手順書案_未承認.xlsx", "相関図②", "相関図③")}
WIDTHS = {"g2_e_e01_l": 112.0, "g2_e_e02_l": 120.0, "g2_e_e08_l": 134.0, "g2_e_e17_l": 168.0}
E03 = {"g3_e_e03_s0": ("Width", 33.0), "g3_e_e03_s1": ("Left", 268.0),
       "g3_e_e03_s2": ("Left", 268.0), "g3_e_e03_s2b": ("Width", 468.0),
       "g3_e_e03_s3": ("Left", 736.0)}
for bk, (fn, s2, s3) in BOOKS.items():
    shutil.copy2(os.path.join(SRC, fn), os.path.join(DST, fn))
print("copies done")

def child(grp, nm):
    return grp.GroupItems(nm)

pythoncom.CoInitialize()
xl = None
try:
    xl = win32com.client.DispatchEx("Excel.Application")
    xl.Visible = False; xl.DisplayAlerts = False
    for bk, (fn, s2name, s3name) in BOOKS.items():
        p = os.path.join(DST, fn)
        wb = xl.Workbooks.Open(p, ReadOnly=False)
        try:
            try: wb.AutoSaveOn = False
            except Exception: pass  # ローカルファイルはAutoSave非対応
            ws2 = wb.Worksheets(s2name); ws3 = wb.Worksheets(s3name)
            # 1) フォント記録(退行4ラベル)
            for nm in WIDTHS:
                sh = ws2.Shapes(nm)
                f = sh.TextFrame2.TextRange.Font
                print(f"  font {bk} {nm}: name={f.Name} far={f.NameFarEast} size={f.Size} bold={f.Bold}")
            # 2) ラベル幅
            for nm, w in WIDTHS.items():
                ws2.Shapes(nm).Width = w
            # 3) e03 経路
            grp = ws3.Shapes("g3_e_e03")
            child(grp, "g3_e_e03_s0").Width = 33.0
            child(grp, "g3_e_e03_s1").Left = 268.0
            s2c = child(grp, "g3_e_e03_s2"); s2c.Left = 268.0; s2c.Width = 468.0
            child(grp, "g3_e_e03_s3").Left = 736.0
            # 4) 設定後検証
            for nm, w in WIDTHS.items():
                got = ws2.Shapes(nm).Width
                assert abs(got - w) < 0.01, f"{nm} width {got} != {w}"
            for nm, want in (("g3_e_e03_s0", (235.0, None, 33.0, None)),
                             ("g3_e_e03_s1", (268.0, None, 0.0, None)),
                             ("g3_e_e03_s2", (268.0, 485.0, 468.0, 0.0)),
                             ("g3_e_e03_s3", (736.0, 205.0, 0.0, 280.0))):
                c = child(grp, nm)
                l, t, w, h = (round(c.Left, 1), round(c.Top, 1), round(c.Width, 1), round(c.Height, 1))
                exp = want
                ok = ((exp[0] is None or abs(l-exp[0]) < 0.05) and (exp[1] is None or abs(t-exp[1]) < 0.05)
                      and (exp[2] is None or abs(w-exp[2]) < 0.05) and (exp[3] is None or abs(h-exp[3]) < 0.05))
                print(f"  e03 {nm}: L{l} T{t} W{w} H{h} {'OK' if ok else 'MISMATCH exp='+str(exp)}")
                if not ok: raise RuntimeError("e03 set mismatch " + nm)
            wb.Save()
            print(f"  saved {bk}")
        finally:
            try: wb.Close(SaveChanges=False)
            except Exception as ex:
                if "0xE0000002" not in str(ex) and "-2147418111" not in str(ex): raise
                print(f"  close transient ({bk}) - save already done")
except Exception:
    traceback.print_exc(); sys.exit(1)
finally:
    if xl is not None:
        try: xl.Quit()
        except Exception: pass
        xl = None
    pythoncom.CoUninitialize()
print("PHASE_T_DONE")
