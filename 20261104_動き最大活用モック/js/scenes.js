/* ============================================================
   動き最大活用モック — 演出層（scenes.js）
   GSAP（SplitText / ScrollTrigger）と anime.js を使う場面を束ねる。
   すべて try-guard つきで、CDN が読めない環境では静的表示に落ちる。

   縮退: prefers-reduced-motion では何もしない（motion.js が js-armed を
   付けないため、CSS 側の隠し状態も効かない）。
   ============================================================ */
(() => {
  'use strict';

  const C = window.__corridor || {};
  const REDUCED = !!C.REDUCED;
  if (REDUCED) return; // 縮退環境では最大構成を全停止

  const HAS_GSAP = typeof window.gsap !== 'undefined';
  const curtain = C.curtain || null;
  const layers = curtain ? [...curtain.querySelectorAll('.curtain-layer')] : [];
  const mark = curtain ? curtain.querySelector('.curtain-mark') : null;

  if (HAS_GSAP && window.ScrollTrigger) gsap.registerPlugin(ScrollTrigger);
  const HAS_ST = HAS_GSAP && !!window.ScrollTrigger;
  const HAS_SPLIT = HAS_GSAP && !!window.SplitText;
  const HAS_ANIME = typeof window.anime !== 'undefined';

  // motion.js の安全装置（幕が取り残されたら外す）に「起動した」ことを伝える
  if (C && typeof C === 'object') C.scenesBooted = true;

  /* ---------- 幕: 到着時の展開（表紙は閉じた状態から、遷移後は払いの継続） ---------- */
  function curtainReveal(done) {
    if (!curtain || !curtain.classList.contains('is-live')) { if (done) done(); return; }
    if (!HAS_GSAP) {
      curtain.classList.remove('is-live', 'is-hold', 'is-cover');
      if (done) done();
      return;
    }
    gsap.timeline({
      onComplete() {
        curtain.classList.remove('is-live', 'is-hold', 'is-cover');
        if (done) done();
      }
    })
      .to(mark, { autoAlpha: 0, duration: 0.26, ease: 'power2.out' }, 0)
      .to('.curtain-ink', { yPercent: 101, duration: 0.85, ease: 'power4.inOut' }, 0.04)
      .to('.curtain-gold', { yPercent: 101, duration: 0.85, ease: 'power4.inOut' }, 0.04)
      .to('.curtain-crimson', { yPercent: 101, duration: 0.92, ease: 'power4.inOut' }, 0.15);
  }

  /* ---------- 幕: 出発時の筆ワイプ（自作再現・参照メモ2の4C's ad.風） ---------- */
  function wipeNavigate(href) {
    if (!HAS_GSAP || !curtain) { location.href = href; return; }
    if (C.setWipeFlag) C.setWipeFlag();
    // 出発側でも幕を可視化する（is-hold/is-cover は付けない。
    // layers は CSS の translateY(-101%) に待機しており、直後の gsap.set と
    // 同フレーム内で確定するためちらつきはない）
    curtain.classList.add('is-live');
    gsap.timeline({ onComplete() { location.href = href; } })
      .set(layers, { yPercent: -101 })
      .to('.curtain-ink', { yPercent: 0, duration: 0.5, ease: 'power4.inOut' }, 0)
      .to('.curtain-gold', { yPercent: 0, duration: 0.5, ease: 'power4.inOut' }, 0)
      .to('.curtain-crimson', { yPercent: 0, duration: 0.5, ease: 'power4.inOut' }, 0.08)
      .to(mark, { autoAlpha: 1, duration: 0.25, ease: 'power2.out' }, 0.3);
  }

  function armLink(a) {
    a.addEventListener('click', (e) => {
      if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
      e.preventDefault();
      wipeNavigate(a.href);
    });
  }

  function setupNavigation() {
    if (!HAS_GSAP || !curtain) return;
    // 幕で送るリンク（index ↔ 外への動線。chara ↔ detail は View Transitions に譲る）
    document.querySelectorAll('a[data-wipe]').forEach(armLink);
    // cross-document View Transitions 非対応のときは、共有要素遷移の代わりに幕で置換する
    if (C.crossDocVTSupported && C.crossDocVTSupported()) return;
    document.querySelectorAll('#grid a[href="detail.html"]').forEach(armLink);
  }

  // bfcache 復帰でも幕が閉じたままにならないようにする
  addEventListener('pageshow', (e) => {
    if (e.persisted && curtain && curtain.classList.contains('is-live')) curtainReveal();
  });

  /* ---------- SplitText の文字マスクリビール（参照メモ2） ---------- */
  function splitChars(el) {
    if (!el || !HAS_SPLIT) return null;
    try {
      const split = new SplitText(el, { type: 'chars', mask: 'chars' });
      return split.chars;
    } catch (err) { return null; }
  }

  /* ---------- anime.js: 線画（参照メモ5） ---------- */
  function drawStrokes() {
    if (!HAS_ANIME) return;
    document.querySelectorAll('[data-draw]').forEach((svg, idx) => {
      const strokes = svg.querySelectorAll('path, circle');
      if (!strokes.length) return;
      anime({
        targets: strokes,
        strokeDashoffset: [anime.setDashoffset, 0],
        duration: 1600,
        delay: anime.stagger(130, { start: idx * 220 }),
        easing: 'easeInOutQuart'
      });
    });
  }

  /* ---------- anime.js: 数字カウンター（参照メモ5） ---------- */
  function setupCounters() {
    const els = document.querySelectorAll('[data-count]');
    if (!els.length || !HAS_ANIME || !('IntersectionObserver' in window)) return;
    const io = new IntersectionObserver((entries, obs) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        obs.unobserve(entry.target);
        const end = Number(entry.target.getAttribute('data-count')) || 0;
        anime({
          targets: entry.target,
          innerHTML: [0, end],
          round: 1,
          duration: 1500,
          easing: 'easeOutExpo'
        });
      });
    }, { threshold: 0.5 });
    els.forEach((el) => io.observe(el));
  }

  /* ---------- 表紙（index）: ヒーローと「序」のスクロール語り ---------- */
  let homeChars = null;
  let homeFades = [];

  function prepHome() {
    if (!HAS_GSAP) return; // CDN 不達時は隠し処理自体を行わない（全要素可視・幕は curtainReveal が払う）
    const h1 = document.querySelector('[data-hero-title]');
    homeChars = splitChars(h1);
    if (homeChars) gsap.set(homeChars, { yPercent: 118 });
    homeFades = [...document.querySelectorAll('[data-hero-fade]')];
    if (homeFades.length) gsap.set(homeFades, { autoAlpha: 0, y: 18 });
  }

  function playHome() {
    if (homeChars) gsap.to(homeChars, { yPercent: 0, duration: 1.05, ease: 'expo.out', stagger: 0.05, delay: 0.05 });
    if (homeFades.length) gsap.to(homeFades, { autoAlpha: 1, y: 0, duration: 0.9, ease: 'expo.out', stagger: 0.14, delay: 0.4 });
    drawStrokes();
  }

  function setupStoryPin() {
    const story = document.querySelector('[data-story]');
    if (!story || !HAS_ST) return;
    const text = story.querySelector('[data-story-text]');
    if (!text || !HAS_SPLIT) return;
    try {
      const lines = new SplitText(text, { type: 'lines', mask: 'lines' }).lines;
      gsap.timeline({
        scrollTrigger: { trigger: story, start: 'top top', end: '+=150%', scrub: 0.6, pin: true }
      })
        .from(lines, { yPercent: 130, duration: 1, ease: 'power3.out', stagger: 0.4 })
        .to({}, { duration: 0.8 }); // 語りを留める駐留
    } catch (err) { /* split に失敗したら固定も語りも外す（本文は見えるまま） */ }
  }

  /* ---------- 人物一覧（chara）: 端から広がる stagger（参照メモ6） ---------- */
  function prepChara() {
    if (!HAS_GSAP) return; // CDN 不達時は隠し処理自体を行わない（全要素可視・幕は curtainReveal が払う）
    const h1 = document.querySelector('[data-hero-title]');
    const chars = splitChars(h1);
    if (chars) gsap.set(chars, { yPercent: 118 });
    const tools = document.querySelector('.toolbar');
    if (tools) gsap.set(tools, { autoAlpha: 0, y: 14 });
    const cells = document.querySelectorAll('#grid .cell');
    if (cells.length) gsap.set(cells, { autoAlpha: 0, y: 36 }); // 幕の裏で待たせる
    return { chars, cells };
  }

  function playChara(prep) {
    if (!prep) return; // prepChara がガードで早期 return した場合
    if (prep.chars) gsap.to(prep.chars, { yPercent: 0, duration: 0.9, ease: 'expo.out', stagger: 0.06 });
    const tools = document.querySelector('.toolbar');
    if (tools) gsap.to(tools, { autoAlpha: 1, y: 0, duration: 0.8, ease: 'expo.out', delay: 0.2 });
    if (prep.cells.length) {
      gsap.to(prep.cells, {
        autoAlpha: 1, y: 0, duration: 1.0, ease: 'power4.out', delay: 0.22,
        stagger: { each: 0.055, from: 'edges', grid: 'auto' }
      });
    }
  }

  /* ---------- 記録見本（detail）: ヒーローと追従出現 ---------- */
  function prepRecord() {
    if (!HAS_GSAP) return; // CDN 不達時は隠し処理自体を行わない（全要素可視・幕は curtainReveal が払う）
    const h1 = document.querySelector('[data-hero-title]');
    const chars = splitChars(h1);
    if (chars) gsap.set(chars, { yPercent: 118 });
    const fades = [...document.querySelectorAll('[data-hero-fade]')];
    if (fades.length) gsap.set(fades, { autoAlpha: 0, y: 18 });
    return { chars, fades };
  }

  function playRecord(prep) {
    if (!prep) return; // prepRecord がガードで早期 return した場合
    if (prep.chars) gsap.to(prep.chars, { yPercent: 0, duration: 1.0, ease: 'expo.out', stagger: 0.045 });
    if (prep.fades.length) gsap.to(prep.fades, { autoAlpha: 1, y: 0, duration: 0.9, ease: 'expo.out', stagger: 0.12, delay: 0.3 });
    drawStrokes();
  }

  function setupRecordScroll() {
    if (!HAS_ST) return;
    gsap.utils.toArray('[data-reveal]').forEach((el) => {
      gsap.from(el, {
        autoAlpha: 0, y: 30, duration: 0.9, ease: 'expo.out',
        scrollTrigger: { trigger: el, start: 'top 86%', once: true }
      });
    });
  }

  /* ---------- 起動（スクリプトは body 末尾・DOM 完成後） ---------- */
  const page = document.body.dataset.page || '';

  if (page === 'home') {
    prepHome();
    setupStoryPin();
    setupCounters();
    curtainReveal(playHome);
  } else if (page === 'chara') {
    const prep = prepChara();
    curtainReveal(() => playChara(prep));
  } else if (page === 'record') {
    const prep = prepRecord();
    setupRecordScroll();
    curtainReveal(() => playRecord(prep));
  } else {
    curtainReveal();
  }

  setupNavigation();
})();
