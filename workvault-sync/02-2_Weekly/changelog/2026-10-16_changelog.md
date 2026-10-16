# Changelog 2026-10-16

## 1. 鹿島引き込み: 差分確認マクロver2.3a.xlsm 分析一式を業務内容フォルダへ納品

- 実行日時: 2026-10-16
- 対象: `10_業務全般/鹿島引き込み/業務内容/`(新規フォルダ)・`00_inbox/Excelデータ設計分析方針.yaml`(spec: analyzed_excel_to_drawio v3.0)・`10_業務全般/鹿島引き込み/差分確認マクロver2.3a.xlsm`(読み取りのみ・未変更)
- 種別: 新規フォルダ作成(Tier B・ユーザー指示による承認済み)と成果物12ファイルの納品
- 内容:
  - 対象ブック16シートの値・数式・条件付き書式・VBA(vbaProject.bin復号・19モジュール)・図形画像2枚を解析。nksv523側コピーとの差分は BOM作成!B15 と Module1 p-code のみ。
  - 台帳4件: ledger_source.json(SRC-01..08・INS-01..08) / ledger_evidence.json(EV-001..027・CV-01..05) / ledger_graph.json(OBJ-01..14・REL-01..23・PG-01..04・インスタンス56) / ledger_issues.json(ISS-01..07)
  - draw.io 図4ページ: 差分確認マクロ分析.drawio(1_全体構成と目的 / 2_シート構成とデータ内容 / 3_参照と連携の流れ / 4_不整合と未確認事項)
  - プレビュー4枚: preview_p1..p4.svg(drawio2svg による実レンダリング)
  - 検証報告: validation_report.json(期待検査42件: PASS23 / BLOCKED16 / NA3 / FAIL0)
  - 利用案内.md(frontmatter type: report / phase: operate / status: active / project: 鹿島引き込み / updated: 2026-10-16)と manifest.yaml
- 保持したもの: 対象ブック・関連資料は一切変更していない(読み取りのみ)
- 未処理・要確認事項: final_status=verification_incomplete。draw.io desktop が本PCに無いため、幾何検査(重なり・線貫通)・アプリ再読込表示・図形移動の接続追従・人手視認の4検査が未実施。ユーザーが draw.io で開いて確認した時点で使用開始とすること。sabunシートは6/30以前のスナップショット(ISS-03)、BOM作成!B15 が2拠点で不一致(ISS-01)などの制約は 利用案内.md に記載。正本(スクリプト・台帳)はワークスペース 20261016_鹿島引き込みExcel分析/

## 記録

- decision-log 1行(2026-10-16・業務内容フォルダへの納品)
- 実行ログ: ワークスペース 20261016_鹿島引き込みExcel分析/実行ログ_20261016.md
