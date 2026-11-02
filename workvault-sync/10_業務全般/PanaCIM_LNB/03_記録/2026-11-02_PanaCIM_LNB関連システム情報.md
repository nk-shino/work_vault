---
type: note
phase: operate
status: active
project: PanaCIM_LNB
updated: 2026-11-02
---

# PanaCIM・LNB関連システム情報(共有サーバー所在)

**2026-11-02 時点。PanaCIM管理文書・相関図の素材候補として、共有サーバー上のシステム所在をまとめたもの。**

出所: 2026-11-02 に共有サーバー \\nksv569.ad.nkc.co.jp の2共有(Share・WWW、計408,760ファイル)へキーワード「アンドン」で総合検索した際に把握した所在。ファイル名一致131件・内容一致12件。照合はUTF-8/CP932両系の文字コードで行い、Officeファイルは内部XMLまで展開して照合した。圧縮アーカイブ内部のファイルとOffice埋込画像は対象外。

## 関わりがありそうなシステム

### 1. Pana-CIM レポート収集(mnt\DGS-SV 直下)

- 場所: `\\nksv569.ad.nkc.co.jp\Share\mnt\DGS-SV\Pana-CIM_report\`
- 構成: `robocopy.bat`・`log.log`・`DIR\`
- `DIR\` 下に **L1/L2/L3 機種切り替えレポート・稼働時間レポートのCSV**(各ライン、毎営業日10:00/10:05出力、2026-01-23〜2026-10-31分の存在を確認)と `Daily\`・`Monthly\`・`Shift\`・`Weekly\`・`個別レポート\` のサブフォルダ。
- Pana-CIMが出力するレポートの収集先。robocopy.bat が取得元から集めている構成と推定(batの中身は未確認)。

### 2. PanaCIM 関連データ一式(★個人フォルダ配下)

- 場所: `\\nksv569.ad.nkc.co.jp\Share\mnt\DGS-SV\★個人フォルダ\PanaCIM\`
- 構成: `Historical\`・`Log\`・`Production\`・`Utils\`
- `Production\RestoreLog\RestoreDB_Log_20201226.log` — DB復元のログ(2020-12-26時点。キーワードの内容一致を確認)。
- 実行サーバー本体は別にある可能性。データ退避・参照用の所在と推定(未確認)。

### 3. MonitorAndon2(アンドンモニタ・EGPro-KOHDENクライアント)

本体が3所在(配置からEGProのクライアント構成と推定):

```
\\nksv569.ad.nkc.co.jp\Share\mnt\DGS-SV\EGP_たぶん古い\EGPro-KOHDEN\Client\MonitorAndon2\
(exe・exe.config・ini)

\\nksv569.ad.nkc.co.jp\Share\mnt\DGS-SV\Line-1 EGPro データ退避\EGPro-KOHDEN\Client\Application\MonitorAndon2\
(exe・exe.config・ini)

\\nksv569.ad.nkc.co.jp\Share\mnt\DGS-SV\★個人フォルダ\佐藤\エラー調査\MonitorAndon2\Log\
(実行ログ MonitorAndon2_YYYYMMDD.LOG ×123、2022-07-01〜11-26)
```

補足:

- `Line-1 EGPro データ退避\Desktop\L1_アンドン.url` — アンドン画面へのショートカット。URL中身は未確認(認証情報を含む可能性のため転記しない)。
- `整理\1\MonitorAndon2_20220210.LOG` — 整理フォルダに単体のログ1本。
- ini・config の中身は未読(設定値の転記はしない方針)。ini内に「アンドン」という語を含むことまでは確認済み。

### 4. EGPro-KOHDEN(生産データシステム)周辺

- `mnt\DGS-SV` 直下に `EGPro-KOHDEN\`・`EGP_たぶん古い\`・`Line-1 EGPro データ退避\` の3系統。MonitorAndon2 はこの配下にある。
- 周辺には `■1Line_JOB\`・`■2Line_JOB\`・`■3Line_JOB\`・`bat\`・`SQL文\`・`sqlcmd\`・`◎棚卸し\`・`稼働率\`・`計画\` などのフォルダ(ライン別JOB・SQL・集計系)。
- BOSS計画・生産負荷シミュレーション(鹿島引き込み案件)が参照するデータ源でもある。

### 5. qcd_DB(WWW共有・Python製Webシステム)

- 場所: `\\nksv569.ad.nkc.co.jp\WWW\cgi\qcd_DB\`
- 構成: `Debug\`・`Release\`(ともに `Main.py`・`ManualUpdate.py`・`html\`・`Mod\`)・`etc\env\`・`Files\`
- `Files\` 下: mdbtools 1.0.0 / 1.0.0-beta7(展開済み+tar.gz)・`perl\`・`websocket\`・`差分チェックシステムのバックアップ\`・`イメージ図.dio`・`イメージ図.png`・`サーバー設定メモ.txt`
- mdbtools(LinuxからAccess(mdb)を読むツール)を同梱していることから、**QCDデータをAccess DBで持ち、Web画面(Python)で閲覧するシステム**と推定。cgi配下にありwebsocket対応。
- `イメージ図.dio`(drawio形式)はシステム構成を図示した素材の可能性があり、相関図作成時の参照候補(中身未確認)。
- 設定メモ・env・Main.py は未読(認証情報を含む可能性のため。中身を見る場合は利用者が開くこと)。

### 6. LNB

- 今回の検索ではLNB関連の新所見なし。
- LNB = Line Network Box(LNB管理書 §3・2026-10-14確定)。iLNBとの同一性は未確認(W43からの持ち越し事項)。

## 確定・推定・未確認

- **確定**: 上記の所在と構成(2026-11-02に実在を確認)。
- **推定**: qcd_DBの用途(mdbtools同梱からの推定)・MonitorAndon2がEGPro系クライアントであること(配置からの推定)・Pana-CIM_reportがrobocopy収集であること。
- **未確認**: PanaCIM本体(実行サーバー)の所在・qcd_DBとPanaCIM/LNBの関係・MonitorAndon2とPanaCIMの連携の有無・Pana-CIM_reportの取得元・iLNB同一性。

## 関連ノート

- `../01_成果物/管理書.md`(Pana-CIM側正本)
- `../01_成果物/LNB管理書.md`(LNB側正本)
- `../01_成果物/PanaCIM_点検文書_情報記入シート.md`・`../01_成果物/LNB_点検文書_情報記入シート.md`
- `2026-11-02_相関図LNBStage5適用.md`
- `../README_管理規則.md`
