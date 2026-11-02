# -*- coding: utf-8 -*-
"""BOSS計画.xlsm シート詳細解析: 次元・見出し・サンプル・数式統計・特殊セル"""
import zipfile, json, sys, io, os, re
from xml.etree import ElementTree as ET

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SRC = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\TOOL改修問題(BOSS)\BOSS計画.xlsm"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

z = zipfile.ZipFile(SRC)

# shared strings
ss = []
sst = ET.fromstring(z.read("xl/sharedStrings.xml"))
for si in sst:
    ss.append("".join(t.text or "" for t in si.iter("{%s}t" % NS["m"])))
print(f"sharedStrings: {len(ss)}")

def col_letters_to_idx(s):
    n = 0
    for ch in s:
        n = n * 26 + (ord(ch) - 64)
    return n

def parse_ref(ref):
    m = re.match(r"([A-Z]+)(\d+)", ref)
    return col_letters_to_idx(m.group(1)), int(m.group(2))

wb = ET.fromstring(z.read("xl/workbook.xml"))
sheets = []
for s in wb.find("m:sheets", NS):
    sheets.append((s.get("name"), s.get("state", "visible")))

# rid mapping
RNS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
rid2target = {rel.get("Id"): rel.get("Target") for rel in rels}

report = []
for idx, (name, state) in enumerate(sheets, 1):
    path = f"xl/worksheets/sheet{idx}.xml"
    ws = ET.fromstring(z.read(path))
    dim = ws.find("m:dimension", NS)
    dim_ref = dim.get("ref") if dim is not None else "?"
    # sheetViews / protection
    sv = ws.find("m:sheetViews/m:sheetView", NS)
    pane = sv.find("m:pane", NS) if sv is not None else None
    protection = ws.find("m:sheetProtection", NS)
    merges = ws.find("m:mergeCells", NS)
    nmerge = int(merges.get("count")) if merges is not None else 0
    # rows: count & max col
    maxrow = 0; maxcol = 0; ncells = 0; nformula = 0
    formulas = {}
    headers = []
    hidden_rows = 0
    for row in ws.iter("{%s}row" % NS["m"]):
        r = int(row.get("r"))
        maxrow = max(maxrow, r)
        if row.get("hidden") == "1":
            hidden_rows += 1
        for c in row:
            ref = c.get("r")
            if ref:
                ci, ri = parse_ref(ref)
                maxcol = max(maxcol, ci)
            ncells += 1
            f = c.find("m:f", NS)
            if f is not None and f.text:
                nformula += 1
                # collect distinct functions
                for fn in set(re.findall(r"([A-Z][A-Z0-9\.]+)\(", f.text)):
                    formulas[fn] = formulas.get(fn, 0) + 1
            if ri == 1 and headers.__len__() < 60:
                v = c.find("m:v", NS)
                t = c.get("t")
                val = None
                if v is not None:
                    val = ss[int(v.text)] if t == "s" else v.text
                elif c.find("m:is", NS) is not None:
                    val = "".join(x.text or "" for x in c.find("m:is", NS).iter("{%s}t" % NS["m"]))
                headers.append(f"{ref}={val}")
    print(f"\n=== [{idx}] {name} ({state}) dim={dim_ref} rows={maxrow} cols={maxcol} cells={ncells} formulas={nformula} merges={nmerge} hiddenRows={hidden_rows}")
    if protection is not None:
        print(f"  protection: {dict(protection.attrib)}")
    if headers:
        print(f"  row1: {headers[:40]}")
    if formulas:
        top = sorted(formulas.items(), key=lambda x: -x[1])[:15]
        print(f"  top functions: {top}")

# calc chain size
print("\ncalcChain entries:", sum(1 for _ in z.read("xl/calcChain.xml").split(b"</c>")) - 1)
