// 用語集アプリの検証ループのドライバ。ブラウザ操作4本と import を順に実行する。
// 実行: node verify-all.cjs [ラウンド名] [keep]
//   ラウンド名: スクリーンショットの保存先（既定 p2）
//   keep      : 登録と import を飛ばし、既存の検証 DB のまま operate 以降だけ回す
// サーバー（http://127.0.0.1:8000）は run-verify.ps1 が起動しておくこと。
// 各ステップのログは JSON で出力する。ok: false の項目が1つでもあれば非ゼロで終わる。
const { chromium } = require('playwright');
const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const APP = 'C:\\Users\\ss80751\\OneDrive - NK\\ドキュメント\\Work_Vault\\06_Tools\\用語集アプリ';
const DB_URL = 'sqlite:///C:/Users/ss80751/AppData/Local/Temp/kohden-code/glossary-deai/p2/verify.db';
const DATA_DIR = 'C:\\Users\\ss80751\\AppData\\Local\\Temp\\kohden-code\\glossary-deai\\p2';
const ROUND = process.argv[2] || 'p2';
const KEEP = process.argv[3] === 'keep';

function runBrowserScript(page, file) {
  const src = fs.readFileSync(path.join(__dirname, file), 'utf8');
  const fn = eval('(' + src + ')');
  return fn(page);
}

function hasFailure(log) {
  return Array.isArray(log) && log.some((e) => e && e.ok === false);
}

(async () => {
  globalThis.__GLOSSARY_ROUND = ROUND;
  let failed = false;
  const browser = await chromium.launch();
  // browser.newPage() の既定コンテキストは 2 ページ目を開けない（競合テストが newPage する）ため
  // 明示的にコンテキストを作る。画面幅は Playwright MCP の既定と同じ 1280x720。
  const context = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await context.newPage();
  try {
    const steps = KEEP
      ? ['operate_flows.js', 'check_state.js', 'queue_flows.js']
      : ['register_terms.js', 'IMPORT', 'operate_flows.js', 'check_state.js', 'queue_flows.js'];
    for (const step of steps) {
      if (step === 'IMPORT') {
        console.log('== import ==');
        const r = spawnSync(
          path.join(APP, '.venv', 'Scripts', 'python.exe'),
          ['tasks.py', 'import', path.join(__dirname, '資料')],
          {
            cwd: APP, encoding: 'utf8',
            env: { ...process.env, DATABASE_URL: DB_URL, GLOSSARY_DATA_DIR: DATA_DIR,
              SOURCE_BACKEND: 'export', LLM_BACKEND: 'mock', PYTHONIOENCODING: 'utf-8' },
          },
        );
        if (r.stdout) console.log(r.stdout);
        if (r.stderr) console.error(r.stderr);
        if (r.status !== 0) { console.error('== import FAILED =='); failed = true; break; }
        continue;
      }
      console.log('== ' + step + ' ==');
      const log = await runBrowserScript(page, step);
      console.log(JSON.stringify(log, null, 2));
      if (hasFailure(log)) { console.error('== ' + step + ' FAILED =='); failed = true; break; }
    }
  } catch (e) {
    console.error('== DRIVER ERROR ==');
    console.error(e);
    failed = true;
  } finally {
    await browser.close();
  }
  process.exit(failed ? 1 : 0);
})();
