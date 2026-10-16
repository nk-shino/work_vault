// 案A: 既存を活かす最小改善（chara.html と同じ構造・操作）。
// 差分は「欠損補正が効いていることを画面上で確かめられる」表示だけ。
"use strict";

const grid = document.getElementById("grid");
const line = document.getElementById("result-line");
const chips = Array.from(document.querySelectorAll(".chip[data-aff]"));
let items = [];

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const text = (s) => esc(s ?? "（未記録）");

function render(list) {
  grid.innerHTML = list
    .map(
      (c) => `<li class="card">
        <div class="plate" role="img" aria-label="肖像は準備中">${text(c.name)}・題箋</div>
        <p class="name" style="margin:0">${text(c.name)}</p>
        <p class="role" style="margin:0">${text(c.role)}／${text(c.affiliation)}</p>
      </li>`
    )
    .join("");
  line.textContent = `${list.length}人を表示中。`;
}

function current() {
  const aff = chips.find((b) => b.getAttribute("aria-pressed") === "true");
  return aff ? aff.dataset.aff : "all";
}

function apply() {
  const aff = current();
  render(aff === "all" ? items : items.filter((c) => c.affiliation === aff));
}

fetch("data/characters.json")
  .then((r) => r.json())
  .then((d) => {
    items = d.characters;
    apply();
  });

chips.forEach((b) =>
  b.addEventListener("click", () => {
    chips.forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    apply();
  })
);
