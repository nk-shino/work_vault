# BOSS計画.xlsm 解析成果物

## 概要

| 項目 | 内容 |
|---|---|
| 解析対象 | `Work_Vault/10_業務全般/TOOL改修問題/BOSS計画.xlsm`（原本・変更禁止） |
| 解析日 | 2026-10-15 |
| 解析方式 | 静的解析のみ（Excel起動なし・VBA実行なし）。zip/XML直読み + Python(openpyxl/pandas) + olevba 0.60.2 |
| 目的 | TOOL改修検討に向けた現行仕様の把握（容量計算ロジック・データフロー・データ品質リスクの明確化） |

## 対象ファイル実在性

- パス: `C:\Users\ss80751\OneDrive - NK\ドキュメント\Work_Vault\10_業務全般\TOOL改修問題\BOSS計画.xlsm`
- サイズ: 1,814,805 bytes ／ 更新: 2026-10-15 10:50:35
- SHA-256: `266AEDE59C68D43D916A7F82D2243B596DB0716C47502A5ED870173A5345D043`

## 関係文書

- 要件: 同フォルダ `20261008_TOOL容量確認_要件メモ.md`（フィーダースロット搭載容量の確認ニーズ。3ノズル90／その他300／全体390、x=0.8安全率、PartList未登録部品の過小評価、履歴記録なし）
- 関連仕様: `Work_Vault/10_業務全般/Job作成/容量確認とJob構成_TOOL.xlam仕様.md`（しきい値90/300/390の裏付け）

## 成果物一覧

```
20261015_BOSS計画解析/
├── README.md            … 本ファイル（全体案内）
├── design/
│   ├── system_design.md … シート構成・VBA仕様・データフロー・外部依存の設計ドキュメント
│   └── data_flow.mmd    … Mermaid データフロー図ソース
├── dictionaries/
│   ├── sheets_dictionary.md … 20シート辞書（役割・構造・保持内容）
│   └── procs_dictionary.md  … VBAプロシージャ辞書（25件・引数・副作用・呼出関係）
├── tests/
│   └── test_report.md   … 検証結果判定表（静的検査12項目PASS／動的テストBLOCKED）
├── evidence/            … 解析証跡（構造レポート・VBA全ソース・Power Query M式ほか）
│   ├── vba_code_all.txt     … olevba抽出 VBA全1,765行
│   ├── pq_extract/Formulas_Section1.m … Power Query M式3件
│   └── （structure_report.txt / sheets_detail*.txt / keys_check.txt /
│       boss_deep.txt / pattern_check.txt / formulas_detail.txt / pq_check.txt）
└── manifest/
    └── manifest.json    … 成果物・ハッシュ・実行環境一覧
```

## 主要な結論（要約）

1. **容量計算の本体は `Cal_Capa`（MainModule.bas）**。`部品リスト.accdb`（egproBOM × PartList）を ADO で照会し、`90 - 3ノズルヘッド容量`, `300 - それ以外容量` の残スロットを返す。しきい値は要件メモの 90/300/390 と一致。**安全率0.8は本関数には無く、時間計算 `chkTime` の `x/3600/0.7`（＝稼働率0.7）に相当する概念が別に存在**。
2. **PartList未登録部品は INNER JOIN で落ちる**ため、要件メモ指摘の「過小評価（容量0扱い）」はコード上確認された（`Cal_Capa` の SQL は `filteredBOM INNER JOIN PartList`）。
3. **BOSSシート10,171行の指図データ**はタイプ `^(LA|ZP1\d|ZP2\d)$` かつ非KVのみが計算対象。±730日フィルタで削除。基準終了日<基準開始日の指図が16行存在（データ品質リスク）。
4. **計算シートの列構成はVBAが動的生成**（固定グループシート＋試作シート＋設備停止予定のヘッダから列名を収集）。「計算」は値専用シートであり、`Main` 実行のたびに全再構築される。
5. **休日データは2026-12-31まで**。2027年の祝日未登録。`mail` プロシージャは祝日テーブルに未来日が無いと警告するのみで、Mainの休日判定（CountIF）は2027-01-01以降は土日のみ適用になる。
6. **壊れた参照・未使用コード**: Cal_Fee が参照する `Sheet_PB`（有鉛DBシート）はブックに存在せず、`Cal_Fee_btn` は実行時エラー424で停止する（使用停止モジュール）。定義名に `#NAME?` の残骸、_FilterDatabase に `カスタム設定!#REF!`・`組取り数!#REF!`。
7. **セキュリティ**: 計算シート図形テキストに指図ファイル取得用の資格情報が平文で埋め込み済み（本成果物ではマスク表記）。VBAはパスワード保護あり。リポジトリPrivate維持の継続が必要。
8. **動的テストは未実施**（VM・隔離環境なし、Excel起動しない方針）。静的検査12項目で代替し、判定表 `tests/test_report.md` に記載。

## 注意事項

- 本解析は読み取り専用であり、原本xlsmは変更していない。
- evidence 内にはサーバ名・DB名・テーブル名を含むが、認証情報は保持していない（マスク確認済み）。
- `BOSS計画.xlsm`・`部品リスト.accdb`・`指図情報全データ.xlsx` は実データを含むため、本成果物フォルダには一切複製していない。
