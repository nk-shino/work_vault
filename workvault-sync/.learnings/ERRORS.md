# ERRORS.md

失敗の記録。形式: `[ERR-YYYYMMDD-XXX] 概要` + 発生コマンド/状況 + 解決法 + Pattern-Key。
Recurrence-Count>=2・resolved・別セッション発生の3条件を満たしたらスキル化を検討する。

---

## [ERR-20261021-001] pywin32 の COM 書き込みで naive な datetime が前日にずれる

- 発生コマンド/状況: `make_pivot_smtkashima.py`(SMT鹿島_BOSS.xlsx のピボット用データ作成)。pandas で読んだ日付(Timestamp→naive datetime)を Excel COM の Range.Value へ一括書き込みしたところ、全行が-9時間(JST→UTC)ずれた。2026-04-10 00:00 が 2026-04-09 15:00 として保存され、日付部分が前日になる。
- 解決法: 書き込み前に `dt.replace(tzinfo=datetime.timezone.utc)` を付ける。pywin32 は naive な datetime をローカル時刻とみなして UTC へ変換するため、UTC 指定で変換が無効化される。全行照合で復号済み。
- Pattern-Key: com.naive-datetime-tz-shift

## [ERR-20261021-002] Excel COM(gen_py)の引数名・コレクション呼び出しで TypeError

- 発生コマンド/状況: 同スクリプトのピボット作成。`PivotCaches().Create(Source=...)` は `TypeError: unexpected keyword argument 'Source'`(正しくは `SourceData`)。`pt.DataFields(1)` は `'PivotFields' object is not callable`(gen_py ではプロパティ扱い)。
- 解決法: 引数名は `SourceData` を使う。データフィールドは `AddDataField` の戻り値を受け取って `NumberFormat` を設定する。
- Pattern-Key: com.excel-genpy-argnames

## [ERR-20261021-003] Range.AutoFilter() が状態依存で失敗する

- 発生コマンド/状況: 同スクリプト。`stg.Range("A1:P1383").AutoFilter()` が「Range クラスの AutoFilter メソッドが失敗しました」で com_error。シートはアクティブ化済みでも失敗することがある。
- 解決法: 付加機能のため try/except で迂回。必須処理と付加機能を分け、付加機能の失敗で全体を止めない構成にした。
- Pattern-Key: com.excel-autofilter-fragile

## [ERR-20261021-004] try/except 構造の編集ミスで本体が到達不能になり exit 0 で何もしない

- 発生コマンド/状況: 同スクリプトの try 節に `except` を挿入する編集で、`raise` の後ろに本体コードが残り、Workbooks.Open 成功時は except がスキップされて本体未実行のまま正常終了。エラー出力なし・ファイル無変更で気づきにくい。
- 解決法: スクリプトを書き直した。教訓: 構造を含む編集の後は「処理が実行されたことを示す出力(保存完了メッセージ等)」が出るまで完了扱いにしない。exit 0 は処理成功の証拠にならない。
- Pattern-Key: edit.try-except-unreachable-silent-skip

## [ERR-20261021-005] ピボットXMLの検証ロジが実装詳細を誤認し誤NGを出した

- 発生コマンド/状況: `verify_full.py`(SMT鹿島_BOSS.xlsx 再検証)。5件のNGを出したが全て検証側の誤りだった。①表示形式は Excel が `yyyy-mm-dd` を `yyyy\-mm\-dd` に正規化する(表示は同一)。②スタイルは pivotTableDefinition の属性ではなく子要素 `pivotTableStyleInfo/@name` にある。③dataField の subtotal は省略時デフォルトが sum。④colFields の `x=-2`(値フィールド位置)は単一データフィールドでは省略される。⑤sharedItems はピボットで使用したフィールド(品目/製造責任者/月)のみ列挙され、未使用フィールドはレコード側にインライン保持される。
- 解決法: 各項目を実ファイル照合・実機RefreshTableテストで切り分けた。OOXML の検証は属性の省略時デフォルト仕様を確認してから判定する。
- Pattern-Key: ooxml.pivot-xml-default-attributes

## [ERR-20261021-006] 一時作業フォルダの検証スクリプトが次セッションで消失していた

- 発生コマンド/状況: `Temp\kohden-codeeport202610alidate.py`(8月版とのXML差分検証)。前セッションで作成・使用したが、同日午後の再実行時にファイルが存在しなかった(build.py は残存)。
- 解決法: 再作成せず、PowerPoint COM でのオープン+PNGエクスポート(パース成功が妥当性の証拠)と markitdown 全文確認で代替検証。長期で使う検証スクリプトは保管庫側かワークスペースの恒久場所に置く。
- Pattern-Key: temp.transient-script-loss-between-sessions
