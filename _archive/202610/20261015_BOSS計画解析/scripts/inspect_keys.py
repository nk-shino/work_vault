# -*- coding: utf-8 -*-
"""表領域の粒度・キー検証: BOSS・過去データ・サイクルタイム・組取り数・グループ等"""
import zipfile, sys, io, re, json
from xml.etree import ElementTree as ET
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
SRC = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\TOOL改修問題(BOSS)\BOSS計画.xlsm"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
z = zipfile.ZipFile(SRC)

ss = []
sst = ET.fromstring(z.read("xl/sharedStrings.xml"))
for si in sst:
    ss.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))

def col_idx(s):
    n = 0
    for ch in s: n = n * 26 + (ord(ch) - 64)
    return n

def load_rows(idx):
    """yield list of raw values per row (1-based cols)."""
    ws = ET.fromstring(z.read(f"xl/worksheets/sheet{idx}.xml"))
    rows = {}
    for row in ws.iter("{%s}row" % NS["m"]):
        r = int(row.get("r"))
        d = {}
        for c in row:
            m = re.match(r"([A-Z]+)", c.get("r"))
            col = col_idx(m.group(1))
            v = c.find("m:v", NS); is_el = c.find("m:is", NS)
            val = None
            if v is not None:
                val = ss[int(v.text)] if c.get("t") == "s" else v.text
            elif is_el is not None:
                val = "".join(x.text or "" for x in is_el.iter("{%s}t" % NS["m"]))
            d[col] = val
        rows[r] = d
    return rows

def num(v):
    if v is None: return None
    try: return float(v)
    except: return None

# ===== BOSS sheet14 =====
print("=== BOSS (sheet14) ===")
rows = load_rows(14)
n = max(rows)
print("data rows:", n - 1)
# キー列A=指図, B=品目, D=指図タイプ, N=基準開始日
orders = Counter(); empty_a = 0
types = Counter()
plants = Counter()
units = Counter()
qty_nonnum = 0
for r in range(2, n + 1):
    a = rows.get(r, {}).get(1)
    if a is None or a == "": empty_a += 1
    orders[a] += 1
    types[rows.get(r, {}).get(4)] += 1
    plants[rows.get(r, {}).get(7)] += 1
    units[rows.get(r, {}).get(13)] += 1
    if num(rows.get(r, {}).get(12)) is None: qty_nonnum += 1
dups = {k: v for k, v in orders.items() if v > 1}
print(f"指図(列A)重複: {len(dups)}件 (例: {dict(list(dups.items())[:5])})")
print(f"指図空欄: {empty_a}")
print(f"指図タイプ分布: {dict(types.most_common(12))}")
print(f"プラント分布: {dict(plants.most_common(5))}")
print(f"単位分布: {dict(units.most_common(5))}")
print(f"目標数量が数値でない: {qty_nonnum}")
# N列 日付範囲
dn = [num(rows.get(r, {}).get(14)) for r in range(2, n + 1)]
dn = [x for x in dn if x]
print(f"基準開始日 min={min(dn):.0f} max={max(dn):.0f} count={len(dn)}")
import datetime
print(f"  -> {datetime.date(1899,12,30) + datetime.timedelta(days=min(dn))} ～ {datetime.date(1899,12,30) + datetime.timedelta(days=max(dn))}")
# ZP21系の割合
zp21 = sum(1 for r in range(2, n+1) if rows.get(r, {}).get(4) == "ZP21")
print(f"ZP21(カスタム追加タイプ): {zp21}")

# ===== 過去データ sheet2 =====
print("\n=== 過去データ (sheet2) ===")
rows2 = load_rows(2)
n2 = max(rows2)
print("rows:", n2)
dates = [num(rows2[r].get(1)) for r in range(2, n2 + 1) if rows2.get(r, {}).get(1)]
dates = [x for x in dates if x]
print(f"日付列: {len(dates)}件, min={datetime.date(1899,12,30)+datetime.timedelta(days=min(dates))} max={datetime.date(1899,12,30)+datetime.timedelta(days=max(dates))}")

# ===== サイクルタイム sheet18 =====
print("\n=== サイクルタイム (sheet18) ===")
rows18 = load_rows(18)
n18 = max(rows18)
ids = Counter()
ct_missing = 0
for r in range(3, n18 + 1):  # 2行目は項目名?
    a = rows18.get(r, {}).get(1)
    if a: ids[a] += 1
d18 = {k: v for k, v in ids.items() if v > 1}
print(f"rows={n18}, typeID重複={len(d18)} (例: {dict(list(d18.items())[:5])})")
print(f"r2: {rows18.get(2)}")
print(f"r3: {rows18.get(3)}")

# ===== 組取り数 sheet19 =====
print("\n=== 組取り数 (sheet19) ===")
rows19 = load_rows(19)
n19 = max(rows19)
k = Counter()
for r in range(2, n19 + 1):
    a = rows19.get(r, {}).get(1)
    if a: k[a] += 1
d19 = {kk: v for kk, v in k.items() if v > 1}
print(f"rows={n19}, typeID重複={len(d19)}")
print(f"r2: {rows19.get(2)}, r3: {rows19.get(3)}")

# ===== グループ sheet17 =====
print("\n=== グループ (sheet17) ===")
rows17 = load_rows(17)
n17 = max(rows17)
gdup = Counter()
b2g = {}
for r in range(2, n17 + 1):
    a = rows17.get(r, {}).get(1)
    b = rows17.get(r, {}).get(2)
    if a: gdup[a] += 1
print(f"rows={n17}, グループ名重複: {len([1 for v in gdup.values() if v>1])}")
# 同一品目が複数グループ?
bg = Counter()
for r in range(2, n17 + 1):
    b = rows17.get(r, {}).get(2)
    if b: bg[b] += 1
db = {kk: v for kk, v in bg.items() if v > 1}
print(f"同一品目が複数行: {db}")
print(f"r2: {rows17.get(2)}")

# ===== 準備工数 sheet4: XLOOKUP構造 =====
print("\n=== 準備工数 (sheet4) r1-3 ===")
rows4 = load_rows(4)
for r in [1,2,3,1555,1556]:
    if r in rows4:
        d = rows4[r]
        line = {k: v for k, v in sorted(d.items())[:12] if v is not None}
        print(f"r{r}: {line}")

# ===== 祝日 sheet15 =====
print("\n=== 祝日 (sheet15) ===")
rows15 = load_rows(15)
vals = [num(rows15[r].get(1)) for r in rows15 if num(rows15[r].get(1))]
print(f"件数={len(vals)} min={datetime.date(1899,12,30)+datetime.timedelta(days=min(vals))} max={datetime.date(1899,12,30)+datetime.timedelta(days=max(vals))}")
d15 = [v for v in vals if v < 44000 or v > 55000]
print(f"範囲外(2020年以前/2030年以降): {len(d15)}")

# ===== メール sheet16 件名・宛先 =====
print("\n=== メール (sheet16) r1-10 ===")
rows16 = load_rows(16)
for r in range(1, 11):
    if r in rows16:
        d = rows16[r]
        line = {k: (v[:60] if isinstance(v, str) else v) for k, v in sorted(d.items()) if v is not None}
        print(f"r{r}: {line}")
