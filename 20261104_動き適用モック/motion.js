/* ============================================================
   回廊の記録 — 動き適用モック 共通駆動（バニラJS・即時実行）
   前回モック（20261104_動きコード併記モック）の6語彙を各ページへ割り当てる:
   curtain（表紙のみ）/ 1文字リビール / 行マスク(GSAP) / IO出現 / stagger / 控えめhover(CSSのみ)

   - file:// で動く（fetch 不使用・モジュール不使用）
   - GSAP は CDN（jsDelivr）。window.SplitText をガードし、未読時は単純フェードへ
   - noscript: 隠し状態は .js-armed 配下なので、JS が動かなければ全要素が見えたまま
   ============================================================ */
(() => {
  'use strict';

  const REDUCED = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // 出現の準備（隠し状態）は JS が動くときだけ付ける。
  // reduced motion のときは付けても即時に表示されるので、最初から付けない。
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

  /* ---------- 1. 読み込み幕（表紙のみ・#curtain-page） ---------- */

  function setupCurtain() {
    const veil = document.getElementById('curtain-page');
    if (!veil) return;
    const open = () => veil.classList.add('is-open');
    if (REDUCED) {
      open();
    } else {
      // 二重 rAF: 初期スタイルの適用を待ってから開ける
      requestAnimationFrame(() => requestAnimationFrame(open));
    }
    const done = () => { if (veil.parentNode) veil.parentNode.removeChild(veil); };
    veil.addEventListener('transitionend', (e) => {
      if (e.target === veil && e.propertyName === 'transform') done();
    });
    setTimeout(done, 1600); // transition が発火しない環境の念押し
  }

  /* ---------- 2. 見出しの1文字リビール（.char-wrap > .char-target） ---------- */

  function setupCharReveals() {
    document.querySelectorAll('.char-wrap').forEach((wrap) => {
      const target = wrap.querySelector('.char-target');
      if (!target) return;
      const show = () => wrap.classList.add('is-shown');
      if (REDUCED) { show(); return; }

      // 文字を span 化して --index を振る（1回だけ）
      const text = target.textContent;
      target.textContent = '';
      [...text].forEach((ch, i) => {
        const s = document.createElement('span');
        s.className = 'char';
        s.style.setProperty('--index', i);
        s.textContent = ch;
        target.appendChild(s);
      });

      // data-wait: 表紙では幕が退き始めるのを待ってから観察を始める
      const wait = parseInt(wrap.dataset.wait || '0', 10);
      if (wait > 0) {
        setTimeout(() => onFirstView(wrap, show), wait);
      } else {
        onFirstView(wrap, show);
      }
    });
  }

  /* ---------- 3. 行マスク（.line-mask・GSAP SplitText／未読時フォールバック） ---------- */

  function setupLineMasks() {
    document.querySelectorAll('.line-mask').forEach((text) => {
      let split = null;
      let mode = 'fallback';

      // ガード: SplitText が読めなければ（圏外・file:// でCDN不通）単純フェードへ
      try {
        if (window.gsap && window.SplitText) {
          split = new SplitText(text, { type: 'lines', mask: 'lines' });
          mode = 'gsap';
        }
      } catch (err) {
        split = null;
        mode = 'fallback';
      }

      const play = () => {
        if (mode === 'gsap') {
          if (REDUCED) {
            gsap.set(split.lines, { yPercent: 0 });
            return;
          }
          gsap.fromTo(split.lines,
            { yPercent: 100 },
            { yPercent: 0, duration: 0.8, ease: 'power3.out', stagger: 0.1, overwrite: true });
        } else {
          text.classList.remove('is-fallback');
          void text.offsetWidth;
          text.classList.add('is-fallback');
        }
      };

      if (mode === 'gsap') {
        if (!REDUCED) gsap.set(split.lines, { yPercent: 100 }); // 行をマスクの下へ
      } else if (!REDUCED) {
        text.classList.add('is-armed');                          // opacity: 0 で待つ
      }

      // data-wait: 表紙では幕＋見出しに続いて再生する。他ページは画面に入ってから
      const wait = parseInt(text.dataset.wait || '0', 10);
      if (wait > 0) {
        setTimeout(play, wait);
      } else {
        onFirstView(text, play);
      }
    });
  }

  /* ---------- 4. 一覧のstagger出現（.stagger 内の .card・--index × 70ms） ---------- */

  function setupStagger() {
    const grid = document.querySelector('.stagger');
    if (!grid) return;
    if (REDUCED || !('IntersectionObserver' in window)) {
      grid.classList.add('is-shown');
      return;
    }
    onFirstView(grid, () => grid.classList.add('is-shown'));
  }

  /* ---------- 5. セクション出現（.reveal・下20%で発火・一度だけ） ---------- */

  function setupReveals() {
    const els = [...document.querySelectorAll('.reveal')];
    if (!els.length) return;
    if (REDUCED || !('IntersectionObserver' in window)) {
      els.forEach((el) => el.classList.add('is-shown'));
      return;
    }
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-shown');
        io.unobserve(entry.target);   // 一度出たら観察をやめる
      });
    }, { rootMargin: '0px 0px -20% 0px' });
    els.forEach((el) => io.observe(el));
  }

  /* ---------- 6. 年表の行（.reveal-batch・行ごとに観察、同時に入った行は上から90ms刻み） ---------- */

  function setupChronicle() {
    const rows = [...document.querySelectorAll('.reveal-batch')];
    if (!rows.length) return;
    if (REDUCED || !('IntersectionObserver' in window)) {
      rows.forEach((row) => row.classList.add('is-shown'));
      return;
    }
    const io = new IntersectionObserver((entries) => {
      entries
        .filter((entry) => entry.isIntersecting)
        .sort((a, b) => Number(a.target.dataset.order) - Number(b.target.dataset.order))
        .forEach((entry, i) => {
          entry.target.style.transitionDelay = (i * 90) + 'ms';
          entry.target.classList.add('is-shown');
          io.unobserve(entry.target);
        });
    }, { rootMargin: '0px 0px -20% 0px' });
    rows.forEach((row, i) => {
      row.dataset.order = i;
      io.observe(row);
    });
  }

  /* ---------- 起動（スクリプトは body 末尾・DOMは整っている） ---------- */

  setupCurtain();
  setupCharReveals();
  setupLineMasks();
  setupStagger();
  setupReveals();
  setupChronicle();
})();
