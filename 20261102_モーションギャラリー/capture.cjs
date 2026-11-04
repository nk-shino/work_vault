/**
 * モーションギャラリー 撮影スクリプト（Playwright / headless Chromium）
 * 先日の Swiper モックアップの capture.cjs と同じ方式。
 *
 * - fullPage 1枚（暗テーマ・自動再生停止の静止状態）
 * - ヒーロー: 自動再生の進行3枚 + ホバー一時停止のDOM検査
 * - F-1: 改修後（容器の淡い切替）と従来（行を立て直す）の各自動スナップ + 節点存続検査
 * - F-2: ホバー状態のスナップ + 浮き2pxの検査
 * - F-3: カード押下 → 詳細切替スナップ + 目印が常に1つの検査
 * - F-4: 読み込み中 / 成功 / 失敗 / 0件(速い) の各スナップ
 * - F-6: 0件 → 候補出現のスナップ
 * - 追加ラウンド（2026-11-04）: 07 読み込み幕・08 年表・09 図形の漂い・10 出現の時間差・11 額の接続・12 装飾部品
 * - 動きを減らす設定: 適用時のスナップ + 遅延0・自動再生停止の検査（新パネル含む）
 * - 明テーマ: ヒーロー / F-2 / fullPage
 * - コンソールメッセージと検査結果を shots/console-report.txt に保存
 *
 * 実行: node capture.cjs
 */
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const ROOT = __dirname;
const SHOTS = path.join(ROOT, 'shots');
fs.mkdirSync(SHOTS, { recursive: true });

const report = [];
const log = (s) => { console.log(s); report.push(s); };
const failures = [];
const check = (name, cond, detail) => {
  const line = `check: ${name} -> ${cond ? 'OK' : 'NG'}${detail ? ' :: ' + detail : ''}`;
  log(line);
  if (!cond) failures.push(line);
};

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({
    viewport: { width: 1440, height: 960 },
    deviceScaleFactor: 2
  });

  const consoleLines = [];
  page.on('console', (m) => consoleLines.push(`[${m.type()}] ${m.text()}`));
  page.on('pageerror', (e) => consoleLines.push(`[pageerror] ${e.message}`));
  page.on('requestfailed', (r) => consoleLines.push(`[requestfailed] ${r.url()} :: ${r.failure() && r.failure().errorText}`));

  const url = 'file:///' + path.join(ROOT, 'index.html').replace(/\\/g, '/');
  await page.goto(url, { waitUntil: 'networkidle', timeout: 90000 });
  await page.waitForTimeout(1800); // フォント・出現アニメの落ち着き待ち

  const shot = async (locator, name) => {
    await locator.scrollIntoViewIfNeeded();
    await page.waitForTimeout(150);
    await locator.screenshot({ path: path.join(SHOTS, name) });
    log(`shot: ${name}`);
  };

  // ---- DOM検査: 初期状態 ----
  const dom = await page.evaluate(() => {
    const g = window.__gallery || {};
    return {
      swiper: typeof window.Swiper !== 'undefined' ? (window.Swiper.version || 'loaded') : 'NOT LOADED',
      heroInitialized: !!(g.hero),
      catalogRows: g.catalogLength || 0,
      persistRows: g.f1PersistCount ? g.f1PersistCount() : -1,
      markerCount: g.markerCount,
      theme: document.documentElement.dataset.theme
    };
  });
  log('--- DOM checks (initial) ---');
  log(JSON.stringify(dom, null, 2));
  check('catalog rows = 61', dom.catalogRows === 61, String(dom.catalogRows));
  check('F-1 rows persist-attached = 61', dom.persistRows === 61, String(dom.persistRows));
  check('F-3 initial marker = 1', dom.markerCount === 1, String(dom.markerCount));

  const hero = page.locator('#panel-hero');
  const f1Panel = page.locator('#panel-f1');
  const f2Panel = page.locator('#panel-f2');
  const f3Panel = page.locator('#panel-f3');
  const f4Panel = page.locator('#panel-f4');
  const f6Panel = page.locator('#panel-f6');
  const holdPanel = page.locator('#panel-hold');
  const veilPanel = page.locator('#panel-veil');
  const tlPanel = page.locator('#panel-timeline');
  const driftPanel = page.locator('#panel-drift');
  const sgPanel = page.locator('#panel-stagger');
  const flPanel = page.locator('#panel-framelink');
  const ornPanel = page.locator('#panel-ornament');

  // ---- 全画面 1枚（ヒーローの自動再生を止めて静止状態で撮る） ----
  if (dom.heroInitialized) {
    await page.evaluate(() => window.__gallery.hero.autoplay.stop());
    await page.waitForTimeout(800);
  }
  await page.screenshot({ path: path.join(SHOTS, 'full-page.png'), fullPage: true });
  log('shot: full-page.png (fullPage, 暗テーマ・自動再生停止の静止状態)');
  if (dom.heroInitialized) {
    await page.evaluate(() => window.__gallery.hero.autoplay.start());
  }

  // ---- ヒーロー: 自動再生の進行を3枚 ----
  if (dom.heroInitialized) {
    await hero.scrollIntoViewIfNeeded();
    await page.waitForFunction(() => !window.__gallery.hero.animating, undefined, { timeout: 15000, polling: 200 });
    await page.waitForTimeout(600);
    const names = ['hero-t1-autoplay.png', 'hero-t2-autoplay.png', 'hero-t3-autoplay.png'];
    let prev = null;
    for (let i = 0; i < names.length; i++) {
      if (i > 0) {
        await page.waitForFunction(
          (p) => window.__gallery.hero.realIndex !== p && !window.__gallery.hero.animating,
          prev,
          { timeout: 15000, polling: 200 }
        );
        await page.waitForTimeout(600);
      }
      prev = await page.evaluate(() => window.__gallery.hero.realIndex);
      await hero.screenshot({ path: path.join(SHOTS, names[i]) });
      log(`shot: ${names[i]} (realIndex=${prev})`);
    }

    // ホバーで一時停止 / 離脱で自動再開（DOMレベル検査）
    let box = await page.locator('.swiper--hero').boundingBox();
    const before = await page.evaluate(() => window.__gallery.hero.realIndex);
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.waitForTimeout(4300);
    const during = await page.evaluate(() => window.__gallery.hero.realIndex);
    await page.mouse.move(5, 5);
    await page.waitForTimeout(3800);
    const afterLeave = await page.evaluate(() => window.__gallery.hero.realIndex);
    log(`hover pause check: hover中 realIndex ${before} -> ${during} (${before === during ? '一時停止 OK' : '変化あり → 要確認'}) / 離脱後 ${during} -> ${afterLeave} (${during !== afterLeave ? '自動再開 OK' : '要確認'})`);
    check('hero hover pause', before === during, `${before} -> ${during}`);
    check('hero autoplay resumes', during !== afterLeave, `${during} -> ${afterLeave}`);
  } else {
    log('hero: Swiper 未読込のため自動再生の撮影を省略');
  }

  // ---- F-1: 改修後（容器の淡い切替） ----
  await f1Panel.scrollIntoViewIfNeeded();
  await page.fill('#f1-input', '灯');
  await page.waitForTimeout(600);
  await shot(f1Panel, 'f1-refined-filtered.png');
  const refined = await page.evaluate(() => {
    const g = window.__gallery;
    const visible = [...document.querySelectorAll('#f1-list .f1-row:not([hidden])')];
    return {
      persist: g.f1PersistCount(),
      visible: visible.length,
      visiblePersist: visible.filter((el) => el.dataset.persist).length,
      wrapOpacity: getComputedStyle(document.getElementById('f1-listwrap')).opacity
    };
  });
  check('F-1 refined: nodes not rebuilt', refined.persist === 61 && refined.visiblePersist === refined.visible,
    `persist=${refined.persist} visible=${refined.visible}/${refined.visiblePersist}`);

  await page.fill('#f1-input', '');
  await page.waitForTimeout(400);

  // ---- F-1: 従来方式（行を立て直して出現から再生） ----
  await page.click('[data-f1mode="legacy"]');
  await page.waitForTimeout(150);
  await page.fill('#f1-input', 'の');
  await page.waitForTimeout(250); // 遅延480ms+出現720ms の途中を捉える
  await shot(f1Panel, 'f1-conventional-settling.png');
  const legacyMid = await page.evaluate(() => {
    const rows = [...document.querySelectorAll('#f1-list .f1-row')];
    return {
      rows: rows.length,
      persistVisible: rows.filter((el) => el.dataset.persist).length,
      lastDelay: rows.length ? getComputedStyle(rows[rows.length - 1]).animationDelay : 'n/a',
      firstOpacity: rows.length ? getComputedStyle(rows[0]).opacity : 'n/a',
      lastOpacity: rows.length ? getComputedStyle(rows[rows.length - 1]).opacity : 'n/a'
    };
  });
  check('F-1 legacy: rows rebuilt (no persist)', legacyMid.persistVisible === 0,
    `rows=${legacyMid.rows} persist=${legacyMid.persistVisible}`);
  check('F-1 legacy: stagger reaches 480ms cap', legacyMid.lastDelay === '0.48s', legacyMid.lastDelay);
  check('F-1 legacy: settling in progress at 250ms', parseFloat(legacyMid.lastOpacity) < 1,
    `first=${legacyMid.firstOpacity} last=${legacyMid.lastOpacity}`);
  await page.waitForTimeout(1400);
  await shot(f1Panel, 'f1-conventional-settled.png');

  // 改修後に戻して初期化
  await page.click('[data-f1mode="refined"]');
  await page.fill('#f1-input', '');
  await page.waitForTimeout(500);

  // ---- F-2: ホバーでの浮き（応答層・2pxまで） ----
  await f2Panel.scrollIntoViewIfNeeded();
  const f2SecondRow = page.locator('#panel-f2 .f2-list .f2-row').nth(1);
  await f2SecondRow.hover();
  await page.waitForTimeout(400);
  await shot(f2Panel, 'f2-status.png');
  const f2Transform = await f2SecondRow.evaluate((el) => getComputedStyle(el).transform);
  log(`F-2 hover transform: ${f2Transform}`);
  check('F-2 hover lift = -2px', f2Transform.includes('-2'), f2Transform);
  await page.mouse.move(5, 5);

  // ---- F-3: カード押下 → 詳細プレビュー ----
  await f3Panel.scrollIntoViewIfNeeded();
  await page.locator('#f3-cards .f3-card').nth(3).click();
  await page.waitForTimeout(450);
  await shot(f3Panel, 'f3-detail.png');
  const f3Count1 = await page.evaluate(() => window.__gallery.markerCount);
  await page.locator('#f3-cards .f3-card').nth(5).click();
  await page.waitForTimeout(350);
  const f3Count2 = await page.evaluate(() => window.__gallery.markerCount);
  const f3DomMarkers = await page.evaluate(() => document.querySelectorAll('#f3-cards .is-marker').length);
  check('F-3 marker = 1 after 1st click', f3Count1 === 1, String(f3Count1));
  check('F-3 marker = 1 after 2nd click (moved)', f3Count2 === 1 && f3DomMarkers === 1, `count=${f3Count2} dom=${f3DomMarkers}`);

  // ---- F-4: 読み込み中 / 成功 / 失敗 / 0件(速い) ----
  await f4Panel.scrollIntoViewIfNeeded();
  await page.click('[data-f4="slow-ok"]');
  await page.waitForTimeout(750); // 300ms遅延 + 表示240ms のあと
  await shot(f4Panel, 'f4-loading.png');
  const f4LoadingText = await page.evaluate(() => document.getElementById('f4-stage').textContent);
  check('F-4 loading indicator shown', f4LoadingText.includes('読み込み中'), f4LoadingText.trim().slice(0, 20));
  await page.waitForTimeout(2300); // 成功結果の表示完了まで
  await shot(f4Panel, 'f4-success.png');
  const f4ResultCount = await page.evaluate(() => document.querySelectorAll('#f4-stage .f4-result li').length);
  check('F-4 success rows = 3', f4ResultCount === 3, String(f4ResultCount));

  await page.click('[data-f4="fail"]');
  await page.waitForTimeout(2500);
  await shot(f4Panel, 'f4-failure.png');
  const f4FailText = await page.evaluate(() => document.getElementById('f4-stage').textContent);
  check('F-4 failure state distinct', f4FailText.includes('失敗'), f4FailText.trim().slice(0, 20));

  await page.click('[data-f4="fast-empty"]');
  await page.waitForTimeout(600);
  await shot(f4Panel, 'f4-empty-fast.png');
  const f4EmptyText = await page.evaluate(() => document.getElementById('f4-stage').textContent);
  const f4HadLoading = await page.evaluate(() => !!document.querySelector('#f4-stage .f4-loading'));
  check('F-4 fast empty: no loading shown', f4EmptyText.includes('該当する記録がありません') && !f4HadLoading,
    f4EmptyText.trim().slice(0, 20));
  await page.click('[data-f4="idle"]');

  // ---- F-6: 0件 → 近い候補 ----
  await f6Panel.scrollIntoViewIfNeeded();
  await page.click('#f6-sample');
  await page.waitForTimeout(1100); // 呼吸層720ms + 遅れ60ms の完了まで
  await shot(f6Panel, 'f6-zero-suggestions.png');
  const f6State = await page.evaluate(() => ({
    zero: !!document.querySelector('#f6-stage .f6-zero'),
    chips: document.querySelectorAll('#f6-stage .f6-chip').length,
    zeroDelay: getComputedStyle(document.querySelector('#f6-stage .f6-zero')).animationDelay,
    zeroDur: getComputedStyle(document.querySelector('#f6-stage .f6-zero')).animationDuration
  }));
  check('F-6 zero card + suggestions', f6State.zero && f6State.chips >= 1, `chips=${f6State.chips}`);
  check('F-6 rise uses breath layer (720ms/10px)', f6State.zeroDur === '0.72s', `dur=${f6State.zeroDur} delay=${f6State.zeroDelay}`);

  // ---- 見送り案（静的カード） ----
  await shot(holdPanel, 'hold-cards.png');

  // ---- パネル7: 読み込み幕（§E-6: 幕は題字の animationend を待つ） ----
  await page.waitForFunction(() => window.__gallery.veilState.lifted === true, undefined, { timeout: 8000 });
  check('veil: curtain lifts after title animationend', true, 'initial run');
  await veilPanel.scrollIntoViewIfNeeded();
  await page.evaluate(() => window.__gallery.veilReplay());
  await page.waitForTimeout(500); // 紋章900ms の途中
  await veilPanel.screenshot({ path: path.join(SHOTS, 'veil-opening.png') });
  log('shot: veil-opening.png (再演・紋章描画中)');
  await page.waitForFunction(() => window.__gallery.veilState.lifted === true, undefined, { timeout: 8000 });
  await page.waitForTimeout(800); // 幕の持ち上がり完了
  await veilPanel.screenshot({ path: path.join(SHOTS, 'veil-closed.png') });
  log('shot: veil-closed.png (題字の終了を待って幕が開いた後)');

  // ---- パネル8: 年表（灯りのゆらぎ4.5s・縦線のスクロール連動・印は戻さない） ----
  await tlPanel.scrollIntoViewIfNeeded();
  await page.waitForTimeout(400);
  const tlInitial = await page.evaluate(() => window.__gallery.tlSeenCount());
  const tlLineBefore = await page.evaluate(() => window.__gallery.tlLineHeight());
  await page.evaluate(() => { document.getElementById('tl-scroller').scrollTo({ top: 9999 }); });
  await page.waitForTimeout(500);
  const tlAfter = await page.evaluate(() => window.__gallery.tlSeenCount());
  const tlLineAfter = await page.evaluate(() => window.__gallery.tlLineHeight());
  check('timeline: marks appear as items enter', tlAfter > tlInitial, `${tlInitial} -> ${tlAfter}`);
  check('timeline: rail line grows with scroll', parseFloat(tlLineAfter) > parseFloat(tlLineBefore), `${tlLineBefore} -> ${tlLineAfter}`);
  await page.evaluate(() => { document.getElementById('tl-scroller').scrollTo({ top: 0 }); });
  await page.waitForTimeout(300);
  const tlBack = await page.evaluate(() => window.__gallery.tlSeenCount());
  check('timeline: marks never reset (once seen)', tlBack === tlAfter, `${tlAfter} -> ${tlBack}`);
  const flickerDur = await page.evaluate(() => getComputedStyle(document.querySelector('.tl-dot')).animationDuration);
  check('timeline: flicker = 4.5s (breath-free ambient layer)', flickerDur === '4.5s', flickerDur);
  await shot(tlPanel, 'tl-scrolled.png');

  // ---- パネル9: 図形の漂い（46〜72秒・意図的な不揃い） ----
  const driftDur = await page.evaluate(() => window.__gallery.driftDurations());
  const driftUniq = new Set(driftDur);
  const driftInRange = driftDur.every((d) => { const s = parseFloat(d); return s >= 46 && s <= 72; });
  check('drift: 6 shapes all have different periods', driftUniq.size === driftDur.length, driftDur.join(','));
  check('drift: periods within 46-72s (§B-1)', driftInRange, driftDur.join(','));
  await shot(driftPanel, 'drift-shapes.png');

  // ---- パネル10: 出現の時間差（E-4: 1枚ずつでは従来に遅れが出ない） ----
  await sgPanel.scrollIntoViewIfNeeded();
  await page.evaluate(() => window.__gallery.sgRun('slow'));
  await page.waitForTimeout(12 * 420 + 1100); // 1枚ずつの再生＋出現の完了
  const sgSlowLegacy = await page.evaluate(() => window.__gallery.sgDelays('legacy'));
  const sgSlowIndexed = await page.evaluate(() => window.__gallery.sgDelays('indexed'));
  check('E-4 slow: legacy delays all 0 (no stagger)', sgSlowLegacy.every((d) => parseFloat(d) === 0), sgSlowLegacy.join(','));
  check('E-4 slow: indexed delays > 0 (stagger works)', sgSlowIndexed.some((d) => parseFloat(d) > 0), sgSlowIndexed.join(','));
  await shot(sgPanel, 'sg-slow.png');
  await page.evaluate(() => window.__gallery.sgRun('burst'));
  await page.waitForTimeout(1000);
  const sgBurstLegacy = await page.evaluate(() => window.__gallery.sgDelays('legacy'));
  const sgBurstIndexed = await page.evaluate(() => window.__gallery.sgDelays('indexed'));
  check('E-4 burst: both columns get stagger', parseFloat(sgBurstLegacy[11]) > 0 && parseFloat(sgBurstIndexed[11]) > 0,
    `last=${sgBurstLegacy[11]} / ${sgBurstIndexed[11]}`);
  await shot(sgPanel, 'sg-burst.png');

  // ---- パネル11: 額の接続（標準API or 240msフォールバック・目印は常に1つ） ----
  const hasVT = await page.evaluate(() => typeof document.startViewTransition === 'function');
  log(`frame-link: document.startViewTransition = ${hasVT}`);
  await flPanel.scrollIntoViewIfNeeded();
  await page.locator('#fl-cards .fl-card').nth(2).click();
  await page.waitForTimeout(90); // 接続の開始直後
  await flPanel.screenshot({ path: path.join(SHOTS, 'fl-connecting.png') });
  log('shot: fl-connecting.png (額の接続の途中)');
  await page.waitForFunction(() => window.__gallery.flMethod && window.__gallery.flMethod.length > 0, undefined, { timeout: 5000 });
  const flMethod = await page.evaluate(() => window.__gallery.flMethod);
  const flMarker = await page.evaluate(() => window.__gallery.flMarkerCount);
  check('frame-link: connection method reported', !!flMethod, flMethod);
  check('frame-link: method matches capability (§D)', hasVT ? flMethod.indexOf('view-transition') === 0 : true, `${hasVT} / ${flMethod}`);
  check('frame-link: marker = 1 (§B-3)', flMarker === 1, String(flMarker));
  await page.waitForTimeout(400);
  await flPanel.screenshot({ path: path.join(SHOTS, 'fl-after.png') });
  log('shot: fl-after.png (詳細の額への接続後)');

  // ---- パネル12: 装飾の部品（四隅の飾りの出現・呼吸層） ----
  await ornPanel.scrollIntoViewIfNeeded();
  await page.evaluate(() => window.__gallery.ornReplay());
  await page.waitForTimeout(250); // 出現の途中
  await ornPanel.screenshot({ path: path.join(SHOTS, 'orn-rising.png') });
  log('shot: orn-rising.png (四隅の飾りの出現・呼吸層の途中)');
  await page.waitForTimeout(900);
  const ornDur = await page.evaluate(() => getComputedStyle(document.querySelector('.orn-corner')).animationDuration);
  const ornVisible = await page.evaluate(() =>
    [...document.querySelectorAll('.orn-corner')].every((el) => !el.classList.contains('is-hidden')));
  check('ornament: rise uses breath layer (720ms)', ornDur === '0.72s', ornDur);
  check('ornament: corners visible after replay', ornVisible, String(ornVisible));

  // ---- 動きを減らす設定（シミュレーション） ----
  await page.locator('.switch').click();
  await page.waitForTimeout(400);
  const rm = await page.evaluate(() => {
    const g = window.__gallery;
    const dur = getComputedStyle(document.getElementById('panel-f2')).animationDuration;
    return {
      cls: document.documentElement.classList.contains('reduce-motion'),
      panelDur: dur,
      autoplayRunning: g.hero ? g.hero.autoplay.running : 'n/a',
      heroSpeed: g.hero ? g.hero.params.speed : 'n/a'
    };
  });
  log('--- 動きを減らす設定 適用時 ---');
  log(JSON.stringify(rm, null, 2));
  check('reduce-motion class applied', rm.cls === true);
  check('reduce-motion: animation durations ~0', parseFloat(rm.panelDur) < 0.01, rm.panelDur);
  if (dom.heroInitialized) {
    check('reduce-motion: hero autoplay stopped', rm.autoplayRunning === false, String(rm.autoplayRunning));
    check('reduce-motion: hero speed = 0', rm.heroSpeed === 0, String(rm.heroSpeed));
  }
  await shot(hero, 'rm-hero.png');

  // 従来方式の絞り込みが遅延0・即時になること（§B-5）
  await f1Panel.scrollIntoViewIfNeeded();
  await page.click('[data-f1mode="legacy"]');
  await page.fill('#f1-input', '点検');
  await page.waitForTimeout(250);
  await shot(f1Panel, 'rm-f1-conventional.png');
  const rmF1 = await page.evaluate(() => {
    const rows = [...document.querySelectorAll('#f1-list .f1-row')];
    return {
      rows: rows.length,
      lastDelay: rows.length ? getComputedStyle(rows[rows.length - 1]).animationDelay : 'n/a',
      lastOpacity: rows.length ? getComputedStyle(rows[rows.length - 1]).opacity : 'n/a'
    };
  });
  check('reduce-motion: JS-written delays = 0', rmF1.lastDelay === '0s', rmF1.lastDelay);
  check('reduce-motion: rows appear instantly', parseFloat(rmF1.lastOpacity) === 1, `opacity=${rmF1.lastOpacity}`);
  await page.fill('#f1-input', '');
  await page.waitForTimeout(200);

  // 新パネルの動きを減らす設定検査（§A-4 全ページ必須）
  await page.evaluate(() => window.__gallery.veilReplay());
  await page.waitForTimeout(250);
  const rmVeilLifted = await page.evaluate(() => window.__gallery.veilState.lifted);
  check('reduce-motion: veil lifts immediately', rmVeilLifted === true, String(rmVeilLifted));

  await page.evaluate(() => window.__gallery.sgRun('burst'));
  await page.waitForTimeout(350);
  const rmSg = await page.evaluate(() => window.__gallery.sgDelays('indexed'));
  check('reduce-motion: stagger delays = 0', rmSg.every((d) => parseFloat(d) === 0), rmSg.join(','));

  await page.locator('#fl-cards .fl-card').nth(3).click();
  await page.waitForTimeout(200);
  const rmFlMethod = await page.evaluate(() => window.__gallery.flMethod);
  check('reduce-motion: frame-link switches instantly', (rmFlMethod || '').indexOf('即時') === 0, rmFlMethod);

  const rmLine = await page.evaluate(() => window.__gallery.tlLineHeight());
  const rmListH = await page.evaluate(() => document.getElementById('tl-list').offsetHeight);
  check('reduce-motion: timeline line starts full length (§B-5)', Math.abs(parseFloat(rmLine) - rmListH) < 2, `${rmLine} vs list ${rmListH}px`);
  const rmDurs = await page.evaluate(() => ({
    drift: getComputedStyle(document.querySelector('.drift-shape')).animationDuration,
    flicker: getComputedStyle(document.querySelector('.tl-dot')).animationDuration
  }));
  check('reduce-motion: drift + flicker stopped', parseFloat(rmDurs.drift) < 0.01 && parseFloat(rmDurs.flicker) < 0.01, JSON.stringify(rmDurs));
  await page.evaluate(() => window.__gallery.sgRun('slow'));
  await page.waitForTimeout(400);
  const rmSgSlow = await page.evaluate(() => window.__gallery.sgDelays('legacy').concat(window.__gallery.sgDelays('indexed')));
  check('reduce-motion: slow mode also instant (delay 0)', rmSgSlow.every((d) => parseFloat(d) === 0), `${rmSgSlow.length} cards`);

  // fullPage（動きを減らす設定適用時）— stickyバーの描画ずれ防止のため最上部へ戻してから撮る
  await page.click('[data-f1mode="refined"]');
  await page.evaluate(() => { window.__gallery.f4Run('idle'); });
  await page.fill('#f6-input', '');
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(300);
  await page.screenshot({ path: path.join(SHOTS, 'rm-full-page.png'), fullPage: true });
  log('shot: rm-full-page.png (fullPage, 動きを減らす設定適用時)');

  await page.locator('.switch').click(); // 戻す
  await page.waitForTimeout(300);

  // ---- 明テーマ ----
  await page.click('#theme-light');
  await page.waitForTimeout(700); // テーマ切替の一括変化400ms の完了まで
  const themeBg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
  log(`light theme body bg: ${themeBg}`);
  check('light theme applied', themeBg !== 'rgb(11, 13, 18)', themeBg);
  await shot(hero, 'light-hero.png');
  await shot(f2Panel, 'light-f2.png');
  if (dom.heroInitialized) await page.evaluate(() => window.__gallery.hero.autoplay.stop());
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(400);
  await page.screenshot({ path: path.join(SHOTS, 'light-full-page.png'), fullPage: true });
  log('shot: light-full-page.png (fullPage, 明テーマ)');
  if (dom.heroInitialized) await page.evaluate(() => window.__gallery.hero.autoplay.start());
  await page.click('#theme-dark');

  // ---- コンソールの集計と保存 ----
  const errors = consoleLines.filter((l) =>
    l.startsWith('[error]') || l.startsWith('[pageerror]') || l.startsWith('[requestfailed]')
  );
  log(`console: ${consoleLines.length} line(s), errors: ${errors.length}`);
  log(`checks: ${failures.length === 0 ? 'ALL OK' : failures.length + ' FAILED'}`);
  if (failures.length) failures.forEach((f) => log('  ' + f));

  fs.writeFileSync(
    path.join(SHOTS, 'console-report.txt'),
    [
      'モーションギャラリー 撮影レポート',
      `撮影日時: ${new Date().toLocaleString('ja-JP')}`,
      '',
      ...report,
      '',
      `--- console messages (${consoleLines.length}) ---`,
      ...(consoleLines.length ? consoleLines : ['(なし)']),
      '',
      errors.length === 0
        ? 'CONSOLE ERRORS: none'
        : 'CONSOLE ERRORS:\n' + errors.join('\n')
    ].join('\n'),
    'utf8'
  );
  log('report: shots/console-report.txt');

  await browser.close();
  if (failures.length) process.exitCode = 2;
})().catch((e) => {
  console.error('CAPTURE FAILED:', e);
  process.exit(1);
});
