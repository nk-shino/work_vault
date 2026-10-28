---
type: note
phase: operate
status: active
project:
updated: 2026-10-27
---

# BOSS計画.xlsm VBAプロシージャ辞書

解析日: 2026-10-15 ／ 根拠: evidence/vba_code_all.txt（olevba 0.60.2 抽出・全1,765行）

## プロシージャ一覧（25件）

| # | モジュール | 種別 | 名前 | 公開 | 概要 |
|---|---|---|---|---|---|
| 1 | MainModule | Sub | Main(Optional Flag_Skip=False) | Public | 本体。クエリ更新→日程修正→フィルタ削除→タイプ絞込→日付×グループ工数計算 |
| 2 | MainModule | Function | chkTime(D_CycleTime, D, D_Sisaku, D_kumitori) | Private | グループ内品目の生産時間計算。戻り値 `"量産h,NotFound,試作h"` |
| 3 | MainModule | Function | Cal_Capa(D) | Private | スロット容量照会。戻り値 `"90-3N残,300-その他残,NonHit,トレイ数,部品数"` |
| 4 | MainModule | Function | Cal_Duplicate(FirstStr, SecondStr) | Private | 2品目のBOM共通/専用スロット数。戻り値 `"共通,専用"` |
| 5 | MainModule | Sub | getBOSS_btn | Public | 容量計算シート: 指定日のBOSS品目をA:Cへ展開＋時間計算（独自実装）＋グループ順ソート |
| 6 | MainModule | Sub | Cal_Capa_btn | Public | 容量計算シート: 選択A列の品目でCal_Capa実行→I4/I6/I8/O4へ表示 |
| 7 | MainModule | Sub | Cal_Capa2_btn | Public | 容量計算シート: A列全品目の使用スロット一括計算→D/E列(3Nzl/4Nzl) |
| 8 | MainModule | Sub | Cal_Dup_btn | Public | 容量計算シート: 選択範囲の品目間BOM重複→専用Slot数と効率(E=専用/共通?→RC[-2]/RC[-1])でソート表示 |
| 9 | MainModule | Sub | mail(ManualSendFlag=False) | Public | 祝日チェック→Outlook下書き→A10:N75画像貼付→Send（手動フラグ時は表示のみ） |
| 10 | MainModule | Sub | ImportBOSS(Optional Flag_Skip=False) | Public | BOSS_Formatコピー→指図xlsx全貼付→Param!A2更新 |
| 11 | MainModule | Sub | saitekika | Public | Mainの絞込部分のみ（±730日+タイプ/KV削除）を再実行 |
| 12 | MainModule | Sub | Custom | Public | カスタム設定L:Oの品目をBOSS末尾へ `'000000000` 指図で仮追加 |
| 13 | MainModule | Function | Cal_Tray(D) | Private | グループ品目のトレイ部品数をADO照会 |
| 14 | MainModule | Sub | openMacro | Public | TOOL.xlam を ReadOnly で開く |
| 15 | MainModule | Sub | 一週間ちょい分のフリーとる | Public | job作成P列へ 明日+2～14日分のフリー/L1試作時間を getBOSS_btn ループで追記 |
| 16 | MainModule | Sub | すべて更新 | Public | RefreshAll のみ |
| 17 | MainModule | Sub | RPA_Main | Public | 連携.txt="Start"出力→連携_msg.txt="OK"ポーリング→ImportBOSS→Main |
| 18 | Msg.frm | Sub | UserForm_Initialize | Private | 画面右下へ配置 |
| 19 | Msg.frm | Sub | UserForm_QueryClose | Private | ×で計算自動化戻し＋「中断」＋End（強制終了） |
| 20 | Job_Class | Sub | setHinmoku(val) | Public | 品目を内部Dictionaryへ追加 |
| 21 | Job_Class | Function | getCapa() | Public | **空実装**（未完成） |
| 22 | Sheet_Junbi | Sub | Reflection_Junbi | Public | XLOOKUP値化＋当日行選択。Main末尾から呼ばれる |
| 23 | Sheet_Junbi | Sub | Worksheet_Activate | Private | シートアクティブ時に当日行選択 |
| 24 | CalFee | Function | Cal_Fee(D) | Public | ノズル>1000判定の容量計算。**Sheet_PB不在で実行時エラー424** |
| 25 | CalFee | Sub | Cal_Fee_btn | Public | 選択A列でCal_Fee実行（壊れ） |

## 呼出グラフ

```
RPA_Main ──→ ImportBOSS ──→ Main
Main ──→ chkTime / Cal_Capa / Cal_Tray / Sheet_Junbi.Reflection_Junbi
getBOSS_btn ──→ (chkTime相当を内蔵・独立実装)
Cal_Capa_btn ──→ Cal_Capa
Cal_Capa2_btn ──→ Cal_Capa (品目毎)
Cal_Dup_btn ──→ Cal_Duplicate (N×N回)
Cal_Fee_btn ──→ Cal_Fee (不可・Sheet_PB不在)
一週間ちょい分のフリーとる ──→ getBOSS_btn (14回)
すべて更新 ──→ RefreshAll
```

## 副作用まとめ

| 系統 | 内容 |
|---|---|
| ファイル | `部品リスト.accdb` を `%TEMP%` へコピー（3関数で同一処理の重複実装）。ImportBOSSは指図xlsxをReadOnlyで開く |
| ネットワーク | ADO/ACE OLEDB 16.0 による SMBパス上のAccess照会（adModeRead） |
| シート書込 | 計算/トレイ/容量計算/BOSS(日程修正・Custom追加)/Param/準備工数(値化) |
| Outlook | mail: CreateItem→表示→WordEditor貼付→Send |
| RPA | `RPA\ロボット(本番)\全指図情報\連携.txt` / `連携_msg.txt` のファイルハンドシェイク（Shift-JIS ADODB.Stream） |
| アプリ状態 | Calculation Manual↔Automatic、ScreenUpdating、Msgフォーム（×で End 強制終了） |

## 埋込定数

| 定数 | 値 | 場所 |
|---|---|---|
| 対象タイプ正規表現 | `^(LA|ZP1\d|ZP2\d)$` | Main / saitekika |
| KV除外 | 品目名が `KV` で始まる | 同上 |
| データ保持幅 | ±730日 | 同上 |
| 段取時間 | 600秒/品目 | chkTime / getBOSS_btn |
| 仮CT | 56秒(量産)/75秒(試作) | 同上 |
| CT下限 | 28秒 | chkTimeコメント（実クリップはPQ側） |
| 稼働率 | 0.7 | `÷3600÷0.7`（chkTime・getBOSS_btn共通） |
| 平日固定停止 | 1.75h × L1/L2/L3 | Main 日付ループ末尾 |
| スロット上限 | 90(3N)/300(その他) | Cal_Capa / Cal_Fee / Cal_Capa2_btn |

## 未使用・壊れている要素

- `Cal_Fee` / `Cal_Fee_btn`: `Sheet_PB`（有鉛DBシート）がブックに存在しない → 実行時エラー424。過去版の残骸。
- `Job_Class.getCapa`: 空実装。`Job_Class` 自体の使用箇所なし（将来拡張用）。
- Main 内の MsgBox 分岐・トレイ質問は全てコメントアウト（flag/flag2 固定 True）。
- カスタム設定 L:O「日程追加」の WorkDay ループはコメントアウト（Custom は1行だけ単純追加）。
- `Sheet1`/`Sheet6` 等の空シートクラス、_FilterDatabase の #REF! ×2、定義名 #NAME? 残骸。
