---
title: Daily Report <% tp.date.now("YYYY-MM-DD") %>
date: <% tp.date.now("YYYY-MM-DD") %>
day: <% tp.date.now("dddd") %>
tags:
  - daily
  - work-log
  - <% tp.date.now("YYYY/MM") %>
status: WIP
---

## 今日の狙い
- 

## やったこと

### 
- 何を: 
- 結果: 
- 成果物: [[]]
- 状態: WIP

## 決めたこと・決まっていないこと
#### 確定
- 

#### 保留
- （詳細は [[]] に集約）

## 打ち合わせ
- 日時 / 場所: 
- 出席: 
- 決定: 
- 次アクション: 

## 気づき
- 

## 課題

- ### 内容: 

- ### 影響: 

- ### 次アクション: 


## 明日やること
- [ ] 


## メモ
- 

## キーワード
- #

## リンク
- 前日: [[Daily Report <% tp.date.now("YYYY-MM-DD", -1) %>]]
- 翌日: [[Daily Report <% tp.date.now("YYYY-MM-DD", 1) %>]]
- 週次: [[Weekly Review <% tp.date.now("gggg-[W]WW") %>]]
<%*
await tp.file.move("/02_Daily/Daily Report " + tp.date.now("YYYY-MM-DD"))
%>
