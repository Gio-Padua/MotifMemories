import { mkdir, writeFile } from 'node:fs/promises';
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
const { default: lighthouse } = await import(process.env.LIGHTHOUSE_MODULE || 'lighthouse');
const output = new URL('../.impeccable/review/', import.meta.url);
await mkdir(output, { recursive: true });
const results = [];
for (let run = 1; run <= 3; run++) {
  const browser = await chromium.launch({ channel: 'msedge', headless: true, args: ['--remote-debugging-port=9233'] });
  try {
    const { lhr } = await lighthouse('http://localhost:3000', { port: 9233, logLevel: 'error', onlyCategories: ['performance', 'accessibility', 'best-practices', 'seo'] });
    await writeFile(new URL(`lighthouse-${run}.json`, output), JSON.stringify(lhr, null, 2));
    const metrics = { run, performance: lhr.categories.performance.score * 100, accessibility: lhr.categories.accessibility.score * 100, bestPractices: lhr.categories['best-practices'].score * 100, seo: lhr.categories.seo.score * 100, lcp: lhr.audits['largest-contentful-paint'].numericValue, cls: lhr.audits['cumulative-layout-shift'].numericValue, tbt: lhr.audits['total-blocking-time'].numericValue, transfer: lhr.audits['total-byte-weight'].numericValue };
    results.push(metrics);
    console.log(JSON.stringify(metrics));
  } finally { await browser.close(); }
}
const median = Object.fromEntries(Object.keys(results[0]).filter(key => key !== 'run').map(key => [key, results.map(r => r[key]).sort((a, b) => a - b)[1]]));
await writeFile(new URL('performance-summary.json', output), JSON.stringify({ results, median }, null, 2));
console.log('Median:', median);
