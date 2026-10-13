# Learnings

## [LRN-20261013-001] correction

**Logged**: 2026-10-13T17:30:00+09:00
**Priority**: high
**Status**: promoted
**Area**: docs

### Summary
ユーザーから「会議で決定した」という記述を確認なしに事実として扱ってはならない。

### Details
「Excel MRUとWindows Recentから利用実態を逆算する方針が会議で決定」という前提の下で作業を進めようとしたが、ユーザーが「これは虚偽。会議で決定した内容をもう一度精査してください。調査方針は独断です」と指摘した。
つまり、(1) 会議で決定された事実は存在せず、(2) その調査方針（MRU/Recent解析による利用実態の逆算）はエージェントまたは誰かの独断に過ぎなかった。
エージェントは会議の実在・決議内容を一次情報（議事録・出席者確認）なしに「決定事項」として扱ってはならない。
事実（会議で決まった）と提案（調査方針）を区別し、後者には「提案・未決」のラベルを付ける。

### Suggested Action
- ユーザーの発話に「会議で決定」等の権威づけが含まれる場合、議事録や関係者の確認という一次根拠を求めるか、確認できない場合は「未確認の主張」として扱う
- 自ら提案した調査方針を「決定事項」として文書化しない

### Metadata
- Source: user_feedback
- Related Files: (none)
- Tags: 虚偽防止, 事実と推測の分離, 会議記録
- See Also: (none)
- Pattern-Key: verify.authority_claim
- Recurrence-Count: 1
- First-Seen: 2026-10-13
- Last-Seen: 2026-10-13

### Context Maintenance
- Decay-Type: decision
- Decay-Rate: durable
- Authority: user feedback; Owner: 篠原 想詩
- Revalidation: 会議記録という主張が再び出たときに毎回適用
- Validation: verified; Last-Validated: 2026-10-13; Evidence: user's direct correction in conversation
- Disposition: externalize; Application: applied (promoted to skill: authority-claim-verification)

---
