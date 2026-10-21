Option Explicit
'================================================================================
' Module2(リファクタ版 2026-10-21): 座標測定の診断用
' getMouseCoordinate は現在のマウス座標を表示するだけの補助ツール(手動実行用)。
' Module1 と同名の Type が並ぶと名前が曖昧になるため、本モジュール内の宣言は
' すべて Private にして局所化した(動作への影響なし)。
' 元コードに PtrSafe の無い宣言があったが、64bit Excel でコンパイルできないため
' PtrSafe を付けた(32bit 側にも影響なし)。
'================================================================================

Private Type coordinate
    x As Long
    y As Long
End Type

Private Declare PtrSafe Function GetCursorPos Lib "user32" (lpPoint As coordinate) As Long

Sub getMouseCoordinate()
    Dim c As coordinate
    GetCursorPos c
    MsgBox "x座標は" & c.x & " y座標は" & c.y
End Sub
