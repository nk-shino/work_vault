# -*- coding: utf-8 -*-
"""相関図の注記行リフォーム:
- C8(凡例)とC9(配置)が印刷幅を超え右端で切断されるため、r10 に1行挿入して4行構成にする
  r7: 確定事項(変更なし)
  r8: 凡例(記号) — 元C8の前半
  r9: 保存領域の凡例+色 — 元C8の後半(字下げ3)
  r10: 配置+drawio残置 — 元C9の圧縮表記(意味同一)
- 印刷範囲を $A$1:$AY$59 へ拡張(図形が1行分下がるため)
図形は twoCellAnchor のため挿入行で自動的に下へ移動する。"""
import sys, io, time, warnings
warnings.filterwarnings("ignore")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import pythoncom, win32com.client

BOOKS = {
 "pana": r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\Pana-CIM管理手順書案_未承認.xlsx",
 "lnb":  r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案\LNB管理手順書案_未承認.xlsx",
}
C8 = "凡例：【サーバ】=サーバー(VM含む)／【端末(PC)】=作業員が操作するPC／【設備】=製造設備／【表示】=画面・表示装置"
C9 = "　　　【保存領域】=ファイル保存場所。色: 青=サーバ・表示系／黄=PC・操作端末／緑=設備・データ保存"
C10 = "配置：A4縦1頁。事象別の図(アンドン・稼働モニタ異常/月次再起動/異常時再起動)は PanaCIM_LNB_確実構成図.drawio に残置"

def fix(path):
    pythoncom.CoInitialize()
    xl = win32com.client.DispatchEx("Excel.Application")
    xl.Visible = False; xl.DisplayAlerts = False
    try:
        wb = xl.Workbooks.Open(path)
        try:
            ws = wb.Worksheets("相関図")
            ws.Rows("10:10").Insert()
            ws.Range("C8").Value = C8
            ws.Range("C9").Value = C9
            ws.Range("C10").Value = C10
            # 書式は挿入時に旧r9(Meiryo UI 9pt)がC10へ移動済みのため設定不要
            ws.PageSetup.PrintArea = "$A$1:$AY$59"
            wb.Save()
        except Exception:
            try: wb.Close(SaveChanges=False)
            except Exception: pass
            raise
        try:
            wb.Close(SaveChanges=False)
        except Exception:
            pass
    finally:
        try: xl.Quit()
        except Exception: pass
        pythoncom.CoUninitialize()

for tag, path in BOOKS.items():
    for attempt in range(1, 4):
        try:
            fix(path)
            print(f"[{tag}] OK")
            break
        except Exception as e:
            print(f"[{tag}] retry {attempt}: {e}")
            time.sleep(3)
    else:
        sys.exit(1)
print("RESULT: OK")
