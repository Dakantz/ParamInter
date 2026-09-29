// e2e: the Interpolator view (`/interpolator/:set`) - selector choice by dimension count, and
// the parallel-coordinates selector's brush/select interactions. Run with: npm run test:e2e

import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setTimeout as sleep } from 'node:timers/promises';
import { makeApp } from './helpers.mjs';
import {
    managerSettings, columnTypesHilti, dataSampleHilti,
    wideManagerSettings, columnTypesWide7, dataSampleWide7,
    makeFixtureRouter,
} from './fixtures.mjs';

const app = makeApp(3003);

const fixtureForHilti = makeFixtureRouter({
    'GET /datasets/hilti': managerSettings,
    'GET /datasets/hilti/data/column_types': columnTypesHilti,
    'GET /datasets/hilti/data/sample': dataSampleHilti,
});

const fixtureForWide7 = makeFixtureRouter({
    'GET /datasets/wide7': wideManagerSettings,
    'GET /datasets/wide7/data/column_types': columnTypesWide7,
    'GET /datasets/wide7/data/sample': dataSampleWide7,
});

before(app.start);
after(app.stop);

test('Interpolator picks its point-selector by input dimension count', async (t) => {
    await t.test('uses the old spider-chart selector for <= 6 input dimensions (hilti, 2 dims)', () => app.withPage(fixtureForHilti, async (page) => {
        await page.goto(`${app.BASE}/interpolator/hilti`, { waitUntil: 'networkidle0' });
        await page.waitForSelector('.spider-container', { timeout: 10000 });
        assert.equal(await page.$('.pc-scroll'), null, 'parallel-coordinates selector should not render for 2 dimensions');
    }));

    await t.test('uses the parallel-coordinates selector for > 6 input dimensions (wide7, 7 dims)', () => app.withPage(fixtureForWide7, async (page) => {
        await page.goto(`${app.BASE}/interpolator/wide7`, { waitUntil: 'networkidle0' });
        await page.waitForSelector('.pc-scroll svg', { timeout: 10000 });
        assert.equal(await page.$('.spider-container'), null, 'old spider-chart selector should not render for 7 dimensions');

        const lineCount = await page.$$eval('path.pc-line', (els) => els.length);
        assert.equal(lineCount, dataSampleWide7.inputs.length, 'one line per sampled row');
    }));
});

test('parallel-coordinates: brushing an axis narrows the shown lines, and clicking a remaining line selects it', (t) => app.withPage(fixtureForWide7, async (page) => {
    await page.goto(`${app.BASE}/interpolator/wide7`, { waitUntil: 'networkidle0' });
    await page.waitForSelector('.pc-scroll svg', { timeout: 10000 });
    await page.waitForFunction(() => document.querySelectorAll('path.pc-line').length > 0);

    await t.test('brushing narrows the shown/total count', async () => {
        const before_count = await page.$eval('.pc-count', (el) => el.textContent.trim());
        assert.equal(before_count, `${dataSampleWide7.inputs.length} / ${dataSampleWide7.inputs.length} shown`);

        // Axes are laid out vertically (one row per dimension) with each dimension's own value
        // scale running horizontally, so the brush (brushX) drags left/right along an axis's
        // row, not up/down - see ParallelCoordinatesSelector.vue's redraw().
        const brush_box = await page.evaluate(() => {
            const overlay = document.querySelector('g.pc-axes g.pc-axis .overlay');
            if (!overlay) return null;
            const r = overlay.getBoundingClientRect();
            return { y: r.y + r.height / 2, left: r.x + r.width * 0.1, right: r.x + r.width * 0.5 };
        });
        assert.ok(brush_box, 'first axis brush overlay should exist');
        await page.mouse.move(brush_box.left, brush_box.y);
        await page.mouse.down();
        await page.mouse.move(brush_box.right, brush_box.y, { steps: 8 });
        await page.mouse.up();
        await sleep(200);

        const after_count = await page.$eval('.pc-count', (el) => el.textContent.trim());
        assert.notEqual(after_count, before_count, 'brushing should change the shown/total count');
    });

    await t.test('clicking a remaining (still-active) line encodes a selection into the URL', async () => {
        // clicking a remaining line should select that datapoint - observable via the selection
        // getting encoded into the URL (InterpolationPanels writes it on every change).
        assert.ok(!page.url().includes('selection='), 'no selection should be encoded yet');
        const clicked = await page.evaluate(() => {
            const active = Array.from(document.querySelectorAll('path.pc-line'))
                .find((l) => l.style.pointerEvents !== 'none');
            if (!active) return false;
            active.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
            return true;
        });
        assert.ok(clicked, 'at least one line should remain active/clickable after brushing');
        await sleep(300);
        assert.ok(page.url().includes('selection='), 'selecting a point should encode the selection into the URL');
    });
}));
