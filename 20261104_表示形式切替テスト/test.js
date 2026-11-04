/* ============================================================
   J-01 表示形式切替テスト — 切替ロジック（vanilla JS・CDN不使用）

   設計原則:
   - 13人分のカードと行を一度だけ作り、切替で作り直さない（hidden とクラスで切り替える）
   - 形式・並べ方・絞り込みの切替は容器の 0.15秒の淡い切替（不透明度のみ・§E-2）
   - 動きを減らす設定では切替は即時・出現遅延も 0（§A-4／§B-5）
   - 出現の呼吸層（720ms・10px上へ）は初回ロードのみ。切替では再生しない
   ============================================================ */
(function () {
  'use strict';

  var html = document.documentElement;

  /* ---------- テストデータ: mock/data/characters.json の13人（模擬データ） ---------- */
  var DATA = [
    { id: 'c001', name: '燭守 セラフ',       role: '封印の継ぎ手',       affiliation: '回廊聖堂', appearance: '左頬に煤の紋。白い手袋を外さない' },
    { id: 'c002', name: '写本屋 ヴェル',     role: '記録の写し手',       affiliation: '独立',     appearance: '眼帯の奥が銀色。墨に指が染まっている' },
    { id: 'c003', name: '灯番 リュミエ',     role: '燭台の管理人',       affiliation: '回廊聖堂', appearance: '背の低い老婆。灯りを数える癖がある' },
    { id: 'c004', name: '異端吏 オクタヴィア', role: '禁書の検閲官',     affiliation: '教団',     appearance: '鉄の仮面を下顎だけ外して話す' },
    { id: 'c005', name: '調律師 カノン',     role: '音の封印師',         affiliation: '回廊聖堂', appearance: '耳に蝋の栓。鼻歌で封を締める' },
    { id: 'c006', name: '号手 タル',         role: '鐘楼の番人',         affiliation: '鐘楼',     appearance: '声が大きく、筆談を好む' },
    { id: 'c007', name: '薬師 ミョルニ',     role: '血の代わりの錬成',   affiliation: '地下病院', appearance: '手に焼いた印。包帯を巻き直す前に必ず洗う' },
    { id: 'c008', name: '囁き ノクス',       role: '名を盗む者',         affiliation: '不明',     appearance: '名乗らない。他人の名を借りて話す' },
    { id: 'c009', name: '祝祭主 アレルイ',   role: '断章を集める祭官',   affiliation: '祝祭庁',   appearance: '極彩色の刺繍の法衣。歩く音がしない' },
    { id: 'c010', name: '鐘鋳師 フォルデ',   role: '鐘を鋳る者',         affiliation: '鐘楼',     appearance: '耳が聞こえない。振動で会話する' },
    { id: 'c011', name: '塵纏い ルゥ',       role: '掃き溜めの附喪女',   affiliation: '不明',     appearance: '灰色の髪。捨てられた物の声が聞こえる' },
    { id: 'c012', name: '算官 セウト',       role: '贖罪の勘定係',       affiliation: '教団',     appearance: '算盤を持たない計算者。指を折らない' },
    { id: 'c013', name: '看取り ヴィゴル',   role: '最期の記録係',       affiliation: '回廊聖堂', appearance: '黒い帳面を胸元に。遺言は書き取らない' }
  ];

  var state = { reduce: false, form: 'card', layout: 'flow', aff: 'all' };

  /* ---------- 速さは CSS 変数から読む（§G-5: 直値を JS に書かない） ---------- */
  function cssMs(name, fallback) {
    var v = getComputedStyle(html).getPropertyValue(name).trim();
    var m = v.match(/^([\d.]+)ms$/);
    if (m) return parseFloat(m[1]);
    m = v.match(/^([\d.]+)s$/);
    if (m) return parseFloat(m[1]) * 1000;
    return fallback;
  }
  var STEP = cssMs('--stagger-card', 55);
  var MAX_DELAY = cssMs('--stagger-max', 480);
  var SWITCH_MS = cssMs('--dur-switch', 150);

  /* ---------- DOM ---------- */
  var gridCard = document.getElementById('grid-card');
  var gridRow = document.getElementById('grid-row');
  var tbody = document.getElementById('tbody');
  var listwrap = document.getElementById('listwrap');
  var resultLine = document.getElementById('result-line');
  var formNote = document.getElementById('form-note');
  var layoutNote = document.getElementById('layout-note');
  var layoutReadout = document.getElementById('layout-readout');
  var reduceInput = document.getElementById('reduce-motion');
  var formChips = [].slice.call(document.querySelectorAll('button[data-form]'));
  var layoutChips = [].slice.call(document.querySelectorAll('button[data-layout]'));
  var affChips = [].slice.call(document.querySelectorAll('button[data-aff]'));

  /* ---------- 遅延の台帳（reduce 時に 0 へ戻す） ---------- */
  var delayRegistry = [];
  function setEnterDelay(el, ms) {
    el.style.animationDelay = ms + 'ms';
    if (ms > 0) delayRegistry.push(el);
  }
  function zeroDelays() {
    delayRegistry.forEach(function (el) { el.style.animationDelay = '0ms'; });
    delayRegistry = [];
  }

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  /* ---------- 13個を一度だけ作る（切替で作り直さない・前作 F-1 の原則） ---------- */
  var cardEls = DATA.map(function (p) {
    var li = document.createElement('li');
    li.className = 'card';
    li.setAttribute('data-id', p.id);
    li.innerHTML =
      '<span class="plate" role="img" aria-label="肖像は準備中（題箋代用の枠・3:4）">' + esc(p.name) + '<br>題箋</span>' +
      '<p class="name">' + esc(p.name) + '</p>' +
      '<p class="role">' + esc(p.role) + '／' + esc(p.affiliation) + '</p>';
    gridCard.appendChild(li);
    return li;
  });

  var rowEls = DATA.map(function (p) {
    var tr = document.createElement('tr');
    tr.setAttribute('data-id', p.id);
    tr.innerHTML =
      '<th scope="row">' + esc(p.name) + '</th>' +
      '<td data-label="役割">' + esc(p.role) + '</td>' +
      '<td data-label="所属">' + esc(p.affiliation) + '</td>' +
      '<td data-label="外見の特徴">' + esc(p.appearance) + '</td>';
    tbody.appendChild(tr);
    return tr;
  });

  /* 初回出現の遅れ（通し番号方式・上限あり）。切替では再生しない。 */
  cardEls.forEach(function (el, i) { setEnterDelay(el, Math.min(i * STEP, MAX_DELAY)); });
  rowEls.forEach(function (el, i) { setEnterDelay(el, Math.min(i * STEP, MAX_DELAY)); });

  /* ---------- 切替の共通動作: 容器の 0.15秒の淡い切替（reduce 時は即時） ---------- */
  function fadeSwap(fn) {
    if (state.reduce) { fn(); return; }
    listwrap.classList.add('is-switching');
    setTimeout(function () {
      fn();
      listwrap.classList.remove('is-switching');
    }, SWITCH_MS / 2);
  }

  function syncChips(chips, key, value) {
    chips.forEach(function (b) {
      b.setAttribute('aria-pressed', b.getAttribute('data-' + key) === value ? 'true' : 'false');
    });
  }

  function matchesAff(p) {
    return state.aff === 'all' || p.affiliation === state.aff;
  }

  function updateReadout() {
    var layoutText = state.layout === 'tile'
      ? '整列タイル流（固定' + (window.innerWidth <= 768 ? '2' : '3') + '列・同一比率・行間列間均一）'
      : '現行流（auto-fill 可変幅）';
    layoutReadout.textContent =
      '並べ方の現状: ' + layoutText +
      ' ／ 形式: ' + (state.form === 'card' ? 'カード' : '行') +
      ' ／ 絞り込み: ' + state.aff +
      '。13人のデータではどちらの並べ方でも最終行に端数が出るため、その見え方の比較が A-3 判断の材料になる。';
  }

  /* ---------- 形式切替（J-01 の本体） ---------- */
  function applyForm(next, opts) {
    state.form = next;
    syncChips(formChips, 'form', next);
    /* 行形式では並べ方の選択が効かない → 非活性化（無理に 2 軸を効かせない判断） */
    layoutChips.forEach(function (b) { b.disabled = next === 'row'; });
    formNote.textContent = next === 'card'
      ? '既定は画面幅で選択（768px 以上はカード・未満は行）。切替は両デバイスで可能。'
      : '行形式は常に1列で並ぶ。最低限の情報（名前・役割・所属・外見）は行内に揃う。';
    layoutNote.textContent = next === 'row'
      ? '行形式では並べ方の選択が効かないため非活性（行は常に1列で並ぶ）。'
      : 'カードの並べ方。現行流は可変幅（最終行の端数で幅が揃わない）、整列タイル流は固定列・同一比率。';
    var swap = function () {
      gridCard.hidden = next !== 'card';
      gridRow.hidden = next !== 'row';
    };
    if (opts && opts.immediate) { swap(); } else { fadeSwap(swap); }
  }

  /* ---------- 並べ方切替（A-3 比較の軸） ---------- */
  function applyLayout(next) {
    state.layout = next;
    syncChips(layoutChips, 'layout', next);
    gridCard.classList.toggle('grid--flow', next === 'flow');
    gridCard.classList.toggle('grid--tile', next === 'tile');
    updateReadout();
  }

  /* ---------- 絞り込み（chara.html と同じ aria-pressed 単一選択） ---------- */
  function applyFilter() {
    syncChips(affChips, 'aff', state.aff);
    fadeSwap(function () {
      var n = 0;
      DATA.forEach(function (p, i) {
        var on = matchesAff(p);
        if (on) n++;
        cardEls[i].hidden = !on;
        rowEls[i].hidden = !on;
      });
      resultLine.textContent = n + '人を表示中。';
    });
    updateReadout();
  }

  /* ---------- 動きを減らす設定（§A-4・シミュレーション） ---------- */
  function setReduce(on) {
    state.reduce = on;
    html.classList.toggle('reduce-motion', on);
    if (on) zeroDelays();
  }
  reduceInput.addEventListener('change', function () { setReduce(reduceInput.checked); });

  /* ---------- チップ操作 ---------- */
  formChips.forEach(function (b) {
    b.addEventListener('click', function () {
      var next = b.getAttribute('data-form');
      if (state.form !== next) applyForm(next);
    });
  });
  layoutChips.forEach(function (b) {
    b.addEventListener('click', function () {
      var next = b.getAttribute('data-layout');
      if (!b.disabled && state.layout !== next) applyLayout(next);
    });
  });
  affChips.forEach(function (b) {
    b.addEventListener('click', function () {
      var next = b.getAttribute('data-aff');
      if (state.aff !== next) { state.aff = next; applyFilter(); }
    });
  });

  /* ---------- 初期化: 既定の形式は画面幅で選ぶ（受け入れ条件①） ---------- */
  var initialForm = window.innerWidth >= 768 ? 'card' : 'row';
  applyForm(initialForm, { immediate: true });
  applyLayout('flow');
  updateReadout();

  /* ---------- 検査用 API（capture.cjs から参照） ---------- */
  function durMs(v) {
    var first = String(v).split(',')[0].trim();
    var num = parseFloat(first);
    return /ms$/.test(first) ? num : num * 1000;
  }

  window.__formtest = {
    state: state,
    counts: function () {
      return {
        cards: cardEls.filter(function (el) { return !el.hidden; }).length,
        rows: rowEls.filter(function (el) { return !el.hidden; }).length,
        cardAll: cardEls.length,
        rowAll: rowEls.length,
        total: DATA.length
      };
    },
    vis: function () { return { card: !gridCard.hidden, row: !gridRow.hidden }; },
    switchMs: function () { return SWITCH_MS; },
    fadeHalfMs: function () { return durMs(getComputedStyle(listwrap).transitionDuration); },
    cardCols: function () { return getComputedStyle(gridCard).gridTemplateColumns; },
    opacity: function () { return parseFloat(getComputedStyle(listwrap).opacity); },
    delays: function () {
      return {
        cards: cardEls.map(function (el) { return el.style.animationDelay; }),
        rows: rowEls.map(function (el) { return el.style.animationDelay; })
      };
    },
    resultText: function () { return resultLine.textContent; },
    chipsState: function () {
      return {
        form: formChips.map(function (b) { return [b.getAttribute('data-form'), b.getAttribute('aria-pressed')]; }),
        layout: layoutChips.map(function (b) { return [b.getAttribute('data-layout'), b.getAttribute('aria-pressed'), String(b.disabled)]; }),
        aff: affChips.map(function (b) { return [b.getAttribute('data-aff'), b.getAttribute('aria-pressed')]; })
      };
    },
    setReduce: setReduce
  };
})();
