# -*- coding: utf-8 -*-
"""corr_pana_19_render.py — アイコン統合後のPana-CIM原本のレンダ。
- 相関図シートのみをtemp PDF→PNG(150dpi)へ出力し視覚確認に供する
- 確認用PDF(原本と同名·冊全体)をvaultへ再生成(旧PDFはtempへ退避)
"""
import json
import os
import shutil
import sys
import time
import subprocess

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
WORK = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\corr_lnb_work"
VAULT = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
ORIG = os.path.join(VAULT, "Pana-CIM管理手順書案_未承認.xlsx")
PDF_SHEET = os.path.join(WORK, "corr_pana_orig_icons.pdf")
PNG_SHEET = os.path.join(WORK, "corr_pana_orig_icons_p1.png")
PDF_BOOK_NEW = os.path.join(VAULT, "Pana-CIM管理手順書案_未承認.pdf")
PDF_BOOK_OLD = os.path.join(WORK, "Pana-CIM管理手順書案_未承認_pdf_before_icons_20261102.pdf")
RESULT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corr_pana_19_render_result.json")

out = {"ok": False, "pid": None, "render": {}, "assert_fails": [], "errors": []}
if os.path.exists(PDF_BOOK_NEW):
    shutil.copy2(PDF_BOOK_NEW, PDF_BOOK_OLD)
    out["render"]["old_book_pdf_backup"] = PDF_BOOK_OLD

import win32com.client
import win32process

xl = win32com.client.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
pid = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
out["pid"] = pid
print("EXCEL PID", pid, flush=True)
try:
    wb = xl.Workbooks.Open(ORIG, ReadOnly=True)
    ws = wb.Worksheets("相関図")
    ws.ExportAsFixedFormat(0, PDF_SHEET, 0, True, False)
    wb.ExportAsFixedFormat(0, PDF_BOOK_NEW, 0, True, False)
    out["render"]["sheet_pdf"] = PDF_SHEET
    out["render"]["book_pdf"] = PDF_BOOK_NEW
    out["render"]["book_pdf_size"] = os.path.getsize(PDF_BOOK_NEW)
    wb.Close(SaveChanges=False)
finally:
    try:
        xl.Quit()
    except Exception as e:
        out["errors"].append(("quit: %r" % e)[:80])
    time.sleep(2)
    try:
        chk = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid], capture_output=True, text=True)
        if "EXCEL" in chk.stdout.upper():
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
            out["cleanup"] = "killed residual %d" % pid
    except Exception as e:
        out["errors"].append(("cleanup: %r" % e)[:80])

try:
    import pymupdf
    doc = pymupdf.open(PDF_SHEET)
    doc[0].get_pixmap(dpi=150).save(PNG_SHEET)
    out["render"]["sheet_png"] = PNG_SHEET
    out["render"]["sheet_pdf_pages"] = doc.page_count
    doc.close()
    doc = pymupdf.open(PDF_BOOK_NEW)
    out["render"]["book_pdf_pages"] = doc.page_count
    doc.close()
except Exception as e:
    out["errors"].append(("png: %r" % e)[:160])

if out["render"].get("sheet_pdf_pages") != 1:
    out["assert_fails"].append("相関図 sheet pdf pages %s != 1" % out["render"].get("sheet_pdf_pages"))
for k in ("sheet_pdf", "sheet_png", "book_pdf"):
    if not (out["render"].get(k) and os.path.exists(out["render"][k])):
        out["assert_fails"].append("missing: %s" % k)

out["ok"] = not out["assert_fails"] and not out["errors"]
with open(RESULT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("ok:", out["ok"])
print("render:", json.dumps(out["render"], ensure_ascii=False))
print("assert:", out["assert_fails"])
print("errors:", out["errors"])
