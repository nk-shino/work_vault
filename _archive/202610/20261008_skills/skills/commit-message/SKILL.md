---
name: commit-message
description: Write commit messages and PR descriptions following Conventional Commits. Use when the user asks to commit ("コミットして"), create a PR ("PR作って"), or asks to improve a commit/PR message. Also use proactively whenever committing changes on the user's behalf.
---

# コミットメッセージ / PR 作成

## コミットメッセージ (Conventional Commits)

形式:

```
<type>(<scope>): <subject>

<body>

<footer>
```

- **type**: `feat`(機能追加)/ `fix`(バグ修正)/ `refactor`(動作を変えない変更)/ `test` / `docs` / `style`(フォーマット)/ `perf` / `chore`(ビルド・工具)/ `ci` / `revert`
- **scope**: 影響範囲(モジュール名、機能名など。任意)
- **subject**: 何をしたか 50 文字以内目安。体言止めまたは動詞で簡潔に。文末にピリオドを付けない
- **body**: なぜその変更が必要か(what は diff が語るので、why を書く)。行は 72 文字以内目安
- **footer**: `BREAKING CHANGE:` や `Refs #123` などの補足

### 例

```
fix(auth): トークン更新時の競合で複数リフレッシュが走る問題を修正

リフレッシュ要求が並行すると複数のリクエストが発行され、
一部が無効化済みトークンで失敗していた。
単一フライトパターンで更新を集約する。
```

## コミット実行時の手順

1. `git status`, `git diff`, `git log --oneline -10` を確認する
   - 直近のコミットメッセージのスタイル(言語、粒度)に合わせる
   - リポジトリに CONTRIBUTING.md やコミット規約があればそれを優先する
2. 変更を論理単位ごとに分けられるか検討する(無関係な変更を 1 コミットに混ぜない)
3. **意図したファイルだけ**をステージする。デバッグコードや秘密情報が混ざっていないか diff を見て確認する
4. `git commit` を実行する(Heredoc 形式で複数行メッセージを渡す)

## PR 作成

タイトルはコミットメッセージと同じ形式。説明には含める:

- **目的**: なぜこの変更か
- **変更内容**: 何をどう変えたか(箇条書き)
- **確認方法**: レビュアーが動作を確認する手順
- **スクリーンショット**: UI 変更の場合(before/after)

## 注意

- コミットや PR の作成はユーザーが明示的に依頼した場合のみ行う
- 秘密情報(API キー、パスワード、個人情報)をコミットに含めない
- `--no-verify` でフックをスキップしない
