/* ============================================================
   動き最大活用モック — 共通層（motion.js・vanilla・ライブラリ非依存）
   担当: js-armed の管理 / 幕の状態 / カスタムカーソル / マグネティック /
   スポットライト座標 / 人物絞り込み / View Transitions の対応検出
   GSAP・anime.js を使う演出は scenes.js が担当する。
   ============================================================ */
(() => {
  'use strict';

  const REDUCED = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const FINE = window.matchMedia &&
    window.matchMedia('(pointer: fine)').matches;

  // 出現まちの隠し状態は JS が動くときだけ付ける（noscript では全要素表示）
  if (!REDUCED) document.documentElement.classList.add('js-armed');

  /* ---------- 幕の状態管理（演出は scenes.js） ---------- */
  const curtain = document.querySelector('[data-curtain]');
  const WIPE_FLAG = 'corridor-wipe-at';

  function readWipeFlag() {
    try {
      const t = Number(sessionStorage.getItem(WIPE_FLAG) || 0);
      return t > 0 && (Date.now() - t) < 4000;
    } catch (e) { return false; }
  }
  function clearWipeFlag() {
    try { sessionStorage.removeItem(WIPE_FLAG); } catch (e) { /* ない環境はそのまま */ }
  }

  if (curtain) {
    if (REDUCED) {
      curtain.classList.remove('is-live', 'is-hold', 'is-cover');
    } else {
      const viaWipe = readWipeFlag();
      const hold = document.body.dataset.curtainHold === '1';
      if (hold || viaWipe) {
        curtain.classList.add('is-live');
        curtain.classList.add(hold ? 'is-hold' : 'is-cover');
      }
      if (viaWipe) clearWipeFlag();
      // scenes.js が動かない環境で幕が取り残されない安全装置
      setTimeout(() => {
        if (!(window.__corridor && window.__corridor.scenesBooted)) {
          curtain.classList.remove('is-live', 'is-hold', 'is-cover');
        }
      }, 1600);
    }
  }

  // scenes.js へ渡す共通ハンドル
  window.__corridor = {
    REDUCED,
    curtain,
    setWipeFlag() {
      try { sessionStorage.setItem(WIPE_FLAG, String(Date.now())); } catch (e) { /* ない環境はそのまま */ }
    },
    // cross-document View Transitions の対応検出（@view-transition 規則が CSSOM に載るか）
    crossDocVTSupported() {
      if (!window.CSSViewTransitionRule) return false;
      try {
        for (const sheet of [...document.styleSheets]) {
          let rules;
          try { rules = sheet.cssRules; } catch (e) { continue; }
          for (const rule of [...rules]) {
            if (rule instanceof CSSViewTransitionRule) return true;
          }
        }
      } catch (e) { /* 読めない式様書は無視 */ }
      return false;
    },
  };

  /* ---------- VT の円形リビール原点（未検討ギャップ #8） ---------- */
  // cross-document View Transitions では遷移元の CSS 変数が遷移先へ伝わらない。
  // そのためカードクリックの座標を sessionStorage で受け渡し、到着側の :root に
  // --vt-x / --vt-y として設定する（未記録なら css/vt.css 側で中央にフォールバック）。
  const VT_ORIGIN = 'corridor-vt-origin';

  function restoreVtOrigin() {
    try {
      const raw = sessionStorage.getItem(VT_ORIGIN);
      if (!raw) return;
      sessionStorage.removeItem(VT_ORIGIN);
      const o = JSON.parse(raw);
      if (o && Number.isFinite(o.x) && Number.isFinite(o.y) && Date.now() - (o.t || 0) < 4000) {
        document.documentElement.style.setProperty('--vt-x', `${Math.round(o.x)}px`);
        document.documentElement.style.setProperty('--vt-y', `${Math.round(o.y)}px`);
      }
    } catch (e) { /* ない環境・壊れた値は中央フォールバック */ }
  }

  // VT 対応環境（CSSViewTransitionRule がある）のカードクリックだけが記録する。
  // 非対応環境の筆ワイプ経路には影響しない
  function setupVtOrigin() {
    if (!window.CSSViewTransitionRule) return;
    const grid = document.getElementById('grid');
    if (!grid) return;
    grid.querySelectorAll('a[href="detail.html"]').forEach((a) => {
      a.addEventListener('click', (e) => {
        if (e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
        document.documentElement.style.setProperty('--vt-x', `${e.clientX}px`);
        document.documentElement.style.setProperty('--vt-y', `${e.clientY}px`);
        try {
          sessionStorage.setItem(VT_ORIGIN, JSON.stringify({ x: e.clientX, y: e.clientY, t: Date.now() }));
        } catch (err) { /* ない環境は中央フォールバック */ }
      });
    });
  }

  /* ---------- カスタムカーソル（Cursor Gallery 系の自作・参照メモ7） ---------- */
  function setupCursor() {
    if (REDUCED || !FINE) return;
    const root = document.querySelector('[data-cursor-el]');
    if (!root) return;
    document.documentElement.classList.add('cursor-on');

    const dot = root.querySelector('.cursor-dot');
    const ring = root.querySelector('.cursor-ring');
    const label = root.querySelector('.cursor-label');
    let mx = innerWidth / 2, my = innerHeight / 2;
    let rx = mx, ry = my, rvx = 0, rvy = 0, seen = false;

    addEventListener('mousemove', (e) => {
      mx = e.clientX; my = e.clientY;
      if (!seen) { seen = true; rx = mx; ry = my; rvx = 0; rvy = 0; root.classList.add('is-on'); }
      dot.style.transform = `translate3d(${mx}px, ${my}px, 0)`;
    }, { passive: true });

    // ring は rAF の spring 積分で追従する（React Spring の物理イージング概念の
    // vanilla 再現・コード非転載・依存追加なし）。臨界減衰 2*sqrt(K)≈26.1 に対し
    // 僅かにアンダーダンプ（DAMP=22・ζ≈0.84）で小さな行き過ぎを作り、生きた手応えにする。
    // dot は即時のまま。dt はタブ復帰時の跳ね防止のため上限で切る。
    const K = 170;    // ばね定数
    const DAMP = 22;  // 減衰係数
    let last = performance.now();
    function loop(now) {
      const dt = Math.min((now - last) / 1000, 1 / 30);
      last = now;
      const ax = -K * (rx - mx) - DAMP * rvx;
      const ay = -K * (ry - my) - DAMP * rvy;
      rvx += ax * dt;
      rvy += ay * dt;
      rx += rvx * dt;
      ry += rvy * dt;
      ring.style.transform = `translate3d(${rx}px, ${ry}px, 0)`;
      requestAnimationFrame(loop);
    }
    requestAnimationFrame(loop);

    addEventListener('mouseover', (e) => {
      const view = e.target.closest('[data-cursor]');
      const link = e.target.closest('a, button, [data-cursor]');
      root.classList.toggle('is-view', !!view);
      root.classList.toggle('is-link', !!link);
      label.textContent = view ? (view.getAttribute('data-cursor') || '') : '';
    }, { passive: true });
  }

  /* ---------- マグネティック hover（参照メモ7） ---------- */
  function setupMagnetic() {
    if (REDUCED || !FINE) return;
    document.querySelectorAll('[data-magnet]').forEach((el) => {
      const strength = Number(el.getAttribute('data-magnet')) || 0.26;
      el.addEventListener('mousemove', (e) => {
        const r = el.getBoundingClientRect();
        const dx = (e.clientX - (r.left + r.width / 2)) * strength;
        const dy = (e.clientY - (r.top + r.height / 2)) * strength;
        el.style.transform = `translate(${dx}px, ${dy}px)`;
      });
      el.addEventListener('mouseleave', () => { el.style.transform = ''; });
    });
  }

  /* ---------- スポットライトの座標（Aceternity パターンの vanilla 移植） ---------- */
  function setupSpotlight() {
    if (REDUCED) return;
    document.querySelectorAll('.card, .work-row').forEach((el) => {
      el.addEventListener('mousemove', (e) => {
        const r = el.getBoundingClientRect();
        el.style.setProperty('--mx', `${e.clientX - r.left}px`);
        el.style.setProperty('--my', `${e.clientY - r.top}px`);
      }, { passive: true });
    });
  }

  /* ---------- 人物一覧の絞り込み（既存 site と同じ実データのチップ） ---------- */
  function setupCharaFilter() {
    const grid = document.getElementById('grid');
    if (!grid) return;
    const chips = [...document.querySelectorAll('.chip[data-aff]')];
    if (!chips.length) return;
    const cells = [...grid.querySelectorAll('.cell')];
    const line = document.getElementById('result-line');

    const apply = (aff) => {
      let shown = 0;
      cells.forEach((cell) => {
        const card = cell.querySelector('[data-aff]');
        const show = aff === 'all' || (card && card.getAttribute('data-aff') === aff);
        cell.hidden = !show;
        if (show) shown += 1;
      });
      chips.forEach((b) => {
        b.setAttribute('aria-pressed', String(b.getAttribute('data-aff') === aff));
      });
      if (line) line.textContent = `${shown}人を表示中。`;
    };

    chips.forEach((b) => b.addEventListener('click', () => apply(b.getAttribute('data-aff'))));
  }

  /* ---------- 起動 ---------- */
  restoreVtOrigin();
  setupVtOrigin();
  setupCursor();
  setupMagnetic();
  setupSpotlight();
  setupCharaFilter();
})();
