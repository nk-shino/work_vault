# -*- coding: utf-8 -*-
"""Power Query DataMashup 展開: Config/Package.zip からM式を抽出"""
import zipfile, sys, io, base64, os, re
from xml.etree import ElementTree as ET

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
SRC = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\TOOL改修問題\BOSS計画.xlsm"
OUT = r"C:\Users\ss80751\kohden-code-workspace\20261015_BOSS計画解析\evidence\pq_extract"
os.makedirs(OUT, exist_ok=True)

z = zipfile.ZipFile(SRC)
# DataMashupはUTF-16のXML。中にBase64でPackage.zipが入っている
raw = z.read("customXml/item2.xml")
text = raw.decode("utf-16")
root = ET.fromstring(text)

# 子要素を全部見る
for child in root:
    tag = child.tag.split("}")[-1]
    print(f"child: {tag}, attribs: {child.attrib}")
    for sub in child:
        stag = sub.tag.split("}")[-1]
        print(f"  sub: {stag}, len={len(sub.text or '')}")

# M式らしいBase64 blobを探す
import glob
def find_and_extract(el, outdir):
    for child in el:
        tag = child.tag.split("}")[-1]
        if child.text and len(child.text) > 200:
            try:
                blob = base64.b64decode(child.text)
                if blob[:2] == b"PK":
                    inner = os.path.join(outdir, f"{tag}.zip")
                    with open(inner, "wb") as f:
                        f.write(blob)
                    print(f"saved zip: {inner} ({len(blob)} bytes)")
                    # 展開
                    with zipfile.ZipFile(inner) as zz:
                        zz.extractall(os.path.join(outdir, tag))
                        for n in zz.namelist():
                            print("   ", n)
                else:
                    print(f"{tag}: not a zip, first bytes = {blob[:20]!r}")
            except Exception as ex:
                print(f"{tag}: decode fail {ex}")
        find_and_extract(child, outdir)

find_and_extract(root, OUT)

# 展開した中身からM式を探す
print("\n=== M式ファイル探索 ===")
for dirpath, dirnames, filenames in os.walk(OUT):
    for fn in filenames:
        p = os.path.join(dirpath, fn)
        if fn.endswith((".m", ".xml", ".json", ".txt", "")):
            try:
                data = open(p, "rb").read()
                if b"let" in data or b"section" in data.lower():
                    print(f"HIT: {p} ({len(data)} bytes)")
            except Exception:
                pass
