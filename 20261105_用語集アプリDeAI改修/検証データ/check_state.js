async (page) => {
  // 用語集アプリの動作確認(3/4): operate_flows.js の後に実行する読み取りだけの確認。何度実行してもデータは変わらない。
  // 各操作の結果・検索と絞り込み・並べ替え・関連語の向き・見直し・CSV出力を集める。
  const BASE = 'http://127.0.0.1:8000';
  const log = [];
  const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const clean = (s) => (s || '').replace(/\s+/g, ' ').trim();
  async function openTerm(hw, status = '') {
    await page.goto(BASE + '/terms?q=' + encodeURIComponent(hw) + (status ? '&status=' + status : ''));
    const link = page.locator('a.hw').filter({ hasText: new RegExp('^' + esc(hw) + '$') }).first();
    await page.goto(BASE + (await link.getAttribute('href')));
  }
  const text = async (sel) => ((await page.locator(sel).count()) ? clean(await page.locator(sel).first().innerText()) : null);

  // A. 書き込み操作の結果
  await openTerm('段取り替え');
  log.push({ step: '段取り替え 評価の表示', hint: await text('section.evaluate p.hint'), comments: await text('ul.ev-comments') });
  await openTerm('リフロー');
  log.push({ step: 'リフロー 評価の表示', hint: await text('section.evaluate p.hint') });
  await openTerm('はんだペースト');
  log.push({ step: 'はんだペースト 注記', scope: await text('article.sense p.scope'), meta: await text('dl.meta') });
  await openTerm('棚卸');
  log.push({ step: '棚卸 語義と警告', senses: (await page.locator('article.sense h3').allInnerTexts()).map(clean), warn: await text('main p.warn') });
  await openTerm('フィーダ');
  log.push({ step: 'フィーダ 英語', meta: await text('dl.meta') });
  await openTerm('ロット');
  log.push({ step: 'ロット 競合後の英語', meta: await text('dl.meta') });
  await openTerm('リフロ', 'archived');
  log.push({ step: 'リフロ 状態', h1: await text('h1') });

  // B. 検索・絞り込み・並べ替え
  for (const q of ['ひょうめん', 'reflow', 'BOM', 'ペースト', 'AOI', 'はんだ', 'けんさ', '検査']) {
    await page.goto(BASE + '/terms?q=' + encodeURIComponent(q));
    log.push({ step: `検索 ${q}`, hits: await page.locator('#terms-table a.hw').allInnerTexts() });
  }
  await page.goto(BASE + '/terms?tag=' + encodeURIComponent('品質'));
  log.push({ step: 'タグ 品質', hits: await page.locator('#terms-table a.hw').allInnerTexts() });
  await page.goto(BASE + '/terms?status=archived');
  log.push({ step: '状態 アーカイブ済み', hits: await page.locator('#terms-table a.hw').allInnerTexts() });
  await page.goto(BASE + '/terms?sort=reading&direction=asc');
  log.push({ step: '読みで並べ替え', hits: await page.locator('#terms-table a.hw').allInnerTexts() });
  await page.goto(BASE + '/terms');
  log.push({ step: '一覧 統計', stats: await text('section.stats'), count: await text('.table-tools p'),
    tags: await page.locator('#tag option').allInnerTexts() });

  // C. 関連語の向き（上位概念・下位概念が相手側でどう見えるか）
  for (const hw of ['表面実装', 'リフロー', '自動光学検査', 'X線検査']) {
    await openTerm(hw);
    const rel = await page.evaluate(() => {
      const out = [];
      const h2 = [...document.querySelectorAll('main h2')].find((h) => h.textContent.trim() === '関連語');
      let el = h2 ? h2.nextElementSibling : null;
      while (el && el.tagName !== 'DETAILS' && el.tagName !== 'H2') {
        out.push(el.tagName + ': ' + el.innerText.replace(/\s+/g, ' ').trim());
        el = el.nextElementSibling;
      }
      const conf = document.querySelector('section.confused');
      return { related: out, confused: conf ? conf.innerText.replace(/\s+/g, ' ').trim() : null };
    });
    log.push({ step: `関連語の表示 ${hw}`, ...rel });
  }

  // D. 見直し
  await page.goto(BASE + '/review?kind=needs_fix');
  log.push({ step: '見直し 修正が必要', kinds: await page.locator('nav.review-kinds a').allInnerTexts(),
    rows: (await page.locator('table tbody tr').allInnerTexts()).map(clean) });

  // E. CSV 出力（BOM・件数・英語の値が混ざっていないか）
  const res = await page.request.get(BASE + '/export.csv');
  const buf = await res.body();
  const lines = buf.toString('utf8').split(/\r?\n/).filter(Boolean);
  log.push({
    step: 'CSV出力', status: res.status(), disposition: res.headers()['content-disposition'],
    bom: buf[0] === 0xef && buf[1] === 0xbb && buf[2] === 0xbf, rows: lines.length - 1,
    header: lines[0].replace(/^\ufeff/, ''),
    sample: lines.filter((l) => /^(棚卸|自動光学検査|表面実装|リフロー),/.test(l)),
  });
  return log;
}
