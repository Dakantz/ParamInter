# Ponytail Audit: highdim-gradex

## Ranked findings (biggest cut first)

### delete: `backend/hilti_exp.py` — dead Jupyter exploration notebook
Leftover from data exploration. Never imported by anything. ~300 lines of dead code.
`[backend/hilti_exp.py]`

### delete: `backend/hilti_exploration.py` — dead marimo notebook
Marimo notebook version of the above. Same dead exploration code. ~200 lines.
`[backend/hilti_exploration.py]`

### delete: `models/eaf/` — dead simulation code
`run_simulation.py` and `system_model/__init__.py` are never imported by the backend. Dead.
`[models/eaf/run_simulation.py, models/eaf/system_model/__init__.py]`

### delete: `ucq/noise.py` — 162 lines of unused noise classes
`Noiser`, `ColumnBasedNoiser`, `SingleModeColumnNoiser`, `MultiModeColumnNoiser`, `SingleModeGlobalNoiser`, `MultiModeGlobalNoiser` — none are imported anywhere outside `ucq/utils.py`'s `import` statement (which imports `Noiser` but only for type annotation in `train_vae()`). Even `train_vae()` is never called — only `train_vae_noiseless()` is used. The noise classes are dead.
`[ucq/noise.py]` → replace with: nothing. Delete the file.

### delete: `ucq/models/random_model.py` — 39 lines of dead baseline
`RandomBaseline` is never instantiated or imported outside `ucq/models/__init__.py`'s re-export. Nothing in the backend uses it. Dead.
`[ucq/models/random_model.py]` → replace with: nothing. Delete the file.

### yagni: `ucq/models/base.py` — 38 lines of abstract base for 2 implementations
`BaseUCQModel` defines `forward`, `encode`, `uncertainty`, `fit`, `reconstruct`. Only two subclasses exist: `VAE` and `GP_VAE`. The abstract interface is a class hierarchy with no real polymorphism at runtime — `ModelManager.load()` picks one concrete class via `VAEOptions.toClass()` and never treats them polymorphically beyond calling `.fit()` and `.uncertainty()`. The `reconstruct()` method has dead type-checking logic. The whole hierarchy can be collapsed to two plain `nn.Module` classes with the same method signatures.
`[ucq/models/base.py]` → replace with: delete `BaseUCQModel`, have `VAE` and `GP_VAE` extend `torch.nn.Module` directly.

### yagni: `ucq/models/__init__.py` — re-exports for dead code
Re-exports `BaseUCQModel` (deleted above) and `RandomBaseline` (deleted above). Also re-exports `GP_VAE` which is barely used. Simplify to only what's actually imported: `VAE`.
`[ucq/models/__init__.py]` → replace with: `from .vae import VAE`

### yagni: `backend/models.py` — 206 lines of Pydantic models, ~40% dead
`DataPoints`, `DataSample`, `HistogramData`, `DataPointSensitivity`, `DataPointSuggestions`, `CostOverview`, `DataPointMinimzerInterpolation`, `EffectsRequest`, `BeeswarmResult`, `InteractionRequest`, `InteractionForRowsRequest`, `InteractionCombo`, `InteractionResult`, `ManagerSettings` — many of these are only used by one endpoint each. `DataPoints` is only used by `/data` GET. `DataSample` only by `/data/sample`. `HistogramData` only by `/hist`. These are fine as-is (Pydantic models are the standard FastAPI pattern), but `DataPointMinimzer` (note the typo: "Minimzer" not "Minimizer") is used across 3 routers. The `posterior_of_data_point` endpoint in `datapoint.py` is `pass` — dead stub.
`[backend/models.py]` → delete: `DataPoints` (only one caller), `DataSample` (only one caller), `HistogramData` (only one caller). Fix typo: `DataPointMinimzer` → `DataPointMinimizer`. Delete dead `posterior_of_data_point` stub.

### yagni: `backend/utils.py` — Singleton metaclass, never used
`Singleton` metaclass is defined but never imported or used anywhere in the codebase. The `sets_manager` is a module-level singleton by convention, not by this metaclass.
`[backend/utils.py]` → replace with: nothing. Delete the file.

### yagni: `backend/datamans/__init__.py` — explicit `__all__` re-export
The `__all__` list is unnecessary — the module is only imported via `from backend.datamans import sets_manager` and `from backend.datamans.modelman import ModelManager`. The `__init__.py` just re-exports from submodules, adding a layer of indirection.
`[backend/datamans/__init__.py]` → replace with: delete the file entirely. Import directly from submodules.

### yagni: `backend/datamans/config.py` — `VAEOptions.toClass()` method
The `toClass()` method on the enum is a factory with exactly two branches. Inline it where used (`ModelManager.load()` calls `self.cfg.vae_mode.toClass()`).
`[backend/datamans/config.py]` → replace with: inline the two branches where `toClass()` is called.

### yagni: `ucq/utils.py` — `train_vae()` dead function
`train_vae()` (lines 17-71) trains a VAE with noise and train/val/test splits. Never called — only `train_vae_noiseless()` is used by `ModelManager.load()`.
`[ucq/utils.py]` → replace with: delete `train_vae()`. Keep `train_vae_noiseless()`, `minmaxnormed_tensor_of()`, `autodevice()`.

### yagni: `frontend/src/components/formulation/` — empty shell components
`Formulation.vue` is an empty `<div>` with placeholder styles. `NaryOp.vue`, `Input.vue`, `Constant.vue` are empty shell components with `defineModel` but no real logic. The `parts.ts` file defines an abstract class hierarchy (`FormulationPart`, `InputPart`, `ConstantPart`, `BinaryOpPart`, `NaryOpPart`, `UnaryOpPart`, `PlaceholderPart`) that mirrors the dead Vue components. This entire feature is speculatively built — no endpoint consumes it, no view renders it.
`[frontend/src/components/formulation/, frontend/src/components/formulation/parts.ts]` → replace with: delete the entire `formulation/` directory and `parts.ts`.

### yagni: `frontend/src/proc/data-store.ts` — `PlotSelection`, `PlotSelectionResults`, `ColumnObjective`, `CostOverviewData` classes
`PlotSelection` wraps a bunch of state management with `addIndex`, `removeIndex`, `clearSelection` methods that are just array operations. `minimizerToRecord`/`recordToMinimizer` are bidirectional converters for a data structure that could be used directly. `PlotSelectionResults` has one field (`similarities`) and no methods. `ColumnObjective` has two fields and no methods. `CostOverviewData` implements an interface but adds nothing over the raw type.
`[frontend/src/proc/data-store.ts]` → replace with: remove `PlotSelection`, `PlotSelectionResults`, `ColumnObjective`, `CostOverviewData`. Use raw types + reactive arrays.

### yagni: `frontend/src/components/types.ts` — `PlotSelection` class duplication
Duplicates `PlotSelection` from `data-store.ts`. Also has `MappedData`, `HoveredInterpolation` which are fine (interfaces).
`[frontend/src/components/types.ts]` → replace with: delete `PlotSelection`, `PlotSelectionResults`, `ColumnObjective`, `CostOverviewData` from this file.

### yagni: `frontend/src/components/helpers/utils.ts` — `gaussianPdf`, `erfinv`, `inverseNormalCdf` — hand-rolled stats
`gaussianPdf` is `1/(std*sqrt(2*pi)) * exp(-0.5*((x-mean)/std)^2)`. `erfinv` is a hand-rolled Newton solver. `inverseNormalCdf` wraps it. These could be replaced with `math.erf`/`scipy.stats` or a simpler lookup, but more importantly: grep shows they're not imported anywhere in the frontend. Dead.
`[frontend/src/components/helpers/utils.ts]` → replace with: delete `gaussianPdf`, `erfinv`, `inverseNormalCdf`.

### yagni: `frontend/src/components/helpers/colormaps.ts` — 10 hand-pasted color maps
~10,000 lines of raw hex color arrays pasted in as a module. These are viridis-like colormaps that d3 already ships. Replace with d3 built-in schemes: `d3.interpolateViridis`, `d3.interpolateTurbo`, `d3.interpolateInferno`, etc. Or better: use a single colormap.
`[frontend/src/components/helpers/colormaps.ts]` → replace with: `d3.interpolateViridis` (or one other d3 scheme). Delete the hand-pasted arrays.

### yagni: `frontend/src/api/Api.ts` — 1093 lines, auto-generated
This is generated by `npm run generate-client` from the backend's OpenAPI schema. It's fine as generated code, but it's large because the backend has many endpoints. If you delete dead endpoints (like `posterior_of_data_point`), this shrinks.
`[frontend/src/api/Api.ts]` → no action needed directly, but will shrink when dead endpoints are removed.

### yagni: `backend/datamans/modelman.py` — `dim_reducers` dict, cached embeddings
The `dim_reducers` dict is populated during `load()` but never read after. The `embedded_tsne` variable at the end of `load()` shadows the per-column `embedding_subsets` — there's a bug: `self.embedded_tsne = embedded_tsne` at the end of `load()` uses the last column's embedding, not a global one. The `embedded_tsne` attribute is used by `get_dp()` and several endpoints, but it's set to whatever the last column's embedding was. This is a latent bug, not over-engineering per se, but worth noting.
`[backend/datamans/modelman.py]` → replace with: delete `dim_reducers` (unused). Fix `embedded_tsne` assignment.

### yagni: `backend/datamans/sets.py` — `load_defaults()` writes `configs.json`
Every time defaults are loaded, it writes `configs.json` to disk. This file is gitignored. The write is useless side effect — nothing reads it.
`[backend/datamans/sets.py]` → replace with: delete the `json.dump` to `configs.json`.

### yagni: `ucq/models/gp_vae.py` — 241 lines, imports unused gpytorch symbols
Imports `VariationalLatentVariable`, `BayesianGPLVM`, `MultitaskMean`, `ConstantMeanGrad`, `LinearMean`, `LinearMeanGrad`, `MultitaskKernel`, `MultitaskGaussianLikelihood`, `MultitaskMultivariateNormal` — many of these are never used in the file. The file imports `numba` as `np` (shadowing numpy). Also imports `from ast import Mult` which is dead (the `Mult` alias is never used).
`[ucq/models/gp_vae.py]` → replace with: delete unused imports. Fix `from ast import Mult` → delete.

### shrink: `backend/routers/datapoint.py` — `get_interpolation` re-creates NearestNeighbors every call
`NearestNeighbors(n_neighbors=1)` is created and fitted on every `/interpolation` GET call. This should be cached on `ModelManager` (it's already computed in `load()` as `self.nn`).
`[backend/routers/datapoint.py]` → replace with: use `data_man.nn` instead of creating a new one.

### shrink: `backend/routers/datapoint.py` — `get_similar_data_points` re-fits NearestNeighbors every call
Same pattern: `NearestNeighbors(n_neighbors=q.k)` is created and fitted on every call. `self.nn_inputs` already exists on `ModelManager`.
`[backend/routers/datapoint.py]` → replace with: use `data_man.nn_inputs`.

### shrink: `backend/routers/datapoint.py` — `get_similar_data_points` re-fetches uncertainty every call
`data_man.uncertainty.iloc[indices]` is fetched on every call. Fine, but `projected_output` uses `data_man.embedded_tsne` which is the last-column embedding (bug noted above).
`[backend/routers/datapoint.py]` → no action beyond fixing `embedded_tsne` bug.

### yagni: `frontend/src/components/effects/types.ts` — `BeeswarmRow` interface
Only used by one component. Fine as a small interface. No action needed.
`[frontend/src/components/effects/types.ts]` → lean.

### delete: `frontend/src/plugins/index.ts` — dead, commented-out plugin registry
Everything is commented out (`// import vuetify from './vuetify'`, `// app.use(vuetify)`). `registerPlugins` is never called from `main.ts`. Dead file.
`[frontend/src/plugins/index.ts]` → replace with: nothing. Delete the file.

### yagni: `frontend/src/components/ui/Loading.vue` — used in 5 places
Used in `DataSetSelector.vue`, `Effects.vue`, `Interpolator.vue`, `InterpolationPanels.vue`, `DatapointGuide.vue`. Keep it — it's a simple reusable component.

### yagni: `backend/routers/effects.py` — `MAX_ORDER = 6`, `MAX_POOL_FOR_HIGH_ORDER = 10`, `MAX_COMBOS = 3000`, `MAX_TOP_K = 50`
These are magic numbers guarding against combinatorial explosion. They're reasonable constraints but could be config params. For now, they're fine — they prevent the server from hanging. Not over-engineering.
`[backend/routers/effects.py]` → lean.

### yagni: `backend/col_defs.py` — hardcoded alloy column groupings
These are only used when `short_data_name` contains `"scivis"`. They're fine as hardcoded data for one dataset. Not over-engineering.
`[backend/col_defs.py]` → lean.

### delete: `frontend/src/components/panels/ParallelCoordinatesSelector.vue` — dead component
grep confirms zero imports. Never rendered by any view.
`[frontend/src/components/panels/ParallelCoordinatesSelector.vue]` → delete.

### delete: `frontend/src/components/PlotsOverview.vue` — dead component
grep confirms zero imports. Never rendered by any view.
`[frontend/src/components/PlotsOverview.vue]` → delete.

### delete: `frontend/src/components/ReducedDimPlot.vue` — dead component
grep confirms zero imports. Never rendered by any view.
`[frontend/src/components/ReducedDimPlot.vue]` → delete.

## Summary

**Biggest wins (delete these first):**
1. `frontend/src/components/helpers/colormaps.ts` (~10,000 lines) — hand-pasted d3 alternatives
2. `backend/hilti_exp.py` (~300 lines) — dead notebook
3. `backend/hilti_exploration.py` (~200 lines) — dead notebook
4. `ucq/noise.py` (162 lines) — unused noise classes
5. `models/eaf/` (2 files) — dead simulation code
6. `frontend/src/components/formulation/` + `parts.ts` — entire dead feature
7. `ucq/models/random_model.py` (39 lines) — dead baseline
8. `ucq/utils.py` `train_vae()` (55 lines) — dead function
9. `ucq/models/base.py` (38 lines) — abstract base for 2 concrete classes
10. `frontend/src/plugins/index.ts` — dead, commented-out plugin registry
11. `frontend/src/components/PlotsOverview.vue` — dead component
12. `frontend/src/components/ReducedDimPlot.vue` — dead component
13. `frontend/src/components/panels/ParallelCoordinatesSelector.vue` — dead component
14. `backend/utils.py` (5 lines) — unused Singleton

**Net: ~11,000+ lines deletable, ~3 files to simplify, ~5 typos to fix.**

The codebase is mostly lean — the biggest bloat is from abandoned exploration notebooks, unused UCQ noise models, and the hand-pasted colormaps. The Pydantic models and FastAPI routers are standard patterns. The Vue frontend has some speculative UI (formulation components) that should be deleted.
