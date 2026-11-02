
"use strict";

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

Promise.all([
  fetch("data/history.json").then((r) => r.json()),
  fetch("data/works.json").then((r) => r.json()),
]).then(([hs, wk]) => {
  const works = new Map(wk.works.map((w) => [w.id, w]));
  document.getElementById("empty").hidden = true;
  document.getElementById("list").hidden = false;
  document.getElementById("line").textContent = `催事0件。代わりに出来事の記録 ${hs.timeline.length} 件を出している。`;
  document.getElementById("tbody").innerHTML = hs.timeline
    .map((e) => {
      const w = works.get(e.workId);
      const wlabel = w ? esc(w.title.replace(/[「」]/g, "").replace(/^第(.+)楽曲/, "第$1曲")) + " →" : "—";
      return `<tr>
        <td>${esc(e.date)}</td>
        <td>${esc(e.title)}</td>
        <td>${w ? `<a href="catalog-b.html">${wlabel}</a>` : "—"}</td>
      </tr>`;
    })
    .join("");
}).catch((e) => {
  console.error(e);
  document.getElementById("line").textContent = "データを読み込めない。data/ の配置を確認。";
});
