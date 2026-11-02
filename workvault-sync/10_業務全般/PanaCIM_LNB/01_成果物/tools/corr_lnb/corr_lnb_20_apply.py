# -*- coding: utf-8 -*-
"""corr_lnb_20_apply.py — Stage 5相関図(アイコン統合済み)をLNB原本へ適用(report §8.3)。
corr_pana_16_apply.py(2026-10-28ユーザー承認·Pana-CIM冊で実績)と同じ方式:
  ①原本の相関図シートを冊内退避(相関図_old) ②dry-runの相関図シートを冊内へ複製
  ③旧シートを削除し複製を改名·元のタブ位置へ ④保存 ⑤検証
差分: 図形数の期待=57+アイコン18=75·B11アンカーをdryと±1.0ptで照合·
      C7文言をcorr_lnb_21_wording_result.jsonのafterと一致照合·PDF生成は含まない
      (レンダは15--target orig検証後·corr_lnb_23で実施)。
前提: dry-runはアイコン18/18·文言適用·corr_lnb_15 --target dry 合格済み。
"""
import json
import os
import shutil
import sys
import time
import subprocess

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
HERE = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\tools\corr_lnb"
WORK = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\corr_lnb_work"
DRY = os.path.join(WORK, "corr_dryrun_lnb.xlsx")
VAULT = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
ORIG = os.path.join(VAULT, "LNB管理手順書案_未承認.xlsx")
BACKUP = os.path.join(WORK, "LNB管理手順書案_未承認_before_apply_20261102.xlsx")
WORDING = os.path.join(HERE, "corr_lnb_21_wording_result.json")
RESULT = os.path.join(HERE, "corr_lnb_20_apply_result.json")

out = {"errors": [], "assert_fails": []}
wres = json.load(open(WORDING, encoding="utf-8"))
shutil.copy2(ORIG, BACKUP)
out["file_backup"] = BACKUP
import hashlib
out["orig_sha256_before"] = hashlib.sha256(open(ORIG, "rb").read()).hexdigest()

import win32com.client
import win32process
import pywintypes


def com_retry(fn, tries=10, wait=0.5):
    """RPC_E_CALL_REJECTED(-2147418111) 等の一時拒否をリトライする(大冊の Move/Delete 後に発生)。"""
    last = None
    for _ in range(tries):
        try:
            return fn()
        except pywintypes.com_error as e:
            last = e
            time.sleep(wait)
    raise last


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
    assert "相関図_old" not in names_o, "orig already has 相関図_old"
    ws_old = wb_o.Worksheets("相関図")
    pos = ws_old.Index
    out["old_sheet"] = {"index": pos, "shapes": ws_old.Shapes.Count}
    if ws_old.Shapes.Count != 34:
        out["assert_fails"].append("orig 相関図 shapes %d != 34" % ws_old.Shapes.Count)

    # 他シートから相関図への参照(数式·定義名)を確認
    refs = []
    for s in wb_o.Sheets:
        if s.Name == "相関図":
            continue
        try:
            txt = str(s.UsedRange.Formula)
            if "相関図!" in txt or "'相関図'!" in txt:
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
    ws_old.Copy(None, wb_o.Sheets(pos))  # After:=自分 → 直後に複製
    dup = wb_o.Sheets(pos + 1)
    dup.Name = "相関図_old"
    out["backup_sheet"] = {"name": "相関図_old", "shapes": dup.Shapes.Count}

    # ② dry-runの相関図を複製して挿入
    wb_d.Worksheets("相関図").Copy(None, wb_o.Sheets("相関図_old"))
    new_sh = None
    for s in wb_o.Sheets:
        if s.Name.startswith("相関図 ("):
            new_sh = s
            break
    assert new_sh is not None, "copied sheet not found"

    # ③ 旧シートを削除し、複製を改名·移動
    app = xl.Application
    app.DisplayAlerts = False
    wb_o.Worksheets("相関図").Delete()
    new_sh.Name = "相関図"
    new_sh.Move(wb_o.Sheets(pos))  # Before:=旧位置のシート → 旧位置へ
    time.sleep(1.5)  # 大冊の Move/Delete 直後は COM が一時拒否するため落ち着かせる
    out["moved_to_index"] = wb_o.Worksheets("相関図").Index

    # ⑤ 検証
    ws = wb_o.Worksheets("相関図")
    ws_d = wb_d.Worksheets("相関図")
    n = com_retry(lambda: ws.Shapes.Count)
    icons = com_retry(lambda: sum(1 for i in range(1, n + 1)
                                  if str(ws.Shapes.Item(i).Name).startswith("icon_")))
    ps = ws.PageSetup
    b11_o = [round(float(ws.Range("B11").Left), 1), round(float(ws.Range("B11").Top), 1)]
    b11_d = [round(float(ws_d.Range("B11").Left), 1), round(float(ws_d.Range("B11").Top), 1)]
    ver = {"shapes": n, "icons": icons,
           "print_area": com_retry(lambda: ps.PrintArea),
           "orientation": com_retry(lambda: int(ps.Orientation)),
           "fit": [int(ps.FitToPagesWide), int(ps.FitToPagesTall)],
           "B11_orig": b11_o, "B11_dry": b11_d,
           "sheets": com_retry(lambda: [s.Name for s in wb_o.Sheets])}
    spot = {}
    try:
        spot["n19_head"] = "CIMA-SV" in str(ws.Shapes("n19_cima_sv").TextFrame2.TextRange.Text)
    except Exception as e:
        spot["n19_head"] = "ERR %r" % e
    try:
        spot["icon_n19_pos"] = [round(float(ws.Shapes("icon_n19_cima_sv").Left)
                                     - float(ws.Range("B11").Left), 1),
                                round(float(ws.Shapes("icon_n19_cima_sv").Top)
                                     - float(ws.Range("B11").Top), 1)]
    except Exception as e:
        spot["icon_n19_pos"] = "ERR %r" % e
    spot["C7_match_wording"] = str(ws.Range("C7").Value) == wres["after"]["C7"]
    spot["C10_match_wording"] = str(ws.Range("C10").Value) == wres["after"]["C10"]
    old_names = com_retry(lambda: [wb_o.Worksheets("相関図_old").Shapes.Item(i).Name
                                   for i in range(1, wb_o.Worksheets("相関図_old").Shapes.Count + 1)])
    spot["old_all_rel"] = all(s.startswith("rel_") for s in old_names)
    ver["spot"] = spot
    out["verify"] = ver

    if n != 75:
        out["assert_fails"].append("shape count %d != 75 (57+18)" % n)
    if icons != 18:
        out["assert_fails"].append("icon count %d != 18" % icons)
    if any(abs(a - b) > 1.0 for a, b in zip(b11_o, b11_d)):
        out["assert_fails"].append("B11 anchor drift orig %s vs dry %s" % (b11_o, b11_d))
    if ver["orientation"] != 2 or ver["print_area"] != "$A$1:$AY$60":
        out["assert_fails"].append("pagesetup NG: %s" % {k: ver[k] for k in ("orientation", "print_area")})
    if not spot.get("n19_head") or spot.get("old_all_rel") is not True:
        out["assert_fails"].append("spot NG: %s" % spot)
    if not spot.get("C7_match_wording") or not spot.get("C10_match_wording"):
        out["assert_fails"].append("C7/C10 wording mismatch")

    if not out["assert_fails"]:
        wb_o.Save()
        print("saved orig.", flush=True)
    else:
        print("NOT saved (assert_fails).", flush=True)
    wb_d.Close(False)
    wb_o.Close(False)
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
print("verify:", json.dumps(out.get("verify"), ensure_ascii=False))
