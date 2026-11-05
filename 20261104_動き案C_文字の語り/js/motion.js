/* ============================================================
   回廊の記録 — 動き案C「文字の語り」: 共通層（motion.js）
   バニラ JS。GSAP・anime.js を使う演出は js/scenes.js が担当する。

   担当:
   - reduced-motion の確定（scenes.js へ渡す）
   - 所属絞り込み（aria-pressed・aria-live・reduced-motion でも機能）

   隠し状態について:
   CSS に隠し状態を置かない。GSAP の対象は「ライブラリの準備が
   整ったことを確認してから」JS 側でのみ隠すため、JS 無効・CDN 不達・
   reduced-motion のいずれでも全要素が表示される。
   ============================================================ */
(() => {
  'use strict';

  const REDUCED = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // scenes.js へ渡す共通ハンドル
  window.__corridor = { REDUCED };

  // 絞り込みは動きの層に依存しない（reduced-motion でも機能させる）
  setupFilter();

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
})();
