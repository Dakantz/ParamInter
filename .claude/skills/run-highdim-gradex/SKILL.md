---
name: run-highdim-gradex
description: Build, run, and drive ParamInter (highdim-gradex) - start the FastAPI backend and Vue/Vuetify frontend, load a dataset, and screenshot/interact with the interpolation UI via a puppeteer browser driver. Use when asked to run, start, build, or screenshot this app, or to verify a frontend/backend change actually works end-to-end.
---

ParamInter is a FastAPI backend + Vue 3/Vuetify frontend. Drive it through
`.claude/skills/run-highdim-gradex/driver.mjs`: it starts both servers, loads a
real dataset through the real API (no mocking - GPU-backed embeddings and
LightGBM/SHAP models are already cached on disk for the `scivis` dataset), and
uses Puppeteer to click through the real UI and take screenshots.

All paths below are relative to the repo root (`highdim-gradex/`).

## Prerequisites

Already satisfied in this container - nothing to install:
- `uv` manages the Python 3.13 backend env (`.uv-agent/`, selected via the
  `UV_PROJECT_ENVIRONMENT` env var already set in this container - `uv run` /
  `uv sync` pick it up automatically).
- `frontend/node_modules` is already installed, including `puppeteer` as a
  devDependency.
- The scivis dataset's embeddings, LightGBM models, and VAE are already
  cached under `data/models/scivis/`, so loading it takes ~1s instead of
  minutes of training.

If Puppeteer's Chrome isn't installed yet (`Could not find Chrome (ver. ...)`
when the driver runs):
```bash
cd frontend && npx puppeteer browsers install chrome
```

## Run (agent path)

```bash
node .claude/skills/run-highdim-gradex/driver.mjs up                                    # start backend :8091 + frontend :3000
node .claude/skills/run-highdim-gradex/driver.mjs load scivis_2025                      # load a dataset through the real API
node .claude/skills/run-highdim-gradex/driver.mjs explore scivis /tmp/explore.png       # screenshot the Interpolator view
node .claude/skills/run-highdim-gradex/driver.mjs effects scivis /tmp/effects.png       # screenshot the Effects (SHAP) view
node .claude/skills/run-highdim-gradex/driver.mjs down                                  # stop both servers
```

`up`/`down`/`status` track PIDs in `.claude/skills/run-highdim-gradex/.run-pids.json`
(gitignored-worthy, session-local) and are idempotent - re-running `up` when
already up is a no-op. Server logs land in `backend.log` and `frontend.log`
next to the driver.

| command | what it does |
|---|---|
| `up` | starts backend (`uv run uvicorn`, port 8091) and frontend (`vite`, port 3000) if not already running, waits until both respond |
| `down` | stops both by PID |
| `status` | prints running/dead/not-started for each |
| `load <set_name>` | `POST /datasets/load/<set_name>` (default `scivis_2025`); retries transient 500s (see Gotchas) |
| `list` | prints every configured dataset and whether it's loaded |
| `shot <route> <out.png>` | navigates to `<route>` under the app base path and screenshots (e.g. `shot /interpolator/scivis_2025 /tmp/x.png`) |
| `explore <short_name> <out.png>` | from the dataset list, clicks that dataset's "Explore" link and screenshots the resulting Interpolator page (default short name `scivis`) |
| `effects <short_name> <out.png>` | same, but clicks "Effects" and waits for the beeswarm SVG to render |

`explore`/`effects` match the dataset card by its "Short Name: X" text (there
are ~30 cards on the list page - scivis, privbayes, mast,
electric_arc_furnace, 24 blast_furnace variants, hilti); the link they click
is inactive until that dataset has been `load`ed, so `load` first.

Dataset names: `scivis_2025` (short name `scivis`, the alloy simulation
dataset with cached models - use this one), `privbayes`, `mast`,
`electric_arc_furnace`, `hilti`, and 24 `blast_furnace-<key>` variants (see
`node driver.mjs list` for exact keys).

## Run (human path)

```bash
uv run python -m uvicorn backend:app --reload --port 8091   # terminal 1
cd frontend && npm run dev                                   # terminal 2, port 3000
```
Then open `http://localhost:3000/param-inter/`. Useless in this headless
container without the driver's Puppeteer step - use the agent path instead.

## Test

```bash
cd frontend && npm run test:e2e   # node --test e2e/*.test.mjs, mocked backend, real vite+puppeteer
```
All 9 tests currently pass, including `Effects link navigates to the effects
view and renders the beeswarm chart and scatterplot matrix` - a basic smoke
test asserting both the beeswarm chart and the scatterplot matrix render
against the mocked `/effects/beeswarm` and `/data/sample` fixtures (confirmed
separately against the real backend: the real Effects view renders both end-
to-end too). Backend has no test suite.

## Gotchas

- **`--host 127.0.0.1` is required for vite.** Its default `localhost` bind
  resolves to the IPv6 loopback (`::1`) in this container, so a plain
  `http://127.0.0.1:3000` connection-refuses even though the server is up and
  `curl localhost:3000` works. The driver always passes `--host 127.0.0.1`.
- **Never spawn the backend or frontend with `detached: true`.** Doing so
  (setsid, new session/process group) reliably breaks the backend: any route
  that calls `ModelManager.load()` (which reaches into cuML/CUDA for the
  TSNE/UMAP embedding - e.g. `POST /datasets/load/<set>`) comes back
  `500 Internal Server Error` with **zero** server-side log output, on every
  retry, forever - even though the identical call succeeds immediately when
  the same process is started the plain `cmd > log 2>&1 &` way (no setsid).
  Root cause not fully nailed down (looks like the sandbox scopes GPU access
  to the original session), but the fix is simple: don't detach. The driver
  spawns both servers attached, with stdio going straight to a log file fd.
- **Invoke `frontend/node_modules/.bin/vite` directly, not `npx vite`.**
  `npx`/`npm exec` interpose an `npm -> sh -> node` chain, and npm doesn't
  forward `SIGTERM` down it - killing the npm wrapper's PID leaks the real
  vite server as an orphan. Same reasoning is why `down()` signals the plain
  child PID, not `-pid` (the process group): since the children aren't
  detached, their pgid is shared with whatever shell launched the driver, so
  a group-kill would take that shell down too.
- **Python stdout is block-buffered when piped**, so `backend.log` can sit
  stale (including hiding a crash traceback) until the buffer fills or the
  process exits. The driver sets `PYTHONUNBUFFERED=1` on the backend.
- **`/datasets/load/<name>` can still 500 transiently** even attached
  (observed maybe 1 in 4 fresh-process attempts) with no log line at all for
  the failing request - looks like contention on this container's shared GPU
  rather than an app bug (a direct in-process call to the same
  `ModelManager.load()` never failed in repeated testing). The driver's
  `load` command retries up to 3 times with a 1s gap, which has cleared it
  every time observed.
- **Every driver command must call `process.exit()`.** An open `fetch`
  keep-alive socket (or, before the fix above, a piped child's stdio) keeps
  node's event loop alive after the command's actual work is done, so the
  process hangs instead of returning - the harness then backgrounds it after
  its own timeout even though the work already finished.
- **~30 dataset cards render on the `/` list page** (scivis + privbayes +
  mast + eaf + 24 blast_furnace splits + hilti), each an untitled
  `.dataset-overview` div - there's no `data-testid` or id on the DOM node,
  so the only reliable way to find one is matching its `Short Name: X` `<p>`
  text (see `openDataset` in the driver).
- A harmless `Error parsing URL parameters on mount: SyntaxError: ...` shows
  up in the browser console on the Interpolator view for the scivis dataset -
  pre-existing mojibake from a `°C` character in an output column name
  (`alloy_data.txt` encoding), unrelated to anything this skill touches.

## Troubleshooting

- **`Could not find Chrome (ver. ...)`** from Puppeteer: run
  `cd frontend && npx puppeteer browsers install chrome` once.
- **`curl 127.0.0.1:3000` connection-refused but the vite log says "ready"**:
  it bound to `::1` only - relaunch with `--host 127.0.0.1` (the driver
  already does this; only relevant if you bypass it).
- **A dataset's "Explore"/"Effects" link is `.inactive` and won't click**:
  the dataset hasn't been loaded yet - run `load <set_name>` first.
