# -*- coding: utf-8 -*-
"""corr_pana_02_backup_fix.py — ドライラン準備のやり直し(確定方式 v2)
1) 原本から working/pristine を再コピー(冪等)
2) 相関図_old を新設: UsedRange複製 → CutCopyMode解除 → 図形34個を Shapes.Paste で複製(リトライ付き)
3) 検証: 34/34・名前・幾何(0.2pt)・セル照合 → 保存
最終処理(残存プロセス掃除+結果JSON)は必ず実行する。
"""
import os, shutil, json, time, subprocess

SRC = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\Pana-CIM管理手順書案_未承認.xlsx"
DST = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\issue6263_work\corr_dryrun_pana.xlsx"
PRISTINE = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\issue6263_work\corr_dryrun_pana_pristine.xlsx"
SURVEY = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\issue6263_work\corr_pana_survey.json"
RESULT = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\issue6263_work\corr_pana_02_backup_fix_result.json"

out = {"recopied": True, "shapes_old": 0, "name_ok": False, "geom_ok": False,
       "cell_ok": False, "pid": None, "errors": [], "done": False}

def cleanup(pid):
    if not pid:
        return
    try:
        chk = subprocess.run(["tasklist", "/FI", "PID eq %d" % pid], capture_output=True, text=True)
        if "EXCEL" in chk.stdout.upper():
            subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True)
            out["errors"].append("killed residual %d" % pid)
    except Exception as e:
        out["errors"].append("cleanup:" + repr(e))

def paste_shape_with_retry(ws_old, retries=5):
    last = None
    for i in range(retries):
        try:
            time.sleep(0.12 * (i + 1))
            return ws_old.Shapes.Paste()
        except Exception as e:
            last = e
    raise last

def main():
    # 前回の孤児(14728 = 自作インスタンス)掃除
    chk = subprocess.run(["tasklist", "/FI", "PID eq 14728"], capture_output=True, text=True)
    if "EXCEL" in chk.stdout.upper():
        subprocess.run(["taskkill", "/PID", "14728", "/F"], capture_output=True)
        out["errors"].append("killed orphan 14728")
        time.sleep(1)

    shutil.copyfile(SRC, DST)
    shutil.copyfile(SRC, PRISTINE)

    with open(SURVEY, encoding="utf-8") as f:
        inv = json.load(f)["shapes"]

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
        ws_old = wb.Worksheets.Add(After=wb.Worksheets(wb.Worksheets.Count))
        ws_old.Name = "相関図_old"

        # セル層
        ws.UsedRange.Copy()
        ws_old.Range("A1").PasteSpecial(Paste=-4104)
        xl.CutCopyMode = False  # コピーモード解除(図形Pasteの干渉防止)

        # 図形
        for idx, meta in enumerate(inv, 1):
            s = ws.Shapes(meta["name"])
            s.Copy()
            p = paste_shape_with_retry(ws_old)
            p.Name = meta["name"]
            p.Left = float(meta["L"]); p.Top = float(meta["T"])
            p.Width = float(meta["W"]); p.Height = float(meta["H"])
            if idx % 10 == 0:
                print("pasted", idx, flush=True)
        xl.CutCopyMode = False

        # 検証
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

        wb.Save()
        out["done"] = True
        print("saved", flush=True)
    finally:
        try:
            wb.Close(SaveChanges=False)
        except Exception as e:
            out["errors"].append("close:" + repr(e))
        try:
            xl.Quit()
        except Exception as e:
            out["errors"].append("quit:" + repr(e))
        time.sleep(2)
        cleanup(out["pid"])

main()
with open(RESULT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=True))
