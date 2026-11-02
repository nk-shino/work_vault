// 方向B 目録棚: 種別棚＋関連列（読み継ぎ）。既存データで組める接続のみを出す。
"use strict";

const tbody = document.getElementById("tbody");
const empty = document.getElementById("empty");
const line = document.getElementById("result-line");
const q = document.getElementById("q");
// home-b からの受け渡し（catalog-b.html?q=語）。value への代入は HTML を経由しないため安全
const q0 = new URLSearchParams(location.search).get("q");
if (q0) q.value = q0;
const chips = Array.from(document.querySelectorAll(".chip[data-kind]"));
const shelves = document.getElementById("shelves");
let rows = [];
let charById = new Map();
let workById = new Map();
let glossById = new Map();
let histById = new Map();
let charsByWork = new Map();
let glossByWork = new Map();

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// 既存データで組める接続（実測）:
//   作品 → 人物（works.characters）/ 出演作（人物→作品は逆索引）
//   用語 → 作品（glossary.workId）
//   出来事 → 作品（history.workId）
//   人物 → 用語: 接続データ無し。出さない
// 行ごとの線形検索を避けるため、読み込み後に索引 Map を組み替えて使う
function linksFor(r) {
  const out = [];
  const tail = (t) => t.replace(/[「」]/g, "").replace(/^第(.+)楽曲/, "第$1曲");
  if (r.kind === "作品") {
    for (const c of charsByWork.get(r.ref) || []) out.push({ label: c.name, href: "chara-b.html" });
    for (const g of glossByWork.get(r.ref) || []) out.push({ label: g.term, href: "catalog.html" });
  } else if (r.kind === "用語") {
    const g = glossById.get(r.ref);
    const w = g && workById.get(g.workId);
    if (w) out.push({ label: tail(w.title), href: "catalog.html" });
  } else if (r.kind === "出来事") {
    const h = histById.get(r.ref);
    const w = h && h.workId && workById.get(h.workId);
    if (w) out.push({ label: tail(w.title), href: "catalog.html" });
  }
  return out.slice(0, 3);
}

function render(list) {
  empty.hidden = list.length > 0;
  tbody.innerHTML = list
    .map((r) => {
      const ls = linksFor(r);
      const rel = ls.length
        ? `<ul class="b-links">${ls.map((l) => `<li><a href="${l.href}">${esc(l.label)} →</a></li>`).join("")}</ul>`
        : `<span style="color:var(--text-sub); font-size:11px;">—</span>`;
      return `<tr>
        <td>${esc(r.id)}</td>
        <td>${esc(r.kind)}</td>
        <td>${esc(r.title)}</td>
        <td>${r.date ? esc(r.date) : "—"}</td>
        <td>${rel}</td>
      </tr>`;
    })
    .join("");
  line.textContent = list.length ? `${list.length}項を表示中。` : "0項。";
}

function apply() {
  const kind = (chips.find((b) => b.getAttribute("aria-pressed") === "true") || {}).dataset.kind || "all";
  const word = q.value.trim().toLowerCase();
  const list = rows.filter(
    (r) =>
      (kind === "all" || r.kind === kind) &&
      (!word || (r.title + r.id + r.kind).toLowerCase().includes(word))
  );
  render(list);
}

function renderShelves() {
  const kinds = ["作品", "人物", "出来事", "用語"];
  shelves.innerHTML = kinds
    .map((k) => {
      const n = rows.filter((r) => r.kind === k).length;
      return `<li><a href="#" data-shelf="${k}"><span class="b-shelf-label">${k}</span>${n}項 →</a></li>`;
    })
    .join("");
  shelves.addEventListener("click", (e) => {
    const a = e.target.closest("a[data-shelf]");
    if (!a) return;
    e.preventDefault();
    const k = a.dataset.shelf;
    chips.forEach((x) => x.setAttribute("aria-pressed", String(x.dataset.kind === k)));
    apply();
  });
}

Promise.all([
  fetch("data/catalog.json").then((r) => r.json()),
  fetch("data/characters.json").then((r) => r.json()),
  fetch("data/works.json").then((r) => r.json()),
  fetch("data/glossary.json").then((r) => r.json()),
  fetch("data/history.json").then((r) => r.json()),
]).then(([cat, ch, wk, gl, hs]) => {
  rows = cat.catalog;
  charById = new Map(ch.characters.map((c) => [c.id, c]));
  workById = new Map(wk.works.map((w) => [w.id, w]));
  glossById = new Map(gl.glossary.map((g) => [g.id, g]));
  histById = new Map(hs.timeline.map((h) => [h.id, h]));
  charsByWork = new Map(
    wk.works.map((w) => [w.id, (w.characters || []).map((id) => charById.get(id)).filter(Boolean)])
  );
  glossByWork = new Map();
  for (const g of gl.glossary) {
    if (!glossByWork.has(g.workId)) glossByWork.set(g.workId, []);
    glossByWork.get(g.workId).push(g);
  }
  renderShelves();
  apply();
}).catch((e) => {
  console.error(e);
  line.textContent = "データを読み込めない。data/ の配置を確認（0件とは別の状態）。";
});

chips.forEach((b) =>
  b.addEventListener("click", () => {
    chips.forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    apply();
  })
);
let qTimer;
q.addEventListener("input", () => {
  clearTimeout(qTimer);
  qTimer = setTimeout(apply, 80);
});

document.getElementById("reset").addEventListener("click", (e) => {
  e.preventDefault();
  q.value = "";
  chips.forEach((x) => x.setAttribute("aria-pressed", String(x.dataset.kind === "all")));
  apply();
});
