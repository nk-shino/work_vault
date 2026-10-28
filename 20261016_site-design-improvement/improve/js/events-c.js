
"use strict";

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// BADGE は js/verify.js の共通定義（C-2）を使う

Promise.all([
  fetch("data/history.json").then((r) => r.json()),
  fetch("data/sources.json").then((r) => r.json()),
]).then(([hs, src]) => {
  const byId = new Map();
  for (const g of src.groups) {
    for (const it of g.items) byId.set(it.id, { ...it, group: g.name });
  }
  document.getElementById("tbody").innerHTML = hs.timeline
    .map((e) => {
      const ids = e.sourceIds || [];
      const cells = ids.length
        ? ids.map((id) => {
            const s = byId.get(id);
            return s ? `<a href="catalog-c.html">${esc(s.group)}（${esc(s.label)}）→</a>` : esc(id);
          }).join("・")
        : `<span class="c-unmatched">出典なし</span>`;
      const st = ids.length && byId.get(ids[0]) ? byId.get(ids[0]).status : "unverified";
      const v = BADGE[st] || BADGE.unverified;
      return `<tr>
        <td>${esc(e.date)}</td>
        <td>${esc(e.title)}</td>
        <td>${cells}</td>
        <td><span class="badge ${v.cls}">${v.label}</span></td>
      </tr>`;
    })
    .join("");
}).catch((e) => {
  console.error(e);
});
