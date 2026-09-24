import { spawn } from 'node:child_process';
import puppeteer from 'puppeteer';

const PORT = 5184;
const BASE = `http://localhost:${PORT}/param-inter`;
const API_BASE = 'http://127.0.0.1:8091';

const managerSettings = {
    data_description: {
        input_cols: ['temp'], output_cols: ['strength'], all_columns: ['temp','strength'],
        num_samples: 10, num_features: 1, num_outputs: 1,
        min_values: {}, max_values: {}, mean_values: {}, std_values: {},
    },
    data_name: 'Hilti', short_data_name: 'hilti', loaded: true,
};

const viteProc = spawn('npx', ['vite', '--port', String(PORT), '--strictPort'], { stdio: 'inherit' });
const deadline = Date.now() + 20000;
while (Date.now() < deadline) {
    try { const r = await fetch(BASE + '/'); if (r.ok) break; } catch {}
    await new Promise(r => setTimeout(r, 300));
}

const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
const page = await browser.newPage();
page.on('console', m => console.log('CONSOLE:', m.text()));
page.on('pageerror', e => console.log('PAGEERROR:', e));
page.on('requestfailed', r => console.log('REQFAILED:', r.url(), r.failure()));
await page.setRequestInterception(true);
page.on('request', (req) => {
    console.log('REQ:', req.method(), req.url());
    if (!req.url().startsWith(API_BASE)) return req.continue();
    const path = new URL(req.url()).pathname;
    if (path === '/datasets/' && req.method() === 'GET') {
        return req.respond({ status: 200, contentType: 'application/json', body: JSON.stringify({ hilti: managerSettings }) });
    }
    return req.continue();
});
await page.goto(BASE + '/', { waitUntil: 'load', timeout: 15000 });
await new Promise(r => setTimeout(r, 2000));
const html = await page.content();
console.log('HTML LEN', html.length);
console.log(html.slice(0, 3000));
await browser.close();
viteProc.kill();
