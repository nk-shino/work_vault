# Excel VBA スタンダード用語ノート（改訂版）

対象: VBAエキスパート「Excel VBA スタンダード」。Windows版デスクトップExcelを主対象とする学習用整理。公式範囲はベーシックの理解も含む。

## 読み方と前提

VBAは **Visual Basic for Applications**（Microsoft Officeアプリケーションに組み込まれた自動化用言語）。VBEは **Visual Basic Editor**（VBAのコードを編集・デバッグする画面）。APIは **Application Programming Interface**（別のソフトウェア機能を呼び出すための仕様）。このノートでは初出時に正式名称と意味を分ける。

コードはExcel実機で実行していない。静的な構文・型・参照関係を点検し、単純な個数・合計などはPythonで計算検算した。破壊的な保存、削除、移動、上書きのコードは実行せず、隔離したテスト用ブックとバックアップを前提とする。合格を保証する資料ではない。

## 基礎（ベーシック範囲の再確認）

### Subプロシージャと変数
正式名称: Sub procedure（値を返さず処理をまとめる手続き）。
意味: `Sub ... End Sub` の間に命令を置く。`Dim`で変数を宣言し、`Option Explicit`で未宣言変数を防ぐ。引数は既定でByRef（呼び出し元の変数を参照して渡す）。

### オブジェクトとプロパティ・メソッド
正式名称: Object（ブック、ワークシート、セル範囲など、操作対象を表すもの）。
意味: プロパティは状態や値、メソッドは操作。`ThisWorkbook.Worksheets("Data").Range("A1").Value2`のように親を明示し、SelectionやActiveWorkbookへの依存を避ける。

### 型・参照・Nothing
正式名称: Long（32ビット整数）、LongPtr（実行環境に応じたポインター整数）、Variant（複数の型を保持できる型）。
意味: 行番号や件数は通常Long。API宣言などポインターを保持する箇所はLongPtr（32/64ビット差に注意）。オブジェクト変数の未設定値はNothingであり、`If rng Is Nothing Then`と判定する。オブジェクトをByValで渡しても参照のコピーであり、オブジェクト自体の変更は共有される。

### コード読解例
```vb
Sub ReadBase()
    Dim n As Long
    n = 2
    AddOne n
    Debug.Print n
End Sub
Sub AddOne(ByRef x As Long)
    x = x + 1
End Sub
```
実行結果: `3`。理由: ByRefで同じ変数を変更したため。`ByVal x As Long`なら呼び出し元は2のまま。

## 1. プロシージャ

### 複数のプロシージャを使ったマクロ
正式名称: Procedure（処理単位）。
意味: 共通処理をSubに分割すると、呼び出し順と責任範囲が明確になる。

### Callステートメント
正式名称: Call statement（別のプロシージャを呼び出すステートメント）。
意味: `Call Prepare`または`Prepare`で呼べる。Callを使う場合は引数を括弧で囲む。

### 値を共有する
正式名称: ByRef（By Reference、参照渡し）、ByVal（By Value、値渡し）。
意味: ByRefは変数そのものを共有し、ByValは値のコピーを渡す。オブジェクトをByValで渡す場合も参照のコピーなので、`obj.Name=...`のような対象変更は元のオブジェクトに及ぶ。別オブジェクトへSetし直すこととは区別する。

### Functionプロシージャ
正式名称: Function procedure（戻り値を返す手続き）。
意味: `Function Total(...) As Long`のように宣言し、関数名へ代入して値を返す。式の中で呼び出せる。

コード読解例:
```vb
Function Twice(ByVal x As Long) As Long
    Twice = x * 2
End Function
Sub CallIt()
    Debug.Print Twice(4)
End Sub
```
実行結果: `8`。引数4のコピーを2倍し、Function名に代入した値が返る。

## 2. 変数の活用

### データの個数を数える、値を合計する
正式名称: Count / Sum（個数を数える／合計する処理）。
意味: `WorksheetFunction.Count`は数値の個数、`CountA`は空でないセル数、`Sum`は合計。For Eachで条件付き集計もできる。行番号や件数はLongにする。

### 配列
正式名称: Array（同じ変数名で複数の値を扱う領域）。
意味: `Dim a(1 To 3) As Long`は固定配列。`Dim v() As Variant: ReDim v(1 To n)`は動的配列。添字の範囲と、二次元Range.Value2の1始まりを意識する。

### オブジェクト変数
正式名称: Object variable（オブジェクトを参照する変数）。
意味: `Dim ws As Worksheet: Set ws=...`のようにSetを使う。未設定のままプロパティへアクセスするとエラー。空のテーブルではDataBodyRangeがNothingになり得る。

コード読解例:
```vb
Dim values As Variant, i As Long, total As Long
values = Array(2, 4, 6)
For i = LBound(values) To UBound(values): total = total + values(i): Next
Debug.Print total, UBound(values)-LBound(values)+1
```
実行結果: `12  3`。LBound/UBoundで配列の実際の範囲を使う。

## 3. ステートメント

### Select Caseステートメント
正式名称: Select Case statement（条件値ごとに分岐するステートメント）。
意味: 複数の等値・範囲条件を読みやすく書ける。`Case Else`で想定外を扱う。

### Do...Loopステートメント
正式名称: Do...Loop statement（条件で繰り返すステートメント）。
意味: Do While/Until、Loop While/Untilを使う。条件更新を忘れると無限ループ。Exit Doで脱出できる。

### For Each...Nextステートメント
正式名称: For Each...Next statement（コレクションの各要素を順に処理するステートメント）。
意味: WorksheetやRangeの各要素を扱う。削除しながら列挙する場合は順序に注意する。

### その他のステートメント
正式名称: If...Then、For...Next、With...End With、Exit、GoTo、Resume。
意味: `With`で親を一貫させ、エラー処理後の`Resume`（エラー行へ戻る等）と`On Error GoTo 0`（通常のエラー処理へ戻す）を混同しない。

コード読解例:
```vb
Dim x As Long, s As String
For x = 1 To 3
    Select Case x
        Case 1: s = s & "A"
        Case 2: s = s & "B"
        Case Else: s = s & "X"
    End Select
Next
Debug.Print s
```
実行結果: `ABX`。3はCase Elseへ進む。

## 4. ファイルの操作

### ファイルの操作
正式名称: File operation（ファイルの存在確認、読書き、コピー、移動など）。
意味: `Dir`で存在確認や列挙、`Open ... For Input`で読み取り、`Close`で閉じる。SaveAsやKillは上書き・削除を伴うためバックアップと隔離フォルダが必要。本ノートでは実行しない。

### フォルダの操作
正式名称: Folder operation（フォルダの作成・存在確認など）。
意味: `MkDir`は親が存在することなどの条件がある。FileSystemObjectを使う場合も参照設定や実行環境差を確認する。

### 文字列操作によるパスの指定
正式名称: Path string（ファイルやフォルダを示す文字列）。
意味: `ThisWorkbook.Path & Application.PathSeparator & "data.csv"`のように区切りを組み立てる。ActiveWorkbookではなくThisWorkbookを基準にする。

コード読解例:
```vb
Dim name As String, p As String
p = ThisWorkbook.Path & Application.PathSeparator
name = Dir(p & "*.csv")
Do While Len(name) > 0
    Debug.Print name
    name = Dir()
Loop
```
実行結果: 対象フォルダのCSV名を順に出力。Dirの引数なし呼び出しで次の一致へ進む。実在ファイルを変更しない。

## 5. WorksheetFunction

### WorksheetFunctionオブジェクト
正式名称: WorksheetFunction object（Excelワークシート関数をVBAから呼ぶためのオブジェクト）。
意味: `Application.WorksheetFunction.Sum(rng)`など。範囲引数はRangeオブジェクトを渡す。Matchなど一致しない場合に実行時エラーになり得るため、エラー処理または事前判定を行う。`Application.Match`はエラー値を返して判定する書き方もある。

コード読解例:
```vb
Dim r As Range, n As Double
Set r = ThisWorkbook.Worksheets("Data").Range("B2:B4")
On Error GoTo NotFound
n = Application.WorksheetFunction.Match("X", r, 0)
Debug.Print n
Exit Sub
NotFound:
Debug.Print "not found"
```
実行結果: Xがなければ`not found`。WorksheetFunction.Matchの未一致をエラー処理で受ける。

## 6. 検索とオートフィルター

### 検索の基本／見つからなかったときの判定
正式名称: Find method（Range内を検索するメソッド）。
意味: 戻り値はRange、未一致はNothing。LookIn、LookAt、SearchOrder、SearchDirection、MatchByte等を毎回明示する。これらの設定はFind実行時に保存され、ダイアログ設定とも影響し合うため、省略時の値を固定的に仮定しない。

### 検索したセルを使う
正式名称: FindNext method（次の一致セルを検索するメソッド）。
意味: 最初のAddressを保存し、同じセルへ戻ったら終了する。無限ループを防ぐ。

### オートフィルターの基本
正式名称: AutoFilter（条件に合う行だけを表示する機能）。
意味: `Range.AutoFilter Field:=2, Criteria1:="OK"`。Fieldは範囲内の列番号。元の範囲を明確にする。

### 絞り込んだ結果のコピーとカウント
正式名称: SpecialCells(xlCellTypeVisible)（可視セルだけを取得する方法）。
意味: 見出しも含めた範囲では、DataBodyRange等から取得する。該当行がない場合はエラーになるためOn Errorで隔離して判定する。可視行の件数は`Areas`や行範囲を考慮し、見出しを数えない。

### 絞り込んだ結果の編集
正式名称: Filtered result editing（絞り込み後の可視行の編集）。
意味: 対象を明示して可視セルだけ変更する。解除・元状態の復元を設計する。

コード読解例:
```vb
Dim hit As Range
With ThisWorkbook.Worksheets("Data").Range("A1:A100")
    Set hit = .Find(What:="abc", LookIn:=xlValues, LookAt:=xlWhole, _
        SearchOrder:=xlByRows, SearchDirection:=xlNext, MatchCase:=False, MatchByte:=False)
End With
If hit Is Nothing Then Debug.Print "none" Else Debug.Print hit.Address
```
実行結果: 完全一致がなければnone。FindはSelectionやActiveCellを変更しない。

## 7. データの並べ替え

### 簡単な条件の並べ替え
正式名称: Sort（データをキー順に並べ替える機能）。
意味: SortFieldsを消去してKey、Order、SetRangeを指定する。ヘッダーの有無を正しく設定する。

### 複雑な条件の並べ替え
正式名称: Multi-key sort（複数キーの並べ替え）。
意味: 優先順位ごとにSortFields.Addを行う。主キー・副キーの順序を意識する。

### 特殊な並べ替え
正式名称: Custom order / SortMethod（ユーザー定義順／並べ替え方式）。
意味: CustomOrderで独自順、SortMethodで文字の並び方式を指定する。日本語のフリガナはデータの設定に依存し、単純な見た目の文字列順と同じとは限らない。

### 文字列の並べ替え
正式名称: Text sort（文字列としての並べ替え）。
意味: 数値に見える文字列、全角半角、大小文字などの扱いを確認してから並べ替える。

### フリガナの操作
正式名称: Phonetic information（セルに保持される日本語の読み情報）。
意味: Range.PhoneticsやCharacters.PhoneticCharacters等で読みを参照・操作する。読み情報がない・誤っている場合、期待する五十音順にならない。

コード読解例:
```vb
With ThisWorkbook.Worksheets("Data").Sort
    .SortFields.Clear
    .SortFields.Add Key:=ThisWorkbook.Worksheets("Data").Range("B2:B10"), Order:=xlAscending
    .SetRange ThisWorkbook.Worksheets("Data").Range("A1:B10")
    .Header = xlYes
    .Apply
End With
```
実行結果: B列をキーにA:Bの行全体を昇順に並べ替える。実行前に対象範囲のバックアップを取る。

## 8. テーブル

### テーブルとは何か
正式名称: ListObject（Excelテーブルを表すオブジェクト）。
意味: 見出し、データ本体、集計行などを構造化して扱う。Rangeより列名で指定しやすい。

### テーブルの特定
正式名称: ListObjects collection（ワークシート内のテーブル集合）。
意味: `ws.ListObjects("Table1")`またはIndexで特定する。名前の衝突や対象シートを確認する。

### テーブル部位の特定
正式名称: HeaderRowRange / DataBodyRange / TotalsRowRange / ListColumns（テーブルの見出し・データ本体・集計行・列）。
意味: `DataBodyRange`はデータ行が0件ならNothingになり得る。`ListColumns("Status").DataBodyRange`も同様に判定してから使う。

### テーブル操作の例
正式名称: ListRows.Add、ListColumns.Add、ShowTotals（行追加、列追加、集計行表示）。
意味: テーブルの部位を対象に値を設定する。削除や並べ替えは実データを変えるため隔離テスト前提。

コード読解例:
```vb
Dim lo As ListObject
Set lo = ThisWorkbook.Worksheets("Data").ListObjects("Sales")
If lo.DataBodyRange Is Nothing Then
    Debug.Print "empty"
Else
    Debug.Print lo.ListRows.Count, lo.ListColumns("Amount").DataBodyRange.Cells.Count
End If
```
実行結果: データ0行ならempty。行があれば行数とAmount列のセル数を出力する。

## 9. エラー対策

### On Errorステートメント
正式名称: On Error statement（実行時エラーへの対応方法を指定するステートメント）。
意味: `On Error GoTo Handler`、`On Error Resume Next`、`On Error GoTo 0`を使い分ける。Resume Nextは対象を狭くし、Err.Numberを確認してすぐ通常処理へ戻す。Handlerでは必要ならResume、Exit Sub等で流れを明確にする。

### エラーが起きないデータに整える
正式名称: Defensive programming（入力や状態を事前に検証する設計）。
意味: Rangeの存在、空テーブル、ゼロ除算、型変換、ファイル存在を先に確認し、エラーを通常分岐へ変える。エラーを隠すだけのResume Nextにしない。

コード読解例:
```vb
On Error GoTo Handler
Dim n As Long: n = 10 / 0
Exit Sub
Handler:
    Debug.Print Err.Number
    Err.Clear
    On Error GoTo 0
End Sub
```
実行結果: 0除算のエラー番号を出力後終了。実務ではエラー内容を記録し、復旧可能性を判断する。

## 10. デバッグ

### Debug.Print
正式名称: Debug.Print（値をイミディエイトウィンドウへ出力するステートメント）。
意味: 変数、Address、Err.Number等を表示する。通常のセルやファイルを書き換えない。

### イミディエイトウィンドウ
正式名称: Immediate window（VBEで式の評価やDebug.Printの結果を見るウィンドウ）。
意味: Ctrl+Gで表示できる。実行中に値を確認し、簡単な式を評価する。

### ブレークポイントとステップ実行
正式名称: Breakpoint / Step execution（指定行で停止／1行ずつ実行）。
意味: F9でブレークポイント、F8でステップ実行。停止中に変数や呼び出し順を確認する。

コード読解例:
```vb
Dim i As Long
For i = 1 To 2
    Debug.Print "i=" & i
Next
```
実行結果: Immediate windowにi=1、i=2。ループ変数の変化を確認できる。

## 試験外の実務補足

ファイル削除・保存、Windows API、イベント、外部参照、Application設定（ScreenUpdating等）は実務で重要だが公式10分野の中心ではない。設定を一時変更する場合は元値を保存し、ErrorHandlerでも復元する。Windows API宣言ではOfficeの32/64ビット差とLongPtrを確認する。Excel for the webではデスクトップVBAを実行できない。

## 目次（学習順）

1. [基礎（ベーシック範囲の再確認）](#基礎ベーシック範囲の再確認) — 用語の読み方、型、オブジェクト
2. [プロシージャ](#1-プロシージャ) → [変数](#2-変数の活用) → [ステートメント](#3-ステートメント)
3. [ファイル](#4-ファイルの操作) → [WorksheetFunction](#5-worksheetfunction) → [検索・オートフィルター](#6-検索とオートフィルター)
4. [並べ替え](#7-データの並べ替え) → [テーブル](#8-テーブル) → [エラー対策](#9-エラー対策) → [デバッグ](#10-デバッグ)
5. [旧153概念の統合索引](#旧153概念の統合索引) — 主章と重複する概念は正式名称・意味を残して相互参照。API・外部連携等は公式の小分類に直接記載のない実務補足。

公式10分野35小分類との対応は `VBA_Standard_Scope.md` を参照する。対応表に見出しがあるだけで全試験内容を網羅すると保証しない。


## 旧153概念の統合索引

旧版の153項目は削除せず、主章にあるものは重複概念としてここにも正式名称と意味を残し、主章への対応を示す。主章に直接置きにくいVBE、型の詳細、イベント、外部連携、セキュリティ等は前提基礎または「公式の小分類に直接記載のない実務補足」として学習上の位置付けを明記する。旧版にあった項目番号は検索・照合用に保持する。

### 旧版項目 1: VBA

- 正式名称: Visual Basic for Applications
- 意味: Microsoft Officeに組み込まれた自動化・拡張用のプログラミング言語。ここではWindows版デスクトップExcelを中心に扱う。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 2: マクロ

- 正式名称: Macro
- 意味: Excel操作を自動化する手続き。VBAのSubなどで実装され、マクロという語自体は略語ではない。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 3: VBE

- 正式名称: Visual Basic Editor
- 意味: VBAコードを作成・編集・デバッグする開発環境。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 4: IDE

- 正式名称: Integrated Development Environment
- 意味: コード編集、実行、デバッグなどをまとめた統合開発環境。VBEはVBA用のIDEに相当する。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 5: プロジェクト

- 正式名称: VBA project
- 意味: ブックに格納されるVBAコード、フォーム、参照設定などの単位。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/library-reference/concepts/security-notes-for-microsoft-office-solution-developers)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 6: 標準モジュール

- 正式名称: Standard module
- 意味: 一般的なSubやFunctionを置くモジュール。シートやThisWorkbookに依存しない処理に向く。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 7: クラスモジュール

- 正式名称: Class module
- 意味: オブジェクトの状態・処理を定義するモジュール。WithEventsでApplication等のイベントを受ける用途もある。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/excel/concepts/events-worksheetfunctions-shapes/using-events-with-excel-objects)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 8: シートモジュール

- 正式名称: Worksheet module
- 意味: 特定のWorksheetに属するモジュール。Worksheet_Changeなどのイベント手続きの置き場所。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/excel/concepts/events-worksheetfunctions-shapes/using-events-with-excel-objects)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 9: ThisWorkbook

- 正式名称: ThisWorkbook object
- 意味: コードを格納しているブックを指すExcel組み込みオブジェクト。ActiveWorkbookとは一致しない場合がある。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 10: 手続き

- 正式名称: Procedure
- 意味: Sub、Function、Propertyなど、実行可能なコードのまとまり。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 11: Sub

- 正式名称: Sub procedure; Subroutineの通称
- 意味: 戻り値を返さない手続き。Subroutineという語は名称の由来を示すもので、Sub自体を架空の略語として展開しない。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 12: Function

- 正式名称: Function procedure
- 意味: 値を返す手続き。ワークシート関数として使えるかは公開範囲や引数などの条件による。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 13: Property

- 正式名称: Property procedure
- 意味: オブジェクトの値を取得・設定する手続き。Property Get、Let、Setがある。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 14: スコープ

- 正式名称: Scope
- 意味: 名前を参照できる範囲。Public、Private、モジュール位置などで決まる。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 15: ライフタイム

- 正式名称: Lifetime
- 意味: 変数やオブジェクトが保持される期間。宣言場所やStatic、プロシージャ終了で変わる。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 16: COM

- 正式名称: Component Object Model
- 意味: Microsoftのコンポーネント連携基盤。VBAから外部オブジェクトを参照・自動化する仕組みの基盤となる。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 17: OLE

- 正式名称: Object Linking and Embedding
- 意味: オブジェクトのリンクと埋め込み。Office間のオブジェクト連携で使われる概念。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 18: API

- 正式名称: Application Programming Interface
- 意味: プログラムから機能を呼び出すための公開インターフェース。Windows APIをDeclareで呼ぶ場合は宣言と型を正確に合わせる必要がある。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/library-reference/concepts/security-notes-for-microsoft-office-solution-developers)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 19: ADO

- 正式名称: ActiveX Data Objects
- 意味: データベース等へ接続するMicrosoftのデータアクセス技術。参照設定または遅延バインディングが必要。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 20: DAO

- 正式名称: Data Access Objects
- 意味: Access/Jet/ACE系データへアクセスするオブジェクトモデル。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 21: SQL

- 正式名称: Structured Query Language
- 意味: データベースの検索・更新等に使う言語。外部入力はパラメーター化し、文字列連結でSQLを作らない。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 22: CSV

- 正式名称: Comma-Separated Values
- 意味: 区切り文字で表形式データを表すテキスト形式。区切りや引用符、文字コードの扱いは相手仕様を確認する。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 23: UTF

- 正式名称: Unicode Transformation Format
- 意味: Unicode文字をバイト列に変換する方式の総称。UTF-8等がある。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 24: Excel for the web

- 正式名称: Excel for the web
- 意味: ブラウザー版Excel。デスクトップVBAマクロの作成・実行環境ではないため、本ノートのコード対象外。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 25: Windows版デスクトップExcel

- 正式名称: Excel for Windows desktop
- 意味: VBE、参照設定、Declare等を含む本ノートの主対象。MacではAPI宣言や一部機能が異なる。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 26: Option Explicit

- 正式名称: Option Explicit statement
- 意味: モジュール内の変数宣言を必須にする文。スペルミスによる暗黙Variantを防ぐ。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 27: Option Base

- 正式名称: Option Base statement
- 意味: 配列の既定下限を0または1に指定する文。配列宣言で明示する方が誤解が少ない。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 28: Option Compare

- 正式名称: Option Compare statement
- 意味: 文字列比較の既定方式を指定する文。Binary、Textなど。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 29: Dim

- 正式名称: Dim statement
- 意味: 変数を宣言するキーワード。正式な略語展開はなく、勝手な頭字語展開をしない。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 30: Const

- 正式名称: Const statement
- 意味: 変更できない定数を宣言するキーワード。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 31: String

- 正式名称: String data type
- 意味: 文字列型。可変長と固定長がある。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/language/reference/user-interface-help/data-type-summary)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 32: Integer

- 正式名称: Integer data type
- 意味: 16ビット符号付き整数型。範囲は-32,768から32,767。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/language/reference/user-interface-help/data-type-summary)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 33: Long

- 正式名称: Long data type
- 意味: 32ビット符号付き整数型。Excelの行番号等では通常Longを使う。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/language/reference/user-interface-help/data-type-summary)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 34: LongLong

- 正式名称: LongLong data type
- 意味: 64ビット整数型。64-bit環境のみ有効で、32-bitでは使えない。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/language/reference/user-interface-help/data-type-summary)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 35: LongPtr

- 正式名称: LongPtr data type
- 意味: 32-bitではLong、64-bitではLongLongに解決される型別名。ポインターやハンドルを保持する用途に使う。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/language/reference/user-interface-help/data-type-summary)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 36: Double

- 正式名称: Double data type
- 意味: 倍精度浮動小数点型。丸め誤差があり、金額の厳密計算では用途を検討する。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/language/reference/user-interface-help/data-type-summary)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 37: Currency

- 正式名称: Currency data type
- 意味: 固定小数点の通貨型。内部的にスケールされた整数で、金額計算向け。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/language/reference/user-interface-help/data-type-summary)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 38: Date

- 正式名称: Date data type
- 意味: 日付と時刻を表す型。Excelセルの日付表示形式とは別概念。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/language/reference/user-interface-help/data-type-summary)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 39: Boolean

- 正式名称: Boolean data type
- 意味: TrueまたはFalseを表す型。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/language/reference/user-interface-help/data-type-summary)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 40: Variant

- 正式名称: Variant data type
- 意味: 数値、文字列、日付、Error、Object等を状況に応じて保持する型。型が曖昧なままになりやすい。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/language/reference/user-interface-help/data-type-summary)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 41: Object

- 正式名称: Object data type
- 意味: オブジェクト参照を保持する型。Setで参照を代入する。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/language/reference/user-interface-help/data-type-summary)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 42: Array

- 正式名称: Array
- 意味: 同じ型またはVariantの値を添字で扱う配列。全体をByValで渡せず、通常ByRefとなる。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 43: UDT

- 正式名称: User-defined type
- 意味: Type文で定義するユーザー定義型。略語としての正式名称はUser-defined type。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 44: Enum

- 正式名称: Enumeration
- 意味: 名前付き定数の集合を定義する型。列挙値の意味をコード上で明確にできる。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 45: Nothing

- 正式名称: Nothing
- 意味: オブジェクト変数が参照を持たない状態を示す特別な値。Setで代入する。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 46: Null

- 正式名称: Null
- 意味: データが存在しないことを示す値。Variantで扱われ、通常の文字列空値とは異なる。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 47: Empty

- 正式名称: Empty
- 意味: 初期化されていないVariantの状態を示す値。IsEmptyで判定する。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 48: Error

- 正式名称: Error value
- 意味: Variantが保持できるエラー値。実行時エラー番号Err.Numberとは区別する。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 49: ByVal

- 正式名称: ByVal parameter
- 意味: 引数の値をコピーして渡す指定。ObjectをByValで渡しても参照値のコピーなので、対象オブジェクトの変更防止にはならない。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 50: ByRef

- 正式名称: ByRef parameter
- 意味: 引数の参照を渡す指定。既定値であり、呼び出し側変数を書き換え得る。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 51: Set

- 正式名称: Set statement
- 意味: オブジェクト変数へ参照を代入するキーワード。値型の代入には使わない。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 52: Let

- 正式名称: Let statement
- 意味: 値を代入するProperty手続きの種類。また古い代入構文のキーワード。通常の値代入では省略される。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 53: With

- 正式名称: With statement
- 意味: 同じオブジェクトを繰り返し修飾する文。End Withまで対象を明確にする。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 54: Call

- 正式名称: Call statement
- 意味: Sub等の手続きを呼び出す文。引数を括弧で囲む書式に注意する。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 55: If

- 正式名称: If...Then...Else statement
- 意味: 条件に応じて実行経路を分岐する文。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 56: Select

- 正式名称: Select Case statement
- 意味: 式の値に応じた複数分岐を読みやすく書く文。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 57: For

- 正式名称: For...Next statement
- 意味: カウンターで繰り返す文。Stepで増分を指定できる。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 58: For Each

- 正式名称: For Each...Next statement
- 意味: Collectionや配列等の各要素を順に処理する文。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 59: Do

- 正式名称: Do...Loop statement
- 意味: 条件または無条件で繰り返す文。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 60: While

- 正式名称: While condition
- 意味: Do While等で条件がTrueの間繰り返す条件。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 61: Exit

- 正式名称: Exit statement
- 意味: Sub、Function、For、Do等から途中退出する文。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 62: Goto

- 正式名称: GoTo statement
- 意味: 指定ラベルへジャンプする文。多用すると制御が追いにくい。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 63: On Error

- 正式名称: On Error statement
- 意味: 実行時エラーの処理方法を指定する文。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 64: Err

- 正式名称: Err object
- 意味: 直近の実行時エラーの番号、説明等を提供する組み込みオブジェクト。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 65: Resume

- 正式名称: Resume statement
- 意味: エラー処理後に再実行・次行・指定ラベルへ戻る文。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 66: エラーハンドラー

- 正式名称: Error handler
- 意味: On Errorで制御されるエラー処理部分。終了時に状態を復元する設計が重要。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 67: Debug

- 正式名称: Debug object/statement
- 意味: デバッグ出力や実行制御に関わる機能。Debug.Printはイミディエイトウィンドウへ出力する。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 68: Break

- 正式名称: Breakpoint
- 意味: 指定行で実行を停止するデバッグ機能。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 69: Watch

- 正式名称: Watch expression
- 意味: 変数や式を監視し、値の変化や条件成立時に停止する機能。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 70: Immediate

- 正式名称: Immediate window
- 意味: 式の評価、Debug.Print出力、簡単な呼び出しを行うVBEのウィンドウ。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 71: Compile

- 正式名称: Compile VBAProject
- 意味: VBAプロジェクトをコンパイルして構文・型などの問題を検出するVBE操作。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 72: Option Explicit

- 正式名称: Option Explicit statement
- 意味: 変数宣言を強制するコンパイラー指示。重複項目だが初心者の必須設定として再掲。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 73: Application

- 正式名称: Application object
- 意味: Excel全体を表す最上位オブジェクト。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 74: Workbook

- 正式名称: Workbook object
- 意味: Excelブックを表すオブジェクト。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 75: Workbooks

- 正式名称: Workbooks collection
- 意味: 開いているWorkbookのコレクション。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 76: Worksheet

- 正式名称: Worksheet object
- 意味: ワークシートを表すオブジェクト。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 77: Worksheets

- 正式名称: Worksheets collection
- 意味: Workbook内のWorksheetコレクション。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 78: Range

- 正式名称: Range object
- 意味: セル、行、列、連続範囲等を表す正式なExcelオブジェクト名。略語ではない。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 79: Cells

- 正式名称: Cells property
- 意味: WorksheetまたはRangeからセル範囲を返す正式APIメンバー。行・列番号で指定できる。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 80: Rows

- 正式名称: Rows property
- 意味: WorksheetまたはRangeの行範囲を返す正式APIメンバー。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 81: Columns

- 正式名称: Columns property
- 意味: WorksheetまたはRangeの列範囲を返す正式APIメンバー。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 82: Offset

- 正式名称: Offset property
- 意味: 基準Rangeから行・列方向にずらしたRangeを返す。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 83: Resize

- 正式名称: Resize property
- 意味: 行数・列数を変えたRangeを返す。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 84: End

- 正式名称: End property
- 意味: Ctrl+矢印相当の方向で連続データ端のセルを返す。空白や途中データに注意。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 85: UsedRange

- 正式名称: UsedRange property
- 意味: 使用済みとExcelが判断する範囲。過去の書式等で広がることがある。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 86: CurrentRegion

- 正式名称: CurrentRegion property
- 意味: 空白行・列で囲まれた現在領域。完全なデータ表とは限らない。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 87: Value

- 正式名称: Value property
- 意味: Rangeの既定値を取得・設定するプロパティ。日付・通貨のVariant変換があり得る。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 88: Value2

- 正式名称: Value2 property
- 意味: Valueから通貨・日付型を使わず値を返すRangeプロパティ。表示形式は変えない。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 89: Formula

- 正式名称: Formula property
- 意味: A1形式の数式を取得・設定するプロパティ。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 90: Formula2

- 正式名称: Formula2 property
- 意味: 動的配列等の新しいExcel数式評価に対応する数式プロパティ。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 91: FormulaR1C1

- 正式名称: FormulaR1C1 property
- 意味: R1C1形式の数式を取得・設定するプロパティ。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 92: Activate

- 正式名称: Activate method
- 意味: ブック・シート・範囲をアクティブ化するメソッド。通常は選択に依存しないコードを優先。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 93: Select

- 正式名称: Select method
- 意味: オブジェクトを選択するメソッド。画面状態やActiveSheetに依存しやすい。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 94: ActiveWorkbook

- 正式名称: ActiveWorkbook property
- 意味: 現在アクティブなWorkbook。処理対象が変わる危険がある。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 95: ActiveSheet

- 正式名称: ActiveSheet property
- 意味: 現在アクティブなシート。明示的なWorksheet修飾を優先する。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 96: Fully qualify

- 正式名称: Fully qualified reference
- 意味: Workbook.Worksheet.Rangeのように親オブジェクトを完全修飾して対象を固定すること。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 97: ListObject

- 正式名称: ListObject object
- 意味: Excelテーブルを表すオブジェクト。列・行・範囲を構造化して扱える。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 98: Find

- 正式名称: Find method
- 意味: Range内を検索するメソッド。LookIn等の設定が前回値から持続するため、必要な引数を毎回明示する。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/api/excel.range.find)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 99: Sort

- 正式名称: Sort object/method
- 意味: 範囲やテーブルを並べ替える機能。キー範囲と順序を明示する。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 100: Filter

- 正式名称: AutoFilter method
- 意味: 表に条件を適用し表示行を絞る機能。フィルター状態と抽出結果を区別する。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 101: Validation

- 正式名称: Validation object
- 意味: セル入力規則を表すオブジェクト。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 102: Format

- 正式名称: FormatConditions object
- 意味: 条件付き書式等の書式設定を表す機能群。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 103: Names

- 正式名称: Names collection
- 意味: ブックまたはシートの定義名コレクション。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 104: PivotTable

- 正式名称: PivotTable object
- 意味: ピボットテーブルを表すオブジェクト。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 105: Chart

- 正式名称: Chart object
- 意味: グラフを表すオブジェクト。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 106: Worksheet_Change

- 正式名称: Worksheet.Change event
- 意味: ワークシートのセル変更時に発生するイベント。コードで変更した場合の再入防止に注意。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/excel/concepts/events-worksheetfunctions-shapes/using-events-with-excel-objects)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 107: Worksheet_SelectionChange

- 正式名称: Worksheet.SelectionChange event
- 意味: 選択セルが変わったときのイベント。頻発するので重い処理を避ける。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/excel/concepts/events-worksheetfunctions-shapes/using-events-with-excel-objects)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 108: Workbook_Open

- 正式名称: Workbook.Open event
- 意味: ブックを開いたときのイベント。信頼されたマクロ環境でのみ実行される。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 109: EnableEvents

- 正式名称: Application.EnableEvents property
- 意味: イベント発生を有効・無効にするBooleanプロパティ。False後はエラーハンドラーでTrueへ戻す。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/excel/concepts/events-worksheetfunctions-shapes/using-events-with-excel-objects)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 110: ScreenUpdating

- 正式名称: Application.ScreenUpdating property
- 意味: 画面再描画を制御するプロパティ。高速化に使うが終了時にTrueへ戻す。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 111: Calculation

- 正式名称: Application.Calculation property
- 意味: 計算モードを制御するプロパティ。変更後は元のモードへ戻す。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 112: 戻すハンドラー

- 正式名称: Cleanup/error-restoration handler
- 意味: ScreenUpdating、EnableEvents、Calculation等を保存前の状態へ復元する終了処理。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 113: macro-enabled workbook

- 正式名称: Excel Macro-Enabled Workbook (.xlsm)
- 意味: VBAプロジェクトを保存できるExcelブック形式。通常の.xlsxはVBAを保存できない。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/library-reference/concepts/security-notes-for-microsoft-office-solution-developers)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 114: xlsx

- 正式名称: Excel Workbook (.xlsx)
- 意味: マクロを格納しない標準ブック形式。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 115: xlsb

- 正式名称: Excel Binary Workbook (.xlsb)
- 意味: バイナリ形式のExcelブック。サイズや読み書き特性は用途と環境で検証する。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 116: SaveAs

- 正式名称: Workbook.SaveAs method
- 意味: 別名・別形式でブックを保存するメソッド。FileFormatを明示し、上書きや警告抑制を慎重に扱う。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/api/excel.workbook.saveas)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 117: File I/O

- 正式名称: File input/output
- 意味: ファイルの読み書き。Openステートメント、FileSystemObject等の方式とエンコードを選ぶ。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 118: Open statement

- 正式名称: Open statement
- 意味: VBAでファイルを開き、読み書き用に割り当てる文。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 119: FileSystemObject

- 正式名称: FileSystemObject object
- 意味: ファイル、フォルダー、テキストを扱うオブジェクト。参照設定またはCreateObjectを使う。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 120: encoding

- 正式名称: Character encoding
- 意味: 文字とバイト列の対応。CSVの日本語ではUTF-8、ANSI等の相手仕様を確認する。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 121: UTF-8

- 正式名称: UTF-8 encoding
- 意味: Unicodeを可変長バイト列で表すエンコード。ExcelのCSV入出力方法によって結果が異なる。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 122: Trust Center

- 正式名称: Trust Center
- 意味: Officeのマクロ、アドイン、信頼済み場所等のセキュリティ設定画面。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/library-reference/concepts/security-notes-for-microsoft-office-solution-developers)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 123: マクロ設定

- 正式名称: Macro Settings
- 意味: マクロ無効、通知付き無効、署名済みのみ許可等を選ぶ設定。全マクロ有効を常用しない。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/library-reference/concepts/security-notes-for-microsoft-office-solution-developers)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 124: Trusted Location

- 正式名称: Trusted Location
- 意味: 信頼済み場所。そこにあるファイルの扱いを緩和するため、フォルダー管理が必要。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 125: digital signature

- 正式名称: Digital signature
- 意味: コードの作成者と改変検知を確認する電子署名。署名後の変更で信頼性が失われる。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/library-reference/concepts/security-notes-for-microsoft-office-solution-developers)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 126: COM add-in

- 正式名称: Component Object Model add-in
- 意味: COM基盤でExcelへ機能を追加するアドイン。VBAマクロとは配布・署名・登録の仕組みが異なる。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/library-reference/concepts/security-notes-for-microsoft-office-solution-developers)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 127: Automation

- 正式名称: Automation
- 意味: 別アプリケーションのオブジェクトをプログラムから操作すること。早期バインディングと遅延バインディングがある。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 128: Declare

- 正式名称: Declare statement
- 意味: 外部DLLの関数をVBAへ宣言する文。Windows APIではPtrSafeとLongPtrを含む32/64-bit対応が必要。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/library-reference/concepts/security-notes-for-microsoft-office-solution-developers)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 129: PtrSafe

- 正式名称: PtrSafe keyword
- 意味: 64-bit OfficeでDeclare宣言が安全なポインター型を使うことを示すキーワード。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 130: parameterization

- 正式名称: Parameterized query
- 意味: SQL文と値を分離して渡す方式。SQLインジェクションや引用符問題を抑える。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 131: Access

- 正式名称: Microsoft Access
- 意味: Microsoftのデータベースアプリケーション。VBAからDAO/ADOで接続する場合がある。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 132: Excel.Application

- 正式名称: Excel.Application automation object
- 意味: 外部VBA等から起動・操作するExcel Applicationオブジェクト。終了忘れや参照解放に注意。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 133: IsEmpty

- 正式名称: IsEmpty function
- 意味: 式がEmptyかを判定する関数。空文字列やNullとは異なる。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 134: IsNull

- 正式名称: IsNull function
- 意味: 式がNullかを判定する関数。Nullとの比較はIsNullを使う。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 135: IsError

- 正式名称: IsError function
- 意味: 式がError値かを判定する関数。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 136: IsDate

- 正式名称: IsDate function
- 意味: 式が日付として認識可能かを判定する関数。地域設定の影響に注意。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 137: IsObject

- 正式名称: IsObject function
- 意味: 式がオブジェクト参照かを判定する関数。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 138: IsArray

- 正式名称: IsArray function
- 意味: 式が配列かを判定する関数。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 139: CStr

- 正式名称: CStr function
- 意味: 式をStringへ変換する関数。Null等は実行時エラーになり得る。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 140: CDate

- 正式名称: CDate function
- 意味: 式をDateへ変換する関数。文字列解釈は地域設定に注意。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 141: CLng

- 正式名称: CLng function
- 意味: 式をLongへ変換する関数。丸めの規則を確認する。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 142: CDbl

- 正式名称: CDbl function
- 意味: 式をDoubleへ変換する関数。浮動小数点の誤差を考慮する。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 143: CVErr

- 正式名称: CVErr function
- 意味: 数値をVariant/Error値に変換する関数。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 144: DateValue

- 正式名称: DateValue function
- 意味: 文字列等から日付部分をDateとして返す関数。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 145: DateSerial

- 正式名称: DateSerial function
- 意味: 年・月・日からDate値を作る関数。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 146: IsMissing

- 正式名称: IsMissing function
- 意味: Variant型のOptional引数が省略されたかを判定する関数。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 147: Optional

- 正式名称: Optional parameter
- 意味: 引数を省略可能にする指定。省略時の既定値またはIsMissingを設計する。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 148: Collection

- 正式名称: Collection object
- 意味: 順序を持つ要素の集まり。キーで取り出せるが、型安全性はDictionary等と異なる。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 149: Dictionary

- 正式名称: Scripting.Dictionary object
- 意味: キーと値の対応を保持するオブジェクト。参照設定またはCreateObjectで利用する。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 150: RegExp

- 正式名称: VBScript.RegExp object
- 意味: 正規表現による文字列検索・置換を行うオブジェクト。参照設定や環境差を確認する。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 151: 安全な小例

- 正式名称: Safe minimal example
- 意味: データ消去・保存を行わず、WorkbookとWorksheetを明示する短い例。Excel実機では未実行。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/api/overview/excel/object-model)

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 152: Select非依存

- 正式名称: Selection-independent code
- 意味: SelectやActiveSheetに依存せず、変数と完全修飾参照で対象を固定する設計。
- 出典: [本文照合済](https://learn.microsoft.com/office/vba/api/excel.range(object))

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目 153: 実機未実行

- 正式名称: Not executed on real Excel
- 意味: 本ノート内のVBAコード例はこの生成環境でExcelを起動して検証していないことを示す注記。
- 出典: [本文未照合](https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office)

## 関連する安全な短例（Excel実機未実行）

次の例はセルの値を読み書きするだけで、消去や保存を行わない。Select、ActiveSheet、ActiveWorkbookに依存しない。実行前に対象ブックを複製し、参照先を確認する。

```vb
Option Explicit

Public Sub SafeWriteExample()
    Dim wb As Workbook
    Dim ws As Worksheet

    Set wb = ThisWorkbook
    Set ws = wb.Worksheets("Sheet1")
    ws.Range("A1").Value2 = "確認用"
End Sub
```

```vb
Public Function IsBlankCell(ByVal target As Range) As Boolean
    IsBlankCell = IsEmpty(target.Value2)
End Function
```

```vb
Public Sub SafeLoopExample()
    Dim ws As Worksheet
    Dim cell As Range

    Set ws = ThisWorkbook.Worksheets("Sheet1")
    For Each cell In ws.Range("A1:A3")
        Debug.Print cell.Address(False, False), cell.Value2
    Next cell
End Sub
```

```vb
Public Sub SafeFindExample()
    Dim ws As Worksheet
    Dim hit As Range

    Set ws = ThisWorkbook.Worksheets("Sheet1")
    Set hit = ws.Range("A1:A20").Find(What:="確認", After:=ws.Range("A20"), _
        LookIn:=xlValues, LookAt:=xlWhole, SearchOrder:=xlByRows, _
        SearchDirection:=xlNext, MatchCase:=False, SearchFormat:=False)
    If Not hit Is Nothing Then Debug.Print hit.Address(False, False)
End Sub
```

注意: Findは前回の設定が持続し得るため、検索条件を明示する。エラー処理でEnableEvents、ScreenUpdating、Calculationを元へ戻す。保存や削除を含む例はここでは扱わない。

**統合状態:** 旧版の正式名称・意味を保持。主章との対応は範囲対応表を参照。

### 旧版項目の扱いと限界

153項目を機械的な数合わせで試験範囲と断定していない。主章の35小分類は公式ページの見出しに対応し、旧版の未収録概念は前提基礎または実務補足に分類した。API、ADO（ActiveX Data Objects）、DAO（Data Access Objects）、SQL（Structured Query Language）、正規表現、イベント、Trust Center等は、公式の小分類に直接記載のない実務補足であり、出題されないとは断定しない。個別用語の一次資料照合状況は `VBA_References.md` の「本文照合済／未照合」に従う。
