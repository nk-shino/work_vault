// 方向C HOME: sources/history/catalog を読み、記録の現状を実数で出す。
"use strict";

fetch("data/sources.json")
  .then((r) => r.json())
  .then((d) => {
    const items = d.groups.flatMap((g) => g.items);
    const by = {};
    for (const it of items) by[it.status] = (by[it.status] || 0) + 1;
    document.getElementById("n-confirmed").textContent = by.confirmed || 0;
    document.getElementById("n-supplement").textContent = by.supplement || 0;
    document.getElementById("n-unverified").textContent = by.unverified || 0;
    document.getElementById("n-none").textContent = by.none || 0;
    document.getElementById("n-nodate").textContent = items.filter((i) => i.date === "no date").length;
  })
  .catch((e) => {
    console.error(e);
  });

Promise.all([
  fetch("data/history.json").then((r) => r.json()),
  fetch("data/catalog.json").then((r) => r.json()),
]).then(([hs, cat]) => {
  const byRef = new Map(cat.catalog.map((r) => [r.ref, r]));
  const matched = hs.timeline.filter((e) => {
    const c = byRef.get(e.id);
    return c && c.verify === "confirmed";
  }).length;
  document.getElementById("n-matched").textContent = matched;
}).catch((e) => {
  console.error(e);
});
