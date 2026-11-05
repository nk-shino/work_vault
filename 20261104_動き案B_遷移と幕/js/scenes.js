/* ============================================================
   演出の本体（scenes.js）— 動き案B「遷移と幕」
   幕の開閉は in-out-expo、出現は out-back。曲線はこの 2 つに統一する。

   - 読み込み幕（index の is-hold）: 割れ扉が中央から左右へ開く
   - ワイプ遷移（data-wipe）: 水平フローが左から閉じ、到着側で右へ抜ける
   - 到着（is-cover）: 流れの継続として右へ流出する
   - 出現: data-rise / data-scale-in / .tl-row / .card を out-back で立てる

   教訓の適用:
   - prep は必ず先頭で HAS_GSAP を確認する（CDN 不達で幕を閉じたままにしない）
   - gsap.set で xPercent を明示してから tween する（CSS クラスの transform と
     計算済み行列の混線を避ける。状態は起動時に inline へ引き取る）
   - playX は prepared フラグを確認してから動く
   ============================================================ */

(function () {
  'use strict';

  var d = document;
  var bridge = window.__bridge;
  if (!bridge) return;

  var REDUCED = bridge.REDUCED;
  var curtain = bridge.curtain;

  /* GSAP 未達または縮退: 幕の状態クラスを解けば CSS 既定
     （扉は開・フローは格納）に戻り、全要素が表示されたままになる */
  var HAS_GSAP = typeof window.gsap !== 'undefined';
  if (REDUCED || !HAS_GSAP) {
    if (curtain) curtain.classList.remove('is-live', 'is-cover', 'is-hold');
    bridge.scenesBooted = true;
    return;
  }

  if (window.ScrollTrigger) gsap.registerPlugin(ScrollTrigger);

  var EASE_CURTAIN = 'expo.inOut';   // 幕系: in-out-expo
  var EASE_IN = 'back.out(1.4)';     // 出現系: out-back（微オーバーシュート）

  var doorLeft = curtain ? curtain.querySelector('.door-left') : null;
  var doorRight = curtain ? curtain.querySelector('.door-right') : null;
  var mark = curtain ? curtain.querySelector('.curtain-mark') : null;
  var flowCrimson = curtain ? curtain.querySelector('.flow-crimson') : null;
  var flowInk = curtain ? curtain.querySelector('.flow-ink') : null;

  function stripState() {
    if (curtain) curtain.classList.remove('is-live', 'is-cover', 'is-hold');
  }

  /* ---------- 幕の状態を CSS クラスから gsap の inline へ引き取る ---------- */
  function takeOverCurtain() {
    if (!curtain) return false;
    var hold = curtain.classList.contains('is-hold');
    var cover = curtain.classList.contains('is-cover');
    if (!hold && !cover) return false;
    if (doorLeft) gsap.set(doorLeft, { xPercent: hold ? 0 : -102 });
    if (doorRight) gsap.set(doorRight, { xPercent: hold ? 0 : 102 });
    if (mark) gsap.set(mark, { autoAlpha: hold ? 1 : 0 });
    if (flowCrimson) gsap.set(flowCrimson, { xPercent: cover ? 0 : -101 });
    if (flowInk) gsap.set(flowInk, { xPercent: cover ? 0 : -101 });
    curtain.classList.remove('is-hold', 'is-cover');
    return hold ? 'hold' : 'cover';
  }

  /* ---------- ワイプ遷移（data-wipe）: 水平フローで閉じてから移動 ---------- */
  function wipeNavigate(url) {
    if (!curtain || !flowCrimson || !flowInk) {
      window.location.href = url;
      return;
    }
    bridge.setWipeFlag();
    curtain.classList.add('is-live'); // 先に可視化してから動かす
    gsap.set(flowCrimson, { xPercent: -101 });
    gsap.set(flowInk, { xPercent: -101 });
    gsap.timeline({
      onComplete: function () { window.location.href = url; }
    })
      .to(flowCrimson, { xPercent: 0, duration: 0.5, ease: EASE_CURTAIN }, 0)
      .to(flowInk, { xPercent: 0, duration: 0.55, ease: EASE_CURTAIN }, 0.08);
  }

  d.addEventListener('click', function (ev) {
    var a = ev.target.closest('a[data-wipe]');
    if (!a) return;
    if (ev.defaultPrevented || ev.button !== 0) return;
    if (ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;
    ev.preventDefault();
    wipeNavigate(a.getAttribute('href'));
  });

  /* ---------- ページ別の準備と出現 ---------- */
  var prepared = { home: false, chara: false, record: false };

  function prepHome() {
    if (!HAS_GSAP) return; // 応急の二重ガード
    gsap.set('.hero [data-rise]', { y: 34, autoAlpha: 0 });
    gsap.set('.num', { y: 26, autoAlpha: 0 });
    prepared.home = true;
  }

  function playHome() {
    if (!prepared.home) return;
    gsap.to('.hero [data-rise]', {
      y: 0, autoAlpha: 1, duration: 0.9, ease: EASE_IN,
      stagger: 0.07, clearProps: 'transform'
    });
    gsap.to('.num', {
      y: 0, autoAlpha: 1, duration: 0.8, ease: EASE_IN, delay: 0.15,
      stagger: 0.06, clearProps: 'transform'
    });
  }

  function prepChara() {
    if (!HAS_GSAP) return;
    gsap.set('.grid .card', { y: 30, autoAlpha: 0 });
    prepared.chara = true;
  }

  function playChara() {
    if (!prepared.chara) return;
    // 一括の立ち上げ（案Bでは stagger を使わない。群れで一度に湧く）
    gsap.to('.grid .card', {
      y: 0, autoAlpha: 1, duration: 0.9, ease: EASE_IN, clearProps: 'transform'
    });
  }

  function prepRecord() {
    if (!HAS_GSAP) return;
    gsap.set('.record-hero [data-rise]', { y: 30, autoAlpha: 0 });
    gsap.set('[data-scale-in]', { scale: 0.94, autoAlpha: 0 });
    gsap.set('.tl-row', { y: 24, autoAlpha: 0 });
    prepared.record = true;
  }

  function playRecord() {
    if (!prepared.record) return;
    gsap.to('.record-hero [data-rise]', {
      y: 0, autoAlpha: 1, duration: 0.9, ease: EASE_IN,
      stagger: 0.07, clearProps: 'transform'
    });
    // scale 入口系: facts と works が 0.94 → 1 で着地する（ScrollTrigger once）
    gsap.utils.toArray('[data-scale-in]').forEach(function (el) {
      gsap.to(el, {
        scale: 1, autoAlpha: 1, duration: 0.9, ease: EASE_IN, clearProps: 'transform',
        scrollTrigger: window.ScrollTrigger
          ? { trigger: el, start: 'top 88%', once: true }
          : undefined
      });
    });
    // 年表の行は通過の順に立ち上がる（out-back）
    gsap.utils.toArray('.tl-row').forEach(function (el, i) {
      gsap.to(el, {
        y: 0, autoAlpha: 1, duration: 0.7, ease: EASE_IN, clearProps: 'transform',
        delay: window.ScrollTrigger ? 0 : i * 0.05,
        scrollTrigger: window.ScrollTrigger
          ? { trigger: el, start: 'top 90%', once: true }
          : undefined
      });
    });
  }

  // 絞り込み後の立ち上げ（motion.js の click から呼ばれる）
  bridge.onFilter = function () {
    var shown = [];
    d.querySelectorAll('.cell[data-aff]').forEach(function (cell) {
      if (!cell.hidden) {
        var card = cell.querySelector('.card');
        if (card) shown.push(card);
      }
    });
    if (!shown.length) return;
    gsap.fromTo(shown, { y: 14, autoAlpha: 0 }, {
      y: 0, autoAlpha: 1, duration: 0.5, ease: EASE_IN, clearProps: 'transform'
    });
  };

  /* ---------- 起動 ---------- */
  var page = d.body.getAttribute('data-page');
  var state = takeOverCurtain(); // 'hold' | 'cover' | false

  if (page === 'home') prepHome();
  else if (page === 'chara') prepChara();
  else if (page === 'record') prepRecord();

  var playX = page === 'home' ? playHome
    : page === 'chara' ? playChara
    : page === 'record' ? playRecord
    : null;

  bridge.scenesBooted = true;

  if (state === 'hold' && doorLeft && doorRight) {
    // 表紙: 扉が中央から左右へ開く。開ききる前に出現を重ねる
    gsap.timeline({ onComplete: stripState })
      .to(mark, { autoAlpha: 0, duration: 0.35, ease: 'power1.in' }, 0)
      .to(doorLeft, { xPercent: -102, duration: 0.9, ease: EASE_CURTAIN }, 0.05)
      .to(doorRight, { xPercent: 102, duration: 0.9, ease: EASE_CURTAIN }, 0.05)
      .add(playX, '-=0.3');
  } else if (state === 'cover' && flowInk && flowCrimson) {
    // 到着: 流れの継続。墨の層が先に抜け、紅の層が追う
    gsap.timeline({ onComplete: stripState })
      .to(flowInk, { xPercent: 101, duration: 0.55, ease: EASE_CURTAIN }, 0)
      .to(flowCrimson, { xPercent: 101, duration: 0.55, ease: EASE_CURTAIN }, 0.09)
      .add(playX, '-=0.3');
  } else if (playX) {
    // 幕なし到着（VT 円弧・直アクセス）
    playX();
  }

  /* ---------- bfcache 復帰: inline の幕状態も既定へ戻す ---------- */
  window.addEventListener('pageshow', function (ev) {
    if (!ev.persisted) return;
    stripState();
    var parts = [doorLeft, doorRight, flowCrimson, flowInk].filter(Boolean);
    if (parts.length) gsap.set(parts, { clearProps: 'transform' });
  });
})();
