# -*- coding: utf-8 -*-
"""実装状況表2.xlsxの開閉確認・グラフ・画像・メンテナンス記録・計算シート列の構造"""
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

# グラフの配置先
print("=== グラフ配置 ===")
RNS = "http://schemas.openxmlformats.org/package/2006/relationships"
for i in range(1, 21):
    rels_name = f"xl/worksheets/_rels/sheet{i}.xml.rels"
    try:
        rels = ET.fromstring(z.read(rels_name))
        charts = [r.get("Target") for r in rels if "chart" in r.get("Type", "")]
        draws = [r.get("Target") for r in rels if "drawing" in r.get("Type", "")]
        qts = [r.get("Target") for r in rels if "queryTable" in r.get("Type", "")]
        if charts or draws or qts:
            print(f"sheet{i}: charts={charts} drawings={draws} queryTables={qts}")
    except KeyError:
        pass

# drawingの宛先(ボタン等) - drawing8 が 61KB
print("\n=== drawing一覧とshape数 ===")
for i in range(1, 10):
    try:
        d = z.read(f"xl/drawings/drawing{i}.xml").decode("utf-8")
        nshapes = d.count("<xdr:sp ")
        npic = d.count("<xdr:pic>")
        ngraphic = d.count("<xdr:graphicFrame")
        anchors = re.findall(r'<xdr:from><xdr:col>(\d+)</xdr:col>', d)
        print(f"drawing{i}: shapes={nshapes} pics={npic} charts={ngraphic} cols={anchors[:10]}")
    except KeyError:
        pass

# ボタンのマクロ割当 (legacy VML / form controls)
print("\n=== VML(フォームコントロール)のマクロ割当 ===")
for name in z.namelist():
    if name.endswith(".vml"):
        data = z.read(name).decode("utf-8", "replace")
        macros = re.findall(r'macro="([^"]+)"', data)
        print(f"{name}: {macros}")

# 計算シート(sheet6)の全列見出しとサンプル
print("\n=== 計算 sheet6 構造 ===")
def col_idx(s):
    n = 0
    for ch in s: n = n * 26 + (ord(ch) - 64)
    return n
ws = ET.fromstring(z.read("xl/worksheets/sheet6.xml"))
rows = {}
for row in ws.iter("{%s}row" % NS["m"]):
    r = int(row.get("r"))
    d = {}
    for c in row:
        m = re.match(r"([A-Z]+)", c.get("r"))
        col = col_idx(m.group(1))
        v = c.find("m:v", NS)
        val = None
        if v is not None:
            val = ss[int(v.text)] if c.get("t") == "s" else v.text
        d[col] = val
    rows[r] = d
n6 = max(rows)
print(f"rows={n6}")
for col in range(1, 22):
    h = rows.get(1, {}).get(col)
    sample = rows.get(2, {}).get(col)
    filled = sum(1 for r in range(2, n6+1) if rows.get(r, {}).get(col) not in (None, ""))
    print(f"col{col}: {h!r} sample={sample!r} filled={filled}")
# 日付範囲
import datetime
epoch = datetime.date(1899,12,30)
dts = [num for r in range(2, n6+1) if (num:=_num(rows.get(r,{}).get(1)))] if False else []
def _num(v):
    try: return float(v)
    except: return None
dts = [float(rows[r][1]) for r in range(2, n6+1) if rows.get(r, {}).get(1) and _num(rows[r][1])]
print(f"日付: {epoch+datetime.timedelta(days=min(dts))} ～ {epoch+datetime.timedelta(days=max(dts))} ({len(dts)}件)")

# 過去データと計算の行数比較
print("\n過去データrows=1020 / 計算rows=183")

# mail シートの宛先詳細（秘匿マスク確認用）
rows16xml = ET.fromstring(z.read("xl/worksheets/sheet16.xml"))
# r8c2 完全
for row in rows16xml.iter("{%s}row" % NS["m"]):
    if row.get("r") == "8":
        for c in row:
            m = re.match(r"([A-Z]+)", c.get("r"))
            if m.group(1) in ("A","B","C","D"):
                v = c.find("m:v", NS)
                if v is not None:
                    val = ss[int(v.text)] if c.get("t") == "s" else v.text
                    print(f"mail r8 {m.group(1)}: {val[:120]}")
