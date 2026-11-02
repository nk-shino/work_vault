# -*- coding: utf-8 -*-
"""corr_lnb_16_render.py — Stage E: ドライラン冊の相関図シートを PDF/PNG へ出力(temp)。
- 新「相関図」(Stage5·57図形) と「相関図_old」(簡略図·34図形) の両方を出力し、視覚比較を可能にする
- PDF: ExportAsFixedFormat(シート単位) / PNG: PyMuPDF で 1頁目を 150dpi 描画
出力(temp):
  corr_lnb_stage5.pdf / corr_lnb_stage5_p1.png       … 新相関図
  corr_lnb_old_簡略図.pdf / corr_lnb_old_簡略図_p1.png … 現行簡略図(退避シート)
"""
import json
import os
import sys
import time
import subprocess

import win32com.client
import win32process

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WORK = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\corr_lnb_work"
DRY = os.path.join(WORK, "corr_dryrun_lnb.xlsx")
PDF_NEW = os.path.join(WORK, "corr_lnb_stage5.pdf")
PNG_NEW = os.path.join(WORK, "corr_lnb_stage5_p1.png")
PDF_OLD = os.path.join(WORK, "corr_lnb_old_簡略図.pdf")
PNG_OLD = os.path.join(WORK, "corr_lnb_old_簡略図_p1.png")
RESULT = os.path.join(HERE, "corr_lnb_16_render_result.json")

out = {"ok": False, "pid": None, "render": {}, "assert_fails": [], "errors": []}

xl = win32com.client.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
out["pid"] = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
print("EXCEL PID", out["pid"], flush=True)

try:
    wb = xl.Workbooks.Open(DRY, ReadOnly=True)
    ws = wb.Worksheets("相関図")
    ws.ExportAsFixedFormat(0, PDF_NEW, 0, True, False)  # xlTypePDF, xlQualityStandard
    out["render"]["new_pdf"] = PDF_NEW
    wso = wb.Worksheets("相関図_old")
    wso.ExportAsFixedFormat(0, PDF_OLD, 0, True, False)
    out["render"]["old_pdf"] = PDF_OLD
    out["render"]["new_shape_count"] = ws.Shapes.Count
    out["render"]["old_shape_count"] = wso.Shapes.Count
    wb.Close(SaveChanges=False)
finally:
    try:
        xl.Quit()
    except Exception as e:
        out["errors"].append(("quit: %r" % e)[:80])
    time.sleep(2)
    try:
        chk = subprocess.run(["tasklist", "/FI", "PID eq %d" % out["pid"]], capture_output=True, text=True)
        if "EXCEL" in chk.stdout.upper():
            subprocess.run(["taskkill", "/PID", str(out["pid"]), "/F"], capture_output=True)
            out["cleanup"] = "killed residual %d" % out["pid"]
    except Exception as e:
        out["errors"].append(("cleanup: %r" % e)[:80])

# PNG 変換
try:
    import pymupdf
    doc = pymupdf.open(PDF_NEW)
    doc[0].get_pixmap(dpi=150).save(PNG_NEW)
    out["render"]["new_png"] = PNG_NEW
    out["render"]["new_pdf_pages"] = doc.page_count
    doc.close()
    doc = pymupdf.open(PDF_OLD)
    doc[0].get_pixmap(dpi=150).save(PNG_OLD)
    out["render"]["old_png"] = PNG_OLD
    out["render"]["old_pdf_pages"] = doc.page_count
    doc.close()
except Exception as e:
    out["errors"].append(("png: %r" % e)[:160])

for k in ("new_pdf", "new_png", "old_pdf", "old_png"):
    p = out["render"].get(k)
    if p and os.path.exists(p):
        out["render"][k + "_size"] = os.path.getsize(p)
    else:
        out["assert_fails"].append("missing render output: %s (%s)" % (k, p))
if out["render"].get("new_pdf_pages") != 1:
    out["assert_fails"].append("new 相関図 pdf pages %s != 1" % out["render"].get("new_pdf_pages"))

out["ok"] = not out["assert_fails"] and not out["errors"]
with open(RESULT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("ok:", out["ok"])
print("render:", json.dumps(out["render"], ensure_ascii=False))
print("assert:", out["assert_fails"])
if out["errors"]:
    print("errors:", out["errors"])
