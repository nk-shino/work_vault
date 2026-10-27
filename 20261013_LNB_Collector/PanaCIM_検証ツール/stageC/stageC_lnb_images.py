# -*- coding: utf-8 -*-
"""Stage C: LNB管理手順書案_未承認.xlsx へ画像6枚を挿入する。
- 構成と管理情報: r31に行挿入71行 → LWS実機画面3枚(図1-3, 要確認34/36/30の実物)
- バックアップ: 空白領域r18以降 → DGSジョブ作成シート3枚(参考添付1-3, 対応未確認)
- 表示サイズ: scale = min(340/自然幅pt, 300/自然高pt, 1.0) 96dpi(px*0.75pt) 拡大しない
- 全画像ブロック手前に手動改頁(Stage B方針踏襲)
- キャプション: 図の下のC列, Meiryo UI 10
- 図1は認証ID伏字版(LWS - LNB構成情報 - [172.25.253.11]_伏字.png)を使用
"""
import io
import sys
import time
import math

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from PIL import Image

BASE = r"C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\PanaCIM_LNB\01_成果物\20261015_管理手順書案"
BOOK = sys.argv[1] if len(sys.argv) > 1 else BASE + r"\LNB管理手順書案_未承認.xlsx"
IMG = BASE + r"\LNBimage"

FONT_NAME = "Meiryo UI"
FONT_SIZE = 10
ROW_H = 12.75


def disp_size(path):
    im = Image.open(path)
    w_pt, h_pt = im.size[0] * 0.75, im.size[1] * 0.75
    scale = min(340.0 / w_pt, 300.0 / h_pt, 1.0)
    return w_pt * scale, h_pt * scale


# (開始行, ファイル, キャプション)
KOUSEI = [
    (31, IMG + r"\日次点検\LWS - LNB構成情報 - [172.25.253.11]_伏字.png",
     "図1 LNB構成情報画面(出典：LWS 実機画面 2026-10-14 撮影。要確認34の実物。認証IDは伏字)"),
    (56, IMG + r"\日次点検\スクリーンショット 2026-10-14 102305.png",
     "図2 個別スイッチ画面(出典：LWS 実機画面 2026-10-14 撮影。要確認36：192.168.0.1が赤表示)"),
    (81, IMG + r"\日次点検\スクリーンショット 2026-10-14 102354.png",
     "図3 再起動系メニュー(出典：LWS 実機画面 2026-10-14 撮影。要確認30の実物：3ボタンを確認)"),
]
BACKUP = [
    (19, IMG + r"\バックアップ\画像_DGSジョブ作成_r007_01.png",
     "参考添付1 DGS メニュー(データ作成ジョブ一覧)(出典：DGS_P2ジョブ作成シート r007。対応：未確認)"),
    (27, IMG + r"\バックアップ\画像_DGSジョブ作成_r016_02.png",
     "参考添付2 DGS データ作成ジョブ一覧(出典：DGS_P2ジョブ作成シート r016。対応：未確認)"),
    (40, IMG + r"\バックアップ\画像_DGSジョブ作成_r034_03.png",
     "参考添付3 DGS データ作成ジョブ詳細(出典：DGS_P2ジョブ作成シート r034。対応：未確認)"),
]
BACKUP_LEAD = ("C18", "参考添付：DGS のジョブ設定画面(出典：DGS_P2ジョブ作成シート。"
               "LNB のバックアップ手順との対応は未確認)")


def open_book(excel, path, tries=3):
    last = None
    for i in range(tries):
        try:
            wb = excel.Workbooks.Open(path)
            return wb
        except Exception as e:  # retry
            last = e
            time.sleep(2)
    raise last


def main():
    import win32com.client as w
    excel = w.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    try:
        wb = open_book(excel, BOOK)

        # ---- 構成と管理情報: 行挿入71行 ----
        ws = wb.Worksheets("構成と管理情報")
        ws.Activate()
        ws.Rows("31:101").Insert()
        for r in range(31, 102):
            ws.Rows(r).RowHeight = ROW_H

        sizes = {}
        for start, path, cap in KOUSEI:
            w_pt, h_pt = disp_size(path)
            sizes[start] = (w_pt, h_pt)
            n_rows = math.ceil(h_pt / ROW_H)
            cap_row = start + n_rows
            cell = ws.Cells(cap_row, 3)
            cell.Value = cap
            cell.Font.Name = FONT_NAME
            cell.Font.Size = FONT_SIZE
            left = ws.Range("C%d" % start).Left
            top = ws.Range("C%d" % start).Top
            shp = ws.Shapes.AddPicture(path, False, True, left, top, w_pt, h_pt)
            shp.Name = "img_K%d" % start
            shp.Placement = 3  # xlFreeFloating
            print("構成管: %s -> %.1fx%.1fpt at r%d (cap r%d)" % (path.split("\\")[-1], w_pt, h_pt, start, cap_row))
        # 改頁: 各画像ブロック手前
        for start, _, _ in KOUSEI:
            ws.HPageBreaks.Add(ws.Range("A%d" % start))
        print("構成管: 改頁追加 A31/A56/A81")

        # ---- バックアップ: 行挿入なし ----
        ws2 = wb.Worksheets("バックアップ")
        ws2.Activate()
        for r in range(18, 56):
            ws2.Rows(r).RowHeight = ROW_H
        lc = ws2.Range(BACKUP_LEAD[0])
        lc.Value = BACKUP_LEAD[1]
        lc.Font.Name = FONT_NAME
        lc.Font.Size = FONT_SIZE
        for start, path, cap in BACKUP:
            w_pt, h_pt = disp_size(path)
            n_rows = math.ceil(h_pt / ROW_H)
            cap_row = start + n_rows
            cell = ws2.Cells(cap_row, 3)
            cell.Value = cap
            cell.Font.Name = FONT_NAME
            cell.Font.Size = FONT_SIZE
            left = ws2.Range("C%d" % start).Left
            top = ws2.Range("C%d" % start).Top
            shp = ws2.Shapes.AddPicture(path, False, True, left, top, w_pt, h_pt)
            shp.Name = "img_B%d" % start
            shp.Placement = 3
            print("バック: %s -> %.1fx%.1fpt at r%d (cap r%d)" % (path.split("\\")[-1], w_pt, h_pt, start, cap_row))
        for start, _, _ in BACKUP:
            ws2.HPageBreaks.Add(ws2.Range("A%d" % start))
        print("バック: 改頁追加 A18/A27/A40")

        wb.Save()

        # ---- 検証読み戻し ----
        ws.Activate()
        print("構成管 shapes=%d breaks=%s" % (
            ws.Shapes.Count,
            [ws.HPageBreaks.Item(i).Location.Row for i in range(1, ws.HPageBreaks.Count + 1)]))
        print("構成管 C55/C80/C101:", ws.Cells(55, 3).Value[:30], "/", ws.Cells(80, 3).Value[:30], "/", ws.Cells(101, 3).Value[:30])
        print("構成管 r103(A列):", ws.Cells(103, 1).Value)
        ws2.Activate()
        print("バック shapes=%d breaks=%s" % (
            ws2.Shapes.Count,
            [ws2.HPageBreaks.Item(i).Location.Row for i in range(1, ws2.HPageBreaks.Count + 1)]))
        print("バック C18:", ws2.Cells(18, 3).Value[:40])
        try:
            wb.Close(False)
        except Exception:
            pass
    finally:
        excel.Quit()
    print("DONE")


if __name__ == "__main__":
    main()
