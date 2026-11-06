async (page) => {
  // 用語集アプリの動作確認(2/4): register_terms.js で登録した語を使い、日常の書き込み操作を一通り行う。
  // 関連語・評価・語義の編集・用語の編集・アーカイブ・同時編集の競合。読み取りの確認は check_state.js で行う。
  // （1本にまとめると MCP の応答待ちが時間切れになり、結果を受け取れなかったため分割した。2026-11-05）
  // POST の応答でしか出ない画面（エラー・競合）は、その場で撮影する。撮影先は SHOTS（フォルダは事前に作る）。
  const BASE = 'http://127.0.0.1:8000';
  const SHOTS = 'C:/Users/ss80751/kohden-code-workspace/20261105_用語集アプリDeAI改修/shots/' + (globalThis.__GLOSSARY_ROUND || 'p1') + '/';
  const log = [];
  const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const clean = (s) => (s || '').replace(/\s+/g, ' ').trim();

  async function openTerm(hw) {
    await page.goto(BASE + '/terms?q=' + encodeURIComponent(hw));
    const link = page.locator('a.hw').filter({ hasText: new RegExp('^' + esc(hw) + '$') }).first();
    const href = await link.getAttribute('href');
    await page.goto(BASE + href);
    return href;
  }
  async function submit(p, locator) {
    await Promise.all([p.waitForNavigation({ waitUntil: 'load' }), locator.click()]);
  }
  async function state(p) {
    const err = p.locator('main .error');
    return {
      url: p.url().replace(BASE, ''),
      h1: clean(await p.locator('h1').first().innerText()),
      error: (await err.count()) ? clean(await err.first().innerText()) : null,
    };
  }

  // 1. 関連語（最後の1件は未登録の語。エラー画面の文言を確かめる）
  const RELS = [
    ['自動光学検査', 'confused_with', 'X線検査'],
    ['マウンタ', 'related', 'フィーダ'],
    ['はんだペースト', 'related', 'メタルマスク'],
    ['部品表', 'related', '設計変更通知'],
    ['ロット', 'related', 'トレーサビリティ'],
    ['表面実装', 'narrower', 'リフロー'],
    ['表面実装', 'related', '挿入実装'],
  ];
  for (const [from, type, to] of RELS) {
    await openTerm(from);
    await page.locator('details > summary', { hasText: '関連語を追加する' }).click();
    await page.selectOption('#rel-type', type);
    await page.fill('#rel-other', to);
    await submit(page, page.locator('form[action$="/relations"] button[type=submit]'));
    const st = await state(page);
    log.push({ step: `関連語 ${from} -[${type}]-> ${to}`, ...st });
    if (st.h1.includes('処理できませんでした')) {
      await page.screenshot({ path: SHOTS + 'error-relation-unregistered.png', fullPage: true });
    }
  }

  // 2. 評価（正しい・役に立つ／修正が必要＋理由）
  await openTerm('リフロー');
  await submit(page, page.locator('form.ev-form').first().locator('button[name=accuracy][value=correct]'));
  log.push({ step: '評価 リフロー 正しい', ...(await state(page)) });
  await submit(page, page.locator('form.ev-form').first().locator('button[name=usefulness][value=useful]'));
  log.push({ step: '評価 リフロー 役に立つ', ...(await state(page)) });
  await openTerm('段取り替え');
  await page.locator('form.ev-form').first().locator('input[name=comment]')
    .fill('後半の「時間の短縮が改善の対象になる」は定義から外し、注記に移したほうがよい。');
  await submit(page, page.locator('form.ev-form').first().locator('button[name=accuracy][value=needs_fix]'));
  log.push({ step: '評価 段取り替え 修正が必要', ...(await state(page)) });

  // 3. 語義の編集（注記の追加／係争中へ変更）
  await openTerm('はんだペースト');
  await submit(page, page.locator('a', { hasText: 'この語義を編集' }).first());
  await page.fill('#scope_note', '保管温度と、常温に戻すまでの時間は、使う製品の指定に従う。');
  await page.fill('#change_reason', '保管の扱いを注記に追加');
  await submit(page, page.locator('form.edit button[type=submit]'));
  log.push({ step: '語義の編集 はんだペースト 注記追加', ...(await state(page)) });
  await openTerm('棚卸');
  await submit(page, page.locator('a', { hasText: 'この語義を編集' }).first());
  await page.selectOption('#status', 'disputed');
  await page.fill('#change_reason', '経理と物流で指す作業の範囲が違うという指摘があったため');
  await submit(page, page.locator('form.edit button[type=submit]'));
  log.push({ step: '語義の編集 棚卸(1) 係争中', ...(await state(page)) });

  // 4. 用語の編集（英語表記の追加）
  await openTerm('フィーダ');
  await submit(page, page.locator('a', { hasText: '読み・英語・略語を編集' }));
  await page.fill('#english', 'feeder');
  await page.fill('#change_reason', '英語表記を追加');
  await submit(page, page.locator('form.edit button[type=submit]'));
  log.push({ step: '用語の編集 フィーダ 英語追加', ...(await state(page)) });

  // 5. アーカイブ（表記ゆれの重複登録）
  await openTerm('リフロ');
  await page.locator('details > summary', { hasText: 'この用語をアーカイブする' }).click();
  await page.fill('#arch-reason', '「リフロー」の表記ゆれで、重複して登録したため');
  await submit(page, page.locator('form[action$="/archive"] button[type=submit]'));
  log.push({ step: 'アーカイブ リフロ', ...(await state(page)) });

  // 6. 同時編集の競合（2つの画面で同じ用語を開き、後から保存した側が 409 になる）
  const lotHref = await openTerm('ロット');
  const p2 = await page.context().newPage();
  await p2.setViewportSize({ width: 1280, height: 900 });
  await page.goto(BASE + lotHref + '/edit');
  await p2.goto(BASE + lotHref + '/edit');
  await page.fill('#english', 'lot (batch)');
  await page.fill('#change_reason', '英語表記に batch を併記');
  await submit(page, page.locator('form.edit button[type=submit]'));
  log.push({ step: '競合 画面A 保存', ...(await state(page)) });
  await p2.fill('#english', 'production lot');
  await p2.fill('#change_reason', '英語表記を修正');
  await submit(p2, p2.locator('form.edit button[type=submit]'));
  log.push({ step: '競合 画面B 保存', ...(await state(p2)),
    diff: (await p2.locator('pre.diff').count()) ? (await p2.locator('pre.diff').innerText()) : null });
  await p2.screenshot({ path: SHOTS + 'conflict-light-1280.png', fullPage: true });
  await p2.close();
  return log;
}
