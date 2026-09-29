// e2e: the Effects view (`/effects/:set`) - beeswarm + scatterplot matrix rendering, hover
// highlighting, cell-size fit for many dimensions, and the magnified popover. Run with:
// npm run test:e2e

import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { setTimeout as sleep } from 'node:timers/promises';
import { makeApp, waitForPanelRow, hoverAt, clickComputeDependency } from './helpers.mjs';
import {
    managerSettings, columnTypesHilti, dataSampleHilti, beeswarmResult, interactionResultHilti,
    interactionBackgroundResultHilti,
    manyDimsManagerSettings, columnTypesManyDims, dataSampleManyDims, manyDimsCols,
    makeFixtureRouter,
} from './fixtures.mjs';

const app = makeApp(3002);

const fixtureForHilti = makeFixtureRouter({
    'GET /datasets/': { hilti: managerSettings },
    'GET /datasets/hilti': managerSettings,
    'GET /datasets/hilti/data/column_types': columnTypesHilti,
    'GET /datasets/hilti/data/sample': dataSampleHilti,
    'POST /datasets/hilti/effects/beeswarm': beeswarmResult,
    'POST /datasets/hilti/effects/interaction': interactionResultHilti,
    'POST /datasets/hilti/effects/interaction-background': interactionBackgroundResultHilti,
});

const fixtureForManyDims = makeFixtureRouter({
    'GET /datasets/manydims': manyDimsManagerSettings,
    'GET /datasets/manydims/data/column_types': columnTypesManyDims,
    'GET /datasets/manydims/data/sample': dataSampleManyDims,
});

const highlightedCount = (page) =>
    page.$$eval('rect.splom-cell-bg', (els) => els.filter((r) => r.getAttribute('fill') !== 'transparent').length);

before(app.start);
after(app.stop);

test('Effects link navigates to the effects view and renders the beeswarm chart and scatterplot matrix', (t) => app.withPage(fixtureForHilti, async (page) => {
    await page.goto(`${app.BASE}/`, { waitUntil: 'networkidle0' });
    await page.waitForSelector('.dataset-overview a.link_btn:nth-of-type(2)');
    await Promise.all([
        page.waitForFunction(() => location.pathname.endsWith('/effects/hilti')),
        page.click('.dataset-overview a.link_btn:nth-of-type(2)'),
    ]);

    await t.test('shows the dataset name in the page title', async () => {
        await page.waitForSelector('h2.small_h2');
        const title = await page.$eval('h2.small_h2', (el) => el.textContent.trim());
        assert.equal(title, 'Hilti - Effects');
    });

    await t.test('renders the beeswarm chart', async () => {
        await waitForPanelRow(page, 0);
        const dotCount = await page.$$eval('.wide-panel svg circle', (els) => els.length);
        assert.ok(dotCount > 0, 'beeswarm chart should render at least one dot');
    });

    await t.test('renders the scatterplot matrix at input-dimension^2 cells', async () => {
        await page.waitForFunction(() => document.querySelectorAll('g.splom-cell').length > 0, { timeout: 10000 });
        const cellCount = await page.$$eval('g.splom-cell', (els) => els.length);
        assert.equal(cellCount, dataSampleHilti.inputs[0].length ** 2, '2 input dimensions -> a 2x2 scatterplot matrix');
    });
}));

test('Effects panel hover highlighting in the scatterplot matrix', (t) => app.withPage(fixtureForHilti, async (page) => {
    await page.goto(`${app.BASE}/effects/hilti`, { waitUntil: 'networkidle0' });
    const beeswarmRow = await waitForPanelRow(page, 0);
    await page.waitForFunction(() => document.querySelectorAll('g.splom-cell').length > 0, { timeout: 10000 });
    assert.equal(await highlightedCount(page), 0, 'nothing highlighted before any hover');

    await t.test('hovering a Beeswarm row highlights its full row', async () => {
        await hoverAt(page, beeswarmRow);
        await sleep(200);
        assert.equal(await highlightedCount(page), 2, 'hovering a first-order row highlights its full row (2 cells for 2 dims)');
    });

    await t.test('hovering an order-2 Dependency row highlights exactly its mirrored cell pair', async () => {
        // compute the order-2 dependency, then hover its row -> should highlight exactly one
        // pair's 2 mirrored cells ((temp,pressure) and (pressure,temp))
        await clickComputeDependency(page);
        const depRow = await waitForPanelRow(page, 1);
        await hoverAt(page, depRow);
        await sleep(200);
        assert.equal(await highlightedCount(page), 2, 'hovering an order-2 row highlights exactly its (mirrored) cell pair');
    });
}));

test('Effects panel: scatterplot matrix cell size shrinks to fit the panel width for a dataset with many input dimensions', (t) => app.withPage(fixtureForManyDims, async (page) => {
    await page.goto(`${app.BASE}/effects/manydims`, { waitUntil: 'networkidle0' });
    await page.waitForFunction(() => document.querySelectorAll('g.splom-cell').length > 0, { timeout: 10000 });

    await t.test('renders an NxN matrix (N = number of input dimensions)', async () => {
        const cellCount = await page.$$eval('g.splom-cell', (els) => els.length);
        assert.equal(cellCount, manyDimsCols.length * manyDimsCols.length, `${manyDimsCols.length}x${manyDimsCols.length} matrix`);
    });

    await t.test('shrinks cell size to fit the container without horizontal overflow', async () => {
        const info = await page.evaluate(() => {
            const scroll = document.querySelector('.splom-scroll');
            const cellRect = document.querySelector('rect.splom-cell-bg');
            return {
                clientWidth: scroll.clientWidth,
                scrollWidth: scroll.scrollWidth,
                cellSize: Number(cellRect.getAttribute('width')),
            };
        });
        assert.ok(
            info.scrollWidth <= info.clientWidth + 2,
            `matrix (${info.scrollWidth}px) should fit within its container (${info.clientWidth}px) without horizontal overflow`,
        );
        // A fixed cell size (the pre-fix behavior) defaults to 88px regardless of how many
        // dimensions there are; with 16 dimensions in a narrow test viewport it must have shrunk.
        assert.ok(info.cellSize < 88, `cell size (${info.cellSize}px) should have shrunk below the 88px max`);
    });
}));

// The popover's axis labels carry the variable names (see ScatterplotMatrix.vue's
// `.popover-x-label`/`.popover-y-label`): popover_cell falls back to {row: highlight_cell[0],
// col: highlight_cell[1]} for a Dependency-row hover, so for highlight_cell ['temp', 'pressure']
// that's x-label 'pressure', y-label 'temp' - and a direct hover on the (temp, pressure)
// off-diagonal cell resolves to the same {row: 'temp', col: 'pressure'}, so both popover tests
// below expect the same labels.
async function assertPopoverLabels(page) {
    const labels = await page.evaluate(() => ({
        x: document.querySelector('.splom-popover .popover-x-label')?.textContent,
        y: document.querySelector('.splom-popover .popover-y-label')?.textContent,
    }));
    assert.equal(labels.x, 'pressure', 'x-axis label should be the column variable');
    assert.equal(labels.y, 'temp', 'y-axis label should be the row variable');
}

test('Effects panel: hovering a Dependency row shows a ~1/3-container-width popover of that pair, which disappears on mouse-leave', (t) => app.withPage(fixtureForHilti, async (page) => {
    await page.goto(`${app.BASE}/effects/hilti`, { waitUntil: 'networkidle0' });
    await page.waitForFunction(() => document.querySelectorAll('g.splom-cell').length > 0, { timeout: 10000 });
    assert.equal(await page.$('.splom-popover'), null, 'no popover before any hover');

    await clickComputeDependency(page);
    const depRow = await waitForPanelRow(page, 1);
    await hoverAt(page, depRow);
    await sleep(200);

    await t.test('shows a ~1/3-container-width popover with axis labels and one point per row', async () => {
        const popover = await page.evaluate(() => {
            const pop = document.querySelector('.splom-popover');
            if (!pop) return null;
            const rect = pop.getBoundingClientRect();
            const containerWidth = document.querySelector('.splom-scroll').getBoundingClientRect().width;
            return { ratio: rect.width / containerWidth, circleCount: pop.querySelectorAll('circle').length };
        });
        assert.ok(popover, 'popover should appear while hovering the order-2 Dependency row');
        assert.ok(popover.ratio > 0.28 && popover.ratio < 0.4, `popover width ratio (${popover.ratio}) should be roughly 1/3 of the container`);
        assert.equal(popover.circleCount, dataSampleHilti.inputs.length, 'popover should plot one point per sampled row');
        await assertPopoverLabels(page);
    });

    await t.test('hovering a specific point in the Dependency row highlights that point in the popover', async () => {
        // interactionResultHilti.indices[0] === 0, and dataSampleHilti.indices includes 0 (the
        // scatterplot matrix's own separate sample), so this dataset row is in both - point 0's
        // dot carries d3 datum {i: 0, ...} (see BeeswarmChart's swarm layout).
        const dotBox = await page.evaluate(() => {
            const panel = document.querySelectorAll('.wide-panel')[1];
            const dot = Array.from(panel.querySelectorAll('g.beeswarm-row circle'))
                .find((c) => c.__data__?.i === 0);
            return dot ? dot.getBoundingClientRect().toJSON() : null;
        });
        assert.ok(dotBox, 'a dot for dependency-row point index 0 should exist');
        await page.mouse.move(dotBox.x + dotBox.width / 2, dotBox.y + dotBox.height / 2, { steps: 10 });
        await sleep(200);

        const highlightedCount = await page.$$eval('.splom-popover circle[r="5.5"]', (els) => els.length);
        assert.equal(highlightedCount, 1, 'exactly one popover point should be highlighted');

        // Moving off the dot but staying within the row (its label area, clear of both dots)
        // should clear the point highlight without closing the popover itself.
        const labelSpot = await page.evaluate(() => {
            const panel = document.querySelectorAll('.wide-panel')[1];
            const r = panel.querySelector('g.beeswarm-row rect').getBoundingClientRect();
            return { x: r.x + 5, y: r.y + r.height / 2 };
        });
        await page.mouse.move(labelSpot.x, labelSpot.y, { steps: 10 });
        await sleep(200);
        assert.equal(
            await page.$$eval('.splom-popover circle[r="5.5"]', (els) => els.length),
            0,
            'no popover point should stay highlighted after leaving the dot',
        );
        assert.notEqual(await page.$('.splom-popover'), null, 'popover itself should still be open');
    });

    await t.test('disappears on mouse-leave', async () => {
        // `steps` matters here: a single-jump mouse.move can fail to fire mouseleave on the old
        // target via CDP-synthesized input in this environment, even though the pointer
        // genuinely ends up elsewhere - stepping through intermediate points fires it reliably.
        // Poll rather than a fixed sleep-then-assert: under load (this test running after
        // several others) a short fixed delay is sometimes not enough for the reactive update
        // to land.
        await page.mouse.move(20, 20, { steps: 10 });
        await page.waitForFunction(() => document.querySelector('.splom-popover') === null, { timeout: 5000 });
    });
}));

test('Effects panel: hovering a cell directly in the scatterplot matrix shows the same magnified popover', (t) => app.withPage(fixtureForHilti, async (page) => {
    await page.goto(`${app.BASE}/effects/hilti`, { waitUntil: 'networkidle0' });
    await page.waitForFunction(() => document.querySelectorAll('g.splom-cell').length > 0, { timeout: 10000 });

    // off-diagonal cells have 3 <rect>s (background, border, hit-target); the diagonal
    // (row === col) cell has 2 <rect>s plus a label <text> instead of circles. A bounding box,
    // not an ElementHandle to `.hover()` - see the comment on `waitForPanelRow` in helpers.mjs.
    const offDiagCellBox = await page.evaluate(() => {
        const cell = Array.from(document.querySelectorAll('g.splom-cell')).find((c) => c.querySelectorAll('rect').length === 3);
        return cell ? cell.getBoundingClientRect().toJSON() : null;
    });
    assert.ok(offDiagCellBox, 'an off-diagonal cell should exist for a 2-dimension matrix');
    await hoverAt(page, offDiagCellBox);
    await sleep(200);

    await t.test('shows a popover with the pair\'s axis labels', () => assertPopoverLabels(page));

    await t.test('disappears on mouse-leave', async () => {
        // stepped move, not a single jump, and polled rather than sleep-then-assert - see the
        // comment on the equivalent move in the Dependency row popover test above.
        await page.mouse.move(20, 20, { steps: 10 });
        await page.waitForFunction(() => document.querySelector('.splom-popover') === null, { timeout: 5000 });
    });
}));

test('Effects panel: scatterplot matrix popover shows a KNN-interpolated background, togglable between model output and SHAP effect', (t) => app.withPage(fixtureForHilti, async (page) => {
    await page.goto(`${app.BASE}/effects/hilti`, { waitUntil: 'networkidle0' });
    await page.waitForFunction(() => document.querySelectorAll('g.splom-cell').length > 0, { timeout: 10000 });

    await t.test('the left panel offers a model-output/SHAP-effect background select', async () => {
        const options = await page.$$eval(
            'select.background_select option',
            (els) => els.map((o) => o.value),
        );
        assert.deepEqual(options, ['output', 'shap']);
    });

    assert.equal(await page.$('.splom-popover image'), null, 'no background image before any hover');

    // interactionBackgroundResultHilti's var1/var2 ('pressure'/'temp') match exactly the
    // {col, row} the Dependency-row hover resolves to for hilti's one combination (see
    // assertPopoverLabels above) - hovering anything else would leave state.background unset.
    await clickComputeDependency(page);
    const depRow = await waitForPanelRow(page, 1);
    await hoverAt(page, depRow);
    await page.waitForFunction(() => document.querySelector('.splom-popover image') !== null, { timeout: 5000 });

    await t.test('renders the background as a data-URL image with a caption describing it', async () => {
        const info = await page.evaluate(() => ({
            href: document.querySelector('.splom-popover image')?.getAttribute('href') ?? '',
            caption: document.querySelector('.splom-bg-caption')?.textContent ?? '',
        }));
        assert.ok(info.href.startsWith('data:image/'), 'background <image> should have a data: URL href');
        assert.match(info.caption, /model output/, 'caption should default to describing the model-output background');
    });

    await t.test('switching to "SHAP effect" re-renders the caption (and range) without a new fetch', async () => {
        let backgroundRequests = 0;
        page.on('request', (req) => {
            if (req.url().includes('/effects/interaction-background')) backgroundRequests += 1;
        });

        await page.select('select.background_select', 'shap');
        // The select interaction can move the mouse off the row; re-assert the hover so the
        // popover (and its background) stays open for the caption check below.
        await hoverAt(page, depRow);
        await page.waitForFunction(
            () => document.querySelector('.splom-bg-caption')?.textContent.includes('SHAP effect'),
            { timeout: 5000 },
        );

        // predictions range 1-9, shap_effect range 1-9 too in the fixture, so this only checks
        // the mode label flipped, not the numbers - the request-count assertion below is what
        // actually proves no re-fetch happened.
        assert.equal(backgroundRequests, 0, 'switching background_mode must not re-fetch (both fields already arrived in one response)');
    });
}));
