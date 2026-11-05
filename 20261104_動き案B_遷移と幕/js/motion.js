/* ============================================================
   基盤（motion.js）— 動き案B「遷移と幕」
   幕の状態機構 / VT 円弧の起点の引き継ぎ / 絞り込み / バニラカウンター。
   演出の本体（GSAP タイムライン）は scenes.js。window.__bridge で繋ぐ。

   規約:
   - 隠し状態は JS だけが作る（noscript では全内容が最初から見える）
   - 幕はクラス（is-live / is-hold / is-cover）で状態を持ち、
     scenes.js が起動した時点で gsap の inline へ引き取られる
   - 幕の取り残し防止: scenes.js が 1600ms 以内に起動しなければ解く
   ============================================================ */

(function () {
  'use strict';

  var d = document;
  var root = d.documentElement;
  root.classList.add('js-armed');

  var REDUCED = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var curtain = d.querySelector('[data-curtain]');

  /* ---------- 札（sessionStorage フラグ） ---------- */
  var WIPE_FLAG = 'caseB-wipe-at';
  var VT_ORIGIN = 'caseB-vt-origin';
  var FLAG_VALID_MS = 4000;

  function readFlag(key) {
    try {
      var raw = sessionStorage.getItem(key);
      if (!raw) return null;
      sessionStorage.removeItem(key);
      var rec = JSON.parse(raw);
      if (!rec || typeof rec.t !== 'number') return null;
      if (Date.now() - rec.t > FLAG_VALID_MS) return null;
      return rec;
    } catch (e) {
      return null;
    }
  }

  function setWipeFlag() {
    try {
      sessionStorage.setItem(WIPE_FLAG, JSON.stringify({ t: Date.now() }));
    } catch (e) { /* 秘密モード等: 幕なし遷移に退く */ }
  }

  /* ---------- 幕の状態機構 ---------- */
  function stripCurtain() {
    if (curtain) curtain.classList.remove('is-live', 'is-cover', 'is-hold');
  }

  function bootCurtain() {
    if (!curtain || REDUCED) return;
    // 1) 水平フローで閉じてきた到着（data-wipe の直後）
    if (readFlag(WIPE_FLAG)) {
      curtain.classList.add('is-live', 'is-cover');
      return;
    }
    // 2) 表紙の初回: 扉を閉じた状態から始める
    if (d.body.hasAttribute('data-curtain-hold')) {
      curtain.classList.add('is-live', 'is-hold');
    }
    // 3) それ以外の到着は幕を出さない（VT 円弧か、素の表示に任せる）
  }

  bootCurtain();

  // 応急の幕取り残し防止: scenes.js が起動しなかった場合のみ解く
  window.setTimeout(function () {
    if (!window.__bridge || !window.__bridge.scenesBooted) stripCurtain();
  }, 1600);

  /* ---------- VT: 円弧の起点 ---------- */
  // conic-gradient の --vt-sweep をアニメさせるには @property 登録が要る。
  // 確認してから :root に vt-arc を付与する（付かなければ既定のクロスフェード）。
  var VT_OK = !!(
    window.CSSViewTransitionRule &&
    window.CSS &&
    typeof window.CSS.registerProperty === 'function'
  );

  function restoreVtOrigin() {
    if (!VT_OK || REDUCED) return;
    var rec = readFlag(VT_ORIGIN);
    if (!rec) return;
    if (typeof rec.x === 'number' && typeof rec.y === 'number') {
      root.style.setProperty('--vt-x', (rec.x * 100).toFixed(2) + '%');
      root.style.setProperty('--vt-y', (rec.y * 100).toFixed(2) + '%');
    }
  }

  function saveVtOrigin(ev) {
    if (!VT_OK || REDUCED) return;
    var x = 0.5;
    var y = 0.5;
    if (ev && typeof ev.clientX === 'number' && (ev.clientX > 0 || ev.clientY > 0)) {
      x = Math.min(Math.max(ev.clientX / window.innerWidth, 0), 1);
      y = Math.min(Math.max(ev.clientY / window.innerHeight, 0), 1);
    }
    try {
      sessionStorage.setItem(VT_ORIGIN, JSON.stringify({ t: Date.now(), x: x, y: y }));
    } catch (e) { /* 起点なし: 円弧は画面中心から広がる */ }
  }

  if (VT_OK) root.classList.add('vt-arc');

  // 記録を開く操作（data-vt）でのみ起点を保存する
  d.addEventListener('click', function (ev) {
    var a = ev.target.closest('a[data-vt]');
    if (a) saveVtOrigin(ev);
  });

  restoreVtOrigin();

  /* ---------- 絞り込み（chara） ---------- */
  function setupCharaFilter() {
    var bar = d.querySelector('[data-filter]');
    var cells = Array.prototype.slice.call(d.querySelectorAll('.cell[data-aff]'));
    var line = d.querySelector('[data-result]');
    if (!bar || !cells.length) return;
    var chips = Array.prototype.slice.call(bar.querySelectorAll('.chip'));

    function apply(key) {
      var shown = 0;
      cells.forEach(function (cell) {
        var hit = key === 'all' || cell.getAttribute('data-aff') === key;
        cell.hidden = !hit;
        if (hit) shown++;
      });
      chips.forEach(function (chip) {
        chip.setAttribute('aria-pressed', chip.getAttribute('data-key') === key ? 'true' : 'false');
      });
      if (line) {
        var msg = shown + '人を表示中。';
        if (line.textContent !== msg) line.textContent = msg;
      }
    }

    bar.addEventListener('click', function (ev) {
      var chip = ev.target.closest('.chip');
      if (!chip) return;
      apply(chip.getAttribute('data-key'));
      // 出現し直しの立ち上げは scenes.js に委ねる（out-back で揃える）
      if (window.__bridge && typeof window.__bridge.onFilter === 'function') {
        window.__bridge.onFilter();
      }
    });

    apply('all');
  }

  setupCharaFilter();

  /* ---------- バニラカウンター（index の nums） ----------
     GSAP に頼らない。待機中は HTML の最終値のまま（noscript・CDN 不達でも
     数値が見える）。発火した瞬間に 0 から数え直す。 */
  function setupCounters() {
    var els = Array.prototype.slice.call(d.querySelectorAll('[data-count]'));
    if (!els.length) return;
    if (REDUCED || !('IntersectionObserver' in window)) return;

    var DURATION = 1200;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        io.unobserve(entry.target);
        run(entry.target);
      });
    }, { threshold: 0.5 });

    els.forEach(function (el) {
      io.observe(el);
    });

    function run(el) {
      var target = parseInt(el.getAttribute('data-count'), 10) || 0;
      var t0 = null;
      function frame(now) {
        if (t0 === null) t0 = now;
        var p = Math.min((now - t0) / DURATION, 1);
        var eased = 1 - Math.pow(1 - p, 3); // cubic-out
        el.textContent = String(Math.round(target * eased));
        if (p < 1) window.requestAnimationFrame(frame);
      }
      window.requestAnimationFrame(frame);
    }
  }

  setupCounters();

  /* ---------- bfcache 復帰: 幕の状態クラスだけは必ず解く ---------- */
  window.addEventListener('pageshow', function (ev) {
    if (ev.persisted) stripCurtain();
  });

  /* ---------- 公開 ---------- */
  window.__bridge = {
    REDUCED: REDUCED,
    curtain: curtain,
    setWipeFlag: setWipeFlag,
    scenesBooted: false
  };
})();
