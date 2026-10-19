// 方向A 目録棚: 帳面形式。検索1欄のみ。種別の列を省いた1行1項の帳面。
"use strict";

const tbody = document.getElementById("tbody");
const empty = document.getElementById("empty");
const line = document.getElementById("result-line");
const q = document.getElementById("q");
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
        <td>${esc(c.title)}</td>
        <td>${c.date ? esc(c.date) : "—"}</td>
        <td><span class="badge ${v.cls}">${v.label}</span></td>
      </tr>`;
    })
    .join("");
  line.textContent = list.length ? `${list.length}項を表示中。` : "0項。";
}

function apply() {
  const word = q.value.trim().toLowerCase();
  const list = rows.filter((r) => !word || (r.title + r.id).toLowerCase().includes(word));
  render(list);
}

fetch("data/catalog.json")
  .then((r) => r.json())
  .then((d) => {
    rows = d.catalog;
    apply();
  })
  .catch((e) => {
    console.error(e);
    line.textContent = "データを読み込めない。data/ の配置を確認（0項とは別の状態）。";
  });

let qTimer;
q.addEventListener("input", () => {
  clearTimeout(qTimer);
  qTimer = setTimeout(apply, 80);
});

document.getElementById("reset").addEventListener("click", (e) => {
  e.preventDefault();
  q.value = "";
  apply();
});
