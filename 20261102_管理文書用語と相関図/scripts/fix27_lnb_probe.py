# -*- coding: utf-8 -*-
"""fix27_lnb_probe.py — LNB冊の現状余白をCOMで読み取り(読み取り専用·保存なし)。

エントリ27 [F1] の事前実測。申し送り(認証情報)シートは一切参照しない。
"""
import os, sys, json, traceback

WORK = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図"
XLSX = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\LNB管理手順書案_未承認.xlsx"
REPORT = os.path.join(WORK, "scripts", "fix27_lnb_margins_before.json")

ORDER17 = ["表紙", "目次", "用語", "構成と管理情報", "相関図", "相関図_old", "管理体制",
           "日次点検", "定期管理", "バックアップ", "復旧", "異常時の対応",
           "チェックシート(日次)", "チェックシート(月次・異常時)", "会議課題一覧(一時)",
           "要確認事項一覧", "引用と部品照合"]

def main():
    import win32com.client as win32
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    out = {"unit_note": "COM PageSetup 余白はポイント単位。inch = pt / 72", "sheets": {}}
    try:
        wb = app.Workbooks.Open(XLSX, UpdateLinks=0, ReadOnly=True)
        for name in ORDER17:
            ps = wb.Worksheets(name).PageSetup
            vals = {}
            for k in ("LeftMargin", "RightMargin", "TopMargin", "BottomMargin", "HeaderMargin", "FooterMargin"):
                v = getattr(ps, k)
                vals[k] = round(float(v), 2)
                vals[k + "_in"] = round(float(v) / 72.0, 4)
            out["sheets"][name] = vals
        wb.Close(SaveChanges=False)
    finally:
        app.Quit()
    with open(REPORT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for name, v in out["sheets"].items():
        print(f"{name}: L{v['LeftMargin']}pt({v['LeftMargin_in']}in) R{v['RightMargin']}pt({v['RightMargin_in']}in) "
              f"T{v['TopMargin']}pt({v['TopMargin_in']}in) B{v['BottomMargin']}pt({v['BottomMargin_in']}in) "
              f"H{v['HeaderMargin']} F{v['FooterMargin']}", flush=True)
    print("DONE", flush=True)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.exit(1)
