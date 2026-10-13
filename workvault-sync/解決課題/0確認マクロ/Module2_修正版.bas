Attribute VB_Name = "Module2"
Option Explicit

' 2026-09-28 修正
'  (1) Module1 にも同名の Type / Declare があり、どちらも公開宣言だったため
'      名前が衝突してプロジェクト全体がコンパイルできなかった。Private にして解消する。
'  (2) PtrSafe が無い Declare は 64bit Excel でコンパイルエラーになる。
'      条件分岐は Win64 ではなく VBA7 で見る。PtrSafe を解するかどうかは
'      ポインタ長ではなく VBA のバージョンで決まるため。

Private Type coordinate
    x As Long
    y As Long
End Type

#If VBA7 Then
    Private Declare PtrSafe Function GetCursorPos Lib "user32" (lpPoint As coordinate) As Long
#Else
    Private Declare Function GetCursorPos Lib "user32" (lpPoint As coordinate) As Long
#End If

Sub getMouseCoordinate()

  Dim c As coordinate
  GetCursorPos c
  MsgBox "x座標は" & c.x & " y座標は" & c.y

End Sub
