# -*- coding: utf-8 -*-
"""corr_lnb_11_dryrun_setup.py — ドライラン準備( Stage A )。
① vault原本 LNB管理手順書案_未承認.xlsx を temp へ複製(原本は最終ハッシュ照合まで不変)
② 複製内で現行「相関図」シート(簡略図·34図形)を「相関図_old」へ改名(Pana-CIM冊と同じ退避パターン)
③ 相関図_old の冊内複製から新「相関図」シートを作成(ヘッダ部セルを引き継ぐ)·旧図形34個を削除
④ 図式フレーム: 列幅 A:AY=2.0字·行高 R11-58=7.7pt·印刷設定(A4横·FitToPages 1×1·範囲 $A$1:$AY$60·余白10mm)
※ openpyxl は使わない(図形消失のため)。COM のみ。用語シートは一切触れない。
出力: corr_lnb_11_setup_result.json (tools/corr_lnb)·ドライラン冊は temp。
"""
import hashlib
import json
import os
import shutil
import sys
import time
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\corr_lnb_work"
VAULT = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
ORIG = os.path.join(VAULT, "LNB管理手順書案_未承認.xlsx")
DRY = os.path.join(WORK, "corr_dryrun_lnb.xlsx")
RESULT = os.path.join(HERE, "corr_lnb_11_setup_result.json")

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.makedirs(WORK, exist_ok=True)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


out = {"ok": False, "pid": None, "assert_fails": [], "errors": [],
       "orig": ORIG, "dryrun": DRY}

h_before = sha256(ORIG)
out["sha256_orig_before"] = h_before
shutil.copy2(ORIG, DRY)
out["dryrun_size"] = os.path.getsize(DRY)

import win32com.client
import win32process

xl = win32com.client.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
out["pid"] = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
print("EXCEL PID", out["pid"], flush=True)

try:
    wb = xl.Workbooks.Open(DRY)
    names = [s.Name for s in wb.Sheets]
    out["sheets"] = names
    if "相関図" not in names:
        out["assert_fails"].append("no 相関図 sheet")
    if "相関図_old" in names:
        out["assert_fails"].append("相関図_old already exists")
    if "用語" not in names:
        out["assert_fails"].append("no 用語 sheet")
    if not out["assert_fails"]:
        ws_old = wb.Worksheets("相関図")
        n0 = ws_old.Shapes.Count
        out["old_shape_count"] = n0
        if n0 != 34:
            out["assert_fails"].append("old 相関図 shapes %d != 34" % n0)
        rel = [ws_old.Shapes.Item(i).Name for i in range(1, n0 + 1)]
        out["old_shape_names_head"] = rel[:8]
        if not all(n.startswith("rel_") for n in rel):
            out["assert_fails"].append("non rel_* shape found in old 相関図")

        pos = ws_old.Index
        out["old_index"] = pos

        # ② 冊内退避: 現行相関図 → 相関図_old
        ws_old.Name = "相関図_old"

        # ③ 新「相関図」シートを 相関図_old の複製で作成(直後に挿入)
        wb.Worksheets("相関図_old").Copy(None, wb.Sheets("相関図_old"))
        new_sh = wb.Sheets(pos + 1)
        assert new_sh.Name.startswith("相関図"), "copied sheet not adjacent: %s" % new_sh.Name
        new_sh.Name = "相関図"
        new_sh.Move(wb.Sheets("相関図_old"))  # 旧位置(相関図_oldの直前)へ
        ws = wb.Worksheets("相関図")
        out["final_index"] = ws.Index
        out["sheet_order"] = [s.Name for s in wb.Sheets]

        # 旧図形34個を削除(後方から)
        n = ws.Shapes.Count
        for i in range(n, 0, -1):
            ws.Shapes.Item(i).Delete()
        out["deleted_shapes"] = n
        if ws.Shapes.Count != 0:
            out["assert_fails"].append("shapes remain after delete: %d" % ws.Shapes.Count)

        # 図域内(行11-60)にセル値が残っていれば記録してクリア
        strays = []
        for r in range(11, 61):
            for c in range(1, 53):
                v = ws.Cells(r, c).Value
                if v is not None and str(v).strip():
                    strays.append("%s%d:%s" % (chr(64 + c) if c <= 26 else "A" + chr(64 + c - 26), r, str(v)[:40]))
        if strays:
            ws.Range("A11:AY60").ClearContents()
        out["stray_cells_cleared"] = strays

        # ④ 図式フレーム(図形を作る前に完了させる·move-and-sizeのため)
        ws.Columns("A:AY").ColumnWidth = 2.0
        w1 = ws.Range("A1:AY1").Width
        if w1 > 770.0:
            f = 770.0 / w1
            for c in range(1, 52):
                ws.Columns(c).ColumnWidth = 2.0 * f
        out["frame_width_pt"] = round(ws.Range("A1:AY1").Width, 1)
        ws.Rows("11:58").RowHeight = 7.7

        ps = ws.PageSetup
        ps.Orientation = 2  # xlLandscape
        ps.Zoom = False     # FitToPages 使用時は False
        ps.FitToPagesWide = 1
        ps.FitToPagesTall = 1
        ps.PrintArea = "$A$1:$AY$60"
        ps.PrintGridlines = False
        ps.LeftMargin = 28.35; ps.RightMargin = 28.35
        ps.TopMargin = 28.35; ps.BottomMargin = 28.35
        ps.HeaderMargin = 14.17; ps.FooterMargin = 14.17

        X0 = ws.Range("B11").Left
        Y0 = ws.Range("B11").Top
        out["anchor_B11"] = {"left": round(float(X0), 1), "top": round(float(Y0), 1)}
        out["fig_bottom_abs"] = round(float(Y0) + 366.0, 1)
        out["row60_bottom_abs"] = round(float(ws.Rows(60).Top + ws.Rows(60).RowHeight), 1)
        if out["row60_bottom_abs"] < out["fig_bottom_abs"]:
            out["assert_fails"].append("print area row60 bottom < figure bottom 366pt")

        # 相関図_old の保全確認
        wso = wb.Worksheets("相関図_old")
        out["old_shapes_after"] = wso.Shapes.Count
        if wso.Shapes.Count != 34:
            out["assert_fails"].append("相関図_old shapes %d != 34 after setup" % wso.Shapes.Count)

        wb.Save()
        print("saved dryrun.", flush=True)
    wb.Close(False)
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
            out["errors"].append("killed residual %d" % out["pid"])
    except Exception as e:
        out["errors"].append(("cleanup: %r" % e)[:80])

out["sha256_orig_after"] = sha256(ORIG)
out["orig_unchanged"] = out["sha256_orig_after"] == h_before
if not out["orig_unchanged"]:
    out["assert_fails"].append("VAULT ORIGINAL HASH CHANGED")

out["ok"] = not out["assert_fails"] and not out["errors"]
with open(RESULT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("ok:", out["ok"])
print("assert:", out["assert_fails"])
print("errors:", out["errors"])
print("sheets:", out.get("sheet_order"))
