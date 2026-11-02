# -*- coding: utf-8 -*-
"""Power Query定義抽出: customXml/dataMashup確認"""
import zipfile, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
SRC = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\TOOL改修問題(BOSS)\BOSS計画.xlsm"
z = zipfile.ZipFile(SRC)

# customXml item2/item4 are large - check for mashup
for name in z.namelist():
    if "customXml" in name and name.endswith(".xml"):
        data = z.read(name).decode("utf-8", "replace")
        print(f"--- {name} ({len(data)} chars) ---")
        print(data[:800])
        print()

# customXml/item1.xml is small - print all
print("=== item1 ===")
print(z.read("customXml/item1.xml").decode("utf-8", "replace"))
print("=== itemProps ===")
for name in z.namelist():
    if "itemProps" in name:
        print(name, z.read(name).decode("utf-8", "replace")[:400])
