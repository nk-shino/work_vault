// 人物一覧（モック）。fetch → 絞り込み → 描画。外部リクエストなし。
"use strict";

const grid = document.getElementById("grid");
const line = document.getElementById("result-line");
const chips = Array.from(document.querySelectorAll(".chip[data-aff]"));
let items = [];

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function render(list) {
  grid.innerHTML = list
    .map(
      (c) => `<li class="card">
        <div class="plate" role="img" aria-label="肖像は準備中">${esc(c.name)}・題箋</div>
        <p class="name" style="margin:0">${esc(c.name)}</p>
        <p class="role" style="margin:0">${esc(c.role)}／${esc(c.affiliation)}</p>
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
