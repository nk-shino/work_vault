# Errors

## [ERR-20261014-001] vault-sync.ps1 git add -u

**Logged**: 2026-10-14T10:45:00+09:00
**Priority**: high
**Status**: resolved
**Area**: config

### Summary
vault-sync.ps1 の `git add -u` は新規ファイルを追跡せず、`workvault-sync/` 全体が .gitignore 配下のため新規フォルダ(PanaCIM_LNB 57件)が GitHub に反映されないまま同期が「完了」していた。

### Error
```
(エラー表示なし。robocopy は反映済み・git add -u は exit 0・push も成功と見える)
→ 実際は workvault-sync/10_業務全般/PanaCIM_LNB/ が git ls-files に存在せず、
  GitHub(nk-shino/work_vault) 上に同フォルダ一式が無い状態で「同期完了」と報告していた。
```

### Context
- 実行コマンド: `scripts/vault-sync.ps1`(タスクスケジューラと手動の両方)
- 原因: `git add -u` は「既に追跡中のファイル」の変更のみステージする。workvault-sync/ 全体が .gitignore(:2)配下のため、新規ファイルは gitlink または ignored となり取り込まれない
- 検知の遅れ: スクリプトが「差分 N 件」を status の追跡済み変更のみで数えており、新規欠落を検知する手段が無かった
- 初回同期(fb7e778)では `git add -A` が通ったが、9354afb の追跡方式変更時に `add -u` になり、以降の新規ファイルが全て欠落していた

### Suggested Fix
- スクリプト側: ミラー実ファイルと `git ls-files` のインデックスを突合し、新規を検出して `git add -f` で強制追加(2026-10-14 実装済み、commit 61ef3bc で検証)
- 除外条件: ネスト .git 作業ツリー/100MB超2ファイル/`__pycache__`・`*.pyc`・`.egg-info`・`.tmp.drive*`・`*.bkp`/glossary.db(実行時生成)
- 教訓: **「同期成功」の判定に追跡済み差分のみを使うと、ignored 配下の新規欠落は無音で通る。同期系スクリプトはファイル実数の突合で検証する**

### Resolution
- **Resolved**: 2026-10-14T10:40:00+09:00
- **Commit/PR**: 61ef3bc(改修後の初回同期、PanaCIM_LNB 等の残新規4件を取り込み)/ 強制反映分は cc9f369
- **Notes**: 改修の運用手順は `vault-sync` スキル(`~/.config/kohden-code/skills/vault-sync/SKILL.md`)として独立させ、AGENTS.md に起動条件を追記

---

## [ERR-20261014-002] drawio 置換の取り違えでラベルが %s のまま出力

**Logged**: 2026-10-14T17:40:00+09:00
**Priority**: medium
**Status**: resolved
**Area**: tooling

### Summary
前セッションの drawio 一括修正で、未確認データ箱3枚の置換元/置換先を取り違えた(PanaCIM_LNB_データフロー図.drawio)。`str.replace` は対象文字列が無くても無音で成功するため、ラベルが `【データ】%s` のまま PNG に書き出され、会議提示図でプレースホルダが露出するところだった。

### Error
```
PNG 図7 の未確認データ箱に「【データ】%s（取得元 要確認・…）」と表示
（正しくは 部品情報 / ノズルデータ / リーダーデータ）
```

### Context
- 原因: 置換パターンを「置換後の文字列」で書いており、元テキスト(`%s`)に一致しない無効な置換になっていた
- str.replace は不一致でも例外を出さないため、パッチ適用「成功」表示の後に静かに無効化されていた
- 検知: 次セッションで PNG を目視確認した際に %s を発見

### Suggested Fix
- 置換前に `s.count(old)` で出現数を検証し、期待件数と違えば中断する(適用前ガード)
- 置換対象が互いに同一文字列の場合(b_nozzle/b_reader が同文)は 1件ずつ順次 replace する
- XML パース後に `'%s' in values` のアサートを入れて露出を機械検出する

### Resolution
- **Resolved**: 2026-10-14(本セッション)。count 検証+順次 replace で修正し、XML アサートで `%s` 残留ゼロを確認。確定版は PanaCIM_LNB リポジトリ commit 39eec76
- **Notes**: Pattern-Key: `patch.silent-replace-miss`

---

## [ERR-20261014-003] BOM 無し UTF-8 の .ps1 を PowerShell 5.1 が ANSI 読みし日本語パスが文字化け

**Logged**: 2026-10-14T17:40:00+09:00
**Priority**: medium
**Status**: resolved
**Area**: tooling

### Summary
画像クロップ用 .ps1(write ツールで出力・BOM 無し UTF-8)を Windows PowerShell 5.1 で実行したところ、ファイル内の日本語パスが ANSI(Shift-JIS)として解読されて文字化けし、FromFile が FileNotFoundException で失敗した。

### Error
```
System.Drawing.Image.FromFile : FileNotFoundException
（パス表示が「ドキュメンチEW…」等に崩壊）
```

### Context
- 実行: `powershell -NoProfile -ExecutionPolicy Bypass -File crop_png.ps1`
- 原因: PowerShell 5.1 は BOM 無しスクリプトをシステム ロケール(ANSI)で読む。UTF-8 の日本語が崩れる。PowerShell 7 は BOM 無し UTF-8 前提のため発生しない

### Suggested Fix
- 日本語を含む .ps1 は先頭に UTF-8 BOM を付けて保存する(または ASCII のみで記述する)

### Resolution
- **Resolved**: 2026-10-14(本セッション)。Python で先頭へ BOM(\xef\xbb\xbf)を追加して再実行し、クロップ成功
- **Notes**: Pattern-Key: `ps1.encoding-bom`

---

---

## [ERR-20261015-001] Excel COM の Workbook.Close/Quit が OLE error 0xe0000002 で不定期失敗

**Logged**: 2026-10-15T12:30:00+09:00
**Priority**: medium
**Status**: resolved
**Area**: tooling

### Summary
Excel COM(gencache.EnsureDispatch)でブック編集後の `wb.Close(SaveChanges=False)` や `app.Quit()` が `-536870910 (OLE error 0xe0000002)` で不定期に失敗する。Save 自体は成功していることが多く、後続の Quit も連鎖して例外になる。

### Error
```
pywintypes.com_error: (-536870910, 'OLE error 0xe0000002', None, None)
→ try/finally の Quit も (-2147352567) で失敗し、EXCEL.EXE が残プロセス化
```

### Context
- 発生: build_step7_cover.py・fix4.py・export_pdf 内(2026-10-15 管理手順書案作業)
- 条件: 同一セッションで複数ブックを開閉した後に出やすい

### Suggested Fix
- Close/Quit は try/except で包み、失敗しても Save 済みなら処理を継続する
- 残プロセスは `tasklist` で PID を特定し `Stop-Process -Id <PID>` で掃除(名前での kill は禁止)
- PDF 出力など 1 ブックだけの処理は別プロセス(別 python 実行)に分けると安定する

### Resolution
- **Resolved**: 2026-10-15(本セッション)。fix4.py は Save 済みだったことを openpyxl で確認後、残った EXCEL.EXE(PID 12888)を Stop-Process -Id で終了。PDF 再出力はスクリプトファイル化+別プロセス実行で成功
- **Notes**: Pattern-Key: `excel-com.ole-close-fail`

## [ERR-20261015-002] git add -A が Temp 配下の作業物を追跡に含めた

### Context
- 発生: 実行ログ追記後の `git add -A && git commit`(2026-10-15 保管庫整理セッション)
- 条件: workspace ルート直下に `AppData/Local/Temp/kohden-code/` が実フォルダとして存在し、`.gitignore` が未設定だった

### Suggested Fix
- コミット前に `git status` と `git show --stat` で混入を確認する
- kohden-code の一時フォルダは pre-approved の `C:\\Users\\ss80751\\AppData\\Local\\Temp\\kohden-code` を使う(workspace 内に作らない)

### Resolution
- **Resolved**: 2026-10-15(本セッション)。`git rm -r --cached AppData` + `.gitignore` に `AppData/` を追加して再 push(b63d292)。機微情報なし
- **Notes**: Pattern-Key: `gitadd.temp-inclusion`

## [ERR-20261016-001] Playwright での SVG 目視確認時、http.server がポート競合で既存サーバーと衝突した

### Context
- 発生: 負荷計算drawio再レンダリング後の Playwright 目視確認(2026-10-16)
- 条件: `python -m http.server 8941` を2重起動した(1つ目は curl 000 で失敗と誤認)。既存の 8931(PID 16124)も前セッションから未回収で残存

### Suggested Fix
- 起動前に `netstat -ano | grep <port>` で使用中を確認
- 停止時は `netstat` で PID を特定し `Stop-Process -Id <PID>`(名前での kill は禁止)
- curl が 000 を返すときは localhost ではなく 127.0.0.1 で再試行(IPv6 解決の失敗)

### Resolution
- **Resolved**: 2026-10-16(本セッション)。8941の二重起動分(22844/25948)と本セッション分(11468/6544/23248/27036)を PID 特定のうえ停止。8931(PID 16124)は前セッション由来のため今回未処理
- **Notes**: Pattern-Key: `httpserver.port-conflict`

## [ERR-20261020-001] 同一チェックアウトでの並行セッションにより、コミット済みファイルが作業ツリーから削除された

### Context
- 発生: サイト改善タスクのテスト再実行中(2026-10-20 17:43 頃)
- 条件: 別セッション(glossary-app)が同一ワークスペース・同一ブランチ(feature/site-mockup-reference)で作業しており、提案ページモックの16ファイルが作業ツリーのみ削除された(履歴は無事)。同セッションは「削除可能ファイルの削除」を記録する運用をしており、それに巻き込まれたと推定
- 症状: http.server が当該ディレクトリの html を全て 404 で返す(listdir にはディレクトリのみ見える)。最初はキャッシュやサーバー起動方法を疑い、切り分けに時間を要した

### Suggested Fix
- 異常時はまず `git status --short` で作業ツリーの意図しない削除を確認する(サーバーやキャッシュより先に)
- 複数セッションで同一チェックアウトを触らない。触る場合は作業前に `git status` と `git log --oneline -3` を確認し、終了時にブランチを報告する
- 復元は `git restore -- <path>`(HEAD に履歴がある間は即復旧可能)

### Resolution
- **Resolved**: 2026-10-20(本セッション)。`git restore -- 20261016_site-design-improvement/提案ページモック` で復元(`git diff 16147f7 HEAD` = 空で内容一致を確認)。再スイープ 39/39 PASS。ユーザーへ並行セッションの注意を報告済み
- **Notes**: Pattern-Key: `session.concurrent-checkout-fileloss`

---

## [ERR-20261021-001] OneDrive保管庫の追跡済み5ファイルが消失し、定期同期が削除をコミット

**Logged**: 2026-10-21T12:10:00+09:00
**Priority**: high
**Status**: resolved(再発防止は未実施)
**Area**: vault-sync

### Summary
`06_Tools/用語集アプリ` の追跡済み5ファイル(propose.py・tasks.py・proposals.html・proposal_edit.html・test_self_improvement.py)が、10/20 17:31 同期(936f176)から 10/21 08:57 同期(29c3dc8)の間に Vault フォルダから消えた。タスクスケジューラの vault-sync が削除をそのままコミット・push し、GitHub 上からも一時的に消えた。

### Error
```
(エラー表示なし。sync は「差分 14 件」を正常処理。削除5件は差分に混ざって通知されない)
→ GitHub 上で propose.py 等が削除済みコミットになる。アプリは壊れていない(C:\work の実行コピーは無傷)
```

### Context
- 消失原因は未確定(OneDrive 側。98_Pass 消失(10/09)に続き2件目の無説明消失)
- 作業コピー `C:\work\用語集アプリ` に同一内容(LF/CRLF違いのみ)が残っていたため復元できた
- 対応: C:\work から5ファイルを復元 → 手動同期 f255663 で再追加・push → `git ls-files` で追跡確認

### Suggested Fix
- vault-sync.ps1 に「追跡済みファイルの削除が N 件(例:3)を超えたら DryRun 停止・本人確認」のガードを入れる
- 消失の一次原因は OneDrive 側のため、pending.md D節の「98_Pass 消失」と同じ調査線(意図的/同期不具合の切り分け)に統合する

### Resolution
- **Resolved**: 2026-10-21T09:00:00+09:00(復元・push・検証済み。commit f255663)
- **Notes**: 同期の削除ガードは未実装。次回 vault-sync 改修時に起票すること
---

## [ERR-20261021-002] 最新指示状態を確認せずに「復元基準」で修復し、L2再追加作業を取消した

**Logged**: 2026-10-21T15:10:00+09:00
**Priority**: high
**Status**: resolved
**Area**: kajima-pullin / verification

### Summary
全データ監査(指示30)で検出した「比較ファイルのL2ブロック残存・version7の行29痕跡」を不整合と判断し、指示28の復元状態を正として Teamsコピー上書き+クリアを実施。その後、実行ログに指示29(2件目: L2情報の再追加)が存在し(コミット済み・完了報告済み)、監査修復がその成果を取消していたことが判明。l2_values_v2.json+バックアップから再構築して回復。

### Error
```
監査結果: 比較ファイル≠Teamsコピー(md5不一致) → 「L2痕跡=不整合」と誤判定
→ 誤った基準での復元を実施 → 指示29(2件目)のL2ブロックが消滅
```

### Context
- 引き継ぎサマリに指示29(2件目)の記載がなく、監査開始時に実行ログの末尾を精査していなかった
- 指示29(2件目)の自己検証も不完全で(versionファイル側の値未書込を見逃し)、ログの記述だけでも状態を確定できなかった
- 回復手段: l2_values_v2.json(全桁値)+backup_L2_20261020(構造・書式の正)+監査前実測値の三点照合で再構築基準を確定

### Suggested Fix
- 監査・修復系タスクでは、監査基準の決定前に実行ログの全エントリ(特に同一日付の後発エントリ)を確認して「最新の指示状態」を確定する。履歴がある場合、後発の指示が先行状態を置換した可能性を必ず検討する
- 引き継ぎ時は実行ログの末尾エントリ(未コミット含む)をサマリに必ず写す

### Resolution
- **Resolved**: 2026-10-21T15:10:00+09:00(指示30エントリで経緯記録・指示29(2件目)に訂正注記・再構築+監査ALL PASS)

## [ERR-20261021-003] Excel COMのNumberFormat設定で日本語ロケール表記とバックスラッシュ処理を誤り、書式を破損保存した

**Logged**: 2026-10-21T15:10:00+09:00
**Priority**: medium
**Status**: resolved
**Area**: kajima-pullin / Excel COM

### Summary
セル書式「#,##0.0;[Red]\-#,##0.0」を再現するため COM に `[Red]` 表記と `\-(バックスラッシュエスケープ)` を渡したところ、(1) `[Red]` は日本語ロケールの Excel でエラー、(2) `[赤]\-…`(バックスラッシュ付き)は保存時に `#,##0.0;[Red]"¥"\-#,##0.0` と¥通貨記号が混入して破損。

### Error
```
ws.Range('I31').NumberFormat = '#,##0.0;[Red]\-#,##0.0'   → エラー
ws.Range('I31').NumberFormat = '#,##0.0;[赤]\-#,##0.0'    → 保存後 '#,##0.0;[Red]"¥"\-#,##0.0'(¥混入)
```

### Context
- 正しい手順: 格納形式(XML)の `[Red]` を `[赤]` に置換し、`\-` を `-` に置換した文字列を設定する
  `#,##0.0;[赤]-#,##0.0` を設定 → 保存時に `#,##0.0;[Red]\-#,##0.0` へ自動正規格納(検証済み・バックアップと完全一致)
- 同セッションで長時間のCOM処理中にセグフォルトが発生し、途中保存の中途状態(値86セル+破損書式)が残った。残存ExcelはPID指定で特定・停止(名前一括停止は禁止)

### Suggested Fix
- Excel COMでセル書式を設定する場合は、格納形式文字列を `replace('[Red]','[赤]').replace('\-','-')` して渡し、保存後にopenpyxlで格納形式を検証する
- COMの例外後はゾンビインスタンスの有無を `Get-Process EXCEL` で確認し、PID指定で停止する

### Resolution
- **Resolved**: 2026-10-21T15:10:00+09:00(全ファイルの書式がバックアップと完全一致で再構築済み・破損書式の残存なし)

## [ERR-20261021-004] pywin32からPivotFieldの日付グループ化(Range.GroupのPeriods配列)がExcelに届かず「ｸﾞﾙｰﾌﾟ1」になる

**Logged**: 2026-10-21T17:30:00+09:00
**Priority**: medium
**Status**: resolved
**Area**: kajima-pullin / Excel COM(ピボット)

### Summary
ピボットの日付フィールドを年/月にグループ化するため `DataRange.Group(Start=True, End=True, Periods=(F,F,F,F,T,T,T))` を実行したところ、エラーにはならないが結果が常に「ｸﾞﾙｰﾌﾟ1」のラベルグループ化になる。Periods配列のみがExcelに渡っていない。

### Error
```
df.DataRange.Group(Start=True, End=True, Periods=(False,False,False,False,True,True,True))
→ 行ラベルが「ｸﾞﾙｰﾌﾟ1」(引数なしGroupと同じ挙動)
```
named引数・位置引数・明示`VARIANT(VT_ARRAY|VT_BOOL, [...])`・makepy型付きディスパッチ(gen_py再構築後)・新規ブック+クリーンな日付データ、のすべてで再現。

### Context
- 解決策: Group()を呼ばない。グループ化済みピボットを含むシート(ver3)を丸ごと複製し、`PivotTable.ChangePivotCache(ローカルキャッシュ)`+`RefreshTable()`でデータ源だけ差し替える。グループ化(月/年/日付フィールド)・フィールド構成・スタイルが完全に保持され、月行は新しいデータに自動再構成される
- 注意: 同一PivotCacheオブジェクトを2つのピボットへ連続適用すると2個目がE_INVALIDARGで失敗する。ピボット毎に個別キャッシュを作成する
- 判別: 行ラベル先頭に「ｸﾞﾙｰﾌﾟ1」が出たら失敗。「2026年/8月…/総計」が出たら成功

### Suggested Fix
- pywin32でピボットの日付グループ化が必要な場合は、Group()を使わず「グループ化済みピボット付きシートの複製+ChangePivotCache」を使う
- ChangePivotCacheは対象ピボット毎に個別のPivotCacheを作成して渡す

### Resolution
- **Resolved**: 2026-10-21T17:30:00+09:00(上記方式でL1=A3:H12/L3=A17:D26の実ピボットを構築・監査ALL PASS)

## [ERR-20261021-005] 日本語ExcelのCOMでNumberFormat='General'が1004エラーになる

**Logged**: 2026-10-21T17:30:00+09:00
**Priority**: medium
**Status**: resolved
**Area**: kajima-pullin / Excel COM(書式)

### Summary
`Range.NumberFormat = 'General'` を設定すると「Range クラスの NumberFormat プロパティを設定できません」(1004)で失敗。日本語ロケールのExcelではNumberFormatプロパティ=ロケール依存文字列のため、標準書式は 'G/標準' を渡す必要がある。

### Error
```
ws.Range('I10').NumberFormat = 'General'  → 1004 例外
ws.Range('I10').NumberFormat = 'G/標準'   → OK(保存後の格納は 'General' に正規化)
```

### Context
- エラーが特定のセルでなく全'General'設定で発生するため、セル側ではなく書式文字列側の問題と切り分けた(時間書式・0%は同一セルで成功)
- openpyxlで読むと 'General' として格納されているため、検証はopenpyxl側で行う

### Suggested Fix
- Excel COMで標準書式を設定する場合は `'G/標準'` を使用する(英語ロケール環境で動かす可能性があるならNumberFormatLocalの利用も検討)

### Resolution
- **Resolved**: 2026-10-21T17:30:00+09:00(ヘッダ/総計行の書式入れ替えを完了・監査ALL PASS)

## [ERR-20261021-006] シート複製方式でテンプレ側のL2ブロックが一緒にコピーされ、既存領域を上書きした

**Logged**: 2026-10-21T17:30:00+09:00
**Priority**: high
**Status**: resolved
**Area**: kajima-pullin / Excel COM(ピボット)

### Summary
ver3シート(グループ化済みピボット+L2ブロック行29-39を含む)を集計シートとして複製した結果、L2ブロックがテンプレ側の値(丸め値・月行7ヶ月構成)で上書きされた。指示30で監査済みの正しいL2ブロック(全桁値・6ヶ月構成)と不一致。

### Error
```
複製後の集計B30=468.4684(テンプレver3由来・丸め値) ≠ バックアップB30=470.6017203968255(監査済み正値)
差分34セル(行30-39・B-E列中心)
```

### Context
- 発見: 構築後検証で「バックアップ(構築前静的版)とのセル単位比較」を実施したことで検出(ピボット本体の検証だけでは見逃していた)
- 修正: バックアップから行29-39×A-Oの165セルを復元(数式はFormula、値はValueで設定)→再計算後、数式とcached値の両方でバックアップと完全一致
- 教訓: テンプレシート複製で目的領域以外(既存ブロック)も一緒に来る。複製後は「意図外領域=バックアップと完全一致」の検証を必ず行う

### Suggested Fix
- シート複製を使う構築では、複製前に「テンプレとターゲットの非共通領域」を洗い出し、複製後にバックアップ突合で意図外差分ゼロを検証する

### Resolution
- **Resolved**: 2026-10-21T17:30:00+09:00(L2ブロック復元済み・最終統合検証+通し監査ALL PASS)

---

## [ERR-20261022-001] 検証用証跡ファイルが書き込み成功後に消失し、diff結果が無効化された

**Logged**: 2026-10-22T11:45:00+09:00
**Priority**: high
**Status**: mitigated(根本原因未確定・並行セッションを疑う)
**Area**: session / kohden-code-workspace

### Summary
BOSS計画.xlsm 再検証で、bashリダイレクト(`> dir/file.txt 2>&1`)により exit=0 で書き込んだ証跡11ファイルと、`cp -r` で複製したバックアップ(evidence_prev)が、後続ラウンドで消失した(evidence_recheck_20261022 が空、evidence_prev には pq_extract のみ残存)。消失前の diff 結果(一致6件・差分2件)は根拠ファイルが無くなり引用不可となった。

### Error
```
python $S/inspect_structure.py > $R/structure_report.txt 2>&1; echo $? → 0 (全11本)
→ 後ラウンド: ls evidence_recheck_20261022 → 空ディレクトリ(0ファイル)
cp -r evidence evidence_prev_20261015 → 後ラウンド: pq_extract ディレクトリのみ残存
```

### Context
- 前例: ERR-20261020-001(同一チェックアウト並行セッションでコミット済みファイルが作業ツリーから削除)と同型。Pattern-Key 同一
- 消失した書き込みは全て bash リダイレクト/cp によるもので、Edit/python による scripts 更新(11本)は存続した
- セッション途中でシェルの cwd が既定ディレクトリへ复位していた(永続セッションのリサイクル併発)
- 被害: 検証結果の証跡が消え「一致」という報告根拠が失われた(0件/消失を成功扱いにする事故の派生形)

### Suggested Fix
- リダイレクト・cp・mkdir 等のファイル生成は**直後に同一コマンド内で `ls -la` とファイルサイズを確認**する
- 生成と依存する読み取り(diff 等)は**同一コマンド内で完結**させ、ラウンドをまたがない
- 異常時はまず `ls`/`git status --short` で実在確認(サーバー・キャッシュ疑う前に)
- 重要証跡は生成直後に Vault 側へコピーし、二重化する

### Resolution
- **Mitigated**: 2026-10-22(再実行は出力実在確認込みでやり直し)。根本原因は未確定(並行セッション仮説が最有力)
- **Notes**: Pattern-Key: `session.concurrent-checkout-fileloss` / Recurrence-Count: 2(20261020-001, 20261022-001) / 関連: windows-execution-preflight スキルに出力実在確認を追記済み

## [ERR-20261023-001] 引用文を記憶と描画結果から再構築して書き込み、原票と文言がドリフトした

**Logged**: 2026-10-23T17:35:00+09:00
**Priority**: high
**Status**: resolved
**Area**: excel / 原票引用

### Summary
Pana-CIM案7-4への原票完全引用の書き込みで、フローチャート再描画スクリプト(fix74_v2)内の手順文を記憶とPDF描画からの復元でハードコードした。後の突合で21セル中9セルしか一致せず、12セルで文言ドリフト(C44/C47/C53〜C62)と発動条件の C7 部分欠落を検出した。

### Error
```
STEPS = [ ... スクリプト内に手順文を直接記述(記憶ベース) ... ]
→ verify: 一致 9/21 (ドリフト12セル)
```

### Context
- 原因: 「見た目が同じならよい」描画作業に引きずられ、引用という完全一致が要求される書き込みを記憶で行った
- PDF描画は改行位置の解釈や伏字で原文と異なり、復元元として不適
- 会議方針は「改変せず完全引用」であり、ドリフトは方針違反に相当(検出により未然に封じ込め)

### Suggested Fix
- 完全引用・突合対象の書き込みは**原票セルを openpyxl で直接読み取り→プログラムで書き込む**。文言を手で打たない
- 伏字化も原文字列を動的抽出(正規表現)して置換し、スクリプト・ログに原文字列を残さない
- 書き込み後は必ず原票との機械突合を実施し、「見た目OK」で完成判定をしない

### Resolution
- **Resolved**: 2026-10-23。fix74_v3 で原票から直接読み取る方式に書き換え、突合21/21一致(伏字2か所は期待差分)を確認
- **Notes**: Pattern-Key: `quote.memory-reconstruction-drift`

## [ERR-20261023-002] 無効なCOM定数(-4103)でHorizontalAlignment設定が10回とも失敗した

**Logged**: 2026-10-23T17:35:00+09:00
**Priority**: medium
**Status**: resolved
**Area**: excel / COM定数

### Summary
旧表書式残存(中央揃え)の解除で `Range.HorizontalAlignment = -4103` を設定しようとし、「Range クラスの HorizontalAlignment プロパティを設定できません」がリトライ10回全部で発生した。-4103 は存在しない値。

### Error
```
ws.Range("A28:N71").HorizontalAlignment = -4103
→ 0x800A03EC: Range クラスの HorizontalAlignment プロパティを設定できません。
```

### Context
- 正しい定数: xlHAlignGeneral=1 / xlHAlignCenter=-4108 / xlHAlignLeft=-4131 / xlHAlignRight=-4152
- -4108(中央)を誤記・取り違えたものが伝播した
- 同種前例: ERR-20261021-005(日本語ExcelでNumberFormat='General'が1004エラー)。COM定数・文字列は実機確認が要る

### Suggested Fix
- Excel COMの列挙値は msdn または実機読み取り(現状値を Range.HorizontalAlignment で取得)で確認してから使う
- 「一般に戻す」は 1(xlHAlignGeneral)。解除目的なら -4108 を代入しない

### Resolution
- **Resolved**: 2026-10-23。実機で中央揃えセル12個の現状値(-4108)を特定し、fix74_v8 で 1 を設定して解除
- **Notes**: Pattern-Key: `com.invalid-halign-constant`

## [ERR-20261023-003] COMリトライの失敗で孤児EXCEL.EXEが残り、xlsxがファイルロックされた

**Logged**: 2026-10-23T17:35:00+09:00
**Priority**: medium
**Status**: resolved
**Area**: windows / プロセス管理

### Summary
OneDrive上のxlsx編集でCOM呼び出しが失敗→リトライループ中に Excel が正常終了せず、ヘッドレス EXCEL.EXE(コマンドライン `/automation -Embedding`)が2プロセス残存。以降の openpyxl 読み取りが PermissionError になった。

### Error
```
openpyxl.load_workbook(F) → PermissionError: [Errno 13] Permission denied
tasklist → EXCEL.EXE 8908, 20740(孤児) + 22804(ユーザーが開いている実Excel)
```

### Context
- リトライループで Quit に到達しない経路があるとプロセスが残る
- 孤児の判別は CommandLine(`Get-CimInstance Win32_Process`)で行い、MainWindowTitle を持つユーザーの Excel(PID 22804)は終了対象から除外した
- プロセス終了は PID 指定のみ(名前指定は禁止)

### Suggested Fix
- COM処理は try/finally で Quit を保証し、リトライは DispatchEx(新プロセス)ごとに行う
- ロック時は `Get-CimInstance Win32_Process -Filter "Name='EXCEL.EXE'"` で CommandLine を確認し、`/automation -Embedding` のみを PID 指定で終了する
- ユーザーが開いている Excel(MainWindowTitle 有り)は触らない

### Resolution
- **Resolved**: 2026-10-23。孤児2プロセス(PID 8908/20740)を PID 指定で終了しロック解除。以降の読み取り・検証は正常
- **Notes**: Pattern-Key: `com.orphan-excel-filelock`

## [ERR-20261023-004] 図解コネクタの矢印方向が仕様と逆(Continue経路が手順14を迂回)

**Logged**: 2026-10-23T18:05:00+09:00
**Priority**: medium
**Status**: resolved
**Area**: excel / 図形描画・検証

### Summary
7-4図解の要素目視では「Continue箱・手順14箱・ENDの存在と欠けの有無」を確認したが、コネクタの矢印方向(接続セマンティクス)は検査していなかった。Continue合流コネクタが「手順14の右辺→合流点」向きで描かれ、はい経路が手順14を通らずENDに至るように読めた。

### Error
```
fix74_v6.py L157: line(lane2X + nodeW, y14 + nodeH / 2, sideX + sideW / 2, y14 + nodeH / 2)
→ EndArrowheadStyle=2 の矢先が合流点側。仕様(移植プロンプト§7.1)は「はい→Continue→手順14へ合流」
```

### Context
- 要素レベルの目視(箱・ラベルの欠け検査)は通るが、接続の向きは矢印の根元/先の座標を見ないと判別できない
- 全数再検証(全107頁の目視指示)で発見。L字型コネクタは「下り線の行き止まりに出力矢印が接続する」形になり流れが読めない

### Suggested Fix
- コネクタは「根元→先」の座標順で描く。合流表現は矢先を合流先の図形辺に向ける(右から左は x2<x1 で HorizontalFlip)
- 図解検証は要素確認に加え、分岐ごとの経路(始点→終点)を目視で辿る。特に分岐合流は経路の通過ノードを列挙して仕様と照合する

### Resolution
- **Resolved**: 2026-10-23。コネクタを削除し逆方向で再作成(fix74_v9_connector.py)。図形数42・geometry不変を確認、PDF再出力(v3)し300dpiで合流方向を確認。移植プロンプト§7.4に落とし穴第7項として追記
- **Notes**: Pattern-Key: `draw.connector-direction-unchecked`

## [ERR-20261023-005] 橋渡しコネクタの矢印方向も逆(修正記録6と同種の2回目発生)

**Logged**: 2026-10-23T18:20:00+09:00
**Priority**: medium
**Status**: resolved
**Area**: excel / 図形描画・検証

### Summary
コネクタ57(手順6→手順7橋渡しの終端)の矢印が手順7の左辺と逆方向(縦セグメントとの接合点側)を向いていた。修正記録6(Continue合流)と同種の誤りの2回目。さらに始点セグメント(コネクタ55)がfc_L6の角から8pt浮いていた。

### Error
```
fix74_v6.py: 橋渡し終端を line(手順7左辺x, y7中心 → 接合点x, y7中心, arrow=True) の順で描いた
→ EndArrowhead が接合点側。手順7は矢なしの線で受ける状態
```

### Context
- 1回目(ERR-20261023-004)の目視修正後も同種の誤りが橋渡し側に残っていた
- 2回目は自動回帰テスト(regtest_flow.py: 端点とノード辺の距離+期待エッジ突合+経路列挙)で検出した

### Suggested Fix
- 図解のコネクタは目視に頼らず自動検査を入れる: (1)全コネクタの端点がノード辺に接するか(許容4pt) (2)有向エッジ集合が仕様どおりか (3)始点→終点の全経路が仕様のノードを通るか
- 同種誤りが2回発生したため、図解コネクタ実装時は本テストを必須とする

### Resolution
- **Resolved**: 2026-10-23。fix75_bridge.py/fix75b_height.py で修正し regtest PASS。修正記録7として対応表に記載、移植プロンプト§7.4第7項に反映
- **Notes**: Pattern-Key: `draw.connector-direction-unchecked`(Recurrence-Count=2, resolved, 別セッション同日)。同種3回目はスキル化を検討

## [ERR-20261023-006] COM保存がprinterSettings(DEVMODE)を書き換え、PDF出力の頁サイズが変わり行末1文字が非表示になった

**Logged**: 2026-10-23T18:20:00+09:00
**Priority**: high
**Status**: resolved
**Area**: excel / PDF出力・検証

### Summary
fix75のCOM保存後にPDFを再出力したところ、頁サイズが595.20×841.68ptから595.32×841.92ptに変化。折返し境界のセル3頁(p68/71/89)で行末1文字(ッ/b/す)が非表示になり、文字数ベクトル比較で検出された。

### Error
```
v4全頁文字数 vs v3: [(68, -1), (71, -1), (89, -1)]
xl/printerSettings/printerSettings2.bin, 3.bin が COM保存時に書き換え済み(diff -rq で確認)
```

### Context
- DEVMODEは ActivePrinter(=Windows既定、この時点で Microsoft Print to PDF)のドライバー基準で書かれる
- ActivePrinter はこの環境ではCOMから変更不可(全組合せでset-fail)
- 原版(10-15)とv2/v3は595.20系で一致。埋め込みbinを持つシート(会議課題一覧・付録引用元)の折返し計算がドライバー差に敏感

### Suggested Fix
- 保存を伴うCOM編集の前にxlsxのバックアップを取り、出力確定前に printerSettingsN.bin を復元するか頁毎文字数を突合する
- 全頁の文字数ベクトル(107頁)の一致を出力の受け入れ条件にする(目視では1文字欠落を見逃す)
- 頁サイズの照合も受け入れ条件に含める(595.20×841.68pt)

### Resolution
- **Resolved**: 2026-10-23。git efb8991 から bin2/3 を復元したxlsxを作成し、全107頁の文字数が旧版と一致するv5を採用。修正記録8として対応表に記載、移植プロンプト§7.4第8項に反映
- **Notes**: Pattern-Key: `export.printersettings-drift`

---

## [ERR-20261023-007] 復元スクリプトが引数を無視し、別ファイルを検査して「復元不要」と誤報告した

**Logged**: 2026-10-23T21:30:00+09:00
**Priority**: high
**Status**: resolved
**Area**: tooling / 検証スクリプト・誤対象操作

### Summary
`restore_printersettings.py <path>` を trial ファイルに対して実行したが、スクリプト内部の対象パス F がハードコード(保管庫の現行ファイル)で引数が未使用だったため、trial の bins ドリフト(5428B)を検出せず「復元不要」と出力。そのまま PDF を出力したところ 595.32 系の頁サイズと行末1文字欠落が発生した(採用前の受け入れ検証で捕捉、誤った採用には至らなかった)。

### Error
```
> python restore_printersettings.py _trial.xlsx
基準と一致済み: ['xl/printerSettings/printerSettings2.bin', ...]   ← 実際には保管庫ファイルを検査していた
復元不要
(その後の検証で trial の bins は 5428B にドリフトしていた)
```

### Context
- スクリプトは引数対応のつもりで運用されていたが、F 定数が argv を見ていなかった
- 「対象を指定して実行したツールが別物を検査する」失敗は windows-execution-preflight の「0件を成功扱いにしない」と同型
- 出力に実行対象パスが表示されないため、誤対象に気付けなかった

### Suggested Fix
- 対象パスを受け取るツールは必ず argv を解釈し、実行開始時に「対象: <パス>」を表示する
- ツール単体テストとして、ドリフトさせたコピーに対して「要復元」が出ることを一度確認してから運用に載せる

### Resolution
- **Resolved**: 2026-10-23。restore_printersettings.py に引数対応(既定=保管庫ファイル)と「対象: パス」表示を追加。修正後、trial への実行で「要復元→復元完了」を確認し、以降の全出力でベクトル検証が通過
- **Notes**: Pattern-Key: `tool.script-arg-ignored`

## [ERR-20261023-008] レンダラー環境のA4寸法解釈が一時的に変化し、未改変ファイルの再出力でも頁サイズが変わった

**Logged**: 2026-10-23T21:30:00+09:00
**Priority**: medium
**Status**: resolved
**Area**: excel / PDF出力・環境要因

### Summary
bins・pageSetup が基準と完全一致の未改変 xlsx(保管庫の現行ファイル)を再出力したところ、595.32×841.92pt で出力され、付録Aの折返し境界3頁で1文字欠落が再現した。ワークブック側の要因を bin・pageSetup・結合の全比較で排除した後、約1時間後に同条件の再出力で 595.20×841.68pt に自然復旧した(Office/ドライバー側の一時的状態変化と推定)。

### Error
```
未改変保管庫ファイルの再出力: 頁サイズ集合 {(595.32, 841.92)} / 差異頁 [(68, -1), (71, -1), (89, -1)]
 bins ハッシュは基準(efb8991)と完全一致
```

### Context
- 頁サイズはシートの DEVMODE(bin)だけでなく、レンダラー側の A4 ラスタライズ(600dpi で 4960×7014 か 4961×7016 か)に依存する
- ベクトル比較の初期実装で、per-page 差分の「内容は同一で折返し境界が動いただけ」と「文字欠落」を区別できていなかった
- 部分列(部分シーケンス)判定と頁毎文字集合比較を併用すると、欠落の有無を確実に分離できる

### Suggested Fix
- 出力の受け入れ条件は「頁サイズ+先頭N頁ベクトル一致」に加え、差異が出た場合は頁毎文字集合比較で内容同一性を確認する
- 環境由来の寸法変化が疑われるときは、未改変ファイルの再出力を対照実験に使う(ワークブック側の切り分けが速い)

### Resolution
- **Resolved**: 2026-10-23。環境が自然復旧し、最終採用 PDF は 115 頁・595.20×841.68pt・先頭107頁ベクトル=基準一致。QA-21 として帯境界欠落の既存特性を対応表に記録
- **Notes**: Pattern-Key: `export.renderer-env-drift`

## [ERR-20261026-001] ローカル検証でブラウザキャッシュが旧HTML/旧CSSを返し、CSS適用とDOM件数の実測が旧値になった

**Logged**: 2026-10-26T00:00:00+09:00
**Priority**: medium
**Status**: resolved
**Area**: verification

### Summary
ui-revamp 改修の実画面検証で、Chromium が Python http.server の旧応答をキャッシュから返し、`text-wrap` の computed style（wrap のまま）と注記削除前の件数を「実装が効いていない」証拠として扱った。ディスク上の実ファイルは正しく更新済みで、無駄な切り分けが発生した。

### Error
```
computed style h1 { text-wrap: wrap }   ← improve.css には balance を追加済み
main dt 件数 = 削除前の値              ← ディスクの HTML は削除済み
```

### Context
- 対象: `20261016_site-design-improvement/improve/`（python -m http.server 8126/8127 で配信・Playwright Chromium で確認）
- 原因: 同一 URL への再アクセスで Chromium がディスクキャッシュを優先。python http.server は 304/キャッシュ検証に弱く、CSS・HTML が更新されても旧応答が返る
- 検知の遅れ: 「未適用」と誤判定した時点で実装側の切り分け（セレクタ・特異度確認）を始めた。実ファイルの突き合わせを先に行うべきだった

### Suggested Fix
- 検証で期待と異なる値が出たら、実装の疑いの前に**ディスク上の実ファイル（grep 等）と突き合わせる**。実ファイルが正しければキャッシュを疑う
- ローカル検証の URL にはクエリ（`?v=<日時>`）を付けてキャッシュを回避する。`<link href>` に変更した CSS がある場合はリンク側にもクエリを付ける
- 組版系プロパティの適用確認は getComputedStyle の実測で行う（スクリーンショットでは読み取れない）
- ui-revamp スキルの手順6・よくある失敗に追記済み（2026-10-26）

### Resolution
- **Resolved**: 2026-10-26。URL クエリで回避し、h1: balance・lead: pretty を computed style で再実測して確認。T-05 基準値も新値で一致
- **Notes**: Pattern-Key: `verify.browser-cache-stale`
