// 検証状態の共通定義（C-2・2026-10-28）: catalog-a/catalog-c（VERIFY）と
// chara-c/events-c（BADGE）に同一内容で重複していた定義を一元化した。
// 既存頁のコード変更を最小限に保つため、両方の名前を残す（BADGE は VERIFY の別名）。
"use strict";

const VERIFY = {
  confirmed: { label: "確認済", cls: "ok" },
  supplement: { label: "要補足", cls: "sup" },
  unverified: { label: "未検証", cls: "" },
  none: { label: "出典なし", cls: "none" },
};
const BADGE = VERIFY;
