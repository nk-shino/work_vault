# -*- coding: utf-8 -*-
"""fix34_apply.py — クリップ5ラベルの表示是正 + LNB認証情報一覧フッター補完(vault直適用)。

適用内容(両冊共通値):
 相関図②: N17 テキスト幅拡張(l 626→620, w 111→118)+高さ拡張(77.7→92)/箱 83.7→97
           N18 全体+8下方移動+高さ拡張(text 59.36→66, box 65.36→72)
 相関図③: N07 高さ拡張(text 43.53→54, box 52→62)+E05/E06縦線・E05ラベル・E10_s0随伴(+10)
           N11 テキスト幅拡張(l 356→334, w 153→179)※高さ・随伴なし
           N09 高さ拡張(box 40→44, text t 428.91→426.41, h 30.19→40)+E04ラベル+4
 LNB: 認証情報一覧シートのフッター3欄を家紋パターンへ(内容は非接触)
テキスト文字列は一切変更しない。
"""
import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import win32com.client

VAULT = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物"
BOOKS = ["Pana-CIM管理手順書案_未承認.xlsx", "LNB管理手順書案_未承認.xlsx"]

# (シート, 図形, プロパティ, 新値) — 両冊共通
EDITS = [
    # --- 相関図② N17 ---
    ("相関図②", "g2_n17_box", "Height", 97.0),
    ("相関図②", "g2_n17_txt", "Left", 620.0),
    ("相関図②", "g2_n17_txt", "Width", 118.0),
    ("相関図②", "g2_n17_txt", "Height", 92.0),
    # --- 相関図② N18: +8下方 + 高さ拡張 ---
    ("相関図②", "g2_n18_tag", "Top", 377.07),
    ("相関図②", "g2_n18_box", "Top", 385.07),
    ("相関図②", "g2_n18_box", "Height", 72.0),
    ("相関図②", "g2_n18_icon_a", "Top", 391.07),
    ("相関図②", "g2_n18_txt", "Top", 388.07),
    ("相関図②", "g2_n18_txt", "Height", 66.0),
    # --- 相関図③ N07: 高さ拡張 + 随伴 ---
    ("相関図③", "g3_n07_box", "Height", 62.0),
    ("相関図③", "g3_n07_txt", "Height", 54.0),
    ("相関図③", "g3_e_e05", "Top", 302.0),
    ("相関図③", "g3_e_e05", "Height", 43.0),
    ("相関図③", "g3_e_e06", "Top", 302.0),
    ("相関図③", "g3_e_e06", "Height", 43.0),
    ("相関図③", "g3_e_e05_l", "Top", 303.5),
    ("相関図③", "g3_e_e10_s0", "Top", 302.0),
    ("相関図③", "g3_e_e10_s0", "Height", 18.0),
    # --- 相関図③ N11: 幅拡張のみ ---
    ("相関図③", "g3_n11_txt", "Left", 334.0),
    ("相関図③", "g3_n11_txt", "Width", 179.0),
    # --- 相関図③ N09: 高さ拡張 + E04ラベル随伴 ---
    ("相関図③", "g3_n09_box", "Height", 44.0),
    ("相関図③", "g3_n09_txt", "Top", 426.41),
    ("相関図③", "g3_n09_txt", "Height", 40.0),
    ("相関図③", "g3_e_e04_l", "Top", 472.0),
]

FOOTER = {
    "LeftFooter": '&"ＭＳ ゴシック,標準"\u3000\u3000\u3000NR4030',
    "CenterFooter": '&"ＭＳ ゴシック,標準"様式 NR4030-0300-A3',
    "RightFooter": '&"ＭＳ ゴシック,標準"日本光電',
}

excel = win32com.client.DispatchEx("Excel.Application")
excel.Visible = False
excel.DisplayAlerts = False
try:
    for bk in BOOKS:
        path = os.path.join(VAULT, bk)
        wb = excel.Workbooks.Open(path, ReadOnly=False)
        try:
            wb.AutoSaveOn = False
            print(f"== {bk} ==")
            for sheet, name, prop, val in EDITS:
                ws = wb.Worksheets(sheet)
                shp = ws.Shapes(name)
                setattr(shp, prop, float(val))
                got = round(float(getattr(shp, prop)), 2)
                ok = "OK" if abs(got - val) < 0.02 else "NG"
                print(f"  {sheet}.{name}.{prop} -> {got} [{ok}]")
                if ok == "NG":
                    raise SystemExit(f"assert fail: {sheet}.{name}.{prop}={got} expect={val}")
            if bk.startswith("LNB"):
                ws = wb.Worksheets("認証情報一覧")
                ps = ws.PageSetup
                for prop, val in FOOTER.items():
                    setattr(ps, prop, val)
                    print(f"  認証情報一覧.{prop} -> {getattr(ps, prop)!r}")
            wb.Save()
            print(f"  saved: {path}")
        finally:
            wb.Close(SaveChanges=False)
finally:
    excel.Quit()
print("APPLY DONE")
