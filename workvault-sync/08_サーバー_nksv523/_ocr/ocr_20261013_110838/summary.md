# OCR 抽出結果サマリ

- 実行日時: 2026-10-13 11:08:56
- 入力CSV: C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\08_サーバー_nksv523\_inventory\scan_20261013_110718\inventory.csv
- 台帳行数: 337 行
- 対象件数: 12 件 (OCR 実行)
- 成功件数: 12 件
- スキップ件数: 325 件 (office-embedded-not-supported: 220 件 / pdf-not-supported: 35 件 / too-small: 3 件 / unsupported-extension: 67 件)
- エラー件数: 0 件
- マスク行数: 0 行
- 出力先: C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\08_サーバー_nksv523\_ocr\ocr_20261013_110838
- OCR 言語: ja

## 備考
- 完全ローカル処理・外部送信なし (WinRT OCR のみ使用)
- 入力元 (台帳 CSV・画像) には書き込んでいない
- PDF は Poppler 未導入のため非対応 (skipped.csv に reason=pdf-not-supported で一覧化)
- Office 埋め込み画像は非対応 (reason=office-embedded-not-supported)
- 機微キーワードを含む行は [REDACTED] に置換済み (内容は redactions.csv にも記録しない)