## ゴール

成果物を保管庫へ配置するときの命名規約が rules.md に明文化され、vault-change-and-report スキルから参照されること。

## 受け入れ基準

- [x] rules.md に命名規約節が存在する（v1.3・2026-10-20）
- [x] 規約は実在ファイルの様式から帰納したものである（1,907 ファイル走査）
- [x] 旧版が rules_history/rules_v1.2.md に保存されている
- [x] vault-change-and-report スキルの登録ルールから命名規約が参照される
- [x] proposals.md の P-014 が承認・反映済みの状態になっている
- [x] work_vault へ同期済み（git ls-files で新規ファイルの追跡を確認）

## 既知情報

- [事実] rules.md v1.3 は 2026-10-20 にユーザー承認のうえ反映済み。命名は新規作成分のみ適用し、既存ファイルの改名は行わない
- [事実] 反映コミット: work_vault 6d8a2d3（vault-sync・差分5件）、ワークスペース実行ログ エントリ22（e75f389）
- [事実] 前例: P-010〜P-013 は GitHub issue #2/#3 で管理（rules.md 冒頭の記載）
