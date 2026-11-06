async (page) => {
  // 用語集アプリの動作確認: 提案キューの操作（書き込みあり）。tasks.py import の後に1回だけ実行する。
  // キーボード（j/k/x/r）、採用できない関係提案の採用、一括採用（モック草案で中止）、修正して採用 2 件、関係の採用、却下。
  const BASE = 'http://127.0.0.1:8000';
  const SHOTS = 'C:/Users/ss80751/kohden-code-workspace/20261105_用語集アプリDeAI改修/shots/' + (globalThis.__GLOSSARY_ROUND || 'p1') + '/';
  const log = [];
  const clean = (s) => (s || '').replace(/\s+/g, ' ').trim();
  async function nav(action) {
    await Promise.all([page.waitForNavigation({ waitUntil: 'load' }), action()]);
  }
  async function state() {
    const box = page.locator('main .error, main p.warn, main .notice, main [role=alert]');
    return {
      url: page.url().replace(BASE, ''),
      h1: clean(await page.locator('h1').first().innerText()),
      msg: (await box.count()) ? clean(await box.first().innerText()) : null,
    };
  }
  // 見出し（h2 の先頭の語と種類）で提案カードを探す。未処理の提案を全ページめくる
  async function findCard(label, kind) {
    let url = BASE + '/proposals?status=pending';
    for (let i = 0; i < 8; i++) {
      await page.goto(url);
      const id = await page.evaluate(([label, kind]) => {
        for (const h of document.querySelectorAll('article.proposal h2')) {
          if (h.textContent.replace(/\s+/g, ' ').trim().startsWith(label + ' ' + kind)) return h.id;
        }
        return null;
      }, [label, kind]);
      if (id) return page.locator(`article.proposal[aria-labelledby="${id}"]`);
      const next = page.locator('nav.pager a[rel=next]');
      if (!(await next.count())) return null;
      url = BASE + (await next.getAttribute('href'));
    }
    return null;
  }
  async function adopt(label, definition, tag) {
    const card = await findCard(label, '語義');
    if (!card) { log.push({ step: `修正して採用 ${label}`, error: '提案が見つからない' }); return; }
    await page.goto(BASE + (await card.locator('a[href$="/edit"]').getAttribute('href')));
    await page.fill('#definition', definition);
    await page.fill('#context_tag', tag);
    await page.fill('#change_reason', 'モックの定義を、用例に基づいて書き直した');
    await nav(() => page.locator('form.edit button.primary').click());
    log.push({ step: `修正して採用 ${label}`, ...(await state()) });
  }

  // 1. キーボード操作（1頁目）: j で移動、x で選択の切り替え、r で却下
  await page.goto(BASE + '/proposals');
  await page.evaluate(() => document.activeElement && document.activeElement.blur());
  const total0 = clean(await page.locator('main > p').first().innerText());
  await page.keyboard.press('j');
  const s1 = clean(await page.locator('#knav-status').textContent());
  await page.keyboard.press('j');
  const s2 = clean(await page.locator('#knav-status').textContent());
  await page.keyboard.press('x');
  const sel1 = clean(await page.locator('#bulk-count').innerText());
  await page.keyboard.press('x');
  const sel0 = clean(await page.locator('#bulk-count').innerText());
  await nav(() => page.keyboard.press('r'));
  log.push({ step: 'キーボード j/j/x/x/r', before: total0, status1: s1, status2: s2, selected: sel1, unselected: sel0,
    after: clean(await page.locator('main > p').first().innerText()), ...(await state()) });

  // 2. 両端の語が未登録の関係提案を採用する（エラーになるはず）
  const bad = await findCard('BGA ⇔ 不良', '関係');
  if (bad) {
    await nav(() => bad.locator('form[data-kaction="accept"] button').click());
    log.push({ step: '採用できない関係提案 BGA ⇔ 不良', ...(await state()) });
    await page.screenshot({ path: SHOTS + 'error-relation-accept-unregistered.png', fullPage: true });
  }

  // 3. 一括採用にモック草案を含める（中止されるはず）
  const anySense = await findCard('BGA', '語義');
  if (anySense) {
    const boxes = page.locator('article.proposal[data-protected="1"] input[name=ids]');
    const n = Math.min(3, await boxes.count());
    for (let i = 0; i < n; i++) await boxes.nth(i).check();
    const warnShown = await page.locator('#bulk-warn').isVisible();
    const count = clean(await page.locator('#bulk-count').innerText());
    await nav(() => page.locator('#bulk-bar-form button[name=action][value=accept]').click());
    const main = clean(await page.locator('main').innerText());
    log.push({ step: '一括採用 モック草案3件', checked: n, warnShown, count, url: page.url().replace(BASE, ''),
      message: main.slice(0, 160) });
  }

  // 4. 修正して採用（新しい語 2 件）
  await adopt('ブリッジ', 'はんだ付けの不良の一つ。隣り合う電極やリードの間が、余分なはんだでつながってしまう状態。', '品質');
  await adopt('BGA', '部品の裏面に格子状に並べたはんだボールで、基板と接続するパッケージ。接合部が部品の下に隠れるため、外観からは確認できない。', '製造');

  // 5. 両端に語義ができた関係提案を採用する
  const ok = await findCard('BGA ⇔ ブリッジ', '関係');
  if (ok) {
    await nav(() => ok.locator('form[data-kaction="accept"] button').click());
    log.push({ step: '関係提案の採用 BGA ⇔ ブリッジ', ...(await state()) });
  }

  // 6. 断り書きから拾われた語の候補を却下する
  const noise = await findCard('作例', '語義');
  if (noise) {
    await nav(() => noise.locator('form[data-kaction="reject"] button').click());
    log.push({ step: '却下 作例', ...(await state()) });
  }

  await page.goto(BASE + '/proposals');
  log.push({ step: '操作後の提案キュー', total: clean(await page.locator('main > p').first().innerText()),
    badge: clean(await page.locator('header nav a[href="/proposals"]').innerText()) });
  await page.screenshot({ path: SHOTS + 'proposals-after-light-1280.png', fullPage: true });
  return log;
}
