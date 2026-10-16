// fixture 境界値テスト: 検査確認.md §6.1・§5-C に基づく合成データの投入検証。
// 「正常・空・欠損・長文・異常値」を characters.json の写しに注入し、
// モックの描画 JS（chara.js と同じロジック）が壊れないかを確かめる。
// 実行: node tools/fixture-boundary-test.js   （DOM 不要・jsdom 不使用）

const assert = require("assert");
const fs = require("fs");
const path = require("path");

// chara.js の esc / text と render の文字列組み立て部分を同一ロジックで再現
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const text = (s) => esc(s ?? "（未記録）");
const card = (c) =>
  `<div class="plate" role="img" aria-label="肖像は準備中">${text(c.name)}・題箋</div>` +
  `<p class="name" style="margin:0">${text(c.name)}</p>` +
  `<p class="role" style="margin:0">${text(c.role)}／${text(c.affiliation)}</p>`;

const base = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "data", "characters.json"), "utf8")).characters;

const cases = [
  { name: "正常（現行データ）", c: base[0] },
  { name: "空文字の名前", c: { ...base[0], name: "" } },
  { name: "欠損キー（role が無い）", c: { name: "欠損", affiliation: "独立" } },
  { name: "長文（300文字の名前）", c: { ...base[0], name: "あ".repeat(300) } },
  { name: "異常値（名前が HTML・script）", c: { ...base[0], name: `<script>alert(1)</script>` } },
  { name: "異常値（引用符とアンパサンド）", c: { ...base[0], name: `"名前" & <記号>` } },
  { name: "数値の名前（型の揺れ）", c: { ...base[0], name: 123 } },
  { name: "null の名前", c: { ...base[0], name: null } },
];

let pass = 0;
let fail = 0;
for (const t of cases) {
  try {
    const html = card(t.c);
    // 検証1: 組み立てが例外を出さない
    assert.ok(typeof html === "string");
    // 検証2: エスケープが効いている（<script> が生で残らない）
    assert.ok(!/<script/i.test(html), "script タグが素通りした");
    // 検証3: null/欠損が "undefined" という文字列にならない
    assert.ok(!/undefined/.test(html), "undefined が表示用文字列に混入した");
    pass++;
    console.log(`PASS: ${t.name}`);
  } catch (e) {
    fail++;
    console.log(`FAIL: ${t.name} — ${e.message}`);
  }
}

console.log(`\n結果: ${pass}/${cases.length} PASS、FAIL ${fail}`);
process.exit(fail ? 1 : 0);
