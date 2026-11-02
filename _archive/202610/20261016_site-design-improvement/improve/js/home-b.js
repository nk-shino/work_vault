
"use strict";

document.getElementById("jump").addEventListener("submit", (e) => {
  e.preventDefault();
  const word = document.getElementById("q").value.trim();
  const line = document.getElementById("line");
  if (word) {
    location.href = "catalog-b.html?q=" + encodeURIComponent(word);
  } else {
    line.textContent = "検索語が空。そのまま目録棚を開くこともできる。";
  }
});
