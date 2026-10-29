Attribute VB_Name = "ModRisky"
Option Explicit

' DB へ直接つなぐ試験コード（マスキング確認用のダミー）
Public Sub ConnectDb()
    Dim password As String
    password = "dummy-pass-1234"
    Dim url As String
    url = "Server=x;pwd=another-secret-99;"
    Debug.Print password, url
End Sub
