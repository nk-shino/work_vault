# -*- coding: utf-8 -*-
"""fix34_backup.py — 適用前のvault正本4ファイルをTEMPへ退避(新メディア照合基準)。"""
import sys, io, os, shutil, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

VAULT = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
DST = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\corr23\stash2_20261105"
FILES = ["Pana-CIM管理手順書案_未承認.xlsx", "Pana-CIM管理手順書案_未承認.pdf",
         "LNB管理手順書案_未承認.xlsx", "LNB管理手順書案_未承認.pdf"]

os.makedirs(DST, exist_ok=True)
for fn in FILES:
    src = os.path.join(VAULT, fn)
    dst = os.path.join(DST, fn)
    shutil.copy2(src, dst)
    h = hashlib.md5(open(dst, "rb").read()).hexdigest()[:16]
    print(f"{fn}: {os.path.getsize(dst)} bytes sha16={h}")
print("BACKUP DONE ->", DST)
