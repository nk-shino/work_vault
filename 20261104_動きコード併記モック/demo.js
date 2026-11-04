/* ============================================================
   動きとコードの併記モック — デモ駆動（バニラJS・即時実行）
   - file:// で直接開いて動く（fetch 不使用・モジュール不使用）
   - 外部CDNは GSAP（デモ3）のみ。読めなければ単純フェードへフォールバック
   - prefers-reduced-motion では幕・出現を即時完了扱いにする
   ============================================================ */
(() => {
  'use strict';

  const REDUCED = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ==================== 共通 ==================== */

  const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

  // pre/code を2〜3色で薄く着色する（外部ライブラリ不使用の簡易処理）
  function highlightCode() {
    const re = /(\/\/[^\n]*|\/\*[\s\S]*?\*\/)|('(?:[^'\\\n]|\\.)*'|"(?:[^"\\\n]|\\.)*")|\b(const|let|var|function|return|if|else|new|window|document|true|false|calc|cubic-bezier)\b/g;
    document.querySelectorAll('pre > code').forEach((code) => {
      const raw = code.textContent;
      let out = '';
      let last = 0;
      let m;
      re.lastIndex = 0;
      while ((m = re.exec(raw))) {
        out += esc(raw.slice(last, m.index));
        const cls = m[1] ? 'tk-c' : (m[2] ? 'tk-s' : 'tk-k');
        out += '<span class="' + cls + '">' + esc(m[0]) + '</span>';
        last = m.index + m[0].length;
      }
      out += esc(raw.slice(last));
      code.innerHTML = out;
    });
  }

  // 再演の型: transition を止めて初期状態へ戻し、次のフレームで付け直す
  function replayClass(el, cls) {
    el.classList.add('no-anim');
    el.classList.remove(cls);
    void el.offsetWidth;   // 強制リフローで「戻した」ことを確定させる
    el.classList.remove('no-anim');
    requestAnimationFrame(() => {
      requestAnimationFrame(() => el.classList.add(cls));
    });
  }

  // 最初に画面に入ったら1回だけ呼ぶ（IntersectionObserver 未対応なら即時）
  function onFirstView(el, fn) {
    if (!('IntersectionObserver' in window)) { fn(); return; }
    const io = new IntersectionObserver((entries, obs) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          obs.disconnect();
          fn();
        }
      });
    }, { threshold: 0.2 });
    io.observe(el);
  }

  /* ==================== デモ1: 読み込み幕 ==================== */

  // 頁全体の幕。読み込み後に1度だけ退く（再読込で確認できる）
  function setupPageCurtain() {
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

  // 枠の中の小型幕。読み込み後に退き、ボタンで再演できる
  function setupMiniCurtain() {
    const mini = document.getElementById('curtain-mini');
    const btn = document.getElementById('replay-curtain');
    if (!mini) return;
    if (REDUCED) {
      mini.classList.add('is-open');
    } else {
      requestAnimationFrame(() => {
        requestAnimationFrame(() => mini.classList.add('is-open'));
      });
    }
    if (btn) btn.addEventListener('click', () => replayClass(mini, 'is-open'));
  }

  /* ==================== デモ2: 見出しの1文字リビール ==================== */

  function setupCharReveal() {
    const target = document.getElementById('char-target');
    const wrap = document.getElementById('char-wrap');
    const btn = document.getElementById('replay-char');
    if (!target || !wrap) return;

    // 文字を span 化して --index を振る（ページ内で1回だけ）
    const text = target.textContent;
    target.textContent = '';
    [...text].forEach((ch, i) => {
      const s = document.createElement('span');
      s.className = 'char';
      s.style.setProperty('--index', i);
      s.textContent = ch;
      target.appendChild(s);
    });

    const show = () => wrap.classList.add('is-shown');
    if (REDUCED) {
      show();
    } else {
      onFirstView(wrap, show);
    }
    if (btn) btn.addEventListener('click', () => replayClass(wrap, 'is-shown'));
  }

  /* ==================== デモ3: 行マスクリビール（GSAP SplitText） ==================== */

  function setupGsapReveal() {
    const text = document.getElementById('gsap-text');
    const status = document.getElementById('gsap-status');
    const btn = document.getElementById('replay-gsap');
    if (!text) return;

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

    if (mode === 'gsap') {
      if (!REDUCED) gsap.set(split.lines, { yPercent: 100 }); // 行をマスクの下へ
      if (status) status.textContent = '方式: SplitText（GSAP CDN・行マスク）';
    } else {
      if (!REDUCED) text.classList.add('is-armed');           // opacity: 0 で待つ
      if (status) status.textContent = '方式: フォールバック（単純フェード）— SplitText を読めませんでした';
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

    onFirstView(text, play);
    if (btn) btn.addEventListener('click', play);
  }

  /* ==================== デモ4: セクション出現（IntersectionObserver） ==================== */

  function setupSectionReveal() {
    const scroller = document.getElementById('reveal-scroller');
    const card = document.getElementById('reveal-card');
    const reset = document.getElementById('replay-reveal');
    if (!scroller || !card) return;

    if (!('IntersectionObserver' in window)) {
      card.classList.add('is-shown');
      if (reset) reset.disabled = true;
      return;
    }

    // 下20%を発火線にする。負の下マージンが判定線を内側へ上げる
    // （このデモは root を枠に指定。本番では root 指定なし＝ビューポート）
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-shown');
        io.unobserve(entry.target);   // 一度出たら観察をやめる
      });
    }, { root: scroller, rootMargin: '0px 0px -20% 0px' });
    io.observe(card);

    if (reset) {
      reset.addEventListener('click', () => {
        card.classList.remove('is-shown');
        scroller.scrollTop = 0;
        io.observe(card);   // 観察を付け直す
      });
    }
  }

  /* ==================== デモ5: 一覧のstagger出現 ==================== */

  // ダミーデータ（無意味な文字列でなく「回廊の記録」の文脈に合わせる）
  const ARCHIVE = [
    { cat: '資料', title: '星読みの章', year: '1931年' },
    { cat: '記録', title: '回廊管理日誌 1923年', year: '1923年' },
    { cat: '記録', title: '渡り廊下 修繕記録', year: '1926年' },
    { cat: '人物', title: '白石 千鶴', year: '記録写真' },
    { cat: '記録', title: '灯りの減り台帳', year: '1935年' },
    { cat: '記録', title: '正門 巡視記録', year: '1929年' }
  ];

  function setupStagger() {
    const list = document.getElementById('stagger-list');
    const btn = document.getElementById('replay-stagger');
    if (!list) return;

    // 通し番号を振り、親に1回だけ合図。遅れの計算は CSS 側
    ARCHIVE.forEach((item, i) => {
      const li = document.createElement('li');
      li.className = 'card';
      li.style.setProperty('--index', i);
      li.innerHTML =
        '<span class="card-cat">' + item.cat + '</span>' +
        '<h3 class="card-title">' + item.title + '</h3>' +
        '<p class="card-year">' + item.year + '</p>';
      list.appendChild(li);
    });

    const show = () => list.classList.add('is-shown');
    if (REDUCED) {
      show();
    } else {
      onFirstView(list, show);
    }
    if (btn) btn.addEventListener('click', () => replayClass(list, 'is-shown'));
  }

  /* ==================== デモ6: 控えめなhover ==================== */

  function setupHover() {
    const btn = document.getElementById('replay-hover');
    const links = [...document.querySelectorAll('.hover-links a')];
    links.forEach((a) => {
      a.addEventListener('click', (e) => e.preventDefault());
    });
    if (!btn) return;
    btn.addEventListener('click', () => {
      // hover 状態を模して順に点ける（本物の hover でも同じ見え方になる）
      links.forEach((a, i) => {
        const delay = REDUCED ? 0 : i * 140;
        setTimeout(() => a.classList.add('is-hover'), delay);
        setTimeout(() => a.classList.remove('is-hover'), delay + 1000);
      });
    });
  }

  /* ==================== 起動（スクリプトは body 末尾・DOMは整っている） ==================== */

  highlightCode();
  setupPageCurtain();
  setupMiniCurtain();
  setupCharReveal();
  setupGsapReveal();
  setupSectionReveal();
  setupStagger();
  setupHover();
})();
