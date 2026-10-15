# -*- coding: utf-8 -*-
"""BOSS計画.xlsm 深掘り: keyセル・サンプル行・特殊領域・接続元ファイル確認"""
import zipfile, sys, io, re
from xml.etree import ElementTree as ET

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
SRC = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\TOOL改修問題\BOSS計画.xlsm"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
z = zipfile.ZipFile(SRC)

ss = []
sst = ET.fromstring(z.read("xl/sharedStrings.xml"))
for si in sst:
    ss.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))

def col_letters_to_idx(s):
    n = 0
    for ch in s: n = n * 26 + (ord(ch) - 64)
    return n

def get_cell(ws_cache, ref):
    """ws_cache: dict row -> dict col->(t,v,f)"""
    m = re.match(r"([A-Z]+)(\d+)", ref)
    row = int(m.group(2)); col = col_letters_to_idx(m.group(1))
    cell = ws_cache.get(row, {}).get(col)
    return cell

def load_sheet(idx, max_rows=None):
    ws = ET.fromstring(z.read(f"xl/worksheets/sheet{idx}.xml"))
    cache = {}
    for row in ws.iter("{%s}row" % NS["m"]):
        r = int(row.get("r"))
        if max_rows and r > max_rows: continue
        d = {}
        for c in row:
            m = re.match(r"([A-Z]+)", c.get("r"))
            col = col_letters_to_idx(m.group(1))
            v = c.find("m:v", NS); is_el = c.find("m:is", NS); f = c.find("m:f", NS)
            val = None
            if v is not None:
                val = ss[int(v.text)] if c.get("t") == "s" else v.text
            elif is_el is not None:
                val = "".join(x.text or "" for x in is_el.iter("{%s}t" % NS["m"]))
            d[col] = (c.get("t"), val, f.text if f is not None and f.text else None)
        cache[r] = d
    return cache

# 容量計算(5) ボタン領域・パラメータ
print("=== 容量計算 sheet5 全セル (値/数式) ===")
c5 = load_sheet(5)
for r in sorted(c5):
    for col in sorted(c5[r]):
        t, v, f = c5[r][col]
        if v is not None or f:
            print(f"  {chr(64+col) if col<=26 else 'A'+chr(64+col-26)}{r}: v={v!r} f={f!r}")

# カスタム設定 sheet8 の領域
print("\n=== カスタム設定 sheet8 (行2-10サンプル + R/S列) ===")
c8 = load_sheet(8, max_rows=12)
for r in sorted(c8):
    line = []
    for col in sorted(c8[r]):
        t, v, f = c8[r][col]
        if v is not None:
            line.append(f"{col}:{v!r}")
    if line: print(f"  r{r}: {line}")

# 試作 sheet9 全行
print("\n=== 試作 sheet9 全行 ===")
c9 = load_sheet(9)
for r in sorted(c9):
    line = []
    for col in sorted(c9[r]):
        t, v, f = c9[r][col]
        if v is not None:
            line.append(f"{col}:{v!r}" + (f" f={f!r}" if f else ""))
    if line: print(f"  r{r}: {line}")

# Param sheet11
print("\n=== Param sheet11 ===")
c11 = load_sheet(11)
for r in sorted(c11):
    for col in sorted(c11[r]):
        t, v, f = c11[r][col]
        print(f"  r{r}c{col}: v={v!r}")

# メンテナンスメモ sheet1 全行
print("\n=== メンテナンスメモ sheet1 ===")
c1 = load_sheet(1)
for r in sorted(c1):
    line = []
    for col in sorted(c1[r]):
        t, v, f = c1[r][col]
        if v is not None: line.append(f"{col}:{v!r}")
    if line: print(f"  r{r}: {line}")

# 列設定 sheet20 全行
print("\n=== 列設定 sheet20 ===")
c20 = load_sheet(20)
for r in sorted(c20):
    line = []
    for col in sorted(c20[r]):
        t, v, f = c20[r][col]
        if v is not None: line.append(f"{col}:{v!r}")
    if line: print(f"  r{r}: {line}")

# BOSS sheet14 サンプル行1-3, 最終行
print("\n=== BOSS sheet14 r1-3, r10170-10172 ===")
c14 = load_sheet(14)
for r in [1,2,3,10170,10171,10172]:
    if r in c14:
        line = []
        for col in sorted(c14[r]):
            t, v, f = c14[r][col]
            line.append(f"{col}:{v!r}")
        print(f"  r{r}: {line}")

# connections元ファイル
print("\n=== connections.xml 詳細 ===")
print(z.read("xl/connections.xml").decode("utf-8")[:1600])
