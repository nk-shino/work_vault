async (page) => {
  // 用語集アプリの動作確認(4/4): 主要画面を明暗 × 1280/375 で撮影する。読み取りだけで、データは変えない。
  // 統計の数え上げ演出は prefers-reduced-motion で止める（app.js:55 が尊重する）。
  // 撮影先: shots/<round>/<画面>-<light|dark>-<幅>.png（round は globalThis.__GLOSSARY_ROUND、既定 p1）
  const BASE = 'http://127.0.0.1:8000';
  const SHOTS = 'C:/Users/ss80751/kohden-code-workspace/20261105_用語集アプリDeAI改修/shots/' + (globalThis.__GLOSSARY_ROUND || 'p1') + '/';
  const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  await page.emulateMedia({ colorScheme: 'light', reducedMotion: 'reduce' });
  await page.setViewportSize({ width: 1280, height: 900 });
  async function termHref(hw) {
    await page.goto(BASE + '/terms?q=' + encodeURIComponent(hw));
    return page.locator('a.hw').filter({ hasText: new RegExp('^' + esc(hw) + '$') }).first().getAttribute('href');
  }
  async function linkOn(path, selector) {
    await page.goto(BASE + path);
    const a = page.locator(selector).first();
    return (await a.count()) ? a.getAttribute('href') : null;
  }
  const tana = await termHref('棚卸');
  const aoi = await termHref('自動光学検査');
  const smt = await termHref('表面実装');
  const feeder = await termHref('フィーダ');
  const paste = await termHref('はんだペースト');
  const lot = await termHref('ロット');
  const targets = [
    ['list', '/terms'],
    ['detail-tanaoroshi', tana],
    ['detail-aoi', aoi],
    ['detail-smt', smt],
    ['new', '/new'],
    ['term-edit', feeder + '/edit'],
    ['sense-edit', await linkOn(paste, 'a[href^="/senses/"][href$="/edit"]')],
    ['proposals', '/proposals'],
    ['proposal-edit', await linkOn('/proposals', 'a[href^="/proposals/"][href$="/edit"]')],
    ['review', '/review?kind=needs_fix'],
    ['history', await linkOn(lot, 'a[href^="/history/"]')],
  ].filter(([, p]) => p);
  const saved = [];
  for (const theme of ['light', 'dark']) {
    await page.emulateMedia({ colorScheme: theme, reducedMotion: 'reduce' });
    for (const width of [1280, 375]) {
      await page.setViewportSize({ width, height: width === 1280 ? 900 : 812 });
      for (const [name, path] of targets) {
        await page.goto(BASE + path);
        const file = `${name}-${theme}-${width}.png`;
        await page.screenshot({ path: SHOTS + file, fullPage: true });
        saved.push(file);
      }
    }
  }
  await page.emulateMedia({ colorScheme: 'light', reducedMotion: null });
  await page.setViewportSize({ width: 1280, height: 900 });
  return { targets, saved: saved.length };
}
