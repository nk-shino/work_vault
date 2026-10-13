---
title: 0確認マクロ Excelデータ仕様書
status: Done
date:
  - - 2026-09-07
updated:
  - - 2026-09-10
tags:
  - 0確認
  - 棚卸
  - リール消費
  - EG-Pro
  - 生産一課
---
要確認
会議後に着手
仕様確認・ソート追加・
9個以下のものは0確認として削除していく動作を追加する
50円以下をソートするフィルター機能を検討する
（加工情報のある場所とエクスポートの可否について）

# 0確認マクロ Excelデータ仕様書

DGS-SVサーバー配下（\\nksv569.ad.nkc.co.jp\Share\mnt\DGS-SV）で見つかった0確認マクロのExcelファイルについて、ファイルそのものから読み取れた内容を記録する。マクロのVBAコードとシート上のセルの値を突き合わせ、どの列・どのセルが何のデータで、どんな意味と役割を持つのかを、担当外の人が追えるようにまとめた。
担当者は不在で聞き取りができないため、ここに書いたのはコードとセルの値から直接確認できた事実に限る。
棚卸の会議と、現場担当者への聞き取りで得た説明も一部反映した。推測が入る箇所はその旨を明記した。
[[棚卸シミュレーション_現場確認事項]]
## 1. このファイルが果たす役割

このExcelは、A列に並べたシリアル番号の一覧をEGProのリール消費画面に一件ずつ自動入力し、そのシリアルが在庫として残っているかどうかを画面の反応から判定して、結果をB列へ書き込むためのものである。人が画面を見て一件ずつ入力・確認していた作業を、VBAが画面クリックとキー入力を代行して自動化している。

シートは大きく二つの領域に分かれる。左側のA列とB列がマクロの入出力データ本体で、右側の離れた列に手作業の座標調整メモが残っている。

## 2. 0確認が何を確認しているか

現場の説明によれば、0確認は部品が在庫として残ったまま設備側で次の部品へ切り替わってしまうことから生まれる。
あるリールを使い切る前に、部品を切り替えなさいという信号が設備に届くと、本来まだ残っているはずの数量が宙に浮く。そ
の残りが本当にゼロになっているのかを確かめ、ゼロであれば消してよいと判断するのが0確認である。

切り替わりの信号が来るタイミングは部品の大きさで変わる。
テープ幅が小さい部品はセンサー位置の都合で吸着位置よりかなり手前で信号が届き、数十個ほど残した段階で切り替わる。
幅の大きい部品は吸着の直前で切り替わる。この差が、宙に浮く残数の大きさに影響する。
出てくる数量は一つから三つ程度の少数が多い。まれにそれを大きく超える数が出ることがあり、この場合は在庫が残ったまま切り替わった理由が読めず、現場でも原因を追う必要があるとされている。

スプライシングとの関係でも0確認は使われる。スプライシングが本来完了しているはずなのに終わっていない、あるいは予備部品として嵌まっていたものが記録上に残っている、こうした状態を見つけたときに、現物が今どうなっているのかを確かめて解消する。このExcelマクロが固定品目かどうかを見て数量の一致を自動で確認する作りになっているのも、この確認を機械的に回すためである。

## 3. 列ごとのデータの意味と役割

- A列 シリアル番号（入力データ）
	- VBAではCells(i, 1).Textとして読み取られ、リール消費画面へ入力する値になる。マクロにとっての入力データにあたる。
	値の書式は三系統が混在している。英字を含むもの（160096C100633、346047B100880、668715A102467など）、頭にTが付くもの（T9000040403100001、T9000040403100002）、そして先頭が9000番台で途中に半角スペースを挟むもの（9000066313 105170、620508 103742など）である。スペースを挟む書式は、元のシリアル表記をそのまま貼り付けたものと考えられる。
	品番部分（スペースまたは英字より前）が同一で、末尾の連番だけが異なる行が連続する箇所が多く、同一品番のシリアルがまとまって並んでいる。連番の部分は、その部品が日本光電に入ってきた順、正確にはラベルを貼られた順に割り振られる。同じ部品コードでも発注番号が異なると、同日納入で前後が入れ替わることがある。

- B列 判定結果（出力データ）
	- マクロがCells(i, 2)に書き込む列で、値は「○」か「無し」のいずれか。マクロの出力データにあたる。加えて、この列は次回実行時の開始位置を決める基準にもなっている。マクロはCells(Rows.Count, 2).End(xlUp)でB列の最下端を調べ、結果が何もなければ1行目から、すでに結果が入っていればその次の行から処理を再開する。途中で止めても続きから再開できる作りは、このB列の状態管理によって成り立っている。

今回のファイルで確認できたB列の値はすべて○だった。無しは一件も残っていない。切り替わりで宙に浮くのが一つから三つ程度と少ないため、
丸印の一件一件は少数の在庫を指していると考えられる。

## 4. ○と無しがどう決まるか

判定は、シリアルを入力してEnterを押した後の画面タイトルの変化で切り分けられる。
VBAのgetWindowTitle関数が最前面ウィンドウのタイトルを読み取り、その文字列で分岐する。
シリアル入力後にタイトルが倉庫管理アプリケーションへ変わった場合、そのシリアルはB列に無しと書かれる。
これは対象のシリアルが在庫として存在していた側にあたる。
タイトルがリール消費【倉庫管理アプリケーション】のまま変わらなかった場合は、
Enterを追加で数回送ったうえでB列に○を書き、次の処理へ進む。
つまり○は、リール消費画面上でその**シリアルが処理対象**として拾われたことを示す。

このファイルにB列が○しか残っていないことから、ここに載っているシリアルはいずれも処理対象として拾われたものと読める。

## 5. 一行あたりの処理とカーソルの送り方

マクロは一行につき一つのシリアルを処理する。処理の流れは、入力欄を座標クリックし、
A列のシリアルをSendKeysで送信、Enterで確定、画面タイトルを見て○か無しを判定、という順序である。
○を書いた後はApplication.Goto Cells(i + 3, 1)でカーソルを三行下のA列へ動かしている。
このため、シート上でシリアルが三行おきに配置されているか、処理の起点が三行ずつ送られる構造になっている。

処理の途中で画面タイトルがリール消費【倉庫管理アプリケーション】でも倉庫管理アプリケーションでもない想定外の状態になった場合、
マクロは中断というメッセージを表示して停止する。異常時にそのまま処理を続けない歯止めになっている。

## 6. 右側に残っていた座標調整メモ

シート右側の離れた列に、マクロ動作の出力とは別の手作業メモが残っている。書かれているのは、アクティブウィンドウ情報という見出しに続けて、ウィンドウタイトルがリール消費【倉庫管理アプリケーション】であること、ウィンドウ左上の座標が99と248であること、x座標が279でy座標が317であることである。さらにその下に、99と248、279と317、180と69という三組の数値が並ぶ。

この数値はVBAコードと突き合わせると意味が読める。マクロは入力欄をクリックする位置を、SetCursorPos WindowX + 180, WindowY + 69として、ウィンドウ左上の座標から横に180、縦に69ずらした点で計算している。メモの180と69はこのずらし幅そのものである。ウィンドウ左上が99と248、クリックしたい入力欄が279と317のとき、横の差は279から99を引いた180、縦の差は317から248を引いた69になる。三組の数値は、入力欄を正しく押すためのずらし幅を実測から割り出した計算の跡であり、コード中の固定値180と69がどう決まったかを示している。

この記録があることから、マクロを別の環境で動かすときはウィンドウ位置を測り直してずらし幅を調整する必要があったとうかがえる。ウィンドウの表示位置や画面の解像度が変わると、この値がずれてクリック位置を外す。

## 7. VBAコードとセルの対応関係

コード上の参照とシート上の位置の対応は次のとおり。A列はCells(i, 1)で、シリアル番号の読み取り元。B列はCells(i, 2)で、○または無しの書き込み先であり、Cells(Rows.Count, 2).End(xlUp)で開始行を決める基準列でもある。処理の下限はCells(Rows.Count, 1).End(xlUp).Rowで求めるA列の最終行。カーソル送りはCells(i + 3, 1)で三行下のA列。クリック座標のずらし幅はコード中のWindowX + 180とWindowY + 69で、右側メモの180と69に対応する。判定に使うウィンドウタイトルは、在庫ありを示す倉庫管理アプリケーションと、処理継続を示すリール消費【倉庫管理アプリケーション】の二つ。

## 8. 0確認までの調査の流れと関連システム

一連の調査は、生産一課の担当者がWebの吸着サマリで対象部品を叩くところから始まる。エラーが発生した注番のロットで異常の有無を確認してシリアルを特定し、実装履歴で部品番号を叩く。対象シリアルのフィーダーアドレスやラインを見て、固定品目かどうかを判定する。ラインがL2とL3のものは固定、L1のものはフィーダーアドレスが同じであれば固定とみなす。

固定品目で次の部品へ切り替わっている場合、担当者は理論値から本来の実績を調べて回答シートに記入し、消費計上されなかったシリアルのEG-Pro在庫数を修正する。そのシリアルが既に消費済みであれば、ここで0確認を行い、リール消費を実行してラベルを消す。ラベル消去は取り消せない。切り替わっていない場合は現場へ行き、スプライシングされているシリアルを確認して在庫と実績を直す。

初期数量の調べ方は二通りある。倉庫管理アプリの在庫推移でシリアルを入力する方法と、ラベル発行アプリのラベル発行履歴で調べる方法である。在庫推移はアーカイブの都合で履歴が途中までしか残っていないことがあり、過去に在庫を修正した分は履歴に乗らず数字が突然変わるため、判断が難しい。現場での修正方法は、SharePointのitpt000509にあるスプライシング解除・在庫修正手順の資料にまとまっている。

参照するシステムは、実装履歴、シリアルごと吸着サマリ、在庫一覧の三つで、いずれもnksv1359のqcd_DB上のCGIになる。

## 9. 実施の規模と担当

0確認を流した実績データには、丸印の付いたシリアルが数千件並ぶ。品番部分が同じで末尾の連番だけ異なる行がまとまって続く箇所が多く、
同一品番のリールがまとめて対象になっている。

棚卸データは半期ごとに残っている。棚卸しフォルダには2024年10月、その後の2024年10月後、2025年3月という単位でフォルダが分かれ、機種はAED、TEC-1000、TEC-5600、送信機の四系統で保管されている。棚卸結果のデータには理論数量と実数量が並び、実数が理論を大きく下回る行が多い。この差が0確認の対象を生み出していると読める。

過去にこの棚卸を担っていたのは佐藤さんである。佐藤さんの個人フォルダに棚卸データが置かれていること、および作業を引き継いだ二人の証言が根拠になる。佐藤さんへの連絡や引き継ぎがあったかどうかは、今あるファイルからは分からない。

```

Option Explicit

Private Type RECT
Left As Long
Top As Long
Right As Long
Bottom As Long
End Type

#If Win64 Then
Private Declare PtrSafe Function GetForegroundWindow Lib "user32" ( _
) As LongPtr

Private Declare PtrSafe Function GetWindowRect Lib "user32" ( _
ByVal hWnd As LongPtr, _
lpRect As RECT) As Long

Private Declare PtrSafe Function GetWindowTextLength Lib "user32" _
Alias "GetWindowTextLengthA" ( _
ByVal hWnd As LongPtr) As Integer

Private Declare PtrSafe Function GetWindowText Lib "user32" _
Alias "GetWindowTextA" ( _
ByVal hWnd As LongPtr, _
ByVal lpString As String, _
ByVal cch As Long) As Long
#Else
Private Declare Function GetForegroundWindow Lib "user32" ( _
) As Long

Private Declare Function GetWindowRect Lib "user32" ( _
ByVal hWnd As Long, _
lpRect As RECT) As Long

Private Declare Function GetWindowTextLength Lib "user32" _
Alias "GetWindowTextLengthA" ( _
ByVal hWnd As Long) As Integer

Private Declare Function GetWindowText Lib "user32" _
Alias "GetWindowTextA" ( _
ByVal hWnd As Long, _
ByVal lpString As String, _
ByVal cch As Long) As Long
#End If


#If Win64 Then
    Private Declare PtrSafe Sub Sleep Lib "kernel32" (ByVal dwMilliseconds As LongPtr)
#Else
    Private Declare Sub Sleep Lib "kernel32" (ByVal dwMilliseconds As Long)
#End If

'マウス
Type coordinate
    x As Long
    y As Long
End Type
Declare Function GetCursorPos Lib "user32" (lpPoint As coordinate) As Long
Declare Function SetCursorPos Lib "user32" (ByVal x As Long, ByVal y As Long) As Long


Declare Sub mouse_event Lib "user32" ( _
ByVal dwFlags As Long, _
Optional ByVal dx As Long, _
Optional ByVal dy As Long, _
Optional ByVal dwDate As Long, _
Optional ByVal dwExtraInfo As Long)

Const MOUSE_LEFTDOWN = &H2 '10進数の2
Const MOUSE_LEFTUP = &H4 '10進数の4


Sub テスト用()

#If Win64 Then
Dim hWnd As LongPtr
#Else
Dim hWnd As Long
#End If

Sleep 5000

hWnd = GetForegroundWindow

Dim structWndowPosition As RECT
Call GetWindowRect(hWnd, structWndowPosition)

Dim PositionText As String
PositionText = "ウィンドウ左上の座標：" & "( " & _
structWndowPosition.Left & " , " & _
structWndowPosition.Top & " )"

' ここから WindowTitle の取得
Dim windowTitleLength As Integer
Const intForNullTerminatedString As Integer = 1
windowTitleLength = _
GetWindowTextLength(hWnd) + intForNullTerminatedString

Dim WindowTitleBuffer As String
WindowTitleBuffer = String(windowTitleLength, vbNullChar)

Dim fucResult As Integer
fucResult = GetWindowText( _
hWnd, WindowTitleBuffer, windowTitleLength)

Dim WindowTitle As String
If fucResult > 0 Then
WindowTitle = Left(WindowTitleBuffer, _
InStr(WindowTitleBuffer, vbNullChar) - intForNullTerminatedString)
Else
WindowTitle = "有りません。または取得できませんでした。"
End If

Dim WindowText As String
WindowText = "ウィンドウタイトル：" & WindowTitle
' ここまで WindowTitle の取得

Debug.Print "アクティブウィンドウ情報です。" & vbCrLf & _
vbCrLf & _
WindowText & vbCrLf & PositionText

Dim c As coordinate
GetCursorPos c
Debug.Print "x座標は" & c.x & " y座標は" & c.y

End Sub



Function getWindowTitle(ByRef WindowX As Long, ByRef WindowY As Long) As String

#If Win64 Then
Dim hWnd As LongPtr
#Else
Dim hWnd As Long
#End If

hWnd = GetForegroundWindow

Dim structWndowPosition As RECT
Call GetWindowRect(hWnd, structWndowPosition)

'X
WindowX = structWndowPosition.Left
'Y
WindowY = structWndowPosition.Top

' ここから WindowTitle の取得
Dim windowTitleLength As Integer
Const intForNullTerminatedString As Integer = 1
windowTitleLength = _
GetWindowTextLength(hWnd) + intForNullTerminatedString

Dim WindowTitleBuffer As String
WindowTitleBuffer = String(windowTitleLength, vbNullChar)

Dim fucResult As Integer
fucResult = GetWindowText( _
hWnd, WindowTitleBuffer, windowTitleLength)

If fucResult > 0 Then
getWindowTitle = Left(WindowTitleBuffer, _
InStr(WindowTitleBuffer, vbNullChar) - intForNullTerminatedString)
Else
getWindowTitle = "Null"
End If

End Function

Sub ゼロ確認()

Dim WindowX As Long
Dim WindowY As Long

Do

    If getWindowTitle(WindowX, WindowY) = "リール消費【倉庫管理アプリケーション】" Then
        Exit Do
    End If

DoEvents
Loop
Sleep 500

Dim i As Long
Dim startRow As Long

If Cells(Rows.Count, 2).End(xlUp).Row = 1 Then
    startRow = 1
Else
    startRow = Cells(Rows.Count, 2).End(xlUp).Row + 1
End If

For i = startRow To Cells(Rows.Count, 1).End(xlUp).Row
    
    SetCursorPos WindowX + 180, WindowY + 69
    mouse_event MOUSE_LEFTDOWN, 0, 0, 0, 0 '左クリックを押す
    mouse_event MOUSE_LEFTUP, 0, 0, 0, 0 '左クリックを離す
    
    SendKeys Cells(i, 1).Text
    Sleep 500
    SendKeys "{ENTER}"
    Sleep 500
    If getWindowTitle(WindowX, WindowY) = "倉庫管理アプリケーション" Then
        SendKeys "{ENTER}"
        Sleep 500
        Cells(i, 2).Value = "無し"
    Else
        SendKeys "{ENTER}"
        Sleep 500
        SendKeys "{ENTER}"
        Sleep 500
        SendKeys "{ENTER}"
        Sleep 500
        If getWindowTitle(WindowX, WindowY) <> "リール消費【倉庫管理アプリケーション】" Then
            MsgBox "中断"
            Exit Sub
        End If
        Cells(i, 2).Value = "○"
        Application.Goto Cells(i + 3, 1)
        DoEvents
        End If
    
    If getWindowTitle(WindowX, WindowY) <> "リール消費【倉庫管理アプリケーション】" Then
        MsgBox "中断"
        Exit Sub
    End If
    
Next i





End Sub

```
部品情報が記載されているデータあると、次のステップに進むことができる。
- 50円以下の部品に関しては消し込む判断が許可されている
- 9個以下の部品をフィルター削除してもよい。また、それに関するコードの記載をVBA上で行う。(追加予定)
- これに関して、複数のエクセルシートを挟む工程の最初の部分に導入し、その後の工程で弾く事が出来るようにする設計で進める。

