Attribute VB_Name = "ModLegacy"
Option Explicit

Private Sub LogWrite(msg As String)
    Dim f As Integer
    f = FreeFile
    Open ThisWorkbook.Path & "\log.txt" For Append As #f
    Print #f, Format(Now, "yyyy-mm-dd hh:nn:ss") & " " & msg
    Close #f
End Sub

' データ取込の本体。接続文字列は設定シートから読む
Public Sub ImportData()
    Dim conn As String
    conn = Sheets("設定").Range("B2").Value
    If conn = "" Then
        LogWrite "接続文字列が空"
        Exit Sub
    End If
    Dim i As Long
    For i = 2 To 100
        Select Case Cells(i, 1).Value
            Case "A"
                LogWrite "A を取込"
            Case Else
                LogWrite "その他"
        End Select
    Next i
End Sub
