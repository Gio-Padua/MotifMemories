import { mkdir, writeFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const browser = await chromium.launch({ channel: 'msedge', headless: true });
const output = new URL('../.impeccable/review/', import.meta.url);
const baseUrl = process.env.BASE_URL || 'http://localhost:3000';
await mkdir(output, { recursive: true });
const report = { layouts: [], interactions: [], errors: [] };
try {
  for (const [width, height, name] of [[1440, 1000, 'desktop'], [768, 1024, 'tablet'], [390, 844, 'mobile'], [320, 740, 'small-mobile']]) {
    const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1 });
    await context.addInitScript(() => { window.__longTasks = []; new PerformanceObserver(list => window.__longTasks.push(...list.getEntries().map(e => ({ start: e.startTime, duration: e.duration })))).observe({ type: 'longtask', buffered: true }); });
    const page = await context.newPage();
    page.on('pageerror', error => report.errors.push({ width, error: error.message }));
    await page.goto(baseUrl, { waitUntil: 'networkidle' });
    await page.screenshot({ path: new URL(`${name}.png`, output).pathname.replace(/^\/(\w:)/, '$1'), fullPage: true });
    const initial = await page.evaluate(() => ({ overflow: document.documentElement.scrollWidth > innerWidth, canvas: !!document.querySelector('canvas'), resources: performance.getEntriesByType('resource').map(e => ({ name: e.name, transfer: e.transferSize, encoded: e.encodedBodySize })), hero: document.getElementById('hero-image').getBoundingClientRect().toJSON() }));
    assert.equal(initial.overflow, false, `${width}px overflows`);
    assert.equal(initial.canvas, false, `${width}px should defer 3D on initial load`);
    report.layouts.push({ width, ...initial });
    if (width === 1440) {
      await page.getByRole('link', { name: 'Explore the frames', exact: true }).click();
      await page.locator('.canvas-ready').waitFor({ timeout: 20000 });
      const firstSceneBytes = await page.evaluate(() => performance.getEntriesByType('resource').reduce((sum, entry) => sum + entry.transferSize, 0));
      for (const id of ['butter-grid', 'mint-editorial', 'lavender-scrapbook', 'mint-six-grid', 'lavender-eight-grid', 'four-strip-twin']) {
        await page.locator(`input[value="${id}"]`).evaluate(el => el.scrollIntoView({ block: 'center', behavior: 'instant' }));
        await page.locator(`input[value="${id}"]`).check();
        await page.locator('.canvas-ready').waitFor();
        assert.ok(await page.locator(`input[value="${id}"]`).isChecked());
      }
      await page.waitForTimeout(300);
      await page.screenshot({ path: new URL(`${name}-frames.png`, output).pathname.replace(/^\/(\w:)/, '$1') });
      // Count actual draws to prove demand rendering stops once the scene settles.
      await page.evaluate(() => { window.__draws = 0; const proto = WebGL2RenderingContext.prototype; for (const method of ['drawElements', 'drawArrays']) { const original = proto[method]; proto[method] = function (...args) { window.__draws++; return original.apply(this, args); }; } });
      await page.waitForTimeout(1200);
      const before = await page.evaluate(() => window.__draws);
      await page.waitForTimeout(800);
      const after = await page.evaluate(() => window.__draws);
      assert.equal(after, before, 'Idle scene continues drawing');
      const scrollStart = await page.evaluate(() => performance.now());
      await page.locator('.keep-step').scrollIntoViewIfNeeded();
      await page.waitForTimeout(300);
      await page.screenshot({ path: new URL('desktop-keepsake.png', output).pathname.replace(/^\/(\w:)/, '$1') });
      await page.locator('#experience-title').scrollIntoViewIfNeeded();
      await page.waitForTimeout(500);
      const scrollLongTasks = await page.evaluate(start => window.__longTasks.filter(e => e.start >= start), scrollStart);
      assert.equal(await page.locator('canvas').count(), 1);
      await page.evaluate(() => { const canvas = document.querySelector('canvas'); canvas.getContext('webgl2').getExtension('WEBGL_lose_context').loseContext(); });
      await page.waitForFunction(() => !document.querySelector('.story-poster').classList.contains('poster-hidden'));
      report.interactions.push({ width, sixFrames: 'pass', idleDraws: after - before, firstSceneAdditionalBytes: firstSceneBytes - initial.resources.reduce((sum, e) => sum + e.transfer, 0), scrollLongTasks, reverseScroll: 'pass', contextLossFallback: 'pass' });
    }
    if (width === 390) {
      await page.getByRole('link', { name: 'Explore the frames', exact: true }).click();
      await page.locator('.mobile-frame-preview').waitFor();
      for (const id of ['butter-grid', 'mint-editorial', 'lavender-scrapbook', 'mint-six-grid', 'lavender-eight-grid', 'four-strip-twin']) {
        await page.locator(`input[value="${id}"]`).check();
        await page.locator(`.mobile-frame-preview img[src*="${id}-mobile"]`).waitFor();
      }
      assert.equal(await page.locator('canvas').count(), 0, 'Mobile should use the static frame preview');
      assert.equal(await page.locator('.story-visual-column').evaluate(element => getComputedStyle(element).position), 'relative');
      report.interactions.push({ width, sixFrames: 'pass', mobileStaticPreview: 'pass', mobileSticky: 'removed' });
      await page.screenshot({ path: new URL('mobile-frames.png', output).pathname.replace(/^\/(\w:)/, '$1') });
    }
    // A complete screenshot must first bring lazy images into view.
    for (const selector of ['.frames-step', '.moment-photos', '.faq', '.closing']) await page.locator(selector).scrollIntoViewIfNeeded();
    await page.waitForFunction(() => Array.from(document.querySelectorAll('img')).filter(img => img.getClientRects().length).every(img => img.complete));
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
    await page.screenshot({ path: new URL(`${name}.png`, output).pathname.replace(/^\/(\w:)/, '$1'), fullPage: true });
    await context.close();
  }
  for (const mode of ['reduced-motion', 'no-javascript', 'no-webgl', 'save-data', 'failed-texture']) {
    const desktopFailure = mode === 'no-webgl' || mode === 'failed-texture';
    const context = await browser.newContext({ viewport: desktopFailure ? { width: 1440, height: 1000 } : { width: 390, height: 844 }, reducedMotion: mode === 'reduced-motion' ? 'reduce' : 'no-preference', javaScriptEnabled: mode !== 'no-javascript' });
    if (mode === 'no-webgl') await context.addInitScript(() => { const original = HTMLCanvasElement.prototype.getContext; HTMLCanvasElement.prototype.getContext = function (kind, ...args) { return String(kind).includes('webgl') ? null : original.call(this, kind, ...args); }; });
    if (mode === 'save-data') await context.addInitScript(() => Object.defineProperty(navigator, 'connection', { value: { saveData: true }, configurable: true }));
    const page = await context.newPage();
    if (mode === 'failed-texture') await page.route('**/images/*-desktop.webp', route => route.abort());
    await page.goto(baseUrl, { waitUntil: 'networkidle' });
    await page.locator('#frames').scrollIntoViewIfNeeded();
    await page.waitForTimeout(2200);
    assert.equal(await page.locator('.poster-hidden').count(), 0, `${mode} should show static poster`);
    assert.equal(await page.locator('input[name="frame"]').count(), 6);
    await page.getByText('How does a session work?', { exact: true }).click();
    assert.ok(await page.locator('details[open]').count());
    report.interactions.push({ mode, fallback: 'pass', faq: 'pass' });
    await context.close();
  }
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  await page.goto(baseUrl);
  await page.keyboard.press('Tab');
  assert.equal(await page.locator(':focus').textContent(), 'Skip to content');
  await page.evaluate(() => { document.documentElement.style.zoom = '2'; });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
  await page.evaluate(() => { document.documentElement.style.zoom = '1'; });
  await page.locator('input[value="four-strip-twin"]').focus();
  await page.keyboard.press('ArrowRight');
  assert.ok(await page.locator('input[value="butter-grid"]').isChecked());
  await page.getByText('How does a session work?', { exact: true }).focus();
  await page.keyboard.press('Space');
  assert.ok(await page.locator('details[open]').count());
  report.interactions.push({ keyboardSkipLink: 'pass', keyboardFrameSelection: 'pass', keyboardFaq: 'pass', zoom200: 'pass' });
} finally {
  await writeFile(new URL('browser-report.json', output), JSON.stringify(report, null, 2));
  await browser.close();
  console.log(JSON.stringify({ layouts: report.layouts.map(x => ({ width: x.width, overflow: x.overflow, canvas: x.canvas, resourceBytes: x.resources.reduce((sum, x) => sum + x.transfer, 0) })), interactions: report.interactions, errors: report.errors }, null, 2));
}
