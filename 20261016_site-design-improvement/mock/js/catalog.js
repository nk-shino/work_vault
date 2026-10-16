// 目録棚（モック）。種別チップ＋検索語。0件のときは「条件に合う項目が無い」を出す。
"use strict";

const tbody = document.getElementById("tbody");
const empty = document.getElementById("empty");
const line = document.getElementById("result-line");
const q = document.getElementById("q");
const chips = Array.from(document.querySelectorAll(".chip[data-kind]"));
let rows = [];

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

const VERIFY = {
  confirmed: { label: "確認済", cls: "ok" },
  supplement: { label: "要補足", cls: "sup" },
  unverified: { label: "未検証", cls: "" },
  none: { label: "出典なし", cls: "none" },
};

function render(list) {
  empty.hidden = list.length > 0;
  tbody.innerHTML = list
    .map((c) => {
      const v = VERIFY[c.verify] || VERIFY.unverified;
      return `<tr>
        <td>${esc(c.id)}</td>
        <td>${esc(c.kind)}</td>
        <td>${esc(c.title)}</td>
        <td>${c.date ? esc(c.date) : "—"}</td>
        <td><span class="badge ${v.cls}">${v.label}</span></td>
      </tr>`;
    })
    .join("");
  line.textContent = list.length
    ? `${list.length}件を表示中。`
    : "0件。";
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

fetch("data/catalog.json")
  .then((r) => r.json())
  .then((d) => {
    rows = d.catalog;
    apply();
  });

chips.forEach((b) =>
  b.addEventListener("click", () => {
    chips.forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    apply();
  })
);

q.addEventListener("input", apply);
document.getElementById("reset").addEventListener("click", (e) => {
  e.preventDefault();
  q.value = "";
  chips.forEach((x) => x.setAttribute("aria-pressed", String(x.dataset.kind === "all")));
  apply();
});
