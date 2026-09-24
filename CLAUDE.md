# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

ParamInter (package name `scivis-2025`, this repo directory: `highdim-gradex`) is an interactive
tool for exploring continuous, high-dimensional input→output parameter sets. It interpolates
between selected samples over a learned embedded subspace, guided by XAI (sensitivity/feature
attribution) and UCQ (uncertainty-conditioned quantification via VAE models). It has a FastAPI
backend and a Vue 3 + Vuetify frontend.

## Commands

### Backend (Python, managed with `uv`, Python 3.13)

```bash
uv sync --index-strategy unsafe-best-match   # install deps; needed because of the NVIDIA CUDA index
python -m uvicorn backend:app --reload       # run the API (serves OpenAPI at /openapi.json)
```

There is no test suite, linter, or formatter configured for the backend.

Useful env vars (see `backend/datamans/config.py`, `.vscode/launch.json`):
- `DATA_DIR` — base directory for datasets/models (default `./data`).
- `SETS_CONFIG_JSON` — path to a JSON file describing dataset configs to load instead of the
  hardcoded defaults in `SetsManager.load_defaults` (`backend/datamans/sets.py`). Example:
  `data/datasets/config_minimal_only_normal.json`.
- `EMBEDDING` — comma-separated dimensionality-reduction modes (`tsne`, `pca`, `umap`); first one
  in the list is what's actually used per `ModelManager`.

The VSCode debug config (`.vscode/launch.json`, "Python Debugger: FastAPI") runs
`uvicorn backend:app --reload --port 8091` with `SETS_CONFIG_JSON` pointed at a minimal dataset
config — use port 8091 to match the frontend's default `PI_API_BASE_URL`.

### Frontend (Vue 3 + Vuetify + Vite, in `frontend/`)

```bash
npm i -D              # install deps
npm run dev           # start Vite dev server on :3000, proxies to PI_API_BASE_URL (.env.development)
npm run build          # vue-tsc --noEmit && vite build (type-check then production build)
npm run preview
npm run generate-client  # regenerate frontend/src/api/Api.ts from a running backend's OpenAPI schema
                          # (`sta generate -p http://localhost:8091/openapi.json -o ./src/api/ --axios`)
                          # run this after changing any backend router/model, then start the backend first
```

There is no frontend test suite or linter/formatter configured (biome/eslint are present only as
transitive deps, not wired up).

### Docker

`Dockerfile` (repo root) builds the backend via `pip install -r requirements.txt`, exposes 8000,
runs `uvicorn backend:app`. `frontend/Dockerfile` builds the Vite app separately (see
`.gitlab-ci.yml` for the two-image `build-frontend` / `build-backend` CI jobs; there is no
configured test stage).

## Architecture

### Backend: multi-dataset manager pattern

The backend is built to serve several unrelated tabular datasets (alloy simulation, PrivBayes,
MAST, electric arc furnace, blast furnace, Hilti, …) through the same generic API, selected via a
`set_name` query param on almost every endpoint.

- `backend/datamans/config.py` — `DataConfig`: a dataclass describing one dataset (file path,
  input/output column counts, whether a time column exists, whether inputs are bounded/constrained,
  which VAE variant to use for UCQ).
- `backend/datamans/sets.py` — `SetsManager`: builds a (possibly nested) tree of `ModelManager`s,
  one per dataset, either from hardcoded `DataConfig` instances or from a JSON file pointed to by
  `SETS_CONFIG_JSON`. Dataset names can be nested/grouped (e.g. `blast_furnace-alkper-BAS2...`,
  joined with `-` as the separator) — `get_manager("a-b-c")` walks the nested dict.
  `sets_manager` (module-level singleton) is imported directly by the routers.
- `backend/datamans/modelman.py` — `ModelManager`: owns one dataset's full lifecycle:
  1. `load_data_file()` reads CSV/TSV, splits columns into inputs/outputs by position (first N
     input_cols, next M output_cols, after an optional leading time column), cleans NaN/inf.
  2. `load()` (lazy — only called when a route passes `load=True`, or a dataset is explicitly
     `POST /datasets/load/{set_name}`'d) is expensive: fits a per-dataset 2D embedding
     (TSNE/UMAP, cached to `.npy` under `models/<short_data_name>/`) for each column-type subset
     from `backend/col_defs.py` (or all-inputs/all-outputs/all for non-scivis datasets), trains
     or loads one LightGBM regressor per output column (`models/<short_data_name>/lgbms/`) as a
     cheap forward surrogate, and — if `use_ucq` is set — trains/loads a VAE (`ucq/models/`) used
     purely to estimate per-column uncertainty (`eval_uncertainties`).
  3. Nearest-neighbor indices (`sklearn`/`cuml` `NearestNeighbors`) over both scaled outputs and
     raw inputs back most of the "find similar/interpolated point" endpoints.
  - GPU acceleration is opportunistic: `cuml` (RAPIDS) is imported for `NearestNeighbors`/`UMAP`/
    `TSNE` and silently falls back to `sklearn`/`umap-learn` if unavailable (see the `try/except`
    at the top of `modelman.py`).
- `backend/col_defs.py` — hardcoded column groupings (`elements`, `phase_formations`, …) specific
  to the scivis/alloy dataset; used only when `short_data_name` contains `"scivis"`.

### Backend: routers

`backend/routers/__init__.py` nests everything data-related under
`/datasets/{set_name}/...` (`grouped_sets_router`), alongside the flat `/datasets` router for
listing/loading datasets:
- `sets.py` — list all datasets' settings, load a dataset, get one dataset's settings.
- `data.py` — description/raw data/histograms/column types/2D embeddings for a dataset.
- `datapoint.py` (`/data-point`) — per-point queries: nearest-neighbor similarity, single point
  lookup, **linear interpolation between two points** (predicts intermediate outputs via the
  LightGBM ensemble, then snaps each interpolated step to its nearest real neighbor for display),
  similarity search by raw values, per-column sensitivity analysis (perturb one input at a time,
  measure output delta), suggestion search (nearest points to a target output vector, optionally
  weighted against a base point's differing columns). Includes `minimizer.py`'s router.
- `minimizer.py` (`/data-point/minimize`) — multi-target cost minimization: `get_costs` computes a
  normalized weighted distance from a set of `LinearTarget`s; `/cost` scores every point;
  `/interpolation` finds the best-`k` candidate points under filters/costs and interpolates paths
  toward them the same way `datapoint.py` does, augmenting the nearest-neighbor lookup with the
  cost value as an extra dimension so the path favors cost-decreasing intermediate points.

When adding a new dataset, add a `DataConfig` (in `sets.py` or a `SETS_CONFIG_JSON` file) rather
than new code — the generic `ModelManager` pipeline is meant to handle arbitrary tabular datasets.

### UCQ module (`ucq/`)

Standalone-ish package for uncertainty-conditioned quantification, imported by the backend for
optional per-point uncertainty estimates:
- `ucq/models/base.py` — `BaseUCQModel(nn.Module)`: interface (`forward`, `encode`, `uncertainty`,
  `fit`) that all UCQ models implement.
- `ucq/models/vae.py`, `ucq/models/gp_vae.py` — the two concrete VAE variants
  (`VAEOptions.m_VAE` / `VAEOptions.m_GPVAE` in `config.py`); a Gaussian-process-flavored VAE and a
  plain VAE.
- `ucq/models/random_model.py` — a baseline/random model for comparison.
- `ucq/utils.py` — training loop (`train_vae_noiseless`) and tensor helpers
  (`minmaxnormed_tensor_of`, `autodevice`) used by `ModelManager.load()`.
- `ucq/exploration.ipynb` — exploratory notebook, not part of the served app.

### Frontend

Vue 3 + Vuetify + Vite SPA (auto-imports components via `unplugin-vue-components`).

- `frontend/src/api/Api.ts` — **generated** typed Axios client (via `npm run generate-client` from
  the backend's live OpenAPI schema). Do not hand-edit; regenerate it after backend model/route
  changes.
- `frontend/src/config.ts` — reads `PI_API_BASE_URL` / `PI_ENV_SITE_BASE_URL` from Vite env
  (`envPrefix: 'PI_'` in `vite.config.mts`; see `.env.development` / `.env.production`).
- `frontend/src/proc/data-store.ts` — client-side state/data handling for the loaded dataset.
- `frontend/src/views/` — top-level routed pages: `DataSetSelector.vue` (pick/load a dataset),
  `Interpolator.vue` (main exploration UI).
- `frontend/src/components/` — organized by feature area: `adjuster/` (parameter sliders),
  `dataset/` (dataset overview), `formulation/` (building linear cost-target expressions, mirrors
  `LinearTarget`/`DataPointMinimzer` on the backend), `interpolation/` and `panels/` (interpolation
  results and guided search UI), `spyder/` (spyder/radar chart for multi-output comparison),
  `helpers/` (D3 color/annotation utilities shared across charts).

### Data/model layout on disk

Not tracked in git (see `.gitignore`): `data/` (raw datasets, expected under
`data/datasets/<data_file>` per each `DataConfig`) and per-dataset trained artifacts under
`models/<short_data_name>/` (cached embeddings as `.npy`, LightGBM models under `lgbms/`, pickled
VAE models). `configs.json` (repo root) is a generated dump of the default dataset configs, also
gitignored.
