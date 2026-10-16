# -*- coding: utf-8 -*-
# Copy deliverables to Work_Vault 業務内容 folder (create if needed)
import os, shutil, sys, hashlib
sys.stdout.reconfigure(encoding='utf-8')

SRC = r"C:\Users\ss80751\kohden-code-workspace\20261016_鹿島引き込みExcel分析"
DST = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\鹿島引き込み\業務内容"

files = [
 "差分確認マクロ分析.drawio",
 "preview_p1.svg", "preview_p2.svg", "preview_p3.svg", "preview_p4.svg",
 "ledger_source.json", "ledger_evidence.json", "ledger_graph.json", "ledger_issues.json",
 "validation_report.json", "利用案内.md", "manifest.yaml",
]

os.makedirs(DST, exist_ok=True)
print("dst exists:", os.path.isdir(DST))

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()

hashes = {}
for f in files:
    s = os.path.join(SRC, f)
    d = os.path.join(DST, f)
    if not os.path.exists(s):
        print("MISSING SRC:", f)
        continue
    shutil.copy2(s, d)
    hashes[f] = sha(d)
    print("copied:", f, os.path.getsize(d), "bytes")

import json
json.dump(hashes, open(os.path.join(SRC, "delivery_hashes_full.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("delivery_hashes_full.json written (full sha256 of delivered copies)")
