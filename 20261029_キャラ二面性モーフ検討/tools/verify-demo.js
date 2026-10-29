// 試作デモの自動点検（Playwright + 系統 Edge）。
// 使い方: node verify-demo.js
// 点検項目: コンソールエラー無し / 横溢れ無し(1280・390) / 濃色軸(自動・手動) /
//           hover 軸 / マスク走査 / グリッチの一射 / 縮小設定での退行
"use strict";
const path = require("path");
const { pathToFileURL } = require("url");
const fs = require("fs");
const { chromium } = require("playwright");

const DEMO = path.resolve(process.argv[2] || "");
const OUT = path.resolve(process.argv[3] || path.join(path.dirname(DEMO), "..", "shots"));
fs.mkdirSync(OUT, { recursive: true });

let passes = 0, failures = 0;
const ok = (name, cond, detail) => {
  if (cond) { passes++; console.log(`PASS ${name}`); }
  else { failures++; console.log(`FAIL ${name}${detail ? " — " + detail : ""}`); }
};

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

  // 自動+ライト: 煤の相は隠れている
  const uraOp = () => page.evaluate(() => {
    const el = document.querySelector(".tile.d-dark .face-ura");
    return Number(getComputedStyle(el).opacity);
  });
  ok("自動+灯: 煤の相は隠れる", (await uraOp()) < 0.05, `opacity=${await uraOp()}`);

  await page.screenshot({ path: path.join(OUT, "light-1280.png"), fullPage: true });

  // OS 設定を濃色へ（自動モードのまま・data-theme 無し）
  await page.emulateMedia({ colorScheme: "dark" });
  await page.waitForTimeout(900);
  ok("自動+煤(OS): 煤の相が浮かぶ", (await uraOp()) > 0.95, `opacity=${await uraOp()}`);
  ok("自動+煤(OS): data-theme は付かない", await page.evaluate(() => !document.documentElement.hasAttribute("data-theme")));
  await page.emulateMedia({ colorScheme: "light" });
  await page.waitForTimeout(900);

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
  await page.screenshot({ path: path.join(OUT, "dark-1280.png"), fullPage: true });

  // hover 軸（交差型）: ヴェル
  const verTile = page.locator(".tile.d-hover[data-morph='settle']").first();
  await verTile.hover();
  await page.waitForTimeout(850);
  const verUra = await page.evaluate(() => {
    const t = [...document.querySelectorAll(".tile.d-hover")].find((x) => x.dataset.morph === "settle");
    return Number(getComputedStyle(t.querySelector(".face-ura")).opacity);
  });
  ok("hover(交差型): 煤の相が浮かぶ", verUra > 0.95, `opacity=${verUra}`);

  // hover 軸（走査型）: マスク位置が動く
  const wipeTile = page.locator(".tile.d-wipe").first();
  const maskBefore = await wipeTile.evaluate((el) => getComputedStyle(el.querySelector(".face-ura")).maskPosition);
  await wipeTile.hover();
  await page.waitForTimeout(850);
  const maskAfter = await wipeTile.evaluate((el) => getComputedStyle(el.querySelector(".face-ura")).maskPosition);
  ok("hover(走査型): マスクが走る", maskBefore !== maskAfter, `before=${maskBefore} after=${maskAfter}`);
  await page.screenshot({ path: path.join(OUT, "hover-1280.png"), fullPage: false });

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
  await rpage.screenshot({ path: path.join(OUT, "reduced-dark-1280.png"), fullPage: true });
  await rctx.close();

  await ctx.close();
  await browser.close();

  ok("コンソールエラー無し", errors.length === 0, errors.join(" / ").slice(0, 400));
  console.log(`\n結果: ${passes} PASS / ${failures} FAIL`);
  process.exit(failures ? 1 : 0);
})().catch((e) => { console.error("点検の実行に失敗:", e); process.exit(2); });
