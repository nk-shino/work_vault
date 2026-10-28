# -*- coding: utf-8 -*-
"""corr_pana_01_backup.py — Pana-CIM冊ドライラン準備
1) 原本をファイルコピーして corr_dryrun_pana.xlsx を作成(原本は触らない)
2) 相関図シートを丸ごと「相関図_old」へ複製(spec §9-1 退避)
3) 図形数を照合して保存
"""
import os, shutil, sys, json

SRC = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\Pana-CIM管理手順書案_未承認.xlsx"
DST = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\issue6263_work\corr_dryrun_pana.xlsx"

# --- 1) ファイルコピー(原本は読み取りのみ) ---
if not os.path.exists(SRC):
    print("ERR: source not found"); sys.exit(1)
shutil.copyfile(SRC, DST)
print("copy ok:", os.path.getsize(DST), "bytes")

# --- 2) COM でコピー先のみ編集 ---
import win32com.client
import pythoncom
import win32process

xl = None; wb = None; ws = None; ws_old = None
pid_reported = None
result = {"copied": True, "old_exists": False, "shapes_main": None, "shapes_old": None, "pid": None}
try:
    xl = win32com.client.DispatchEx("Excel.Application")
    xl.Visible = False
    xl.DisplayAlerts = False
    try:
        pid_reported = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
        result["pid"] = pid_reported
        print("EXCEL.EXE PID:", pid_reported)
    except Exception as e:
        print("pid capture failed:", e)

    wb = xl.Workbooks.Open(DST)

    # 既存の相関図_old があれば削除(再実行対応)
    for i in range(wb.Worksheets.Count, 0, -1):
        if wb.Worksheets(i).Name == "相関図_old":
            wb.Worksheets(i).Delete
            result["old_exists"] = True  # had to delete
            print("existing 相関図_old deleted")

    ws = wb.Worksheets("相関図")
    result["shapes_main"] = ws.Shapes.Count

    ws.Copy(After=ws)
    ws_old = wb.Worksheets(ws.Index + 1)
    ws_old.Name = "相関図_old"
    result["shapes_old"] = ws_old.Shapes.Count

    print("shapes main =", result["shapes_main"], "/ old =", result["shapes_old"])

    wb.Save()
    print("saved")
except Exception as e:
    print("COM ERR:", repr(e))
finally:
    try:
        if wb is not None: wb.Close(SaveChanges=False)
    except Exception as e:
        print("close err:", repr(e))
    try:
        if xl is not None: xl.Quit()
    except Exception as e:
        print("quit err (PDF/保存は完了済みの可能性):", repr(e))

with open(r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\issue6263_work\corr_pana_01_backup_result.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
print("done", json.dumps(result, ensure_ascii=False))

# 残存確認(PIDを名前でなく個別に)
if pid_reported:
    import subprocess
    chk = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid_reported], capture_output=True, text=True)
    line = [l for l in chk.stdout.splitlines() if "EXCEL" in l.upper()]
    print("residual:", line if line else "none (EXCEL.EXE exited)")
