---
title: Xsynth参考資料
type: note
phase: organize
status: 作成済
project: 
updated: 2026-10-02
---

# Xsynth参考資料

## 対象選定根拠

検索で確認した候補のうち、ESI公式サイトに製品ページ、公式ダウンロードページ、英語ユーザーマニュアルが揃う「ESI Xsynth」を資料が揃う対象として採用した。公式製品ページは「Ultra-Thin 25-key Synthesizer with integrated Master Keyboard and Audio/MIDI Interface」と記載し、3オシレーター、3 LFO、3 AHDSR、16 mod matrix slots、最大10 voices、24-bit/96kHz Audio Interfaceを明記している。Xsynth DSSIは今回の公式一次資料として同等に確認できなかったため対象外とし、別製品の機能を混ぜていない。

- 出典: [ESI Xsynth製品ページ](https://www.esi-audio.com/products/xsynth)
- 出典: [ESI Xsynth公式ダウンロード](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)

## マニュアル照合範囲

英語 User Manual v. 1.8（February 2026）を本文確認済み。章1の目次、章3 Quickstart、章7 Connections、章8–11の操作・鍵盤、章12–20の音源エンジン、章21–24のGLOBAL/MIDI/Editor、AppendixのMIDI Channel Messagesまで照合した。PDFは全104ページの構成を確認し、用語本文は製品ページおよびマニュアル記載の実機UI名・端子名・仕様に限定した。

- 出典: [Xsynth User Manual v. 1.8 PDF](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 確認: 本文確認済

## 仕様制限・未確認

- 実機を操作しての音量、鍵盤感触、個体差、実測レイテンシーは未確認。
- エフェクト内部アルゴリズムの詳細、全パラメータの数値範囲、未掲載の波形名は断定していない。
- Firmware／Editorの版による差はあり得る。本文は製品ページとManual v. 1.8の範囲であり、最新Editorの画面差は未確認。
- Audio Interfaceのサンプルレートは96kHz固定、音源出力とAux InをUSB録音できることを本文確認済み。MIDIは音声ではなく演奏・制御情報として区別した。
- Xsynthの鍵盤はvelocity sensitive 25鍵、polyphonic aftertouch。GLOBALではAT typeをPolyphonic／Monophonic（Channel）に切替可能と本文確認済み。

## 学習順

1. Quickstart 3.1–3.4で電源、ヘッドホン、Patch Select、鍵盤、USB音声を確認
2. 章9でVelocity、Polyphonic Aftertouch、Pitchbend、Modulation、Hold、Octaveを確認
3. 章12–17でOscillator、Envelope、LFO、Filter、Mixerを確認
4. 章18–20でRouting、Effects、Modulation Matrixを確認
5. 章21–24で保存、MIDI、Editor、Factory Resetの注意を確認

## 復習運用

- 復習キュー: 未確認空欄を最優先。次に確認日が古い順に最大5件。誤答要復習は常に優先する。
- 各用語の確認日は用語集の「最終確認」欄で個別更新する（現在は公式本文照合日を基準とし、実機確認とは区別）。
- 誤答要復習: 空欄（実機学習後に記入）
- 確認日: 2026-10-02（公式本文照合日。実機確認日ではない）
- 自動スキル: 未実装
- 既存の楽典ノートとは別管理
