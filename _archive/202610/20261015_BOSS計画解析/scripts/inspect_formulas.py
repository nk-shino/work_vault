# -*- coding: utf-8 -*-
"""数式の詳細: 準備工数のXLOOKUP・#N/A状況・メールシートのINDEX/MATCH・計算依存"""
import zipfile, sys, io, re
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

def load_rows_with_formula(idx):
    ws = ET.fromstring(z.read(f"xl/worksheets/sheet{idx}.xml"))
    rows = {}
    for row in ws.iter("{%s}row" % NS["m"]):
        r = int(row.get("r"))
        d = {}
        for c in row:
            m = re.match(r"([A-Z]+)", c.get("r"))
            col = col_idx(m.group(1))
            v = c.find("m:v", NS); is_el = c.find("m:is", NS); f = c.find("m:f", NS)
            val = None
            if v is not None:
                val = ss[int(v.text)] if c.get("t") == "s" else v.text
            elif is_el is not None:
                val = "".join(x.text or "" for x in is_el.iter("{%s}t" % NS["m"]))
            d[col] = (val, f.text if f is not None and f.text else None)
        rows[r] = d
    return rows

# 準備工数: 数式サンプルとエラー値
print("=== 準備工数 sheet4 ===")
rows4 = load_rows_with_formula(4)
n4 = max(rows4)
err_count = Counter()
na_rows = []
for r in range(3, n4 + 1):
    has_err = False
    for col, (v, f) in rows4.get(r, {}).items():
        if v in ("#N/A", "#REF!", "#VALUE!", "#DIV/0!"):
            err_count[v] += 1
            has_err = True
    if has_err: na_rows.append(r)
print(f"rows={n4}, エラー値: {dict(err_count)}, エラー行数={len(na_rows)}")
# 数式サンプル
for r in [3, 4, 100, 1556]:
    if r in rows4:
        print(f"--- r{r} ---")
        for col, (v, f) in sorted(rows4[r].items()):
            if f: print(f"  col{col}: v={v!r} f={f[:150]!r}")

# 最終行の値を確認（XLOOKUP先がBOSS更新で壊れていないか）
lastv = rows4.get(n4, {}).get(1, (None, None))[0]
print(f"最終行r{n4}の日付: {lastv}")

# メールシート: 数式サンプル
print("\n=== メール sheet16 ===")
rows16 = load_rows_with_formula(16)
for r in range(1, 12):
    if r in rows16:
        for col, (v, f) in sorted(rows16[r].items()):
            if f: print(f"  r{r}c{col}: v={v!r} f={f[:200]!r}")

# サイクルタイム: XLOOKUP式サンプル
print("\n=== サイクルタイム sheet18 ===")
rows18 = load_rows_with_formula(18)
for r in [2, 3, 971, 972, 973]:
    if r in rows18:
        for col, (v, f) in sorted(rows18[r].items()):
            if f: print(f"  r{r}c{col}: v={v!r} f={f[:200]!r}")

# 試作 E列 XLOOKUP -1モード
print("\n=== 試作 sheet9 E列数式 ===")
rows9 = load_rows_with_formula(9)
for r in [2, 3]:
    for col, (v, f) in sorted(rows9[r].items()):
        if f: print(f"  r{r}c{col}: v={v!r} f={f[:200]!r}")
