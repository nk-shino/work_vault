# -*- coding: utf-8 -*-
"""corr_pana_03_backup_v3.py — 相関図退避 v3
教訓: pywin32 動的ディスパッチは名前付き引数を黙って落とすことがある → COM の省略可能引数は位置引数で渡す。
方法A: ws.Copy(None, ws) 位置引数でシート複製 → 34図形確認 → 相関図_old に改名
方法B(フォールバック): 図形を1個ずつ s.Copy() → ws_old.Paste()(Worksheet.Paste・CutCopyMode解除済み・リトライ)
検証: 図形数・名前・幾何(0.2pt)・A6セル → 保存。最終処理は必ず実行。
"""
import shutil, json, time, subprocess

SRC = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\Pana-CIM管理手順書案_未承認.xlsx"
DST = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\issue6263_work\corr_dryrun_pana.xlsx"
PRISTINE = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\issue6263_work\corr_dryrun_pana_pristine.xlsx"
SURVEY = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\issue6263_work\corr_pana_survey.json"
RESULT = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\issue6263_work\corr_pana_03_backup_result.json"

out = {"method": None, "shapes_old": 0, "name_ok": False, "geom_ok": False,
       "cell_ok": False, "pid": None, "errors": [], "done": False}

def kill_if_excel(pid):
    try:
        chk = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid], capture_output=True, text=True)
        if "EXCEL" in chk.stdout.upper():
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
            out["errors"].append("killed residual %d" % pid)
    except Exception as e:
        out["errors"].append("cleanup:" + repr(e))

with open(SURVEY, encoding="utf-8") as f:
    inv = json.load(f)["shapes"]

shutil.copyfile(SRC, DST)
shutil.copyfile(SRC, PRISTINE)

import win32com.client
import win32process

xl = win32com.client.DispatchEx("Excel.Application")
xl.Visible = False
xl.DisplayAlerts = False
out["pid"] = win32process.GetWindowThreadProcessId(xl.Hwnd)[1]
print("EXCEL PID", out["pid"], flush=True)

try:
    wb = xl.Workbooks.Open(DST)
    ws = wb.Worksheets("相関図")
    n0 = wb.Worksheets.Count

    # --- 方法A: 位置引数でシート複製 ---
    try:
        ws.Copy(None, ws)  # (Before, After) 位置引数 → After=ws
        time.sleep(0.3)
        n1 = wb.Worksheets.Count
        if n1 == n0 + 1:
            ws_new = wb.Worksheets(ws.Index + 1)
            sc = ws_new.Shapes.Count
            if sc == len(inv) and ws_new.Name != "相関図_old":
                ws_new.Name = "相関図_old"
                out["method"] = "A:sheet copy positional"
                print("method A ok, shapes", sc, flush=True)
            else:
                out["errors"].append("A: copied sheet shapes=%d name=%s" % (sc, ws_new.Name))
                # 予期しないシートを触らず、A は不採用(作成物は残置せず削除)
                if ws_new.Name != "相関図_old":
                    xl.DisplayAlerts = False
                    ws_new.Delete
                    out["errors"].append("A: deleted unexpected copy")
        else:
            out["errors"].append("A: sheet count %d -> %d (copy created a workbook?)" % (n0, n1))
            # 新ブックに複製された可能性 → 開いている他ブックを無保存で閉じる
            for wbx in list(xl.Workbooks):
                if wbx.Name != wb.Name:
                    wbx.Close(SaveChanges=False)
    except Exception as e:
        out["errors"].append("A exc:" + repr(e)[:160])

    # --- 方法B: 図形を1個ずつ(方法A不成立のとき) ---
    if out["method"] is None:
        ws_old = wb.Worksheets.Add(After=wb.Worksheets(wb.Worksheets.Count))
        ws_old.Name = "相関図_old"
        for idx, meta in enumerate(inv, 1):
            s = ws.Shapes(meta["name"])
            ok = False; last = None
            for i in range(5):
                try:
                    s.Copy()
                    time.sleep(0.15 * (i + 1))
                    ws_old.Paste()
                    p = ws_old.Shapes(ws_old.Shapes.Count)
                    p.Name = meta["name"]
                    p.Left = float(meta["L"]); p.Top = float(meta["T"])
                    p.Width = float(meta["W"]); p.Height = float(meta["H"])
                    ok = True; break
                except Exception as e:
                    last = e
                    xl.CutCopyMode = False
            if not ok:
                out["errors"].append("B: shape %d %s: %r" % (idx, meta["name"], last)[:160])
                break
        else:
            out["method"] = "B:per-shape paste"
            print("method B ok", flush=True)

    # --- 検証と保存 ---
    if out["method"]:
        ws_old = wb.Worksheets("相関図_old")
        out["shapes_old"] = ws_old.Shapes.Count
        name_ok = True; geom_ok = True
        for meta in inv:
            try:
                p = ws_old.Shapes(meta["name"])
            except Exception:
                name_ok = False; out["errors"].append("missing " + meta["name"]); continue
            dl = max(abs(p.Left - float(meta["L"])), abs(p.Top - float(meta["T"])),
                     abs(p.Width - float(meta["W"])), abs(p.Height - float(meta["H"])))
            if dl > 0.2:
                geom_ok = False; out["errors"].append("geom %s d=%.2f" % (meta["name"], dl))
        out["name_ok"] = name_ok
        out["geom_ok"] = geom_ok
        out["cell_ok"] = (str(ws_old.Range("A6").Value).strip() == str(ws.Range("A6").Value).strip())
        if out["name_ok"] and out["geom_ok"] and out["shapes_old"] == len(inv):
            wb.Save()
            out["done"] = True
            print("saved", flush=True)
        else:
            out["errors"].append("verify failed - not saved (file stays clean copy)")
finally:
    try:
        wb.Close(SaveChanges=False)
    except Exception as e:
        out["errors"].append("close:" + repr(e)[:80])
    try:
        xl.Quit()
    except Exception as e:
        out["errors"].append("quit:" + repr(e)[:80])
    time.sleep(2)
    kill_if_excel(out["pid"])

with open(RESULT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=True))
