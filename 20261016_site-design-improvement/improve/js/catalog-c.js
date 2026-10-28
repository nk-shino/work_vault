// 方向C 目録棚: 検証列を押すと照合の内訳が開く。日付なし出典は「日付なし」と明示。
"use strict";

const tbody = document.getElementById("tbody");
const empty = document.getElementById("empty");
const line = document.getElementById("result-line");
const q = document.getElementById("q");
const chips = Array.from(document.querySelectorAll(".chip[data-kind]"));
let rows = [];
let claims = [];
const openSet = new Set();
// 照合の内訳を行を開くたびに探さないですむよう、読み込み後に題核ごとに計算して置く
let claimByCore = new Map();

const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// VERIFY は js/verify.js の共通定義（C-2）を使う

const norm = (s) => String(s).replace(/[「」]/g, "").trim();
const coreOf = (title) => norm(title).replace(/(公開|発売)$/, "").trim();

// make-catalog.js と同じ照合の再現（表示用）: 内訳を可視化するため。
// 当たり判定は claimByCore に事前計算した結果を使う（探索の順序は元のまま）
function traceFor(r) {
  if (r.kind !== "出来事") {
    return `<dd>この種別は自動照合の対象外（本家 §6-4 と同じ）。${r.verify === "confirmed" ? "出典側の status が confirmed。" : "未照合のまま表示。"}</dd>`;
  }
  const hit = claimByCore.get(coreOf(r.title));
  if (!hit || !hit.any) {
    return `<dd>①日付あり出典: 当たらず → ②日付なし出典: 当たらず → <strong>未照合</strong>。題核「${esc(coreOf(r.title))}」に一致する出典labelが無い。</dd>`;
  }
  const via = hit.dated ? "日付あり出典" : "日付なし出典（日付の欄は「日付なし」と出す）";
  return `<dd>①${via}「${esc(hit.any.label)}」（${esc(hit.any.id)}・status=${esc(hit.any.status)}）に当たった。</dd>`;
}

function render(list) {
  empty.hidden = list.length > 0;
  tbody.innerHTML = list
    .map((r) => {
      const v = VERIFY[r.verify] || VERIFY.unverified;
      const isOpen = openSet.has(r.id);
      const trace = isOpen ? `<tr><td colspan="5" style="background:var(--bg-sink);">${traceFor(r)}</td></tr>` : "";
      return `<tr>
        <td>${esc(r.id)}</td>
        <td>${esc(r.kind)}</td>
        <td>${esc(r.title)}</td>
        <td>${r.date ? esc(r.date) : "—"}</td>
        <td><button class="chip" aria-expanded="${isOpen}" data-id="${esc(r.id)}"><span class="badge ${v.cls}">${v.label}</span></button></td>
      </tr>${trace}`;
    })
    .join("");
  line.textContent = list.length ? `${list.length}項を表示中。` : "0項。";
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

tbody.addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-id]");
  if (!btn) return;
  const id = btn.dataset.id;
  if (openSet.has(id)) openSet.delete(id);
  else openSet.add(id);
  apply();
});

Promise.all([
  fetch("data/catalog.json").then((r) => r.json()),
  fetch("data/sources.json").then((r) => r.json()),
]).then(([cat, src]) => {
  rows = cat.catalog;
  for (const g of src.groups) for (const it of g.items) claims.push(it);
  for (const r of rows) {
    if (r.kind !== "出来事") continue;
    const core = coreOf(r.title);
    const dated = claims.find((s) => s.date !== "no date" && norm(s.label).includes(core));
    claimByCore.set(core, { core, dated, any: dated || claims.find((s) => norm(s.label).includes(core)) });
  }
  apply();
}).catch((e) => {
  console.error(e);
  line.textContent = "データを読み込めない。data/ の配置を確認（0件とは別の状態）。";
});

chips.forEach((b) =>
  b.addEventListener("click", () => {
    chips.forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    apply();
  })
);
let qTimer;
q.addEventListener("input", () => {
  clearTimeout(qTimer);
  qTimer = setTimeout(apply, 80);
});

document.getElementById("reset").addEventListener("click", (e) => {
  e.preventDefault();
  q.value = "";
  chips.forEach((x) => x.setAttribute("aria-pressed", String(x.dataset.kind === "all")));
  apply();
});
