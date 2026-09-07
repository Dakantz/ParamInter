// Shared infrastructure for the e2e test files: spins up a real Vite dev server + a Puppeteer
// browser per file, mocks the backend on `page.setRequestInterception` using each file's own
// fixture map (see fixtures.mjs), and provides the hover/wait helpers the individual tests need.
//
// The real backend needs GPU-backed embeddings/LightGBM models to load a dataset, which isn't
// something a frontend test should depend on - see the module doc comment that used to live in
// the single app.test.mjs this was split out of.
//
// `node --test` isolates each *.test.mjs file into its own process and may run files
// concurrently, so each file needs its own Vite dev server - on its own port, passed in here, so
// concurrent files don't collide on the same port.

import { spawn } from 'node:child_process';
import path from 'node:path';
import assert from 'node:assert/strict';
import puppeteer from 'puppeteer';

export const FRONTEND_DIR = new URL('..', import.meta.url).pathname;
export const API_BASE = 'http://127.0.0.1:8091'; // matches .env.development PI_API_BASE_URL

// Starts a Vite dev server on `port` and a headless browser; returns `{ BASE, withPage, start,
// stop }`. Call `start()` in the file's `before()` and `stop()` in its `after()`.
export function makeApp(port) {
    // 127.0.0.1, not localhost: vite's default bind resolves "localhost" to the IPv6 loopback
    // (::1) in this container, so http://localhost only connects by luck of resolver ordering.
    const BASE = `http://127.0.0.1:${port}/param-inter`;
    let viteProc;
    let browser;

    async function start() {
        // Invoke the vite binary directly, not `npx vite`: npx/`npm exec` interpose an
        // npm -> sh -> node chain that doesn't forward SIGTERM, so killing this process only
        // kills the npx wrapper and leaks the real vite server as an orphan holding this
        // process's stdio pipes open - which then hangs `after()` (and the whole `node --test`
        // run) on shutdown even though every test has already finished.
        const viteBin = path.join(FRONTEND_DIR, 'node_modules', '.bin', 'vite');
        viteProc = spawn(viteBin, ['--host', '127.0.0.1', '--port', String(port), '--strictPort'], {
            cwd: FRONTEND_DIR,
            stdio: 'pipe',
        });
        const deadline = Date.now() + 20000;
        while (Date.now() < deadline) {
            try {
                const res = await fetch(`${BASE}/`);
                if (res.ok) break;
            } catch {
                // not up yet
            }
            await new Promise((r) => setTimeout(r, 300));
        }
        browser = await puppeteer.launch({
            headless: true,
            args: ['--no-sandbox', '--disable-setuid-sandbox'],
        });
    }

    async function stop() {
        await browser?.close();
        viteProc?.kill();
    }

    async function withMockedApi(page, fixtureFor) {
        await page.setRequestInterception(true);
        page.on('request', (req) => {
            if (!req.url().startsWith(API_BASE)) return req.continue();
            if (req.method() === 'OPTIONS') {
                // The app (127.0.0.1:port) and the mocked API (127.0.0.1:8091) are different
                // origins, so the browser sends a CORS preflight OPTIONS request before any
                // cross-origin POST with a JSON body. fixtureFor only answers GET/POST, so
                // without this the preflight falls through to `req.continue()`, hits the real
                // (not-running) backend, connection-refuses, and the browser never sends the
                // actual POST at all - every POST-backed fixture (beeswarm, interaction, ...)
                // would silently fail, every time.
                return req.respond({
                    status: 204,
                    headers: {
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                        'Access-Control-Allow-Headers': 'Content-Type',
                    },
                });
            }
            const fixture = fixtureFor(req.url(), req.method());
            if (fixture === undefined) return req.continue();
            req.respond({
                status: 200,
                contentType: 'application/json',
                headers: { 'Access-Control-Allow-Origin': '*' },
                body: JSON.stringify(fixture),
            });
        });
    }

    // Opens a fresh mocked-API page for `fn`, and always closes it afterwards - including when
    // `fn` throws (e.g. a failed assertion). Without the try/finally, a failing test leaks its
    // page open for the rest of the run, which showed up as later, unrelated tests timing out
    // under the resulting resource contention.
    async function withPage(fixtureFor, fn) {
        const page = await browser.newPage();
        try {
            // Puppeteer's default 800x600 viewport is small enough that some panels sit right
            // at/past its edge, which made mouse-leave events on hover targets there (e.g. a
            // Dependency row) unreliable via CDP-synthesized mouse moves - not an app bug, but a
            // viewport-dependent quirk that a wider, more realistic viewport avoids.
            await page.setViewport({ width: 1440, height: 1000 });
            await withMockedApi(page, fixtureFor);
            await fn(page);
        } finally {
            await page.close();
        }
    }

    return { BASE, start, stop, withPage };
}

// Clicks the "Compute dependency" button in the Effects panel.
export async function clickComputeDependency(page) {
    const clicked = await page.evaluate(() => {
        const btn = Array.from(document.querySelectorAll('button')).find((b) => b.textContent.includes('Compute dependency'));
        if (!btn) return false;
        btn.click();
        return true;
    });
    assert.ok(clicked, '"Compute dependency" button should exist');
}

// Waits for the Beeswarm chart (`.wide-panel`s are Beeswarm, Dependency, Scatterplot Matrix, in
// that order) to have rendered its data rows, then returns the bounding box of its first row.
// NOT the same as waiting for `.wide-panel svg`: the Scatterplot Matrix's <svg> renders
// unconditionally, before its own data has loaded, so that selector can resolve before the
// Beeswarm chart actually has any rows.
//
// Deliberately a bounding box, not an ElementHandle to `.hover()`: BeeswarmChart's redraw() does
// `svg.selectAll('*').remove()` and rebuilds from scratch on every data change (e.g. the
// ResizeObserver firing once more as layout settles), which can detach a previously-grabbed
// handle a moment later ("Node is either not clickable or not an Element"). A plain (x, y) is
// immune to that - and to make the resulting hover actually register (see `hoverAt` below), it
// still needs a stepped mouse.move, not a single jump.
export async function waitForPanelRow(page, panelIndex) {
    await page.waitForFunction(
        (i) => (document.querySelectorAll('.wide-panel')[i]?.querySelectorAll('g.beeswarm-row').length ?? 0) > 0,
        { timeout: 10000 },
        panelIndex,
    );
    const handle = await page.evaluateHandle(
        (i) => document.querySelectorAll('.wide-panel')[i].querySelector('g.beeswarm-row rect'),
        panelIndex,
    );
    return handle.asElement().boundingBox();
}

// Moves the mouse onto the center-ish of `box` via a stepped move. A single-jump `mouse.move`
// can fail to fire mouseenter/mouseleave on the old/new target via CDP-synthesized input in this
// environment (reproduced consistently at the default small viewport, and intermittently even at
// a larger one); stepping through intermediate points fires them reliably.
export async function hoverAt(page, box) {
    await page.mouse.move(box.x + box.width * 0.7, box.y + box.height / 2, { steps: 10 });
}
