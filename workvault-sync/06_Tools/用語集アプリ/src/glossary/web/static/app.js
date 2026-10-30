// 送信中の二重押しを防ぎ、処理中であることを画面読み上げにも伝える。
// JavaScript が無くてもフォームはそのまま動く（これは補助にすぎない）。
// ボタンは disabled にしない。押したボタン自体を無効にすると、その name/value（評価の「正しい」など）が
// 送信内容から落ちてしまうため。代わりに、同じフォームの2回目の送信だけを止める。
document.addEventListener("submit", function (ev) {
  var form = ev.target;
  if (!form.classList || !form.classList.contains("busy-on-submit")) return;
  if (!form.checkValidity()) return;
  if (form.dataset.busy === "1") {
    ev.preventDefault();
    return;
  }
  form.dataset.busy = "1";
  var status = document.getElementById("busy-status");
  if (status) status.hidden = false;
});

// JS が要る操作の入口。.js-only は HTML では hidden になっていて、JS が動くときだけ出す
document.querySelectorAll(".js-only").forEach(function (el) {
  el.hidden = false;
});

// 今開いているページをナビで示す。下の階層（詳細・編集画面）も親の項目を光らせる
document.querySelectorAll("header nav a").forEach(function (a) {
  var path = (a.getAttribute("href") || "").split("?")[0];
  if (path === "/export.csv") return;
  if (location.pathname === path || location.pathname.indexOf(path + "/") === 0) {
    a.setAttribute("aria-current", "page");
  }
});

// 「/」で検索欄へ移る。入力欄の中では効かせない
document.addEventListener("keydown", function (ev) {
  if (ev.key !== "/" || ev.ctrlKey || ev.metaKey || ev.altKey) return;
  var tag = (document.activeElement && document.activeElement.tagName) || "";
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
  var q = document.getElementById("q");
  if (q) {
    ev.preventDefault();
    q.focus();
  }
});

// 戻るボタンで戻ったとき、送信中の印を外す
window.addEventListener("pageshow", function () {
  var status = document.getElementById("busy-status");
  if (status) status.hidden = true;
  document.querySelectorAll("form.busy-on-submit").forEach(function (f) {
    delete f.dataset.busy;
  });
});

// 統計カードの数をゆっくり上げる。動きは飾りで、数値自体は HTML に書いてある（JS が無くても読める）
(function () {
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  document.querySelectorAll(".stat .n[data-count]").forEach(function (el) {
    var target = parseInt(el.dataset.count, 10) || 0;
    if (!target || reduce) return;
    var t0 = null;
    function step(t) {
      if (t0 === null) t0 = t;
      var k = Math.min((t - t0) / 500, 1);
      k = 1 - Math.pow(1 - k, 3);
      el.textContent = String(Math.round(target * k));
      if (k < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  });
})();

// ---- 提案キュー: 一括処理の選択バー ----
// チェックの数を数えてバーに出す。0件のときはバーを隠す（JS が無ければ常に見えていて、
// 何も選ばずに押すとサーバーが一覧に理由を出して戻す）。
(function () {
  var list = document.getElementById("proposals-list");
  var bar = document.getElementById("bulk-bar-form");
  if (!list || !bar) return;
  var count = document.getElementById("bulk-count");
  var warn = document.getElementById("bulk-warn");
  var all = document.getElementById("bulk-select-all");

  function boxes() {
    return Array.prototype.slice.call(list.querySelectorAll('input[name="ids"]'));
  }
  function checkedBoxes() {
    return boxes().filter(function (b) { return b.checked; });
  }
  function protectedChecked() {
    return checkedBoxes().filter(function (b) {
      var card = b.closest(".proposal");
      return card && card.dataset.protected === "1";
    }).length;
  }
  function refresh() {
    var n = checkedBoxes().length;
    if (count) count.textContent = "選択 " + n + " 件";
    bar.hidden = n === 0;
    if (warn) warn.hidden = protectedChecked() === 0;
    if (all) all.textContent = n === boxes().length ? "選択をすべて外す" : "このページをすべて選択";
  }
  list.addEventListener("change", function (ev) {
    if (ev.target && ev.target.name === "ids") refresh();
  });
  if (all) {
    all.addEventListener("click", function () {
      var cs = boxes();
      var fill = checkedBoxes().length !== cs.length;
      cs.forEach(function (b) { b.checked = fill; });
      refresh();
    });
  }
  refresh();
})();

// ---- 用語一覧: 表の密度切替 ----
// 狭い表示の好みは端末ごとに保存する（データではないので URL には載せない）。
// JS が無ければボタン自体が出ない。既定は普段の行高。
(function () {
  var table = document.getElementById("terms-table");
  var btn = document.getElementById("density-toggle");
  if (!table || !btn) return;
  function apply(compact) {
    table.classList.toggle("compact", compact);
    btn.setAttribute("aria-pressed", compact ? "true" : "false");
  }
  var saved = null;
  try { saved = localStorage.getItem("glossary-density"); } catch (e) { /* 保存できない端末では既定のまま */ }
  apply(saved === "compact");
  btn.addEventListener("click", function () {
    var compact = !table.classList.contains("compact");
    apply(compact);
    try { localStorage.setItem("glossary-density", compact ? "compact" : "cozy"); } catch (e) { /* 同上 */ }
  });
})();

// ---- 提案キュー: キーボードトリアージ ----
// j/k で提案の間を移動し、a/r でその提案の採用・却下のフォームを送る。x で一括処理のチェックを切り替える。
// 入力欄・ボタン・リンクにフォーカスがあるときは何もしない（誤操作とキーボードトラップを防ぐ）。
// Tab の順序は変えない（カードは tabindex=-1 で Tab では来ない）。JS が無くても画面は成り立つ。
(function () {
  var list = document.getElementById("proposals-list");
  if (!list) return;
  var cards = Array.prototype.slice.call(list.querySelectorAll(".proposal"));
  if (!cards.length) return;
  var status = document.getElementById("knav-status");
  var cur = -1;

  function guarded() {
    var el = document.activeElement;
    if (!el) return true;
    var t = el.tagName;
    if (t === "INPUT" || t === "TEXTAREA" || t === "SELECT" || t === "BUTTON" || t === "A") return true;
    return !!(el.isContentEditable);
  }
  function say(text) {
    if (status) status.textContent = text;
  }
  function move(step) {
    var next = Math.min(Math.max(cur + step, 0), cards.length - 1);
    if (next === cur) return;
    if (cur >= 0) cards[cur].classList.remove("kcursor");
    cur = next;
    var card = cards[cur];
    card.classList.add("kcursor");
    card.focus();
    var title = card.querySelector("h2");
    var name = title ? title.textContent.replace(/\s+/g, " ").trim() : "";
    var note = card.dataset.protected === "1"
      ? name + "（定義の記入が必要です。「修正して採用」で開いてください）"
      : name;
    say(note + " ／ " + (cur + 1) + "件目（全 " + cards.length + " 件）");
  }
  function act(card, action) {
    var form = card.querySelector('form[data-kaction="' + action + '"]');
    if (!form) {
      if (card.dataset.protected === "1") {
        say("この提案は定義の記入が必要です。「修正して採用」で開いてください。");
      } else {
        say("この提案は処理済みです。採用・却下の操作はありません。");
      }
      return;
    }
    if (form.requestSubmit) form.requestSubmit();
    else form.submit();
  }
  function toggleSelect(card) {
    var box = card.querySelector('input[name="ids"]');
    if (!box) return;
    box.checked = !box.checked;
    box.dispatchEvent(new Event("change", { bubbles: true }));
  }
  document.addEventListener("keydown", function (ev) {
    if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
    var k = ev.key;
    if (k !== "j" && k !== "k" && k !== "a" && k !== "r" && k !== "x") return;
    if (guarded()) return;
    if (k === "j" || k === "k") {
      ev.preventDefault();
      move(k === "j" ? 1 : -1);
      return;
    }
    if (cur < 0) return;
    ev.preventDefault();
    if (k === "a") act(cards[cur], "accept");
    else if (k === "r") act(cards[cur], "reject");
    else toggleSelect(cards[cur]);
  });
})();
