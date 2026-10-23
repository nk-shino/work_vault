# -*- coding: utf-8 -*-
"""PDF出力の受け入れ検証: 頁数・頁サイズ・全頁文字数を基準ベクトルと突合する。
使いどころ: xlsx編集後にPDFを再出力するとき、出力の確定条件として実行する(ERR-20261023-006)。
使い方: python verify_export.py <出力したPDFのパス>"""
import sys, io, json, warnings
warnings.filterwarnings("ignore")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import fitz, os

HERE = os.path.dirname(os.path.abspath(__file__))
REF = json.load(open(os.path.join(HERE, "reference_vector.json"), encoding="utf-8"))

if len(sys.argv) != 2:
    print("使い方: python verify_export.py <PDFのパス>")
    sys.exit(2)
pdf = sys.argv[1]
doc = fitz.open(pdf)
r = doc[0].rect
n = len(doc)
vec = [len(p.get_text()) for p in doc]
sizes = {(round(p.rect.width, 2), round(p.rect.height, 2)) for p in doc}
doc.close()

print(f"頁数: {n} (基準 {REF['pages']})")
print(f"頁サイズ: {sorted(sizes)} (基準 {REF['page_width_pt']}x{REF['page_height_pt']})")
mism = [(i + 1, a, b) for i, (a, b) in enumerate(zip(vec, REF["per_page_text_chars"])) if a != b]
print(f"文字数不一致頁: {mism if mism else 'なし'}")

ok = (n == REF["pages"]
      and sizes == {(REF["page_width_pt"], REF["page_height_pt"])}
      and not mism)
print("RESULT:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
