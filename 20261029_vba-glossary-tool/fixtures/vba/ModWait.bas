Attribute VB_Name = "ModWait"
Option Explicit

' 引数の題名を表示して待機し、成否を返す共通ルーチン
Public Function WaitMain(title As String, Optional ByVal seconds As Long = 3) As Boolean
    Dim rc As Boolean
    On Error GoTo Fail
    MsgBox title, vbInformation, "待機"
    rc = WaitSeconds(seconds)
    WaitMain = rc
    Exit Function
Fail:
    WaitMain = False
End Function

' 秒数だけ待つ
Public Function WaitSeconds(ByVal seconds As Long) As Boolean
    Dim t As Date
    t = Timer + seconds
    Do While Timer < t
        DoEvents
    Loop
    WaitSeconds = True
End Function

Private Sub CommandButton1_Click()
    Call WaitMain("処理中")
End Sub
