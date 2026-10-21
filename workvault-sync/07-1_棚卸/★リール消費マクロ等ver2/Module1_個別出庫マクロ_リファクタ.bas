Attribute VB_Name = "Module1"
Option Explicit
'================================================================================
' Module1(リファクタ版 2026-10-21)
' 元コード: ★リール消費マクロ等(DGS-SV) の 2026-06-26 版。運用実績のある動作を維持し、
'           意図と根拠をコメントとして明示した。Sleep 値・キー列・座標は実績値のため変更していない。
'
' 使い方(共通):
'   1. 対象アプリケーションの画面を前面に出す(各 Sub の冒頭で画面タイトルを待つ)
'   2. ボタンまたはマクロ一覧から Sub を実行する
'   3. A列の先頭未処理行(記録列の最終行の次)から最終行まで順に送信する
'   4. 記録列(既定は B列)に結果を書き、途中で止めても次回はその次の行から再開する
'
' 画面が前面から外れると「中断」で止まる設計(誤送信の防止)。実行中は PC を操作しないこと。
' Sub 名はボタン割り当てが参照しているため変更しないこと。
'================================================================================

#If Win64 Then
' 64bit Excel ではポインタ系 API が LongPtr を要求するため、宣言を二重化している
Private Type RECT
    Left As Long
    Top As Long
    Right As Long
    Bottom As Long
End Type

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
Private Declare PtrSafe Sub Sleep Lib "kernel32" (ByVal dwMilliseconds As LongPtr)
#Else
Private Type RECT
    Left As Long
    Top As Long
    Right As Long
    Bottom As Long
End Type

Private Declare PtrSafe Function GetForegroundWindow Lib "user32" ( _
) As Long
Private Declare PtrSafe Function GetWindowRect Lib "user32" ( _
    ByVal hWnd As Long, _
    lpRect As RECT) As Long
Private Declare PtrSafe Function GetWindowTextLength Lib "user32" _
    Alias "GetWindowTextLengthA" ( _
    ByVal hWnd As Long) As Integer
Private Declare PtrSafe Function GetWindowText Lib "user32" _
    Alias "GetWindowTextA" ( _
    ByVal hWnd As Long, _
    ByVal lpString As String, _
    ByVal cch As Long) As Long
Private Declare PtrSafe Sub Sleep Lib "kernel32" (ByVal dwMilliseconds As Long)
#End If

'--- マウス操作(座標指定クリックに使用) --------------------------------------
Private Type coordinate
    x As Long
    y As Long
End Type
Private Declare PtrSafe Function GetCursorPos Lib "user32" (lpPoint As coordinate) As Long
Private Declare PtrSafe Function SetCursorPos Lib "user32" (ByVal x As Long, ByVal y As Long) As Long
Private Declare PtrSafe Sub mouse_event Lib "user32" ( _
    ByVal dwFlags As Long, _
    Optional ByVal dx As Long, _
    Optional ByVal dy As Long, _
    Optional ByVal dwDate As Long, _
    Optional ByVal dwExtraInfo As Long)

Private Const MOUSE_LEFTDOWN = &H2 '左ボタン押下
Private Const MOUSE_LEFTUP = &H4   '左ボタン解放

'--- アクティブウィンドウのタイトルと左上座標を取得する ------------------------
' 戻り値: ウィンドウタイトル(取得失敗時は "Null")
' WindowX / WindowY: 左上座標を返す(ByRef)。以降のクリック座標はこの相対値で指定する
Function getWindowTitle(ByRef WindowX As Long, ByRef WindowY As Long) As String
    #If Win64 Then
        Dim hWnd As LongPtr
    #Else
        Dim hWnd As Long
    #End If

    hWnd = GetForegroundWindow

    Dim structWndowPosition As RECT
    Call GetWindowRect(hWnd, structWndowPosition)

    WindowX = structWndowPosition.Left
    WindowY = structWndowPosition.Top

    Dim windowTitleLength As Integer
    Const intForNullTerminatedString As Integer = 1
    windowTitleLength = GetWindowTextLength(hWnd) + intForNullTerminatedString

    Dim WindowTitleBuffer As String
    WindowTitleBuffer = String(windowTitleLength, vbNullChar)

    Dim fucResult As Integer
    fucResult = GetWindowText(hWnd, WindowTitleBuffer, windowTitleLength)

    If fucResult > 0 Then
        getWindowTitle = Left(WindowTitleBuffer, InStr(WindowTitleBuffer, vbNullChar) - intForNullTerminatedString)
    Else
        getWindowTitle = "Null"
    End If
End Function

'--- 共通の小さな処理(元コードで繰り返されていた 3 パターンを括り出した) -------
' 動作は元のコードと同一。Sleep 値も変えていない。

'指定座標を左クリックする
Private Sub 左クリック(ByVal x As Long, ByVal y As Long)
    SetCursorPos x, y
    mouse_event MOUSE_LEFTDOWN, 0, 0, 0, 0
    mouse_event MOUSE_LEFTUP, 0, 0, 0, 0
End Sub

'指定タイトルの画面が前面に来るまで待ち、切り替わり後の安定待ち(0.5秒)を置く
'元コードと同じく、来ない場合は無限に待つ(タイムアウトなし=既存仕様)
Private Sub 画面を待つ(ByVal 画面タイトル As String, ByRef WindowX As Long, ByRef WindowY As Long)
    Do
        If getWindowTitle(WindowX, WindowY) = 画面タイトル Then
            Exit Do
        End If
        DoEvents
    Loop
    Sleep 500
End Sub

'記録列の最終行の次の行番号を返す(記録が1行も無ければ1)
'途中で中断しても記録済み行を送り直さないための、再開地点の算出
Private Function 再開行を求める(ByVal 記録列 As Long) As Long
    If Cells(Rows.Count, 記録列).End(xlUp).Row = 1 Then
        再開行を求める = 1
    Else
        再開行を求める = Cells(Rows.Count, 記録列).End(xlUp).Row + 1
    End If
End Function

'--- 診断用: 前面ウィンドウのタイトル・座標・マウス座標をイミディエイトに出力 ---
' 実行すると 5 秒待つので、見たい画面を前面にしてから実行する。ボタン割当とは無関係。
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
    PositionText = "ウィンドウ左上の座標：" & "( " & structWndowPosition.Left & " , " & structWndowPosition.Top & " )"

    Dim windowTitleLength As Integer
    Const intForNullTerminatedString As Integer = 1
    windowTitleLength = GetWindowTextLength(hWnd) + intForNullTerminatedString

    Dim WindowTitleBuffer As String
    WindowTitleBuffer = String(windowTitleLength, vbNullChar)

    Dim fucResult As Integer
    fucResult = GetWindowText(hWnd, WindowTitleBuffer, windowTitleLength)

    Dim WindowTitle As String
    If fucResult > 0 Then
        WindowTitle = Left(WindowTitleBuffer, InStr(WindowTitleBuffer, vbNullChar) - intForNullTerminatedString)
    Else
        WindowTitle = "有りません。または取得できませんでした。"
    End If

    Dim WindowText As String
    WindowText = "ウィンドウタイトル：" & WindowTitle

    Debug.Print "アクティブウィンドウ情報です。" & vbCrLf & vbCrLf & WindowText & vbCrLf & PositionText

    Dim c As coordinate
    GetCursorPos c
    Debug.Print "x座標は" & c.x & " y座標は" & c.y
End Sub

'================================================================================
' 個別出庫(ロス数入力アプリケーションへ A/B/C 列の値を順に送信して登録する)
' 前提: A列=項目1 / B列=項目2 / C列=項目3 / D列=結果(◯ ※大丸記号)
' 画面: 個別出庫入力【ロス数入力アプリケーション】
'================================================================================
Sub 個別出庫()

    Dim WindowX As Long
    Dim WindowY As Long

    Call 画面を待つ("個別出庫入力【ロス数入力アプリケーション】", WindowX, WindowY)

    Dim i As Long
    Dim startRow As Long
    startRow = 再開行を求める(4) '本ブックのみ D列を記録列として使う

    For i = startRow To Cells(Rows.Count, 1).End(xlUp).Row

        '3 項目入力+登録確定の ENTER 連送(回数は実績値)
        SendKeys Cells(i, 1).Text
        Sleep 50
        SendKeys "{ENTER}"
        Sleep 50
        SendKeys Cells(i, 2).Text
        Sleep 50
        SendKeys "{ENTER}"
        Sleep 50
        SendKeys Cells(i, 3).Text
        SendKeys "{ENTER}"    '※ C列入力の直後は Sleep なし(元コードのまま)
        Sleep 50
        SendKeys "{ENTER}"
        Sleep 50
        SendKeys "{ENTER}"
        Sleep 50
        SendKeys "{ENTER}"
        Sleep 50
        SendKeys "{ENTER}"
        Sleep 50

        '※ 他ブックの ゼロ確認 は「○」(小)だが、本ブックのみ「◯」(大)。
        '   記号の揺れ。目視確認には問題ないが、文字列比較する処理を足す場合は注意。
        Cells(i, 4).Value = "◯"

        Application.Goto Cells(i + 3, 1)
        DoEvents

        Debug.Print getWindowTitle(WindowX, WindowY)  '診断用の出力(既存のまま残置)
        If getWindowTitle(WindowX, WindowY) <> "個別出庫入力【ロス数入力アプリケーション】" Then
            MsgBox "中断"
            Exit Sub
        End If

    Next i

End Sub

'--------------------------------------------------------------------------------
' ゼロ確認(記録を行わない版。B列への「無し/○」書き込みが無い)
' ※ 単独で動かすと結果が残らない。記録が必要な場合はリール消費マクロ.xlsm 側を使うこと。
'--------------------------------------------------------------------------------
Sub ゼロ確認()

    Dim WindowX As Long
    Dim WindowY As Long

    Call 画面を待つ("リール消費【倉庫管理アプリケーション】", WindowX, WindowY)

    Dim i As Long
    Dim startRow As Long
    startRow = 再開行を求める(2)

    For i = startRow To Cells(Rows.Count, 1).End(xlUp).Row

        Call 左クリック(WindowX + 180, WindowY + 69)

        SendKeys Cells(i, 1).Text
        Sleep 250
        SendKeys "{ENTER}"
        Sleep 250

        If getWindowTitle(WindowX, WindowY) = "倉庫管理アプリケーション" Then
            SendKeys "{ENTER}"
            Sleep 250
        Else
            '在庫あり: 冗長送信(既存採用)
            SendKeys "{ENTER}"
            Sleep 250
            SendKeys "{ENTER}"
            Sleep 250
            SendKeys "{ENTER}"
            Sleep 250
            If getWindowTitle(WindowX, WindowY) <> "リール消費【倉庫管理アプリケーション】" Then
                MsgBox "中断"
                Exit Sub
            End If
            Application.Goto Cells(i + 3, 1)
            DoEvents
        End If

        If getWindowTitle(WindowX, WindowY) <> "リール消費【倉庫管理アプリケーション】" Then
            MsgBox "中断"
            Exit Sub
        End If

    Next i

End Sub
