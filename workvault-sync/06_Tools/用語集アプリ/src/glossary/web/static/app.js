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
