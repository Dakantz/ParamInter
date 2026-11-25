// e2e: the GP-VAE Conditioner view (`/conditioner/:setname`) - conditional parallel coordinates
// (brush = range condition, double click = point condition), uncertainty-encoded mean segments,
// the detail panel, presets, and the dataset-list link. Run with: npm run test:e2e

import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { setTimeout as sleep } from 'node:timers/promises';
import { makeApp, FRONTEND_DIR } from './helpers.mjs';
import {
    CONDITIONER_SET, COLS, BASE_REL,
    makeConditionerRouter, statusUnavailable,
} from './conditioner-fixtures.mjs';

const app = makeApp(3005);
const SCREENSHOT_DIR = path.join(FRONTEND_DIR, 'e2e', 'screenshots');

before(app.start);
after(app.stop);

async function openConditioner(page) {
    await page.goto(`${app.BASE}/conditioner/${CONDITIONER_SET}`, { waitUntil: 'networkidle0' });
    await page.waitForFunction(
        (n) => document.querySelectorAll('g.axis').length === n
            && document.querySelectorAll('line.pred-mean').length === n - 1,
        { timeout: 10000 },
        COLS.length,
    );
}

// Polls the recorded predict bodies until one (after index `from`) satisfies `pred`.
async function waitForPredict(predictBodies, pred, from = 0, timeout = 5000) {
    const deadline = Date.now() + timeout;
    while (Date.now() < deadline) {
        for (let i = predictBodies.length - 1; i >= from; i--) {
            if (pred(predictBodies[i])) return predictBodies[i];
        }
        await sleep(50);
    }
    assert.fail(`no matching predict request; last bodies: ${JSON.stringify(predictBodies.slice(from))}`);
}

// Bounding box of an axis's brush overlay (the vertical strip the user drags / double clicks in).
async function overlayBox(page, col) {
    const box = await page.evaluate((c) => {
        const r = document.querySelector(`g.brush-${c} .overlay`)?.getBoundingClientRect();
        return r ? { x: r.x, y: r.y, width: r.width, height: r.height } : null;
    }, col);
    assert.ok(box, `brush overlay for ${col} should exist`);
    return box;
}

async function brushAxis(page, col, fromFrac, toFrac) {
    const box = await overlayBox(page, col);
    const cx = box.x + box.width / 2;
    await page.mouse.move(cx, box.y + box.height * fromFrac, { steps: 4 });
    await page.mouse.down();
    await page.mouse.move(cx, box.y + box.height * toFrac, { steps: 8 });
    await page.mouse.up();
}

async function dblclickAxis(page, col, frac) {
    const box = await overlayBox(page, col);
    await page.mouse.click(box.x + box.width / 2, box.y + box.height * frac, { count: 2 });
}

async function clickButton(page, text) {
    const ok = await page.evaluate((t) => {
        const b = Array.from(document.querySelectorAll('button')).find((x) => x.textContent.trim() === t);
        b?.click();
        return !!b;
    }, text);
    assert.ok(ok, `button "${text}" should exist`);
}

const condRowNames = (page) => page.$$eval('.cond-row .cond-name', (els) => els.map((e) => e.textContent.trim()));
const detailTitle = (page) => page.$eval('.ud-container h3', (el) => el.textContent.replace(/\s+/g, ' ').trim());
const uncText = (page, col) => page.$eval(`text.axis-unc-${col}`, (el) => el.textContent);

test('dataset list shows the Conditioner link only for use_ucq datasets', () => {
    const { fixtureFor } = makeConditionerRouter();
    return app.withPage(fixtureFor, async (page) => {
        await page.goto(`${app.BASE}/`, { waitUntil: 'networkidle0' });
        await page.waitForFunction(() => document.querySelectorAll('.dataset-overview').length === 2, { timeout: 10000 });
        const byName = await page.$$eval('.dataset-overview', (els) => Object.fromEntries(els.map((el) => [
            el.querySelector('h3').textContent.trim(),
            Array.from(el.querySelectorAll('a.link_btn')).filter((a) => a.textContent.trim() === 'Conditioner').map((a) => a.getAttribute('href')),
        ])));
        assert.equal(byName['Gas Turbine (mock)'].length, 1, 'use_ucq dataset should have a Conditioner link');
        assert.match(byName['Gas Turbine (mock)'][0], new RegExp(`/conditioner/${CONDITIONER_SET}$`));
        assert.equal(byName['Plain (no UCQ)'].length, 0, 'use_ucq=false dataset should not have a Conditioner link');
    });
});

test('Conditioner: unconditioned rendering', (t) => {
    const { fixtureFor, predictBodies } = makeConditionerRouter();
    return app.withPage(fixtureFor, async (page) => {
        await openConditioner(page);

        await t.test('initial predict request has no conditions', async () => {
            await waitForPredict(predictBodies, (b) => Array.isArray(b.conditions));
            assert.deepEqual(predictBodies[0].conditions, []);
        });

        await t.test('one axis per column, mean segments, bands and error bars', async () => {
            for (const c of COLS) assert.ok(await page.$(`g.axis.axis-${c}`), `axis for ${c}`);
            assert.equal(await page.$$eval('path.pred-band', (els) => els.length), COLS.length - 1);
            assert.equal(await page.$$eval('rect.pred-errbar', (els) => els.length), COLS.length);
            assert.equal(await page.$$eval('.cond-row', (els) => els.length), 0);
        });

        await t.test('axis labels show σ values when unconditioned', async () => {
            for (const c of COLS) assert.match(await uncText(page, c), /^σ \d/, `σ label for ${c}`);
        });

        await t.test('mean segment opacity encodes confidence (c-y1 opaque, a-b faint)', async () => {
            const op = await page.$$eval('line.pred-mean', (els) => els.map((e) => +e.getAttribute('opacity')));
            const conf = (c) => 1 - Math.min(1, BASE_REL[c]); // fixture: std / data_std == BASE_REL unconditioned
            const expected = COLS.slice(0, -1).map((c, s) => 0.2 + 0.8 * (conf(c) + conf(COLS[s + 1])) / 2);
            op.forEach((v, s) => assert.ok(Math.abs(v - expected[s]) < 1e-6, `segment ${s}: ${v} vs ${expected[s]}`));
            const ab = op[0];
            const cy1 = op[2];
            assert.ok(cy1 > ab + 0.5, `low-uncertainty c-y1 (${cy1}) should be far more opaque than a-b (${ab})`);
        });

        await t.test('default detail column is the most uncertain one (y2)', async () => {
            assert.match(await detailTitle(page), /^y2\b/);
        });

        await t.test('hovering an axis switches the detail panel to that column', async () => {
            const box = await overlayBox(page, 'c');
            await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 10 });
            await page.waitForFunction(() => document.querySelector('.ud-container h3')?.textContent.trim().startsWith('c'), { timeout: 3000 });
            assert.match(await detailTitle(page), /^c - predicted input/);
            const box2 = await overlayBox(page, 'y1');
            await page.mouse.move(box2.x + box2.width / 2, box2.y + box2.height / 2, { steps: 10 });
            await page.waitForFunction(() => document.querySelector('.ud-container h3')?.textContent.trim().startsWith('y1'), { timeout: 3000 });
            assert.match(await detailTitle(page), /^y1 - predicted output/);
            // the detail panel draws a density chart, per-column bars and correlations
            const counts = await page.$$eval('.ud-container svg', (svgs) => svgs.map((s) => s.childElementCount));
            assert.ok(counts.length >= 3 && counts.slice(0, 3).every((n) => n > 0), `detail svgs should be drawn: ${counts}`);
        });
    });
});

test('Conditioner: brush / double click / remove / clear conditions', (t) => {
    const { fixtureFor, predictBodies } = makeConditionerRouter();
    return app.withPage(fixtureFor, async (page) => {
        await openConditioner(page);
        await waitForPredict(predictBodies, () => true);
        const sigmaA0 = await uncText(page, 'a');

        await t.test('brushing an axis adds a range condition', async () => {
            const from = predictBodies.length;
            await brushAxis(page, 'b', 0.3, 0.6);
            await page.waitForFunction(() => document.querySelectorAll('.cond-row').length === 1, { timeout: 3000 });
            assert.deepEqual(await condRowNames(page), ['b']);
            const body = await waitForPredict(predictBodies, (b) => b.conditions?.some((c) => c.column === 'b'), from);
            const cond = body.conditions.find((c) => c.column === 'b');
            assert.ok(cond.width > 0, `range condition should have width > 0, got ${cond.width}`);
            // dragged 30%..60% of the overlay (domain 0..100 padded by 5%): roughly 40..70
            assert.ok(cond.value > 30 && cond.value < 75, `value ${cond.value}`);
            await page.waitForFunction(() => document.querySelector('text.axis-unc-b')?.textContent === 'conditioned', { timeout: 3000 });
            // other columns' σ shrink with each condition in the fixture
            await page.waitForFunction((s) => document.querySelector('text.axis-unc-a')?.textContent !== s, { timeout: 3000 }, sigmaA0);
        });

        await t.test('double clicking an axis adds a point condition with a diamond handle', async () => {
            const from = predictBodies.length;
            await dblclickAxis(page, 'y1', 0.5);
            await page.waitForFunction(() => document.querySelectorAll('path.cond-handle').length === 1, { timeout: 3000 });
            assert.deepEqual((await condRowNames(page)).sort(), ['b', 'y1']);
            const body = await waitForPredict(predictBodies, (b) => b.conditions?.some((c) => c.column === 'y1'), from);
            const y1 = body.conditions.find((c) => c.column === 'y1');
            assert.equal(y1.width, 0);
            assert.ok(Math.abs(y1.value - 25) < 6, `point value near the middle of y1's domain, got ${y1.value}`);
            assert.ok(body.conditions.find((c) => c.column === 'b')?.width > 0, 'range condition on b kept');
            await page.waitForFunction(() => document.querySelector('text.axis-unc-y1')?.textContent === 'conditioned', { timeout: 3000 });
        });

        await t.test('double clicking the diamond removes the point condition', async () => {
            const from = predictBodies.length;
            const box = await page.$eval('path.cond-handle', (el) => {
                const r = el.getBoundingClientRect();
                return { x: r.x + r.width / 2, y: r.y + r.height / 2 };
            });
            await page.mouse.click(box.x, box.y, { count: 2 });
            await page.waitForFunction(() => document.querySelectorAll('path.cond-handle').length === 0, { timeout: 3000 });
            assert.deepEqual(await condRowNames(page), ['b']);
            const body = await waitForPredict(predictBodies, (b) => !b.conditions?.some((c) => c.column === 'y1'), from);
            assert.deepEqual(body.conditions.map((c) => c.column), ['b']);
            assert.match(await uncText(page, 'y1'), /^σ /);
        });

        await t.test('"Clear all" removes every condition', async () => {
            await dblclickAxis(page, 'a', 0.4);
            await page.waitForFunction(() => document.querySelectorAll('.cond-row').length === 2, { timeout: 3000 });
            const from = predictBodies.length;
            await clickButton(page, 'Clear all');
            await page.waitForFunction(() => document.querySelectorAll('.cond-row').length === 0, { timeout: 3000 });
            const body = await waitForPredict(predictBodies, (b) => b.conditions?.length === 0, from);
            assert.deepEqual(body.conditions, []);
            assert.equal(await page.$$eval('path.cond-handle', (els) => els.length), 0);
            assert.equal(await page.$$eval('g.brush .selection', (els) => els.filter((e) => getComputedStyle(e).display !== 'none').length), 0,
                'no brush selection should remain visible');
            for (const c of COLS) assert.match(await uncText(page, c), /^σ /);
        });

        await t.test('presets set conditions (point preset -> 2 diamonds, range preset -> 2 ranges)', async () => {
            let from = predictBodies.length;
            await clickButton(page, 'Hot ambient, fixed TIT');
            await page.waitForFunction(() => document.querySelectorAll('path.cond-handle').length === 2, { timeout: 3000 });
            let body = await waitForPredict(predictBodies, (b) => b.conditions?.length === 2, from);
            assert.ok(body.conditions.every((c) => c.width === 0), 'hot-ambient preset uses point conditions');

            from = predictBodies.length;
            await clickButton(page, 'Low NOx + high load');
            await page.waitForFunction(() => document.querySelectorAll('path.cond-handle').length === 0, { timeout: 3000 });
            body = await waitForPredict(predictBodies, (b) => b.conditions?.length === 2 && b.conditions.every((c) => c.width > 0), from);
            assert.deepEqual(body.conditions.map((c) => c.column).sort(), ['a', 'y2']);
            assert.deepEqual((await condRowNames(page)).sort(), ['a', 'y2']);
        });
    });
});

test('Conditioner: status available=false shows the reason instead of the plot', () => {
    const { fixtureFor, predictBodies } = makeConditionerRouter({ status: statusUnavailable });
    return app.withPage(fixtureFor, async (page) => {
        await page.goto(`${app.BASE}/conditioner/${CONDITIONER_SET}`, { waitUntil: 'networkidle0' });
        await page.waitForSelector('.cond-error', { timeout: 10000 });
        assert.equal(await page.$eval('.cond-error', (el) => el.textContent.trim()), statusUnavailable.reason);
        assert.equal(await page.$('g.axis'), null);
        assert.equal(predictBodies.length, 0, 'no predict request when unavailable');
    });
});

test('Conditioner: screenshots of the mocked view', () => {
    const { fixtureFor, predictBodies } = makeConditionerRouter();
    return app.withPage(fixtureFor, async (page) => {
        fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
        await page.setViewport({ width: 1600, height: 1100, deviceScaleFactor: 2 });
        await openConditioner(page);
        await waitForPredict(predictBodies, () => true);
        await sleep(300);
        await page.mouse.move(5, 5);
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'conditioner-mock-unconditioned.png') });

        await brushAxis(page, 'b', 0.25, 0.55);
        await dblclickAxis(page, 'c', 0.35);
        await page.waitForFunction(() => document.querySelectorAll('.cond-row').length === 2
            && document.querySelectorAll('path.cond-handle').length === 1, { timeout: 3000 });
        await waitForPredict(predictBodies, (b) => b.conditions?.length === 2);
        await page.mouse.move(5, 5);
        await sleep(300);
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'conditioner-mock-conditioned.png') });

        const box = await overlayBox(page, 'y1');
        await page.mouse.move(box.x + box.width / 2, box.y + box.height * 0.8, { steps: 10 });
        await page.waitForFunction(() => document.querySelector('.ud-container h3')?.textContent.trim().startsWith('y1'), { timeout: 3000 });
        await sleep(200);
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, 'conditioner-mock-hover-output.png') });

        for (const f of ['unconditioned', 'conditioned', 'hover-output']) {
            assert.ok(fs.statSync(path.join(SCREENSHOT_DIR, `conditioner-mock-${f}.png`)).size > 10000);
        }
    });
});
