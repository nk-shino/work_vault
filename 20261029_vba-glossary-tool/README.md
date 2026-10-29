# VBA 学習辞書

Excel ブック内の VBA コードを解析し、プロシージャごとに「語義カード」を作る学習アプリ。
社内用語集アプリ（`C:\work\用語集アプリ`）と同じ設計型に乗っている。

- プロシージャ = 用語項目。名前・種類（Sub/Function/Property）・引数・呼び出し元・呼び出し先・タグを自動で拾う
- 語義と用例は最初は空。解析が「提案」として下書きを出し、利用者が受理して初めて語義になる
- 語義は後から修正できる。修正には理由が必須で、変更はすべて履歴に残る
- 物理削除は全面禁止。データベーストリガーとアプリ層の二重防壁で拒否する
- 評価（correct / needs_fix / unsure × useful / not_useful）を付けた語義は「見直し」画面に集まる

## 起動まで

```powershell
# 初回のみ
python tasks.py setup

# マイグレーション（DB が無ければ作る）
python tasks.py migrate --db data/glossary.db

# 実物の解析（.xlsm は開かず、内部の VBA を取り出して解析する）
python tasks.py analyze "C:\path\to\ブック.xlsm" --db data/glossary.db

# 起動（ブラウザが開く）
python tasks.py serve --open
```

デモデータだけで試すなら `python tasks.py demo` のあと `python tasks.py serve --db data/demo/glossary-demo.db`。

## コマンド

| コマンド | 内容 |
|---|---|
| `setup` | venv 作成と依存導入 |
| `migrate` | Alembic マイグレーション（`--db` で切替） |
| `analyze <source>` | ブック（.xlsm/.xls）またはフォルダを解析して DB に投入 |
| `serve` | FastAPI を起動（`--port` `--db` `--open`） |
| `demo` | デモ用 DB を作成（fixtures/vba の架空モジュールを使用） |
| `test` / `lint` / `typecheck` / `check` | pytest / ruff / mypy / 3つ全部 |

## 画面

- `/` ホーム: 学習の進み具合（語義あり・なし・提案待ち）と次に開く項目の候補
- `/procedures` 一覧: キーワード・種類・モジュール・学習状態・タグで絞り込み
- `/procedures/{id}` 詳細: 語義カード（受理・差し戻し）、署名、呼び出し関係、用例、履歴
- `/procedures/{id}/code` コード全文: 解析時に書き出した `.bas` をそのまま表示（シンタックスハイライト付き）
- `/proposals` 提案キュー: 自動生成の下書きを1件ずつ確認
- `/review` 見直し: needs_fix 評価や同名混同の語義を集めて再編集
- `/history/{entity}/{id}` 履歴: 語義・提案の変更記録（追記専用）

テーマは右上のボタンで auto / light / dark を切り替える。auto は OS の設定に従う。

## 設計の決めごと

- **VBA 全文は DB に入れない。** 解析時に `export/{ブック名}/{モジュール}.bas` へ書き出し、コード表示はそこから読む
- **項目の同一性はブック名 + モジュール名 + プロシージャ名。** 再解析すると同じ項目を更新する（版が変わっても二重登録にならない）。ブックの sha は記録するが同一判定には使わない
- **受理ベース。** 自動動採用はしない（`config/adoption.yaml` で将来の切替に備える）。提案は受理・差し戻し・保留のいずれか
- **禁止情報のマスキング。** `config/masking_rules.yaml` に列挙した語が VBA 内に見つかると、その提案は保留になり、コード表示では一致部を ■ で塗る。語義文にも同じ規則を適用する
- **削除しない。** senses / proposals / evaluations / histories は追記または論理削除のみ。楽観ロック（version カラム）で同時編集を検知する
- **語義の書き込みは sense_writer.py 1か所。** UI も CLI もここを通る。理由なしの更新は ChangeReasonMissing で止まる

## 構成

```
src/vbaglossary/
  db/         models.py, session.py, guards.py（物理削除拒否・履歴自動記録）
  domain/     errors, sense_writer, proposals, evaluations, review, queries
  vba/        extract(oletools) → parse → mask → analyzer（提案生成）
  web/        app.py, templates/, static/（Jinja2 + 素の JS）
migrations/   Alembic（0001_baseline: 8表 + トリガー）
fixtures/vba/ デモ・テスト用の架空モジュール
config/       masking_rules.yaml, adoption.yaml
```

## 未決事項

- 語義の自動下書きは決まり文句ベース。LLM による語義案（用語集アプリで LiteLLM 連携済み）は次フェーズ
- CSV 出力は未実装
- adoption.yaml の自動採用モードは未検証（規定は off）
