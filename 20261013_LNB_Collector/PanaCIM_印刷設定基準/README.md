# Pana-CIM 管理手順書案: 印刷設定基準とPDF出力の受け入れ検証

## 目的

COM保存を伴うxlsx編集の後、PDF出力の頁サイズと文字の折返しが変わる問題
(ERR-20261023-006)を防ぐ。2026-10-23 実績: 保存で printerSettings2/3.bin
(プリンタDEVMODE)が書き換わり、頁サイズが 595.20×841.68pt → 595.32×841.92pt
に変化し、折返し境界のセル3頁(p68/71/89)で行末1文字が非表示になった。

## 基準

- `printerSettings2.bin` / `printerSettings3.bin`: 基準版のDEVMODE
  (git efb8991 版 = 頁 595.20×841.68pt で全文字表示の状態から採取)
- `reference_vector.json`: 基準PDF(panacim_full_v5.pdf)の頁数・頁サイズ・全頁文字数

## 手順(保存を伴う編集をしたとき)

1. **PDF出力の前に** `restore_printersettings.py` を実行
   - bin2/3 が基準と異なれば復元し、他エントリが無変更であることを検証してから上書き
   - 「復元不要」と出ればそのまま進む
2. PDFを出力(ExportAsFixedFormat)
3. **出力の確定条件として** `python verify_export.py <出力PDF>` を実行
   - 頁数107・頁サイズ595.20×841.68pt・全頁文字数が基準と一致すれば PASS
   - FAIL の場合は出力を使わない(文字欠落の恐れ)

## 注意

- xlsxを保存すると bin は再び現行プリンタドライバー基準で書き換わる。
  毎回の手順1〜3を省略しない
- 図解(異常時の対応シート)を編集したときは、加えて `../PanaCIM_検証ツール/`
  の regtest_flow.py(接続グラフ)・audit_shapes.py(重なり監査)・
  verify74_v3.py(原票突合)を実行する
