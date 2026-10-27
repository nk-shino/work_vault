# -*- coding: utf-8 -*-
"""Stage B修正2(方式B): 全画像ブロックの手前に手動改頁を追加する
- HPageBreak.Location が解決しない改頁が存在するため位置計算はしない
- 各 img_N の先頭行手前に改頁 → 図+キャプションが必ず頁頭から(分断の構造的排除)
- 既存の自動改頁と同位置になった場合は手動改頁が置き換わるだけで害はない
- 事後検証は再PDF出力+目視で行う
"""
import io, sys, time, warnings
warnings.filterwarnings("ignore")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pythoncom, win32com.client

BOOK = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\Pana-CIM管理手順書案_未承認.xlsx"
SHEETS = ["月次再起動", "バックアップ", "7-5仮_サービス起動停止", "異常時の対応"]

def run():
    pythoncom.CoInitialize()
    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    rep = []
    try:
        wb = excel.Workbooks.Open(BOOK, 0)
        try:
            for sn in SHEETS:
                ws = wb.Worksheets(sn)
                ws.Activate()
                shs = ws.Shapes
                tops = []
                for i in range(1, shs.Count + 1):
                    s = shs.Item(i)
                    if s.Name.startswith("img_"):
                        tops.append(int(s.TopLeftCell.Row))
                tops.sort()
                added = 0
                for t in tops:
                    ws.HPageBreaks.Add(ws.Range(f"A{t}"))
                    added += 1
                rep.append(f"[{sn}] img={len(tops)} 改頁追加={added} 行={tops}")
            wb.Save()
        finally:
            try:
                wb.Close(SaveChanges=False)
            except Exception as e:
                print(f"WARN Close: {e}")
    finally:
        try:
            excel.Quit()
        except Exception as e:
            print(f"WARN Quit: {e}")
        pythoncom.CoUninitialize()
    return rep

for attempt in range(1, 6):
    try:
        rep = run()
        break
    except Exception as e:
        print(f"retry {attempt}: {e!r}")
        time.sleep(2)
else:
    sys.exit(1)
print("=== 結果 ===")
for r in rep:
    print(" ", r)
print("DONE")
