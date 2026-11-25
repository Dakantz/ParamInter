// e2e: the dataset list page (`/`). Run with: npm run test:e2e

import { test, before, after } from 'node:test';
import assert from 'node:assert/strict';
import { makeApp } from './helpers.mjs';
import { managerSettings, makeFixtureRouter } from './fixtures.mjs';

const app = makeApp(3001);

const fixtureFor = makeFixtureRouter({
    'GET /datasets/': { hilti: managerSettings },
});

before(app.start);
after(app.stop);

test('dataset list shows a loaded dataset with working Interpolator/Effects links', (t) => app.withPage(fixtureFor, async (page) => {
    await page.goto(`${app.BASE}/`, { waitUntil: 'networkidle0' });
    await page.waitForSelector('.dataset-overview');

    await t.test('shows the dataset name as its heading', async () => {
        const heading = await page.$eval('.dataset-overview h3', (el) => el.textContent);
        assert.equal(heading, 'Hilti');
    });

    // Overview.vue labels the links 'Interpolator' and 'Effects', and only adds a third
    // 'Conditioner' link when the dataset has `use_ucq` set - the hilti fixture has it false.
    await t.test('shows Interpolator and Effects links, both enabled, and no Conditioner link without use_ucq', async () => {
        const links = await page.$$eval('.dataset-overview a.link_btn', (as) =>
            as.map((a) => ({ text: a.textContent.trim(), inactive: a.classList.contains('inactive') })),
        );
        assert.equal(managerSettings.use_ucq, false, 'fixture precondition: hilti has use_ucq false');
        assert.deepEqual(links.map((l) => l.text), ['Interpolator', 'Effects']);
        assert.ok(!links.some((l) => l.text === 'Conditioner'), 'Conditioner link should be absent when use_ucq is false');
        assert.ok(links.every((l) => !l.inactive), 'links should not be disabled for a loaded dataset');
    });
}));
