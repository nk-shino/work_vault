// 提案ページモック共通スクリプト。外部依存なし。
"use strict";

window.P = (() => {
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  const STATUS = {
    confirmed: { label: "確認済", cls: "ok" },
    supplement: { label: "要補足", cls: "sup" },
    unverified: { label: "未検証", cls: "" },
    none: { label: "出典なし", cls: "none" }
  };
  const badge = (status) => {
    const v = STATUS[status] || STATUS.unverified;
    return `<span class="badge ${v.cls}">${v.label}</span>`;
  };

  const fetchJson = (path) => fetch(path).then((r) => {
    if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
    return r.json();
  });

  // [ANIM-1][ANIM-6] data-reveal の順次出現。兄弟順に遅延 --d を振り、画面内に入ったら .is-in を付ける。
  const reveal = () => {
    const els = [...document.querySelectorAll("[data-reveal]")];
    els.forEach((el) => {
      if (el.dataset.d !== undefined) { el.style.setProperty("--d", `${el.dataset.d * 0.05}s`); return; }
      const sibs = [...el.parentElement.children].filter((c) => c.hasAttribute("data-reveal"));
      el.style.setProperty("--d", `${Math.min(sibs.indexOf(el), 12) * 0.05}s`);
    });
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (e.isIntersecting) { e.target.classList.add("is-in"); io.unobserve(e.target); }
      }
    }, { threshold: 0.08 });
    els.forEach((el) => io.observe(el));
  };

  // [ANIM-7] 数のカウント: data-count の目標値へ 900ms で上げる。reduced-motion では即時に最終値。
  const countUp = () => {
    const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
    const els = [...document.querySelectorAll("[data-count]")];
    const io = new IntersectionObserver((entries) => {
      for (const e of entries) {
        if (!e.isIntersecting) continue;
        io.unobserve(e.target);
        const el = e.target;
        const target = parseInt(el.dataset.count, 10) || 0;
        if (reduced) { el.textContent = target; continue; }
        const t0 = performance.now();
        const tick = (t) => {
          const p = Math.min((t - t0) / 900, 1);
          el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3)));
          if (p < 1) requestAnimationFrame(tick);
        };
        requestAnimationFrame(tick);
      }
    }, { threshold: 0.4 });
    els.forEach((el) => io.observe(el));
  };

  // 色の切替（紙/灯の夜側）。選択は localStorage に置く。
  const theme = () => {
    const btn = document.getElementById("themeToggle");
    if (!btn) return;
    const saved = localStorage.getItem("p-theme");
    if (saved) document.documentElement.dataset.theme = saved;
    else if (matchMedia("(prefers-color-scheme: dark)").matches) document.documentElement.dataset.theme = "dark";
    btn.addEventListener("click", () => {
      const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
      document.documentElement.dataset.theme = next;
      localStorage.setItem("p-theme", next);
    });
  };

  const init = () => { theme(); reveal(); countUp(); };
  document.readyState === "loading" ? document.addEventListener("DOMContentLoaded", init) : init();

  return { esc, badge, fetchJson, reveal, countUp, STATUS };
})();
