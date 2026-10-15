# -*- coding: utf-8 -*-
"""BOSSシート指図タイプとコード条件の照合: reg.Pattern ^(LA|ZP1\d|ZP2\d)$ 対象外の行"""
import zipfile, sys, io, re, datetime
from xml.etree import ElementTree as ET
from collections import Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
SRC = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\TOOL改修問題\BOSS計画.xlsm"
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

rows = load_rows(14)
n = max(rows)
pat = re.compile(r"^(LA|ZP1\d|ZP2\d)$")
keep = Counter()
drop = Counter()
kv = 0
for r in range(2, n + 1):
    t = rows[r].get(4) or ""
    h = rows[r].get(2) or ""
    if pat.match(t) and not h.startswith("KV"):
        keep[t] += 1
    else:
        drop[(t, h[:3])] += 1
        if h.startswith("KV"): kv += 1
print("保持される行:", dict(keep))
print("削除される行タイプ×品目頭3字:", dict(drop.most_common(10)))
print("合計:", sum(keep.values()) + sum(drop.values()), "削除対象:", sum(drop.values()), f"(KVを含む: {kv})")

# ZP21の品目多様性
zp21_hinmoku = set(rows[r].get(2) for r in range(2, n + 1) if rows[r].get(4) == "ZP21")
print(f"ZP21ユニーク品目数: {len(zp21_hinmoku)}")
# ZP21の指図番号は21xxxxxxx → Customマクロ由来か?
# カスタム設定のR列(指図)と照合
rows8 = load_rows(8)
custom_orders = set()
for r in range(2, max(rows8) + 1):
    v = rows8.get(r, {}).get(18)
    if v: custom_orders.add(str(v))
boss_orders = set(str(rows[r].get(1)) for r in range(2, n + 1))
inter = custom_orders & boss_orders
print(f"カスタム設定R列の指図 {len(custom_orders)}件のうちBOSSに存在: {len(inter)}")
print(f"例: {sorted(inter)[:5]}")
