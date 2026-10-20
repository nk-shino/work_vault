#!/usr/bin/env node
// UT + ITA テストランナー（依存なし）。webroot 直下の tools/ に置いて実行する。
//   node tools/run-tests.js
// UT: make-catalog.js の関数を vm で読み込み、正規化・採番・重複統合を検査する
// ITA: html→js→data→html(id) の結合と、サイト内リンクの完全性を検査する
"use strict";

const fs = require("fs");
const path = require("path");
const os = require("os");
const vm = require("vm");

const ROOT = path.join(__dirname, "..");
let passes = 0;
let failures = 0;
const ok = (name, cond, detail) => {
  if (cond) { passes++; console.log(`PASS ${name}`); }
  else { failures++; console.log(`FAIL ${name}${detail ? " — " + detail : ""}`); }
};

// ========== UT: make-catalog.js の関数単体 ==========
const catSrc = fs.readFileSync(path.join(__dirname, "make-catalog.js"), "utf8")
  .replace(/^#![^\n]*\n/, "")
  .replace(/^main\(\);\s*$/m, "");

function loadMakeCatalog(toolsDir) {
  const src = fs.readFileSync(path.join(toolsDir, "make-catalog.js"), "utf8")
    .replace(/^#![^\n]*\n/, "")
    .replace(/^main\(\);\s*$/m, "");
  const sandbox = { require, console, __dirname: toolsDir, module: { exports: {} }, process: { argv: [] } };
  vm.runInNewContext(src + "\nmodule.exports = { norm, build, check };", sandbox);
  return sandbox.module.exports;
}

const mk = loadMakeCatalog(__dirname);
ok("UT norm: 鉤括弧と前後空白を両側で除去", mk.norm("「第一楽曲黄昏の封印」") === "第一楽曲黄昏の封印" && mk.norm("  題名  ") === "題名");
ok("UT norm: 鉤括弧が無い値は変化なし", mk.norm("調律") === "調律");

const built = mk.build();
ok("UT build: 件数は元データの合計", built.length === 50, `実際=${built.length}`);
const kinds = {};
for (const c of built) kinds[c.kind] = (kinds[c.kind] || 0) + 1;
ok("UT build: 種別の内訳 13/13/9/15", kinds["作品"] === 13 && kinds["人物"] === 13 && kinds["出来事"] === 9 && kinds["用語"] === 15, JSON.stringify(kinds));
const ids = built.map((c) => c.id);
ok("UT build: ID重複なし", new Set(ids).size === ids.length);
ok("UT build: 先頭作品は W-001", built.find((c) => c.id === "W-001")?.title === "第一楽曲黄昏の封印");
ok("UT build: E-001 は日付を持つ", built.find((c) => c.id === "E-001")?.date === "2023-01-15");
ok("UT check: 現行データでエラー無し", mk.check(built).length === 0, mk.check(built).join(" / "));

// 重複題の統合と採番の連続性（カウンタ方式の検証）。temp に同構成を作って本物の関数で試す
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "mkcat-ut-"));
fs.mkdirSync(path.join(tmp, "tools"));
fs.mkdirSync(path.join(tmp, "data"));
fs.copyFileSync(path.join(__dirname, "make-catalog.js"), path.join(tmp, "tools", "make-catalog.js"));
const w = (f, d) => fs.writeFileSync(path.join(tmp, "data", f), JSON.stringify(d));
w("works.json", { works: [] });
w("characters.json", { characters: [] });
w("glossary.json", { glossary: [] });
w("sources.json", { groups: [] });
w("history.json", { timeline: [
  { id: "h1", date: "2020-01-01", title: "「試験の鐘」" },
  { id: "h2", date: "2020-01-02", title: "試験の鐘" },
  { id: "h3", date: "2020-01-03", title: "「終わりの歌」" }
] });
const mkTmp = loadMakeCatalog(path.join(tmp, "tools"));
const builtTmp = mkTmp.build();
const byRef = new Map(builtTmp.map((c) => [c.ref, c.id]));
ok("UT build: 正規化して同題の出来事は同一IDに統合", byRef.get("h1") === "E-001" && byRef.get("h2") === "E-001", `h1=${byRef.get("h1")} h2=${byRef.get("h2")}`);
ok("UT build: 統合の後ろの項は欠番を作らず連続採番", byRef.get("h3") === "E-002", `h3=${byRef.get("h3")}`);
fs.rmSync(tmp, { recursive: true, force: true });

// ========== ITA: html→js→data→html(id) の結合 ==========
const htmls = fs.readdirSync(ROOT).filter((f) => f.endsWith(".html"));
const jsFiles = fs.readdirSync(path.join(ROOT, "js")).filter((f) => f.endsWith(".js"));

// 1. html が読み込む js は実在する
const htmlToJs = new Map();
for (const h of htmls) {
  const src = fs.readFileSync(path.join(ROOT, h), "utf8");
  const m = src.match(/<script[^>]*src="js\/([^"]+)"/);
  if (m) htmlToJs.set(h, m[1]);
}
for (const [h, j] of htmlToJs) {
  ok(`ITA ${h} → js/${j} 実在`, fs.existsSync(path.join(ROOT, "js", j)));
}

// 2. すべての js はどこかの html から読まれる
const usedJs = new Set(htmlToJs.values());
for (const j of jsFiles) ok(`ITA js/${j} は少なくとも1頁から読まれる`, usedJs.has(j));

// 3. js が fetch する data は実在し、JSON として解釈できる
const jsToHtml = new Map([...htmlToJs].map(([h, j]) => [j, h]));
for (const j of jsFiles) {
  const src = fs.readFileSync(path.join(ROOT, "js", j), "utf8");
  const fetches = [...src.matchAll(/fetch\("data\/([^"]+)"\)/g)].map((m) => m[1]);
  for (const f of [...new Set(fetches)]) {
    const p = path.join(ROOT, "data", f);
    let good = false;
    let detail = "ファイル無し";
    if (fs.existsSync(p)) {
      try { JSON.parse(fs.readFileSync(p, "utf8")); good = true; detail = ""; }
      catch (e) { detail = e.message; }
    }
    ok(`ITA js/${j} → data/${f} 実在かつJSON`, good, detail);
  }
}

// 4. data の最上位キー（js が参照する形）
const expectedKeys = {
  "catalog.json": ["catalog"],
  "characters.json": ["characters"],
  "works.json": ["works"],
  "glossary.json": ["glossary"],
  "history.json": ["timeline"],
  "sources.json": ["groups"],
  "series.json": ["series"]
};
for (const [f, keys] of Object.entries(expectedKeys)) {
  const p = path.join(ROOT, "data", f);
  if (!fs.existsSync(p)) continue;
  const d = JSON.parse(fs.readFileSync(p, "utf8"));
  ok(`ITA data/${f} の最上位キー`, keys.every((k) => Array.isArray(d[k])), `期待=${keys.join(",")}`);
}

// 5. js が getElementById / querySelector("#…") で拾う id は、対応する html に存在する
for (const [j, h] of jsToHtml) {
  const src = fs.readFileSync(path.join(ROOT, "js", j), "utf8");
  const html = fs.readFileSync(path.join(ROOT, h), "utf8");
  const ids = new Set();
  for (const m of src.matchAll(/getElementById\("([^"]+)"\)/g)) ids.add(m[1]);
  for (const m of src.matchAll(/querySelector(?:All)?\("#([A-Za-z0-9_-]+)"/g)) ids.add(m[1]);
  for (const id of ids) {
    ok(`ITA js/${j} の #${id} は ${h} に存在`, new RegExp(`id="${id}"`).test(html));
  }
}

// 6. サイト内リンクの完全性（html + js の href、クエリや # は除外）
const missing = new Map();
for (const h of htmls) {
  const src = fs.readFileSync(path.join(ROOT, h), "utf8");
  for (const m of src.matchAll(/href="([^"]+)"/g)) {
    const t = m[1].split("?")[0].split("#")[0];
    if (t.endsWith(".html") && !fs.existsSync(path.join(ROOT, t))) missing.set(`${h} → ${t}`, (missing.get(`${h} → ${t}`) || 0) + 1);
  }
}
for (const j of jsFiles) {
  const src = fs.readFileSync(path.join(ROOT, "js", j), "utf8");
  for (const m of src.matchAll(/href="([^"]+)"/g)) {
    const t = m[1].split("?")[0].split("#")[0];
    if (t.endsWith(".html") && !fs.existsSync(path.join(ROOT, t))) missing.set(`js/${j} → ${t}`, (missing.get(`js/${j} → ${t}`) || 0) + 1);
  }
}
ok("ITA サイト内リンクはすべて実在ページを指す", missing.size === 0, [...missing.keys()].join(" / "));

console.log(`\n結果: ${passes} PASS / ${failures} FAIL`);
process.exit(failures ? 1 : 0);
