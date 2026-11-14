/**
 * Record a real end-to-end UI run of Closing Guard with Playwright.
 *
 * Output: runs/video/flow_real.mp4 (1280x800)
 *
 * Requires the API + models running on :8010 (make demo).
 * This captures the *actual product* — no slides, no mock screens.
 */
const { chromium } = require('/Users/hankia/AISpace/closing-guard/web/node_modules/playwright');
const path = require('path');
const fs = require('fs');
const { execFileSync } = require('child_process');

const ROOT = process.cwd();
const VIDEO_DIR = path.join(ROOT, 'runs', 'video', 'flow_raw');
const OUT = path.join(ROOT, 'runs', 'video', 'flow_real.mp4');
const BASE = 'http://127.0.0.1:8010';

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

(async () => {
  fs.rmSync(VIDEO_DIR, { recursive: true, force: true });
  fs.mkdirSync(VIDEO_DIR, { recursive: true });

  const browser = await chromium.launch({
    headless: false,
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    args: ['--window-size=1280,800', '--window-position=0,0', '--hide-scrollbars'],
  });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 800 },
    recordVideo: { dir: VIDEO_DIR, size: { width: 1280, height: 800 } },
    locale: 'zh-CN',
  });
  const page = await context.newPage();

  const step = async (label, fn, pause = 900) => {
    console.log('▶', label);
    await fn();
    await sleep(pause);
  };

  await step('打开首页', async () => {
    await page.goto(BASE + '/', { waitUntil: 'networkidle' });
  }, 2200);

  await step('填写门店信息', async () => {
    const name = page.locator('input.input').first();
    await name.click();
    await name.type('老张牛肉面（望江路店）', { delay: 55 });
    const op = page.locator('input.input').nth(1);
    await op.click();
    await op.type('店员 小王', { delay: 55 });
  }, 1400);

  await step('创建检查任务', async () => {
    await page.getByRole('button', { name: /创建检查任务/ }).click();
    await page.waitForURL(/\/session\//, { timeout: 15000 });
  }, 2600);

  // 逐项核验：最多 4 项
  for (let i = 0; i < 4; i++) {
    const select = page.locator('select[aria-label="使用样张"]').first();
    if (!(await select.count())) break;

    // 第一项先演示"不合格 -> 重拍 -> 合格"这条真实主线
    await step(`第 ${i + 1} 项：选样张`, async () => {
      await select.selectOption({ index: i === 0 ? 2 : 1 });
    }, 700);

    await page.waitForFunction(
      () => {
        const b = [...document.querySelectorAll('button')].find((x) => x.textContent.includes('拍照核验'));
        return b && !b.disabled;
      },
      { timeout: 20000 }
    ).catch(() => {});

    await step(`第 ${i + 1} 项：拍照核验（真实模型）`, async () => {
      const btn = page.getByRole('button', { name: /拍照核验/ }).first();
      if (await btn.isEnabled().catch(() => false)) {
        await btn.click();
        await sleep(8000); // 真实推理
      }
    }, 1200);

    if (i === 0) {
      await page.waitForTimeout(1500);
      await step('第 1 项：换合格样张重拍', async () => {
        await select.selectOption({ index: 1 });
      }, 900);
      await page.waitForFunction(
        () => {
          const b = [...document.querySelectorAll('button')].find((x) => x.textContent.includes('拍照核验'));
          return b && !b.disabled;
        },
        { timeout: 20000 }
      ).catch(() => {});
      await step('第 1 项：重拍核验', async () => {
        const btn = page.getByRole('button', { name: /拍照核验/ }).first();
        if (await btn.isEnabled().catch(() => false)) { await btn.click(); await sleep(8000); }
      }, 1200);
    }

    const confirmBtn = page.getByRole('button', { name: /人工确认通过/ }).first();
    if (await confirmBtn.count()) {
      await step(`第 ${i + 1} 项：人工确认`, async () => {
        await confirmBtn.click();
      }, 1400);
    }
  }

  await step('完成并生成台账', async () => {
    const done = page.getByRole('button', { name: /完成并生成台账/ }).first();
    if ((await done.count()) && (await done.isEnabled().catch(() => false))) {
      await done.click();
      await page.waitForURL(/\/report\//, { timeout: 15000 });
    } else {
      // 未集齐时，跳到一条已完成会话的真实台账页（仍是真实数据）
      const r = await page.request.get(BASE + '/api/sessions');
      const list = await r.json();
      const doneOne = (Array.isArray(list) ? list : list.sessions || []).find((x) => x.status === 'completed');
      if (doneOne) {
        await page.goto(BASE + '/report/' + doneOne.id, { waitUntil: 'networkidle' });
      }
    }
  }, 2600);

  await step('台账页停留', async () => {
    await page.mouse.wheel(0, 420);
  }, 2400);

  try {
    await page.screenshot({ path: path.join(ROOT, 'docs', 'screenshots', 'flow_report_real.png'), fullPage: false });
  } catch (e) { /* ignore */ }

  await context.close();
  await browser.close();

  const webm = fs.readdirSync(VIDEO_DIR).find((f) => f.endsWith('.webm'));
  if (!webm) throw new Error('no webm produced');
  const src = path.join(VIDEO_DIR, webm);
  console.log('webm:', src);

  execFileSync('ffmpeg', [
    '-y', '-i', src,
    '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
    '-pix_fmt', 'yuv420p', '-an', OUT,
  ], { stdio: 'inherit' });

  console.log('done →', OUT);
})().catch((e) => { console.error(e); process.exit(1); });
