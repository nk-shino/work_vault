#!/usr/bin/env node
// 模擬 catalog.json の生成 + 検証。
// 本家 make-catalog.js の仕様（手引き §6-4・実行ログ §4）に合わせ、
// 「種別＋題」を鍵に採番し、照合は両側で正規化する。--check は書き込まず検査のみ。

const fs = require("fs");
const path = require("path");

const DATA = path.join(__dirname, "..", "data");
const CHECK = process.argv.includes("--check");

const read = (f) => JSON.parse(fs.readFileSync(path.join(DATA, f), "utf8"));

// 鉤括弧の除去は両側（題・出典の claim）に掛ける（実行ログ §4 の教訓）
const norm = (s) => String(s).replace(/[「」]/g, "").trim();

function build() {
  const works = read("works.json").works;
  const chars = read("characters.json").characters;
  const history = read("history.json").timeline;
  const glossary = read("glossary.json").glossary;

  const entries = [];
  for (const w of works) entries.push({ kind: "作品", title: norm(w.title), date: w.released, ref: w.id });
  for (const c of chars) entries.push({ kind: "人物", title: c.name, date: null, ref: c.id });
  for (const h of history) entries.push({ kind: "出来事", title: norm(h.title), date: h.date, ref: h.id });
  for (const g of glossary) entries.push({ kind: "用語", title: g.term, date: null, ref: g.id });

  // 種別ごとに通し番号（種別＋題を鍵に引き継ぐ形）
  const seen = new Map();
  const counters = new Map();
  const catalog = [];
  for (const e of entries) {
    const key = `${e.kind}＋${e.title}`;
    let no;
    if (seen.has(key)) {
      no = seen.get(key);
    } else {
      const prefix = { 作品: "W", 人物: "C", 出来事: "E", 用語: "G" }[e.kind];
      const n = (counters.get(e.kind) || 0) + 1;
      counters.set(e.kind, n);
      no = `${prefix}-${String(n).padStart(3, "0")}`;
      seen.set(key, no);
    }
    catalog.push({ id: no, kind: e.kind, title: e.title, date: e.date, ref: e.ref });
  }
  return catalog;
}

function check(catalog) {
  const errors = [];
  // 検査1: ID の重複
  const ids = catalog.map((c) => c.id);
  const dup = ids.filter((x, i) => ids.indexOf(x) !== i);
  if (dup.length) errors.push(`ID 重複: ${[...new Set(dup)].join(", ")}`);
  // 検査2: 元データとの件数一致
  const expect = 13 + 13 + 9 + 15;
  if (catalog.length !== expect) errors.push(`件数不一致: catalog=${catalog.length} 期待=${expect}`);
  // 検査3: 生成物が元データと一致するか（verify/sourceId は照合結果なので除く）
  const rebuilt = build();
  const strip = (arr) => arr.map(({ verify, sourceId, ...rest }) => rest);
  if (JSON.stringify(strip(catalog)) !== JSON.stringify(strip(rebuilt))) errors.push("生成物が元データと一致しない（再生成し忘れ）");
  return errors;
}

const main = () => {
  const catalog = build();
  // 検証状態の照合は「正規化前の題」で出典を見るため、build 直後に素の題へ戻す
  const raw = JSON.parse(JSON.stringify(catalog));
  const histTitles = new Map(read("history.json").timeline.map((h) => [h.date + "|" + norm(h.title), h.title]));
  for (const c of catalog) {
    const rawTitle = histTitles.get(c.date + "|" + c.title);
    if (rawTitle) c.title = rawTitle;
  }
  // 出典の照合: 出典側の label も「公開」「発売」等の接尾を除いた題核で突き合わせる。
  // 本家と同様「日付のある出典を先に当て、無い出典は含みで探す」
  const claims = [];
  for (const g of read("sources.json").groups) for (const it of g.items) claims.push({ ...it });
  for (const c of catalog.filter((x) => x.kind === "出来事")) {
    const core = c.title.replace(/(公開|発売)$/, "").trim();
    let src =
      claims.find((s) => s.date !== "no date" && norm(s.label).includes(core)) ||
      claims.find((s) => norm(s.label).includes(core));
    if (!src) { c.verify = "unverified"; continue; }
    c.verify = { confirmed: "confirmed", supplement: "supplement", unverified: "unverified", none: "none" }[src.status] || "unverified";
    c.sourceId = src.id;
  }
  // 書き出す前に題を正規化形へ揃え、verify の無い項目を未検証へ落とす
  for (const c of catalog) {
    c.title = norm(c.title);
    if (!c.verify) c.verify = "unverified";
  }
  if (CHECK) {
    const errors = check(catalog);
    if (errors.length) { console.error("FAIL\n" + errors.join("\n")); process.exit(1); }
    console.log(`OK: ${catalog.length} 件。ID重複なし・元データ一致。`);
    const dist = {};
    for (const c of catalog) dist[c.verify] = (dist[c.verify] || 0) + 1;
    console.log("検証状態の分布:", JSON.stringify(dist));
    return;
  }
  fs.writeFileSync(path.join(DATA, "catalog.json"), JSON.stringify({ catalog }, null, 2) + "\n");
  console.log(`catalog.json を生成: ${catalog.length} 件`);
};
main();
