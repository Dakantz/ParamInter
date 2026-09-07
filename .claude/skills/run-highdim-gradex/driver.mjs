#!/usr/bin/env node
// Driver for running + poking ParamInter (highdim-gradex): starts the FastAPI backend and the
// Vite dev server, loads a dataset through the real API, and drives the real UI with Puppeteer
// (navigate / click / screenshot). See SKILL.md in this directory for the full command list and
// example invocations - this header is intentionally short.
//
// Puppeteer is a frontend devDependency (frontend/node_modules), not a root one, and this file
// lives outside frontend/ so plain ESM `import 'puppeteer'` can't find it (Node only walks up
// node_modules from the importing file, and the repo root has none). createRequire() rooted at
// frontend/package.json resolves it correctly without moving this file into frontend/.

import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import { setTimeout as sleep } from 'node:timers/promises';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, '../../..');
const FRONTEND_DIR = path.join(REPO_ROOT, 'frontend');
const require = createRequire(path.join(FRONTEND_DIR, 'package.json'));
const puppeteer = require('puppeteer');

const API_PORT = 8091;
const WEB_PORT = 3000;
const API_BASE = `http://127.0.0.1:${API_PORT}`;
const SITE_BASE = '/param-inter';
const WEB_BASE = `http://127.0.0.1:${WEB_PORT}${SITE_BASE}`;
const PID_FILE = path.join(__dirname, '.run-pids.json');

function log(...args) {
    console.error('[driver]', ...args);
}

async function waitForHttp(url, timeoutMs) {
    const deadline = Date.now() + timeoutMs;
    let lastErr;
    while (Date.now() < deadline) {
        try {
            const res = await fetch(url);
            if (res.ok || res.status < 500) return true;
        } catch (err) {
            lastErr = err;
        }
        await sleep(300);
    }
    throw new Error(`Timed out waiting for ${url}: ${lastErr}`);
}

function spawnDetached(cmd, args, opts) {
    // IMPORTANT: `detached: true` (setsid, new session/process-group) reliably breaks the
    // backend in this container - `/datasets/load/<set>` (or any route that calls
    // ModelManager.load(), which touches cuML/CUDA for the TSNE/UMAP embedding) comes back
    // "500 Internal Server Error" with *zero* server-side log output for every retry, forever,
    // even though the exact same load() call succeeds every time run directly or backgrounded
    // the plain `cmd > log 2>&1 &` way (no setsid). Piping stdio through Node (`stdio: 'pipe'`)
    // isn't the cause on its own - only detached is. So: no `detached`, and stdio goes straight
    // to an fd for the log file (not a Node pipe) so nothing here holds the event loop open.
    const out = fs.openSync(opts.logPath, 'a');
    const child = spawn(cmd, args, { ...opts, detached: false, stdio: ['ignore', out, out] });
    fs.closeSync(out);
    child.unref();
    return child.pid;
}

function readPids() {
    try {
        return JSON.parse(fs.readFileSync(PID_FILE, 'utf8'));
    } catch {
        return {};
    }
}

function writePids(pids) {
    fs.writeFileSync(PID_FILE, JSON.stringify(pids, null, 2));
}

function isAlive(pid) {
    try {
        process.kill(pid, 0);
        return true;
    } catch {
        return false;
    }
}

// --- lifecycle -------------------------------------------------------------

async function up() {
    const pids = readPids();

    if (pids.backend && isAlive(pids.backend)) {
        log('backend already running (pid', pids.backend + ')');
    } else {
        log('starting backend: uv run python -m uvicorn backend:app --port', API_PORT);
        const pid = spawnDetached(
            'uv',
            ['run', 'python', '-m', 'uvicorn', 'backend:app', '--port', String(API_PORT)],
            {
                cwd: REPO_ROOT,
                logPath: path.join(__dirname, 'backend.log'),
                // Without this, Python block-buffers stdout when it's a pipe (not a tty), so
                // backend.log can sit empty/stale for minutes - including hiding a crash
                // traceback - until the buffer fills or the process exits.
                env: { ...process.env, PYTHONUNBUFFERED: '1' },
            },
        );
        pids.backend = pid;
        writePids(pids);
        await waitForHttp(`${API_BASE}/openapi.json`, 60_000);
        log('backend up on', API_BASE);
    }

    if (pids.frontend && isAlive(pids.frontend)) {
        log('frontend already running (pid', pids.frontend + ')');
    } else {
        // Invoke the vite binary directly rather than `npx vite`: npx/`npm exec` interpose an
        // npm -> sh -> node chain, and npm doesn't forward SIGTERM down that chain, so `down()`
        // would kill only the npm wrapper and leak the real vite server as an orphan.
        const viteBin = path.join(FRONTEND_DIR, 'node_modules', '.bin', 'vite');
        log('starting frontend:', viteBin, '--host 127.0.0.1 --port', WEB_PORT, '--strictPort');
        // --host 127.0.0.1 matters: vite's default `localhost` bind resolves to the IPv6
        // loopback (::1) in this container, so plain http://127.0.0.1:3000 connection-refuses
        // even though the server is up and `curl localhost:3000` works fine.
        const pid = spawnDetached(
            viteBin,
            ['--host', '127.0.0.1', '--port', String(WEB_PORT), '--strictPort'],
            { cwd: FRONTEND_DIR, logPath: path.join(__dirname, 'frontend.log') },
        );
        pids.frontend = pid;
        writePids(pids);
        await waitForHttp(`${WEB_BASE}/`, 30_000);
        log('frontend up on', WEB_BASE);
    }
}

async function down() {
    const pids = readPids();
    for (const key of ['backend', 'frontend']) {
        const pid = pids[key];
        if (pid && isAlive(pid)) {
            log('killing', key, 'pid', pid);
            // Plain pid, NOT the process group (`-pid`): these children are no longer detached
            // (see spawnDetached's comment), so their pgid is shared with whatever shell
            // launched this driver invocation - signaling the group would hit that shell too.
            // `uv run` forwards the signal to the python child it wraps, so this is enough.
            try { process.kill(pid, 'SIGTERM'); } catch {}
        }
    }
    writePids({});
}

async function status() {
    const pids = readPids();
    for (const key of ['backend', 'frontend']) {
        const pid = pids[key];
        console.log(key, pid ? (isAlive(pid) ? `running (pid ${pid})` : `dead (stale pid ${pid})`) : 'not started');
    }
}

// --- dataset loading (real backend, no mocking) -----------------------------

async function loadDataset(setName) {
    // The first /datasets/load/<name> call for a dataset occasionally 500s with no server-side
    // traceback at all (reproduced directly: same request, same process, succeeds on retry) -
    // looks like transient contention on the shared GPU this container's cuML build reaches for
    // (TSNE/UMAP/NearestNeighbors), not an app bug. Retrying clears it in practice.
    let lastErr;
    for (let attempt = 1; attempt <= 3; attempt++) {
        const res = await fetch(`${API_BASE}/datasets/load/${setName}`, { method: 'POST' });
        if (res.ok) {
            log('loaded dataset', setName, attempt > 1 ? `(succeeded on attempt ${attempt})` : '');
            return;
        }
        lastErr = `load ${setName} failed: HTTP ${res.status} ${await res.text()}`;
        log(`load attempt ${attempt}/3 failed, retrying:`, lastErr);
        await sleep(1000);
    }
    throw new Error(lastErr);
}

async function listDatasets() {
    const res = await fetch(`${API_BASE}/datasets/`);
    const data = await res.json();
    for (const [name, settings] of Object.entries(data)) {
        console.log(name, '-', settings.data_name, '- loaded:', settings.loaded);
    }
}

// --- browser ----------------------------------------------------------------

async function withPage(fn) {
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });
    try {
        const page = await browser.newPage();
        await page.setViewport({ width: 1440, height: 1000 });
        page.on('pageerror', (err) => log('page error:', err.message));
        page.on('console', (msg) => {
            if (msg.type() === 'error') log('console.error:', msg.text());
        });
        return await fn(page, browser);
    } finally {
        await browser.close();
    }
}

async function shot(route, outFile) {
    await withPage(async (page) => {
        await page.goto(`${WEB_BASE}${route}`, { waitUntil: 'networkidle0', timeout: 30_000 });
        fs.mkdirSync(path.dirname(path.resolve(outFile)), { recursive: true });
        await page.screenshot({ path: outFile, fullPage: true });
        log('screenshot saved to', outFile);
    });
}

// Clicks the Explore/Effects link inside the `.dataset-overview` card whose "Short Name: X" line
// matches shortName exactly (there are ~30 dataset cards on this page - text match is the only
// reliable way to find the right one since Overview.vue doesn't put the id on the DOM node).
async function openDataset(page, shortName, linkText) {
    await page.goto(`${WEB_BASE}/`, { waitUntil: 'networkidle0', timeout: 30_000 });
    await page.waitForSelector('.dataset-overview');
    const clicked = await page.evaluate((shortName, linkText) => {
        const cards = Array.from(document.querySelectorAll('.dataset-overview'));
        const card = cards.find((c) =>
            Array.from(c.querySelectorAll('p')).some((p) => p.textContent.trim() === `Short Name: ${shortName}`),
        );
        if (!card) return `no card found for short name ${shortName}`;
        const link = Array.from(card.querySelectorAll('a.link_btn')).find((a) => a.textContent.trim() === linkText);
        if (!link) return `no ${linkText} link found (dataset likely not loaded yet - run 'load' first)`;
        if (link.classList.contains('inactive')) return `${linkText} link is inactive for ${shortName}`;
        link.click();
        return null;
    }, shortName, linkText);
    if (clicked) throw new Error(clicked);
}

async function explore(shortName, outFile) {
    await withPage(async (page) => {
        await openDataset(page, shortName, 'Explore');
        await page.waitForFunction(
            (base) => location.pathname.startsWith(`${base}/interpolator/`),
            {},
            SITE_BASE,
        );
        await page.waitForSelector('svg', { timeout: 15_000 }).catch(() => {});
        await sleep(500); // let embedding/chart render settle
        fs.mkdirSync(path.dirname(path.resolve(outFile)), { recursive: true });
        await page.screenshot({ path: outFile, fullPage: true });
        log('screenshot saved to', outFile);
    });
}

async function effects(shortName, outFile) {
    await withPage(async (page) => {
        await openDataset(page, shortName, 'Effects');
        await page.waitForFunction(
            (base) => location.pathname.startsWith(`${base}/effects/`),
            {},
            SITE_BASE,
        );
        await page.waitForSelector('svg', { timeout: 20_000 }).catch(() => {});
        await sleep(500);
        fs.mkdirSync(path.dirname(path.resolve(outFile)), { recursive: true });
        await page.screenshot({ path: outFile, fullPage: true });
        log('screenshot saved to', outFile);
    });
}

// --- CLI ---------------------------------------------------------------------

const [, , cmd, ...args] = process.argv;

try {
    switch (cmd) {
        case 'up':
            await up();
            break;
        case 'down':
            await down();
            break;
        case 'status':
            await status();
            break;
        case 'load':
            await loadDataset(args[0] ?? 'scivis_2025');
            break;
        case 'list':
            await listDatasets();
            break;
        case 'shot':
            await shot(args[0], args[1]);
            break;
        case 'explore':
            await explore(args[0] ?? 'scivis', args[1] ?? 'explore.png');
            break;
        case 'effects':
            await effects(args[0] ?? 'scivis', args[1] ?? 'effects.png');
            break;
        default:
            console.error(`Usage: node driver.mjs <up|down|status|load <set>|list|shot <route> <out.png>|explore <short_name> <out.png>|effects <short_name> <out.png>>`);
            process.exit(1);
    }
    // Node's fetch (undici) keeps a keep-alive socket/timer around after a request, which can
    // leave the event loop alive - every command exits explicitly rather than letting node
    // decide it's done on its own.
    process.exit(0);
} catch (err) {
    console.error('[driver] ERROR:', err.message);
    process.exit(1);
}
