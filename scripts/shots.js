// Headless screenshots of every built page at mobile + desktop, both themes.
// node scripts/shots.js [base-url]   → shots/<page>-<width>-<theme>.png
const { chromium } = require(process.env.PLAYWRIGHT_PATH || '/home/claude/.npm-global/lib/node_modules/playwright');
const fs = require('fs'), path = require('path');
const BASE = process.argv[2] || 'http://localhost:8080/homekeep-site';
const pages = ['', 'find-a-cleaner/', 'cleaners/', 'cleaners/example-maria/', 'become-a-cleaner/', 'cleaner-app/', 'pricing/', 'about/', 'contact/', 'legal/', 'legal/privacy/', 'legal/delete-account/', '404.html'];
const widths = (process.env.WIDTHS || '390,1280').split(',').map(Number);
const themes = (process.env.THEMES || 'light,dark').split(',');
(async () => {
  fs.mkdirSync('shots', { recursive: true });
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/opt/pw-browsers/chromium-1194/chrome-linux/chrome' });
  const errors = [];
  for (const theme of themes) for (const w of widths) {
    const ctx = await browser.newContext({ viewport: { width: w, height: w < 600 ? 844 : 900 }, colorScheme: theme, deviceScaleFactor: 1 });
    for (const p of pages) {
      const page = await ctx.newPage();
      page.on('console', m => { if (m.type() === 'error') errors.push(`${p} ${w} ${theme}: ${m.text()}`); });
      page.on('requestfailed', r => errors.push(`${p} ${w} ${theme}: FAILED ${r.url()}`));
      page.on('response', r => { if (r.status() >= 400) errors.push(`${p} ${w} ${theme}: ${r.status()} ${r.url()}`); });
      const url = BASE + '/' + p;
      await page.goto(url, { waitUntil: 'networkidle' });
      const name = (p || 'home').replace(/[\/.]+/g, '-').replace(/-$/, '');
      await page.screenshot({ path: `shots/${name}-${w}-${theme}.png`, fullPage: true });
      // horizontal overflow check
      const over = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      if (over > 0) errors.push(`${p} ${w} ${theme}: horizontal overflow ${over}px`);
      await page.close();
    }
    await ctx.close();
  }
  await browser.close();
  fs.writeFileSync('shots/errors.txt', errors.join('\n'));
  console.log(errors.length ? 'ISSUES:\n' + errors.join('\n') : 'no console errors, failed requests or overflow');
})();
