// 作品一覧（モック）。序列順に並べて出す。0件と読み込み失敗は文言で区別する。
"use strict";

const tbody = document.getElementById("tbody");
const empty = document.getElementById("empty");
const line = document.getElementById("result-line");

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function render(list) {
  empty.hidden = list.length > 0;
  tbody.innerHTML = list
    .map((w) => `<tr>
        <td>${esc(w.orderLabel || "")}</td>
        <td>${esc(w.title)}</td>
        <td>${esc(w.released || "—")}</td>
      </tr>`)
    .join("");
  line.textContent = list.length
    ? `${list.length}件を表示中。`
    : "0件。";
}

fetch("data/works.json")
  .then((r) => r.json())
  .then((d) => {
    const works = (d.works || []).slice().sort((a, b) => {
      const ao = a.order == null;
      const bo = b.order == null;
      if (ao !== bo) return ao ? 1 : -1;
      if (ao && bo) return String(a.released || "").localeCompare(String(b.released || ""));
      return a.order - b.order;
    });
    render(works);
  })
  .catch((e) => {
    console.error(e);
    line.textContent = "";
    empty.hidden = false;
  });
