---
type: note
phase: operate
status: active
project: PanaCIM_LNB
updated: 2026-11-10
---

# VMware ESXi 6.7 公式情報(トラブルシューティング·パッチ適用·バージョンアップ)

**2026-11-10 時点。使用中の ESXi 6.7.0(ビルド17167734)と VMware Host Client 1.33.7(ビルド15803439)を対象に、公式ドキュメントと KB から収集した情報を整理したもの。以後の加工(手順書·管理書への反映)を前提とし、出典 URL と未確認事項を区別して記載する。**

## 0. この文書について

- 出典は VMware(Broadcom)の公式ドキュメントと KB のみ。取得日はすべて 2026-11-10。
- `docs.vmware.com` は 2026-11-10 時点で `techdocs.broadcom.com` へ全面リダイレクトされている。6.7 の個別ページは転送先に存在しないため(404)、本文の取得には Wayback Machine のアーカイブ(公式ページのスナップショット)を用いた。各項目は「元の公式 URL」と「参照したアーカイブ URL」を併記する。
- 6.7 の公式ドキュメント本体は TechDocs の「vSphere Legacy Releases」から PDF で提供されている。
- KB は `knowledge.broadcom.com` の新記事 ID(6桁)に統一されている。旧 KB 番号は `?legacyId=` 形式でリダイレクトされる。本文では「新 ID / 旧 ID」を併記する。確認できた ID のみ記載し、推測した番号は記載していない。
- 確認できた事実と、確認できなかった事項(未確認)を区別する。未確認事項は §7 にまとめた。
- コマンドは ESXi 6.7 で有効なものを記載する。

## 1. 対象環境

| 項目 | 値 |
|---|---|
| ハイパーバイザー | ESXi 6.7.0(ビルド17167734) |
| クライアント | VMware Host Client 1.33.7(ビルド15803439) |
| 管理形態 | 不明(vCenter 管理下かスタンドアロンか未確認) |

- 2026-11-09 のキャプチャ記録(`02_参照元/VMwareキャプチャ/`)ではビルド8169922(6.7 GA。2020-12-23 時点の VIB 導入状態)だった。現行のビルド17167734 はこれと異なり、その間に更新が適用されている。ビルド17167734 の正確なパッチ対応は §2 を参照。
- 管理形態が不明のため、本資料はスタンドアロン(Host Client 直結)と vCenter 管理下の双方に触れる。vCenter 固有の手順(vpxa·vpxd 等)は該当環境でのみ使用する。

## 2. バージョン特定とサポート状況

本環境のビルド17167734 は、KB 316595 の対応表で **ESXi 6.7 P04(ESXi670-202011002)** に一致する。

| 項目 | 値 |
|---|---|
| パッチ名 | ESXi670-202011002(6.7 P04) |
| リリース日 | 2020-11-19 |
| 種別 | Patch |
| ビルド | 17167734 |
| ロールアップ Bulletin | ESXi670-202011002(Bugfix / Critical) |

**リリースノート記載事項**(ESXi 6.7 Release Notes: ESXi670-202011002)
元 URL: `https://docs.vmware.com/en/VMware-vSphere/6.7/rn/esxi670-202011002.html`
参照: https://web.archive.org/web/2023id_/https://docs.vmware.com/en/VMware-vSphere/6.7/rn/esxi670-202011002.html

| 項目 | 値 |
|---|---|
| ダウンロードファイル | ESXi670-202011002.zip(475.3 MB) |
| md5 | `ba6c848559c291809bcb0e81d2c60a0c` |
| sha1 | `073ab9895c9db6e75ab38e41e5d79cbb37a5f760` |
| ホストの再起動 | 必要 |
| VM の移行またはシャットダウン | 必要 |

含まれる Bulletin:

| Bulletin | 種別 | 重大度 |
|---|---|---|
| ESXi670-202011401-BG | Bugfix | Critical |
| ESXi670-202011402-BG | Bugfix | Important |
| ESXi670-202011403-BG | Bugfix | Moderate |
| ESXi670-202011404-BG | Bugfix | Important |
| ESXi670-202011101-SG | Security | Critical |

Image Profile(オフライン バンドルに収録):

- `ESXi-6.7.0-20201104001-standard` / `ESXi-6.7.0-20201104001-no-tools`
- `ESXi-6.7.0-20201101001s-standard` / `ESXi-6.7.0-20201101001s-no-tools`

**6.7 のパッチ系列**(KB 316595、2026-11-10 取得)

| パッチ | パッチ名 | リリース日 | ビルド |
|---|---|---|---|
| GA | ESXi 6.7 GA | 2018-04-17 | 8169922 |
| U3 | ESXi 6.7 U3 | 2019-08-20 | 14320388 |
| **P04(本環境)** | **ESXi670-202011002** | **2020-11-19** | **17167734** |
| EP 18 | ESXi670-202102001 | 2021-02-23 | 17499825 |
| P05 | ESXi670-202103001 | 2021-03-18 | 17700523 |
| P06 | ESXi670-202111001 | 2021-11-23 | 18828794 |
| EP 23 | ESXi670-202201001 | 2022-01-25 | 19195723 |
| P07 | ESXi670-202206001 | 2022-06-14 | 19898906 |
| EP 24 | ESXi670-202207001 | 2022-07-12 | 19997733 |
| **P08(最終)** | **ESXi670-202210001** | **2022-10-06** | **20497097** |

**サポート状況**

| 項目 | 日付 | 出典 |
|---|---|---|
| 一般サポート終了(EOGS) | 2022-10-15 | KB 326984(6.5/6.7/vSAN 6.5/6.6/6.7 の EOGS) |
| テクニカルガイダンス終了(EOTG) | 2023-11-15 | VMware ライフサイクル告知(EOGS の1年後) |

2026-11-10 時点で 6.7 はサポート期間外。6.7 の最終パッチは P08(2022-10-06)で、これ以降の 6.7 向けパッチは提供されていない。

**Host Client の版**

- Host Client は `esx-ui` VIB として ESXi に同梱される。1.33.7-15803439 は ESXi670-202004002(6.7 P02)系で提供された版(セキュリティ Bulletin ESXi670-202004103-SG に対応)。
- 本環境はビルド17167734(P04)で、Host Client 1.33.7(ビルド15803439)が動作している(2026-11-09 キャプチャ)。

## 3. パッチ適用

6.7 は Image Profile ベースの更新方式である。公式の適用方法は、vCenter 管理下での vSphere Update Manager(VUM)と、ESXi Shell の `esxcli` による方法。KB 343840 がコマンドライン手順を示す。

**前提**

- ホスト構成のバックアップ(KB 313510)
- パッチのダウンロード(KB 372545。Broadcom Support Portal の Products=ベースリリース、Solutions=パッチ。ダウンロードには対象版のライセンスが必要)
- メンテナンスモードへの移行

**手順(KB 343840)**

1. 構成バックアップ

```bash
vim-cmd hostsvc/firmware/sync_config
vim-cmd hostsvc/firmware/backup_config
```

出力される URL(例 `http://<host>/downloads/123456/configBundle-<ip>.tgz`)からバンドルを取得する。復元は `configBundle.tgz` を `/tmp` に置き、メンテナンスモードで `vim-cmd hostsvc/firmware/restore_config 0`。前提は「復元先のビルドがバックアップ時と同一」「ホスト UUID が同一」。

2. パッチをデータストアへアップロード(新規ディレクトリを推奨)

3. メンテナンスモードへ移行(KB 311213)

```bash
vim-cmd /hostsvc/maintenance_mode_enter
vim-cmd /hostsvc/hostsummary | grep inMaintenanceMode
```

4. オフライン バンドル内のプロファイルを一覧

```bash
esxcli software sources profile list -d /vmfs/volumes/<datastore>/<folder>/<patch>.zip
```

5. プロファイル更新(推奨)

```bash
esxcli software profile update -p <Image_Profile> -d /vmfs/volumes/<datastore>/<folder>/<patch>.zip
```

- `update` は新しい内容を適用し、リビジョンが低い VIB は無視する(KB 343840)。
- `install` はプロファイルを上書きし、プロファイルにない VIB を削除し得る(侵襲的)。ダウングレードには `--allow-downgrade` が必要。
- VIB 単位の更新も可能: `esxcli software vib update -d <zip>`(KB 343840。8.0 Update 2 以降は upgrade/update に非対応。6.7 では使用可)。

6. 再起動とメンテナンスモード解除

```bash
esxcli system shutdown reboot -r 'apply patch'
vim-cmd hostsvc/maintenance_mode_exit
```

7. 適用後の確認

```bash
vmware -v
esxcli software profile get
```

**本環境での適用先**

- P04(17167734)→ 最終 P08(ESXi670-202210001 / 20497097 / 2022-10-06)。6.7 のパッチは P08 で終了している。
- ハードウェア警告の迂回オプション `--no-hardware-warning` は 6.7 Update 1 以降で使用できる(KB 82794)。KB 343840 は本番環境で検証を迂回しないよう注記している。

## 4. バージョンアップ経路

**公式の順序**

- vCenter Server を ESXi ホストより先にアップグレードする(サポートされる順序。KB 390293)。vCenter 管理下の環境では、この順序で実施する。
- スタンドアロン(Host Client 直結)の場合は ESXi 単体のアップグレードとなる。

**アップグレード方法(7.0 / 8.0 共通、5種)**(KB 390293)

1. 対話式(CD / DVD / USB / ISO イメージ)
2. `esxcli`
3. スクリプト
4. Auto Deploy
5. vSphere Lifecycle Manager

**アップデート順序**

- vSphere 8.0: KB 308161「Update Sequence for VMware vSphere 8.0 and Compatible VMware Products」
- vSphere 7.0: KB 317899(KB 390293 が参照。2026-11-10 時点で記事ページは 404)。KB 330373 に各バージョンの更新順序記事の一覧がある(7.0 は旧 ID 78221)。

**アップグレード経路の確認**

- Interoperability Matrix の Upgrade Path で、現在の版から対象版への互換を確認する。
  - ESXi: https://interopmatrix.broadcom.com/Upgrade?productId=1&isHidePatch=true&isHideLegacyReleases=false
  - vCenter: `productId=2` / vSAN: `productId=1746`(KB 326984 にも同リンク)
- 2026-11-10 時点の表示: **ESXi 6.7 U3 → 8.0 / 8.0U1 / 8.0U2 / 8.0U3 は Compatible**。7.0 / 7.0U1 / 7.0U2 / 7.0U3 も Compatible。9.x は非互換(表示なし)。
  - マトリクスの行は「6.7 U3」。本環境のビルド17167734 は 6.7 U3 系のパッチ P04 である。
  - 脚注: 6.7 は legacy release(lifecycle.vmware.com を参照)。

**確認事項**

- ハードウェアの互換性(HCL)は Compatibility Guide(https://compatibilityguide.broadcom.com/)で確認する。
- ゲスト OS(本環境は RHEL 6)のサポート状況は Compatibility Guide の Guest OS 互換で確認する。
- 6.7 は EOGS / EOTG 済み(§2)。アップグレード先の選定は、ハードウェア更新の計画と合わせて別途判断する。

## 5. 障害対応

### 5.1 ログの場所と読み方

#### 5.1.1 公式のログ一覧(6.7)

出典: vSphere 6.7「vSphere Monitoring and Performance」ESXi Log File Locations
元 URL: `https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.monitoring.doc/GUID-832A2618-6B11-4A28-9672-93296DA931D0.html`
参照: https://web.archive.org/web/2023id_/https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.monitoring.doc/GUID-832A2618-6B11-4A28-9672-93296DA931D0.html

| コンポーネント | 場所 | 公式の目的記載 |
|---|---|---|
| VMkernel | `/var/log/vmkernel.log` | 仮想マシンおよび ESXi に関するアクティビティを記録 |
| VMkernel warnings | `/var/log/vmkwarning.log` | 仮想マシンに関するアクティビティを記録 |
| VMkernel summary | `/var/log/vmksummary.log` | 稼働時間·可用性の統計(カンマ区切り) |
| ESXi host agent | `/var/log/hostd.log` | ESXi ホストと VM を管理·構成するエージェントの情報 |
| vCenter agent | `/var/log/vpxa.log` | vCenter Server と通信するエージェントの情報(vCenter 管理下のときのみ) |
| Shell | `/var/log/shell.log` | ESXi Shell に入力された全コマンドと Shell イベント(有効化履歴を含む) |
| Authentication | `/var/log/auth.log` | ローカルシステムの認証イベント |
| System messages | `/var/log/syslog.log` | 一般的なログ。トラブルシューティング用(旧 messages ログ) |
| 仮想マシン | VM の構成ファイルと同じディレクトリの `vmware.log` / `vmware*.log` | 電源イベント、障害情報、Tools 状態、時刻同期、仮想ハードウェア変更、vMotion、クローン等 |

**6.7 の公式一覧表に載っていないログ**

- `vobd.log`: 上記 6.7 一覧表には記載なし。ただし KB 318850 は APD 調査の参照先として `/var/run/log/vobd.log` を明記している。
- `esxupdate.log`: 上記 6.7 一覧表には記載なし(パッチ適用時に関連するログとして広く参照されるが、6.7 公式一覧での記載は確認できなかった)。

#### 5.1.2 ログの保存特性(揮発性)

出典: vSphere 6.7「vSphere Security」Securing ESXi Hosts
元 URL: `https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.security.doc/GUID-F35D7005-58EB-48AC-99D5-B9942EB2A8EF.html`
参照: https://web.archive.org/web/2023id_/https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.security.doc/GUID-F35D7005-58EB-48AC-99D5-B9942EB2A8EF.html

- 既定では ESXi のログはインメモリファイルシステム上に保存される。
- そのためホスト再起動で失われ、保持されるのは約24時間分のみ。
- 対策としてデータストアへの永続ログ保存(persistent logging)とリモート syslog 転送が推奨されている。

初動では「再起動していないか」「永続ログを設定しているか」を先に確認する。設定していない場合、証拠が残っていない可能性がある。syslog 設定は同ガイドの「Configure Syslog on ESXi Hosts」(`GUID-9F67DB52-F469-451F-B6C8-DAE8D95976E7`)に記載があり、vSphere Client または `esxcli system syslog` で構成する。

補足: `/var/log` は実体として `/var/run/log` と同じ領域を指すため、KB では `/var/run/log/vmkernel.log` と表記されることがある(KB 318712·318850·456421 は `/var/run/log/...` 表記)。どちらでアクセスしても同一ログである。

#### 5.1.3 確認の優先順位(実務上の推奨)

公式に「この順で見る」という規定は確認できなかった。以下は各 KB の参照先を整理した実務上の推奨順であり、公式見解ではない。

1. `/var/log/vmksummary.log` — いつ再起動したか、稼働状況の当たりを付ける
2. `/var/log/vmkernel.log` — PSOD·ストレージ I/O エラー·NMP/PSA·死活(heartbeat/starvation)
3. `/var/log/vmkwarning.log` — vmkernel の警告のダイジェスト
4. `/var/log/hostd.log` — 管理エージェント異常(API 失敗、OOM、設定破損)。esxcli が固まる事象の主战场
5. `/var/log/vpxa.log` — vCenter との通信断(vCenter 管理下のみ)
6. `/var/log/vobd.log` — APD/PDL など vobd イベント(`esx.problem.storage.apd.start` 等)
7. `/var/log/syslog.log` / `auth.log` / `shell.log` — 全般、認証、作業履歴

#### 5.1.4 UI からの閲覧

- DCUI: 「View System Logs」→ 番号キーでログ選択 → Enter/スペースでスクロール → `/` で正規表現検索 → `q` で戻る。vCenter 管理下では vpxa ログが表示される、と公式に明記。
  出典: vSphere 6.7 View System Logs on an ESXi Host
  `https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.monitoring.doc/GUID-498D2802-4802-4F18-B8B2-D398D45BE249.html`
  参照: https://web.archive.org/web/2023id_/https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.monitoring.doc/GUID-498D2802-4802-4F18-B8B2-D398D45BE249.html
- Host Client: Host → Monitor → Logs で主要ログをブラウザ閲覧(6.7 Host Client の標準機能)。

### 5.2 サポートバンドル(vm-support)

#### 5.2.1 SSH / ESXi Shell(公式の基本手順)

出典: vSphere 6.7「Collect ESXi Log Files」
元 URL: `https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.monitoring.doc/GUID-4A172F04-2593-4819-99A2-9BEB7D7F4037.html`
参照: https://web.archive.org/web/2023id_/https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.monitoring.doc/GUID-4A172F04-2593-4819-99A2-9BEB7D7F4037.html

公式記載: ESXi Shell で `/usr/bin/vm-support` を実行。生成ファイル名は `esx-date-unique-xnumber.tgz`。

```bash
/usr/bin/vm-support
```

出典: KB 313542「Collecting diagnostic information for VMware ESX/ESXi using vm-support command」
https://knowledge.broadcom.com/external/article/313542

```bash
# 保存先をデータストアに指定
vm-support -w /vmfs/volumes/DATASTORE_NAME

# オプション一覧
vm-support -h

# SSH 経由でストリーム取得(lockdown mode では不可)
ssh root@ESXHostnameOrIPAddress vm-support -s > vm-support-Hostname.tgz

# HTTP 経由
# https://ESXHostnameOrIPAddress/cgi-bin/vm-support.cgi
```

保存先(`-w` 未指定時): `/var/tmp/`、`/var/log/`、カレントディレクトリ、または空き容量が最大の VMFS/VFFS パーティションから自動選択(KB 313542)。既定は実質 `/var/tmp/esx-YYYY-MM-DD--HH.MM.SSxxxxx.tgz` である(KB 326320 に `/var/tmp/esx-20##-01-26--20.46.3236587.tgz` の実例記載)。

注意: `-w` を付けないと `/var/tmp`(RAM 領域)を圧迫し、収集失敗の原因になる。6.7 では `/var/tmp` の空きが小さい場合があるため、データストア指定を推奨する。

#### 5.2.2 Host Client / vSphere Client

出典: KB 319493「Collecting diagnostic information for VMware ESXi using vSphere Client」
https://knowledge.broadcom.com/external/article/319493

- Host Client(ESXi へ直接接続): Host タブ → Actions → Generate support bundle → 管理者資格情報を再入力 → ダウンロード開始
- vSphere Client(vCenter 経由): Hosts and Clusters → ホストを右クリック → Export System Logs → 必要に応じて「Gather performance data」「Password for encrypted core dumps」を選択 → Export Logs
- vCenter オブジェクトを右クリックすると複数ホスト分を一括収集できる

#### 5.2.3 DCUI

- DCUI からのサポートバンドル生成手順は、今回の調査では公式記載を確認できなかった(未確認)。
- DCUI は「View System Logs」による閲覧と、管理エージェント再起動のメニューを持つことが KB 320280 の警告文(DCUI 版の再起動手順を名指し)から読み取れるが、バンドル生成は Host Client または SSH を使用する。

#### 5.2.4 性能スナップショット(パフォーマンス低下時)

出典: KB 326320(旧 KB 1967)「Collecting performance snapshots using vm-support in ESX and ESXi」
https://knowledge.broadcom.com/external/article/326320
※ 記事の Environment は ESXi 7.x / 8.x と明記。6.7 で使う場合は同一コマンド体系だが公式サポート範囲外である点に注意。

```bash
vm-support -p
vm-support -p -d 300 -i 10
vm-support -p -a PerformanceSnapshot:vsi -d 300 -i 10
# HTTP: https://<esxi>/cgi-bin/vm-support.cgi?performance=true&interval=5&duration=300
```

公式注記: 間隔は「スナップショット間の待ち時間」ではなく「各スナップショット内のポーズ」。大規模ホストでは1回の収集に100秒以上かかることがあり、`duration/interval` の回数は集まらない。取得は性能問題が発生している最中に行うこと。

### 5.3 よくある障害と公式 KB

各 KB の「対象バージョン」欄は記事の Environment 記載に基づく。6.7 が明記されていない記事は、手順の互換性を個別に判断する。

#### 5.3.1 パープルスクリーン(PSOD)

| 項目 | 内容 |
|---|---|
| KB | 337182「ESX/ESXi host stops responding and displays a purple diagnostic screen」 https://knowledge.broadcom.com/external/article/337182 (Environment: ESXi 7.x/8.x) |
| 関連 KB | 343033「Interpreting an ESXi host purple diagnostic screen (PSOD)」 https://knowledge.broadcom.com/external/article/343033 / 303440 Exception 13 / Exception 14 https://knowledge.broadcom.com/external/article/303440 / 310769(旧 1006796)PSOD 後のログ抽出 https://knowledge.broadcom.com/external/article/310769 / 372284 Machine Check Exception (MCE) https://knowledge.broadcom.com/external/article/372284 |

初動(公式の警告をそのまま守る):

1. ホストをリセットしない。画面の全文を撮影する(コンソールのスクリーンショットでも可)。「技術データはすべて必要」と明記されている。
2. 画面下部に `Disk Dump Successful` が出ているか確認する。出ていなければ最大1時間待つ。失敗表示なら次へ進む。
3. リブートする。次回起動時に core dump パーティションの内容が処理される。
4. root で SSH/コンソールに入り、起動時に生成された `vmkernel-zdump` からログを抽出する(旧 KB 1006796 の手順)。
5. 診断情報を収集しサポートリクエストへ提出する(旧 KB 1008524)。

ログの見どころ:

- 画面のエラーメッセージ(例: `Spin count exceeded (iplLock) - possible deadlock`、`Failed to ack TLB invalidate`)
- Physical CPU(`*` または `CPU0:` の接頭辞)。毎回同じ CPU なら CPU 側の疑い
- World(実行中プロセス名)。毎回同じならその World の命令が契機の可能性
- Stack trace、Uptime、core dump の有無
- 複数回発生時は「メッセージとスタックが同一か/変動するか」でソフト/ハードの当たりを付ける(公式は「決定的ではない」と注記)

#### 5.3.2 ホストの切断(Disconnected / Not Responding)

| 項目 | 内容 |
|---|---|
| KB | 303652「Changing an ESXi host's connection status in vCenter Server / unable to reconnect ESXi host back to vCenter Server」 https://knowledge.broadcom.com/external/article/303652 (ESX 6.x/7.x/8.x, vCenter Server) |
| 関連 KB | 456421「No healthy upstream」 https://knowledge.broadcom.com/external/article/456421 / 320280 管理エージェント再起動 https://knowledge.broadcom.com/external/article/320280 / 447199 管理ストールによる Not Responding https://knowledge.broadcom.com/external/article/447199 |
| 6.7 ドキュメント | 「Troubleshooting Hosts」 https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.vcenterhost.doc/GUID-6F6CE545-58FA-490B-8C8A-3CB8196CAEA8.html / 「ESXi Host Disconnects from vCenter Server」(ライセンス期限切れが原因の項) https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.vcenterhost.doc/GUID-1D945AFF-3BAF-4A02-B547-A99353321E59.html |

初動(KB 303652 の順序):

1. vSphere Client でホストを右クリック → Disconnect → 完了を待つ
2. 右クリック → Connection → Connect → 完了を待つ(通信経路の再検証を兼ねる)
3. 改善しなければ管理エージェントを再起動する

```bash
/etc/init.d/hostd restart
/etc/init.d/vpxa restart
# または
services.sh restart
```

4. それでも改善しなければ vCenter 側の vpxd を再起動する

```bash
service-control --restart vmware-vpxd
# または VAMI (https://<vcenter>:5480) → Services → VMware vCenter Server
```

見落としやすい原因: 6.7 公式ドキュメントは「ホストの評価期間(60日)またはライセンス切れでホストが切断される」「vCenter のライセンス切れで全ホストが同時に切断される」と明記している。全ホスト同時切断はまずライセンスを疑う。

#### 5.3.3 APD(All Paths Down)/ PDL(Permanent Device Loss)

| 項目 | 内容 |
|---|---|
| KB | 318712(旧 2004684)「Permanent Device Loss (PDL) and All-Paths-Down (APD) on ESXi host」 https://knowledge.broadcom.com/external/article/318712 |
| 関連 KB | 318850「All Paths Down for a storage device」 https://knowledge.broadcom.com/external/article/318850 / 316417 パスが Dead になる仕組み https://knowledge.broadcom.com/external/article/316417 / 406100 APD/PDL に対する HA のベストプラクティス https://knowledge.broadcom.com/external/article/406100 / 451740 PDL による管理エージェントのデッドロック https://knowledge.broadcom.com/external/article/451740 |

判定(vmkernel.log のシグネチャ)

PDL(恒久的喪失。ホストは再試行をやめる):

```
Path "vmhba##:C0:T0:L0" (PERM LOSS) command 0xa3 failed with status Device is permanently unavailable. H:0x0 D:0x2 P:0x0 Valid sense data: 0x5 0x25 0x0.
WARNING: ScsiDevice: 1223: Device :#### has been removed or is permanently inaccessible.
WARNING: NMP: nmp_DeviceStartLoop:721:NMP Device "####" is blocked. Not starting I/O from device.
StorageDevice: 10480: Device naa.#### APD Notify PERM LOSS
```

PDL と判定される SCSI sense コード(KB 318712 の表): `0x5/0x25/0x0`(LOGICAL UNIT NOT SUPPORTED)、`0x5/0x68/0x0`(LOGICAL UNIT NOT CONFIGURED)、`0x4/0x4c/0x0`、`0x4/0x3e/0x3`、`0x4/0x3e/0x1`、`0x2/0x4c/0x0`、`0x2/0x3e/0x3`、`0x2/0x3e/0x1`。
※ ESXi は ASC/ASCQ のみを見て `0x25/0x0` または `0x68/0x0` なら PDL と判定する。
※ iSCSI アレイが LUN とターゲットを 1:1 でマップしている場合、適切な sense が返らず PDL を検出できない(公式の明記)。

APD(一時的喪失。ホストは無期限に再試行):

```
WARNING: NMP: nmp_IssueCommandToDevice:2954:I/O could not be issued to device "####" due to Not found
WARNING: NMP: nmpDeviceAttemptFailover:658:Retry world failover device "####" - failed to issue command due to Not found (APD), try again...
WARNING: NMP: nmp_DeviceStartLoop:721:NMP Device "####" is blocked. Not starting I/O from device.
```

NVMe/HPP の場合は `vmkwarning.log` と `vmkernel.log` の両方に:
`WARNING: HPP: HppDeviceUpdateState:5279: Device 'eui.####' is changing to 'APD' from 'on'.`

初動:

- APD: クリーンな回復手段はない(公式明記)。ストレージアレイ/ファブリック側で復旧させる。残存参照を消すには影響ホストの再起動が必要。APD 中は管理エージェントのコマンドも応答せず、vMotion も失敗し得る(=ホスト再起動は非影響 VM も含めた停止を意味する)。
- APD の既定タイマは 140秒(KB 318850)。`StorageApdHandler: 692: APD Handle Created with lock.` は「タイマ開始、まだ APD ではない」状態。`esx.problem.storage.apd.timeout` の vobd イベントで APD 確定。
- PDL(計画外): アレイ側の接続·LUN マスキングをベンダと確認 → 全 VM のパワーオフ/登録解除 → データストア Unmount → 全ホストで Rescan → 必要なら Mount。
- PDL(計画): 先に Unmount → Detach してからアレイ側で unpresent する(順序を逆にすると計画外 PDL になる)。

HA 連携: vSphere 6.x 以降は VM Component Protection (VMCP) が APD/PDL から VM を保護する(KB 318712 に明記)。6.7 でも利用可能だが、既定値と応答時間はクラスタ設定で必ず確認する。

#### 5.3.4 ストレージ障害(APD/PDL 以外)

- パス冗長性の劣化: KB 318935「Path Redundancy to Storage Device Degraded」(KB 318850 から参照)
- NFS データストア接続断: KB 323107「Troubleshooting NFS datastore connectivity issues」(同上)
- デバイスが APD/PDL に遷移せずホストが無応答: KB 449327 https://knowledge.broadcom.com/external/article/449327
- 参考コマンド: `esxcli storage core path list`、`esxcli storage nmp device list`、`esxcli storage core device world list`

#### 5.3.5 ネットワーク障害

ネットワーク専用の公式 KB は、今回の調査で 6.7 を対象とした決定的な1本を特定できなかった(該当 KB 未確認)。代替として以下が使える。

| 項目 | 内容 |
|---|---|
| KB | 385031「vSphere HA Agent Alert: Cannot Reach Management Network Addresses」 https://knowledge.broadcom.com/external/article/385031 |
| 6.7 ドキュメント | vSphere Networking 6.7(Legacy PDF バンドルに収録) |

KB 385031 の原因記載は「ファイアウォール規則、管理ネットワーク IP の誤設定、IPv6 の使用、その他の到達性問題」。対処は HA 無効化→有効化、HA エージェント再起動、`hostd`/`vpxa` 再起動、ホストの切断→再接続。

ログの見どころ: `vmkernel.log` の `vmnic` リンク状態、`/var/log/vobd.log` のネットワークイベント、`esxcli network nic list` の Link Status。

#### 5.3.6 vSphere HA 関連

| 項目 | 内容 |
|---|---|
| 6.7 ドキュメント | 「Troubleshooting vSphere HA Host States」 https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.vcenterhost.doc/GUID-DF7CEF44-98EC-458A-8614-50CCAEC0A7C5.html / 「vSphere HA Agent Is in the Agent Unreachable State」 https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.vcenterhost.doc/GUID-3662595F-8E4C-452E-AEEC-3393E46293BC.html / 「Cannot Configure vSphere HA When Using Custom SSL Certificates」 https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.vcenterhost.doc/GUID-3FC16DC8-7157-4340-AB8A-B8DC87D7DC0F.html |
| 関連 KB | 385031(前述) / 415249「vSphere HA: Agent UnInitialization error」 https://knowledge.broadcom.com/external/article/415249 / 390647 証明書更新中の HA フェイルオーバー https://knowledge.broadcom.com/external/article/390647 |

公式の状態分類(6.7): Agent Unreachable / Uninitialized / Initialization Error / Uninitialization Error / Host Failed / Network Partitioned / Network Isolated / HA 構成タイムアウト。

Agent Unreachable の公式解釈: 「vCenter またはプライマリホストがエージェントに到達できない」。多くはネットワーク問題、または全ホスト停止、あるいは ESXi ホストエージェントの障害で watchdog が再起動できなかったケース。この状態ではフェイルオーバーは発動しない。対処は「vCenter 側でホストが not responding か確認 → 解消後に HA を再構成」。

ログの見どころ: `/var/run/log/fdm.log`(HA エージェント)、`vpxa.log`、`hostd.log`。

#### 5.3.7 証明書期限切れ

| 項目 | 内容 |
|---|---|
| KB | 414244「ESXi host disconnected from vCenter due to invalid or expired SSL certificate and ESXi host client is inaccessible」 https://knowledge.broadcom.com/external/article/414244 |
| 関連 KB | 377969「Unable to refresh/renew ESXi certificate from vCenter」(Environment: 7.0/8.0) https://knowledge.broadcom.com/external/article/377969 / 376026「Error: 503 Service Unavailable」(`/sbin/generate-certificates`) https://knowledge.broadcom.com/external/article/376026 / 341649 CA 署名証明書の構成 https://knowledge.broadcom.com/external/article/341649 |
| 6.7 ドキュメント | 「Troubleshooting vCenter Server and ESXi Host Certificates」 https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.vcenterhost.doc/GUID-2C61E02D-D0D3-4BB5-B4FD-B0DD97791EE9.html |

確認コマンド:

```bash
openssl x509 -in /etc/vmware/ssl/rui.crt -noout -dates
openssl x509 -in /etc/vmware/ssl/rui.crt -noout -text | grep -A2 Validity
openssl s_client -connect <esxi_host_ip>:443 -showcerts
```

`Verification error: unable to verify the first certificate` は期限切れ/未信頼/チェーン不完全のサイン(KB 414244)。

再生成(vCenter からの更新が失敗する場合の最終手段):

```bash
# バックアップ
cd /etc/vmware/ssl
mv rui.crt rui.crt.bak
mv rui.key rui.key.bak

# 自己署名の再生成(VMCA 相当)
/sbin/generate-certificates

# 反映
/etc/init.d/hostd restart
/etc/init.d/vpxa restart
/etc/init.d/rhttpproxy restart
```

- vCenter から更新できる場合は Host → Certificates → Renew Certificate(6.7 でも可)。
- 証明書更新は `vpxa` / `hostd` / `fdm` / `rhttpproxy` の再起動を伴うため、一時的な切断と HA 再構成が発生する(KB 390647)。
- 6.7 注意: KB 377969 は 7.0/8.0 限定の記載である。6.7 で同手順を用いる場合は、`/sbin/generate-certificates` の存在と `rui.crt` のパスを事前確認する。

#### 5.3.8 パフォーマンス低下

| 項目 | 内容 |
|---|---|
| KB | 447199「ESXi host not responding due to management starvation and 100% CPU utilization」 https://knowledge.broadcom.com/external/article/447199 |
| 関連 KB | 326320(旧 1967)性能スナップショット https://knowledge.broadcom.com/external/article/326320 / 326275 vSphere Client からの性能データ収集 https://knowledge.broadcom.com/external/article/326275 |
| 6.7 ドキュメント | vSphere Monitoring and Performance 6.7(Legacy PDF バンドル)。`esxtop` / `resxtop` の章を含む |

典型シグネチャ(vmkernel.log):

```
Alert: PCPU 24: no heartbeat for 7 seconds; possible starvation or lockup.
Warning: World 2097152 (vpxa) blocked for 12000 ms on CPU 24.
vcpu-0:36989572: Jump in wallclock detected. Previous: 1720383022, Current: 1720384805.
```

初動:

```bash
/etc/init.d/hostd restart
/etc/init.d/vpxa restart
# 改善しなければ
services.sh restart
```

原因は「CPU 100% 固定により管理エージェント(vpxa/hostd)が飢餓状態になり、heartbeat を送れず vCenter が Not Responding と判定」。VM 自体は動き続けるが低速化し、DRS の vMotion も失敗する。

性能データの取り方: `esxtop`(対話)または `resxtop`(リモート)。原因究明には KB 326320 の性能スナップショットを「現象発生中に」取得するのが公式推奨。

### 5.4 esxcli が応答しない/管理エージェント異常時の初動

#### 5.4.1 公式の基本手順(KB 320280「Restarting Management Agents in ESXi」)

https://knowledge.broadcom.com/external/article/320280

```bash
/etc/init.d/hostd restart
/etc/init.d/vpxa restart
```

- Host Client からは Host → Manage → Services で対象サービス(hostd / vpxa)を再起動する。
- 再起動後 1〜2分待って vSphere Client の「Connected」を確認する。
- 起動しない場合は `/var/log/hostd.log` を確認する(OOM、ディスク逼迫などの記載)。

#### 5.4.2 services.sh restart の禁止条件(公式の警告)

以下に該当する環境では `services.sh restart` も DCUI の管理エージェント再起動も使わず、個別サービスだけを再起動する。

| 条件 | 確認コマンド |
|---|---|
| vSAN を使用 | `esxcli vsan cluster get` |
| LACP を使用 | `esxcli network vswitch dvs vmware lacp status get` |
| NSX を構成 | `esxcli software vib list \| grep -E 'nsx\|vsipfwlib'` |
| View 環境の共有グラフィックス(vGPU/vDGA/vSGA) | (環境情報で判断) |

- 追加の注意(同 KB): 管理エージェントの再起動は一時的な中断を招き、ホスト再起動が必要な不安定化や、実行中タスク·ゲスト性能への影響があり得る。
- NSX 環境では `services.sh restart` が VM のデータパスを切断する(KB 310647 https://knowledge.broadcom.com/external/article/310647 )。実施するならメンテナンスモードへ移行する。

#### 5.4.3 「No healthy upstream」/ esxcli·df がハングする場合(KB 456421)

https://knowledge.broadcom.com/external/article/456421

症状: Host Client に `No healthy upstream`、vCenter で Disconnected/Not Responding、`esxcli` や `df -h` がハング。

原因: リバースプロキシ(Envoy)が管理サービスと通信できない。起動シーケンス中のハング、SSL 証明書(`rui.crt`)と秘密鍵(`rui.key`)の不整合、ストレージメタデータ破損など。

手順:

1. SSH 可能なら `hostd` / `vpxa` を再起動する
2. SSH 不可または改善しない場合はコールドリブート(iLO/iDRAC 経由)。vSAN クラスタでは安易な強制リセットを避ける
3. 改善しなければ `/var/run/log/hostd.log` と `/var/run/log/vmkernel.log` を確認する(SSL ハンドシェイク失敗、メタデータ破損、ストレージ遅延)。`rui.crt` と `rui.key` の SHA-256 サムプリント一致を確認する

#### 5.4.4 PDL が原因で管理エージェントがデッドロックする場合(KB 451740)

https://knowledge.broadcom.com/external/article/451740

- `WARNING: vmw_psp_rr: psp_rrSelectPathToActivate:###: Could not select path for device "naa.####".` が出る。
- `hostd`/`vpxa` を再起動しても起動直後に落ちる場合は、ホスト再起動が必要(デッドロックしたプロセスと PDL カーネル構造の掃除)。
- 再発防止: LUN をアレイから外す前に、必ず Unmount → Detach を実施する。

#### 5.4.5 初動フローチャート(公式情報の組み合わせ)

```
esxcli が応答しない / Host Client が開けない
  ├─ SSH は通じる？
  │    ├─ Yes → /var/log/hostd.log を確認 → hostd/vpxa 個別再起動(5.4.1)
  │    │         → 改善せず & 禁止条件に非該当なら services.sh restart
  │    └─ No  → DCUI / iLO・iDRAC でコンソール確認
  │              ├─ PSOD → 撮影・リセット禁止・core dump 待ち(5.3.1)
  │              └─ ハング → コールドリブート(5.4.3)
  └─ 直前にストレージ操作/アレイ作業があった？
       └─ Yes → vmkernel.log で APD/PDL 判定(5.3.3)→ アレイ側復旧 → 必要なら再起動
```

## 6. コマンド集(ESXi 6.7 で有効なもの)

6.7 のコマンドリファレンスは TechDocs の Legacy PDF(`vmware-vsphere-6-7.pdf`)に収録されている。個別コマンドの公式ページ URL は 6.7 版が廃止済みのため、バンドル PDF と、内容を裏付けた KB/6.7 ドキュメントページを併記する。

### 6.1 バージョン·ビルド確認

```bash
vmware -v
esxcli system version get
```

- `vmware -v`: 製品名·バージョン·ビルドを1行表示(例: `VMware ESXi 6.7.0 build-17167734`)
- `esxcli system version get`: Product / Version / Build / Update を項目別に表示
- ビルド番号とパッチの対応は KB 316595「Build numbers and versions of VMware ESXi/ESX」 https://knowledge.broadcom.com/external/article/316595 で確認する(本環境のビルド17167734 の対応は §2 を参照)

### 6.2 ネットワーク

```bash
esxcli network nic list                 # 物理 NIC の一覧・リンク状態・速度
esxcli network nic get -n vmnic0        # 個別 NIC の詳細
esxcli network vm list                  # 仮想マシン単位のネットワークポート一覧
esxcli network ip interface list        # VMkernel インターフェース(vmk0等)と有効サービス
esxcli network ip route ipv4 list       # ルーティングテーブル
esxcli network vswitch standard list    # 標準スイッチとポートグループ
```

- `esxcli network nic list`: リンクアップ/ダウン、Speed/Duplex の一次確認(物理層切り分けの起点)
- `esxcli network vm list`: どの VM がどのポートグループ/スイッチに載っているか
- `esxcli network ip interface list`: 管理ネットワーク(vmk0)の IP と有効化サービス(vMotion 等)の確認
- `esxcli network vswitch standard list`: アップリンク構成の確認(vmnic の割当漏れ検出)

### 6.3 ストレージ

```bash
esxcli storage core adapter list        # HBA/アダプタの状態(online/offline, ドライバ)
esxcli storage core device list         # LUN/デバイスの状態(size, Is SSD, Is Offline 等)
esxcli storage core path list           # パス単位の状態(active/dead/standby)
esxcli storage vmfs extent list         # VMFS データストアとエクステントの対応
esxcli storage filesystem list          # マウント状況・容量・UUID(VMFS/NFS 双方)
esxcli storage nmp device list          # PSP(SATP)とパス選択ポリシー
esxcli storage core device world list   # デバイスを掴んでいる VMkernel ワールド(KB 318712 が案内)
```

- `esxcli storage core adapter list`: HBA 認識とドライバ状態。APD 時にまず「アダプタは online か」
- `esxcli storage core device list`: デバイスが `offline`/`dead` になっていないか
- `esxcli storage vmfs extent list`: データストア名と NAA ID の対応(KB のログに出る `naa.xxx` と突き合わせる)
- `esxcli storage filesystem list`: 「Inaccessible」判定と残容量の確認

### 6.4 パッケージ(VIB/プロファイル)

```bash
esxcli software vib list                # インストール済み VIB とベンダー・版
esxcli software profile get             # 現在のイメージプロファイル(6.7 は Image Profile 方式)
esxcli software vib get -n <vibname>    # 個別 VIB の依存・詳細
```

- 6.7 は Image Profile ベースである。更新手順の詳細は §3 を参照。
- 7.0 以降との差異: 7.0/8.0 では `esxcli software vib update` 主体の運用や vSphere Lifecycle Manager のイメージ管理へ移行している。6.7 の `esxcli software profile get` 前提の手順を 7.0 以降にそのまま持ち込まないこと。

### 6.5 仮想マシン操作(vim-cmd)

```bash
vim-cmd vmsvc/getallvms                 # 登録 VM の一覧(VMID / 名前 / .vmx パス)
vim-cmd vmsvc/get.summary <vmid>        # 個別 VM の状態・リソース・Tools 状態
vim-cmd vmsvc/power.getstate <vmid>     # 電源状態
vim-cmd vmsvc/power.on <vmid>           # 電源投入
vim-cmd vmsvc/power.off <vmid>          # 電源オフ(ゲストへの ACPI シャットダウン要求)
vim-cmd vmsvc/power.reset <vmid>        # リセット
vim-cmd vmsvc/power.suspend <vmid>      # サスペンド
```

- Host Client が使えない状況での VM 状態確認·電源操作に有効。
- 注意: `power.off` は「ゲスト OS へのシャットダウン要求」であり、応答がない場合は `power.stop`(強制停止)が必要になる。強制停止はデータ破損リスクがあるため、安易に使わないこと。

### 6.6 サービス確認·操作

```bash
/etc/init.d/hostd status
/etc/init.d/hostd restart
/etc/init.d/vpxa status
/etc/init.d/vpxa restart
/etc/init.d/rhttpproxy restart
```

- 一覧確認は `ls /etc/init.d/`、Host Client では Host → Manage → Services。
- `esxcli system services` の 6.7 での有無は、本調査で公式記載を確認できなかった(未確認)。6.7 では `/etc/init.d/` と `services.sh`、Host Client の Services 画面で管理するのが確実。
- `services.sh restart` は全サービス再起動であり、§5.4.2 の禁止条件(vSAN / NSX / LACP / View の共有グラフィックス)に該当しない場合のみ使用する。

### 6.7 DCUI 操作

- View System Logs(ログ閲覧)、Troubleshooting Options(ESXi Shell / SSH の有効化、タイムアウト変更)、Restart Management Agents。
- 6.7 の DCUI メニュー構成そのものは公式ページで直接確認できていない(未確認)。KB 320280 が「DCUI を使った管理エージェント再起動」を名指しで警告しているため、機能の存在自体は公式に裏付けられる。

### 6.8 6.7 固有の注意(7.0/8.0 との差異)

| 項目 | ESXi 6.7 | 7.0 / 8.0 |
|---|---|---|
| クライアント | Host Client(HTML5)と vSphere Web Client(Flash)が併存 | Flash ベースの vSphere Web Client は廃止 |
| イメージ管理 | Image Profile 方式(`esxcli software profile`)が中心 | vSphere Lifecycle Manager のイメージ管理が主流 |
| VMCP(APD/PDL 連動 HA) | 6.x から利用可(KB 318712 に「vSphere 6.x and later」と明記) | 継続。設定 UI·既定値はバージョンで異なる |
| サポート | 2022-10-15 に一般サポート終了(EOGS)。最終パッチは ESXi670-202210001(2022-10-06) | 現行 |

## 7. 未確認事項

1. `esxcli system services` の 6.7 での有無(公式記載を確認できず)。6.7 では `/etc/init.d/` と Host Client の Services を使用する。
2. DCUI からのサポートバンドル生成手順(公式記載を確認できず)。Host Client / SSH を使用する。
3. DCUI のメニュー構成(6.7)。個別ページを取得できず。「View System Logs」と「管理エージェント再起動」の存在のみ KB から裏付け。
4. ネットワーク障害専用の 6.7 対象 KB(決定的な1本を特定できず)。KB 385031 と 6.7 Networking ガイドで代替。
5. `esxupdate.log` / `vobd.log` の 6.7 公式一覧での位置づけ。一覧表に記載なし。`vobd.log` は KB 318850 が参照先として明記。
6. KB の対象バージョン。343033 / 337182 / 377969 / 326320 は Environment が 7.x/8.x。6.7 への適用可否は公式に保証されていない(手順の互換性は高いが、サポート範囲外)。
7. 6.7 の個別ドキュメントページ URL。docs.vmware.com 廃止により、記載 URL は現時点で直接開けない。TechDocs の Legacy PDF か Wayback を使用する。
8. KB 317899(vSphere 7.0 のアップデート順序)の記事ページが 2026-11-10 時点で 404。KB 390293 が参照しており、KB 330373 では旧 ID 78221 として掲載されている。
9. EOTG(2023-11-15)の一次ページ。lifecycle.vmware.com は動的表示のため本文を取得できず、VMware のライフサイクル告知に基づく。
10. 6.7 の VUM(vSphere Update Manager)の個別手順ページ。6.7 ドキュメントは Legacy PDF バンドルに収録されており、個別 URL は確認していない。
11. Host Client の単体更新の提供有無(6.7)。`esx-ui` は ESXi のパッチに同梱される形で提供されている。

## 8. 参照リンク一覧(2026-11-10 取得)

### 8.1 公式ドキュメント(6.7)

| 内容 | URL |
|---|---|
| vSphere 6.7 PDF バンドル(Legacy) | https://techdocs.broadcom.com/content/dam/broadcom/techdocs/us/en/pdf/vmware/vsphere/vsphere/legacy/vmware-vsphere-6-7.pdf |
| Legacy Releases 入口 | https://techdocs.broadcom.com/us/en/vmware-cis/vsphere/vsphere/legacy/vsphere-legacy-releases.html |
| ESXi Log File Locations | https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.monitoring.doc/GUID-832A2618-6B11-4A28-9672-93296DA931D0.html |
| Collect ESXi Log Files | https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.monitoring.doc/GUID-4A172F04-2593-4819-99A2-9BEB7D7F4037.html |
| View System Logs on an ESXi Host | https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.monitoring.doc/GUID-498D2802-4802-4F18-B8B2-D398D45BE249.html |
| Securing ESXi Hosts(ログ永続化) | https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.security.doc/GUID-F35D7005-58EB-48AC-99D5-B9942EB2A8EF.html |
| Troubleshooting Overview | https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.vcenterhost.doc/GUID-C70D5A5E-7D84-446C-B8CE-0766AA7351A4.html |
| Troubleshooting Hosts | https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.vcenterhost.doc/GUID-6F6CE545-58FA-490B-8C8A-3CB8196CAEA8.html |
| Troubleshooting vSphere HA Host States | https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.vcenterhost.doc/GUID-DF7CEF44-98EC-458A-8614-50CCAEC0A7C5.html |
| HA Agent Unreachable | https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.vcenterhost.doc/GUID-3662595F-8E4C-452E-AEEC-3393E46293BC.html |
| Cannot Configure HA with Custom SSL Certs | https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.vcenterhost.doc/GUID-3FC16DC8-7157-4340-AB8A-B8DC87D7DC0F.html |
| Troubleshooting Certificates | https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.vcenterhost.doc/GUID-2C61E02D-D0D3-4BB5-B4FD-B0DD97791EE9.html |
| ESXi Host Disconnects from vCenter(ライセンス) | https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.vsphere.vcenterhost.doc/GUID-1D945AFF-3BAF-4A02-B547-A99353321E59.html |
| Upgrade Hosts by Using esxcli Commands | https://docs.vmware.com/en/VMware-vSphere/6.7/com.vmware.esxi.upgrade.doc/GUID-A4301ADA-8E02-459D-BF9D-0AD308DA5325.html |
| ESXi 6.7 Release Notes(ESXi670-202011002) | https://docs.vmware.com/en/VMware-vSphere/6.7/rn/esxi670-202011002.html |
| ESXi Upgrade Path(Interoperability Matrix) | https://interopmatrix.broadcom.com/Upgrade?productId=1&isHidePatch=true&isHideLegacyReleases=false |
| vCenter Upgrade Path | https://interopmatrix.broadcom.com/Upgrade?productId=2&isHidePatch=true&isHideLegacyReleases=false |
| vSAN Upgrade Path | https://interopmatrix.broadcom.com/Upgrade?productId=1746&isHidePatch=true&isHideLegacyReleases=false |
| Broadcom Support Portal Downloads | https://support.broadcom.com/group/ecx/downloads |
| Compatibility Guide | https://compatibilityguide.broadcom.com/ |
| VMware Lifecycle | https://lifecycle.vmware.com/ |

### 8.2 KB(新 ID / 旧 ID)

| 新 ID | 旧 ID | タイトル | URL |
|---|---|---|---|
| 343033 | — | Interpreting an ESXi host PSOD | https://knowledge.broadcom.com/external/article/343033 |
| 337182 | — | Host stops responding and displays PSOD | https://knowledge.broadcom.com/external/article/337182 |
| 303440 | — | Exception 13 / Exception 14 | https://knowledge.broadcom.com/external/article/303440 |
| 310769 | 1006796 | Extracting the log file after PSOD | https://knowledge.broadcom.com/external/article/310769 |
| 318712 | 2004684 | PDL and APD on ESXi host | https://knowledge.broadcom.com/external/article/318712 |
| 318850 | — | All Paths Down for a storage device | https://knowledge.broadcom.com/external/article/318850 |
| 320280 | — | Restarting Management Agents in ESXi | https://knowledge.broadcom.com/external/article/320280 |
| 303652 | — | Changing an ESXi host's connection status | https://knowledge.broadcom.com/external/article/303652 |
| 456421 | — | Troubleshooting "No healthy upstream" | https://knowledge.broadcom.com/external/article/456421 |
| 447199 | — | Host not responding due to management starvation | https://knowledge.broadcom.com/external/article/447199 |
| 451740 | — | PDL causing management agent deadlock | https://knowledge.broadcom.com/external/article/451740 |
| 385031 | — | HA: Cannot Reach Management Network Addresses | https://knowledge.broadcom.com/external/article/385031 |
| 414244 | — | Host disconnected due to expired SSL cert | https://knowledge.broadcom.com/external/article/414244 |
| 377969 | — | Unable to refresh/renew ESXi certificate | https://knowledge.broadcom.com/external/article/377969 |
| 376026 | — | 503 Service Unavailable after cert update | https://knowledge.broadcom.com/external/article/376026 |
| 313542 | 1010705 系 | Collecting diagnostic info using vm-support | https://knowledge.broadcom.com/external/article/313542 |
| 319493 | — | Collecting diagnostic info using vSphere Client | https://knowledge.broadcom.com/external/article/319493 |
| 326320 | 1967 | Collecting performance snapshots | https://knowledge.broadcom.com/external/article/326320 |
| 316595 | — | Build numbers and versions of ESXi/ESX | https://knowledge.broadcom.com/external/article/316595 |
| 326984 | — | End of General Support for vSphere 6.5/6.7/7.0 | https://knowledge.broadcom.com/external/article/326984 |
| 343840 | — | Patching ESXi host using Command Line | https://knowledge.broadcom.com/external/article/343840 |
| 313510 | — | How to back up and restore the ESXi host configuration | https://knowledge.broadcom.com/external/article/313510 |
| 372545 | — | Download latest ISOs and patches for vSphere ESXi | https://knowledge.broadcom.com/external/article/372545 |
| 366685 | — | VMware vSphere downloads, Converter, OEM images, patches and addons in the Broadcom Support Portal | https://knowledge.broadcom.com/external/article/366685 |
| 142814 | — | Download Broadcom products and software | https://knowledge.broadcom.com/external/article/142814 |
| 390293 | — | Install or upgrade ESXi from 7.x to 8.x | https://knowledge.broadcom.com/external/article/390293 |
| 308161 | — | Update Sequence for VMware vSphere 8.0 and Compatible VMware Products | https://knowledge.broadcom.com/external/article/308161 |
| 317899 | 78221 | vSphere 7.0 のアップデート順序(KB 390293 が参照。記事ページは 404) | https://knowledge.broadcom.com/external/article?articleId=317899 |
| 330373 | — | VMware update sequence of vSphere products | https://knowledge.broadcom.com/external/article/330373 |
| 311213 | — | Using ESXi Shell(KB 343840 が参照) | https://knowledge.broadcom.com/external/article/311213 |
| 82794 | — | CPU support warning(`--no-hardware-warning`、KB 343840 が参照) | https://knowledge.broadcom.com/external/article/82794 |

> 旧 ID は、記事本文に明記されているもの、または `?legacyId=` で同一記事に到達して確認できたもののみ記載している。それ以外は「—」としている。
