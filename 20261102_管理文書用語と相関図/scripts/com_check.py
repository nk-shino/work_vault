# -*- coding: utf-8 -*-
"""COM検証(改): リトライ+ローカル一時コピー経路。ReadOnly·保存なし。"""
import win32com.client, os, json, time, shutil, hashlib

VAULT = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
TMP = r"C:\Users\ss80751\AppData\Local\Temp\kohden-code\20261102_terms"

FILES = [
    ("pana", VAULT + r"\Pana-CIM管理手順書案_未承認.xlsx"),
    ("lnb", VAULT + r"\LNB管理手順書案_未承認.xlsx"),
]

def local_copy(path):
    """同一バイトのローカル一時コピーを作り(OneDrive/ネットワーク経路を回避)、パスを返す。"""
    dst = os.path.join(TMP, "comcheck_" + os.path.basename(path))
    shutil.copy2(path, dst)
    return dst

def open_with_retry(app, path, tries=3):
    last = None
    for i in range(tries):
        try:
            return app.Workbooks.Open(path, 0, True)  # UpdateLinks=0, ReadOnly=True
        except Exception as e:
            last = e
            time.sleep(2 + i * 2)
    raise last

results = []
app = win32com.client.DispatchEx("Excel.Application")
app.Visible = False
app.DisplayAlerts = False
try:
    for tag, path in FILES:
        res = {"tag": tag, "file": os.path.basename(path)}
        wb = None
        try:
            try:
                wb = open_with_retry(app, path)
                res["opened_via"] = "vault_path"
            except Exception as e1:
                res["vault_open_error"] = repr(e1)[:200]
                lpath = local_copy(path)
                wb = open_with_retry(app, lpath)
                res["opened_via"] = "local_copy"
        finally:
            if wb is not None:
                res["sheets"] = [ws.Name for ws in wb.Worksheets]
                counts = {}
                for ws in wb.Worksheets:
                    if ws.Name.startswith("相関図"):
                        counts[ws.Name] = ws.Shapes.Count
                res["shape_counts"] = counts
                # 用語シートの最終行の確認(表示上の整合)
                ws_t = wb.Worksheets("用語")
                res["last_used_row_C"] = ws_t.Cells(ws_t.Rows.Count, 3).End(-4162).Row  # xlUp
                wb.Close(SaveChanges=False)
        results.append(res)
finally:
    app.Quit()

with open(os.path.join(TMP, "com_check.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)
print("COM DONE")
for r in results:
    print(r["tag"], "| via:", r.get("opened_via"), "| err:", r.get("vault_open_error"),
          "| shapes:", r["shape_counts"], "| lastrowC:", r["last_used_row_C"])
    print("   sheets:", r["sheets"])
