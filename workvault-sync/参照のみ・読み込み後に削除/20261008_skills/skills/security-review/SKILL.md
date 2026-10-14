---
name: security-review
description: Security-focused code review based on OWASP Top 10. Use when reviewing code for security issues, when the user says "セキュリティ", "脆弱性チェック", "安全確認", when handling authentication/authorization/input-validation/file-upload/external-API code, or before releasing user-facing features. Also use proactively when writing code that processes untrusted input.
---

# セキュリティレビュー (OWASP Top 10 観点)

## 使い方

対象コードを以下の観点で順に確認し、指摘は「リスク + 該当箇所(file:line) + 修正案」で報告する。重大度(高/中/低)を付ける。

## チェックリスト

### 1. インジェクション (SQL / コマンド / LDAP など)

- [ ] SQL はプレースホルダ(パラメータ化クエリ)を使用しているか。文字列連結で組み立てていないか
- [ ] OS コマンド実行(`exec`, `spawn`, `subprocess` 等)にユーザー入力を渡していないか。渡す場合は引数配列 + シェル経由しない
- [ ] パス操作にユーザー入力を使う場合、`../` などのパストラバーサルを防いでいるか(パスの正規化とルート配下の検証)

### 2. 認証・認可

- [ ] 認可チェックはサーバー側で行っているか(クライアントだけに任せていないか)
- [ ] オブジェクト直接参照(IDOR): 他ユーザーのリソース ID を指定してアクセスできないか。所有者確認をしているか
- [ ] セッション・トークンの生成に安全な乱数を使っているか(`Math.random` や時刻ベースは不可)
- [ ] パスワードは専用ハッシュ(bcrypt / argon2 等)で保存しているか

### 3. 機密情報の取り扱い

- [ ] キー・トークン・接続文字列がコードやコミットにハードコードされていないか(環境変数やシークレット管理を使う)
- [ ] ログに機密情報(トークン、個人情報、パスワード)を出力していないか
- [ ] エラーメッセージに内部情報(スタックトレース、SQL、パス)をそのままユーザーに返していないか

### 4. XSS / 出力エンコーディング

- [ ] HTML にユーザー入力を埋め込む際、エスケープしているか(`innerHTML` への直接代入は特に注意)
- [ ] `dangerouslySetInnerHTML` 等の使用箇所でサニタイズしているか
- [ ] URL スキーム(`javascript:` 等)を検証しているか

### 5. CSRF / セキュリティ設定

- [ ] 状態を変更するエンドポイントに CSRF 対策があるか
- [ ] CORS 設定が過剰に寛容(`*` + 資格情報)でないか
- [ ] Cookie に `HttpOnly`, `Secure`, `SameSite` を設定しているか

### 6. その他

- [ ] ファイルアップロード: 種類・サイズの検証、保存先の実行権限除去
- [ ] 外部 API 応答をそのまま信頼していないか(検証してから使う)
- [ ] 依存パッケージに既知脆弱性がないか(`npm audit` 等で確認)
- [ ] レート制限・入力サイズ上限が必要なエンドポイントにあるか

## 報告形式

```
## セキュリティレビュー結果

### 高: <タイトル>
- 箇所: src/xxx.ts:42
- リスク: <何が起きうるか>
- 修正案: <具体的なコードまたは方針>
```

指摘ゼロでも確認した観点を簡潔に報告する。推測で断定せず、確認できたことと不明なことを区別する。
