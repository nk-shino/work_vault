// 案B: 作業効率を優先。13人を一覧（行形式）で並べ、検索・並び替え・所属横断を短くする。
"use strict";

const tbody = document.getElementById("tbody");
const empty = document.getElementById("empty");
const line = document.getElementById("result-line");
const q = document.getElementById("q");
const sortSel = document.getElementById("sort");
const chips = Array.from(document.querySelectorAll(".chip[data-aff]"));
let rows = [];

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const text = (s) => esc(s ?? "（未記録）");

const AFF_ORDER = ["回廊聖堂", "教団", "鐘楼", "祝祭庁", "地下病院", "独立", "不明"];

function render(list) {
  empty.hidden = list.length > 0;
  tbody.innerHTML = list
    .map(
      (c) => `<tr>
        <th scope="row">${text(c.name)}</th>
        <td>${text(c.role)}</td>
        <td>${text(c.affiliation)}</td>
        <td class="app">${text(c.appearance)}</td>
      </tr>`
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
  }

  render(list);
}

fetch("data/characters.json")
  .then((r) => r.json())
  .then((d) => {
    rows = d.characters;
    apply();
  });

chips.forEach((b) =>
  b.addEventListener("click", () => {
    chips.forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    apply();
  })
);
q.addEventListener("input", apply);
sortSel.addEventListener("change", apply);

document.getElementById("reset").addEventListener("click", (e) => {
  e.preventDefault();
  q.value = "";
  sortSel.value = "id";
  chips.forEach((x) => x.setAttribute("aria-pressed", String(x.dataset.aff === "all")));
  apply();
});
