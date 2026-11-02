# -*- coding: utf-8 -*-
"""probe_breaks.py — 保存後ファイルの実改ページ·行高·図形位置を実測する(読取専用)。"""
import json, os
import win32com.client as win32

XLSX = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\Pana-CIM管理手順書案_未承認.xlsx"
OUT = r"C:\Users\ss80751\kohden-code-workspace\20261102_管理文書用語と相関図\scripts\probe_breaks_out.json"

SHEETS = {
    "月次再起動": 93, "バックアップ": 190, "異常時の対応": 321,
    "7-5仮_サービス起動停止": 56, "付録 引用元と確認範囲": 28,
    "目次": 20, "用語": 32, "構成と管理情報": 21, "管理体制": 20,
    "復旧": 14, "チェックシート(月次・異常時)": 45, "会議課題一覧(一時)": 42,
    "要確認事項一覧": 36, "表紙": 36,
}

def main():
    app = win32.DispatchEx("Excel.Application")
    app.Visible = False
    app.DisplayAlerts = False
    out = {}
    try:
        wb = app.Workbooks.Open(XLSX, UpdateLinks=0, ReadOnly=True)
        for name, last in SHEETS.items():
            ws = wb.Worksheets(name)
            rec = {"last": last}
            hs = [round(float(ws.Rows[r].RowHeight), 2) for r in range(1, last + 1)]
            rec["row_heights"] = hs
            brk = []
            try:
                for i in range(1, ws.HPageBreaks.Count + 1):
                    brk.append(int(ws.HPageBreaks.Item(i).Location.Row))
            except Exception as e:
                rec["hpbreak_err"] = repr(e)
            rec["hpagebreaks"] = sorted(set(brk))
            shapes = []
            for sh in ws.Shapes:
                try:
                    shapes.append({
                        "name": sh.Name, "type": int(sh.Type),
                        "tlr": int(sh.TopLeftCell.Row), "brr": int(sh.BottomRightCell.Row),
                        "top": round(float(sh.Top), 1), "h": round(float(sh.Height), 1),
                    })
                except Exception:
                    pass
            rec["shapes"] = shapes
            # 値行
            vals = []
            ur = ws.UsedRange
            vv = ur.Value
            r0, c0 = ur.Row, ur.Column
            if isinstance(vv, tuple):
                for i, row in enumerate(vv):
                    if not isinstance(row, tuple):
                        continue
                    for j, v in enumerate(row):
                        if v is not None and str(v) != "":
                            vals.append(r0 + i)
            rec["value_rows"] = sorted(set(vals))
            out[name] = rec
        wb.Close(SaveChanges=False)
    finally:
        app.Quit()
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print("WROTE", OUT)

if __name__ == "__main__":
    main()
