---
type: note
phase: operate
status: active
project:
updated: 2026-10-13
---

# 開発用PC(環境B) 異常系テスト実施手順

日付: 2026-10-13
対象: E:\Collect_LNB.ps1 (v6.5-review, V-1修正済み)
根拠: 結合テスト計画書.md §6.3 エラーケース・§9-2 環境B

## 前提

- 実USB E:\ は登録済み・収集1件完了済み(正常系は合格済み)
- 異常系は **E:\ を改変→復元→ハッシュ確認** の順で実施する
- テスト後、正規状態へ完全復元すること

## 実施ケース(結合テスト計画書 §6.3 より環境Bで実施可能なもの)

| # | ケース | 手順 | 期待結果 |
|---|---|---|---|
| T-01 | ライン不正値 | `powershell -File E:\Collect_LNB.ps1 -Line L4` | exit 2, 収集開始前 |
| T-02 | `NO` 入力 | `-Line L1` 実行中に `NO` 入力 | exit 2, 収集開始前 |
| T-03 | ImportExcel 版不一致 | E:\tools\ImportExcel\ImportExcel.psd1 の ModuleVersion を 7.8.9 に書換 → PrepareOnly | exit 5, 依存検証で停止 |
| T-04 | ImportExcel 不在 | E:\tools\ImportExcel をリネーム → PrepareOnly | exit 5, DEPENDENCY_NOT_INCLUDED 相当 |
| T-05 | ImportExcel reparse | E:\tools\ImportExcel を junction に置換 → PrepareOnly | exit 5, reparse 拒否 |
| T-06 | マーカー改変(DiskSerial不一致) | E:\LNB_USB_ID.txt の DiskSerial を1文字変更 → Run | exit 4(VerifyUsb 失敗) |
| T-07 | マーカー破損(GUID破損) | E:\LNB_USB_ID.txt の GUID を不正値に → Run | exit 4 |
| T-08 | XLSX 上書き拒否 | 既存 run ディレクトリ内の XLSX を残した状態での再実行は新ディレクトリなので不可。代替: 出力ディレクトリ内に LNB_Collector.xlsx を事前配置する方法は採れない(ディレクトリ名にGUID)。**XLSX 既存チェックは CreateWorkbook 内 throw のコード確認で代替** | コード検証 |
| T-09 | 出力パス junction | data\LNB_ライン\ 配下に junction を作成しても、run ディレクトリは新規作成のため干渉しない。**代替: PrepareOnly 前提の T-05 で reparse 検知は確認済み。実USB での junction 設置は環境C で実施** | 環境Cへ繰り越し |
| T-10 | TestOnly 失敗時 exit 3 | 人工的に SelfTest を失敗させるのは改変が必要なため、**正常時 exit 0 と parser 失敗時の挙動確認で代替** | 代替確認 |
| T-11 | 警告あり完了 exit 10 | CIM 応答なしを人工的に作るのは困難。**コード解析で確認済み(§6.3 収集系)** | コード確認 |

## 復元確認

- ImportExcel: SHA256SUMS 264ファイル再照合
- LNB_USB_ID.txt: 登録時内容に戻す(バックアップ: %TEMP%\kohden-code\LNB_USB_ID.txt.bak)
- 収集出力: テストで出た不完全ディレクトリは削除(0バイト・status.json のみ等)

## 判定

- すべての異常系で **収集が開始されない、または安全に停止** し **COMPLETE.txt が作られない** こと
