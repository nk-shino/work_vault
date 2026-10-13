---
title: Xsynth用語集
type: note
phase: organize
status: 作成済
project: 
updated: 2026-10-02
---

# Xsynth用語集

対象: ESI Xsynth

## 索引

- 音を出すまでと基本操作
- 音源・フィルター・時間変化
- 変調・演奏表現
- エフェクト・アルペジエーター
- 音声・MIDI・システム

## 音を出すまでと基本操作
### パッチ

- **正式名称**: Patch（UI名）
- **直訳**: 継ぎ当て
- **意味**: 音色一式を保存した呼出単位。オシレーター、フィルター、エフェクトなどの状態をまとめて再現する。例: Patch Selectで音色を切り替える。
- **混同**: プリセット
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Init Patch

- **正式名称**: Init Patch（UI名）
- **直訳**: 初期パッチ
- **意味**: GLOBALから呼び出せる初期状態の音色。音が出ない原因を切り分けたり、ゼロから音色を作る出発点にする。
- **混同**: Factory Reset
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Patch Select

- **正式名称**: Patch Select（UI名）
- **直訳**: パッチ選択
- **意味**: 本体右上のエンコーダーで保存音色を選ぶ操作。選択対象を変えるだけで、音色パラメータを直接変える操作ではない。
- **混同**: Encoder
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

## 音源・フィルター・時間変化
### オシレーター (Oscillator)

- **正式名称**: Oscillator（OSC）
- **直訳**: 振動するもの
- **意味**: 音の周期的な波形を作る音源ブロック。Xsynthでは3基あり、各音量・音高・波形などをMixerへ送る。
- **混同**: LFO
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### オシレーター1 (OSC1)

- **正式名称**: OSC1（UI名／Oscillator 1）
- **直訳**: オシレーター1
- **意味**: 3基ある音源の第1基。MIDI CC 29で粗い音高、CC 56でミックスレベルを受ける。
- **混同**: Osc2/Osc3
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### オシレーター2 (OSC2)

- **正式名称**: OSC2（UI名／Oscillator 2）
- **直訳**: オシレーター2
- **意味**: 3基ある音源の第2基。Osc1とのRingMod組み合わせにも関係する。
- **混同**: Osc1
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### オシレーター3 (OSC3)

- **正式名称**: OSC3（UI名／Oscillator 3）
- **直訳**: オシレーター3
- **意味**: 3基ある音源の第3基。Osc3→Osc1 FM amountという接続がMIDI実装に記載される。
- **混同**: Osc1
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### 波形 (Wave)

- **正式名称**: Wave（UI名）
- **直訳**: 波
- **意味**: オシレーターが周期的に出す形状。波形を変えると倍音構成が変わり、同じ音高でも音色が変わる。
- **混同**: Sample ROM
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### サンプルROM (Sample ROM)

- **正式名称**: Sample ROM（Sample Read-Only Memory）
- **直訳**: 標本読み出し専用メモリ
- **意味**: Xsynthのvirtual analog subtractive音源が波形素材を読み出す内蔵メモリ。外部サンプル録音機能を意味しない。
- **混同**: Audio Interface recording
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Coarse Tune

- **正式名称**: Coarse Tune（UI名）
- **直訳**: 粗い調律
- **意味**: オシレーターの音高を大きな単位で移動するパラメータ。Osc1〜3に個別に設定できる。
- **混同**: Fine Tune
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Fine Tune

- **正式名称**: Fine Tune（UI名）
- **直訳**: 細かい調律
- **意味**: オシレーターの音高を微小にずらすパラメータ。3基を少しずらすと厚みが変わる。
- **混同**: Coarse Tune
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### PWM

- **正式名称**: PWM（Pulse Width Modulation）
- **直訳**: パルスの短い時間幅を変えること
- **意味**: パルス波の幅を変える処理。XsynthのMIDI実装にはOsc1 PWMが記載される。
- **混同**: 音量変調
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### FM amount

- **正式名称**: FM amount（UI名／Frequency Modulation amount）
- **直訳**: 周波数変調量
- **意味**: Osc3からOsc1へ与える周波数変調の強さ。上げるほどOsc1の周期が変化し、音色のスペクトルが変わる。
- **混同**: RingMod
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### RingMod

- **正式名称**: Ring Modulation
- **直訳**: 環状変調
- **意味**: Osc1とOsc2を掛け合わせる音色処理。基音以外の成分が強くなり、金属的な結果になり得る。
- **混同**: FM
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Oscillator Drift

- **正式名称**: Oscillator Drift（UI名）
- **直訳**: オシレーターの漂い
- **意味**: オシレーターの音高・位相の安定からの揺らぎを調整する項目。固定ピッチの移調そのものではない。
- **混同**: Fine Tune
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### ミキサー (Mixer)

- **正式名称**: Mixer（UI名）
- **直訳**: 混ぜるもの
- **意味**: 各オシレーターや外部入力のレベルをまとめる段。音源を鳴らすには少なくとも一つのオシレーターを可聴レベルにする必要がある。
- **混同**: Audio Routing
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Osc Mix Level

- **正式名称**: OSC Mix Level（UI名）
- **直訳**: オシレーター混合レベル
- **意味**: Osc1〜3をミックスへ送る音量。上げ下げで音源間の比率を変える。
- **混同**: Patch Volume
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### フィルター (Filter)

- **正式名称**: Filter（UI名／VCF: Voltage Controlled Filter）
- **直訳**: ろ過器
- **意味**: 周波数成分を通過・減衰させる段。XsynthではCutoff、Resonance、モード、傾斜などを操作する。
- **混同**: EQ
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### カットオフ (Cutoff)

- **正式名称**: Filter Cutoff（UI名）
- **直訳**: 切断点
- **意味**: フィルターが通過させる帯域の境界周波数。ローパスでは下げると高域が減り、ハイパスでは設定により低域が減る。
- **混同**: Resonance
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### レゾナンス (Resonance)

- **正式名称**: Filter Resonance（UI名）
- **直訳**: 共鳴
- **意味**: Cutoff付近を強調する量。上げると境界周辺が目立ち、過度なら鋭い響きになる。
- **混同**: Cutoff
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### ローパス (Low-pass)

- **正式名称**: 12dB LP / 24dB LP（UI名）
- **直訳**: 低域通過
- **意味**: Cutoffより上の成分を主に減衰させるフィルターモード。明るさを抑える用途に使う。
- **混同**: High-pass
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### ハイパス (High-pass)

- **正式名称**: 12dB HP / 24dB HP（UI名）
- **直訳**: 高域通過
- **意味**: Cutoffより下の成分を主に減衰させるフィルターモード。低域を整理する用途に使う。
- **混同**: Low-pass
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### バンドパス (Band-pass)

- **正式名称**: 12dB BP / 24dB BP（UI名）
- **直訳**: 帯域通過
- **意味**: Cutoff周辺の帯域を通し、低域と高域を減衰させるモード。狭い音域の強調に使う。
- **混同**: Low-pass
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### 12dB slope

- **正式名称**: 12dB slope（UI名）
- **直訳**: 12デシベルの傾斜
- **意味**: フィルターの減衰傾斜を表す設定。24dBより境界の外側を緩やかに減衰させる。
- **混同**: 24dB slope
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### 24dB slope

- **正式名称**: 24dB slope（UI名）
- **直訳**: 24デシベルの傾斜
- **意味**: フィルターの減衰傾斜を表す設定。12dBより急な帯域外減衰になる。
- **混同**: 12dB slope
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Drive/PreFilter

- **正式名称**: Drive/PreFilter（UI名）
- **直訳**: 駆動／フィルター前
- **意味**: フィルター前段の信号レベルまたは駆動量を調整する項目。入力を押し上げて音色や歪みの変化を作る。
- **混同**: Post level
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Keytrack

- **正式名称**: Keytrack（KTrck）
- **直訳**: 鍵盤追跡
- **意味**: 押した音高に応じてフィルター設定を追従させる量。高い鍵盤ほど明るくするような音域差を作れる。
- **混同**: Velocity
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### エンベロープ量 (EnvAmt)

- **正式名称**: EnvAmt（UI名／E.Amt／Envelope Amount）
- **直訳**: エンベロープ量
- **意味**: エンベロープがフィルターなどの目的地を動かす深さ。時間変化を使うための量で、Cutoffの初期値そのものではない。
- **混同**: Cutoff
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### AHDSRエンベロープ

- **正式名称**: AHDSR Envelope（Attack Hold Decay Sustain Release Envelope）
- **直訳**: アタック・ホールド・ディケイ・サステイン・リリース包絡
- **意味**: 音量や音色の時間変化をAttack、Hold、Decay、Sustain、Releaseで定めるXsynthの包絡。
- **混同**: ADSR
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Attack

- **正式名称**: Attack（UI名）
- **直訳**: 攻撃
- **意味**: ノート開始から包絡が最大値へ達するまでの時間。長くすると立ち上がりが遅くなる。
- **混同**: Release
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Hold

- **正式名称**: Hold（UI名）
- **直訳**: 保持
- **意味**: Attack後に最大値を保つ時間。鍵盤を押し続ける時間とは別の内部段階である。
- **混同**: Sustain
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Decay

- **正式名称**: Decay（UI名）
- **直訳**: 減衰
- **意味**: 最大値からSustain値へ移る時間。音の立ち上がり後の落ち着き方を変える。
- **混同**: Release
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Sustain

- **正式名称**: Sustain（UI名）
- **直訳**: 持続
- **意味**: 鍵盤を押している間に包絡が保つレベル。時間ではなくレベルの設定である。
- **混同**: Hold
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Release

- **正式名称**: Release（UI名）
- **直訳**: 解放
- **意味**: ノートを離した後に包絡が終点へ戻る時間。長くすると余韻が残る。
- **混同**: Decay
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### LFO（低周波オシレーター）

- **正式名称**: LFO（Low-Frequency Oscillator）
- **直訳**: 低周波オシレーター
- **意味**: 周期的な制御信号を作り、ピッチ・Cutoff・音量などを揺らす。Xsynthには3基ある。
- **混同**: Oscillator
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### LFO Rate

- **正式名称**: LFO Rate（UI名）
- **直訳**: LFOの割合
- **意味**: LFOが1周期を繰り返す速さ。固定レートまたはTempo Sync時の拍分割として扱われる。
- **混同**: LFO Wave
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### LFO Wave

- **正式名称**: LFO Wave（UI名）
- **直訳**: LFOの波
- **意味**: LFOが出す制御信号の形。Sin、Tri、Saw、Sqr、S&HなどがMIDI実装に列挙される。
- **混同**: Wave
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### LFO Attack

- **正式名称**: LFO Attack（UI名）
- **直訳**: LFOの攻撃
- **意味**: LFOの効果が始まってから現れるまでの立ち上がり時間。瞬時に揺らさず遅れて揺らす場合に使う。
- **混同**: LFO Delay
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### LFO Delay

- **正式名称**: LFO Delay（UI名）
- **直訳**: LFOの遅延
- **意味**: ノート開始後にLFO効果を開始するまでの遅れ。Rateを遅くする設定とは異なる。
- **混同**: LFO Attack
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### LFO TempoSync

- **正式名称**: LFO TempoSync（UI名）
- **直訳**: LFOのテンポ同期
- **意味**: LFO周期をテンポの拍分数へ同期する設定。マニュアルのMIDI実装には1/32から4/1までの値が示される。
- **混同**: 固定LFO Rate
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

## 変調・演奏表現
### モジュレーション・マトリクス (Modulation Matrix)

- **正式名称**: Modulation Matrix（MOD）
- **直訳**: 変調の格子
- **意味**: 16個のスロットでSourceからDestinationへDepthを割り当てる画面・機構。鍵盤入力やLFOで音色を動かす。
- **混同**: Macro
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Mod Slot

- **正式名称**: Modulation slot（UI名）
- **直訳**: 変調枠
- **意味**: 一つのSource、Destination、Depthの組を置く枠。空にするとその経路からの変化はなくなる。
- **混同**: Patch
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Source

- **正式名称**: Source（UI名）
- **直訳**: 源
- **意味**: 変調を発生させる側。Velocity、Pitchbend、LFO、Modwheelなどを選び、目的地を動かす。
- **混同**: Destination
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Destination

- **正式名称**: Destination（UI名）
- **直訳**: 行き先
- **意味**: 変調されるパラメータ。Pitch、VCF Cutoff、Volumeなどを選ぶ対象である。
- **混同**: Source
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Depth

- **正式名称**: Depth（UI名）
- **直訳**: 深さ
- **意味**: 変調源が目的地を動かす幅。正負で動く向きも変わる場合がある。
- **混同**: Rate
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Macro

- **正式名称**: Macro（UI名）
- **直訳**: 大きな操作単位
- **意味**: M1〜M4に複数パラメータ操作をまとめ、素早く音色を変える仕組み。単一の音源ブロックではない。
- **混同**: Modulation Matrix
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

## エフェクト・アルペジエーター
### Effects/Aux

- **正式名称**: Effects/Aux（AUX）
- **直訳**: 効果／補助
- **意味**: FX、EQ、外部入力などの補助経路をまとめるページ。エフェクトのPost levelやAux入力を扱う。
- **混同**: Audio Routing
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Distortion/Reduction

- **正式名称**: FX1 Distortion/Reduction（UI名）
- **直訳**: 歪み／縮減
- **意味**: FX1に用意された効果名。信号を歪ませる処理とReduction系処理を選ぶ対象で、具体的なアルゴリズム詳細は未確認。
- **混同**: Reverb
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Reverb/Hall

- **正式名称**: FX2 Reverb/Hall（UI名）
- **直訳**: 残響／ホール
- **意味**: FX2の効果名。音に反射音・空間感を加える。Hallはその空間タイプを示すUI名である。
- **混同**: Delay
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Chorus/Flanger/Delay

- **正式名称**: FX3 Chorus/Flanger/Delay（UI名）
- **直訳**: 合唱／フランジャー／遅延
- **意味**: FX3で選ぶ効果群。短い遅延の反復・変調などにより厚み、揺れ、反復音を作る。
- **混同**: Reverb
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Post level

- **正式名称**: Post level（UI名）
- **直訳**: 後段レベル
- **意味**: 各エフェクト後の出力レベル。ゼロなら効果の出力が聞こえないため、音が出ない切り分けで確認する。
- **混同**: Patch Volume
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### EQ

- **正式名称**: EQ（Equalizer）
- **直訳**: 等化器
- **意味**: 周波数帯ごとのレベルを調整する処理。XsynthではパッチのAUX側にEQが記載される。
- **混同**: Filter
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### アルペジエーター (Arpeggiator)

- **正式名称**: Arpeggiator（ARP）
- **直訳**: 分散和音装置
- **意味**: 押さえた音をパターンとして順に鳴らす機能。XsynthにはStandardとPhraseのModeがある。
- **混同**: Sequencer
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Arp Pattern

- **正式名称**: Arp Pattern（UI名）
- **直訳**: 分散和音パターン
- **意味**: アルペジエーターが繰り返す音の並び。Xsynth Editorでは2バンク各128プリセットと記載される。
- **混同**: Patch
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Phrase Mode

- **正式名称**: Phrase Mode（UI名）
- **直訳**: 句モード
- **意味**: アルペジオを定義済みスケール内に保つモード。押した鍵盤が結果パターンの開始音を決める。
- **混同**: Standard Mode
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Glide

- **正式名称**: Glide（Portamento）
- **直訳**: 滑走
- **意味**: ある音高から次の音高へ連続的に移る時間・動作。MIDI実装ではOff、Legato、Trigの状態がある。
- **混同**: Octave Shift
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Hold button

- **正式名称**: HOLD（UI名）
- **直訳**: 保持ボタン
- **意味**: ノート保持を操作する本体ボタン。GLOBALのSustain ModeでMomentaryまたはLatchを選ぶ。
- **混同**: Sustain envelope
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Octave shift

- **正式名称**: OCTAVE −／＋（UI名）
- **直訳**: オクターブ移動
- **意味**: 鍵盤から出す音高範囲を上下へ移す操作。音色のオクターブ設定を直接変更するものではない。
- **混同**: Transpose
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Pitchbend

- **正式名称**: PITCH −／＋（UI名）
- **直訳**: 音高曲げ
- **意味**: 圧力感知ボタンの左右で音高を下げ上げする演奏情報。MIDIではPitch Bend Changeとして送られる。
- **混同**: Modulation
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Modulation button

- **正式名称**: MODULATION（UI名）
- **直訳**: 変調ボタン
- **意味**: 押す強さに応じた値を送る圧力感知ボタン。内部音源またはMIDI先の変調深度に割り当てて使う。
- **混同**: Aftertouch
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Velocity

- **正式名称**: Velocity
- **直訳**: 速度
- **意味**: 鍵盤を押す速さとして生成される演奏値。音量そのものではなく、Mod MatrixでVolumeやCutoffなどへ割り当てられる。
- **混同**: Volume
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Polyphonic Aftertouch

- **正式名称**: Polyphonic Aftertouch（Poly AT）
- **直訳**: 多声音後押し
- **意味**: 押した各鍵盤ごとの追加圧力値。Xsynthの25鍵はポリフォニック・アフタータッチを出力する。
- **混同**: Channel Aftertouch
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Channel Aftertouch

- **正式名称**: Channel Aftertouch（Channel Pressure）
- **直訳**: チャンネル後押し
- **意味**: MIDIチャンネル全体に一つ送る追加圧力値。GLOBALのAT typeでPolyphonicとMonophonic（Channel）を切り替える。
- **混同**: Polyphonic Aftertouch
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Touch curve

- **正式名称**: Touch curve（UI名）
- **直訳**: 触れ方の曲線
- **意味**: VelocityとAftertouchの応答カーブを選ぶGLOBAL設定。入力値に対する反応の変わり方を調整する。
- **混同**: Fixed Value
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Polyphony

- **正式名称**: Polyphony
- **直訳**: 多声音
- **意味**: 同時に発音できる声部数。Xsynthの仕様は最大10 voicesだが、パッチによって実際の制限が異なる場合がある。
- **混同**: Monophony
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Voice

- **正式名称**: Voice
- **直訳**: 声
- **意味**: 一つの発音単位。Xsynthの仕様上、同時発音数は最大10 voiceとされる。
- **混同**: Oscillator
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Mono On

- **正式名称**: Mono On（MIDI CC 126）
- **直訳**: 単音オン
- **意味**: MIDIで単音動作を選ぶメッセージ。対してPoly Onは多声音動作を選ぶ。
- **混同**: Poly On
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Poly On

- **正式名称**: Poly On（MIDI CC 127）
- **直訳**: 多声音オン
- **意味**: MIDIで多声音動作を選ぶメッセージ。電源投入時の既定値としてマニュアルに記載される。
- **混同**: Mono On
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

## 音声・MIDI・システム
### 音声・接点インターフェース (Audio Interface)

- **正式名称**: Audio Interface
- **直訳**: 音声・接点
- **意味**: Xsynthの音源出力とAux InをUSB経由でコンピューターへ録音できる機能。MIDI情報を録音する機能とは別である。
- **混同**: MIDI Interface
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Aux In

- **正式名称**: AUX IN（UI名）
- **直訳**: 補助入力
- **意味**: 外部のラインレベル音声を入力する3.5mm端子。USB Audio Interfaceでコンピューターへ録音できる。
- **混同**: Line Out
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Line Out

- **正式名称**: LINE OUT（UI名）
- **直訳**: 線出力
- **意味**: Xsynthの音声をミキサー、アンプ、別インターフェースなどへ送る3.5mm出力。
- **混同**: Phones
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Phones

- **正式名称**: PHONES（UI名）
- **直訳**: 電話機
- **意味**: ヘッドホンを接続する3.5mm出力。標準ライン／ヘッドホン出力で、推奨ヘッドホンは32Ω以下とマニュアルにある。
- **混同**: Line Out
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### USB-C

- **正式名称**: USB-C（Universal Serial Bus Type-C）connection
- **直訳**: USB-C接続
- **意味**: Mac、PC、モバイル機器へ電源・MIDI・音声を通す接続。クラスコンプライアントのAudio Interfaceとして認識される。
- **混同**: DIN MIDI
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### サンプリングレート (Sampling rate)

- **正式名称**: Sampling rate
- **直訳**: 標本化率
- **意味**: 音声を1秒あたり何回測るかを表す値。Xsynth Audio Interfaceは96kHz固定で、コンピューター側から変更できない。
- **混同**: Bit depth
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### 24-bit

- **正式名称**: 24-bit
- **直訳**: 24ビット
- **意味**: 音声サンプルの振幅を表すデータ精度。XsynthのAudio Interface仕様は24-bit／96kHzである。
- **混同**: Sampling rate
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### MIDI（Musical Instrument Digital Interface）

- **正式名称**: MIDI（Musical Instrument Digital Interface）
- **直訳**: 音楽機器デジタル接続
- **意味**: ノート、Velocity、Aftertouch、CCなどの演奏・制御情報を送る規格。音声波形そのものを送るものではない。
- **混同**: Audio Interface
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### MIDI In

- **正式名称**: MIDI IN（UI名）
- **直訳**: MIDI入力
- **意味**: 外部機器からのMIDI情報をXsynthへ入れる3.5mm端子。受信チャンネルやGLOBAL設定が一致しないと反応しない。
- **混同**: MIDI Out
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### MIDI Out

- **正式名称**: MIDI OUT（UI名）
- **直訳**: MIDI出力
- **意味**: Xsynthから外部機器へMIDI情報を出す3.5mm端子。USB MIDIとのブリッジにも使える。
- **混同**: MIDI In
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### USB MIDI

- **正式名称**: USB MIDI
- **直訳**: USBによるMIDI
- **意味**: USB経由でコンピューターとXsynthの演奏情報を送受信する経路。USB Audioとはデータ種別が異なる。
- **混同**: DIN MIDI
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### MIDI CC

- **正式名称**: MIDI CC（MIDI Control Change）
- **直訳**: MIDI制御変化
- **意味**: 連続的なパラメータ値を送るMIDIメッセージ。XsynthにはCutoff、LFO、Envelope等の既定CC番号がある。
- **混同**: Note On
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Note On

- **正式名称**: Note On
- **直訳**: 音符オン
- **意味**: 音高番号とVelocityを含むMIDI発音メッセージ。Velocity 1〜127がマニュアルの実装表に記載される。
- **混同**: Note Off
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Note Off

- **正式名称**: Note Off
- **直訳**: 音符オフ
- **意味**: 発音を止めるMIDIメッセージ。Xsynthの実装表はNote Off専用形式とVelocity 0のNote Onを示す。
- **混同**: Sustain
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### MIDI Clock

- **正式名称**: MIDI Clock
- **直訳**: MIDI時計
- **意味**: テンポ同期用のMIDIタイミング情報。XsynthではGLOBALで受信を設定し、ArpeggiatorやLFO同期に関係する。
- **混同**: Sampling rate
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Local Off

- **正式名称**: Local Off（UI名）
- **直訳**: 局所オフ
- **意味**: Xsynth自身の鍵盤と内蔵シンセの直結を切る設定。外部MIDI経路で二重発音やMIDIフィードバックを避ける。
- **混同**: MIDI Panic
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### MIDI Panic

- **正式名称**: MIDI PANIC（UI名）
- **直訳**: MIDI非常停止
- **意味**: 止まらないノートを止めるための本体操作。音色やパッチを初期化する操作ではない。
- **混同**: Factory Reset
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Factory Reset

- **正式名称**: Factory reset（UI名）
- **直訳**: 工場リセット
- **意味**: 全設定、パッチ、構成データを工場状態へ戻し、保存データを消す操作。実行前にバックアップが必要。
- **混同**: Init Patch
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Editor

- **正式名称**: Xsynth Editor（製品付属ソフト名）
- **直訳**: 編集者
- **意味**: Mac、Windows、iPadで音色や設定を編集・保存する専用アプリ。ハードウェア内部の音源そのものではない。
- **混同**: Firmware
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Firmware

- **正式名称**: Firmware
- **直訳**: 
- **意味**: Xsynth本体の動作を更新するデータ。更新中はUSB、電源、MIDI接続を切らないようマニュアルが指示する。
- **混同**: Editor
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Category Filter

- **正式名称**: Category Filter（Editor UI名）
- **直訳**: 分類絞り込み
- **意味**: Editorでパッチをカテゴリ単位に表示・並べ替える機能。一つのパッチを複数カテゴリへ割り当てられる。
- **混同**: Bank
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Patch memory

- **正式名称**: Patch memory
- **直訳**: パッチ記憶
- **意味**: 保存音色を保持する本体メモリ。製品ページは512 sounds、4 banks of 128 patchesと記載する。
- **混同**: Arp Pattern
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Bank

- **正式名称**: Bank（UI名）
- **直訳**: 銀行・貯蔵所
- **意味**: パッチやパターンをまとめる保存区分。Xsynth製品ページではパッチが4バンクに分かれる。
- **混同**: Category
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Bus-powered

- **正式名称**: Bus-powered
- **直訳**: バスから電力供給
- **意味**: USB接続側から電源を受けて動作する方式。電池式という意味ではない。
- **混同**: Power switch
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### TRS A

- **正式名称**: TRS A（Tip Ring Sleeve Type A）端子配列
- **直訳**: チップ・リング・スリーブA配列
- **意味**: Xsynthの3.5mm DIN MIDI変換で使う端子配列。DIN MIDIアダプターはTRS A対応が必要である。
- **混同**: USB-C
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### Class compliant

- **正式名称**: Class compliant
- **直訳**: 規格準拠
- **意味**: 追加ドライバーなしで標準USB Audio機器として扱える性質。Windowsでは推奨ASIOドライバーが別に案内される。
- **混同**: ASIO
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

### ASIO

- **正式名称**: ASIO（Audio Stream Input/Output）
- **直訳**: 音声データの入出力
- **意味**: Windowsで低遅延音声入出力を扱うドライバー方式。XsynthにはWindows 10/11用ASIOドライバーが案内される。
- **混同**: Class compliant
- 出典: [Xsynth User Manual v. 1.8（公式）](https://download.esi-audio.com?w=esi&p=131&g=5&l=en)
- 最終確認: 

