/* 明/暗/自動の 3 段階。既定は auto（OS に従う）。選択は localStorage に残す */
(function () {
  "use strict";

  var KEY = "vba-glossary-theme";
  var ORDER = ["auto", "light", "dark"];
  var ICON = { auto: "◐", light: "☀", dark: "☾" };

  function apply(mode) {
    document.documentElement.setAttribute("data-theme", mode);
    var btn = document.getElementById("theme-toggle");
    if (btn) {
      btn.textContent = ICON[mode] || "◐";
      btn.title = "表示: " + ({ auto: "自動", light: "明", dark: "暗" })[mode];
    }
  }

  var current = localStorage.getItem(KEY) || "auto";
  if (ORDER.indexOf(current) < 0) current = "auto";
  apply(current);

  var btn = document.getElementById("theme-toggle");
  if (btn) {
    btn.addEventListener("click", function () {
      var next = ORDER[(ORDER.indexOf(current) + 1) % ORDER.length];
      current = next;
      localStorage.setItem(KEY, next);
      apply(next);
    });
  }

  /* 「/」で検索欄へ */
  document.addEventListener("keydown", function (ev) {
    if (ev.key !== "/" || ev.ctrlKey || ev.metaKey || ev.altKey) return;
    var tag = (document.activeElement && document.activeElement.tagName) || "";
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
    var q = document.getElementById("q");
    if (q) {
      ev.preventDefault();
      q.focus();
      q.select();
    }
  });

  /* VBA の軽い着色: キーワード / 文字列 / コメント / 数値 */
  var KEYWORDS = /\b(Sub|Function|Property|End|If|Then|Else|ElseIf|For|Each|To|Step|Next|Do|While|Until|Loop|Select|Case|Dim|Const|Set|Let|Get|Public|Private|Friend|Static|Call|Exit|On|Error|GoTo|Resume|With|New|Nothing|True|False|As|ByVal|ByRef|Optional|ParamArray|Option|Explicit|Implements|Event|RaiseEvent|Type|Enum|Declare|Lib)\b/g;

  function highlight(el) {
    if (el.dataset.done) return;
    el.dataset.done = "1";
    var text = el.textContent;
    var lines = text.split("\n");
    var out = lines.map(function (line) {
      var esc = line
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
      /* コメント以降はそのまま */
      var codePart = esc;
      var comment = "";
      var inStr = false;
      var cut = -1;
      for (var i = 0; i < esc.length; i++) {
        var ch = esc[i];
        if (ch === '"') inStr = !inStr;
        if (ch === "'" && !inStr) {
          cut = i;
          break;
        }
      }
      if (cut >= 0) {
        codePart = esc.slice(0, cut);
        comment = '<span class="tok-com">' + esc.slice(cut) + "</span>";
      }
      codePart = codePart
        .replace(/("(?:[^"]|"")*")/g, '<span class="tok-str">$1</span>')
        .replace(KEYWORDS, '<span class="tok-kw">$1</span>')
        .replace(/\b(\d+(\.\d+)?)\b/g, '<span class="tok-num">$1</span>');
      return codePart + comment;
    });
    el.innerHTML = out.join("\n");
  }

  document.querySelectorAll("[data-vba]").forEach(highlight);
})();
