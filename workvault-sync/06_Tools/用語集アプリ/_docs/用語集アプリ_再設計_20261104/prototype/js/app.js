/* 社内用語集 再設計プロトタイプ — 共通スクリプト
 * 想定: Jinja2 版では template/base.html に集約して include。
 * 外部依存なし。prefers-reduced-motion を尊重する。 */

document.documentElement.classList.add('js');

const REDUCE = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/* document.startViewTransition が使えるときだけ包む（M-01/M-06） */
function vt(update) {
  if (!REDUCE && typeof document.startViewTransition === 'function') {
    document.startViewTransition(update);
  } else {
    update();
  }
}

/* 入力欄にいる間はショートカットを無効にする */
function isTyping(e) {
  return !!e.target.closest('input, textarea, select, [contenteditable]');
}

/* ---- 帯（M-09）: 結果の伝え方。ボタン上の文字ではなく、帯と読み上げで示す ---- */
function showBand(id, text) {
  const band = document.getElementById(id);
  if (!band) return;
  band.textContent = text;
  band.hidden = false;
  band.classList.remove('band-in');
  void band.offsetWidth;
  if (!REDUCE) band.classList.add('band-in');
}

/* ---- 数の整列（現行維持: カウントアップ。reduced-motion では即時表示） ---- */
function countUp(el) {
  const target = Number(el.dataset.countup);
  if (!Number.isFinite(target) || REDUCE) { el.textContent = String(target); return; }
  const dur = 500;
  const start = performance.now();
  function tick(now) {
    const p = Math.min(1, (now - start) / dur);
    const eased = 1 - Math.pow(1 - p, 3);
    el.textContent = String(Math.round(target * eased));
    if (p < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

/* ---- M-02: 一覧の stagger 再生（.rows に --i を与えておく） ---- */
function playRowStagger(table) {
  if (!table) return;
  table.classList.remove('rows-in');
  void table.offsetWidth;
  table.classList.add('rows-in');
}

/* ================= コマンドパレット（M-04, FR-017） ================= */

const TERMS = [
  { hw: '竜舎', y: 'りゅうしゃ', abbr: '', senses: 2 },
  { hw: '竜車', y: 'りんしゃ', abbr: '', senses: 1 },
  { hw: '卵温計', y: 'らんおんけい', abbr: '', senses: 1 },
  { hw: 'FLT点検', y: 'えふえるてぃーてんけん', abbr: 'FLT', senses: 1 },
  { hw: '浮遊石', y: 'ふゆうせき', abbr: '', senses: 1 },
  { hw: '星読み台帳', y: 'ほしよみだいちょう', abbr: '', senses: 2 },
  { hw: 'ほうき便', y: 'ほうきびん', abbr: '', senses: 1 },
  { hw: 'スカイポスト', y: 'すかいぽすと', abbr: '', senses: 1 },
  { hw: '雲切り', y: 'くもきり', abbr: '', senses: 1 },
  { hw: '霧抜き作業', y: 'きりぬきさぎょう', abbr: '', senses: 1 },
  { hw: 'ドラゴンミルク', y: 'どらごんみるく', abbr: '', senses: 1 },
  { hw: 'MGK', y: 'えむじーけー', abbr: 'MGK', senses: 1 },
  { hw: 'FLT', y: 'えふえるてぃー', abbr: 'FLT', senses: 1 },
];

function ensurePalette() {
  if (document.getElementById('palette')) return;
  const dlg = document.createElement('dialog');
  dlg.id = 'palette';
  dlg.className = 'palette';
  dlg.setAttribute('aria-label', '語を探す');
  const input = document.createElement('input');
  input.id = 'palette-input';
  input.type = 'text';
  input.setAttribute('role', 'combobox');
  input.setAttribute('aria-expanded', 'true');
  input.setAttribute('aria-controls', 'palette-list');
  input.setAttribute('aria-autocomplete', 'list');
  input.placeholder = '見出し語・読み・略語で探す';
  const ul = document.createElement('ul');
  ul.id = 'palette-list';
  ul.setAttribute('role', 'listbox');
  ul.setAttribute('aria-label', '候補');
  dlg.append(input, ul);
  document.body.append(dlg);

  let items = [];
  let pos = 0;

  function render(q) {
    const key = q.trim().toLowerCase();
    const scored = [];
    for (const t of TERMS) {
      const hay = [t.hw, t.y, t.abbr].join(' ').toLowerCase();
      if (!key || hay.includes(key)) {
        const starts = t.hw.toLowerCase().startsWith(key) || t.y.startsWith(key);
        scored.push({ t, rank: starts ? 0 : 1 });
      }
    }
    scored.sort((a, b) => a.rank - b.rank);
    items = scored.slice(0, 10).map((s) => s.t);
    pos = 0;
    ul.textContent = '';
    if (!items.length) {
      const li = document.createElement('li');
      li.className = 'p-empty';
      li.textContent = '一致する語はありません。見出し語を登録できます。';
      ul.append(li);
      input.removeAttribute('aria-activedescendant');
      return;
    }
    items.forEach((t, i) => {
      const li = document.createElement('li');
      li.id = 'palette-opt-' + i;
      li.setAttribute('role', 'option');
      li.setAttribute('aria-selected', i === pos ? 'true' : 'false');
      const hw = document.createElement('span');
      hw.className = 'p-hw';
      hw.textContent = t.hw;
      const meta = document.createElement('span');
      meta.className = 'p-meta';
      meta.textContent = (t.abbr ? t.abbr + ' ・ ' : '') + '語義 ' + t.senses;
      li.append(hw, meta);
      li.addEventListener('click', () => choose());
      ul.append(li);
    });
    input.setAttribute('aria-activedescendant', 'palette-opt-0');
  }

  function move(delta) {
    if (!items.length) return;
    pos = (pos + delta + items.length) % items.length;
    ul.querySelectorAll('li').forEach((li, i) => li.setAttribute('aria-selected', i === pos ? 'true' : 'false'));
    input.setAttribute('aria-activedescendant', 'palette-opt-' + pos);
    ul.children[pos].scrollIntoView({ block: 'nearest' });
  }

  function choose() {
    if (!items.length) return;
    dlg.close();
    location.href = 'detail.html';
  }

  input.addEventListener('input', () => render(input.value));
  input.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); move(1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); move(-1); }
    else if (e.key === 'Enter') { e.preventDefault(); choose(); }
  });
  dlg.addEventListener('close', () => { input.value = ''; render(''); });
  render('');
}

function openPalette() {
  ensurePalette();
  const dlg = document.getElementById('palette');
  if (!dlg.open) dlg.showModal();
  const input = document.getElementById('palette-input');
  input.value = '';
  input.dispatchEvent(new Event('input'));
  input.focus();
}

/* ================= キーボードヘルプ（FR-018, M-04） ================= */

const KEYS_HELP = {
  index: [['/', '検索欄へ移動'], ['Ctrl+K', 'コマンドパレット'], ['c', '一覧の表示をコンパクトにする']],
  detail: [['e', '編集'], ['h', '履歴'], ['Ctrl+K', 'コマンドパレット']],
  queue: [['j / k', '前後の提案へ'], ['a', '採用'], ['x', '却下'], ['Ctrl+K', 'コマンドパレット']],
  review: [['a', '正しい'], ['x', '修正が必要'], ['u', '役に立つ'], ['Ctrl+K', 'コマンドパレット']],
  new: [['Ctrl+Enter', '登録'], ['Esc', 'やめて一覧へ戻る']],
  history: [['Ctrl+K', 'コマンドパレット']],
};

function openKeysHelp() {
  let dlg = document.getElementById('keys-help');
  if (!dlg) {
    dlg = document.createElement('dialog');
    dlg.id = 'keys-help';
    dlg.className = 'keys-help';
    const h = document.createElement('h2');
    h.textContent = 'この画面で使えるキー';
    const table = document.createElement('table');
    const tbody = document.createElement('tbody');
    for (const [k, label] of (KEYS_HELP[document.body.dataset.page] || [['Ctrl+K', 'コマンドパレット']])) {
      const tr = document.createElement('tr');
      const td1 = document.createElement('td');
      const kbd = document.createElement('kbd');
      kbd.textContent = k;
      td1.append(kbd);
      const td2 = document.createElement('td');
      td2.textContent = label;
      tr.append(td1, td2);
      tbody.append(tr);
    }
    table.append(tbody);
    const note = document.createElement('p');
    note.className = 'hint';
    note.textContent = '入力欄にいる間はショートカットが働きません。Esc で閉じます。';
    const close = document.createElement('button');
    close.textContent = '閉じる';
    close.className = 'close';
    close.addEventListener('click', () => dlg.close());
    dlg.append(h, table, note, close);
    document.body.append(dlg);
  }
  if (!dlg.open) dlg.showModal();
}

/* ================= 朱印（M-05, FR-013/FR-008） ================= */

function setupStamps() {
  document.querySelectorAll('.stamp').forEach((btn) => {
    btn.setAttribute('aria-pressed', btn.classList.contains('is-stamped') ? 'true' : 'false');
    if (!btn.querySelector('.ring')) {
      const ring = document.createElement('span');
      ring.className = 'ring';
      ring.setAttribute('aria-hidden', 'true');
      btn.append(ring);
    }
    btn.addEventListener('click', () => {
      const group = btn.closest('.ev-buttons, .inline-eval');
      const wasStamped = btn.classList.contains('is-stamped');
      if (group) group.querySelectorAll('.stamp').forEach((b) => {
        b.classList.remove('is-stamped');
        b.setAttribute('aria-pressed', 'false');
      });
      if (!wasStamped) {
        btn.classList.add('is-stamped');
        btn.setAttribute('aria-pressed', 'true');
        const ring = btn.querySelector('.ring');
        if (!REDUCE && ring) { ring.style.animation = 'none'; void ring.offsetWidth; ring.style.animation = ''; }
      }
      const label = btn.dataset.evLabel || btn.textContent.trim();
      const rev = btn.closest('[data-rev]')?.dataset.rev || '現行の版';
      announce(wasStamped ? `「${label}」の記録を外しました（デモ）` : `${rev}に「${label}」を記録しました（デモ）`);
    });
  });
}

/* aria-live の共通応答口。各ページに 1 個置く（無ければ作る） */
function ensureStatus() {
  let s = document.getElementById('live-status') || document.getElementById('knav-status');
  if (!s) {
    s = document.createElement('p');
    s.id = 'live-status';
    s.className = 'sr-only';
    s.setAttribute('role', 'status');
    s.setAttribute('aria-live', 'polite');
    document.body.append(s);
  }
  return s;
}
function announce(text) { ensureStatus().textContent = text; }

/* ================= 一覧（FR-003, FR-004） ================= */

function setupIndex() {
  const table = document.querySelector('table.rows');
  const rows = table ? [...table.querySelectorAll('tbody tr')] : [];
  const zero = document.getElementById('zero');
  const countEl = document.getElementById('count');
  const q = document.getElementById('q');
  const form = document.getElementById('search-form');

  function applyFilter(raw) {
    const key = (raw || '').trim().toLowerCase();
    let shown = 0;
    rows.forEach((tr, i) => {
      const hay = ((tr.dataset.headword || '') + ' ' + (tr.dataset.reading || '') + ' ' + (tr.dataset.abbr || '')).toLowerCase();
      const hit = !key || hay.includes(key);
      tr.hidden = !hit;
      if (hit) { tr.style.setProperty('--i', String(Math.min(shown, 5))); shown++; }
    });
    if (countEl) countEl.textContent = `${rows.length} 件中 ${shown} 件を表示`;
    if (zero) {
      zero.hidden = shown !== 0;
      if (shown === 0) {
        document.getElementById('zero-term').textContent = raw;
        const link = document.getElementById('zero-new');
        link.href = 'new.html?headword=' + encodeURIComponent(raw.trim());
      }
    }
    announce(`${rows.length} 件中 ${shown} 件を表示`);
    if (shown && !REDUCE) playRowStagger(table);
  }

  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      vt(() => applyFilter(q.value));
    });
  }

  const params = new URLSearchParams(location.search);
  if (params.get('q')) {
    q.value = params.get('q');
    applyFilter(q.value);
  } else if (!REDUCE) {
    playRowStagger(table);
  }

  /* 表示の切り替え（現行維持・FR-002） */
  const compact = document.getElementById('compact-toggle');
  function toggleCompact() {
    const on = table.classList.toggle('compact');
    compact.setAttribute('aria-pressed', on ? 'true' : 'false');
    announce(on ? '一覧をコンパクト表示にしました' : '一覧を標準表示にしました');
  }
  if (compact) {
    compact.hidden = false;
    compact.addEventListener('click', toggleCompact);
  }

  if (q) {
    document.addEventListener('keydown', (e) => {
      if (isTyping(e) || e.ctrlKey || e.metaKey || e.altKey) return;
      if (e.key === '/' ) {
        e.preventDefault();
        q.focus();
        q.select();
      } else if (e.key === 'c' && compact) {
        e.preventDefault();
        toggleCompact();
      }
    });
    q.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') { q.value = ''; applyFilter(''); announce('検索をやめました'); }
    });
  }
  const kh = document.querySelector('.knav-hint');
  if (kh) kh.hidden = false;
}

/* ================= 提案キュー（FR-006, M-06） ================= */

function setupQueue() {
  const cards = () => [...document.querySelectorAll('.proposal.is-pending')];
  let kpos = -1;
  const hint = document.querySelector('.knav-hint');
  if (hint) hint.hidden = false;

  document.querySelectorAll('.proposal.is-pending').forEach((c) => {
    c.tabIndex = -1;
    const cb = c.querySelector('.prop-check input');
    if (cb) cb.addEventListener('change', updateBulk);
  });

  function updateBulk() {
    const bar = document.getElementById('bulk-bar');
    const n = [...document.querySelectorAll('.prop-check input:checked')].length;
    const cnt = document.getElementById('bulk-count');
    if (cnt) cnt.textContent = `${n} 件を選択`;
    if (bar) bar.hidden = n === 0;
    announce(`${n} 件を選択`);
  }

  function focusCard(delta) {
    const list = cards();
    if (!list.length) { announce('未処理の提案はありません'); return; }
    if (kpos >= 0 && list[kpos]) list[kpos].classList.remove('kcursor');
    kpos = Math.max(0, Math.min(list.length - 1, kpos < 0 ? 0 : kpos + delta));
    const c = list[kpos];
    c.classList.add('kcursor');
    c.focus({ preventScroll: true });
    c.scrollIntoView({ block: 'center', behavior: REDUCE ? 'auto' : 'smooth' });
    const h = c.querySelector('h2');
    announce(h ? h.textContent.trim() : '提案');
  }

  function process(card, accept) {
    if (!card) return;
    const titleEl = card.querySelector('.hw-inline');
    const title = titleEl ? titleEl.textContent : '提案';
    if (accept && card.hasAttribute('data-protected')) {
      showBand('queue-band', `「${title}」は出典数が基準に満たないため、一括でも自動でも採用できません。修正して採用するか、却下してください（デモ）。`);
      announce('基準を満たさない提案のため採用しませんでした');
      return;
    }
    vt(() => {
      card.classList.remove('is-pending');
      card.classList.add('is-done');
      card.classList.remove('kcursor');
      const cb = card.querySelector('.prop-check input');
      if (cb) { cb.checked = false; cb.disabled = true; }
      const badge = card.querySelector('.badge');
      if (badge) {
        badge.textContent = accept ? '採用済み' : '却下済み';
        badge.classList.remove('st-pending');
        badge.classList.add(accept ? 'st-accepted' : 'st-rejected');
      }
      kpos = -1;
      updateBulk();
    });
    showBand('queue-band', `「${title}」を${accept ? '採用' : '却下'}しました。決定は履歴に残ります（デモ）。`);
    announce(`「${title}」を${accept ? '採用' : '却下'}しました`);
  }

  /* 種別の絞り込み（FR-006） */
  document.querySelectorAll('.seg a[data-kind]').forEach((chip) => {
    chip.addEventListener('click', (e) => {
      e.preventDefault();
      const kind = chip.dataset.kind;
      document.querySelectorAll('.seg a[data-kind]').forEach((c) => c.setAttribute('aria-pressed', c === chip ? 'true' : 'false'));
      let n = 0;
      document.querySelectorAll('.proposal').forEach((c) => {
        const show = kind === 'all' || c.dataset.type === kind;
        c.hidden = !show;
        if (show && !c.classList.contains('is-done')) n++;
      });
      announce(`種別を ${chip.textContent.trim()} にしました。未処理 ${n} 件`);
    });
  });

  /* 個別の採用/却下ボタン（カード内の .actions） */
  document.querySelectorAll('.proposal.is-pending .actions button').forEach((btn) => {
    btn.addEventListener('click', () => {
      const card = btn.closest('.proposal');
      process(card, btn.classList.contains('primary'));
    });
  });

  /* 一括処理（FR-006） */
  const bulkAccept = document.getElementById('bulk-accept');
  const bulkReject = document.getElementById('bulk-reject');
  function bulkRun(accept) {
    const chosen = [...document.querySelectorAll('.proposal.is-pending')].filter((c) => c.querySelector('.prop-check input')?.checked);
    const blocked = chosen.filter((c) => c.hasAttribute('data-protected'));
    let done = 0;
    chosen.forEach((c) => {
      if (accept && c.hasAttribute('data-protected')) return;
      process(c, accept);
      done++;
    });
    if (blocked.length) {
      showBand('queue-band', `${blocked.length} 件は出典数が基準に満たないため一括採用の対象になりません。個別に判断してください（デモ）。`);
    } else if (done) {
      announce(`${done} 件を${accept ? '採用' : '却下'}しました`);
    }
  }
  if (bulkAccept) bulkAccept.addEventListener('click', () => bulkRun(true));
  if (bulkReject) bulkReject.addEventListener('click', () => bulkRun(false));

  document.addEventListener('keydown', (e) => {
    if (isTyping(e) || e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.key === 'j') { e.preventDefault(); focusCard(1); }
    else if (e.key === 'k') { e.preventDefault(); focusCard(-1); }
    else if (e.key === 'a') { e.preventDefault(); process(cards()[Math.max(kpos, 0)], true); }
    else if (e.key === 'x') { e.preventDefault(); process(cards()[Math.max(kpos, 0)], false); }
  });
}

/* ================= 見直し（FR-008）: 行内の朱印は setupStamps が処理 ================= */

/* ================= 関連語プレビュー（FR-012, M-03） ================= */

function setupPreviews() {
  const triggers = [...document.querySelectorAll('[data-preview-title]')];
  if (!triggers.length) return;
  const canPopover = typeof HTMLElement !== 'undefined' && 'popover' in HTMLElement.prototype;
  if (!canPopover) {
    triggers.forEach((t) => { t.title = `${t.dataset.previewTitle} — ${t.dataset.previewDef || ''}`; });
    return;
  }
  const rp = document.createElement('div');
  rp.className = 'rp';
  rp.setAttribute('popover', 'manual');
  document.body.append(rp);
  const supportsAnchor = (() => {
    try { return CSS.supports('anchor-name: --rp-a'); } catch { return false; }
  })();

  let hideTimer = 0;
  let showTimer = 0;

  function place(trigger) {
    if (supportsAnchor) {
      const name = '--rp-' + Math.abs([].indexOf.call(triggers, trigger));
      trigger.style.setProperty('anchor-name', name);
      rp.style.setProperty('--rp-anchor', name);
    } else {
      const r = trigger.getBoundingClientRect();
      const left = Math.max(8, Math.min(r.left, window.innerWidth - 336));
      const below = r.bottom + 8;
      rp.style.left = left + 'px';
      rp.style.top = (below + 190 > window.innerHeight ? Math.max(8, r.top - 190) : below) + 'px';
    }
  }

  function show(trigger) {
    rp.textContent = '';
    const h = document.createElement('span');
    h.className = 'rp-h';
    h.textContent = trigger.dataset.previewTitle;
    const r = document.createElement('span');
    r.className = 'rp-r';
    r.textContent = trigger.dataset.previewReading || '';
    const d = document.createElement('p');
    d.className = 'rp-d';
    d.textContent = trigger.dataset.previewDef || '';
    rp.append(h, r, d);
    if (trigger.dataset.previewCount) {
      const c = document.createElement('span');
      c.className = 'rp-c';
      c.textContent = trigger.dataset.previewCount;
      rp.append(c);
    }
    place(trigger);
    if (!rp.open) rp.showPopover();
  }
  function hide() {
    if (rp.open) rp.hidePopover();
  }

  triggers.forEach((t) => {
    t.addEventListener('pointerenter', () => {
      clearTimeout(hideTimer); clearTimeout(showTimer);
      showTimer = window.setTimeout(() => show(t), REDUCE ? 0 : 150);
    });
    t.addEventListener('pointerleave', () => { clearTimeout(showTimer); hide(); });
    t.addEventListener('focus', () => { clearTimeout(hideTimer); show(t); });
    t.addEventListener('blur', () => { hideTimer = window.setTimeout(hide, 80); });
  });
  window.addEventListener('scroll', hide, { passive: true });
  window.addEventListener('keydown', (e) => { if (e.key === 'Escape') hide(); });
}

/* ================= グローバルのキーボード操作 ================= */

function setupGlobalKeys() {
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      openPalette();
      return;
    }
    const inDialog = e.target.closest('dialog');
    if (inDialog) return; /* dialog 内はネイティブの Esc に任せる */
    if (isTyping(e)) return;
    if (e.key === '?') { e.preventDefault(); openKeysHelp(); return; }
    const page = document.body.dataset.page;
    if (page === 'detail') {
      if (e.key === 'e') location.href = 'new.html';
      if (e.key === 'h') location.href = 'history.html';
    }
    if (page === 'new' && e.key === 'Escape') location.href = 'index.html';
  });
  const openBtn = document.getElementById('open-palette');
  if (openBtn) {
    openBtn.hidden = false;
    openBtn.addEventListener('click', (e) => { e.preventDefault(); openPalette(); });
  }
}

/* ================= 登録フォーム（FR-019 のデモ） ================= */

function setupNew() {
  const form = document.getElementById('term-form');
  if (!form) return;
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    showBand('new-band', '登録しました（デモ）。一覧に戻ると、上部の帯で結果を伝えます。');
    announce('登録しました（デモ）');
  });
  const cancel = document.getElementById('new-cancel');
  if (cancel) cancel.addEventListener('click', (e) => { e.preventDefault(); location.href = 'index.html'; });
}

/* ================= 起動 ================= */

window.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-countup]').forEach(countUp);
  setupGlobalKeys();
  setupStamps();
  setupPreviews();
  const page = document.body.dataset.page;
  if (page === 'index') setupIndex();
  if (page === 'queue') setupQueue();
  if (page === 'new') setupNew();
});
