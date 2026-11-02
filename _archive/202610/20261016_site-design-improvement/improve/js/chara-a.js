// 方向A 人物一覧: 静かな名簿。現行の絞り込みだけを守り、題箋の余韻を深める。
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
        <div class="plate a-plate-fine" role="img" aria-label="肖像は準備中">${text(c.name)}</div>
        <p class="a-caption" style="margin:0">${text(c.role)}</p>
        <p class="name" style="margin:0; text-align:center;">${text(c.name)}</p>
        <p class="role" style="margin:0; text-align:center;">${text(c.affiliation)}</p>
      </li>`
    )
    .join("");
  line.textContent = `${list.length}人を表示中。`;
}

function apply() {
  const chip = chips.find((b) => b.getAttribute("aria-pressed") === "true");
  const aff = chip ? chip.dataset.aff : "all";
  const list = items.filter((c) => aff === "all" || c.affiliation === aff);
  render(list);
}

fetch("data/characters.json")
  .then((r) => r.json())
  .then((d) => {
    items = d.characters;
    apply();
  })
  .catch((e) => {
    console.error(e);
    line.textContent = "データを読み込めない。data/ の配置を確認（0人とは別の状態）。";
  });

chips.forEach((b) =>
  b.addEventListener("click", () => {
    chips.forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    apply();
  })
);
