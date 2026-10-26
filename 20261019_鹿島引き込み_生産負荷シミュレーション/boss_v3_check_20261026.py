# -*- coding: utf-8 -*-
"""share上のBOSS計画 version 3 (1).xlsm の内容確認(読み取り専用・無変更)"""
import openpyxl, sys
sys.stdout.reconfigure(encoding='utf-8')

P = r"\\nksv569.ad.nkc.co.jp\Share\mnt\DGS-SV\★個人フォルダ\篠原\サイクルタイムx1.3\BOSS計画_鹿島4(半製品が鹿島除く)+NKV_1 (version 3) (1).xlsm"
wb = openpyxl.load_workbook(P, data_only=True, read_only=True)
print("シート一覧(", len(wb.sheetnames), "枚):", wb.sheetnames)
print("鹿島_除外シートの有無:", '鹿島_除外' in wb.sheetnames)

CAL = {6: 'フリー', 7: 'L1試作', 8: 'NKV', 9: 'NKV-440', 10: 'NKV-550', 11: 'BSM-1700',
       12: 'L1停止時間', 14: 'TEC-5600(L2)', 15: 'TEC-1000(L2)', 16: '送信機_L2', 17: 'L2停止時間',
       19: 'AED(L3)', 20: 'BSM-1700L3', 21: 'L3停止時間'}
cnt = {v: 0 for v in CAL.values()}
mset = {v: set() for v in CAL.values()}
rows = 0
ws = wb['計算']
for row in ws.iter_rows(min_row=2, max_col=21, values_only=True):
    d = row[0]
    if not hasattr(d, 'year'):
        continue
    rows += 1
    vals = tuple(row) + (None,) * 21
    for c, name in CAL.items():
        v = vals[c - 1]
        if isinstance(v, (int, float)) and v != 0:
            cnt[name] += 1
            mset[name].add(d.month)
print(f"計算シート: 日付行{rows}行")
for name in CAL.values():
    flag = "有" if cnt[name] else "無"
    print(f"  {name}: {flag} (非空{cnt[name]}セル・月{sorted(mset[name]) if mset[name] else '-'}回目)")
wb.close()
