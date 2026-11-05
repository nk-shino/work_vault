/* ============================================================
   回廊の記録 — 動き案C「文字の語り」: 演出層（scenes.js）
   GSAP 3.13.0（SplitText / ScrollTrigger）と anime.js 3.2.2 を使う。
   文字の立ち上がり・13枚の stagger random・行の追従・カウンターを
   束ねる。MIT ライセンスの CDN 固定バージョンのみ。

   縮退:
   - prefers-reduced-motion では何もしない（motion.js の判定を
     受け取り、自前でも再確認する）
   - CDN が読めない環境では何も隠さず静的表示のまま
     （GSAP なし → 何もしない。ScrollTrigger なし → 行を隠さない）
   - 個々の処理は try-catch で包み、失敗しても可視のままにする
   ============================================================ */
(() => {
  'use strict';

  const REDUCED = !!(window.__corridor && window.__corridor.REDUCED) ||
    (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  if (REDUCED) return; // 縮退環境では文字の語りを全停止

  const HAS_GSAP = typeof window.gsap !== 'undefined';
  if (!HAS_GSAP) return; // 文字の語りは GSAP 前提。無ければ何もしない（全要素表示）

  const HAS_ST = !!window.ScrollTrigger;
  const HAS_SPLIT = !!window.SplitText;
  const HAS_ANIME = typeof window.anime !== 'undefined';
  if (HAS_ST) gsap.registerPlugin(ScrollTrigger);

  /* ---------- 文字リビール: 右から左へ（mask: chars・out-back） ---------- */
  /* 最大案とは逆方向（from: 'end'）。微オーバーシュートで跳ねさせる。 */
  function charsReveal(el, delay) {
    if (!el || !HAS_SPLIT) return;
    try {
      const full = el.textContent;
      const split = new SplitText(el, { type: 'chars', mask: 'chars' });
      el.setAttribute('aria-label', full); // 元文を読み上げへ退避
      gsap.from(split.chars, {
        yPercent: 118,
        duration: 0.55,
        ease: 'back.out(1.7)', // 微オーバーシュート
        stagger: { each: 0.042, from: 'end' }, // 右 → 左
        delay: delay || 0
      });
    } catch (err) { /* 分割に失敗したら元のまま（可視） */ }
  }

  /* ---------- フェード（out-expo） ---------- */
  function fadeIn(els, delay, stagger) {
    const list = Array.prototype.slice.call(els || []);
    if (!list.length) return;
    try {
      gsap.from(list, {
        autoAlpha: 0, y: 16,
        duration: 0.55, ease: 'expo.out',
        stagger: stagger || 0.1, delay: delay || 0
      });
    } catch (err) { /* 何もしない（可視のまま） */ }
  }

  /* ---------- 13枚: stagger random（不採用#16の再検討・初回のみ） ---------- */
  /* 読み込みの一度だけ random 順で立ち上げる。絞り込みの再描画は
     動かさず即時表示（本番候補の挙動に合わせる）。
     grid: 'auto' は付けない — グリッド近傍順が優先されて random の散らばりが
     宣言値の 1/3（実測 spread 167ms）に縮むため、from: 'random' だけで並べる */
  function playGridRandom() {
    const cells = gsap.utils.toArray('#grid > li');
    if (!cells.length) return;
    try {
      gsap.from(cells, {
        autoAlpha: 0, y: 26,
        duration: 0.55, ease: 'back.out(1.6)',
        stagger: { each: 0.042, from: 'random' },
        delay: 0.3
      });
    } catch (err) { /* 何もしない（可視のまま） */ }
  }

  /* ---------- 行の追従出現（ScrollTrigger batch・once・out-expo） ---------- */
  function setupRows() {
    if (!HAS_ST) return; // 隠さないので CDN 不達でも崩れない
    const rows = gsap.utils.toArray('[data-row]');
    if (!rows.length) return;
    try {
      gsap.set(rows, { autoAlpha: 0, y: 22 });
      ScrollTrigger.batch(rows, {
        start: 'top 88%',
        once: true,
        onEnter: (batch) => gsap.to(batch, {
          autoAlpha: 1, y: 0,
          duration: 0.5, ease: 'expo.out',
          stagger: 0.04, overwrite: true
        })
      });
    } catch (err) {
      gsap.set(rows, { clearProps: 'all' }); // 失敗時は全表示へ倒す
    }
  }

  /* ---------- 数字カウンター強調版（anime.js・in-out-quart） ---------- */
  function setupCounters() {
    if (!HAS_ANIME || !('IntersectionObserver' in window)) return;
    const els = Array.prototype.slice.call(document.querySelectorAll('[data-count]'));
    if (!els.length) return;
    const io = new IntersectionObserver((entries, obs) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        obs.unobserve(entry.target);
        const el = entry.target;
        const end = Number(el.getAttribute('data-count')) || 0;
        try {
          anime({
            targets: el,
            innerHTML: [0, end],
            round: 1,
            duration: 1200,
            easing: 'easeInOutQuart'
          });
        } catch (err) { /* 初期値＝完成値のまま */ }
      });
    }, { rootMargin: '0px 0px -25% 0px', threshold: 0 });
    els.forEach((el) => {
      const end = Number(el.getAttribute('data-count')) || 0;
      // 演出中の数字は見た目のみ。読み上げ値は完成値を退避しておく
      const sr = document.createElement('span');
      sr.className = 'visually-hidden';
      sr.textContent = String(end);
      el.setAttribute('aria-hidden', 'true');
      el.insertAdjacentElement('afterend', sr);
      io.observe(el);
    });
  }

  /* ---------- ページ別の段取り ---------- */
  const page = document.body.getAttribute('data-page');

  function qa(sel) { return Array.prototype.slice.call(document.querySelectorAll(sel)); }

  if (page === 'home') {
    fadeIn(qa('.front-eyebrow, .front-lead, .front-cue'), 0.15, 0.12);
    charsReveal(document.querySelector('.front-title'), 0.35);
    setupRows(); // 数字帯の見出し（data-row）
    setupCounters();
  } else if (page === 'chara') {
    charsReveal(document.querySelector('.page-title'), 0.15);
    fadeIn(qa('.page-head .lead'), 0.55);
    playGridRandom();
  } else if (page === 'record') {
    fadeIn(qa('.record-plate, .record-id, .record-role, .record-appearance'), 0.1, 0.12);
    charsReveal(document.querySelector('.record-title'), 0.3);
    setupRows();
  }
})();
