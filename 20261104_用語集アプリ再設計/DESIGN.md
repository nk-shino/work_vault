---
version: alpha
name: 社内用語集アプリ（辞書編集室）
description: 朱は、人の手が入ったところにだけ刷る。自動判定の辞書の上に、人の判断だけを朱で刻む三色体系（墨・緑青・朱）。
---

# 社内用語集アプリ — DESIGN.md

`03_デザイン設計書.md`（2026-11-04）を DESIGN.md 形式へ変換したもの。トークンが規範値で、本文は適用の文脈を示す。実装済みプロトタイプ（`prototype/`）の CSS 変数と突き合わせて作成し、設計書 §4.2 とプロトタイプの微妙な差（読みの文字寸・h1・clamp の vw）はプロトタイプの実値を採った。出典と検証の記録は `04_出典対応表.md` を参照。

## 2026-11-06 適用差分（DeAI改修 Phase 2・3）

2026-11-05 の監査（`20261105_用語集アプリDeAI改修/02_デザイン監査と改修案.md`）に基づく改修を適用した。この節の記載が、本文の規範値・未決事項と矛盾するときはこの節が優先する。実装の正本は `06_Tools/用語集アプリ/src/glossary/web/static/style.css`。

### 確定した変更（実測で確認済み）

- **書体**: 明朝 2 書体（見出し語・定義）を廃止し、Noto Sans JP 可変フォント（woff2 4,350,080 バイト・OFL.txt 同梱・`/static/fonts/` から自己配信）の単一書体にした。`--font-ui`（Noto Sans JP）と `--font-mono`（Consolas）だけを残す。letter-spacing 0.04em / 0.3em と【】の括りは廃止。外部通信は発生しない
- **暗テーマ**: トークンを作り直した（`--paper: #2b2f36`・`--surface: #33383f`・`--surface-2: #3c424a`・`--ink: #e8e6df`・`--muted: #a8adb8`）。本文の `paper-dark: #191b1f` 等の値は廃止。muted と surface-2 の組合せは 4.51:1
- **角丸**: card 8px / field 6px / chip 4px。pill（999px）は廃止
- **間隔**: `--space-1`〜`--space-7` = 4 / 8 / 12 / 16 / 24 / 32 / 48 px（4px グリッド）
- **動き**: モーショントークン（`--dur-*`・`--ease-*`）とパターン M-01〜M-11 は全部廃止した。CSS の transition・animation は 0。`html { scroll-behavior: smooth }` のみを残し、`prefers-reduced-motion: reduce` では auto にする。共有要素遷移（`view-transition-name`）は使わない
- **機能（Phase 3）**: 一覧の既定並びは読み順（昇順。読みの無い語は末尾に置き、その中で見出し順）。関係の表示は読み出し時に向きを反転する（broader↔narrower、abbrev_of↔「略語」、related・synonym・confused_with は対称）。関係を登録するときの操作は変更なし

### 未決の整理

- 設計書 §4.2・未決 7（OFL フォントの同梱）は「同梱する」で確定
- CSV 出力の状態・関係ラベルの日本語化は未決（利用者の確認待ち）

## Overview

社内の用語を登録・評価・見直すローカル業務アプリ。外部接続なし・ログインなし。使う人は用語の登録者と評価者。体験の目標は「引く速さ」（索引・共有要素遷移）と「手応え」（朱印・即時フィードバック）。

視覚言語は三層。

- **紙と墨**（和紙白＋墨）: 辞書の地。本文・定義・表。動かない規律
- **緑青**: 構造と導線。リンク・フォーカス・進行。押せるところ・進むところ
- **朱**: 人の手。評価・採用・訂正・混同注意。自動生成には刷らない

原則（詳細は設計書 §2）: 辞書の組版（明朝の見出し語・行間 1.9 の定義）を完成させる。朱は人の手に限る。引く操作はどの画面からでも 2 キー以内（`Ctrl+K`・`/`）。状態は帯と badge で示し、トーストや幕は作らない。`j/k/a/r/x` のキーボード完結（入力欄では無効）。動きは意味の変化にだけ付ける。新 API は全部機能検出つきの段階的強化。

動きの実装はネイティブ API のみ。GSAP 等のライブラリは同梱しない。Web フォントは Noto Sans JP 可変フォント（OFL）を同梱して自己配信する（「2026-11-06 適用差分」を参照）。明暗テーマは OS 設定への自動追従のみ。

## Colors

明テーマが規範。括弧内は主要組合せのコントラスト比の実測値（設計書 §4.1）。暗テーマは `prefers-color-scheme` で自動切替され、`-dark` 接尾のトークンへ差し替わる。

- **paper `#f8f7f2`（和紙）**: 画面の地。surface はカード・表・入力の白
- **ink `#26282e`（墨）**: 本文。paper 上 13.7:1。muted は補足文字で 5.7:1
- **primary（緑青 `#14685b`）**: リンク・フォーカス・進行。paper 上 6.2:1。roku と同値
- **shu（朱 `#b23a24`）**: 人の手の色。評価・採用・訂正・混同注意。paper 上 5.6:1、白文字 5.96:1。破壊的操作と混同注意の縁は shu-strong `#8f2a1c`（7.8:1）
- **kuchi（黄）・matsu（緑）**: 保留・注意と、確定・成功の帯・badge。文字は bg 上で 5.7:1 / 5.5:1

朱の意味規律は明暗で変わらない（暗テーマでは明るい口紅色 `#f08a72` に調整するが「人の手」の用法は同じ）。

```yaml
colors:
  primary: "#14685b"
  paper: "#f8f7f2"
  surface: "#ffffff"
  surface-2: "#f1efe8"
  ink: "#26282e"
  muted: "#5c6270"
  line: "#d8d5ca"
  line-soft: "#e7e4da"
  roku: "#14685b"
  roku-strong: "#0f544a"
  roku-soft: "#e7f1ee"
  shu: "#b23a24"
  shu-strong: "#8f2a1c"
  shu-soft: "#f9ebe7"
  kuchi-fg: "#7a5a00"
  kuchi-bg: "#fbf1d8"
  kuchi-border: "#e3cd93"
  matsu-fg: "#1f6e46"
  matsu-bg: "#e8f3ea"
  focus-ring: "rgba(20,104,91,.25)"
  paper-dark: "#191b1f"
  surface-dark: "#1f2126"
  surface-2-dark: "#26282e"
  ink-dark: "#e8e6df"
  muted-dark: "#9aa0ab"
  roku-dark: "#7cc8b4"
  shu-dark: "#f08a72"
  kuchi-fg-dark: "#e0b45c"
  kuchi-bg-dark: "#332a17"
  matsu-fg-dark: "#7cc89b"
  matsu-bg-dark: "#1d3326"
```

暗テーマの kuchi・matsu は現行の暗テーマ値の流用（設計書 §4.1）。`line`・`line-soft`・`roku-soft`・`shu-soft` の暗テーマ値は実装時に確定する（未決）。

## Typography

見出し語・定義・UI は同一の書体（Noto Sans JP 可変フォントを同梱して自己配信する。2026-11-06 適用差分を参照）。以下の yaml は 2026-11-04 時点の規範値の記録で、実装は適用差分節が優先する。

- **見出し語**: 明朝 weight 700・letter-spacing 0.04em。詳細ヒーローは `clamp(1.9rem, 3.4vw, 2.4rem)`（トークンは上限 2.4rem を記録）＋【】の括り。一覧のセルは 1.08rem
- **読み**: UI 書体・muted・1rem・letter-spacing 0.3em（プロトタイプ実値。設計書 §4.2 の 0.92rem を置換）
- **定義**: 明朝・1.1rem・行間 1.9（現行維持）
- **本文**: UI 書体・1rem・行間 1.65。h1 は 1.4rem
- **数値**: tabular-nums（健全性ストリップ・件数・更新日）

```yaml
typography:
  hero-headword:
    fontFamily: '"Yu Mincho", "YuMincho", "Hiragino Mincho ProN", serif'
    fontSize: 2.4rem
    fontWeight: 700
    letterSpacing: 0.04em
  headword-cell:
    fontFamily: '"Yu Mincho", "YuMincho", "Hiragino Mincho ProN", serif'
    fontSize: 1.08rem
    fontWeight: 700
    letterSpacing: 0.04em
  hero-reading:
    fontFamily: '"Yu Gothic UI", "Meiryo UI", "Segoe UI", sans-serif'
    fontSize: 1rem
    letterSpacing: 0.3em
  h1:
    fontFamily: '"Yu Gothic UI", "Meiryo UI", "Segoe UI", sans-serif'
    fontSize: 1.4rem
    letterSpacing: 0.02em
  definition:
    fontFamily: '"Yu Mincho", "YuMincho", "Hiragino Mincho ProN", serif'
    fontSize: 1.1rem
    lineHeight: 1.9
  body:
    fontFamily: '"Yu Gothic UI", "Meiryo UI", "Segoe UI", sans-serif'
    fontSize: 1rem
    lineHeight: 1.65
  hint:
    fontFamily: '"Yu Gothic UI", "Meiryo UI", "Segoe UI", sans-serif'
    fontSize: 0.85rem
  numeric:
    fontFamily: '"Segoe UI Variable Text", "Yu Gothic UI", "Meiryo UI", sans-serif'
    fontFeature: tnum
  mono:
    fontFamily: 'Consolas, "Courier New", monospace'
```

## Layout

4px グリッドの間隔基準。左サイドバーは作らず、上部ナビ 5 項目（用語一覧・提案キュー・見直し・用語を登録・CSV出力）＋数値バッジ。本文幅は `main` 60rem を維持。

語義カードは ≥1000px で 2 カラム（定義本体＋評価右列 22rem）、未満で縦積み。一覧→詳細は見出し語の共有要素遷移（`view-transition-name: hw-<term_id>`）でつなぐ。

```yaml
spacing:
  sp-1: 4px
  sp-2: 8px
  sp-3: 12px
  sp-4: 16px
  sp-5: 24px
  sp-6: 32px
  content-width: 60rem
  sense-aside-width: 22rem
```

## Elevation & Depth

影は 2 段階のみ。階層の基本は面の色（paper → surface → surface-2）と罫線。hover での浮き上げ（常時運転の elevation 変化）は作らない。

- 静置（カード・ヒーロー・表・stamp の既定）: `0 1px 2px rgba(32, 32, 40, .05), 0 1px 6px rgba(32, 32, 40, .06)`
- 浮き（popover・dialog）: `0 6px 16px rgba(32, 32, 40, .14)`

暗テーマでは影を強める（`0 1px 2px rgba(0,0,0,.3), 0 1px 6px rgba(0,0,0,.25)` / `0 6px 16px rgba(0,0,0,.45)`）。

## Shapes

角丸は 3 種。badge・チップ・評価ボタン（stamp）は pill。入力・小部品は 6px、カード・表・帯は 10px。

```yaml
rounded:
  sm: 6px
  md: 10px
  pill: 999px
```

## Components

部品の規律: ヘッダーの上罫は緑青単色。badge は色＋文字併記（点は ::before）で色単独では状態を伝えない。評価ボタン（stamp）は丸形で、押下すると朱に染まりスタンプの応答（M-05）がある。混同注意帯は朱の縁＋斜線地。成功帯は `role=status`。パレット・キーボードヘルプは `<dialog>`。当たり面積は ≥24px（WCAG 2.2 AA 2.5.8）。

```yaml
components:
  header:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    borderColor: "{colors.roku}"
  health-strip:
    backgroundColor: "{colors.surface-2}"
    textColor: "{colors.ink}"
  link:
    textColor: "{colors.roku}"
  link-hover:
    textColor: "{colors.roku-strong}"
  reading:
    textColor: "{colors.muted}"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    boxShadow: "0 1px 2px rgba(32, 32, 40, .05), 0 1px 6px rgba(32, 32, 40, .06)"
  popover:
    backgroundColor: "{colors.surface}"
    rounded: "{rounded.sm}"
    boxShadow: "0 6px 16px rgba(32, 32, 40, .14)"
  dialog:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.md}"
    boxShadow: "0 6px 16px rgba(32, 32, 40, .14)"
  stamp:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    borderColor: "{colors.line}"
    rounded: "{rounded.pill}"
    padding: "0.22rem 0.8rem"
  stamp-hover:
    backgroundColor: "{colors.roku-soft}"
    textColor: "{colors.roku-strong}"
    borderColor: "{colors.roku}"
  stamp-stamped:
    backgroundColor: "{colors.shu}"
    textColor: "#ffffff"
  stamp-stamped-hover:
    backgroundColor: "{colors.shu-strong}"
    textColor: "#ffffff"
  badge:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    borderColor: "{colors.line}"
    rounded: "{rounded.pill}"
  badge-caution:
    backgroundColor: "{colors.kuchi-bg}"
    textColor: "{colors.kuchi-fg}"
    borderColor: "{colors.kuchi-border}"
  badge-success:
    backgroundColor: "{colors.matsu-bg}"
    textColor: "{colors.matsu-fg}"
  band-success:
    backgroundColor: "{colors.matsu-bg}"
    textColor: "{colors.matsu-fg}"
    rounded: "{rounded.sm}"
  band-caution:
    backgroundColor: "{colors.kuchi-bg}"
    textColor: "{colors.kuchi-fg}"
    borderColor: "{colors.kuchi-border}"
    rounded: "{rounded.sm}"
  band-confusion:
    backgroundColor: "{colors.shu-soft}"
    textColor: "{colors.shu-strong}"
    borderColor: "{colors.shu-strong}"
    rounded: "{rounded.sm}"
  input-field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    borderColor: "{colors.line}"
    rounded: "{rounded.sm}"
  input-focus:
    borderColor: "{colors.roku}"
```

`boxShadow` と `borderColor` は本形式の部品プロパティの定義外のため、lint で warning が出る（値は Elevation & Depth 節と各部品の規律が正）。`-dark` 接尾のトークンは `prefers-color-scheme` での差し替え用で、部品からは参照しない。`focus-ring` は入力・リンクの `:focus-visible` の外暈に使い、`line-soft` はヒーローカードの罫に使う。

## Motion

DESIGN.md 形式に時間のトークン群はないため、モーションの規範値はこの節に記録する（CSS 変数として実装）。パターンの詳細・出典・削る順序は設計書 §7・§8。

### モーショントークン

| トークン | 値 | 用途 |
|---|---|---|
| `--dur-1` | `100ms` | 押下応答（stamp・ボタン）。入力応答の上限 |
| `--dur-2` | `180ms` | hover・popover・小さな開閉 |
| `--dur-3` | `260ms` | パレット・ページ遷移・帯の登場。主要遷移の基準 |
| `--dur-4` | `420ms` | タイムラインの線の成長（スクロール駆動） |
| `--ease-out` | `cubic-bezier(0.22, 1, 0.36, 1)` | 出現・入場 |
| `--ease-inout` | `cubic-bezier(0.65, 0, 0.35, 1)` | 共有要素遷移（往復で対称） |
| `--ease-stamp` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | stamp の跳ね（小さな要素限定） |
| stagger | `calc(var(--i) * 30ms)`・最大 6 項目・合計 ≤180ms | 検索結果の順次出現 |

### 振付の規則

1 場面 1 焦点。動かすのは opacity と transform（例外は CSS アンカー配置の位置決めのみ）。動きの間も入力を受け付ける（幕を作らない）。View Transitions 有効時は `main` の rise を二重運転しない。

### パターンと reduced-motion の代替

| ID | パターン | reduce 時 |
|---|---|---|
| M-01 | 共有要素遷移（見出し語） | `navigation: none`＋通常遷移 |
| M-02 | 検索結果の stagger | 遅延なし・即時表示 |
| M-03 | 関連語ホバープレビュー | 即時表示 |
| M-04 | コマンドパレット | 即時表示 |
| M-05 | 朱印（評価のスタンプ） | 色変化のみ |
| M-06 | キュー裁定の状態遷移 | フェードなし・即時 |
| M-07 | 履歴タイムラインの朱線 | 線を最初から全表示 |
| M-08 | 数値カウントアップ | 即時最終値 |
| M-09 | 成功帯の登場 | 即時表示（帯は出る） |
| M-10 | ページ入場 | なし（即時） |
| M-11 | busy 表示 | 静的表示 |

reduce では「止めて情報を失う」のではなく「同じ情報を即時に」示す。M-01・M-05・M-09 は性能予算超過時も最後まで維持する（削る順序は M-07 → M-02 → M-08）。

## Do's and Don'ts

- Do 朱は評価・採用・訂正・混同注意（人の手）にだけ使う。AI 草案・自動採用・統計の関係など自動生成には使わない
- Do 色・トークンはこの文書のトークン経由で使い、画面ごとの直値を作らない
- Do badge・評価状況点・diff は文字（併記・title/sr-only・＋/− 記号）でも状態を伝える
- Do reduced-motion では動きを全停止し、同じ情報を即時に提示する
- Don't hover での浮き上げ・漂い・パララックス・1 文字ずつのテキストリビールなど、装飾的な常時運転を作らない
- Don't 読み込み幕・全画面オーバーレイ・トーストを作らない。処理中は busy 表示、結果は帯で示す
- Don't GSAP・Anime.js 等のライブラリと画像を同梱しない（外部依存ゼロ。Web フォントは Noto Sans JP のみ）
- Don't 見出し語の文言を壊す（テストの文言回帰リスト 155 件がある）
