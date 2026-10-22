# -*- coding: utf-8 -*-
"""BOSS計画.xlsm 静的解析: シート・名前定義・接続・テーブル・VBA抽出"""
import zipfile, re, json, os, sys
from xml.etree import ElementTree as ET

SRC = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\TOOL改修問題(BOSS)\BOSS計画.xlsm"
OUT = r"C:\Users\ss80751\kohden-code-workspace\20261015_BOSS計画解析"
os.makedirs(OUT, exist_ok=True)

NS = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pr": "http://schemas.openxmlformats.org/package/2006/relationships",
}

z = zipfile.ZipFile(SRC)

# ---------- workbook.xml: シート一覧・計算設定 ----------
wb = ET.fromstring(z.read("xl/workbook.xml"))
calc = wb.find("m:calcPr", NS)
print("=== calcPr ===")
if calc is not None:
    print(dict(calc.attrib))
f1904 = wb.find("m:workbookPr", NS)
print("=== workbookPr ===")
if f1904 is not None:
    print(dict(f1904.attrib))

sheets = []
for s in wb.find("m:sheets", NS):
    rid = s.get("{%s}id" % NS["r"])
    sheets.append({"name": s.get("name"), "sheetId": s.get("sheetId"), "rid": rid, "state": s.get("state", "visible")})

# rid -> target
rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
rid2target = {rel.get("Id"): rel.get("Target") for rel in rels}
for s in sheets:
    s["target"] = rid2target.get(s["rid"], "?")

print("\n=== sheets ===")
for i, s in enumerate(sheets, 1):
    print(f"{i:>2}. {s['name']:<20} state={s['state']:<10} {s['target']}")

# ---------- defined names ----------
print("\n=== definedNames ===")
dn = wb.find("m:definedNames", NS)
if dn is not None:
    for d in dn:
        print(f"{d.get('name'):<40} = {d.text}")

# ---------- connections ----------
try:
    conns = ET.fromstring(z.read("xl/connections.xml"))
    print("\n=== connections ===")
    for c in conns.iter():
        tag = c.tag.split("}")[1]
        if tag == "connection":
            print({k: v for k, v in c.attrib.items() if k in ("name", "type", "background", "refreshOnLoad", "saveData", "deleted")})
        if tag == "connectionPr" or "odc" in tag.lower():
            print("   ", tag, c.attrib)
except KeyError:
    print("no connections.xml")

# queryTables
print("\n=== queryTables ===")
for name in z.namelist():
    if "queryTable" in name:
        qt = ET.fromstring(z.read(name))
        print(name, dict(qt.attrib))
        for child in qt:
            tag = child.tag.split("}")[1]
            if tag in ("queryTableRefresh", "connectionPr"):
                print("   ", tag, child.attrib)

# ---------- tables ----------
print("\n=== tables ===")
for name in z.namelist():
    if "xl/tables/table" in name and name.endswith(".xml"):
        t = ET.fromstring(z.read(name))
        rels_name = "xl/tables/_rels/" + name.split("/")[-1] + ".rels"
        conn_id = None
        if rels_name in z.namelist():
            tr = ET.fromstring(z.read(rels_name))
            for rel in tr:
                if "tableDefinition" in rel.get("Type", ""):
                    pass
        print(f"{name}: name={t.get('name')} ref={t.get('ref')} headerRowCount={t.get('headerRowCount')}")

# ---------- external links ----------
print("\n=== externalLinks ===")
for name in z.namelist():
    if "externalLink" in name and name.endswith(".xml"):
        print(name)

# ---------- customXml 概要 ----------
print("\n=== docProps ===")
for p in ("docProps/core.xml", "docProps/app.xml", "docProps/custom.xml"):
    try:
        data = z.read(p).decode("utf-8", "replace")
        print(f"--- {p} ---")
        print(data[:1500])
    except KeyError:
        pass
