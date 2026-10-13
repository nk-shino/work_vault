Attribute VB_Name = "Module2"

Option Explicit
Type coordinate
    x As Long
    y As Long
End Type
Declare Function GetCursorPos Lib "user32" (lpPoint As coordinate) As Long
 
Sub getMouseCoordinate()
 
  Dim c As coordinate
  GetCursorPos c
  MsgBox "xç¿ïWÇÕ" & c.x & " yç¿ïWÇÕ" & c.y
  
End Sub
