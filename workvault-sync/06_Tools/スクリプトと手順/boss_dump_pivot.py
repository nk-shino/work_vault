# -*- coding: utf-8 -*-
"""SMT鹿島_BOSS.xlsx に実ピボットテーブルを作成する。"""
import datetime as _dt
import pandas as pd
import win32com.client as win32

SRC = r"C:\Users\ss80751\Downloads\SMT鹿島_BOSS.xlsx"
P_START = pd.Timestamp("2026-04-01")
P_END = pd.Timestamp("2026-09-30")
TYPES = ("ZP11", "ZP21")

df = pd.read_excel(SRC, sheet_name="結果")
st = df["システムステータス"].fillna("").astype(str).str.upper()
mask = (
    df["指図タイプ"].isin(TYPES)
    & ~st.str.contains("TECO")
    & (df["基準開始日"] >= P_START)
    & (df["基準開始日"] <= P_END)
)
sub = df.loc[mask].copy()
months = sub["基準開始日"].dt.strftime("%Y-%m")

header = list(df.columns) + ["月"]
rows = []
for r, m in zip(sub.itertuples(index=False, name=None), months):
    vals = []
    for v in r:
        if isinstance(v, pd.Timestamp):
            vals.append(v.to_pydatetime().replace(tzinfo=_dt.timezone.utc))
        elif pd.isna(v):
            vals.append("")
        else:
            vals.append(v)
    vals.append(m)
    rows.append(tuple(vals))

n = len(rows)
ncol = len(header)
print("抽出行数:", n)

excel = win32.gencache.EnsureDispatch("Excel.Application")
excel.Visible = False
excel.DisplayAlerts = False
excel.ScreenUpdating = False
wb = None
try:
    wb = excel.Workbooks.Open(SRC)

    for name in ("ピボット用データ", "ピボットテーブル"):
        for sh in list(wb.Worksheets):
            if sh.Name == name:
                sh.Delete()
                break

    ws_src = wb.Worksheets("結果")
    stg = wb.Worksheets.Add()
    stg.Move(After=ws_src)
    stg.Name = "ピボット用データ"

    stg.Range(stg.Cells(1, 1), stg.Cells(1, ncol)).Value = header
    stg.Range(stg.Cells(1, 1), stg.Cells(1, ncol)).Font.Bold = True
    stg.Columns("N:O").NumberFormat = "yyyy-mm-dd"
    stg.Columns("P").NumberFormat = "@"
    stg.Range(stg.Cells(2, 1), stg.Cells(n + 1, ncol)).Value = rows
    stg.Columns.AutoFit()
    stg.Activate()
    excel.ActiveWindow.SplitRow = 1
    excel.ActiveWindow.FreezePanes = True
    try:
        stg.Range(f"A1:P{n+1}").AutoFilter()
    except Exception:
        pass

    pv = wb.Worksheets.Add()
    pv.Move(After=stg)
    pv.Name = "ピボットテーブル"

    src_range = stg.Range(stg.Cells(1, 1), stg.Cells(n + 1, ncol))
    cache = wb.PivotCaches().Create(SourceType=1, SourceData=src_range)

    def make_pivot(table_name, dest, row_fields, col_fields=None):
        pt = cache.CreatePivotTable(TableDestination=dest, TableName=table_name)
        for f in row_fields:
            pt.PivotFields(f).Orientation = 1  # xlRowField
        for f in col_fields or []:
            pt.PivotFields(f).Orientation = 2  # xlColumnField
        data_field = pt.AddDataField(pt.PivotFields("目標数量"), "目標数量 合計", -4157)  # xlSum
        data_field.NumberFormat = "#,##0"
        pt.RowGrand = True
        pt.ColumnGrand = True
        pt.TableStyle2 = "PivotStyleMedium9"
        return pt

    def title(cell, text):
        c = pv.Range(cell)
        c.Value = text
        c.Font.Bold = True
        c.Font.Size = 12

    title("A1", "品目別合計(目標数量)")
    make_pivot("PT_品目別", pv.Range("A3"), ["品目"])

    title("D1", "製造責任者別合計(目標数量)")
    make_pivot("PT_製造責任者別", pv.Range("D3"), ["製造責任者"])

    title("G1", "月別合計(目標数量)")
    make_pivot("PT_月別", pv.Range("G3"), ["月"])

    title("J1", "品目×月 クロス集計(目標数量)")
    make_pivot("PT_品目x月", pv.Range("J3"), ["品目"], ["月"])

    note = pv.Range("A236")
    note.Value = (
        "※ソース:ピボット用データシート(結果シートからの抽出値)。"
        "条件:指図タイプ=ZP11/ZP21、システムステータスにTECOを含まない、"
        "基準開始日が2026-04-01〜2026-09-30(76期)。抽出日:2026-10-21。"
        "結果シートを更新した場合は再抽出が必要。"
    )
    note.Font.Size = 9

    pv.Columns.AutoFit()
    pv.Range("A1").Select()

    wb.Save()
    print("保存完了")
finally:
    if wb is not None:
        wb.Close(SaveChanges=False)
    excel.ScreenUpdating = True
    excel.Quit()
