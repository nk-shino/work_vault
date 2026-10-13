# Excel VBA スタンダード 自作演習

公式サンプルや実試験問題の転載・再現ではない学習用の自作問題。コードはExcel実機未実行で、静的確認用。解答は別ファイル。

## 問題1: ByRefとByVal
出力は？

```vb
Sub Main()
    Dim n As Long: n = 1
    Add n
    Debug.Print n
End Sub
Sub Add(ByVal x As Long)
    x = x + 1
End Sub
```

## 問題2: Function
F(4)の値は？

```vb
Function F(ByVal x As Long) As Long: F=x*3: End Function
```

## 問題3: 配列
UBound(a)-LBound(a)+1は？

```vb
Dim a: a = Array(5, 7, 9)
```

## 問題4: Select Case
sは？

```vb
x=3: Select Case x: Case 1: s="A": Case Else: s="X": End Select
```

## 問題5: Do Loop
終了時iは？

```vb
i=0: Do Until i=3: i=i+1: Loop
```

## 問題6: For Each
値2,4の合計は？

```vb
Dim total As Long, c As Range
Range("A1").Value = 2: Range("A2").Value = 4
For Each c In Range("A1:A2")
    total = total + c.Value
Next
```

## 問題7: Dir
何を数える？

```vb
Dim fileName As String, n As Long
fileName = Dir("C:\T\*.csv")
Do While Len(fileName) > 0
    n = n + 1
    fileName = Dir()
Loop
```

## 問題8: パス
区切りの役割は？

```vb
p=ThisWorkbook.Path & Application.PathSeparator & "x.csv"
```

## 問題9: WorksheetFunction
未一致時の注意は？

```vb
WorksheetFunction.Match("Z", r, 0)  ' rは検索範囲（未一致を想定）
```

## 問題10: Find
未一致時cは？

```vb
Set c = r.Find(What:="A", LookIn:=xlValues, LookAt:=xlWhole)  ' rは検索範囲
```

## 問題11: FindNext
終了判定に何を比較？

```vb
first=c.Address: Set c=r.FindNext(c)
```

## 問題12: AutoFilter
Field 2は？

```vb
r.AutoFilter Field:=2, Criteria1:="OK"
```

## 問題13: 可視行
該当なし時の注意は？

```vb
Set v=r.SpecialCells(xlCellTypeVisible)
```

## 問題14: 単純Sort
何を指定？

```vb
SortFields.Add Key:=Range("B2:B5"),Order:=xlAscending
```

## 問題15: 複合Sort
優先順位は？

```vb
主キーを先に追加し副キーを次に追加
```

## 問題16: 文字列Sort
先に来るのは？

```vb
"10","2"を文字列として並べる
```

## 問題17: フリガナ
何の情報？

```vb
Range("A1").Phonetics
```

## 問題18: ListObject
何を表す？

```vb
Dim body As Range
Set body = lo.DataBodyRange
If body Is Nothing Then
```

## 問題19: On Error
何を確認して解除する？

```vb
On Error Resume Next の直後
```

## 問題20: Debug
どこに出る？

```vb
Debug.Print i
```

