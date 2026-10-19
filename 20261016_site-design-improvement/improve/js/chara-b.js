// 方向B 人物一覧: 行形式の索引。検索・並び替え（出演数を含む4種）・所属絞り込み・読み継ぎ列。
"use strict";

const tbody = document.getElementById("tbody");
const empty = document.getElementById("empty");
const line = document.getElementById("result-line");
const q = document.getElementById("q");
const sortSel = document.getElementById("sort");
const chips = Array.from(document.querySelectorAll(".chip[data-aff]"));
let rows = [];
let works = [];
// 出演数は行ごと・比較ごとに数えないですむよう、読み込み後に人物ID→作数の索引を組む
let workCountById = new Map();

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const text = (s) => esc(s ?? "（未記録）");

const AFF_ORDER = ["回廊聖堂", "教団", "鐘楼", "祝祭庁", "地下病院", "独立", "不明"];

function workCount(id) {
  return workCountById.get(id) || 0;
}

function render(list) {
  empty.hidden = list.length > 0;
  tbody.innerHTML = list
    .map(
      (c) => {
        const n = workCount(c.id);
        const label = n > 0 ? `${n}作` : "0作";
        return `<tr>
        <th scope="row">${text(c.name)}</th>
        <td>${text(c.role)}</td>
        <td>${text(c.affiliation)}</td>
        <td class="app">${text(c.appearance)}</td>
        <td><a href="catalog.html" title="目録棚へ">${label} →</a></td>
      </tr>`;
      }
    )
    .join("");
  line.textContent = list.length ? `${list.length}人を表示中。` : "0件。";
}

function apply() {
  const chip = chips.find((b) => b.getAttribute("aria-pressed") === "true");
  const aff = chip ? chip.dataset.aff : "all";
  const word = q.value.trim().toLowerCase();
  const key = sortSel.value;

  let list = rows.filter(
    (r) =>
      (aff === "all" || r.affiliation === aff) &&
      (!word || (r.name + r.role + r.affiliation + (r.appearance || "")).toLowerCase().includes(word))
  );

  if (key === "aff") {
    list = list.slice().sort((a, b) => {
      const ia = AFF_ORDER.indexOf(a.affiliation);
      const ib = AFF_ORDER.indexOf(b.affiliation);
      return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib) || a.name.localeCompare(b.name, "ja");
    });
  } else if (key === "name") {
    list = list.slice().sort((a, b) => a.name.localeCompare(b.name, "ja"));
  } else if (key === "works") {
    list = list.slice().sort((a, b) => workCount(b.id) - workCount(a.id) || a.name.localeCompare(b.name, "ja"));
  }

  render(list);
}

Promise.all([
  fetch("data/characters.json").then((r) => r.json()),
  fetch("data/works.json").then((r) => r.json()),
]).then(([ch, wk]) => {
  rows = ch.characters;
  works = wk.works;
  for (const w of works) {
    for (const id of w.characters || []) {
      workCountById.set(id, (workCountById.get(id) || 0) + 1);
    }
  }
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
sortSel.addEventListener("change", apply);

document.getElementById("reset").addEventListener("click", (e) => {
  e.preventDefault();
  q.value = "";
  sortSel.value = "id";
  chips.forEach((x) => x.setAttribute("aria-pressed", String(x.dataset.aff === "all")));
  apply();
});
