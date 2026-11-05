/* ============================================================
   回廊の記録 — 動き案A「静謐紙」: 制御層（motion.js）
   バニラ JS のみ・依存ゼロ。外部リクエストは発生しない。

   担当:
   - js-armed の管理（reduce・IO未対応では付けない＝何も隠れない）
   - IO出現（fade + rise のみ・一回きり・発火線は画面下30%）
   - 数字カウンター（バニラ rAF・data 属性の数値・cubic-out —
     数値の可読性のため出現の out-quint から例外的に分離）
   - typewriter（index のリード1箇所・caret 点滅つき）
   - 所属絞り込み（aria-pressed・aria-live・reduced-motion でも機能）

   縮退: prefers-reduced-motion では js-armed を付けず、
   typewriter も出現まちも行わない（CSS 側の二重安全と重ねがけ）。
   ============================================================ */
(() => {
  'use strict';

  const REDUCED = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // 絞り込みは動きの層に依存しない（reduced-motion でも機能させる）
  setupFilter();

  if (REDUCED || !('IntersectionObserver' in window)) return;
  document.documentElement.classList.add('js-armed');

  try { setupReveal(); } catch (err) {
    // 出現まちに失敗したら全表示へ倒す
    document.querySelectorAll('[data-reveal]').forEach((el) => el.classList.add('is-in'));
  }
  try { setupCounters(); } catch (err) { /* 初期値＝完成値のまま */ }
  try { setupTypewriter(); } catch (err) { /* 初期値＝完成文のまま */ }

  /* ---------- 所属絞り込み（チップ aria-pressed・結果行 aria-live） ---------- */
  function setupFilter() {
    const grid = document.getElementById('grid');
    const chips = [...document.querySelectorAll('.chip[data-aff]')];
    const line = document.getElementById('result-line');
    if (!grid || !chips.length || !line) return;
    const cells = [...grid.querySelectorAll('li[data-aff]')];
    chips.forEach((chip) => {
      chip.addEventListener('click', () => {
        const aff = chip.getAttribute('data-aff');
        chips.forEach((c) => c.setAttribute('aria-pressed', String(c === chip)));
        let shown = 0;
        cells.forEach((cell) => {
          const hit = aff === 'all' || cell.getAttribute('data-aff') === aff;
          cell.hidden = !hit;
          if (hit) shown += 1;
        });
        line.textContent = shown + '人を表示中。';
      });
    });
  }

  /* ---------- IO出現: fade + rise のみ・一回きり・発火線は画面下30% ---------- */
  function setupReveal() {
    // 段差（stagger 125ms）の割り当て:
    // data-reveal-seq は並び順どおり 0,1,2…（表紙・数字帯・記録の頭）。
    // 一覧（13枚）は要素別の IO 発火に任せ、行の割り当て機構は持たない
    //（行単位の --i は行高が発火線をまたぐと待ち時間が実効的に無効化されるため廃止）
    document.querySelectorAll('[data-reveal-seq]').forEach((group) => {
      [...group.querySelectorAll(':scope > [data-reveal]')].forEach((el, i) => {
        el.style.setProperty('--i', String(i));
      });
    });

    const io = new IntersectionObserver((entries, obs) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-in');
        obs.unobserve(entry.target); // 一回きり
      });
    }, { rootMargin: '0px 0px -30% 0px', threshold: 0 });
    document.querySelectorAll('[data-reveal]').forEach((el) => io.observe(el));
  }

  /* ---------- 数字カウンター: バニラ rAF・cubic-out・data 属性から ---------- */
  function setupCounters() {
    const els = [...document.querySelectorAll('[data-count]')];
    if (!els.length) return;
    els.forEach((el) => {
      const end = Number(el.getAttribute('data-count'));
      if (!Number.isFinite(end)) return;
      // 演出中の数字は見た目のみ。読み上げ値は完成値を退避しておく
      const sr = document.createElement('span');
      sr.className = 'visually-hidden';
      sr.textContent = String(end);
      el.setAttribute('aria-hidden', 'true');
      el.insertAdjacentElement('afterend', sr);
    });
    const io = new IntersectionObserver((entries, obs) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        obs.unobserve(entry.target);
        runCount(entry.target);
      });
    }, { rootMargin: '0px 0px -30% 0px', threshold: 0 });
    els.forEach((el) => io.observe(el));
  }

  function runCount(el) {
    const end = Number(el.getAttribute('data-count')) || 0;
    const DURATION = 1150; // ms — 0.9〜1.2秒の帯の中段
    const start = performance.now();
    const tick = (now) => {
      const t = Math.min((now - start) / DURATION, 1);
      // out-quint では最終 15% の到達に曲線の後半をすべて使うため、
      // 完走後も数値が目標の約半分の位置に留まる（実測）。数値の可読性を
      // 優先し、この箇所のみ cubic-out に例外的に分離する
      const eased = 1 - Math.pow(1 - t, 3); // cubic-out
      el.textContent = String(Math.round(end * eased));
      if (t < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  /* ---------- typewriter: index のリード1箇所・caret 点滅つき ---------- */
  /* JS 無効・reduced-motion では実行されず、完成文がそのまま見える。 */
  function setupTypewriter() {
    const el = document.querySelector('[data-tw]');
    if (!el) return;
    const full = (el.textContent || '').trim();
    if (!full) return;
    try {
      // 完成文は aria-label と sr-only の両方に退避（視覚は 1 字ずつ）
      el.setAttribute('aria-label', full);
      el.textContent = '';
      const sr = document.createElement('span');
      sr.className = 'visually-hidden';
      sr.textContent = full;
      const text = document.createElement('span');
      text.className = 'tw-text';
      text.setAttribute('aria-hidden', 'true');
      const caret = document.createElement('span');
      caret.className = 'tw-caret';
      caret.setAttribute('aria-hidden', 'true');
      el.append(sr, text, caret);
      el.classList.add('tw-on');
      const SPEED = 46; // ms / 1字
      let i = 0;
      const step = () => {
        i += 1;
        text.textContent = full.slice(0, i);
        if (i < full.length) window.setTimeout(step, SPEED);
      };
      window.setTimeout(step, 700); // 表紙の立ち上がりに合わせて置く
    } catch (err) {
      el.textContent = full; // 失敗時は完成文をそのまま
      el.classList.add('tw-on');
    }
  }
})();
