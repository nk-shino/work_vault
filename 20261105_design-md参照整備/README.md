# 20261105_design-md参照整備

Google Labs の design.md（DESIGN.md 形式の仕様と CLI）を読み取り、参照・実行できる状態にした作業フォルダ。

## 保管したもの（`参照/design.md-repo/`）

- 出典: https://github.com/google-labs-code/design.md （2026-11-05 時点の main。ライセンスは Apache-2.0）
- `docs/spec.md`: DESIGN.md 形式の仕様（418 行）。YAML フロントマターのトークン群と、固定順の本文節（Overview → Colors → Typography → Layout → Elevation & Depth → Shapes → Components → Do's and Don'ts）で構成する
- `examples/`: 使用例 3 件（atmospheric-glass / paws-and-paths / totality-festival）。いずれも DESIGN.md + Tailwind 設定の組
- `packages/cli`: CLI のソース。実行には npm パッケージの方を使う

## CLI（`@google/design.md` v0.4.0）

このフォルダで `npm install` 済み。使い方:

```bash
npx designmd lint <DESIGN.mdのパス>     # 構造・トークン参照・WCAG AA コントラスト等の検証
npx designmd spec                       # 形式の仕様を標準出力へ（エージェントのプロンプトに渡す用途）
npx designmd diff <旧> <新>             # 2版の比較
npx designmd export <DESIGN.mdのパス> --format css-tailwind|json-tailwind|dtcg|css-vars
```

- `lint` の検証項目は 11 種（構造・トークン参照の破損・キーの誤記・WCAG AA 4.5:1 等）
- `export --format css-tailwind` は Tailwind v4 の `@theme`、`json-tailwind` は v3 の `theme.extend`、`dtcg` は W3C Design Tokens 形式

## 動作確認（2026-11-05）

- `npx designmd spec` で仕様が出力されることを確認
- `npx designmd lint 参照/design.md-repo/examples/atmospheric-glass/DESIGN.md` で warning 4 件（ガラス素材の半透明白背景に白色文字、コントラスト 1.00:1）が出ることを確認。ツールの正常動作の確認を兼ねる

## 用途の想定

`20261104_用語集アプリ再設計/03_デザイン設計書.md` の内容を DESIGN.md 形式に起こし、`lint` で検証する。以後、アプリのデザイン改訂は DESIGN.md を正として管理する。
