# -*- coding: utf-8 -*-
"""ver別簡易比較の「総計」ラベルを「平均」に修正(案A・定義=月別平均のまま・数式無変更)
対象: ユーザーが<前回版>シートを追加済みの現行ファイル。Phase1編集→Phase2 COM再計算→Phase3突合
"""
import openpyxl, shutil, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\boss_pivot13\比較グラフ_x1.3_share_now_20261026.xlsx"
TMP = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\boss_pivot13\比較グラフ_x1.3_平均ラベル_20261026.xlsx"
SHEET = 'ver別簡易比較'

# ---- Phase1: 編集 ----
shutil.copyfile(BASE, TMP)
wb = openpyxl.load_workbook(TMP)
ws = wb[SHEET]
target = None
for r in range(15, 35):
    if ws.cell(r, 1).value == '総計':
        target = r
        break
assert target, f"「総計」ラベル不在: A15:A35={[ws.cell(r,1).value for r in range(15,35)]}"
old = ws.cell(target, 1).value
ws.cell(target, 1).value = '平均'
print(f"Phase1: {SHEET}!A{target} 「{old}」→「平均」 (B{target}={ws.cell(target,2).value})")
wb.save(TMP)

# ---- Phase2: COM再計算+保存 ----
import win32com.client
app = win32com.client.DispatchEx("Excel.Application")
app.DisplayAlerts = False
app.Visible = False
try:
    wbx = app.Workbooks.Open(TMP)
    app.CalculateFullRebuild()
    wbx.Save()
    wbx.Close(SaveChanges=False)
    print("Phase2: COM再計算+保存 完了")
finally:
    app.Quit()

# ---- Phase3: 現行share版との突合 ----
def load(p, only):
    return openpyxl.load_workbook(p, data_only=only)
base_v, new_v = load(BASE, True), load(TMP, True)
base_f, new_f = load(BASE, False), load(TMP, False)
assert base_v.sheetnames == new_v.sheetnames, f"シート構成の変化: {base_v.sheetnames} vs {new_v.sheetnames}"
diffs = []
for sn in base_v.sheetnames:
    s1, s2 = base_v[sn], new_v[sn]
    mr, mc = max(s1.max_row, s2.max_row), max(s1.max_column, s2.max_column)
    for r in range(1, mr + 1):
        for c in range(1, mc + 1):
            a, b = s1.cell(r, c).value, s2.cell(r, c).value
            if a != b:
                diffs.append((sn, s1.cell(r, c).coordinate, a, b))
print(f"Phase3: 値差分 {len(diffs)}件")
for d in diffs[:20]:
    print("   ", d)
fdiffs = 0
fdiff_cells = set()
for sn in base_f.sheetnames:
    s1, s2 = base_f[sn], new_f[sn]
    mr, mc = max(s1.max_row, s2.max_row), max(s1.max_column, s2.max_column)
    for r in range(1, mr + 1):
        for c in range(1, mc + 1):
            if s1.cell(r, c).value != s2.cell(r, c).value:
                fdiffs += 1
                fdiff_cells.add((sn, s1.cell(r, c).coordinate))
                if fdiffs <= 10:
                    print("    式差分", sn, s1.cell(r, c).coordinate, repr(s1.cell(r, c).value), repr(s2.cell(r, c).value))
print(f"Phase3: 数式差分 {fdiffs}件")
npiv = sum(len(w._pivots) for w in new_f.worksheets)
errs = sum(1 for w in new_v.worksheets for row in w.iter_rows() for cell in row
           if isinstance(cell.value, str) and cell.value.startswith('#'))
print(f"Phase3: ピボット定義 {npiv}個 / エラー値 {errs}件")
print("\nver別簡易比較 A26:H30(現行→修正後の確認):")
for r in range(26, 31):
    a = base_v[SHEET].cell(r, 1).value
    b = new_v[SHEET].cell(r, 1).value
    b28 = new_v[SHEET].cell(r, 2).value
    print(f"  行{r}: A列 「{a}」→「{b}」 B列={b28 if r != target else '(値は同じ)'}")
ok = (len(diffs) == 1 and diffs[0][0] == SHEET and diffs[0][1] == f'A{target}'
      and diffs[0][2] == '総計' and diffs[0][3] == '平均'
      and fdiffs == 1 and fdiff_cells == {(SHEET, f'A{target}')}
      and npiv == 26 and errs == 0)
print("Phase3: 判定 =", "PASS" if ok else "NG")
sys.exit(0 if ok else 1)
