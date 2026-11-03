# -*- coding: utf-8 -*-
"""Pana-CIM冊 改修実装の機械検証(読み取り専用·保存なし)"""
import hashlib
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

import fitz
import openpyxl

TOP = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
VAULT = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
BOOK = os.path.join(VAULT, "Pana-CIM管理手順書案_未承認.xlsx")
PDF = os.path.join(VAULT, "Pana-CIM管理手順書案_未承認.pdf")
BACKUP = os.path.join(TOP, "backup_20261102", "Pana-CIM管理手順書案_未承認_改修前.xlsx")

ok = True


def check(label, cond, detail=""):
    global ok
    if not cond:
        ok = False
    tag = "PASS " if cond else "FAIL "
    line = tag + label + ((" | " + detail) if detail else "")
    print(line)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_sha(obj):
    if isinstance(obj, str) and len(obj) == 64 and all(c in "0123456789abcdef" for c in obj):
        return obj
    if isinstance(obj, dict):
        for v in obj.values():
            r = find_sha(v)
            if r:
                return r
    if isinstance(obj, list):
        for v in obj:
            r = find_sha(v)
            if r:
                return r
    return None


# 1. バックアップの証跡(改修前のxlsxが正しく保全されているか)
sumj = json.load(open(os.path.join(TOP, "xlsx_dump", "summary_Pana-CIM管理手順書案_未承認.json"), encoding="utf-8"))
exp = find_sha(sumj)
hb = sha256(BACKUP)
check("backup_sha==dump_sha", bool(exp) and hb == exp, "expected=" + str(exp)[:16] + "... actual=" + hb[:16] + "...")
hc = sha256(BOOK)
check("book_changed_after_impl", hc != hb, "current=" + hc[:16] + "...")

# 2. openpyxl 再計数(読み取り専用·保存なし)
wb = openpyxl.load_workbook(BOOK, read_only=True, data_only=False)
total_cells = 0
total_formula = 0
sheets = []
for ws in wb.worksheets:
    n = 0
    f = 0
    for row in ws.iter_rows():
        for c in row:
            if c.value is not None and str(c.value) != "":
                n += 1
                if c.data_type == "f":
                    f += 1
    sheets.append(ws.title + ":" + str(n))
    total_cells += n
    total_formula += f
wb.close()
print("sheets: " + " ".join(sheets))
check("sheet_count==16", len(sheets) == 16, str(len(sheets)))
check("formula_count==0", total_formula == 0, str(total_formula))
print("nonempty_total=" + str(total_cells) + " (改修前=586·C:AZ結合で結合域の非トップ左セルは空になるため減少があり得る)")

# 3. PDF 検証
doc = fitz.open(PDF)
n_pages = len(doc)
empty = [i + 1 for i in range(n_pages) if not doc[i].get_text().strip()]
full = "\n".join(doc[i].get_text() for i in range(n_pages))
check("pdf_pages==47", n_pages == 47, str(n_pages))
check("no_empty_pages", not empty, str(empty))
check("no_null_string", "null" not in full, "null出現=" + str(full.count("null")))
check("style_number_present", "NR4030" in full, "NR4030出現=" + str(full.count("NR4030")))
for kw in ["約3分", "Route Editer", "windwos", "タグ", "タブ"]:
    print("keyword " + kw + ": " + str(full.count(kw)) + "件")
doc.close()

# 4. 成果物の存在
artifacts = [
    os.path.join(TOP, "変更リスト_Pana-CIM冊_20261102.md"),
    os.path.join(TOP, "scripts", "impl_pana.py"),
    os.path.join(TOP, "scripts", "impl_report.json"),
]
for p in artifacts:
    check("exists:" + os.path.basename(p), os.path.isfile(p), (str(os.path.getsize(p)) + "B") if os.path.isfile(p) else "missing")

print("RESULT: " + ("PASS" if ok else "FAIL"))
