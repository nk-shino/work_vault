# -*- coding: utf-8 -*-
"""fix35_rev3_verify.py — rev-3修正の検証(読み取り専用).

1. No.20 が1頁内で完全に印字されていること(テキスト抽出+レンダ目視)
2. 認証情報一覧の頁に頁番号が印字されていること(番号欄のみ照会·本文は見ない)
3. 相関図_old が冊PDFに含まれないこと(旧見出し「2-3. 相関図」の消失·p12=管理体制)
4. 印字頁番号と冊内位置の一致(抜き取り照会)
出力: 数値·ブール·頁番号のみ。セルテキストは出力しない。
"""
import os, sys, json, re

sys.stdout.reconfigure(encoding="utf-8")

PDFP = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\LNB管理手順書案_未承認.pdf"
OUT = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\rev3_lnb"
RES = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関图\scripts".replace("图", "図") + r"\fix35_rev3_verify_report.json"

import fitz  # pymupdf
from pypdf import PdfReader

doc = fitz.open(PDFP)
R = {"pages": len(doc)}

# ---------- 1. No.20 の印字(テキストレベル) ----------
no20_pages = []
for i in range(len(doc)):
    t = doc[i].get_text()
    if "20：復旧の手順と戻す試験" in t:
        no20_pages.append(i + 1)
        ok_full = ("未確認(2026-10-14時点)" in t.replace("\n", "")) and ("現行実施者" in t)
        R["no20_page"] = i + 1
        R["no20_complete_text"] = bool(ok_full)
assert len(no20_pages) == 1, f"No.20 appears on pages {no20_pages}"
assert R["no20_complete_text"], "No.20 tail missing"

# ---------- 2. p12 の内容(旧図除外の確認) ----------
t12 = doc[11].get_text()
R["p12_has_kanriseitai"] = "管理体制" in t12
R["p12_has_old_heading"] = ("2-3. 相関図" in t12) or ("2-3．相関図" in t12)
R["old_heading_pages"] = [i + 1 for i in range(len(doc))
                          if ("2-3. 相関図" in doc[i].get_text()) or ("2-3．相関図" in doc[i].get_text())]
R["old_name_pages"] = [i + 1 for i in range(len(doc)) if "相関図_old" in doc[i].get_text()]
assert R["p12_has_kanriseitai"] and not R["p12_has_old_heading"], "p12 check failed"
assert not R["old_heading_pages"] and not R["old_name_pages"], "old sheet still in booklet"

# ---------- 3. 印字頁番号と位置の一致(右上欄の抜き取り) ----------
def corner_number(page_idx):
    """右上の頁番号欄のみテキスト抽出する(本文には触れない)。"""
    pg = doc[page_idx]
    r = pg.rect
    clip = fitz.Rect(r.width * 0.82, 10, r.width, 60)
    t = pg.get_text(clip=clip)
    nums = re.findall(r"\d+", t)
    return nums

expect = {12: "12", 13: "13", 19: "19", 25: "25", 26: "26", 27: "27",
          30: "30", 31: "31", 28: "28", 29: "29"}
num_checks = {}
for pos, want in expect.items():
    nums = corner_number(pos - 1)
    num_checks[pos] = {"found": nums, "ok": want in nums}
R["printed_numbers"] = num_checks
bad = [p for p, v in num_checks.items() if not v["ok"]]
assert not bad, f"printed number mismatch at positions {bad}"

# ---------- 4. 検証用レンダ(TEMP) ----------
os.makedirs(OUT, exist_ok=True)
mat = fitz.Matrix(150 / 72, 150 / 72)
p_no20 = R["no20_page"] - 1
pix = doc[p_no20].get_pixmap(matrix=mat)
pix.save(os.path.join(OUT, "after_p%02d_full.png" % (p_no20 + 1)))
# No.20 領域のズーム(テキスト位置から矩形を取る)
tp = doc[p_no20].search_for("20：復旧の手順と戻す試験")[0]
clip = fitz.Rect(30, tp.y0 - 8, doc[p_no20].rect.width - 30, min(tp.y1 + 60, doc[p_no20].rect.height - 50))
pix = doc[p_no20].get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72), clip=clip)
pix.save(os.path.join(OUT, "after_no20_zoom.png"))
# 認証情報一覧の頁(30)は番号欄のみレンダ(本文は見ない)
pg30 = doc[29]
r = pg30.rect
clip = fitz.Rect(r.width * 0.80, 8, r.width, 62)
pix = pg30.get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72), clip=clip)
pix.save(os.path.join(OUT, "after_p30_numberfield.png"))

with open(RES, "w", encoding="utf-8") as f:
    json.dump(R, f, ensure_ascii=False, indent=1)
print(json.dumps(R, ensure_ascii=False, indent=1))
print("RENDERS ->", OUT)
