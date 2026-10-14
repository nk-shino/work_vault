Attribute VB_Name = "modEGProB列更新"
Option Explicit

'============================================================
' セットアップレポートとEGPro在庫を照合し「不足部品計算」B列を更新
'   - 未照合は「部品単位」で据え置き(棚卸で調整するためスキップ)
'   - セトレ非掲載部品のみB列0・EGPro未照合は0にしない(据え置き)
'   - 部品番号"0"はフィーダー情報なし扱いで集計対象外
'   - EGPro在庫情報ダウンロードは0確認を"含まない"方を取得
'   - 実行順: 本処理 → 不足部品計算(ジョブ作成のもの)
'   Private Function BackupABでB列更新前のフォルダを指定しています。
'   ver7での変更点は[modEGProB列更新]モジュールの追加です。
'============================================================
Private Const CALC_SHEET As String = "不足部品計算"
Private Const HISTORY_SHEET As String = "りれき"
Private Const RESULT_SHEET As String = "EGPro照合結果"

Public Sub EGPro在庫をB列へ反映()

    Dim wb As Workbook: Set wb = ThisWorkbook
    Dim wsCalc As Worksheet, wsRes As Worksheet, wsHist As Worksheet
    Dim pRep As Variant, pEg As Variant
    Dim setData As Variant, egData As Variant
    Dim parts As Object, serials As Object, egDup As Object, egLoc As Object
    Dim partBad As Object                       ' ★追加:未照合を含む部品(据え置き対象)
    Dim warnings As Collection, zeroParts As Collection, unmatched As Collection
    Dim holdParts As Collection                 ' ★追加:据え置き部品一覧
    Dim setupHeader As Long, partCol As Long, matCol As Long, spliceCol As Long
    Dim i As Long, r As Long, lastRow As Long
    Dim a As Variant, b As Variant, newB As Variant
    Dim part As String, serial As String, q As Double
    Dim msg As String, oldCalc As XlCalculation
    Dim updCnt As Long, holdCnt As Long, zeroCnt As Long

    On Error GoTo EH
    oldCalc = Application.Calculation
    Application.ScreenUpdating = False
    Application.EnableEvents = False
    Application.Calculation = xlCalculationManual

    Set wsCalc = wb.Worksheets(CALC_SHEET)
    Set wsRes = GetOrCreateSheet(wb, RESULT_SHEET)
    Set wsHist = wb.Worksheets(HISTORY_SHEET)
    wsRes.Cells.Clear

    pRep = Application.GetOpenFilename("CSVファイル (*.csv),*.csv", , "L2セットアップレポートCSVを選択")
    If VarType(pRep) = vbBoolean Then GoTo Finally
    pEg = Application.GetOpenFilename("CSVファイル (*.csv),*.csv", , "EGPro在庫CSVを選択")
    If VarType(pEg) = vbBoolean Then GoTo Finally

    setData = ReadCsvToArray(CStr(pRep))   ' UTF-8/CP932自動判定で読込
    egData = ReadCsvToArray(CStr(pEg))

    Set warnings = New Collection
    Set zeroParts = New Collection
    Set unmatched = New Collection
    Set holdParts = New Collection
    Set parts = CreateObject("Scripting.Dictionary"): parts.CompareMode = vbBinaryCompare
    Set serials = CreateObject("Scripting.Dictionary"): serials.CompareMode = vbBinaryCompare
    Set egDup = CreateObject("Scripting.Dictionary"): egDup.CompareMode = vbBinaryCompare
    Set egLoc = CreateObject("Scripting.Dictionary"): egLoc.CompareMode = vbBinaryCompare
    Set partBad = CreateObject("Scripting.Dictionary"): partBad.CompareMode = vbBinaryCompare

    ' 見出し行と列を特定(半角カナは正規化して照合)
    setupHeader = FindHeaderRow(setData, "材料バーコード", "部品番号", "スプライシングリール")
    If setupHeader = 0 Then Err.Raise vbObjectError + 100, , "セットアップレポートの見出し行を特定できません。"
    matCol = FindHeaderCol(setData, setupHeader, "材料バーコード")
    partCol = FindHeaderCol(setData, setupHeader, "部品番号")
    spliceCol = FindHeaderCol(setData, setupHeader, "スプライシングリール")
    If matCol = 0 Or partCol = 0 Or spliceCol = 0 Then Err.Raise vbObjectError + 101, , "セットアップレポートの必要列がありません。"

    ' セトレ:部品ごとに対象リール(材料BC・スプラ)を収集(同一は二重計上しない)
    For r = setupHeader + 1 To UBound(setData, 1)
        part = HeaderKey(setData(r, partCol))
        If part = "0" Then part = ""      ' ★パッチ②:部品番号"0"はフィーダー情報なし扱い
        If part <> "" Then
            AddSerial parts, part, SerialKey(setData(r, matCol))
            AddSerial parts, part, SerialKey(setData(r, spliceCol))
        ElseIf SerialKey(setData(r, matCol)) <> "" Or SerialKey(setData(r, spliceCol)) <> "" Then
            warnings.Add "セトレの部品番号が空欄(行 " & r & ")"
        End If
    Next r

    ' EGPro:1列目シリアル(全空白除去で正規化)→6列目在庫数
    For r = 1 To UBound(egData, 1)
        serial = SerialKey(egData(r, 1))
        If serial <> "" And UBound(egData, 2) >= 6 Then
            If IsNumeric(egData(r, 6)) Then
                If serials.Exists(serial) Then
                    egDup(serial) = True
                Else
                    serials.Add serial, CDbl(egData(r, 6))
                    If UBound(egData, 2) >= 8 Then egLoc(serial) = HeaderKey(egData(r, 8))
                End If
            End If
        End If
    Next r

    ' 対象リールを照合(未照合は「部品単位」で据え置き対象に登録・重複は警告)
    Dim k As Variant, lst As Variant, s As Variant
    For Each k In parts.Keys
        lst = Split(CStr(parts(k)), "|")
        For Each s In lst
            If Not serials.Exists(CStr(s)) Then
                unmatched.Add CStr(s) & " (部品 " & CStr(k) & ")"
                partBad(CStr(k)) = True      ' ★この部品は据え置き対象
            ElseIf egDup.Exists(CStr(s)) Then
                warnings.Add "EGProシリアル重複:" & CStr(s)
            End If
        Next s
    Next k

    ' B列反映値を作成
    '   - セトレ掲載&未照合なし  → EGPro在庫合計で更新
    '   - セトレ掲載&未照合あり  → 据え置き(棚卸で調整)
    '   - セトレ非掲載           → 0
    lastRow = wsCalc.Cells(wsCalc.rows.Count, "A").End(xlUp).Row
    a = wsCalc.Range("A1:A" & lastRow).Value2
    b = wsCalc.Range("B1:B" & lastRow).Value2
    ReDim newB(1 To lastRow, 1 To 1)

    wsRes.Range("A1:G1").value = Array("部品番号", "対象リール数", "EGPro在庫合計", "変更前B列", "変更後B列", "判定", "備考")
    wsRes.Range("A1:G1").Font.Bold = True
    r = 2
    For i = 1 To lastRow
        part = HeaderKey(a(i, 1))
        newB(i, 1) = b(i, 1)                     ' 既定は現状維持
        If i > 1 And part <> "" And part <> "0" Then   ' ★パッチ②:部品番号"0"はB列側も対象外
            If parts.Exists(part) Then
                If partBad.Exists(part) Then
                    ' ★据え置き:未照合を含む部品はB列を変更しない(棚卸で調整)
                    holdParts.Add part
                    holdCnt = holdCnt + 1
                    wsRes.Cells(r, 1).value = part
                    wsRes.Cells(r, 2).value = CountSerials(CStr(parts(part)))
                    wsRes.Cells(r, 3).value = SumSerials(CStr(parts(part)), serials)
                    wsRes.Cells(r, 4).value = b(i, 1)
                    wsRes.Cells(r, 5).value = b(i, 1)      ' 据え置き=変更なし
                    wsRes.Cells(r, 6).value = "保留(据え置き)"
                    wsRes.Cells(r, 7).value = "EGPro未照合を含む・棚卸で調整"
                Else
                    q = SumSerials(CStr(parts(part)), serials)
                    newB(i, 1) = q
                    updCnt = updCnt + 1
                    wsRes.Cells(r, 1).value = part
                    wsRes.Cells(r, 2).value = CountSerials(CStr(parts(part)))
                    wsRes.Cells(r, 3).value = q
                    wsRes.Cells(r, 4).value = b(i, 1)
                    wsRes.Cells(r, 5).value = q
                    wsRes.Cells(r, 6).value = "更新"
                    wsRes.Cells(r, 7).value = "セトレ掲載部品"
                End If
            Else
                newB(i, 1) = 0
                zeroParts.Add part
                zeroCnt = zeroCnt + 1
                wsRes.Cells(r, 1).value = part
                wsRes.Cells(r, 2).value = 0
                wsRes.Cells(r, 3).value = 0
                wsRes.Cells(r, 4).value = b(i, 1)
                wsRes.Cells(r, 5).value = 0
                wsRes.Cells(r, 6).value = "0へ更新"
                wsRes.Cells(r, 7).value = "セトレに存在しない部品"
            End If
            r = r + 1
        End If
    Next i

    ' 独立セクション:0へ更新する部品一覧
    r = r + 1
    wsRes.Cells(r, 1).value = "セトレ非掲載のため0へ更新する部品 (" & zeroParts.Count & "件)"
    wsRes.Cells(r, 1).Font.Bold = True
    For i = 1 To zeroParts.Count
        r = r + 1: wsRes.Cells(r, 1).value = zeroParts(i)
    Next i

    ' 独立セクション:据え置き部品一覧(棚卸で調整)
    r = r + 2
    wsRes.Cells(r, 1).value = "据え置き部品 (" & holdParts.Count & "件) ※未照合を含む・棚卸で調整"
    wsRes.Cells(r, 1).Font.Bold = True
    For i = 1 To holdParts.Count
        r = r + 1: wsRes.Cells(r, 1).value = holdParts(i)
    Next i

    ' 独立セクション:EGPro未照合リール一覧(参考・0にはしない)
    r = r + 2
    wsRes.Cells(r, 1).value = "EGPro未照合リール (" & unmatched.Count & "件) ※据え置き部品の内訳"
    wsRes.Cells(r, 1).Font.Bold = True
    For i = 1 To unmatched.Count
        r = r + 1: wsRes.Cells(r, 1).value = unmatched(i)
    Next i

    ' 独立セクション:警告一覧
    If warnings.Count > 0 Then
        r = r + 2
        wsRes.Cells(r, 1).value = "警告一覧 (" & warnings.Count & "件)"
        wsRes.Cells(r, 1).Font.Bold = True
        For i = 1 To warnings.Count
            r = r + 1: wsRes.Cells(r, 1).value = warnings(i)
        Next i
    End If

    wsRes.Columns.AutoFit

    ' ★安全側の全中止は「EGProシリアル重複(=warnings)」のみ維持
    '   未照合は据え置きに変更したため全中止しない
    If warnings.Count > 0 Then
        MsgBox "EGProシリアル重複などの警告があるため、B列は更新していません。" & vbCrLf & _
               "「EGPro照合結果」シートの警告一覧を確認してください。" & vbCrLf & vbCrLf & _
               "警告:" & warnings.Count & "件", vbExclamation
        GoTo Finally
    End If

    ' 実行前サマリ(更新/据え置き/0化の件数を提示)
    msg = "照合が完了しました。B列を更新します。" & vbCrLf & vbCrLf & _
          "  更新する部品      : " & updCnt & " 件" & vbCrLf & _
          "  据え置き(棚卸調整): " & holdCnt & " 件" & vbCrLf & _
          "  0へ更新(非掲載)   : " & zeroCnt & " 件" & vbCrLf & vbCrLf & _
          "据え置き部品はEGPro未照合を含むため変更しません。" & vbCrLf & _
          "実行しますか。"
    If MsgBox(msg, vbYesNo + vbQuestion) <> vbYes Then GoTo Finally

    ' B列書き込み直前に退避(確認「はい」の後)
    Dim bkPath As String
    bkPath = BackupAB(wsCalc)

    WriteHistory wsHist, a, b, newB, CStr(pRep), CStr(pEg)
    wsCalc.Range("B1:B" & lastRow).value = newB
    Application.CalculateFull
    ThisWorkbook.Save
    MsgBox "B列の更新が完了しました。" & vbCrLf & _
           "更新 " & updCnt & "件 / 据え置き " & holdCnt & "件 / 0化 " & zeroCnt & "件" & vbCrLf & _
           "退避ファイル: " & bkPath, vbInformation

Finally:
    On Error Resume Next
    Application.Calculation = oldCalc
    Application.EnableEvents = True
    Application.ScreenUpdating = True
    Exit Sub
EH:
    MsgBox "処理を中止しました。B列は更新していません。" & vbCrLf & Err.Description, vbCritical
    Resume Finally
End Sub

Private Sub AddSerial(ByVal d As Object, ByVal part As String, ByVal serial As String)
    Dim x As String
    If part = "" Or serial = "" Then Exit Sub
    If d.Exists(part) Then
        x = CStr(d(part))
        If InStr(1, "|" & x & "|", "|" & serial & "|", vbBinaryCompare) = 0 Then d(part) = x & "|" & serial
    Else
        d.Add part, serial
    End If
End Sub

Private Function SumSerials(ByVal x As String, ByVal d As Object) As Double
    Dim v As Variant, n As Double
    For Each v In Split(x, "|")
        If d.Exists(CStr(v)) Then n = n + CDbl(d(CStr(v)))
    Next v
    SumSerials = n
End Function

Private Function CountSerials(ByVal x As String) As Long
    If x = "" Then CountSerials = 0 Else CountSerials = UBound(Split(x, "|")) + 1
End Function

' 見出し・部品番号用:半角カナを全角へ正規化し前後空白を除去
Private Function HeaderKey(ByVal v As Variant) As String
    If IsError(v) Or IsEmpty(v) Then
        HeaderKey = ""
    Else
        HeaderKey = Trim$(StrConv(CStr(v), vbWide))
    End If
End Function

Private Function SerialKey(ByVal v As Variant) As String
    Dim s As String
    If IsError(v) Or IsEmpty(v) Then
        SerialKey = ""
        Exit Function
    End If
    s = CStr(v)
    s = Replace(s, " ", "")
    s = Replace(s, ChrW$(&H3000), "")
    s = Replace(s, vbTab, "")
    SerialKey = s
End Function
Private Function FindHeaderRow(ByVal a As Variant, ByVal h1 As String, ByVal h2 As String, ByVal h3 As String) As Long
    Dim r As Long, c As Long, s As String, n As Long
    For r = 1 To UBound(a, 1)
        n = 0
        For c = 1 To UBound(a, 2)
            s = HeaderKey(a(r, c))
            If s = h1 Or s = h2 Or s = h3 Then n = n + 1
        Next c
        If n >= 2 Then FindHeaderRow = r: Exit Function
    Next r
End Function

Private Function FindHeaderCol(ByVal a As Variant, ByVal r As Long, ByVal h As String) As Long
    Dim c As Long
    For c = 1 To UBound(a, 2)
        If HeaderKey(a(r, c)) = h Then FindHeaderCol = c: Exit Function
    Next c
End Function

Private Function GetOrCreateSheet(ByVal wb As Workbook, ByVal n As String) As Worksheet
    On Error Resume Next
    Set GetOrCreateSheet = wb.Worksheets(n)
    On Error GoTo 0
    If GetOrCreateSheet Is Nothing Then
        Set GetOrCreateSheet = wb.Worksheets.Add(AFTER:=wb.Worksheets(wb.Worksheets.Count))
        GetOrCreateSheet.Name = n
    End If
End Function

Private Sub WriteHistory(ByVal ws As Worksheet, ByVal a As Variant, ByVal b As Variant, ByVal nb As Variant, ByVal p1 As String, ByVal p2 As String)
    Dim c As Long, i As Long
    c = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column + 2
    ws.Cells(1, c).value = "EGPro在庫反映"
    ws.Cells(2, c).value = "実行日時": ws.Cells(2, c + 1).value = Now
    ws.Cells(3, c).value = "セトレ": ws.Cells(3, c + 1).value = p1
    ws.Cells(4, c).value = "EGPro": ws.Cells(4, c + 1).value = p2
    ws.Cells(5, c).value = "部品番号": ws.Cells(5, c + 1).value = "変更前→変更後"
    For i = 2 To UBound(a, 1)
        ws.Cells(5 + (i - 1), c).value = a(i, 1)
        ws.Cells(5 + (i - 1), c + 1).value = CStr(b(i, 1)) & "→" & CStr(nb(i, 1))
    Next i
End Sub

Private Function BackupAB(ByVal wsCalc As Worksheet) As String
    Dim wb As Workbook, backupPath As String, baseName As String
    Const BACKUP_DIR As String = _
        "\\nksv523.ad.nkc.co.jp\第二工場実装課用\1係用\Job作成\不足部品リスト関係\01_buckup_B列更新前_ver7"

    Set wb = wsCalc.parent
    If wb.path = "" Then
        Err.Raise vbObjectError + 2001, , "バックアップを作成できません。先にブックを保存してください。"
    End If

    EnsureFolder BACKUP_DIR   ' ★多階層でも作成

    baseName = wb.Name
    If InStrRev(baseName, ".") > 0 Then baseName = Left$(baseName, InStrRev(baseName, ".") - 1)

    backupPath = BACKUP_DIR & Application.PathSeparator & _
                 baseName & "_B列更新前_" & Format(Now, "yyyymmdd_hhnnss") & ".xlsm"

    On Error GoTo SaveErr
    wb.SaveCopyAs backupPath
    On Error GoTo 0

    BackupAB = backupPath
    Exit Function
SaveErr:
    Err.Raise vbObjectError + 2002, , _
        "退避先へ保存できませんでした。共有フォルダのパス/権限/接続を確認してください。" & vbCrLf & backupPath
End Function

' 多階層フォルダを再帰的に作成（UNC対応）
Private Sub EnsureFolder(ByVal path As String)
    Dim parent As String
    If Len(Dir(path, vbDirectory)) > 0 Then Exit Sub
    parent = Left$(path, InStrRev(path, "\") - 1)
    ' UNCのサーバー\共有ルート（\\server\share）まで来たら止める
    If InStr(3, parent, "\") = 0 Then Exit Sub
    EnsureFolder parent
    On Error Resume Next
    MkDir path
    On Error GoTo 0
End Sub

'============================================================
' CSVを文字コード自動判定(UTF-8優先)で読み、2次元配列(1始まり)で返す
'============================================================
Private Function ReadCsvToArray(ByVal filePath As String) As Variant
    Dim stm As Object, allText As String

    If Dir(filePath) = "" Then
        Err.Raise vbObjectError + 300, , _
            "ファイルが見つかりません: " & filePath
    End If

    On Error GoTo ReadErr

    Set stm = CreateObject("ADODB.Stream")
    stm.Type = 2                       ' adTypeText
    stm.Charset = "UTF-8"
    stm.Open
    stm.LoadFromFile filePath
    allText = stm.ReadText(-1)
    stm.Close: Set stm = Nothing

    If InStr(1, allText, ChrW(&HFFFD)) > 0 Then
        Set stm = CreateObject("ADODB.Stream")
        stm.Type = 2
        stm.Charset = "shift_jis"      ' = CP932
        stm.Open
        stm.LoadFromFile filePath
        allText = stm.ReadText(-1)
        stm.Close: Set stm = Nothing
    End If

    If Len(allText) > 0 Then
        If AscW(Left$(allText, 1)) = -257 Then allText = Mid$(allText, 2)
    End If

    allText = Replace(allText, vbCrLf, vbLf)
    allText = Replace(allText, vbCr, vbLf)

    ReadCsvToArray = ParseCsv(allText)
    Exit Function

ReadErr:
    If Not stm Is Nothing Then
        On Error Resume Next
        stm.Close
        On Error GoTo 0
        Set stm = Nothing
    End If
    Err.Raise vbObjectError + 301, , _
        "CSVの読み込みに失敗しました。" & vbCrLf & _
        "ファイル: " & filePath & vbCrLf & _
        "詳細: " & Err.Description
End Function

Private Function ParseCsv(ByVal s As String) As Variant
    Dim rows As Collection, fields As Collection
    Dim i As Long, ch As String, cur As String
    Dim inQ As Boolean
    Set rows = New Collection
    Set fields = New Collection
    inQ = False: cur = ""

    For i = 1 To Len(s)
        ch = Mid$(s, i, 1)
        If inQ Then
            If ch = """" Then
                If i < Len(s) And Mid$(s, i + 1, 1) = """" Then
                    cur = cur & """": i = i + 1
                Else
                    inQ = False
                End If
            Else
                cur = cur & ch
            End If
        Else
            Select Case ch
                Case """": inQ = True
                Case ",": fields.Add cur: cur = ""
                Case vbLf
                    fields.Add cur: cur = ""
                    rows.Add CollectionToArray(fields)
                    Set fields = New Collection
                Case Else: cur = cur & ch
            End Select
        End If
    Next i
    If cur <> "" Or fields.Count > 0 Then
        fields.Add cur
        rows.Add CollectionToArray(fields)
    End If

    Dim rCount As Long, cCount As Long, rowArr As Variant, j As Long
    rCount = rows.Count
    For i = 1 To rCount
        rowArr = rows(i)
        If (UBound(rowArr) + 1) > cCount Then cCount = UBound(rowArr) + 1
    Next i
    If rCount = 0 Then rCount = 1
    If cCount = 0 Then cCount = 1

    Dim arr() As Variant
    ReDim arr(1 To rCount, 1 To cCount)
    For i = 1 To rows.Count
        rowArr = rows(i)
        For j = 0 To UBound(rowArr)
            arr(i, j + 1) = rowArr(j)
        Next j
    Next i
    ParseCsv = arr
End Function

Private Function CollectionToArray(ByVal c As Collection) As Variant
    Dim a() As String, i As Long
    ReDim a(0 To c.Count - 1)
    For i = 1 To c.Count
        a(i - 1) = CStr(c(i))
    Next i
    CollectionToArray = a
End Function



