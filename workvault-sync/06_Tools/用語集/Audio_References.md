# 音響資格 参照

## 資格範囲の確認

[A1] 中央職業能力開発協会・令和8年度「技能検定 受検案内」
https://www.javada.or.jp/jigyou/gino/pdf/R08_ginoukentei3kyu.pdf

照合内容: 「舞台機構調整（音響機構調整作業）3級」について、実技は課題音源を用いた音響機器のセッティング、リハーサル、本番ミキシング（音出し）、原状復帰、およびCDに記録された種々の音の判別。学科は舞台一般、音響機構調整法、電気、関係法規、安全衛生。案内には実技の標準時間（セッティング8分、ミキシング約2分、原状復帰2分以内、判断等約20分）と、原則の合否基準（実技60点以上、学科65点以上）も記載されています。

本成果物はこの3級案内を確認したうえで作った「級未指定の共通基礎ノート」です。3級の範囲を含む基礎学習資料ですが、受検地・年度の細目や公式問題を網羅せず、試験対策完全・合格を保証しません。最新の受検資格、日程、持参品、課題は受検地の職業能力開発協会の案内を優先してください。

## 一次技術資料

[A2] Yamaha Corporation, “Audio quality in networked systems,” 5.2 Dynamic range / 5.3 Sampling issues / 5.5 Absolute latency / 5.10 Jitter
https://uk.yamaha.com/en/business/audio/resources/self-training/audio-quality/05-audio-quality.html

照合範囲: ADC/DAC、PCM、ビット深度、量子化誤差、ナイキスト・シャノン標本化定理、アンチエイリアスフィルター、サンプリング周波数、デジタル遅延、ジッター。48 kHzの標本間隔やfs/2の帯域限界の説明を本文で確認しました。

[A3] Shure, “Microphone Techniques for Recording,” Microphone Techniques / Phantom Power / Balanced / Impedance
https://www.shure.com/damfiles/default/global/documents/publications/en/performance-production/microphone_techniques_for_recording_english.pdf-bb0469316afdb6118691d2f3f5e3ff01.pdf

照合範囲: バランス回路、ファンタム電源（一般に12–48 V、XLRのPin 2/3への供給）、マイク指向性、インピーダンス、ダイナミック・コンデンサー・リボンの基礎。本文を確認しました。なお、バランス伝送の本質は同相ノイズ除去とインピーダンス対称性であり、常に「逆相信号が必須」と単純化しません。

[A4] Yamaha Corporation, “Audio quality in networked systems,” 5.3 Sampling issues（公式別地域URL）
https://usa.yamaha.com/products/contents/proaudio/docs/audio_quality/05-audio-quality.html

照合範囲: 対象帯域をサンプリング周波数の半分未満に制限すること、ADC前のローパス（アンチエイリアス）処理、エイリアシングの不可逆性。本文を確認しました。

## 数式・基準の照合メモ

- 電圧・音圧など振幅比: 20 log10(x/x0)。電力比: 10 log10(P/P0)。
- dB SPLの基準音圧: 20 µPa（空気中）。
- 0 dBu: 0.775 Vrms。0 dBV: 1 Vrms。
- dBFSはデジタルフルスケールに対するサンプル値のレベル。サンプルピークと、補間して求めるtrue peak（dBTP）は区別する。
- ナイキスト周波数はサンプリング周波数の1/2。ただし、信号帯域をその値未満へ制限することが必要。

## 限界

Web資料の本文照合と文献ベースの確認であり、実機操作、測定マイクによる校正、会場での音出し、技能検定の公式過去問による採点は実施していません。
