---
type: spec
phase: develop
status: waiting
project: LNB_Collector
updated: 2026-10-13
---

# LNB_Collector v6.5-review — 現状と残タスク

## 位置づけ

LNB(L1/L2/L3 端末)の実態把握のための収集ツール。LNB管理手順書(草案 v0.3)の記入項目を埋める元データを取る。
Open WebUI チャットで作成された v6.4.3-review を Kohden Code 側でレビュー・改修した版が v6.5-review。

## v6.4.3-review → v6.5-review の改修(6点)

1. `Safe` の式注入対策正規表現 `[=+@-]` の文字クラス範囲解釈の恐れ → `[=+@\-]` に修正
2. 出力書込後の読み戻し検証なし → `WriteAllTextVerified` 新設(status.json/CSV/JSON/COMPLETE.txt に適用)
3. XLSX 出力先の USB 上確認 → `AssertOnUsb` を CreateWorkbook 冒頭に追加
4. 出力ディレクトリ作成後の reparse 再検査の TOCTOU → 作成直後に再検査追加
5. XLSX 作成中の USB 抜去で Metadata が未確定値 → `$metaCopy` に確定値を反映
6. fatal 時 catch 内の WriteState 失敗で fatal 記録が失われる → try-catch 二重化

## 回帰テストで検出・修正した重大欠陥(V-1)

**`VerifyUsb` の正規表現が CRLF 行末のマーカーで必ず不一致になる。**
ツール自身が書き込む `LNB_USB_ID.txt` は CRLF。.NET の `$`(Multiline) は `\n` の前に一致するが
最終 GUID 文字の次は `\r` で、`[0-9a-fA-F-]{36}` が `\r` を吞めない。
**v6.4.3-review のまま実機投入すると、登録済み USB での収集が必ず停止した。**
修正: 3つの正規表現を `\r?$` / `(.+?)\r?$` に変更。CRLF/LF 両方で検証 PASS。

## 実施済み試験(環境A: 作業用PC、2026-10-13)

- 自己テスト(`-TestOnly`)14ケース全PASS、Parser エラー 0
- 回帰テスト 31ケース全PASS(AST 関数抽出+subst 疑似USBドライブ X:\)
  - 計画/結果: 同フォルダの「回帰テスト計画.md」「回帰テスト結果_20261013.md」
- CMD のスイッチ対応確認(Run/TEST/Register/PREPARE)
- MANIFEST_SHA256.txt 再生成・12/12 照合一致

## 実施済み試験(環境B: 実USB E:\、2026-10-13)
- **ImportExcel 7.8.10 静的レビュー: 条件付き合格**
  - PSGallery版 EPPlus.dll = GitHub公式リリース = NuGet EPPlus 4.5.3.2(net40)のハッシュ一致(正真正銘)
  - 212スクリプト×10危険カテゴリのスキャン: 検出15件はすべて正当用途(今回未使用の関数とExamples)
  - インポート時動作: ネットワーク・プロセス起動なし
  - 記録: `ImportExcel_静的レビュー/`(264ファイルのSHA256SUMS、ツリーハッシュ `1a9f990b...4efb`)
  - 残作業: 社内マルウェアスキャン → **実施済み(本人確認)**
- **USB配置と完全性検証**: 264/265ファイル照合一致(USB上のコピーはレビュー対象とバイト一致)
- **PREPARE_USB.cmd: exit 0**(登録済みマーカー検証+依存検証通過)
- **TEST_LNB.cmd: exit 0、自己テスト 14/14 PASS**(USB上のスクリプトで実行)
- **Run_LNB.cmd: Completed / Warnings 0**
  - `-Line L1` 指定で収集実行。10ステージ Success(excel_recent は NoData=正常)
  - 13ワークシートの XLSX 生成・再読込検証済み(computer/os/cpu/memory/disks/printers/processes/office/excel_recent/windows_recent/Metadata/SelfTest/Status)
  - 出力: `E:\data\LNB_ライン\L1_PCS03112_20261013_155647_...\`(COMPLETE.txt あり)
  - **Run_LNB.cmd は対話プロンプト(Line/YES確認)あり。空入力だと exit 5 で停止するのは仕様どおり**
- **V-1 修正の実機検証**: 登録済みマーカー(E:\LNB_USB_ID.txt)に対し修正版正規表現が一致、旧式では不一致を確認(修正が無ければ収集は必ず停止していた)

## 異常系テスト(環境B、2026-10-13)

- 9ケース実施、**8件合格・1件(出力パス junction)は exFAT のため実施不可→環境Cで繰り越し**
  - 合格: ライン不正値(exit 1・収集開始前)、NO入力(exit 2)、ImportExcel 版不一致/不在(exit 5)、マーカー DiskSerial 改変/GUID 破損(停止・出力なし)、XLSX 上書き拒否と TestOnly exit 3(コード確認)
  - 詳細: `異常系テスト/異常系テスト結果_開発用PC_20261013.md`
- テスト後の復元: ImportExcel 264/264 ハッシュ一致、マーカー改変なし、正本スクリプトと一致
- 発見事項: 復元時のエディタ保存で psd1 ハッシュが変わる(BOM付加)。**バイナリ正本からコピー復元+SUMS全件照合が必須**

## 未実施(結合テスト計画書.md の環境C)

- 環境C: LNB 端末での本番相当収集、異常系(junction/マーカー改変/XLSX 上書き拒否)
- **前提: スクリプト署名(組織の手順)。**ImportExcel は環境Bと同じ手順で端末側 USB へ配置

## ファイル

| ファイル | 内容 |
| --- | --- |
| `Collect_LNB.ps1` | 収集スクリプト本体(V-1 修正済み、版 6.5-review) |
| `LNB_Collector_v6.5-review.zip` | 配布用一式(SHA-256: 73d4e4d7fe5efe216b53476d6f62bf713cf44c34f4130e51c1cc760f07227c75) |
| `MANIFEST_SHA256.txt` | 同梱ファイルのハッシュ一覧 |
| `regression_test.ps1` | 回帰テストハーネス。**環境A専用、本番USBに配置しない** |
| `結合テスト計画書.md` | 環境A/B/C 3段階の結合テスト計画(v1.0) |
| `回帰テスト計画.md` / `回帰テスト結果_20261013.md` | 回帰テストの計画と結果 |

## 次のアクション

1. ~~ImportExcel 7.8.10 の調達(IT承認手続き)~~ **完了(2026-10-13、静的レビュー+マルウェアスキャン通過、USB配置済み)**
2. ~~環境Bテスト(結合テスト計画書 §9-2)~~ **完了(2026-10-13、全項目合格)**
3. スクリプト署名(組織の手順)— 環境Cの前提
4. 環境Cテスト(§9-3、実LNB端末)
5. 合格後に L1/L2/L3 へ展開、結果を LNB 管理手順書へ反映
