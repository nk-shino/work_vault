# -*- coding: utf-8 -*-
"""corr_pana_16_apply.py — Stage 5相関図をPana-CIM原本へ適用(2026-10-28ユーザー承認済み)。
手順: ①原本の相関図シートを相関図_oldとして冊内退避 ②dry-runの相関図シートを冊内へ複製
③旧相関図シートを削除し複製を改名·元のタブ位置へ ④保存 ⑤検証 ⑥確認用PDF再生成。
前提: dry-run(corr_dryrun_pana.xlsx)はP-1適用済み(validator HARD=0)。
"""
import json, os, sys, shutil, time, subprocess
HERE = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\issue6263_work"
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DRY = os.path.join(HERE, "corr_dryrun_pana.xlsx")
VAULT = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案"
ORIG = os.path.join(VAULT, "Pana-CIM管理手順書案_未承認.xlsx")
PDF_OUT = os.path.join(VAULT, "Pana-CIM管理手順書案_未承認.pdf")
BACKUP = os.path.join(HERE, "Pana-CIM管理手順書案_未承認_before_apply_20261028.xlsx")
RESULT = os.path.join(HERE, "corr_pana_16_apply_result.json")

out = {"errors": [], "assert_fails": []}
shutil.copy2(ORIG, BACKUP)
out["file_backup"] = BACKUP

import win32com.client, win32process
xl = win32com.client.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
pid = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
print("EXCEL PID", pid, flush=True)
out["pid"] = pid
try:
    wb_o = xl.Workbooks.Open(ORIG)
    wb_d = xl.Workbooks.Open(DRY, ReadOnly=True)
    names_o = [s.Name for s in wb_o.Sheets]
    out["orig_sheets"] = names_o
    assert "相関図" in names_o, "orig has no 相関図 sheet"
    ws_old = wb_o.Worksheets("相関図")
    pos = ws_old.Index
    out["old_sheet"] = {"index": pos, "shapes": ws_old.Shapes.Count}

    # 他シートから相関図への参照(数式·定義名)を確認
    refs = []
    for s in wb_o.Sheets:
        if s.Name == "相関図":
            continue
        try:
            f = s.UsedRange.Formula
            import re as _re
            txt = str(f)
            if "相関図!" in txt or "相関図!" in txt.replace("'相関図'!", "相関図!"):
                refs.append(s.Name)
        except Exception:
            pass
    for dn in wb_o.Names:
        try:
            if "相関図" in str(dn.RefersTo):
                refs.append("name:" + dn.Name)
        except Exception:
            pass
    out["refs_to_相関図"] = refs

    # ① 冊内退避
    if "相関図_old" in names_o:
        bk_name = "相関図_old_20261028"
    else:
        bk_name = "相関図_old"
    ws_old.Copy(None, wb_o.Sheets(pos))  # After:=自分 → 直後に複製
    dup = wb_o.Sheets(pos + 1)
    dup.Name = bk_name
    out["backup_sheet"] = {"name": bk_name, "shapes": dup.Shapes.Count}

    # ② dry-runの相関図を複製して挿入
    wb_d.Worksheets("相関図").Copy(None, wb_o.Sheets(bk_name))
    new_sh = None
    for s in wb_o.Sheets:
        if s.Name.startswith("相関図 ("):
            new_sh = s
            break
    assert new_sh is not None, "copied sheet not found"
    copied_name = new_sh.Name

    # ③ 旧シートを削除し、複製を改名·移動
    app = xl.Application
    app.DisplayAlerts = False
    wb_o.Worksheets("相関図").Delete()
    new_sh.Name = "相関図"
    new_sh.Move(wb_o.Sheets(pos))  # Before:=旧位置のシート → 旧位置へ
    out["moved_to_index"] = wb_o.Worksheets("相関図").Index

    # ⑤ 検証
    ws = wb_o.Worksheets("相関図")
    n = ws.Shapes.Count
    ps = ws.PageSetup
    ver = {"shapes": n, "print_area": ps.PrintArea, "fit": [ps.FitToPagesWide, ps.FitToPagesTall],
           "zoom": ps.Zoom, "B11_top": round(ws.Range("B11").Top, 1),
           "sheets": [s.Name for s in wb_o.Sheets]}
    chk = {}
    try:
        chk["n02_text_head"] = str(ws.Shapes("n02_app").TextFrame2.TextRange.Text)[:24]
    except Exception as e:
        chk["n02_text_head"] = "ERR %r" % e
    try:
        e9 = ws.Shapes("edge_E09")
        chk["edge_E09_left"] = round(e9.Left - ws.Range("B11").Left, 1)
    except Exception as e:
        chk["edge_E09_left"] = "ERR %r" % e
    ver["spot"] = chk
    out["verify"] = ver
    if n != 57:
        out["assert_fails"].append("shape count %d != 57" % n)
    if ver["B11_top"] > 200.0:
        out["assert_fails"].append("B11.Top %.1f looks wrong (dry-run=180)" % ver["B11_top"])

    wb_o.Save()
    print("saved orig.", flush=True)
    wb_d.Close(False)

    # ⑥ 確認用PDF再生成(冊全体)
    wb_o.ExportAsFixedFormat(0, PDF_OUT, 0, True, False)
    out["pdf"] = {"path": PDF_OUT, "size": os.path.getsize(PDF_OUT)}
    wb_o.Close(False)
    print("pdf regenerated.", flush=True)
finally:
    time.sleep(2)
    try:
        xl.Quit()
    except Exception as e:
        out["errors"].append(("quit: %r" % e)[:80])
    time.sleep(3)
    try:
        chk = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid], capture_output=True, text=True)
        if "EXCEL" in chk.stdout.upper():
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
            out["errors"].append("killed residual %d" % pid)
    except Exception as e:
        out["errors"].append(("cleanup: %r" % e)[:80])

out["ok"] = not out["assert_fails"] and not out["errors"]
with open(RESULT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print("ok:", out["ok"])
print("assert:", out["assert_fails"])
print("errors:", out["errors"])
print(json.dumps({k: out[k] for k in ("old_sheet", "backup_sheet", "refs_to_相関図", "moved_to_index")}, ensure_ascii=False))
print("verify:", json.dumps(out.get("verify"), ensure_ascii=False))
