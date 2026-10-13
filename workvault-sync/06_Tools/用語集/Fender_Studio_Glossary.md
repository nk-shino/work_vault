---
title: Fender Studio用語集
type: note
phase: organize
status: 作成済
project: ""
updated: 2026-10-02
---

# Fender Studio用語集
対象: Fender Studio無料版の一般的な用語と、公式公開資料で確認できたUI・接続・素材の範囲。製品版を特定した資料ではないため、確認日は版番号を示さない。

## 章索引
- [基本操作と構成](#基本操作と構成)
- [音声入力と再生](#音声入力と再生)
- [ファイルと制作語](#ファイルと制作語)
- [音作りと伴奏](#音作りと伴奏)
- [関連用語と登録](#関連用語と登録)

## 基本操作と構成

### Fender Studio
- **正式名称**: Fender Studio
- **直訳**: 
- **意味**: 演奏を接続機器から取り込み、録音、停止、再生、音声ファイルの入出力を行うFenderのアプリ。公式資料ではiPhone、タブレット、コンピューターでの利用例が示される。
- 出典: [Fender公式「How To Use Fender Studio With Compatible Interfaces」](https://www.fender.com/articles/parts-and-accessories/how-to-use-fender-studio-with-compatible-interfaces)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### Fender Studio Pro
- **正式名称**: Fender Studio Pro
- **直訳**: 
- **意味**: Fender Studioとは別製品として案内される制作環境。本用語集では無料Fender Studioの機能と混ぜず、対象を区別するために名称だけ扱う。
- 出典: [Fender公式「Fender Studio Pro」](https://www.fender.com/products/fender-studio-pro)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### 録音開始
- **正式名称**: Record
- **英語表記**: Record（UI表記）
- **直訳**: 記録する
- **意味**: Recordを押して、選択した録音デバイスから演奏を音声として取り込み始める操作。録音の開始と同時に編集や書き出しが完了するわけではない。
- 出典: [Fender公式「How To Use Fender Studio With Compatible Interfaces」](https://www.fender.com/articles/parts-and-accessories/how-to-use-fender-studio-with-compatible-interfaces)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### 停止
- **正式名称**: Stop
- **英語表記**: Stop（UI表記）
- **直訳**: 止める
- **意味**: 進行中の録音または再生を止める操作。録音後は、そのテイクを再生して確認する段階へ移る。
- 出典: [Fender公式「How To Use Fender Studio With Compatible Interfaces」](https://www.fender.com/articles/parts-and-accessories/how-to-use-fender-studio-with-compatible-interfaces)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### 再生
- **正式名称**: Playback
- **英語表記**: Playback（UI表記）
- **直訳**: もう一度再生すること
- **意味**: 録音済みの音声を再生して聴き直す操作。録音中に入力音を聴くモニターとは目的が異なる。
- 出典: [Fender公式「How To Use Fender Studio With Compatible Interfaces」](https://www.fender.com/articles/parts-and-accessories/how-to-use-fender-studio-with-compatible-interfaces)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### トラック
- **正式名称**: track
- **直訳**: 道筋、録音単位
- **意味**: 音を分けて録音・配置する作業上の列。ギターと伴奏を別トラックにしておけば、それぞれを区別して扱える。上限数や具体的な編集機能はこの資料で確認していない。
- 出典: [Fender公式「How To Use Fender Studio With Compatible Interfaces」](https://www.fender.com/articles/parts-and-accessories/how-to-use-fender-studio-with-compatible-interfaces)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

## 音声入力と再生

### 録音デバイス
- **正式名称**: Record Device
- **英語表記**: Record Device（UI表記）
- **直訳**: 録音する機器
- **意味**: Preferences > Audio Setupで、音声をFender Studioへ入れる機器を選ぶUI項目。Fender Link I/O、Fender Mustang Micro Plus、Fender Tone Master Proが公式手順の例に登場する。
- **区別**: 再生デバイスは音を外へ出す機器で、録音デバイスとは役割が異なる。
- 出典: [Fender公式「How To Use Fender Studio With Compatible Interfaces」](https://www.fender.com/articles/parts-and-accessories/how-to-use-fender-studio-with-compatible-interfaces)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### 再生デバイス
- **正式名称**: Playback Device
- **英語表記**: Playback Device（UI表記）
- **直訳**: 再生する機器
- **意味**: Preferences > Audio Setupで、録音済み音声やモニター音を出す機器を選ぶUI項目。Link I/Oのヘッドホン端子を再生先にする構成が公式資料に示される。
- **区別**: 録音デバイスは音声をアプリへ入れる側である。
- 出典: [Fender公式「How To Use Fender Studio With Compatible Interfaces」](https://www.fender.com/articles/parts-and-accessories/how-to-use-fender-studio-with-compatible-interfaces)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### Audio Setup
- **正式名称**: Audio Setup
- **英語表記**: Audio Setup（UI表記）
- **直訳**: 音声設定
- **意味**: 録音元と再生先を選び、アプリの音声の入口と出口を指定する設定項目。OS全体のサウンド設定とは別に、Fender Studio内の経路を扱う。
- 出典: [Fender公式「Audio Monitoring & Signal Routing in Fender Studio」](https://www.fender.com/articles/fender-studio/audio-monitoring-and-signal-routing-in-fender-studio)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### Preferences
- **正式名称**: Preferences
- **英語表記**: Preferences（UI表記）
- **直訳**: 好み、設定
- **意味**: Audio Setupへ進む入口として公式手順に示される設定項目。アプリの音声入出力を選ぶ前段に位置する。
- 出典: [Fender公式「How To Use Fender Studio With Compatible Interfaces」](https://www.fender.com/articles/parts-and-accessories/how-to-use-fender-studio-with-compatible-interfaces)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### 音声モニタリング
- **正式名称**: audio monitoring
- **英語表記**: audio monitoring
- **直訳**: 音声を確認して聴くこと
- **意味**: 録音中の入力音や再生中の音をヘッドホンなどで聴き、音が入っているか確認すること。録音操作そのものではない。
- **区別**: 録音は音声を保存する操作、モニターは聴いて確認する経路である。
- 出典: [Fender公式「Audio Monitoring & Signal Routing in Fender Studio」](https://www.fender.com/articles/fender-studio/audio-monitoring-and-signal-routing-in-fender-studio)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### 信号経路
- **正式名称**: signal routing
- **英語表記**: signal routing
- **直訳**: 信号の経路
- **意味**: 楽器や接続機器からアプリへ入り、再生デバイスへ出ていく音の流れ。Audio Setupで入力と出力を選ぶときに考える経路である。
- 出典: [Fender公式「Audio Monitoring & Signal Routing in Fender Studio」](https://www.fender.com/articles/fender-studio/audio-monitoring-and-signal-routing-in-fender-studio)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### 互換インターフェース
- **正式名称**: compatible interface
- **英語表記**: compatible interface
- **直訳**: 対応する接続機器
- **意味**: 楽器の電気信号を端末へ渡し、必要に応じて端末から音を受ける外部機器。公式手順ではLink I/O、Mustang Micro Plus、Tone Master Proが例に挙げられる。
- 出典: [Fender公式「How To Use Fender Studio With Compatible Interfaces」](https://www.fender.com/articles/parts-and-accessories/how-to-use-fender-studio-with-compatible-interfaces)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### Fender Link I/O
- **正式名称**: Fender Link I/O
- **直訳**: 
- **意味**: 楽器入力、ヘッドホン、USB-Cの接続を備え、Fender Studioの録音デバイスまたは再生デバイスとして使う例が示された機器。
- 出典: [Fender公式「How To Use Fender Studio With Compatible Interfaces」](https://www.fender.com/articles/parts-and-accessories/how-to-use-fender-studio-with-compatible-interfaces)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### Fender Mustang Micro Plus
- **正式名称**: Fender Mustang Micro Plus
- **直訳**: 
- **意味**: ギターまたはベースを接続し、USB-C経由でFender Studioの録音デバイスとして選ぶ例が示された機器。内蔵アンプやエフェクトは機器側の機能として扱う。
- 出典: [Fender公式「How To Use Fender Studio With Compatible Interfaces」](https://www.fender.com/articles/parts-and-accessories/how-to-use-fender-studio-with-compatible-interfaces)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### Fender Tone Master Pro
- **正式名称**: Fender Tone Master Pro
- **直訳**: 
- **意味**: USB-C経由でFender Studioへ音声を送り、録音デバイスに選ぶ例が示された機器。機器内のアンプやエフェクトをFender Studioの搭載機能とは扱わない。
- 出典: [Fender公式「How To Use Fender Studio With Compatible Interfaces」](https://www.fender.com/articles/parts-and-accessories/how-to-use-fender-studio-with-compatible-interfaces)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### ヘッドホン出力
- **正式名称**: headphone output
- **英語表記**: headphone output
- **直訳**: ヘッドホンへ出す音
- **意味**: ヘッドホンで入力音や再生音を聴くための出力。Link I/Oのヘッドホン端子が公式の接続例に含まれる。
- 出典: [Fender公式「How To Use Fender Studio With Compatible Interfaces」](https://www.fender.com/articles/parts-and-accessories/how-to-use-fender-studio-with-compatible-interfaces)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

## ファイルと制作語

### 音声信号
- **正式名称**: audio signal
- **英語表記**: audio signal
- **直訳**: 音声の信号
- **意味**: 演奏などの音を電気的またはデジタルな情報として運ぶ信号。録音・再生で扱う波形の元になる。
- **区別**: MIDIは音声波形ではなく、演奏を表す情報を伝える規格である。
- 出典: [Fender公式「Audio Monitoring & Signal Routing in Fender Studio」](https://www.fender.com/articles/fender-studio/audio-monitoring-and-signal-routing-in-fender-studio)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### 音声ファイル
- **正式名称**: audio file
- **英語表記**: audio file
- **直訳**: 音声を保存したファイル
- **意味**: 録音した音や外部から取り込む音を保存するファイル。Fender Studioではインポートまたはエクスポートの対象として扱われる。
- 出典: [Fender公式「Import & Export Audio in Fender Studio」](https://www.fender.com/articles/fender-studio/import-and-export-audio-in-fender-studio)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### インポート
- **正式名称**: import
- **英語表記**: import
- **直訳**: 中へ取り込む
- **意味**: 外部にある音声ファイルをFender Studioの作業へ入れる操作。新たに入力音を録音する操作とは別である。
- **区別**: エクスポートはアプリ内の音声を外へ出す向きの操作である。
- 出典: [Fender公式「Import & Export Audio in Fender Studio」](https://www.fender.com/articles/fender-studio/import-and-export-audio-in-fender-studio)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### エクスポート
- **正式名称**: export
- **英語表記**: export
- **直訳**: 外へ送り出す
- **意味**: Fender Studio内の音声を音声ファイルとして外部へ出す操作。対応形式や保存先の全選択肢は確認していない。
- **区別**: インポートは外部ファイルをアプリへ入れる操作である。
- 出典: [Fender公式「Import & Export Audio in Fender Studio」](https://www.fender.com/articles/fender-studio/import-and-export-audio-in-fender-studio)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### DAW
- **正式名称**: Digital Audio Workstation
- **英語表記**: DAW
- **直訳**: 数字で扱う・音声・作業場
- **意味**: コンピューターで録音、音声編集、ミックスなどを行う制作環境の総称。個々のソフトの機能範囲は異なる。
- 出典: [Fender公式「Fender Studio Pro」](https://www.fender.com/products/fender-studio-pro)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### MIDI
- **正式名称**: Musical Instrument Digital Interface
- **英語表記**: MIDI
- **直訳**: 楽器・数字で扱う・接点
- **意味**: 鍵盤の音高・押す強さ・発音開始終了などを機器間で伝える規格。音声波形そのものを送るのではない。Fender StudioのMIDI録音対応は未確認である。
- **区別**: 音声は波形を扱い、MIDIは演奏イベントを扱う。
- 出典: [Fender公式「How To Use Fender Studio With Compatible Interfaces」](https://www.fender.com/articles/parts-and-accessories/how-to-use-fender-studio-with-compatible-interfaces)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### USB-C
- **正式名称**: USB Type-C
- **英語表記**: USB-C
- **直訳**: 
- **意味**: 対応機器と端末を接続するUSB系のコネクターおよび接続規格名。USB-C端子があることだけで、すべての機器が音声入出力に対応するとは限らない。
- 出典: [Fender公式「How To Use Fender Studio With Compatible Interfaces」](https://www.fender.com/articles/parts-and-accessories/how-to-use-fender-studio-with-compatible-interfaces)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

## 音作りと伴奏

### アンプシミュレーター
- **正式名称**: amplifier simulator
- **英語表記**: amp simulator / amplifier simulator
- **直訳**: 増幅器を模擬するもの
- **意味**: 実機アンプの音色、音量感、歪みなどをソフトウェアで再現する音作りの仕組み。Fender Studioの無料版インストールガイドにampsの項目はあるが、個別モデルや操作手順までは確定しない。
- 出典: [Fender Support「Fender Studio Installation Guide」](https://support.fender.com/en-us/knowledgebase/article/KA-02274)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### エフェクト
- **正式名称**: effect
- **英語表記**: effects
- **直訳**: 効果
- **意味**: 音に残響や歪みなどの処理を加える総称。インストールガイドにeffectsの項目はあるが、それらすべてが搭載されることや個別モデルの操作は断定しない。残響や歪みは一般的な例である。
- 出典: [Fender Support「Fender Studio Installation Guide」](https://support.fender.com/en-us/knowledgebase/article/KA-02274)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### Jam Tracks
- **正式名称**: Jam Tracks
- **英語表記**: Jam Tracks
- **直訳**: 一緒に演奏する曲素材
- **意味**: 演奏に合わせて使う伴奏素材。インストールガイドでは登録後に解除される項目として挙げられるが、素材の種類や数は確認していない。
- 出典: [Fender Support「Fender Studio Installation Guide」](https://support.fender.com/en-us/knowledgebase/article/KA-02274)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

## 関連用語と登録

### Supported operating systems
- **正式名称**: Supported operating systems
- **英語表記**: Supported operating systems
- **展開**: Operating System
- **直訳**: 対応する・動作を管理する・仕組み
- **意味**: アプリを動かせるOSの対応範囲を表す項目名。公式サポート資料ではiOS、macOS、Windows、Android、Linux向けの案内があるが、版ごとの詳細要件は確認していない。
- 出典: [Fender Support「Fender Studio Release Notes」](https://support.fender.com/en-us/knowledgebase/article/KA-02275)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）

### 登録
- **正式名称**: registration
- **英語表記**: registration
- **直訳**: 登録
- **意味**: インストールガイドで、ログインまたは登録後に追加のtracks、amps、effects、Jam Tracksが解除される案内に関係する手続き。必須条件や解除内容の詳細は確認していない。
- 出典: [Fender Support「Fender Studio Installation Guide」](https://support.fender.com/en-us/knowledgebase/article/KA-02274)
- 最終確認: 2026-10-02（資料確認日。版番号ではない）
