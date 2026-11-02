---
name: verification-before-completion
description: Pre-completion verification checklist. Use BEFORE declaring any task done, before telling the user "完了しました", after implementing a fix or feature, and before committing. Trigger on "完了", "できた", "動作確認", or whenever about to report finished work. Ensures the work actually works, not just looks done.
---

# 完了前検証 (Verification Before Completion)

## 原則

「ビルドが通った」「エラーが出なくなった」は「正しく動く」と同じではない。**完了を宣言する前に、自分の作業の出力を自分の目で確認する。**

## 検証チェックリスト

完了報告の前に、順に確認する:

1. **要求の再確認**: ユーザーの依頼内容をもう一度読み、すべて満たしているか。一部だけ実装していないか
2. **動作確認**:
   - 実際にコードを実行したか(コンパイル/型チェックだけでは不十分)
   - 変更した機能の動作を具体的に確認したか
   - プロジェクトにテストがあればテストを実行したか(テストコマンドが不明ならユーザーに尋ねる)
3. **差分確認**: `git diff` で変更内容を見直す
   - デバッグ用のコード(console.log, print, 一時的なコメントアウト)が残っていないか
   - 意図しないファイルが変更されていないか
   - 秘密情報(キー、トークン、パスワード)が含まれていないか
4. **副作用確認**: 変更が他の機能を壊していないか。呼び出し元、関連テストを確認する
5. **虚偽報告の排除**:
   - 実行していないコマンドを「実行した」と報告しない
   - エラーが出たまま「動くと思います」と報告しない。エラーを解決するか、正直に状態を報告する
   - ツールの結果をちゃんと読み、失敗を成功として扱わない

## 報告の形式

検証結果を含めて報告する:

```
完了: <やったこと>
確認: <実行したコマンドと結果>
残課題: <あれば>
```

検証できなかった項目がある場合は、その理由と確認方法を明示する。「たぶん動きます」は報告しない。
