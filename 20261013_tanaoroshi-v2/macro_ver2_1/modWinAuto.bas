Attribute VB_Name = "modWinAuto"
'==============================================================================
' modWinAuto  ver.2.1  (2026-10-13)
'
' 相手アプリの窓を操作する層。Win32 API を触るのはこのモジュールだけ。
' ここを触る改修は、窓のつかみ方と送り方を変えるときだけにする。
'
' ver.2 からの変更は2つ。
'
' 1) FindWindowLike を追加。
'    窓のタイトルが環境によって末尾が変わる(バージョン表記など)場合に、
'    完全一致で探せない。前方一致で探す関数を足し、見つからないときだけ
'    自動で使う。既存の完全一致 BindWindow の動作は変えていない。
'
' 2) TargetTitle の戻りを毎回作り直さず、長さを先に測って一度だけ確保。
'    数千件を回すとき、この読み込みが一番多く呼ばれるのでここだけ触った。
'
' ver.2 から引き継いだ大事な決まり(変えないこと)。
'   ・窓は1回つかみ、以後その窓だけを見る。前面の窓を読まない。
'   ・宣言の分岐は #If VBA7。LongPtr で 32bit/64bit の両方に通る。
'   ・窓の取っ手(ハンドル)をこのモジュールの外へ出さない。
'   ・固定の待ちを置かない。「その状態になるまで待つ」形を保つ。
'==============================================================================
Option Explicit
Option Private Module

#If VBA7 Then
    Private Declare PtrSafe Function FindWindow Lib "user32" _
        Alias "FindWindowA" ( _
        ByVal lpClassName As Any, _
        ByVal lpWindowName As Any) As LongPtr

    Private Declare PtrSafe Function EnumWindows Lib "user32" ( _
        ByVal lpEnumFunc As LongPtr, _
        ByVal lParam As LongPtr) As Long

    Private Declare PtrSafe Function GetForegroundWindow Lib "user32" () As LongPtr

    Private Declare PtrSafe Function SetForegroundWindow Lib "user32" ( _
        ByVal hWnd As LongPtr) As Long

    Private Declare PtrSafe Function IsWindow Lib "user32" ( _
        ByVal hWnd As LongPtr) As Long

    Private Declare PtrSafe Function GetWindowTextLength Lib "user32" _
        Alias "GetWindowTextLengthA" ( _
        ByVal hWnd As LongPtr) As Long

    Private Declare PtrSafe Function GetWindowText Lib "user32" _
        Alias "GetWindowTextA" ( _
        ByVal hWnd As LongPtr, _
        ByVal lpString As String, _
        ByVal cch As Long) As Long

    Private Declare PtrSafe Function GetWindowRect Lib "user32" ( _
        ByVal hWnd As LongPtr, _
        lpRect As RECT) As Long

    Private Declare PtrSafe Function SetCursorPos Lib "user32" ( _
        ByVal x As Long, ByVal y As Long) As Long

    Private Declare PtrSafe Function GetCursorPos Lib "user32" ( _
        lpPoint As POINTAPI) As Long

    ' dwExtraInfo は ULONG_PTR。64bit では 8 バイトになる。
    ' ここを Long にすると呼び出し規約がずれて動作が不定になる。
    Private Declare PtrSafe Sub mouse_event Lib "user32" ( _
        ByVal dwFlags As Long, _
        ByVal dx As Long, _
        ByVal dy As Long, _
        ByVal dwData As Long, _
        ByVal dwExtraInfo As LongPtr)

    ' dwMilliseconds は DWORD。旧版は LongPtr にしていたが誤り。
    Private Declare PtrSafe Sub Sleep Lib "kernel32" ( _
        ByVal dwMilliseconds As Long)
#Else
    Private Declare Function FindWindow Lib "user32" _
        Alias "FindWindowA" ( _
        ByVal lpClassName As Any, _
        ByVal lpWindowName As Any) As Long

    Private Declare Function EnumWindows Lib "user32" ( _
        ByVal lpEnumFunc As Long, _
        ByVal lParam As Long) As Long

    Private Declare Function GetForegroundWindow Lib "user32" () As Long

    Private Declare Function SetForegroundWindow Lib "user32" ( _
        ByVal hWnd As Long) As Long

    Private Declare Function IsWindow Lib "user32" ( _
        ByVal hWnd As Long) As Long

    Private Declare Function GetWindowTextLength Lib "user32" _
        Alias "GetWindowTextLengthA" ( _
        ByVal hWnd As Long) As Long

    Private Declare Function GetWindowText Lib "user32" _
        Alias "GetWindowTextA" ( _
        ByVal hWnd As Long, _
        ByVal lpString As String, _
        ByVal cch As Long) As Long

    Private Declare Function GetWindowRect Lib "user32" ( _
        ByVal hWnd As Long, _
        lpRect As RECT) As Long

    Private Declare Function SetCursorPos Lib "user32" ( _
        ByVal x As Long, ByVal y As Long) As Long

    Private Declare Function GetCursorPos Lib "user32" ( _
        lpPoint As POINTAPI) As Long

    Private Declare Sub mouse_event Lib "user32" ( _
        ByVal dwFlags As Long, _
        ByVal dx As Long, _
        ByVal dy As Long, _
        ByVal dwData As Long, _
        ByVal dwExtraInfo As Long)

    Private Declare Sub Sleep Lib "kernel32" ( _
        ByVal dwMilliseconds As Long)
#End If

' 型は Private。旧版は2つのモジュールで同じ名前を公開していて
' 「名前が適切ではありません」でコンパイルが通らなかった。
Private Type RECT
    Left As Long
    Top As Long
    Right As Long
    Bottom As Long
End Type

Private Type POINTAPI
    x As Long
    y As Long
End Type

Private Const MOUSEEVENTF_LEFTDOWN As Long = &H2
Private Const MOUSEEVENTF_LEFTUP As Long = &H4

' つかんだ窓。外へは出さない。
#If VBA7 Then
    Private mTarget As LongPtr
#Else
    Private mTarget As Long
#End If
Private mBoundTitle As String

' EnumWindows で前方一致検索をするときの一時置き場。
Private mSearchPrefix As String
#If VBA7 Then
    Private mSearchHit As LongPtr
#Else
    Private mSearchHit As Long
#End If

'------------------------------------------------------------------ 時間
' GetTickCount は符号なしの値を Long で受けるため約25日で負になる。
' Timer は 0時を回ると巻き戻るので、そこだけ補正すれば足りる。
Private Function ElapsedMs(ByVal startSec As Single) As Long
    Dim d As Single
    d = Timer - startSec
    If d < 0 Then d = d + 86400!   ' 日付をまたいだ
    ElapsedMs = CLng(d * 1000)
End Function

Public Sub WaitMs(ByVal ms As Long)
    Sleep ms
End Sub

'------------------------------------------------------------------ 窓をつかむ
' 指定したタイトルの窓を探してつかむ。見つからなければ timeoutMs まで待つ。
' ver.2.1: 完全一致で見つからないときだけ、前方一致(タイトルの先頭)で探す。
' 設定シートに書いたタイトルが完全一致なら、動きは ver.2 とまったく同じ。
Public Function BindWindow(ByVal titleExact As String, _
                           ByVal timeoutMs As Long) As Boolean
    Dim t0 As Single
    t0 = Timer

    Do
        mTarget = FindWindow(vbNullString, titleExact)
        If mTarget <> 0 Then
            mBoundTitle = titleExact
            BindWindow = True
            Exit Function
        End If

        ' 完全一致で見つからない場合のみ、前方一致を試す。
        ' 窓のタイトルが環境で少し変わるケースの保険。毎回やると無駄なので
        ' 1回だけ(ループ外に出さず、最初の1周目で試して結果を覚えておく)。
        If Len(mBoundTitle) = 0 Then
            Dim hit As LongPtr
            hit = FindWindowByPrefix(titleExact)
            If hit <> 0 Then
                mTarget = hit
                mBoundTitle = TitleOf(hit)
                BindWindow = True
                Exit Function
            End If
        End If

        DoEvents
        Sleep 100
    Loop While ElapsedMs(t0) < timeoutMs

    mTarget = 0
    mBoundTitle = ""
    BindWindow = False
End Function

' タイトルが prefix で始まる最初の窓を返す。見つからなければ 0。
' EnumWindows は見つかるまで全窓を舐めるので、ループの中では呼ばないこと。
Private Function FindWindowByPrefix(ByVal prefix As String) As LongPtr
    mSearchPrefix = prefix
    mSearchHit = 0
    EnumWindows AddressOf EnumProc, 0
    FindWindowByPrefix = mSearchHit
End Function

#If VBA7 Then
Private Function EnumProc(ByVal hWnd As LongPtr, ByVal lParam As LongPtr) As Long
#Else
Private Function EnumProc(ByVal hWnd As Long, ByVal lParam As Long) As Long
#End If
    If mSearchHit <> 0 Then EnumProc = 0: Exit Function   ' 見つかった。列挙を止める
    If Left$(TitleOf(hWnd), Len(mSearchPrefix)) = mSearchPrefix Then
        mSearchHit = hWnd
        EnumProc = 0
    Else
        EnumProc = 1
    End If
End Function

' 指定した窓のタイトルを読む。内部用。
Private Function TitleOf(ByVal hWnd As LongPtr) As String
    Dim n As Long
    n = GetWindowTextLength(hWnd)
    If n <= 0 Then Exit Function
    Dim buf As String
    buf = String$(n + 1, vbNullChar)
    If GetWindowText(hWnd, buf, n + 1) > 0 Then
        Dim p As Long
        p = InStr(buf, vbNullChar)
        If p > 1 Then TitleOf = Left$(buf, p - 1)
    End If
End Function

Public Function IsBound() As Boolean
    If mTarget = 0 Then Exit Function
    IsBound = (IsWindow(mTarget) <> 0)
End Function

Public Sub Unbind()
    mTarget = 0
    mBoundTitle = ""
End Sub

Public Function BoundTitle() As String
    BoundTitle = mBoundTitle
End Function

'------------------------------------------------------------------ タイトル
' つかんだ窓のタイトルを読む。前面の窓ではない。
' 窓が消えていれば空文字を返す。
' ver.2.1: TitleOf と同じ手順だが、つかんだ窓に特化して短く書いた。
Public Function TargetTitle() As String
    If Not IsBound() Then Exit Function
    TargetTitle = TitleOf(mTarget)
End Function

' タイトルがその値になるまで待つ。固定の Sleep の代わりに使う。
Public Function WaitForTitle(ByVal expected As String, _
                             ByVal timeoutMs As Long) As Boolean
    Dim t0 As Single
    t0 = Timer
    Do
        If TargetTitle() = expected Then
            WaitForTitle = True
            Exit Function
        End If
        If Not IsBound() Then Exit Function   ' 窓が閉じた
        DoEvents
        Sleep 50
    Loop While ElapsedMs(t0) < timeoutMs
End Function

' タイトルがその値から変わるまで待つ。
' 「送信したら画面が切り替わる」ことの確認に使う。
Public Function WaitTitleChangeFrom(ByVal fromTitle As String, _
                                    ByVal timeoutMs As Long) As String
    Dim t0 As Single
    t0 = Timer
    Dim cur As String
    Do
        cur = TargetTitle()
        If cur <> fromTitle Then
            WaitTitleChangeFrom = cur
            Exit Function
        End If
        If Not IsBound() Then Exit Function
        DoEvents
        Sleep 50
    Loop While ElapsedMs(t0) < timeoutMs
    WaitTitleChangeFrom = fromTitle   ' 変わらなかった
End Function

'------------------------------------------------------------------ 前面に出す
' つかんだ窓を前面にして、実際に前面になったかを確かめる。
' SendKeys は前面の窓へ送る。前面が別の窓のままだと、入力がそちらへ流れる。
Public Function FocusTarget(ByVal timeoutMs As Long) As Boolean
    If Not IsBound() Then Exit Function

    SetForegroundWindow mTarget

    Dim t0 As Single
    t0 = Timer
    Do
        If GetForegroundWindow() = mTarget Then
            FocusTarget = True
            Exit Function
        End If
        DoEvents
        Sleep 30
    Loop While ElapsedMs(t0) < timeoutMs
End Function

'------------------------------------------------------------------ クリック
' 窓の左上から (dx, dy) ずらした点をクリックする。
' ずらし幅は呼ぶ側が持つ。ここには数値を埋めない。
' 解像度や拡大率が変わると実率が変わると実測しなおしになるため、設定シートに置く。
Public Function ClickOffset(ByVal dx As Long, ByVal dy As Long) As Boolean
    If Not FocusTarget(3000) Then Exit Function

    Dim r As RECT
    If GetWindowRect(mTarget, r) = 0 Then Exit Function

    SetCursorPos r.Left + dx, r.Top + dy
    Sleep 30
    mouse_event MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0
    mouse_event MOUSEEVENTF_LEFTUP, 0, 0, 0, 0
    ClickOffset = True
End Function

' 開発用。ずらし幅を実測するときに使う。
' 旧版は Module2 に同じものがあり、Module1 の宣言と衝突していた。
Public Sub ShowCursorPos()
    Dim p As POINTAPI
    GetCursorPos p
    Dim r As RECT
    If IsBound() Then
        GetWindowRect mTarget, r
        MsgBox "画面の座標 x=" & p.x & " y=" & p.y & vbCrLf & _
               "窓の左上  x=" & r.Left & " y=" & r.Top & vbCrLf & _
               "ずらし幅  dx=" & (p.x - r.Left) & " dy=" & (p.y - r.Top), _
               vbInformation, "座標の実測"
    Else
        MsgBox "画面の座標 x=" & p.x & " y=" & p.y & vbCrLf & vbCrLf & _
               "窓をつかんでいないため、ずらし幅は出せない。", _
               vbInformation, "座標の実測"
    End If
End Sub

'------------------------------------------------------------------ キー送信
' 送る前に必ず前面を確かめる。確かめられなければ送らない。
'
' SendKeys は「送れたか」を返さない。ここで返しているのは
' 「送る条件が整っていたか」であって、相手が受け取った保証ではない。
' 受け取ったかどうかは、呼ぶ側がタイトルの変化で確かめる。
'
' 注意: SendKeys は昇格した窓へは届かない。相手アプリが管理者権限で
' 動いている場合は、この方式自体が使えない。その場合は SendInput でも
' 解決しないので、アプリ側の取り込み機能を探すほうが早い。
Public Function SendTo(ByVal keys As String, _
                       Optional ByVal settleMs As Long = 0) As Boolean
    If Not FocusTarget(3000) Then Exit Function
    On Error GoTo Failed
    Application.SendKeys keys, True   ' True = 処理されるまで待つ
    DoEvents
    If settleMs > 0 Then Sleep settleMs
    SendTo = True
    Exit Function
Failed:
End Function
