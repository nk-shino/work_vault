
"use strict";

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const li = (arr) => arr.length ? `<ul class="b-links">${arr.join("")}</ul>` : `<span style="color:var(--text-sub); font-size:12px;">—</span>`;

Promise.all([
  fetch("data/works.json").then((r) => r.json()),
  fetch("data/characters.json").then((r) => r.json()),
  fetch("data/glossary.json").then((r) => r.json()),
  fetch("data/history.json").then((r) => r.json()),
  fetch("data/series.json").then((r) => r.json()),
]).then(([wk, ch, gl, hs, se]) => {
  const w = wk.works.find((x) => x.id === "w001");
  document.getElementById("chars").innerHTML = li(
    (w.characters || []).map((cid) => {
      const c = ch.characters.find((x) => x.id === cid);
      return c ? `<li><a href="chara-b.html">${esc(c.name)} →</a></li>` : "";
    })
  );
  const terms = gl.glossary.filter((g) => g.workId === "w001");
  document.getElementById("terms").innerHTML = li(
    terms.map((g) => `<li><a href="catalog-b.html">${esc(g.term)}（${esc(g.reading)}）→</a></li>`)
  );
  const evs = hs.timeline.filter((e) => e.workId === "w001");
  document.getElementById("events").innerHTML = li(
    evs.map((e) => `<li><a href="events-b.html">${esc(e.date)} ${esc(e.title)} →</a></li>`)
  );
  const sr = se.series.find((s) => s.workIds.includes("w001"));
  document.getElementById("series").innerHTML = li(
    sr ? sr.workIds.filter((id) => id !== "w001").slice(0, 4).map((id) => {
      const x = wk.works.find((y) => y.id === id);
      return x ? `<li><a href="catalog-b.html">${esc(x.title.replace(/[「」]/g, "").replace(/^第(.+)楽曲/, "第$1曲"))} →</a></li>` : "";
    }) : []
  );
}).catch((e) => {
  console.error(e);
});
