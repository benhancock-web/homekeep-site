// Stage E on the live site: every internal link resolves, LCP on a throttled 4G connection,
// keyboard focus ring visible, four widths × two themes rendered without horizontal overflow.
const { chromium } = require(process.env.PLAYWRIGHT_PATH || '/home/claude/.npm-global/lib/node_modules/playwright');
const BASE = process.argv[2] || 'https://benhancock-web.github.io/homekeep-site';
const pages = ['', 'find-a-cleaner/', 'cleaners/', 'cleaners/example-maria/', 'become-a-cleaner/', 'cleaner-app/', 'pricing/', 'about/', 'contact/', 'legal/', 'legal/terms-for-households/', 'legal/terms-for-cleaners/', 'legal/privacy/', 'legal/cookies/', 'legal/insurance-and-complaints/', 'legal/modern-slavery/', 'legal/delete-account/'];
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const issues = [];
  // 1. links
  const ctx = await browser.newContext();
  const seen = new Set();
  for (const p of pages) {
    const page = await ctx.newPage();
    const r = await page.goto(BASE + '/' + p, { waitUntil: 'load' });
    if (r.status() !== 200) issues.push(`page ${p}: ${r.status()}`);
    const hrefs = await page.$$eval('a[href]', as => as.map(a => a.href));
    for (const h of hrefs) {
      if (!h.startsWith(BASE) || seen.has(h)) continue;
      seen.add(h);
      const res = await page.request.get(h.split('#')[0]);
      if (res.status() !== 200) issues.push(`${p} -> ${h}: ${res.status()}`);
    }
    await page.close();
  }
  console.log('links checked:', seen.size);
  await ctx.close();
  // 2. widths × themes, overflow
  for (const theme of ['light', 'dark']) for (const w of [390, 768, 1024, 1280]) {
    const c = await browser.newContext({ viewport: { width: w, height: 900 }, colorScheme: theme });
    for (const p of pages) {
      const page = await c.newPage();
      await page.goto(BASE + '/' + p, { waitUntil: 'networkidle' });
      const over = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      if (over > 0) issues.push(`${p} ${w} ${theme}: overflow ${over}px`);
      if (w === 768 || w === 1024) await page.screenshot({ path: `shots/live-${(p || 'home').replace(/[\/]+/g, '-').replace(/-$/, '')}-${w}-${theme}.png`, fullPage: false });
      await page.close();
    }
    await c.close();
  }
  // 3. LCP on throttled 4G (1.6 Mbps down, 150 ms RTT), mobile CPU 4x slower, cold cache
  for (const p of ['', 'become-a-cleaner/']) {
    const c = await browser.newContext({ viewport: { width: 390, height: 844 } });
    const page = await c.newPage();
    const cdp = await c.newCDPSession(page);
    await cdp.send('Network.enable');
    await cdp.send('Network.emulateNetworkConditions', { offline: false, latency: 150, downloadThroughput: 1.6 * 1024 * 1024 / 8, uploadThroughput: 750 * 1024 / 8 });
    await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
    await page.addInitScript(() => { window.__lcp = 0; new PerformanceObserver(l => { for (const e of l.getEntries()) window.__lcp = e.startTime; }).observe({ type: 'largest-contentful-paint', buffered: true }); });
    await page.goto(BASE + '/' + p, { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);
    const lcp = await page.evaluate(() => window.__lcp);
    console.log(`LCP ${p || 'home'} (4G, 4x CPU): ${Math.round(lcp)} ms`);
    if (lcp > 2000) issues.push(`LCP ${p || 'home'} ${Math.round(lcp)}ms > 2000`);
    await c.close();
  }
  // 4. keyboard: tab through the home page, focus ring visible on the first link and the brass button
  const kc = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const kp = await kc.newPage();
  await kp.goto(BASE + '/', { waitUntil: 'networkidle' });
  const names = [];
  for (let i = 0; i < 8; i++) { await kp.keyboard.press('Tab'); names.push(await kp.evaluate(() => { const e = document.activeElement; const cs = getComputedStyle(e); return (e.textContent.trim().slice(0, 30) || e.tagName) + ' [outline ' + cs.outlineWidth + ' ' + cs.outlineStyle + ']'; })); }
  console.log('tab order:', names.join(' → '));
  await kp.keyboard.press('Tab');
  await kp.screenshot({ path: 'shots/live-focus.png', clip: { x: 0, y: 0, width: 1280, height: 500 } });
  await kc.close();
  await browser.close();
  console.log(issues.length ? 'ISSUES:\n' + issues.join('\n') : 'ALL CLEAR');
})();
