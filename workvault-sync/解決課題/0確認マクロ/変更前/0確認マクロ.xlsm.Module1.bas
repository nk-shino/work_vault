Attribute VB_Name = "Module1"
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
