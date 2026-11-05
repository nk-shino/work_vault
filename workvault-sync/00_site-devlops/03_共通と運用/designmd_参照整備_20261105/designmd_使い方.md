---
title: designmd_使い方
type: note
phase: organize
project:
created: 2026-11-05
updated: 2026-11-05
---

# design.md（DESIGN.md 形式）の使い方

DESIGN.md は、デザインシステム（色・タイポグラフィ・余白・部品のトークンと、その根拠）を 1 つの md ファイルに書き、エージェントやツールが参照できるようにする形式。Google Labs の `google-labs-code/design.md` が仕様と CLI を公開している（Apache-2.0・2026-11-05 時点で alpha）。

## このフォルダの中身

- `docs/spec.md`: 形式の仕様（原典のまま）。YAML フロントマターのトークン群と、固定順の本文節（Overview → Colors → Typography → Layout → Elevation & Depth → Shapes → Components → Do's and Don'ts）で構成する
- `examples/`: 使用例 3 件（atmospheric-glass / paws-and-paths / totality-festival）。いずれも DESIGN.md + Tailwind 設定の組
- `README.md`・`LICENSE`: 原典リポジトリのもの
- `package.json`・`package-lock.json`: CLI の導入定義（CLI 本体はここには入れない）

## CLI

CLI `@google/design.md`（v0.4.0）はワークスペース側 `20261105_design-md参照整備/` に導入済み。任意のフォルダで使うときは `npm install @google/design.md` する。

```bash
npx designmd lint <DESIGN.mdのパス>     # 構造・トークン参照・WCAG AA コントラスト等11種の検証
npx designmd spec                       # 仕様を標準出力へ（エージェントのプロンプトに渡す用途）
npx designmd diff <旧> <新>             # 2版の比較
npx designmd export <DESIGN.mdのパス> --format css-tailwind|json-tailwind|dtcg|css-vars
```

`export` の各形式: `css-tailwind` は Tailwind v4 の `@theme`、`json-tailwind` は v3 の `theme.extend`、`dtcg` は W3C Design Tokens。

## 用途の想定

用語集アプリの `03_デザイン設計書.md`（`06_Tools/用語集アプリ/_docs/用語集アプリ_再設計_20261104/`）を DESIGN.md 形式に起こし、`lint` で検証する。以後のデザイン改訂は DESIGN.md を正として管理する。
