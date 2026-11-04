// 案C: 理解と根拠確認を優先。各人物に出典状態と作品出演を出し、根拠への導線を短くする。
"use strict";

const grid = document.getElementById("grid");
const line = document.getElementById("result-line");
const chips = Array.from(document.querySelectorAll(".chip[data-aff]"));
const q = document.getElementById("q");
let chars = [];
let works = [];
let sourceNames = {};

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const text = (s) => esc(s ?? "（未記録）");

// catalog.json から「この人物の項目が検証済みか」を引く（出典数で判定しない・verify 値を見る）
let catalogByRef = {};

const BADGE = {
  confirmed: { label: "確認済", cls: "ok" },
  supplement: { label: "要補足", cls: "sup" },
  unverified: { label: "未検証", cls: "" },
  none: { label: "出典なし", cls: "none" },
};

function worksOf(id) {
  return works
    .filter((w) => (w.characters || []).includes(id))
    .sort((a, b) => (a.released || "").localeCompare(b.released || ""));
}

function render(list) {
  grid.innerHTML = list
    .map((c) => {
      const wks = worksOf(c.id);
      const ws = wks
        .map((w) => `<a href="catalog.html" title="${esc(w.title)}（${esc(w.released)}）">${esc(w.orderLabel || w.title)}</a>`)
        .join("・");
      const cat = catalogByRef[c.id];
      const v = BADGE[cat && cat.verify] || BADGE.unverified;
      const srcId = cat && cat.sourceId;
      const src = srcId && sourceNames[srcId]
        ? `<a href="catalog.html">出典 ${esc(sourceNames[srcId])}</a>`
        : `<span class="src-none">出典なし</span>`;
      return `<li class="card">
        <div class="plate" role="img" aria-label="肖像は準備中">${text(c.name)}・題箋</div>
        <p class="name" style="margin:0">${text(c.name)} <span class="badge ${v.cls}">${v.label}</span></p>
        <p class="role" style="margin:0">${text(c.role)}／${text(c.affiliation)}</p>
        <p class="appears" style="margin:0">${ws ? `出演: ${ws}` : "出演記録なし"}</p>
        <p class="src" style="margin:0">${src}</p>
      </li>`;
    })
    .join("");
  line.textContent = `${list.length}人を表示中。`;
}

function apply() {
  const chip = chips.find((b) => b.getAttribute("aria-pressed") === "true");
  const aff = chip ? chip.dataset.aff : "all";
  const word = q.value.trim().toLowerCase();
  const list = chars.filter(
    (c) =>
      (aff === "all" || c.affiliation === aff) &&
      (!word || (c.name + c.role + c.affiliation).toLowerCase().includes(word))
  );
  render(list);
}

Promise.all([
  fetch("data/characters.json").then((r) => r.json()),
  fetch("data/works.json").then((r) => r.json()),
  fetch("data/catalog.json").then((r) => r.json()),
  fetch("data/sources.json").then((r) => r.json()),
]).then(([ch, wk, cat, src]) => {
  chars = ch.characters;
  works = wk.works;
  cat.catalog.forEach((row) => {
    if (row.kind === "人物") catalogByRef[row.ref] = row;
  });
  // 出典ID → 出典群の名前。項目単位の照合は本家 sources.json の構造に寄せる
  src.groups.forEach((g) => g.items.forEach((i) => { sourceNames[i.id] = g.name; }));
  apply();
}).catch((e) => {
  console.error(e);
  line.textContent = "データを読み込めない。data/ の配置を確認（0人とは別の状態）。";
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
