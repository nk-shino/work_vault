# VBA References（Excel VBA スタンダード改訂版）

確認日: 2026-10-01。URLを実際に取得・本文確認した範囲と、参照先として未照合の範囲を分ける。全用語を個別照合済みとはしない。

## 本文照合済み

|対象|URL|確認範囲|
|---|---|---|
|公式試験概要・10分野35小分類・試験形式|https://vbae.odyssey-com.co.jp/about/excel_standard.html|公式本文の出題範囲、40問前後、50分、ベーシック含む、リニューアル告知導線を確認|
|Range.Find|https://learn.microsoft.com/office/vba/api/excel.range.find|Nothing、引数、LookIn/LookAt/SearchOrder/MatchByte等の保存、FindNext、循環を確認|
|WorksheetFunction|https://learn.microsoft.com/office/vba/excel/concepts/events-worksheetfunctions-shapes/using-excel-worksheet-functions-in-visual-basic|Range引数、Min/Match、未一致時の注意を確認|
|VBA入門|https://learn.microsoft.com/office/vba/library-reference/concepts/getting-started-with-vba-in-office|VBA、VBE、マクロ、オブジェクトモデルの位置づけを確認|
|データ型|https://learn.microsoft.com/office/vba/language/reference/user-interface-help/data-type-summary|Long、LongPtr等の公式データ型一覧を確認|
|Excelオブジェクトモデル|https://learn.microsoft.com/office/vba/api/overview/excel/object-model|オブジェクト、プロパティ、メソッドの参照入口を確認|
|ListObject|https://learn.microsoft.com/office/vba/api/excel.listobject|DataBodyRange、HeaderRowRange、ListColumns等の部位を確認|
|SortField|https://learn.microsoft.com/office/vba/api/excel.sortfield|複数キーのSortField概念を確認|
|フリガナ関連|https://learn.microsoft.com/office/vba/api/excel.range.phonetic|RangeのPhonetic関連プロパティを参照|
|ソート方式|https://learn.microsoft.com/office/vba/api/excel.xlsortmethod|SortMethodの定義を確認|

## 参照先として掲載するが本文未照合

FileSystemObject、Workbook.SaveAs、全てのListObject操作、全てのFilter・Sort定数、Windows API、Office版差の細部は、用途ごとに最新のMicrosoft Learnと実機仕様を確認する。本資料で全項目の一次資料照合済みとは扱わない。

## 技術上の注意

FindのLookIn、LookAt、SearchOrder、MatchByte等は呼出し時に明示する。SearchDirectionも毎回指定するが、設定が永続的に保存確定すると断定しない。Selection、ActiveWorkbook、ActiveCellに依存せずThisWorkbookとWorksheetを修飾する。API宣言はLongPtrを検討する。コードは実行していない。
