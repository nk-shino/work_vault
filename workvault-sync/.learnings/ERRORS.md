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

## [ERR-20261022-001] 読み取り専用推奨ブックへのCOM保存が黙って無視される

- 発生コマンド/状況: セットアップレポート計算機原本_v2.0.xlsm を PowerShell の Excel COM で開いてVBモジュール追加→`$wb.Save()`。エラーなし・`$wb.Saved=True` が返るのに、ファイルはタイムスタンプ・サイズ・内容とも無変更。原因はブックの `ReadOnlyRecommended=True`(読み取り専用を推奨)で、`DisplayAlerts=$false` の自動応答により読み取り専用で開いていた(`$wb.ReadOnly=True`)。
- 解決法: `Workbooks.Open(path, 0, $false, [Type]::Missing, [Type]::Missing, [Type]::Missing, $true)` と第7引数 IgnoreReadOnlyRecommended を明示して開く。保存系処理の後は戻り値を信用せず、mtime/サイズ/内容の再読込で検証する。
- Pattern-Key: com.excel-readonlyrecommended-silent-save-skip

## [ERR-20261022-002] フォームボタンのマクロ割当がdrawing XMLに無いと誤診した

- 発生コマンド/状況: Shapes.AddFormControl で作ったボタンの OnAction を確認するため、xl/drawings/drawing1.xml の macro 属性だけを grep したら空で、「OnActionが保存されない」と誤判断。PSから Worksheet.Buttons のアクセスも失敗し、InvokeMember 静的呼び出しもエラーで切り分けが長引いた。
- 解決法: フォームボタン(Buttons)のマクロ割当は `xl/drawings/vmlDrawing1.vml` の `<x:FmlaMacro>` に保存される。 Shapes(図形)の割当は drawing XML の macro 属性。両方を見て判定する。PSで非表示COMメンバーを触る必要が出たら VBScript(cscript) の方が確実。なお Shape.OnAction への代入自体は正しくVMLへ書かれており、問題は検証側だった。
- Pattern-Key: ooxml.form-button-vml-fmlamacro

## [ERR-20261022-003] テンプレート高さがA4印刷可能域とほぼ等しくPDFに空白ページが混入

- 発生コマンド/状況: セットアップレポート計算機のPDF出力。20行=732ptのラベルチャンクに対しA4縦の印刷可能高さが約734pt(マージン0.75in)で、自動改ページがチャンク内に割り込み、空白のスライバーページが挟まった(pypdf で 3ページ・うち1ページ19バイトを検出)。
- 解決法: ExportAsFixedFormat の前だけ上下マージンを0.25inへ縮め、出力後に元へ戻す。ページ数とページ毎のコンテンツストリーム長で確認し、2ページ(40+4件)になった。
- Pattern-Key: excel.pdf-export-autobreak-slack

## [ERR-20261022-004] フィルタ有効のシートへのRange.ClearContentsが表示行しか消さない

- 発生コマンド/状況: PS の Excel COM で AutoFilter 有効(FilterMode=True)のシートに `Range("A2:T1000").ClearContents()`。エラーなしで完了するが、フィルタで除外された非表示行のデータが残る。テスト用合成データの消去で「消えたつもりで残ったデータ」により Core マクロの対象無し判定が崩れ、原因切り分けに数プローブ要した。VBAの本番取込フローではフィルタ下の ClearContents をしていないため実害なし。
- 解決法: クリア前にフィルタを解除(`Range("A1:T1000").AutoFilter()`)してから ClearContents する。マクロの異常のように見えてテスト側の挙動であるケースが多いので、合成データ操作は「行の見え方」を先にログしてから判定する。
- Pattern-Key: com.excel-clearcontents-filtered-visible-only

## [ERR-20261022-005] PSのCOM列挙でOLEObjects.Countが全シート「1」を返す偽値になる

- 発生コマンド/状況: PS 5.1 から複数シートの `$ws.OLEObjects.Count` を評価 → 全シートが1。foreach 列挙の要素 Name が "OLEObjects"(コレクション自身)になる等、列挙子が正しく取れていない。実体は ActiveX 0 個(Shapes の Type=12 カウントで確認)。マクロ側の後片付け不良と誤診しかけた。
- 解決法: 実数は Shapes を Type(12=ActiveX)で数える。VBA内の削除は For Each ではなく後ろからのインデックス削除(`Do While .OLEObjects.Count > 0: .OLEObjects(.Count).Delete: Loop`)に統一。
- Pattern-Key: com.ps-oleobjects-false-count

## [ERR-20261022-006] bashからpowershell -Commandへ渡す際$変数がbashに展開され消える

- 発生コマンド/状況: `powershell -Command "... $c = ... UTF8Encoding $true ..."` を bash の二重引用符で実行 → $c・$true が bash の変数展開で空になり、PowerShell 側は引数欠けで構文エラー。
- 解決法: -Command へは bash の単一引用符で渡す(内部は PowerShell の二重引用符)。または \$ エスケープ。
- Pattern-Key: bash.powershell-dollar-stripping

## [ERR-20261022-007] BOM無しUTF-8の.ps1がPowerShell 5.1で日本語含み構文エラーになる

- 発生コマンド/状況: ツールが書き出した .ps1 が BOM 無しの場合、PowerShell 5.1 は ANSI(CP932)で解読し、日本語文字列を含む行の引用符解釈が崩れて「')' が存在しません」等のパースエラー。同内容でも BOM 付きなら正常動作する。発生が断続的(ツール側で BOM が付く/付かないが揺れる)のため厄介。
- 解決法: 実行前に `[System.IO.File]::WriteAllText($p, [System.IO.File]::ReadAllText($p,[Text.Encoding]::UTF8), (New-Object Text.UTF8Encoding $true))` で BOM を付けてから実行(セッション内で常套化)。
- Pattern-Key: ps1.bom-required-for-japanese

## [ERR-20261022-008] VBAモジュールの全行削除+単一関数のみ再挿入でプロジェクト全体がコンパイルエラーになりRun不能・COMハング

- 発生コマンド/状況: ExportBarcodePdf だけ差し替えるつもりで CodeModule.DeleteLines(1, CountOfLines) → AddFromString(新関数のみ)。同モジュール内の ExportBarcodeFromFilter/WriteSerialCsv も消え、他モジュールから呼ばれる SaveSpliceBarcode_Core が未定義に→プロジェクト全体がコンパイルエラー。Application.Run は「マクロ 'xxx' を実行できません。このブックでマクロが使用できないか…」を返し、VBAから呼ぶとコンパイルエラーのモーダルダイアログが出て PS の COM 呼び出しが永久ブロック(タイムアウトに見える。VBE が該当モジュールを開いたまま残る)。
- 解決法: モジュール差し替えは「元の他メンバーを残して目的の関数だけ置換」(元ダンプの頭部+新関数を連結して全行再構成)。Run 失敗時は EXCEL.EXE の MainWindowTitle に「Visual Basic for Applications」と出ているゾンビを PID 確認して停止。
- Pattern-Key: vba.module-full-replace-breaks-compile

## [ERR-20261022-009] OneDrive配下(C:\work)のブックをCOMで開くとFullNameがSharePoint URLになりSave()がローカルに反映されない

- 発生コマンド/状況: C:\work\splicing_review\fixcheck2\dev_qr.xlsm を Workbooks.Open → readonly=True・FullName が https://nk365-my.sharepoint.com/... に。モジュール編集+Save() してもローカルファイルは無反応(クラウド側へ飛ぶ)。再読込で編集が消えたように見え、原因切り分けに数回の再実行を要した。
- 解決法: VBA編集を伴う検証は OneDrive 配下でないフォルダ(C:\Users\ss80751\AppData\Local\Temp\kohden-code など)で実施し、完成物をファイルコピーで戻す。Open 時は第7引数 IgnoreReadOnlyRecommended:=$true を付け、Open 直後に wb.FullName がローカルパスか・wb.ReadOnly が False かを必ずアサート。
- Pattern-Key: com.excel-onedrive-save-goes-to-cloud

## [ERR-20261022-010] PrintArea+IgnorePrintAreas:=Falseでアンカー列からはみ出すOLEが全て印刷対象から消える

- 発生コマンド/状況: S2 に PrintArea "$A$1:$E$49" を設定し ExportAsFixedFormat(IgnorePrintAreas:=False)。QRのOLEはアンカー列の幅より広く(90pt)、はみ出し分が印刷範囲外扱いでQR描画が全滅(文字ラベルだけ出る。ファイルサイズが半分になったことで発覚)。
- 解決法: OLEを含むシートのPDF出力は IgnorePrintAreas:=True のまま(範囲絞り込みはオブジェクト配置側で解決)。PrintArea と ActiveX の併用は避ける。
- Pattern-Key: vba.printarea-drops-ole-overflow

## [ERR-20261022-011] OLE幅がページ幅境界を跨ぐとQRごと「負座標の迷入QR」右ページが各バンドに1枚生成される

- 発生コマンド/状況: 列ピッチ108pt+QR90pt で5列目QR右端=549.75pt がS2の印刷可能幅(約549.6pt)を0.15pt跨ぎ。シート内のOLEは正しく103個(Left<0は0個)なのに、PDFは8ページ(各バンドの右に白背景+黒モジュールのQR断片が x=-64〜28 で出現)。dbgダンプ(出力直前のOLE全Left/Top)でシート側は正常と証明してから PDF 側のページングと断定した。
- 解決法: 列ピッチを104ptに下げて5列目右端を533.75ptに収める。PageSetup の Left/RightMargin 代入はハングする環境がある(ERR-012)ため、レイアウト微調整はマージンではなくピッチで行う。
- Pattern-Key: vba.ole-crosses-page-width-phantom-page

## [ERR-20261022-012] PageSetupのLeft/RightMargin代入がCOMで確定的にハングする

- 発生コマンド/状況: ExportBarcodePdf 内で S2.PageSetup.LeftMargin/RightMargin へ 0.25in を代入→PrintSplice_Core が毎回停止(2回再現。TopMargin/BottomMargin の代入は問題なし)。VBE がモジュールを開いたままのゾンビ EXCEL.EXE が残る。
- 解決法: L/Rマージン代入をやめ、列ピッチ変更で同じ効果を得る。ゾンビは PID 確認後に Stop-Process -Id で停止。
- Pattern-Key: com.excel-pagesetup-lrmargin-hang

## [ERR-20261022-013] cv2のページ全体detectAndDecodeMultiが1〜2件取りこぼす

- 発生コマンド/状況: QR 30個/ページのPDFを300dpiで一括 detectAndDecodeMulti → 29件(1件欠け)。個別に見るとQR自体は正常。
- 解決法: 全数検証は QR白背景矩形(幅高さ80〜100ptの白fill)でグリッド抽出→ソート→個別クロップ→300/450/650dpiの順で再試行。103/103完全一致を確認できた。
- Pattern-Key: cv2.qr-fullpage-detect-misses

## [ERR-20261028-001] 密なスライドへの注記追加が既存本文と衝突する(レンダリング目視検証の初回で検出)

- 発生コマンド/状況: 固定テーブル棚卸し方法_v2.pptxへの注記追加(apply_edits_v15.py初回適用)後、PowerPoint COMで全27枚をPNG化した目視検証で、S9の注記が本文の②行と最終行に、S10の注記がボタンモック[7]の3行目にそれぞれ衝突。python-pptxの追加時点では既存図形との重なりを自動判定していなかった。
- 解決法: 対象スライドの既存図形の外接矩形を実測(inspect_shapes.py)して空き帯を特定し、S9注記Aを1行9pt(T9.95)・S9注記Bを右側空き帯(L18.3/T13.7)・S10注記を最下部帯(T18.3)へ配置し直して解消(2回目のレンダリングで全8枚衝突なし)。テキストボックス追加を含むスライド編集は、座標実測→適用→全枚レンダリング→目視衝突確認を検証工程に含める。
- Pattern-Key: pptx.textbox-overlaps-existing-shapes

## [ERR-20261028-002] 読み取り専用推奨のxlsmをCOMで開くと無音でReadOnlyになりSaveが無音で不反映する

- 発生コマンド/状況: セットアップレポート計算機原本_v2.0.xlsm(読み取り専用推奨で保存されている)のdevコピーへVBAモジュール注入+ボタン追加後、Workbooks.Open(DisplayAlerts=False)→Save()がエラー無しで完了するがファイルは無変更(警告ダイアログが抑制され既定の「読み取り専用で開く」扱いになる)。Save後のwb.SavedはTrueを返すため検出できない。IgnoreReadOnlyRecommended名前付き引数は動的ディスパッチ(DispatchEx)では効かなかった。
- 解決法: devコピーではZIPを直接編集しxl/workbook.xmlの<fileSharing readOnlyRecommended="1"/>を除去してから開く(検証用・flag除去はdevのみ)。本番配備では、(a)元のfileSharing要素を事前取得→(b)ZIP一時除去→(c)COM編集+保存→(d)ZIPでフラグを復元、またはmakepy早期バインディング(EnsureDispatch)でIgnoreReadOnlyRecommendedを正しく渡す。Save後は必ずmd5比較でディスク反映を確認する。
- Pattern-Key: excel.com-readonly-recommended-silent-nosave
