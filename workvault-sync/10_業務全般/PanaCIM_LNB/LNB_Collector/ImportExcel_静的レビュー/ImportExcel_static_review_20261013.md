# ImportExcel 7.8.10 静的レビュー報告

日付: 2026-10-13
実施: 開発用PC(Kohden Code)
対象: `C:\Users\ss80751\AppData\Local\Temp\kohden-code\ImportExcel\7.8.10`(PSGallery `Save-Module ImportExcel -RequiredVersion 7.8.10` で取得、264ファイル/3.6MB)

## 結論: 配置可(条件付き合格)

## 1. 真正性検証(すべて一致)

| 検証 | 結果 |
|---|---|
| PSGallery版 EPPlus.dll SHA256 | `C32CEFBD1EA051ED3AF06E7FB9DD558598A612F042164140CD8BE722A351BC63` |
| GitHub公式リリース v7.8.10 同DLL | **同一ハッシュ(一致)** |
| 公式NuGet EPPlus 4.5.3.2 net40ビルド | **同一ハッシュ(一致)** — 同梱DLLは正規の EPPlus **4.5.3.2**(LGPL)であることを確認 |
| モジュール全体 | 264ファイル分の個別SHA256を記録(下記参照) |

注: マニフェスト上の想定と異なり同梱 EPPlus は 4.5.3.2(4.5.3.3ではない)。いずれも LGPL 4.x 系でライセンス上の扱いは同じ。

## 2. 静的スキャン(212スクリプト、10カテゴリの危険パターン)

検出15件、うちモジュール本体で呼ばれ得るものはすべて正当な用途:

- `Public\Close-ExcelPackage.ps1` / `Compare-Worksheet.ps1` / `Convert-ExcelRangeToImage.ps1`: `Start-Process` は `-Show` スイッチ指定時のファイル表示のみ。Convert-ExcelRangeToImage は Excel COM 自動化(要Excelインストール、今回未使用)
- `Public\Get-HtmlTable.ps1`: `Invoke-WebRequest` による HTMLテーブル取得(今回未使用)
- `Examples\` 配下 9件: サンプルスクリプトで、モジュールインポート時には実行されない

未検出: 混淆(Base64実行/EncodedCommand)、セキュリティ回避(ExecutionPolicy変更/AMSI改変/MpPreference)、認証情報アクセス、永続化(スケジュールタスク/Runキー)、破壊的ファイル操作

## 3. インポート時動作(ImportExcel.psm1 61行)

- `ScriptsToProcess` / `NestedModules` / `RequiredModules`: なし
- トップレベル処理: ローカライズ文字列読込(`Import-LocalizedData`)と `Public`/`Private` のドットソーシングのみ。ネットワーク・プロセス起動なし

## 4. 今回の収集ツールでの使用範囲

`Export-Excel` / `Open-ExcelPackage` / `Close-ExcelPackage` のみ。ネットワーク系・COM系関数は呼ばない。

## 5. 記録したハッシュ

- 全ファイル個別: `ImportExcel_7.8.10_SHA256SUMS.txt`
- ツリー結合ハッシュ: `1a9f990b5f9388dd52d3f5227e86aee112c312c8d14341d71f333fcebd3b4efb`
- USB配置後に同じ SUMS ファイルで照合すること。

## 残作業(静的レビュー外)

- [ ] 社内マルウェアスキャン(配置前)
- [ ] OSSライセンス規程確認(EPPlus 4.5.3.2 = LGPL)
