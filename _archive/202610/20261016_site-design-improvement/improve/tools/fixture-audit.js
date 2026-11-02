// fixture の品質点検: 空・null・欠損キーの棚卸し（検査確認.md §6.1）
const fs = require("fs");
const path = require("path");
const DATA = path.join(__dirname, "..", "data");

let empty = 0;
const emptyList = [];
for (const f of fs.readdirSync(DATA)) {
  const d = JSON.parse(fs.readFileSync(path.join(DATA, f), "utf8"));
  const walk = (o, p) => {
    if (o === null) { empty++; emptyList.push(`${f}: ${p} = null`); return; }
    if (o === "") { empty++; emptyList.push(`${f}: ${p} = ""`); return; }
    if (Array.isArray(o)) { o.forEach((x, i) => walk(x, `${p}[${i}]`)); return; }
    if (typeof o === "object") {
      for (const [k, v] of Object.entries(o)) {
        walk(v, `${p}.${k}`);
      }
    }
  };
  walk(d, "");
}
console.log("空値・null の総数:", empty);
for (const l of emptyList) console.log("  ", l);

// 長文・境界値の有無
console.log("\n--- 長文の棚卸し（100文字超の文字列値） ---");
let long = 0;
for (const f of fs.readdirSync(DATA)) {
  const d = JSON.parse(fs.readFileSync(path.join(DATA, f), "utf8"));
  const walk = (o, p) => {
    if (typeof o === "string" && o.length > 100) { long++; console.log(`  ${f}: ${p} = ${o.length}文字`); }
    if (Array.isArray(o)) { o.forEach((x, i) => walk(x, `${p}[${i}]`)); return; }
    if (o && typeof o === "object") for (const [k, v] of Object.entries(o)) walk(v, `${p}.${k}`);
  };
  walk(d, "");
}
if (!long) console.log("  なし");
