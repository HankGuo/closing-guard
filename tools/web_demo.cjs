const { chromium } = require('/Users/hankia/AISpace/closing-guard/web/node_modules/playwright');
const path = require('path');

const ROOT = '/Users/hankia/AISpace/closing-guard';
const SHOTS = path.join(ROOT, 'docs', 'screenshots');

(async () => {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    args: [
      '--use-fake-device-for-media-stream',
      '--use-fake-ui-for-media-stream',
      '--use-file-for-fake-video-capture=/tmp/valve.y4m',
    ],
  });
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    recordVideo: { dir: path.join(ROOT, 'runs', 'video'), size: { width: 1440, height: 900 } },
  });
  const page = await context.newPage();
  const shot = (name) => page.screenshot({ path: path.join(SHOTS, name) });
  page.on('console', (m) => { if (m.type() === 'error') console.log('PAGE ERROR:', m.text()); });

  const strip = () => page.locator('.result-strip').innerText().catch(() => '');
  const confirmIfPossible = async () => {
    const btn = page.getByRole('button', { name: '人工确认通过' });
    if (await btn.count()) {
      await btn.first().click();
      await page.waitForTimeout(1500);
      return true;
    }
    return false;
  };

  await page.goto('http://127.0.0.1:8010/', { waitUntil: 'networkidle' });
  await page.waitForTimeout(800);
  await shot('web_01_home.png');

  const sid = await page.evaluate(async () => {
    const r = await fetch('/api/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ store_name: '老张牛肉面（演示店）', checklist_id: 'restaurant_closing', operator: '店员小王' }),
    });
    const s = await r.json();
    location.href = '/session/' + s.id;
    return s.id;
  });
  console.log('session', sid);
  await page.waitForTimeout(2500);
  await shot('web_02_session.png');

  // Real camera path: Chromium's fake camera is fed a real photo of a valve.
  await page.getByRole('button', { name: '拍照核验' }).click();
  await page.waitForTimeout(12000);
  await shot('web_03_camera_verdict.png');
  console.log('camera:', (await strip()).replace(/\n/g, ' | ').slice(0, 200));

  // If the live camera framing is not accepted, use the real sample photo.
  if (/未通过|待确认/.test(await strip())) {
    await page.locator('select[aria-label="使用样张"]').selectOption('/samples/gas_valve_closed.jpg');
    await page.waitForTimeout(12000);
  }
  await confirmIfPossible();
  await shot('web_04_gas_confirm.png');

  const pick = async (cp, sample, name) => {
    await page.locator('.check-item').filter({ hasText: cp }).first().click();
    await page.waitForTimeout(500);
    await page.locator('select[aria-label="使用样张"]').selectOption(sample);
    await page.waitForTimeout(12000);
    console.log(cp, ':', (await strip()).replace(/\n/g, ' | ').slice(0, 180));
    await confirmIfPossible();
    await shot(name);
  };

  await pick('配电箱', '/samples/power_panel_off.jpg', 'web_05_panel.png');
  await pick('后门/总门门锁', '/samples/door_locked.jpg', 'web_06_door.png');
  await pick('燃气表读数', '/samples/gas_meter_card.jpg', 'web_07_meter.png');

  const complete = page.getByRole('button', { name: /完成并生成台账/ });
  console.log('complete enabled:', await complete.isEnabled().catch(() => false));
  if (await complete.count()) {
    await complete.click();
    await page.waitForTimeout(3000);
  }
  console.log('final url', page.url());
  await page.waitForTimeout(800);
  await shot('web_08_report.png');
  await context.close();
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
