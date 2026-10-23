# -*- coding: utf-8 -*-
"""図形ジオメトリ監査: 表紙・異常時の対応の全図形について
(1) bbox同士の重なり(意図的なペアは除外) (2) UsedRange外への逸脱 (3) 文字セルとの重なり を検査"""
import sys, io, time, warnings
warnings.filterwarnings("ignore")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pythoncom, win32com.client

F = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\Pana-CIM管理手順書案_未承認.xlsx"
# 意図的な重なり: ダイヤとその重ねテキスト(実名は自動採番のTextBox)
# 表紙の変更記号バッジⒾ(Freeform=三角形枠+TextBox=文字)は原版10-15と同一座標の意図的構造
WHITELIST = {("fc_dia", "fc_dia_txt"), ("fc_dia", "TextBox 72"),
             ("Freeform 104", "Text Box 105")}

def rect(sh):
    l, t = sh.Left, sh.Top
    return (l, t, l + sh.Width, t + sh.Height)

def inter(a, b):
    x = min(a[2], b[2]) - max(a[0], b[0])
    y = min(a[3], b[3]) - max(a[1], b[1])
    return x * y if (x > 0 and y > 0) else 0.0

def audit(ws, cell_overlap=False):
    print(f"=== {ws.Name} ===")
    shapes = []
    for sh in ws.Shapes:
        r = rect(sh)
        txt = ""
        try:
            txt = sh.TextFrame2.TextRange.Text[:12].replace("\r", "/").replace("\n", "/")
        except Exception:
            pass
        shapes.append((sh.Name, sh.Type, r, txt))
    print(f"shapes: {len(shapes)}")
    ur = ws.UsedRange
    ub = (ur.Left, ur.Top, ur.Left + ur.Width, ur.Top + ur.Height)
    print(f"used range bbox: L={ub[0]:.0f} T={ub[1]:.0f} R={ub[2]:.0f} B={ub[3]:.0f}")
    bad = 0
    # (1) 図形同士の重なり
    for i in range(len(shapes)):
        for j in range(i + 1, len(shapes)):
            n1, _, r1, _ = shapes[i]
            n2, _, r2, _ = shapes[j]
            a = inter(r1, r2)
            if a > 1.0 and (n1, n2) not in WHITELIST and (n2, n1) not in WHITELIST:
                print(f"  [重なり] {n1} × {n2} area={a:.0f}pt2")
                bad += 1
    # (2) UsedRange 外への逸脱
    for n, _, r, _ in shapes:
        if r[0] < ub[0] - 2 or r[1] < ub[1] - 2 or r[2] > ub[2] + 2 or r[3] > ub[3] + 2:
            print(f"  [範囲外] {n} bbox=({r[0]:.0f},{r[1]:.0f},{r[2]:.0f},{r[3]:.0f})")
            bad += 1
    # (3) 文字セルとの重なり(指定時のみ)
    if cell_overlap:
        nc = 0
        for row in ws.UsedRange.Rows:
            for c in row.Cells:
                v = c.Value
                if v is None or not str(v).strip():
                    continue
                cb = (c.Left, c.Top, c.Left + c.MergeArea.Width, c.Top + c.MergeArea.Height)
                for n, _, r, _ in shapes:
                    a = inter(cb, r)
                    if a > 4.0:
                        print(f"  [セル重なり] 図形 {n} × {c.Address} 「{str(v)[:15]}」 area={a:.0f}pt2")
                        nc += 1
        if nc == 0:
            print("  セル文字との重なり: なし")
    if bad == 0:
        print("  図形同士の重なり・範囲外: なし")
    return bad

def run_once():
    pythoncom.CoInitialize()
    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    try:
        wb = excel.Workbooks.Open(F, False, True)  # ReadOnly
        try:
            b1 = audit(wb.Worksheets("表紙"), cell_overlap=False)
            b2 = audit(wb.Worksheets("異常時の対応"), cell_overlap=True)
            print("RESULT:", "OK" if (b1 + b2) == 0 else f"NG({b1+b2})")
        finally:
            wb.Close(SaveChanges=False)
    finally:
        excel.Quit()
        pythoncom.CoUninitialize()

for attempt in range(1, 6):
    try:
        run_once()
        break
    except Exception as e:
        print(f"retry {attempt}: {e}")
        time.sleep(1.5)
else:
    sys.exit(1)
