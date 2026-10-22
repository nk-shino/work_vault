# BOSS計画.xlsm システム設計ドキュメント（静的解析によるリバースエンジニアリング結果）

解析日: 2026-10-15 ／ 方式: Excel起動なしの静的解析（OOXML直読み・olevba）

## 1. ブック全体構成

### 1.1 シート一覧（表示順 = zip内sheetN順、全20枚）

| # | シート名 | codeName | 表示 | 役割 |
|---|---|---|---|---|
| 1 | メンテナンスメモ | Sheet2 | 表示 | 修正履歴メモ（A1:C17） |
| 2 | 過去データ | Sheet6 | 表示 | 過去の計算結果保管（A:V 1,020行、2023-11-24～2026-09-30） |
| 3 | トレイ | Sheet_Tray | 非表示 | Cal_Tray結果出力先（Mainがクリア→再生成） |
| 4 | 準備工数 | Sheet_Junbi | 表示 | 計算シートのXLOOKUP引用＋準備工数パラメータ（r3定数） |
| 5 | 容量計算 | Sheet_Cal2 | 表示 | スロット容量計算UI（getBOSS_btn等の操作先） |
| 6 | 計算 | Sheet_Cal | 表示 | Main のメイン出力先（日付×グループの工数マトリクス） |
| 7 | 設備停止予定 | Sheet_tenken | 表示 | 停止時間の入力（A:L 261行）。Mainが列6以降のヘッダを列名として収集 |
| 8 | カスタム設定 | Sheet_Custom | 表示 | 日程変更(A:D)/日程追加(L:O)/指図指定日程変更(R:S) |
| 9 | 試作 | Sheet_Sisaku | 表示 | 試作品目→グループ割当・固定時間・組取り数 |
| 10 | ←の使い方 | Sheet4 | 表示 | 試作シートの説明 |
| 11 | Param | Sheet_Param | 非表示 | ImportBOSSの取得日時記録（A2=46310.31→2026-10-15 07:31） |
| 12 | BOSS_Format | Sheet_BOSS_Format | 非表示 | ImportBOSS時の書式テンプレート（値なし・書式のみ） |
| 13 | job作成 | Sheet_Job | 表示 | 「一週間ちょい分のフリーとる」の出力先（P列14行目以降） |
| 14 | BOSS | Sheet_BOSS | 表示 | 指図データ本体（A:O 10,171行）。ImportBOSSで全置換 |
| 15 | 祝日 | Sheet_Holiday | 表示 | 祝日リスト（71件、最終2026-12-31） |
| 16 | メール | Sheet_Mail | 表示 | 日報メールのHTML組版（グラフ19枚含む） |
| 17 | グループ | Sheet_Group | 表示 | 品目→グループ対応（Power Query「固定グループ」の取り込み先） |
| 18 | サイクルタイム | Sheet_CycleTime | 表示 | PQ「CycleTime (集計用)」取り込み先（1,269行） |
| 19 | 組取り数 | Sheet_Kumitori | 表示 | PQ「組取り数」取り込み先 |
| 20 | 列設定 | Sheet_CalumSetting | 表示 | 計算シートの強制列順（A1:D44・鹿島品目日程変更ラベル領域と同居） |

### 1.2 ブック設定

- calcId=191028、1904日付システム無し（標準シリアル）
- 定義名: mail関連に `#NAME?` 残骸、_FilterDatabase に `カスタム設定!#REF!`・`組取り数!#REF!` の壊れた参照
- Webアドイン: NKAI_* カスタム関数（taskpane。計算ロジックとは無結合）

## 2. Power Query（3クエリ・3テーブル）

接続先の詳細は evidence/pq_extract/Formulas_Section1.m 参照。資格情報はM式内に平文保持（クエリ認証ダイアログ保存）だが本書ではマスク。

| クエリ | 取込先 | 接続先 | 集約ロジック |
|---|---|---|---|
| CycleTime (集計用) | サイクルタイム!テーブル | ODBC MySQL (nksv1359 / DB=QCD) | CycleTime_Points を typeID 毎に最新10件（両面は5件ずつ合算）、cycleTime<28は28へ下限クリップ後平均 |
| 組取り数 | 組取り数!テーブル | ODBC MySQL (nksv1359 / DB=scheduled) | unitInfo.chldID が単一要素のもの（`",%"` かつ `",%,%"` 以外）を抽出しカンマ除去→数値化 |
| 固定グループ | グループ!テーブル | Access マスタ.accdb (nksv523/SMT_Schedule2) | 固定グループテーブル全件 |

## 3. VBA プロジェクト構成

- 参照ライブラリ: stdole / Office16 / **ADODB 6.1** / Scripting / VBScript RegExp 5.5 / **Outlook 16.0** / MSForms 2.0
- プロジェクト保護: あり（CMG/DPB/GC設定。ソースは可読）
- 実装モジュール: `MainModule.bas`（本体・行19–1358）、`CalFee.bas`（行1533–1722・**壊れモジュール**）、`Sheet_Junbi.cls`、`Job_Class.cls`（getCapaは空実装）、`BUHIN_Class.cls`、`Msg.frm`（進捗表示＋×ボタンで中断=計算自動化戻し＋End）
- その他シートクラスは全て `Option Explicit` のみ

### 3.1 プロシージャ一覧（25件）

詳細は `dictionaries/procs_dictionary.md`。主要経路:

```
[ボタン]
計算シート: Main / ImportBOSS / RPA_Main
容量計算シート: getBOSS_btn / Cal_Capa_btn / Cal_Capa2_btn / Cal_Dup_btn
job作成シート: openMacro / 一週間ちょい分のフリーとる

[内部関数]
chkTime(D_CycleTime, D, D_Sisaku, D_kumitori) → "量産h,NotFound,試作h"
Cal_Capa(D) → "残3N,残other,NonHit,cnt_Tray,BUHINSU"   ← ADO(ACE16.0, adModeRead)
Cal_Duplicate(First,Second) → "共通Slot,専用Slot"        ← ADO
Cal_Tray(D) → トレイ部品数                                ← ADO
Cal_Fee(D) → 同Cal_Capa形式                              ← Sheet_PB不在で実行不可

[RPA連携]
RPA_Main: 連携.txt に "Start" 出力 → 連携_msg.txt が "OK" になるまでポーリング
  → ImportBOSS(True) → Main
```

### 3.2 Main の処理順序（行26–483）

1. `Application.Calculation = Manual` ／ Sheet_Cal.Activate ／ B1以降全クリア
2. 試作DB・組取数DBをDictionary化
3. `Msg` フォーム表示（進捗用・モードレス）→ `ThisWorkbook.RefreshAll`（PQ更新）
4. **日程修正**: カスタム設定A:C（品目|変更前日→変更後日）でBOSS N列を上書き。R:S（指図指定）も同様（2重ループ O(BOSS×Custom)）
5. **±730日フィルタ削除**: AutoFilter Field14 で `<=Now-730` or `>=Now+730` を SpecialCells.Delete
6. **最適化**: タイプが `^(LA|ZP1\d|ZP2\d)$` 以外、または品目が `KV*` の行を Union→一括削除
7. **D_Day構築**: key=計算シートA列の表示文字列（.Text）→ val=Dictionary(品目→L列数量合計)。BOSS N列の値を CStr したキーで突合（jaロケールで書式 yyyy/mm/dd と一致する前提の**書式依存結合**）
8. 計算シート列生成: 固定列(日付/DBにBOM無し/DBにサイクルタイム無し/フリー容量/フリー部品種類数/フリー) → 列設定シート → 試作シートのグループ → グループシート → 設備停止予定のヘッダ（列6以降）。全て表示形式 `0.00"h"`
9. Sheet_Tray をクリア→骨組みコピー
10. サイクルタイムDB構築（重複時は警告ラベル・上の行優先）
11. 日付ループ: D_Dayの品目をChkGroupでグループ振り分け→グループ毎に `chkTime`（量産時間/サイクルタイム無し一覧/試作時間）。先頭グループがフリー/試作系なら `Cal_Capa` を呼びフリー容量・BOM無し・トレイ・部品種類数を記録
12. 平日のみ L1/L2/L3停止時間 +1.75h（祝日CountIF or 土日で除外）
13. `Sheet_Junbi.Reflection_Junbi`（XLOOKUP値化＋当日行選択）→ 計算自動化戻し → 「完了」MsgBox

### 3.3 時間計算仕様（chkTime）

| 条件 | 式 |
|---|---|
| サイクルタイムDBあり | `数量 × CT + 600(段取10分)` |
| DBなし・組取り数あり | `数量 ÷ 組取り数 × 56(量産)/75(試作) + 600` |
| DBなし・組取り数なし | `数量 × 28 + 600`（★付きで未命中一覧へ） |
| 試作品 | 上記に加え `+600` ＋ 試作シートの固定時間(C列)を別途加算 |
| 共通 | `合計秒 ÷ 3600 ÷ 0.7`（**安全率相当=0.7稼働率**。要件メモの x=0.8 とは値が異なる） |

※ getBOSS_btn は Main と同一式だが独立実装（「★★★時間計算はこのプロシージャ独自なので超注意」のコメントあり）。

### 3.4 容量計算仕様（Cal_Capa / Cal_Fee）

- DB: `\\nksv523...\Job作成\部品リスト.accdb` を `%TEMP%` へコピー（更新日時不一致時のみ再コピー）し ACE OLEDB 16.0 adModeRead で照会
- Cal_Capa: `egproBOM`(品目→部品, DISTINCT) INNER JOIN `PartList`（部品名）
  - `三ノズルヘッド=1` のフィーダーサイズ合計 → `90 − 合計` が3ノズルヘッド残スロット
  - `三ノズルヘッド=0` の合計 → `300 − 合計` がその他残スロット
  - トレイ部品数 / BOM登録部品数 も返却
  - **INNER JOINのためPartList未登録部品は除外**（過小評価の根拠）
- Cal_Fee: ノズル番号>1000を3N判定、フィーダーサイズは `テープ幅` 列使用。**`With Sheet_PB`（存在しないシート）で実行時エラー424** → 本モジュールは過去実装の残骸と判定

## 4. データフロー（data_flow.mmd 参照）

```
指図情報全データ.xlsx (nksv523)
  └─ ImportBOSS ─→ BOSSシート(全置換) ─→ Main(日程修正/フィルタ/タイプ絞込)
                                            ↓
MySQL QCD ─PQ─→ サイクルタイム ┐
MySQL scheduled ─PQ─→ 組取り数   ├─→ chkTime ─→ 計算シート(日付×グループ工数)
Access マスタ.accdb ─PQ─→ グループ ┘              │
試作シート ─────────────────────────┘              ├─→ 準備工数(XLOOKUP) ─→ メール(グラフ) ─→ Outlook送信
部品リスト.accdb ─ADO─→ Cal_Capa ─→ 容量計算/計算シートのフリー容量列
```

## 5. 既知の問題・リスク（静的検査で確認済み）

| ID | 種別 | 内容 | 影響 |
|---|---|---|---|
| R-01 | データ | BOSS 基準終了日<基準開始日 16行 | 日程修正・日付突合の取りこぼし候補 |
| R-02 | データ | 過去データ列名「送信機L2」vs 計算「送信機_L2」 | 過去データの列対応が手動前提 |
| R-03 | データ | サイクルタイム重複 typeID 3件（URS-4558/URS-4559/UR-0610-03） | 上の行優先で計算継続（警告表示のみ） |
| R-04 | データ | 祝日テーブル最終 2026-12-31 | 2027-01-01以降、Mainの休日判定は土日のみ |
| R-05 | 構造 | Cal_Fee が Sheet_PB 参照で実行時エラー | Cal_Fee_btn は使用不可（残骸コード） |
| R-06 | 構造 | 準備工数 #N/A 6,802セル/179行（r1378–1556=2027-04-01以降） | 計算シート範囲(2026-10-01～2027-03-31)外の先行数式。表示上のノイズ |
| R-07 | 結合 | D_Day突合が .Text（表示書式 yyyy/mm/dd）と CStr(Value) の比較 | OSロケール・書式変更で結合破綻する隠れ依存 |
| R-08 | 性能 | 日程修正の2重ループ O(BOSS×Custom) | データ増加時にMainが遅延 |
| R-09 | セキュリティ | 図形テキストに平文資格情報・PQ接続に資格情報保存 | マスク必須。Private運用継続 |
| R-10 | 一貫性 | グラフ参照範囲が計算!$A$2:$A$92 の**92行固定** | 計算シートは183行あり、グラフは約3ヶ月分のみ表示 |
| R-11 | 構造 | カスタム設定A1:D44 に「鹿島品目日程変更」ラベルが同居、列設定シートと領域重複 | 列順変更時の混線リスク |
| R-12 | 構造 | _FilterDatabase #REF! ×2、定義名 #NAME? | ファイル健全性の軽微な劣化 |
