/* ============================================================
   J-01 表示形式切替テスト — capture.cjs
   Playwright（file:// 直読み・headless・ローカルの playwright を使用）
   点検 26 項目 + fullPage スクリーンショット 7 枚 + console-report.txt 出力

   実行: node capture.cjs
   ※ page.evaluate は関数を持ち帰れないため、ページ内でスナップショットを
     計算してから返す（window.__formtest の各関数はページ内で呼ぶ）。
   ※ 切替フェードの観測は click 後のポーリングでは間に合わない（click の
     actionability 待ちがフェード 75ms を超える実測）ため、ページ内の
     rAF サンプラーと transition イベント記録で行う（probe-fade の実測による）。
   ============================================================ */
'use strict';

const path = require('path');
const fs = require('fs');
const { pathToFileURL } = require('url');
const { chromium } = require('playwright');

const results = [];
function check(name, cond, detail) {
  results.push({ ok: !!cond, name, detail: detail === undefined ? '' : String(detail) });
}

(async () => {
  const shotsDir = path.join(__dirname, 'shots');
  fs.mkdirSync(shotsDir, { recursive: true });
  const URL_INDEX = pathToFileURL(path.join(__dirname, 'index.html')).href;
  const shots = [];

  const consoleErrors = [];

  function collectConsole(page, label) {
    page.on('console', (m) => {
      if (m.type() === 'error') consoleErrors.push(`[${label}] console.error: ${m.text()}`);
    });
    page.on('pageerror', (e) => {
      consoleErrors.push(`[${label}] pageerror: ${e.message}`);
    });
  }

  /* ページ内でスナップショットを計算して返す */
  const SNAP_SRC = () => {
    const F = window.__formtest;
    return {
      state: { reduce: F.state.reduce, form: F.state.form, layout: F.state.layout, aff: F.state.aff },
      counts: F.counts(),
      vis: F.vis(),
      switchMs: F.switchMs(),
      fadeHalfMs: F.fadeHalfMs(),
      cardCols: F.cardCols(),
      opacity: F.opacity(),
      delays: F.delays(),
      resultText: F.resultText(),
      chipsState: F.chipsState()
    };
  };
  const snapOf = (page) => page.evaluate(SNAP_SRC);
  const setReduceOf = (page, on) =>
    page.evaluate((v) => {
      const el = document.getElementById('reduce-motion');
      el.checked = v;
      el.dispatchEvent(new Event('change'));
    }, on);

  /* 切替フェードの観測: ページ内で最小 opacity と transition イベントを記録する */
  const armFadeProbe = (page) =>
    page.evaluate(() => {
      const lw = document.getElementById('listwrap');
      const probe = { events: [], min: 1 };
      window.__fadeProbe = probe;
      ['transitionrun', 'transitionstart', 'transitionend', 'transitioncancel'].forEach((ev) =>
        lw.addEventListener(ev, () => probe.events.push(ev))
      );
      (function loop() {
        const p = window.__fadeProbe;
        if (!p) return;
        const o = parseFloat(getComputedStyle(lw).opacity);
        if (o < p.min) p.min = o;
        requestAnimationFrame(loop);
      })();
    });
  const readFadeProbe = (page) =>
    page.evaluate(() => {
      const p = window.__fadeProbe;
      const r = { events: p ? p.events.slice() : [], min: p ? p.min : null };
      window.__fadeProbe = null; /* サンプラー停止 */
      return r;
    });

  const browser = await chromium.launch({ headless: true });

  /* ================= パスA: 1280px で機能点検 ================= */
  const pageA = await browser.newPage({ viewport: { width: 1280, height: 900 }, deviceScaleFactor: 2 });
  collectConsole(pageA, 'A-1280');
  await pageA.goto(URL_INDEX);
  await pageA.waitForTimeout(1700); /* 初回出現の呼吸層（最大480ms+720ms）が終わるのを待つ */
  let t = await snapOf(pageA);
  let c = t.counts;
  let chips = t.chipsState;
  let d = t.delays;

  /* --- A. 初期状態（受け入れ条件①: 既定は画面幅で適した形式） --- */
  check('A01 初期(1280px): 既定形式はカード（画面幅で選択）', t.vis.card && !t.vis.row, JSON.stringify(t.vis));
  check('A02 初期: カード13件を表示（総数13を保持・両容器とも13個を作りっぱなし）',
    c.cards === 13 && c.cardAll === 13 && c.rowAll === 13 && c.total === 13, JSON.stringify(c));
  const colsFlow = t.cardCols;
  const tracksFlow = colsFlow.split(' ').filter(Boolean).length;
  check('A03 現行流: auto-fill の可変グリッド（1280px で3列以上）', tracksFlow >= 3, `${tracksFlow}列 / ${colsFlow}`);
  check('A04 初期: 出現遅延は通し番号方式（1件目0ms・13件目480ms=上限）',
    d.cards[0] === '0ms' && d.cards[12] === '480ms' && d.rows[0] === '0ms' && d.rows[12] === '480ms',
    `cards: ${d.cards[0]}..${d.cards[12]} / rows: ${d.rows[0]}..${d.rows[12]}`);
  check('A05 初期: 形式チップの aria-pressed（カード=true・行=false）',
    chips.form[0][1] === 'true' && chips.form[1][1] === 'false', JSON.stringify(chips.form));

  /* --- B. 形式切替 → 行（J-01 の本体） --- */
  await armFadeProbe(pageA);
  await pageA.click('button[data-form="row"]');
  await pageA.waitForTimeout(450); /* 切替（150ms）完了まで待つ・記録はページ内で取る */
  t = await snapOf(pageA);
  const probe1 = await readFadeProbe(pageA);
  check('A06 切替中: 容器の淡い切替が効いている（transitionstart 発火・最小 opacity 0.45台）',
    probe1.events.includes('transitionstart') && probe1.min > 0.3 && probe1.min < 0.5,
    `min=${probe1.min} events=[${probe1.events.join(',')}]`);
  check('A07 切替: 容器フェードは 0.15秒の半分（75ms・不透明度のみ）',
    Math.abs(t.fadeHalfMs - 75) <= 3, `${t.fadeHalfMs}ms`);
  chips = t.chipsState;
  c = t.counts;
  check('A08 行形式: aria-pressed 遷移（行=true・カード=false）',
    chips.form[1][1] === 'true' && chips.form[0][1] === 'false', JSON.stringify(chips.form));
  check('A09 行形式: 行13件を保持し、行コンテナが表示される（切替後も件数13）',
    c.rows === 13 && c.rowAll === 13 && t.vis.row && !t.vis.card, JSON.stringify(c));
  check('A10 行形式: 並べ方チップは非活性（行は常に1列で並ぶため）',
    chips.layout.every((x) => x[2] === 'true'), JSON.stringify(chips.layout));

  /* --- C. カードへ復帰 --- */
  await pageA.click('button[data-form="card"]');
  await pageA.waitForTimeout(320);
  t = await snapOf(pageA);
  c = t.counts;
  check('A11 カード復帰: aria-pressed が戻り・13件保持',
    t.chipsState.form[0][1] === 'true' && c.cards === 13 && t.vis.card, `cards=${c.cards}`);

  /* --- D. 並べ方 → 整列タイル流（A-3 比較の軸） --- */
  await pageA.click('button[data-layout="tile"]');
  await pageA.waitForTimeout(120);
  t = await snapOf(pageA);
  const colsTile = t.cardCols;
  check('A12 整列タイル流: 固定3列（PC）', colsTile.split(' ').filter(Boolean).length === 3, colsTile);
  check('A13 整列タイル流: 件数13を保持', t.counts.cards === 13, `cards=${t.counts.cards}`);

  /* 整列タイル → 行 → カード（layout=tile のまま）: 両レイアウト×両形式の組合せで13を保持 */
  await pageA.click('button[data-form="row"]');
  await pageA.waitForTimeout(320);
  await pageA.click('button[data-form="card"]');
  await pageA.waitForTimeout(320);
  t = await snapOf(pageA);
  c = t.counts;
  check('A14 整列タイル→行→カード: 件数13を保持（両レイアウト×両形式）',
    c.cards === 13 && c.rows === 13 && t.cardCols.split(' ').filter(Boolean).length === 3, JSON.stringify(c));

  /* --- E. 絞り込み（テストデータを用意して実行する部分） --- */
  await pageA.click('button[data-aff="回廊聖堂"]');
  await pageA.waitForTimeout(320);
  t = await snapOf(pageA);
  check('A15 絞り込み: 回廊聖堂 → 4人表示（テストデータ上の実数）',
    t.counts.cards === 4 && t.resultText === '4人を表示中。', `${t.counts.cards}人 / 「${t.resultText}」`);
  await pageA.click('button[data-form="row"]');
  await pageA.waitForTimeout(320);
  t = await snapOf(pageA);
  check('A16 絞り込み×行形式: 行の表示は4件（同じ13人から4人）', t.counts.rows === 4, `rows=${t.counts.rows}`);
  await pageA.click('button[data-aff="all"]');
  await pageA.waitForTimeout(320);
  t = await snapOf(pageA);
  check('A17 絞り込み解除: 13人に戻る（両容器とも）',
    t.counts.cards === 13 && t.counts.rows === 13 && t.resultText === '13人を表示中。',
    `${t.counts.cards}/${t.counts.rows} 「${t.resultText}」`);

  /* --- F. 動きを減らす設定（§A-4 シミュレーション） --- */
  await pageA.click('button[data-form="card"]');
  await pageA.waitForTimeout(320);
  await setReduceOf(pageA, true);
  t = await snapOf(pageA);
  check('A18 reduce ON: html.reduce-motion が付く（§A-4）', t.state.reduce === true, `reduce=${t.state.reduce}`);
  d = t.delays;
  const allZero = d.cards.concat(d.rows).every((v) => v === '0ms');
  check('A19 reduce ON: 出現遅延がすべて 0（§B-5 遅延も0）', allZero,
    `cards=${d.cards[0]}..${d.cards[12]} / rows=${d.rows[0]}..${d.rows[12]}`);
  check('A19b reduce ON: 容器の transition がほぼ 0', t.fadeHalfMs < 5, `${t.fadeHalfMs}ms`);
  await pageA.click('button[data-form="row"]');
  await pageA.waitForTimeout(60);
  t = await snapOf(pageA);
  check('A20 reduce ON: 切替は即時（60ms後に行形式へ移り opacity===1）',
    t.vis.row === true && t.opacity === 1, `row=${t.vis.row} opacity=${t.opacity}`);
  await setReduceOf(pageA, false);
  await armFadeProbe(pageA);
  await pageA.click('button[data-form="card"]');
  await pageA.waitForTimeout(450);
  t = await snapOf(pageA);
  const probe2 = await readFadeProbe(pageA);
  check('A21 reduce OFF: フェードが復活し・切替後は opacity===1 で止まる',
    probe2.events.includes('transitionstart') && probe2.min > 0.3 && probe2.min < 0.5 && t.opacity === 1 && t.vis.card,
    `min=${probe2.min} events=[${probe2.events.join(',')}] endOpacity=${t.opacity}`);

  /* --- 1280px のスクリーンショット（状態を撮る） --- */
  await pageA.click('button[data-layout="tile"]');
  await pageA.waitForTimeout(420);
  await pageA.screenshot({ path: path.join(shotsDir, 'full-1280-tile.png'), fullPage: true });
  shots.push('full-1280-tile.png（1280px・カード×整列タイル流）');
  await pageA.click('button[data-form="row"]');
  await pageA.waitForTimeout(420);
  await pageA.screenshot({ path: path.join(shotsDir, 'full-1280-row.png'), fullPage: true });
  shots.push('full-1280-row.png（1280px・行形式）');
  await setReduceOf(pageA, true);
  await pageA.waitForTimeout(200);
  await pageA.screenshot({ path: path.join(shotsDir, 'full-1280-reduce.png'), fullPage: true });
  shots.push('full-1280-reduce.png（1280px・行形式・動きを減らす設定ON）');
  await pageA.close();

  /* ================= パスB: 1920px（PC 幅の広い側） ================= */
  const pageB = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2 });
  collectConsole(pageB, 'B-1920');
  await pageB.goto(URL_INDEX);
  await pageB.waitForTimeout(1700);
  t = await snapOf(pageB);
  check('A22 1920px: 既定はカード・13件（広い PC 幅でも同じ既定）',
    t.vis.card && t.counts.cards === 13, JSON.stringify(t.vis));
  await pageB.screenshot({ path: path.join(shotsDir, 'full-1920-card.png'), fullPage: true });
  shots.push('full-1920-card.png（1920px・カード×現行流の既定）');
  await pageB.close();

  /* ================= パスC: 375px（モバイル幅） ================= */
  const pageC = await browser.newPage({ viewport: { width: 375, height: 812 }, deviceScaleFactor: 2 });
  collectConsole(pageC, 'C-375');
  await pageC.goto(URL_INDEX);
  await pageC.waitForTimeout(1700);
  t = await snapOf(pageC);
  check('A23 375px: 既定は行（画面幅で適した形式・受け入れ条件①）',
    t.vis.row && !t.vis.card, JSON.stringify(t.vis));
  check('A24 375px: 行13件（最低限の情報=名前・役割・所属・外見が行内にある）',
    t.counts.rows === 13 && t.counts.rowAll === 13, JSON.stringify(t.counts));
  await pageC.screenshot({ path: path.join(shotsDir, 'full-375-row.png'), fullPage: true });
  shots.push('full-375-row.png（375px・行形式の既定）');
  await pageC.click('button[data-form="card"]');
  await pageC.waitForTimeout(420);
  await pageC.screenshot({ path: path.join(shotsDir, 'full-375-card.png'), fullPage: true });
  shots.push('full-375-card.png（375px・カード×現行流へ切替）');
  await pageC.click('button[data-layout="tile"]');
  await pageC.waitForTimeout(420);
  t = await snapOf(pageC);
  const colsTileM = t.cardCols;
  check('A25 375px: 整列タイル流は2列固定（規則的・均一を保つ）',
    colsTileM.split(' ').filter(Boolean).length === 2, colsTileM);
  await pageC.screenshot({ path: path.join(shotsDir, 'full-375-tile.png'), fullPage: true });
  shots.push('full-375-tile.png（375px・カード×整列タイル流=2列固定）');
  await pageC.close();

  await browser.close();

  /* ================= 報告 ================= */
  const ng = results.filter((r) => !r.ok);
  const lines = [];
  lines.push('J-01 表示形式切替テスト — capture 結果');
  lines.push(`実行日時: ${new Date().toISOString()}`);
  lines.push('対象: index.html（file:// 直読み・headless Chromium・deviceScaleFactor=2）');
  lines.push('');
  lines.push('--- 点検結果 ---');
  results.forEach((r, i) => {
    lines.push(`${String(i + 1).padStart(2, '0')} ${r.ok ? 'OK' : 'NG'} ${r.name}${r.detail ? ` — ${r.detail}` : ''}`);
  });
  lines.push('');
  lines.push('--- コンソール ---');
  lines.push(`エラー件数: ${consoleErrors.length}`);
  consoleErrors.forEach((e) => lines.push(`  ${e}`));
  lines.push('');
  lines.push('--- スクリーンショット ---');
  shots.forEach((s) => lines.push(`  ${s}`));
  lines.push('');
  lines.push(`合計: ${results.length}件 / OK ${results.length - ng.length} / NG ${ng.length} / consoleエラー ${consoleErrors.length}`);
  lines.push(ng.length === 0 && consoleErrors.length === 0 ? '判定: ALL OK' : '判定: NG — 上記を修正のこと');
  const report = lines.join('\n') + '\n';
  fs.writeFileSync(path.join(shotsDir, 'console-report.txt'), report, 'utf8');

  console.log(report);
  process.exit(ng.length === 0 && consoleErrors.length === 0 ? 0 : 1);
})().catch((e) => {
  console.error('[capture] 実行失敗:', e);
  process.exit(1);
});
