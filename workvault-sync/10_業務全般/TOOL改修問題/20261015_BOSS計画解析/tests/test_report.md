# BOSS計画.xlsm 検証結果判定表

解析日: 2026-10-15 ／ 実行環境: Windows 11 ja-JP・Excel不使用・Python 3.13.15（openpyxl 3.1.5 / pandas 3.0.6 / oletools 0.60.2）

## 総合判定

| 区分 | 判定 | 件数 |
|---|---|---|
| 静的検査（PASS） | PASS | 12 |
| 静的検査（リスク検出） | WARN（仕様通り・要対処候補） | 12（design/system_design.md R-01～R-12） |
| 動的テスト（VBA実行・再計算） | **BLOCKED** | 全件 |

## BLOCKED の理由と代替

- 本PCにはVM・隔離環境が無く、「隔離された環境でのマクロ実行」条件を満たせない。
- 対象ブックは実指図データ・実DB接続（SMBパス）を持つため、実行テストは本番環境に副作用を与える恐れがある。
- 代替: OOXML直読み＋pandas検査＋olevbaによる全VBAソース静的解析でロジックを確定し、Mainの削除フィルタ等はPythonで等価再現して検証。

## 静的検査 明細（全て PASS）

| # | 検査 | 手段 | 結果 | 証跡 |
|---|---|---|---|---|
| 1 | ブック構造・20シート・表示状態・codeName | XML | 全シート列挙・コード名対応確定 | structure_report.txt |
| 2 | シート詳細（行列・数式数・ヘッダ） | openpyxl | 20枚分記録 | sheets_detail.txt / sheets_detail2.txt |
| 3 | BOSS指図キー一意性 | pandas | 指図列A 重複0 | keys_check.txt |
| 4 | BOSSタイプ分布・全行B020/PC | pandas | ZP21 7,212/LA 2,638/ZP12 128/ZP13 99/ZP11 94 | boss_deep.txt |
| 5 | BOSS日付整合 | pandas | 開始2024-10-16～2028-04-11、**終了<開始16行**（WARN=データ品質） | boss_deep.txt |
| 6 | 過去データ日付一意・欠け | pandas | 1,020行・重複0・欠け4 | keys_check.txt |
| 7 | 計算シート日付連続性 | XML | 182日・2026-10-01～2027-03-31・欠落0・重複0 | 本検証(再実行可) |
| 8 | Main削除フィルタの等価再現 | Python | 現行10,171行は全て±730日内→削除0対象 | pattern_check.txt |
| 9 | 準備工数 #N/A 分布 | XML | r1378–1556（2027-04-01以降・計算シート範囲外）のみ | formulas_detail.txt |
| 10 | Power Query M式展開 | DataMashup zip手動展開 | 3クエリ確定・接続先記録 | pq_check.txt / pq_extract/Formulas_Section1.m |
| 11 | VBA全量抽出と解析 | olevba 0.60.2 | 27ストリーム・25プロシージャ・参照ライブラリ7種確定 | vba_code_all.txt |
| 12 | 図形・コメント・グラフ・アドイン棚卸し | XML | 資格情報所在確定（マスク対象）・グラフ92行固定確認 | drawings_calc.txt / 本検証 |

## 等価再現検証の詳細（#7, #8 に対応）

- 計算シートA列: 182行連続（土日含む52日、値なし行は無し）→ Mainが全日付を処理対象にする。
- ±730日フィルタ: `基準終了日(N列) <= 今日-730 or >= 今日+730` を10,171行へ適用 → 0件。現時点で削除対象なし。
- D_Day突合: BOSS N列の表示形式 yyyy/mm/dd（numFmtId=176）と計算A列が同一書式 → jaロケールで結合成立（書式依存であることをR-07として記録）。
- カスタム設定 R:S の指図212131570はBOSS存在確認済み（1/1件）。

## 動的テスト計画（実施未遂・将来VMで実施する場合の項目）

| # | テスト | 期待結果 | 状態 |
|---|---|---|---|
| D-1 | Main実行 | 計算シート183日分再構築・列順が生成規則通り | BLOCKED |
| D-2 | getBOSS_btn（指定日） | A:C展開＋ソート順一致 | BLOCKED |
| D-3 | Cal_Capa_btn（既知品目選択） | I4/I6が実DB値と一致 | BLOCKED（実DB依存） |
| D-4 | Cal_Capa2_btn | D/E列=使用スロット。未登録品目は「DB未登録」 | BLOCKED |
| D-5 | Cal_Fee_btn | 実行時エラー424（Sheet_PB不在の裏取り） | BLOCKED |
| D-6 | Cal_Dup_btn（2品目） | 共通/専用スロット整合 | BLOCKED |
| D-7 | ImportBOSS | BOSS全置換・Param!A2更新 | BLOCKED（実ファイル上書き） |
| D-8 | RPA_Main | 連携ファイル生成・ハング挙動 | BLOCKED（RPA本番連携） |
| D-9 | mail | Outlook下書き生成 | BLOCKED |

## 回帰防止の再現手順

工作域 `kohden-code-workspace/20261015_BOSS計画解析/scripts/` の inspect_*.py 11本（inspect_structure / inspect_sheets / inspect_detail / inspect_keys / inspect_boss_deep / inspect_pattern / inspect_formulas / inspect_drawings / inspect_pq / extract_pq / inspect_charts）で全証跡を再生成可能。対象パスはスクリプト内に直書き（原本を変更しないRead Only運用）。
