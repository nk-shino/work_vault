// 試作デモの自動点検（Playwright + 系統 Edge）。
// 使い方: node verify-demo.js [demo/index.html] [shots出力先]
// 点検項目: コンソールエラー無し / 横溢れ無し(1280・390) / 濃色主軸（自動・手動・全題箋） /
//           hover 軸（交差・走査・解除） / グリッチの一射と字の限定 / データモデルの一致と正規化 /
//           押印操作子の不在（S-19） / タッチ（hover 無し）での非反応と濃色確認 / 縮小設定での退行
// 2026-10-30: 確定仕様（めもB・台帳 S-19）の点検項目を追加。既存 15 項目は基準値を変えずに保持し、
//             hover の 2 項目だけは意味を保つため手動煤の前（灯モード）へ移動した。
"use strict";
const path = require("path");
const { pathToFileURL } = require("url");
const fs = require("fs");
const { chromium } = require("playwright");

const DEMO = path.resolve(process.argv[2] || "");
const OUT = path.resolve(process.argv[3] || path.join(path.dirname(DEMO), "..", "shots"));
fs.mkdirSync(OUT, { recursive: true });

let passes = 0, failures = 0, skips = 0;
const ok = (name, cond, detail) => {
  if (cond) { passes++; console.log(`PASS ${name}${detail ? " — " + detail : ""}`); }
  else { failures++; console.log(`FAIL ${name}${detail ? " — " + detail : ""}`); }
};
const skip = (msg) => { skips++; console.log(`SKIP ${msg}`); };

const DUAL_IDS = ["c001", "c003", "c002", "c004", "c005", "c008", "c009"];
const WIPE_IDS = ["c004", "c005"];

// 各題箋の煤の相の実測値（opacity とマスク位置）。単面の題箋は null。
const state = (p) => p.evaluate(() => {
  const read = (el) => {
    const cs = getComputedStyle(el);
    return { op: Number(cs.opacity), mask: cs.maskPosition || cs.webkitMaskPosition || "" };
  };
  const out = {};
  for (const t of document.querySelectorAll(".tile[data-char]")) {
    const ura = t.querySelector(".face-ura");
    out[t.dataset.char] = ura ? read(ura) : null;
  }
  const single = document.querySelector('.tile[data-char="c013"] .plate');
  out.__single = single ? { dual: single.classList.contains("dual"), single: single.classList.contains("single") } : null;
  return out;
});

const judgeDual = (st, shown) => {
  const bad = [];
  for (const id of DUAL_IDS) {
    const s = st[id];
    if (!s) { bad.push(`${id}: face-ura なし`); continue; }
    if (WIPE_IDS.includes(id)) {
      /* 罫走の煤の相は opacity 1 のまま mask で隠す。判定は mask 位置で行う。
         computed 値は shown="0px 0px" / hidden="100% 0px" に正規化される */
      const mask = String(s.mask);
      const maskOk = shown ? !mask.startsWith("100") : mask.startsWith("100");
      if (!maskOk) bad.push(`${id}: mask=${mask}`);
    } else {
      const opOk = shown ? s.op > 0.95 : s.op < 0.05;
      if (!opOk) bad.push(`${id}: opacity=${s.op}`);
    }
  }
  return bad;
};

// 押印（押下）の操作子が頁に存在しないこと。開閉器（.seg のテーマ固定）だけが button。
const pressProbe = (p) => p.evaluate(() => ({
  tileControls: document.querySelectorAll('.tile button, .tile [role="button"], .tile [aria-pressed], [data-press]').length,
  segButtons: document.querySelectorAll(".seg button").length,
  allButtons: document.querySelectorAll("button").length,
}));

(async () => {
  const url = pathToFileURL(DEMO).href;
  const browser = await chromium.launch({ channel: "msedge" });
  const errors = [];

  // ---- デスクトップ(1280) ----
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();
  page.on("console", (m) => { if (m.type() === "error") errors.push(`console: ${m.text()}`); });
  page.on("pageerror", (e) => errors.push(`pageerror: ${e}`));
  await page.emulateMedia({ colorScheme: "light" });
  await page.goto(url);
  await page.waitForTimeout(900);

  const overflow = (p) => p.evaluate(() =>
    ({ sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));
  let o = await overflow(page);
  ok("1280px: 横溢れなし", o.sw <= o.cw, `scrollWidth=${o.sw} clientWidth=${o.cw}`);

  // 自動+灯: 煤の相は隠れている（主軸の題箋と hover 軸の題箋の双方）
  const uraOp = () => page.evaluate(() => {
    const el = document.querySelector(".tile.d-dark .face-ura");
    return Number(getComputedStyle(el).opacity);
  });
  ok("自動+灯: 煤の相は隠れる", (await uraOp()) < 0.05, `opacity=${await uraOp()}`);
  let st = await state(page);
  ok("自動+灯: hover軸の題箋も煤の相は隠れる", judgeDual(st, false).length === 0, judgeDual(st, false).join(" / ") || `c002 opacity=${st.c002.op}`);

  await page.screenshot({ path: path.join(OUT, "light-1280.png"), fullPage: true });

  // OS 設定を濃色へ（自動モードのまま・data-theme 無し）
  await page.emulateMedia({ colorScheme: "dark" });
  await page.waitForTimeout(1200);
  ok("自動+煤(OS): 煤の相が浮かぶ", (await uraOp()) > 0.95, `opacity=${await uraOp()}`);
  ok("自動+煤(OS): data-theme は付かない", await page.evaluate(() => !document.documentElement.hasAttribute("data-theme")));
  st = await state(page);
  const badOs = judgeDual(st, true);
  ok("自動+煤(OS): 主軸は全ての二面題箋に効く", badOs.length === 0, badOs.join(" / ") || DUAL_IDS.map((id) => `${id} op=${st[id].op}`).join(" "));
  await page.emulateMedia({ colorScheme: "light" });
  await page.waitForTimeout(1200);
  st = await state(page);
  const badBack = judgeDual(st, false);
  ok("灯へ戻す: 全ての題箋が灯の相へ戻る", badBack.length === 0, badBack.join(" / ") || `c002 opacity=${st.c002.op}`);

  // hover 軸（補助・ポインタ環境）— 灯の相のまま確認する
  const verTile = page.locator('.tile[data-char="c002"]').first();
  await verTile.hover();
  await page.waitForTimeout(850);
  st = await state(page);
  ok("hover(交差型): 煤の相が浮かぶ", st.c002.op > 0.95, `opacity=${st.c002.op}`);
  await page.mouse.move(8, 8); /* ポインタを題箋の外へ */
  await page.waitForTimeout(850);
  st = await state(page);
  ok("hover を外す: 灯の相へ戻る", st.c002.op < 0.05, `opacity=${st.c002.op}`);

  const wipeTile = page.locator('.tile[data-char="c004"]').first();
  const maskBefore = await wipeTile.evaluate((el) => getComputedStyle(el.querySelector(".face-ura")).maskPosition);
  await wipeTile.hover();
  await page.waitForTimeout(850);
  const maskAfter = await wipeTile.evaluate((el) => getComputedStyle(el.querySelector(".face-ura")).maskPosition);
  ok("hover(走査型): マスクが走る", maskBefore !== maskAfter, `before=${maskBefore} after=${maskAfter}`);
  await page.screenshot({ path: path.join(OUT, "hover-1280.png"), fullPage: false });

  // 押印（押下）の操作子は設けていない（台帳 S-19: 詳細頁での提供を待つ）
  const press = await pressProbe(page);
  ok("押印の操作子は無い（S-19）", press.tileControls === 0 && press.allButtons === press.segButtons,
    `tile内操作子=${press.tileControls} button数=${press.allButtons}(開閉器=${press.segButtons})`);

  // 手動で煤へ → グリッチの一射と交差を確認
  await page.click('.seg button[data-mode="dark"]');
  await page.waitForTimeout(120);
  ok("手動煤: theme-flipped が付く", await page.evaluate(() => document.documentElement.classList.contains("theme-flipped")));
  const gritAnim = await page.evaluate(() => {
    const g = document.querySelector(".tile.g-dark .grit.g1");
    return getComputedStyle(g).animationName;
  });
  ok("手動煤: グリッチ断片が走る", gritAnim === "grit-a", `animation-name=${gritAnim}`);
  await page.waitForTimeout(800);
  ok("手動煤: 煤の相が浮かぶ", (await uraOp()) > 0.95, `opacity=${await uraOp()}`);
  await page.waitForTimeout(700); /* 段差（--i×110ms）の分を足して全題箋の交差を待つ */
  st = await state(page);
  const badMan = judgeDual(st, true);
  ok("手動煤: 主軸は全ての二面題箋に効く", badMan.length === 0, badMan.join(" / ") || DUAL_IDS.map((id) => `${id} op=${st[id].op}`).join(" "));
  ok("単面の題箋は二面構造を持たない", st.__single && !st.__single.dual && st.__single.single, JSON.stringify(st.__single));
  const gritScope = await page.evaluate(() => {
    const owners = [...new Set([...document.querySelectorAll(".grit")].map((g) => g.closest(".tile")?.dataset.char))];
    return { total: document.querySelectorAll(".grit").length, owners };
  });
  ok("走りの字は限定（ノクス・アレルイのみ）",
    gritScope.total === 4 && gritScope.owners.length === 2 && gritScope.owners.includes("c008") && gritScope.owners.includes("c009"),
    `断片=${gritScope.total}所有=${gritScope.owners.join(",")}`);
  await page.screenshot({ path: path.join(OUT, "dark-1280.png"), fullPage: true });

  // データモデル: 埋め込みデータと題箋の割当が一致し、正規化が働く
  const dm = await page.evaluate(() => {
    const { characters, dualityOf, axisClasses } = window.__duality;
    const mism = [];
    for (const c of characters) {
      const tile = document.querySelector(`.tile[data-char="${c.id}"]`);
      if (!tile) { mism.push(`${c.id}: tile なし`); continue; }
      const expect = axisClasses(dualityOf(c)).sort().join(" ");
      const actual = [...tile.classList].filter((x) => x !== "tile").sort().join(" ");
      if (expect !== actual) mism.push(`${c.id}: 期待[${expect}] 実際[${actual}]`);
      const plate = tile.querySelector(".plate");
      if (!plate) { mism.push(`${c.id}: plate なし`); continue; }
      const d = dualityOf(c);
      const wantLabel = d
        ? `${c.name}の肖像（${d.faces.omote.label}／${d.faces.ura.label}）`
        : `${c.name}の肖像（準備中）`;
      if (plate.getAttribute("aria-label") !== wantLabel) mism.push(`${c.id}: aria-label 不一致`);
    }
    return { count: characters.length, tiles: document.querySelectorAll(".tile[data-char]").length, mism };
  });
  ok("データモデル: 埋め込みデータと題箋の割当が一致",
    dm.count === 8 && dm.tiles === 8 && dm.mism.length === 0,
    `字数=${dm.count} 題箋=${dm.tiles} ${dm.mism.join(" / ")}`);
  const nz = await page.evaluate(() => {
    const { dualityOf } = window.__duality;
    const a = dualityOf({ duality: { trigger: "sparkle", morph: "storm", faces: { omote: { label: "灯の相" }, ura: { label: "煤の相" } } } });
    const b = dualityOf({ name: "単面の字" });
    return { trig: a.trigger, morph: a.morph, single: b === null };
  });
  ok("データモデル: 不明値は既定（dark/settle）・省略は単面",
    nz.trig === "dark" && nz.morph === "settle" && nz.single, JSON.stringify(nz));
  // 静的 markup（noscript 用）もデータと一致するか。JS が適用する前の記述を直接読む
  const src = fs.readFileSync(DEMO, "utf8");
  const expectCls = {
    c001: ["d-dark"], c003: ["d-dark"], c002: ["d-dark", "d-hover"],
    c004: ["d-dark", "d-hover", "d-wipe"], c005: ["d-dark", "d-hover", "d-wipe"],
    c008: ["d-dark", "g-dark"], c009: ["d-dark", "g-dark", "d-hover", "g-hover"], c013: [],
  };
  const srcBad = [];
  for (const [id, cls] of Object.entries(expectCls)) {
    const m = src.match(new RegExp(`<li class="([^"]*)" data-char="${id}"`));
    if (!m) { srcBad.push(`${id}: 記述なし`); continue; }
    const have = m[1].split(/\s+/).filter((x) => x !== "tile");
    const missing = cls.filter((c) => !have.includes(c));
    const extra = have.filter((c) => !cls.includes(c));
    if (missing.length || extra.length) srcBad.push(`${id}: 不足[${missing}] 過剰[${extra}]`);
  }
  ok("静的 markup: noscript 用の割当がデータと一致", srcBad.length === 0, srcBad.join(" / "));

  // ---- モバイル(390) ----
  const mctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
  const mpage = await mctx.newPage();
  mpage.on("pageerror", (e) => errors.push(`pageerror(390): ${e}`));
  await mpage.goto(url);
  await mpage.waitForTimeout(900);
  const mo = await overflow(mpage);
  ok("390px: 横溢れなし", mo.sw <= mo.cw, `scrollWidth=${mo.sw} clientWidth=${mo.cw}`);
  await mpage.screenshot({ path: path.join(OUT, "mobile-390.png"), fullPage: true });
  await mctx.close();

  // ---- タッチ（hover 無し環境）: 押印・hover は出ず、濃色で確認できる ----
  const tctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
  const tpage = await tctx.newPage();
  tpage.on("pageerror", (e) => errors.push(`pageerror(touch): ${e}`));
  await tpage.goto(url);
  await tpage.waitForTimeout(900);
  try {
    const cdp = await tctx.newCDPSession(tpage);
    await cdp.send("Emulation.setEmulatedMedia", {
      features: [{ name: "hover", value: "none" }, { name: "pointer", value: "coarse" }],
    });
  } catch (e) {
    errors.push(`cdp(hover emulation): ${e}`);
  }
  const media = await tpage.evaluate(() => ({
    hoverHover: matchMedia("(hover: hover)").matches,
    pointerCoarse: matchMedia("(pointer: coarse)").matches,
  }));
  if (!media.hoverHover) {
    await tpage.tap('.tile[data-char="c002"] .plate');
    await tpage.waitForTimeout(900);
    const tst = await state(tpage);
    ok("タッチ: 触れても煤の相は出ない（hover 無し環境）", tst.c002.op < 0.05,
      `hover:hover=false pointer:coarse=${media.pointerCoarse} opacity=${tst.c002.op}`);
  } else {
    skip(`タッチ: hover 無し環境を用意できず（hover:hover=true pointer:coarse=${media.pointerCoarse}）— 濃色確認のみ実施`);
  }
  const tpress = await pressProbe(tpage);
  ok("タッチ: 押印の操作子は無い", tpress.tileControls === 0 && tpress.allButtons === tpress.segButtons,
    `tile内操作子=${tpress.tileControls} button数=${tpress.allButtons}`);
  await tpage.tap('.seg button[data-mode="dark"]');
  await tpage.waitForTimeout(1700);
  const tstd = await state(tpage);
  const badTouch = judgeDual(tstd, true);
  ok("タッチ: 濃色で全ての煤の相を確認できる", badTouch.length === 0, badTouch.join(" / ") || DUAL_IDS.map((id) => `${id} op=${tstd[id].op}`).join(" "));
  await tpage.screenshot({ path: path.join(OUT, "touch-dark-390.png"), fullPage: true });
  await tctx.close();

  // ---- 縮小設定 ----
  const rctx = await browser.newContext({ viewport: { width: 1280, height: 900 }, reducedMotion: "reduce" });
  const rpage = await rctx.newPage();
  rpage.on("pageerror", (e) => errors.push(`pageerror(reduced): ${e}`));
  await rpage.goto(url);
  await rpage.waitForTimeout(400);
  const gritHidden = await rpage.evaluate(() => {
    const g = document.querySelector(".grit.g1");
    return getComputedStyle(g).display === "none";
  });
  ok("縮小設定: 断片は出ない", gritHidden);
  const tDur = await rpage.evaluate(() => {
    const f = document.querySelector(".tile.d-dark .face-ura");
    return getComputedStyle(f).transitionDuration;
  });
  ok("縮小設定: 交差は即時", tDur === "0s", `transition-duration=${tDur}`);
  await rpage.click('.seg button[data-mode="dark"]');
  await rpage.waitForTimeout(150);
  ok("縮小設定: 手動煤でも走らない", await rpage.evaluate(() => {
    const g = document.querySelector(".tile.g-dark .grit.g1");
    return getComputedStyle(g).display === "none" && getComputedStyle(g).animationName === "none";
  }));
  const rUra = await rpage.evaluate(() => Number(getComputedStyle(document.querySelector(".tile.d-dark .face-ura")).opacity));
  ok("縮小設定: 煤の相は即時に浮かぶ", rUra > 0.95, `opacity=${rUra}`);
  const rVer = await rpage.evaluate(() => Number(getComputedStyle(document.querySelector('.tile[data-char="c002"] .face-ura')).opacity));
  ok("縮小設定: hover軸の題箋も濃色で即時に浮かぶ", rVer > 0.95, `opacity=${rVer}`);
  const rBlur = await rpage.evaluate(() => getComputedStyle(document.querySelector('.tile[data-char="c002"] .face-ura')).filter);
  ok("縮小設定: ぼけは出ない", rBlur === "none", `filter=${rBlur}`);
  await rpage.screenshot({ path: path.join(OUT, "reduced-dark-1280.png"), fullPage: true });
  await rctx.close();

  await ctx.close();
  await browser.close();

  ok("コンソールエラー無し", errors.length === 0, errors.join(" / ").slice(0, 400));
  console.log(`\n結果: ${passes} PASS / ${failures} FAIL${skips ? ` / ${skips} SKIP` : ""}`);
  process.exit(failures ? 1 : 0);
})().catch((e) => { console.error("点検の実行に失敗:", e); process.exit(2); });
