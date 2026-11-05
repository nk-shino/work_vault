# 網羅調査 exp-2: TOOL.xlam / TOOL_Load.xlam 静的解析(2026-10-19)

- 実施: explorer(読み取り専用・実行なし)。台帳ID: A-04/B-07/B-09
- **重要訂正(台帳A-04)**: `tool_vba.txt` 25,217行のうち実ソースは **1〜5,090行(プロシージャ162個)**。5,091行以降約20,100行は olevba が出力した P-code 逆アセンブル(行頭'コメント)でソースではない。プロシージャ行番号は実ソース側の値

## A. モジュール構成(標準14+フォーム/クラス15)

核心=品目選定ADO.bas(3,671-4,261行): `BuhinKakunin_ADO`(共通部品率)/`Buhinkakunin_btn:3753`/`PrintJob_btn:3962`/`KIBAN_Mail_btn:4159`(容量確認・Job印刷・基板出庫メール)。他: 差分確認関係(2,789・SabunMeisai/ReadHenkouHinmoku)/crb読む(3,434・.crb→MySQL orderNumberBOM登録)/Module6(2,217・job作成シート数式12列挿入等)/UserForm1(262-1,889・CT登録/crb/QR/Tray/Job作成/FIX削除の各タブ)ほか。

デッド/特殊: メルセンヌ・ツイスタ乱数(4,328-4,422・呼出0件)/SASHIZU_Class・品目_Class(使用0件・空)/un.bas(VBA保護解除・182-257)/`testttttt`(2,452・DB直叩きテスト)/`asda`(3,439・他人ホームハードコード)/`csv読み込み`(4,615・E:\RCハードコード・リボン未登録)/`差分確認`スタブ(3,105)。

## B. 外部接続(認証情報の所在のみ記録・値は非扱い)

- MySQL ODBC 8.0 Unicode: nksv1359/QCD(694,979,1,846,1,879)/nksv1359/scheduled(1,192-1,196)/nksv1359/WorkCommunication(2,458)/**nksv569/QCD2(3,593)** — **接続文字列+資格情報が7か所ハードコード**。値は本報告に記載しない(再配布・コミット禁止)
- ACE OLEDB 16.0・adModeRead: `\\nksv523…\Job作成\部品リスト.accdb`(3,778-3,779)
- SQL: CycleTime_Points(707-768)/orderNumberBOM+Log(1,007-1,038↔3,621-3,652=同一文が2実装)/unitInfo+liveOrder(1,202-1,212)/ApplyOrder(2,464)/egproBOM JOIN PartList(3,788,3,814,3,885,3,900)

## C. BOSS計画.xlsm との対照

| 機能 | BOSS計画 | TOOL.xlam | 同等性 |
|---|---|---|---|
| スロット容量判定 | Cal_Capa(vba_code_all.txt:573) | BuhinKakunin_ADO(tool:3,759) | 同一ロジック。集計単位差のみ(BOSS=日付×グループ一括/TOOL=選択品目ごと) |
| 上限90/300/390 | vba:663 | tool:3,933,3,939-3,942 | 同値・**2ブック二重定義(変更時取り違えリスク)** |
| ノズル1000超→3ノズル枠全量 | Cal_Capa内 | tool:3,839-3,848 | 同一 |
| テーブル禁止 x=0.8×(150…270) | なし | tool:3,918-3,929 | TOOLのみ |
| chkTime(時間負荷) | vba:486-567(+getBOSS_btn内835-861に重複実装) | なし | BOSSのみ |
| 安全率の方向 | ÷0.7(工数1.43倍) | ×0.8(禁止判定を縮める) | **別物・混同禁止** |

## D. TOOL_Load.xlam

実体は Workbook_Open 1個のみ(tool_load_vba.txt:50-55): `bin\TOOL.xlam` を開き、自分自身を保存せず即閉じる**ブートストラップ**。リボン「Reload」(tool:2,123-2,129)で JOB作成関連マクロ.xlsm に戻るローダ連鎖。

## E. 再設計観点

- **統合候補**: ①crb→MySQL同期2実装(QCD:836-1,077 vs QCD2:3,458-3,669・同一SQL・接続先分岐=片系が旧番の疑い・要確認) ②MySQL接続7か所→ファクトリ化+DSN外部化 ③容量判定のBOSS/TOOL2ブック重複(定数90/300/390含む) ④日ボタン01-42_Click 42個(2,528-2,696)→単一ハンドラ化で約150行短縮 ⑤印刷範囲解除2実装(102-115/117-126) ⑥CSV選択系2実装(357-548/603-663)
- **性能**: BuhinKakunin_ADOのループ内SQL(品目ごとにSELECT 3,885+SUM 3,900・自らコメント「サブクエリでフィルターするべき いつか修正しよう...」3,884)→GROUP BY 1本化。ReDim TMP_out(1 To 300)(3,879)固定300行=暗黙上限。SQL文字列連結(3,788,3,816,3,885,3,900,707-711,2,464)→パラメータ化。接続都度Open/Close→一元管理
- **保守**: 資格情報平文(本報告では値非扱い)・updateTable_CycleTime_top1が「段取り予定」ブックQueryTable(562)に密結合・デバッグ残骸(MsgBox "Err"/Stop/コメント化ブロック)
