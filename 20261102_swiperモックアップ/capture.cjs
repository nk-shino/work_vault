/**
 * Swiper モックアップ 撮影スクリプト（Playwright / headless Chromium）
 * - fullPage 1枚
 * - 基本パネルを数秒空けて3枚（自動再生で表示スライドが変わる証拠）
 * - ホバー一時停止・自動再開をDOMレベルで検査
 * - フェード / カバー フローは矢印クリック後に1枚ずつ
 * - コンソールメッセージとDOM検査の結果を shots/console-report.txt に保存
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
  await page.waitForTimeout(1800); // フォント・初回遷移の落ち着き待ち

  // ---- DOM検査: Swiperの初期化・スライド枚数 ----
  const dom = await page.evaluate(() => {
    const d = window.__swiperDemo || {};
    const out = {
      swiperGlobal: typeof window.Swiper !== 'undefined' ? (window.Swiper.version || 'loaded') : 'NOT LOADED',
      containerCount: document.querySelectorAll('.swiper').length,
      panels: {}
    };
    for (const key of ['base', 'fade', 'cover']) {
      const s = d[key];
      out.panels[key] = s
        ? { initialized: true, slides: s.slides.length, realIndex: s.realIndex, effect: s.params.effect, loop: s.params.loop }
        : { initialized: false };
    }
    return out;
  });
  log('--- DOM checks ---');
  log(JSON.stringify(dom, null, 2));

  // ---- 全画面 1枚（遷移中に撮れないよう、いったん自動再生を止めて静止状態で撮る） ----
  await page.evaluate(() => window.__swiperDemo.base.autoplay.stop());
  await page.waitForTimeout(800);
  await page.screenshot({ path: path.join(SHOTS, 'full-page.png'), fullPage: true });
  log('shot: full-page.png (fullPage, 自動再生停止中の静止状態)');
  await page.evaluate(() => window.__swiperDemo.base.autoplay.start());

  // ---- 基本パネル: 自動再生の進行を3枚 ----
  const basePanel = page.locator('#panel-base');
  await basePanel.scrollIntoViewIfNeeded();
  // 初回ショットの前に遷移が完全に終わっていることを待つ
  await page.waitForFunction(() => !window.__swiperDemo.base.animating, undefined, { timeout: 15000, polling: 200 });
  await page.waitForTimeout(600);
  const baseShots = ['base-t1-autoplay.png', 'base-t2-autoplay.png', 'base-t3-autoplay.png'];
  let prev = null;
  for (let i = 0; i < baseShots.length; i++) {
    if (i > 0) {
      // realIndex が変わり、かつ遷移が完了するまで待つ（= 自動再生で動いている証拠）
      await page.waitForFunction(
        (p) => window.__swiperDemo.base.realIndex !== p && !window.__swiperDemo.base.animating,
        prev,
        { timeout: 15000, polling: 200 }
      );
      await page.waitForTimeout(600);
    }
    prev = await page.evaluate(() => window.__swiperDemo.base.realIndex);
    await basePanel.screenshot({ path: path.join(SHOTS, baseShots[i]) });
    log(`shot: ${baseShots[i]} (realIndex=${prev})`);
  }

  // ---- ホバーで一時停止 / 離脱で自動再開（DOMレベル検査） ----
  await basePanel.scrollIntoViewIfNeeded();
  let box = await page.locator('.swiper--base').boundingBox();
  const before = await page.evaluate(() => window.__swiperDemo.base.realIndex);
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.waitForTimeout(4300); // 1周期(約3.65秒)より長く待つ
  const during = await page.evaluate(() => window.__swiperDemo.base.realIndex);
  await page.mouse.move(5, 5);
  await page.waitForTimeout(3800);
  const afterLeave = await page.evaluate(() => window.__swiperDemo.base.realIndex);
  log(`hover pause check: hover中 realIndex ${before} -> ${during} (${before === during ? '一時停止 OK' : '変化あり → 要確認'}) / 離脱後 ${during} -> ${afterLeave} (${during !== afterLeave ? '自動再開 OK' : '要確認'})`);

  // ---- フェードパネル: 矢印クリック後 ----
  await page.mouse.move(5, 5);
  const fadePanel = page.locator('#panel-fade');
  await fadePanel.scrollIntoViewIfNeeded();
  await page.locator('.swiper--fade .swiper-button-next').click();
  await page.waitForTimeout(1400); // speed 900ms の完了待ち
  await fadePanel.screenshot({ path: path.join(SHOTS, 'fade-after-next.png') });
  log('shot: fade-after-next.png');

  // ---- カバー フローパネル: 矢印クリック後 ----
  const coverPanel = page.locator('#panel-cover');
  await coverPanel.scrollIntoViewIfNeeded();
  await page.locator('.swiper--cover .swiper-button-next').click();
  await page.waitForTimeout(1200); // speed 700ms の完了待ち
  await coverPanel.screenshot({ path: path.join(SHOTS, 'cover-after-next.png') });
  log('shot: cover-after-next.png');

  // ---- コンソールの集計と保存 ----
  const errors = consoleLines.filter((l) =>
    l.startsWith('[error]') || l.startsWith('[pageerror]') || l.startsWith('[requestfailed]')
  );
  log(`console: ${consoleLines.length} line(s), errors: ${errors.length}`);

  fs.writeFileSync(
    path.join(SHOTS, 'console-report.txt'),
    [
      'Swiper モックアップ 撮影レポート',
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
})().catch((e) => {
  console.error('CAPTURE FAILED:', e);
  process.exit(1);
});
