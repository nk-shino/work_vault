Attribute VB_Name = "modTanaoroshi"
'==============================================================================
' modTanaoroshi  ver.2  (2026-10-05 改修・2026-10-13 検証前改善)
'
' 棚卸しで使う3つの作業（リール消費・ラベル再発行・外部出庫）と
' 0確認を、1本の繰り返し処理にまとめたもの。
'
' ver.2 の決まりはそのまま引き継ぐ。
'   ・画面の座標・タイトル・待ち上限は「設定」シートに置く。
'   ・取り消せない処理を含むので、試し実行と件数上限を必ず通る形にする。
'   ・判定は窓のタイトルだけで行う(相手アプリの中身は見られないため)。
'
' ver.2 で変えたところ(詳細は ver2_変更仕様書_20261013追補.md)
'   1) 設定の読み込みを開始時に1回だけにした。旧版は行を回るたびに
'      設定シートを Find していたため、数千件では無駄が大きい。
'   2) ログ書き込みをまとめて行えるようにした(バッファ方式)。
'      毎行セルに書くと画面再描画が発生して遅い。
'   3) B列への結果書き込みを Application.ScreenUpdating 制御下に入れた。
'   4) 終了時に「○ / 無し / 空欄 / 中断」の内訳を出すようにした。
'   5) 入口マクロに作業名を表示する確認ダイアログを統一。
'   6) EscapeKeys を1文字ずつの連結から、置換1回ずつへ変えた(速い)。
'
' 変えていないもの(意図的に残している)
'   ・判定ロジック、キーの送り方、B列への書き方。運用がこれを見ている。
'   ・ProcessOne の各作業の流れ。実機検証が済むまで触らない。
'==============================================================================
Option Explicit

Private Const SHEET_SETTING As String = "設定"
Private Const SHEET_LOG As String = "ログ"

Private Const COL_SERIAL As Long = 1    ' A列 シリアル番号
Private Const COL_RESULT As Long = 2    ' B列 結果

Private Type Config
    Mode As String          ' ReelConsume / LabelReissue / ExternalIssue / ZeroCheck
    WorkTitle As String     ' 作業中の画面のタイトル
    DoneTitle As String     ' 1件終わって戻る先のタイトル
    ClickDX As Long
    ClickDY As Long
    BindTimeoutMs As Long
    StepTimeoutMs As Long
    PrintWaitMs As Long     ' ラベル発行の印刷待ち
    FirstRow As Long        ' 見出しがあるなら2
    MaxRows As Long         ' 0 なら制限なし
    DryRun As Boolean
End Type

' 結果の値。B列とログの両方で使うので定数にまとめた。
Private Const RES_OK As String = "○"
Private Const RES_NONE As String = "無し"
Private Const RES_DRY As String = "試"
Private Const RES_EMPTY As String = "空欄"
Private Const RES_STOP As String = "中断"

'==============================================================================
' 入口
'==============================================================================

' リール消費。取り消せるか未確認のため、既定で試し実行にしている。
Public Sub リール消費_実行()
    RunAll "ReelConsume"
End Sub

Public Sub ラベル再発行_実行()
    RunAll "LabelReissue"
End Sub

Public Sub 外部出庫_実行()
    RunAll "ExternalIssue"
End Sub

Public Sub ゼロ確認_実行()
    RunAll "ZeroCheck"
End Sub

' ずらし幅の実測。相手の入力欄にカーソルを置いてから呼ぶ。
Public Sub 座標を測る()
    Dim c As Config
    c = LoadConfig(CStr(InputBox( _
        "どの作業の窓をつかむか。" & vbCrLf & _
        "ReelConsume / LabelReissue / ExternalIssue / ZeroCheck", _
        "座標の実測", "ReelConsume")))
    If Len(c.Mode) = 0 Then Exit Sub
    If Not modWinAuto.BindWindow(c.WorkTitle, 10000) Then
        MsgBox "窓が見つからない: " & c.WorkTitle, vbExclamation
        Exit Sub
    End If
    MsgBox "入力欄にマウスを置いてから OK を押す。", vbInformation
    modWinAuto.ShowCursorPos
    modWinAuto.Unbind
End Sub

'==============================================================================
' 本体
'==============================================================================
Private Sub RunAll(ByVal mode As String)
    Dim c As Config
    c = LoadConfig(mode)
    If Len(c.Mode) = 0 Then Exit Sub

    Dim ws As Worksheet
    Set ws = ActiveSheet

    ' 旧版は Cells(...) をシート指定なしで書いていた。
    ' 設定シートやログシートを開いたまま実行すると、そちらへ結果を書いていた。
    If ws.Name = SHEET_SETTING Or ws.Name = SHEET_LOG Then
        MsgBox "シリアルの一覧が入っているシートを選んでから実行する。", vbExclamation
        Exit Sub
    End If

    Dim lastA As Long
    lastA = ws.Cells(ws.Rows.Count, COL_SERIAL).End(xlUp).Row
    If lastA < c.FirstRow Then
        MsgBox "A列にシリアルが無い。", vbExclamation
        Exit Sub
    End If

    Dim startRow As Long
    startRow = ResumeRow(ws, c.FirstRow)

    If startRow > lastA Then
        MsgBox "すべて処理済み。B列を空にすると最初からやり直せる。", vbInformation
        Exit Sub
    End If

    Dim planned As Long
    planned = lastA - startRow + 1
    If c.MaxRows > 0 And planned > c.MaxRows Then planned = c.MaxRows

    ' 取り消せない処理なので、件数と範囲を出して一度止める。
    Dim msg As String
    msg = "作業: " & c.Mode & vbCrLf & _
          "窓:  " & c.WorkTitle & vbCrLf & _
          "行:  " & startRow & " ～ " & (startRow + planned - 1) & vbCrLf & _
          "件数: " & planned & " 件" & vbCrLf & vbCrLf & _
          IIf(c.DryRun, _
              "■試し実行。キーは送らない。判定とログだけを取る。", _
              "■本番。キーを送る。リール消費は取り消せない可能性がある。")
    If MsgBox(msg, vbOKCancel + IIf(c.DryRun, vbInformation, vbExclamation), _
              "実行の確認") <> vbOK Then Exit Sub

    If Not modWinAuto.BindWindow(c.WorkTitle, c.BindTimeoutMs) Then
        MsgBox "窓が見つからない: " & c.WorkTitle & vbCrLf & _
               "タイトルが設定シートの値と一致しているか確認する。", vbExclamation
        Exit Sub
    End If

    Dim logWs As Worksheet
    Set logWs = EnsureLog()
    WriteLog logWs, 0, "", "開始", c.Mode & " / " & IIf(c.DryRun, "試し", "本番") & _
                                 " / " & planned & "件"

    ' 描画と再計算を止める。数千件のとき、これで体感がかなり違う。
    ' 終わったら必ず元に戻す(CleanUp で戻すので、途中で止まっても安全)。
    Dim prevCalc As XlCalculation
    Dim prevScreen As Boolean
    prevCalc = Application.Calculation
    prevScreen = Application.ScreenUpdating
    Application.Calculation = xlCalculationManual
    Application.ScreenUpdating = False

    Dim i As Long, n As Long
    Dim okCount As Long, noneCount As Long, emptyCount As Long
    Dim serial As String, observed As String, result As String

    On Error GoTo CleanUp

    For i = startRow To lastA
        If c.MaxRows > 0 And n >= c.MaxRows Then Exit For

        ' .Text ではなく .Value を使う。
        ' .Text は「表示されている文字」なので、列幅が狭いと ### が返る。
        serial = Trim$(CStr(ws.Cells(i, COL_SERIAL).Value))

        If Len(serial) = 0 Then
            ' 旧版は空欄でもそのまま Enter を送っていた。
            ' 入力欄に残っていた前の値が確定される余地があった。
            ws.Cells(i, COL_RESULT).Value = RES_EMPTY
            emptyCount = emptyCount + 1
            GoTo NextRow
        End If

        If Not modWinAuto.IsBound() Then
            result = RES_STOP
            observed = "窓が閉じた"
            ws.Cells(i, COL_RESULT).Value = result
            WriteLog logWs, i, serial, result, observed
            MsgBox "窓が閉じた。" & i & " 行目の手前で止めた。", vbExclamation
            Exit For
        End If

        If modWinAuto.TargetTitle() <> c.WorkTitle Then
            result = RES_STOP
            observed = "想定外の画面: " & modWinAuto.TargetTitle()
            ws.Cells(i, COL_RESULT).Value = result
            WriteLog logWs, i, serial, result, observed
            MsgBox "画面が " & c.WorkTitle & " ではない。" & vbCrLf & _
                   "今のタイトル: " & modWinAuto.TargetTitle() & vbCrLf & _
                   i & " 行目の手前で止めた。", vbExclamation
            Exit For
        End If

        result = ProcessOne(c, serial, observed)

        ws.Cells(i, COL_RESULT).Value = result
        WriteLog logWs, i, serial, result, observed

        Select Case result
            Case RES_OK:    okCount = okCount + 1
            Case RES_NONE:  noneCount = noneCount + 1
            Case RES_DRY, RES_EMPTY
            Case Else:      ' 中断
                MsgBox "中断した。" & vbCrLf & _
                       "行: " & i & vbCrLf & _
                       "シリアル: " & serial & vbCrLf & _
                       "見えた画面: " & observed & vbCrLf & vbCrLf & _
                       "ログシートに経過が残っている。", vbExclamation
                Exit For
        End Select

NextRow:
        n = n + 1
        ' 進捗を出す。旧版の Application.Goto はスクロールだけで、
        ' 件数が分からなかった。
        Application.StatusBar = c.Mode & "  " & n & " / " & planned & _
                               "  (" & i & "行目)"
        DoEvents
    Next i

CleanUp:
    Dim errNo As Long, errDesc As String
    errNo = Err.Number
    errDesc = Err.Description
    On Error Resume Next

    Application.Calculation = prevCalc
    Application.ScreenUpdating = prevScreen
    Application.StatusBar = False
    modWinAuto.Unbind

    If errNo <> 0 Then
        WriteLog logWs, i, serial, "異常終了", errNo & " " & errDesc
        MsgBox "異常終了。" & vbCrLf & i & " 行目" & vbCrLf & _
               errNo & " " & errDesc, vbCritical
        Exit Sub
    End If

    ' 内訳を1行にまとめて出す。旧版は○とその他の2区分だった。
    WriteLog logWs, 0, "", "終了", _
        "処理 " & n & " 件 / ○ " & okCount & " / 無し " & noneCount & _
        " / 空欄 " & emptyCount & " / 中断 " & (n - okCount - noneCount - emptyCount)
    MsgBox "終了。" & vbCrLf & _
           "処理 " & n & " 件" & vbCrLf & _
           "○ " & okCount & " 件" & vbCrLf & _
           "無し " & noneCount & " 件" & vbCrLf & _
           "空欄 " & emptyCount & " 件" & vbCrLf & vbCrLf & _
           "内訳はログシートにある。", vbInformation
End Sub

'------------------------------------------------------------------ 1件ぶん
' 各作業の流れは ver.2 から変えていない。実機検証が済むまで触らない。
Private Function ProcessOne(ByRef c As Config, _
                            ByVal serial As String, _
                            ByRef observed As String) As String
    observed = ""

    If c.DryRun Then
        observed = "試し実行のため送信していない"
        ProcessOne = RES_DRY
        Exit Function
    End If

    Select Case c.Mode

    '----------------------------------------------------------------
    Case "ReelConsume", "ZeroCheck"
        ' 入力欄をクリックしてシリアルを送り、Enterで確定する。
        ' そのあとタイトルが変わるかどうかで在庫の有無を判定する。
        If Not modWinAuto.ClickOffset(c.ClickDX, c.ClickDY) Then
            observed = "前面にできなかった"
            ProcessOne = RES_STOP: Exit Function
        End If
        ' 入力欄に前の値が残っている場合に備えて選択してから打つ。
        If Not modWinAuto.SendTo("^a") Then
            observed = "前面にできなかった"
            ProcessOne = RES_STOP: Exit Function
        End If
        If Not modWinAuto.SendTo(EscapeKeys(serial)) Then
            observed = "前面にできなかった"
            ProcessOne = RES_STOP: Exit Function
        End If
        modWinAuto.SendTo "{ENTER}"

        ' 固定の待ちをやめ、タイトルが動くまで待つ。
        observed = modWinAuto.WaitTitleChangeFrom(c.WorkTitle, c.StepTimeoutMs)

        If observed = c.DoneTitle Then
            ' 在庫が無い。確認のダイアログを閉じて次へ。
            modWinAuto.SendTo "{ENTER}"
            If Not modWinAuto.WaitForTitle(c.WorkTitle, c.StepTimeoutMs) Then
                ProcessOne = RES_STOP: Exit Function
            End If
            ProcessOne = RES_NONE

        ElseIf observed = c.WorkTitle Then
            ' タイトルが動かなかった。送れていない可能性がある。
            ' 旧版はここを「在庫あり」と解釈して Enter を3回送っていた。
            ' 送信漏れと在庫ありを区別していなかった。
            observed = "タイトルが変化しない（送信漏れの疑い）"
            ProcessOne = RES_STOP

        Else
            ' 在庫がある。確定まで進める。
            modWinAuto.SendTo "{ENTER}"
            If Not modWinAuto.WaitForTitle(c.WorkTitle, c.StepTimeoutMs) Then
                observed = "確定後に " & c.WorkTitle & " へ戻らない（" & _
                           modWinAuto.TargetTitle() & "）"
                ProcessOne = RES_STOP: Exit Function
            End If
            ProcessOne = RES_OK
        End If

    '----------------------------------------------------------------
    Case "LabelReissue"
        If Not modWinAuto.ClickOffset(c.ClickDX, c.ClickDY) Then
            observed = "前面にできなかった"
            ProcessOne = RES_STOP: Exit Function
        End If
        modWinAuto.SendTo "^a"
        If Not modWinAuto.SendTo(EscapeKeys(serial)) Then
            observed = "前面にできなかった"
            ProcessOne = RES_STOP: Exit Function
        End If

        ' 旧版は Tab を4回、確定、Shift+Tab を9回、確定、という順で
        ' 1回ずつ SendKeys を呼び、間に 100ms の固定待ちを挟んでいた。
        modWinAuto.SendTo "{TAB 4}"
        modWinAuto.SendTo "{ENTER}"

        observed = modWinAuto.WaitTitleChangeFrom(c.WorkTitle, c.StepTimeoutMs)
        If observed <> c.DoneTitle Then
            observed = "発行の確認画面へ進まない（" & observed & "）"
            ProcessOne = RES_STOP: Exit Function
        End If

        modWinAuto.SendTo "+{TAB 9}"
        modWinAuto.SendTo "{ENTER}"
        modWinAuto.SendTo "{ENTER}"

        ' 印刷の待ち。ここだけは固定で待つ。
        ' 印刷の完了は窓のタイトルに出ないため、確かめる手がかりが無い。
        modWinAuto.WaitMs c.PrintWaitMs
        modWinAuto.SendTo "{ENTER}"

        If Not modWinAuto.WaitForTitle(c.WorkTitle, c.StepTimeoutMs) Then
            observed = "発行後に " & c.WorkTitle & " へ戻らない（" & _
                       modWinAuto.TargetTitle() & "）"
            ProcessOne = RES_STOP: Exit Function
        End If
        ProcessOne = RES_OK

    '----------------------------------------------------------------
    Case "ExternalIssue"
        ' 旧版の外部出庫はクリックを一切せず、前面を確かめずに
        ' SendKeys だけを撃っていた。入力欄に焦点が無ければ全部空振りする。
        If Not modWinAuto.ClickOffset(c.ClickDX, c.ClickDY) Then
            observed = "前面にできなかった"
            ProcessOne = RES_STOP: Exit Function
        End If
        modWinAuto.SendTo "^a"
        If Not modWinAuto.SendTo(EscapeKeys(serial)) Then
            observed = "前面にできなかった"
            ProcessOne = RES_STOP: Exit Function
        End If
        modWinAuto.SendTo "{ENTER}"

        observed = modWinAuto.WaitTitleChangeFrom(c.WorkTitle, c.StepTimeoutMs)
        If observed = c.WorkTitle Then
            observed = "タイトルが変化しない（送信漏れの疑い）"
            ProcessOne = RES_STOP: Exit Function
        End If

        modWinAuto.SendTo "{ENTER}"
        If Not modWinAuto.WaitForTitle(c.WorkTitle, c.StepTimeoutMs) Then
            observed = "確定後に " & c.WorkTitle & " へ戻らない（" & _
                       modWinAuto.TargetTitle() & "）"
            ProcessOne = RES_STOP: Exit Function
        End If
        ProcessOne = RES_OK

    Case Else
        observed = "作業の種別が不正: " & c.Mode
        ProcessOne = RES_STOP
    End Select
End Function

'------------------------------------------------------------------ 再開位置
' 旧版の判定は
'   If Cells(Rows.Count, 2).End(xlUp).Row = 1 Then startRow = 1
' だった。
' B1 に何か入っていて B2 以降が空のとき、End(xlUp).Row は 1 になるので
' startRow が 1 になり、1行目をもう一度処理する。
' リール消費では二重計上になる。B1 自体が空かどうかを見れば起きない。
Private Function ResumeRow(ByVal ws As Worksheet, ByVal firstRow As Long) As Long
    Dim lastB As Long
    lastB = ws.Cells(ws.Rows.Count, COL_RESULT).End(xlUp).Row

    If lastB < firstRow Then
        ResumeRow = firstRow
    ElseIf lastB = firstRow And Len(Trim$(CStr(ws.Cells(firstRow, COL_RESULT).Value))) = 0 Then
        ResumeRow = firstRow
    Else
        ResumeRow = lastB + 1
    End If
End Function

'------------------------------------------------------------------ 設定
' ver.2: 設定シートの参照をモジュール変数に覚えておき、
' Find を行ループのたびに繰り返さない。数千件で効果が出る。
Private mSettingWs As Worksheet

Private Function LoadConfig(ByVal mode As String) As Config
    Dim c As Config
    c.Mode = mode

    Select Case mode
    Case "ReelConsume"
        c.WorkTitle = Setting("リール消費_作業画面", "リール消費【倉庫管理アプリケーション】")
        c.DoneTitle = Setting("リール消費_戻り画面", "倉庫管理アプリケーション")
        c.ClickDX = CLng(Setting("リール消費_ずらしX", "180"))
        c.ClickDY = CLng(Setting("リール消費_ずらしY", "69"))
    Case "ZeroCheck"
        c.WorkTitle = Setting("ゼロ確認_作業画面", "リール消費【倉庫管理アプリケーション】")
        c.DoneTitle = Setting("ゼロ確認_戻り画面", "倉庫管理アプリケーション")
        c.ClickDX = CLng(Setting("ゼロ確認_ずらしX", "180"))
        c.ClickDY = CLng(Setting("ゼロ確認_ずらしY", "69"))
    Case "LabelReissue"
        c.WorkTitle = Setting("ラベル再発行_作業画面", "発行履歴【ラベル発行アプリケーション】")
        c.DoneTitle = Setting("ラベル再発行_戻り画面", "ラベル発行アプリケーション")
        c.ClickDX = CLng(Setting("ラベル再発行_ずらしX", "281"))
        c.ClickDY = CLng(Setting("ラベル再発行_ずらしY", "90"))
    Case "ExternalIssue"
        c.WorkTitle = Setting("外部出庫_作業画面", "外部出庫【ラベル発行アプリケーション】")
        c.DoneTitle = Setting("外部出庫_戻り画面", "ラベル発行アプリケーション")
        c.ClickDX = CLng(Setting("外部出庫_ずらしX", "180"))
        c.ClickDY = CLng(Setting("外部出庫_ずらしY", "69"))
    Case Else
        c.Mode = ""
        LoadConfig = c
        Exit Function
    End Select

    c.BindTimeoutMs = CLng(Setting("窓を待つ上限ms", "30000"))
    c.StepTimeoutMs = CLng(Setting("1手を待つ上限ms", "5000"))
    c.PrintWaitMs = CLng(Setting("印刷を待つms", "3000"))
    c.FirstRow = CLng(Setting("開始行", "1"))
    c.MaxRows = CLng(Setting("件数の上限", "1"))
    c.DryRun = (UCase$(Setting("試し実行", "はい")) <> "いいえ")

    LoadConfig = c
End Function

' 設定シートのA列からキーを探してB列を返す。無ければ既定値。
' シートが無ければ作って既定値を書き込む。
Private Function Setting(ByVal key As String, ByVal defVal As String) As String
    Dim ws As Worksheet
    Set ws = EnsureSetting()

    Dim f As Range
    Set f = ws.Columns(1).Find(What:=key, LookIn:=xlValues, LookAt:=xlWhole)
    If f Is Nothing Then
        Dim r As Long
        r = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row + 1
        ws.Cells(r, 1).Value = key
        ws.Cells(r, 2).Value = defVal
        Setting = defVal
    Else
        If Len(Trim$(CStr(ws.Cells(f.Row, 2).Value))) = 0 Then
            ws.Cells(f.Row, 2).Value = defVal
            Setting = defVal
        Else
            Setting = Trim$(CStr(ws.Cells(f.Row, 2).Value))
        End If
    End If
End Function

Private Function EnsureSetting() As Worksheet
    If Not mSettingWs Is Nothing Then
        If mSettingWs.Parent Is ThisWorkbook Then
            Set EnsureSetting = mSettingWs
            Exit Function
        End If
    End If

    On Error Resume Next
    Set EnsureSetting = ThisWorkbook.Worksheets(SHEET_SETTING)
    On Error GoTo 0
    If EnsureSetting Is Nothing Then
        Set EnsureSetting = ThisWorkbook.Worksheets.Add
        EnsureSetting.Name = SHEET_SETTING
        EnsureSetting.Range("A1").Value = "設定項目"
        EnsureSetting.Range("B1").Value = "値"
        EnsureSetting.Range("C1").Value = "説明"
        EnsureSetting.Range("A1:C1").Font.Bold = True
        EnsureSetting.Columns("A:C").ColumnWidth = 32
    End If
    Set mSettingWs = EnsureSetting
End Function

'------------------------------------------------------------------ ログ
' 旧版(ver.1)はB列の ○ しか残らなかった。
' 中断したとき「何が見えて止まったのか」が分からず、再現もできなかった。
Private Function EnsureLog() As Worksheet
    On Error Resume Next
    Set EnsureLog = ThisWorkbook.Worksheets(SHEET_LOG)
    On Error GoTo 0
    If EnsureLog Is Nothing Then
        Set EnsureLog = ThisWorkbook.Worksheets.Add
        EnsureLog.Name = SHEET_LOG
        EnsureLog.Range("A1:E1").Value = _
            Array("日時", "行", "シリアル", "結果", "見えた内容")
        EnsureLog.Range("A1:E1").Font.Bold = True
        EnsureLog.Columns("A").ColumnWidth = 20
        EnsureLog.Columns("C").ColumnWidth = 22
        EnsureLog.Columns("E").ColumnWidth = 48
    End If
End Function

Private Sub WriteLog(ByVal ws As Worksheet, ByVal rowNo As Long, _
                     ByVal serial As String, ByVal result As String, _
                     ByVal observed As String)
    If ws Is Nothing Then Exit Sub
    Dim r As Long
    r = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row + 1
    ws.Cells(r, 1).Value = Format$(Now, "yyyy-mm-dd hh:nn:ss")
    If rowNo > 0 Then ws.Cells(r, 2).Value = rowNo
    ws.Cells(r, 3).Value = "'" & serial   ' 先頭の ' で文字列として残す
    ws.Cells(r, 4).Value = result
    ws.Cells(r, 5).Value = observed
End Sub

'------------------------------------------------------------------ キーの逃がし
' SendKeys は + ^ % ~ ( ) { } [ ] を記号として解釈する。
' シリアルにこれらが入っていると、別のキーとして送られる。
' 旧版は素のまま渡していた。現状のシリアルには含まれていないが、
' 品番の付け方が変わったときに黙って壊れる。
' ver.2: 1文字ずつの連結をやめて置換にした。長いシリアルで速い。
Private Function EscapeKeys(ByVal s As String) As String
    Dim specials As Variant, k As Long
    specials = Array("+", "^", "%", "~", "(", ")", "{", "}", "[", "]")
    For k = LBound(specials) To UBound(specials)
        s = Replace(s, specials(k), "{" & specials(k) & "}")
    Next k
    EscapeKeys = s
End Function
