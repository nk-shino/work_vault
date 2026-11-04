/* ============================================================
   動きの追加層（motion.js）— バニラJS・即時実行・file:// 前提
   既存 js 6本には触れず、フック（data-motion 属性）だけを読んで動く。
   語彙: 1文字リビール / IO出現 / stagger / 行マスク(GSAP)。幕は使わない。

   - 隠し状態は .js-armed 配下。JS が動かなければ何も隠れない（noscript 安全）
   - GSAP は CDN（chara-a のみで読み込み）。window.SplitText をガードし、
     未読時は単純フェードへフォールバック
   - 人物一覧の stagger は初回描画のみ。絞り込みによる再描画後は即時表示
   - prefers-reduced-motion では発火させない（style.css の全般停止に従う）
   ============================================================ */
(() => {
  'use strict';

  const REDUCED = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // 出現の準備（隠し状態）は JS が動くときだけ付ける
  if (!REDUCED) document.documentElement.classList.add('js-armed');

  /* ---------- 共通 ---------- */

  // 最初に画面に入ったら1回だけ呼ぶ（IO 未対応なら即時）
  function onFirstView(el, fn) {
    if (!('IntersectionObserver' in window)) { fn(); return; }
    const io = new IntersectionObserver((entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) { obs.disconnect(); fn(); }
      });
    }, { threshold: 0.2 });
    io.observe(el);
  }

  /* ---------- 1文字リビール（[data-motion~="chars"]） ---------- */

  function setupChars() {
    document.querySelectorAll('[data-motion~="chars"]').forEach((el) => {
      const text = el.textContent;
      const show = () => el.classList.add('m-chars-on');
      if (REDUCED) { show(); return; }

      // 文字を span 化して --index を振る（空白は text node のまま残す）
      el.textContent = '';
      el.setAttribute('aria-label', text);
      [...text].forEach((ch, i) => {
        if (/\s/.test(ch)) {
          el.appendChild(document.createTextNode(ch));
          return;
        }
        const s = document.createElement('span');
        s.className = 'm-char';
        s.setAttribute('aria-hidden', 'true');
        s.style.setProperty('--index', i);
        s.textContent = ch;
        el.appendChild(s);
      });
      onFirstView(el, show);
    });
  }

  /* ---------- セクション出現（[data-motion~="reveal"]・下20%で発火） ---------- */

  function setupReveals() {
    const els = [...document.querySelectorAll('[data-motion~="reveal"]')];
    if (!els.length || REDUCED) return;
    if (!('IntersectionObserver' in window)) {
      els.forEach((el) => el.classList.add('m-on'));
      return;
    }
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('m-on');
        io.unobserve(entry.target);   // 一度出たら観察をやめる
      });
    }, { rootMargin: '0px 0px -20% 0px' });
    els.forEach((el) => io.observe(el));
  }

  /* ---------- stagger（[data-motion~="stagger"]・初回描画のみ） ---------- */

  function setupStagger() {
    document.querySelectorAll('[data-motion~="stagger"]').forEach((grid) => {
      if (REDUCED || !('MutationObserver' in window)) return;
      let played = false;

      // 初回の描画だけ遅れを振って再生。以降の再描画（絞り込み）は即時表示
      const mo = new MutationObserver(() => {
        const cards = [...grid.children].filter((li) => li.classList.contains('card'));
        if (!cards.length) return;
        if (!played) {
          played = true;
          cards.forEach((li, i) => li.style.setProperty('--index', i));
          grid.classList.add('m-stagger');   // CSS側のセレクタ .m-stagger[data-motion-state="first"] が参照する合図
          grid.dataset.motionState = 'first';
          // 再生が終わったら属性を剥がし、以降は何も起きない状態にする
          const lastDelay = (cards.length - 1) * 70 + 600;
          setTimeout(() => { grid.dataset.motionState = 'done'; }, lastDelay + 60);
        } else {
          grid.dataset.motionState = 'done';   // 絞り込み等の再描画は即時
        }
      });
      mo.observe(grid, { childList: true });
    });
  }

  /* ---------- 行マスク（[data-motion~="lines"]・GSAP SplitText／未読時フォールバック） ---------- */

  function setupLineMasks() {
    document.querySelectorAll('[data-motion~="lines"]').forEach((el) => {
      let lines = null;
      let mode = 'fallback';

      // ガード: SplitText が読めなければ（圏外・file:// でCDN不通）単純フェードへ
      try {
        if (window.gsap && window.SplitText) {
          const split = new SplitText(el, { type: 'lines', mask: 'lines' });
          lines = split.lines;
          mode = 'gsap';
        }
      } catch (err) {
        lines = null;
        mode = 'fallback';
      }

      const play = () => {
        if (mode === 'gsap') {
          if (REDUCED) {
            gsap.set(lines, { yPercent: 0 });
            return;
          }
          gsap.fromTo(lines,
            { yPercent: 100 },
            { yPercent: 0, duration: 0.8, ease: 'power3.out', stagger: 0.1, overwrite: true });
        } else {
          el.classList.remove('m-lines-armed');
          el.classList.add('m-lines-fallback');
        }
      };

      if (mode === 'gsap') {
        if (!REDUCED) gsap.set(lines, { yPercent: 100 }); // 行をマスクの下へ
      } else if (!REDUCED) {
        el.classList.add('m-lines-armed');                // opacity: 0 で待つ
      }
      onFirstView(el, play);
    });
  }

  /* ---------- 起動（スクリプトは既存 js の後・DOMは整っている） ---------- */

  setupChars();
  setupReveals();
  setupStagger();
  setupLineMasks();
})();
