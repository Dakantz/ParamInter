# ParamInter: Disclaimer

ParamInter is a visual analytics tool for exploring high-dimensional input-output parameter spaces of simulations; it has no clinical function.

> **Research use only. Not a medical device.**
> This software was developed in the HEREDITARY project as a research prototype. It has not been assessed or certified under the EU Medical Device Regulation (EU) 2017/745. It must not be used to diagnose, treat, monitor or make any other decision about individual patients.

## Overview

| Field | Value |
|---|---|
| Name | ParamInter (working title *AlloyInter* in HEREDITARY D5.2 and in the first Zenodo archive) |
| Version | `mlvis-2026` (latest tag; earlier tags `vis-2025`, `eurova-2026`) |
| Type | Web application with source code (FastAPI backend, Vue 3 + TypeScript frontend) |
| Owner partner and contact | TU Graz, Institute of Visual Computing (IVC); Benedikt Kantz, benedikt.kantz@tugraz.at |
| Licence | MIT, see [LICENSE](LICENSE) |
| Repository | https://github.com/Dakantz/ParamInter |
| DOI | Paper: [10.2312/mlvis.20261001](https://doi.org/10.2312/mlvis.20261001); code (`mlvis-2026`): [10.5281/zenodo.19886990](https://doi.org/10.5281/zenodo.19886990), all versions: [10.5281/zenodo.17415353](https://doi.org/10.5281/zenodo.17415353) |
| Demo | https://hereditary.cgv.tugraz.at/param-inter/ |
| Release date | Public since 2025-07-29; release `mlvis-2026` archived on Zenodo on 2026-04-29 |
| Related HEREDITARY task | WP5, T5.1 (high-dimensional data visualisation); described in D5.2 as "AlloyInter" |
| How to cite | Kantz, Waldert, Lengauer, Staudinger, Schuster, Schreck: *Parameter Space Analysis through Guided Visual Interpolations*, MLVis 2026, doi:10.2312/mlvis.20261001. BibTeX in the [README](README.md#citation) and [citation.cff](citation.cff). |

## Intended use

**Intended use.** Research into guided visual analytics for high-dimensional parameter spaces: the user picks a start sample, defines a cost function over target output values, and inspects an interpolation path from the start towards the lowest-cost sample, shown as small multiples and on a t-SNE embedding, with surrogate-based sensitivity (effect) hints and, where enabled, uncertainty estimates.

**Intended users.** Visualisation and simulation researchers, process and materials engineers, data scientists, developers.

**Out-of-scope uses.** This software must not be used for
- clinical diagnosis, prognosis, treatment or any other decision about a patient, including reading the in-silico tumour-immune simulation (`mast`) as treatment advice;
- decisions about individuals (insurance, employment, access to care);
- re-identification of individuals or any processing of personal or patient data;
- safety-critical control of a real process: the surrogates are research prototypes and not validated against the physical system;
- other data types or datasets whose input/output semantics the user does not understand: an interpolation path is only as meaningful as the simulation behind it.

## Data provenance

The repository contains **no datasets**. Data is read at runtime from `$DATA_DIR/datasets/` (default `./data/datasets/`), which is git-ignored.

The public demo serves four datasets:

| Dataset (`set_name`) | Source | Type | Content | Licence / ethics |
|---|---|---|---|---|
| `scivis_2025` | [IEEE SciVis Contest 2025](https://sciviscontest2025.github.io/data/), [Zenodo 10.5281/zenodo.15189444](https://doi.org/10.5281/zenodo.15189444) | Public, simulated | 6 scrap-input fractions, 64 simulated alloy properties | CC-BY-4.0 |
| `electric_arc_furnace` | Generated with `models/eaf` (Latin-hypercube sampling of an electric arc furnace model) | Synthetic | 6 process inputs, simulated melt and slag outputs | Simulation output |
| `mast` | Agent-based tumour-immune simulation runs (origin not documented in this repository) | Synthetic, in silico | 8 normalised cell-population counts, 10 simulation parameters | Simulation output; no patient records |
| `privbayes` | Privacy and utility metrics of synthetic-data generator configurations (origin not documented in this repository) | Aggregate metrics | 18 privacy-risk metrics as inputs, per-column utility metrics as outputs, one row per configuration | No individual-level records |

No dataset is patient-derived, so no ethics approval applies. `backend/datamans/sets.py` also defines configurations for industrial process data (blast furnace, used in the MLVis 2026 paper; Hilti). That data is not in the repository and not deployed on the public demo.

## Method

- **Pipeline.** The table is split by column position into inputs and outputs. The backend fits a 2D embedding per column group (t-SNE by default; UMAP or PCA via the `EMBEDDING` environment variable), a nearest-neighbour index over inputs and outputs, and one LightGBM regressor per output column as a forward surrogate. Interpolations between two samples are predicted with the surrogates and snapped to the nearest real sample for display. Sensitivity hints perturb one input at a time; the effects view computes SHAP values and interaction effects on the surrogates.
- **Training.** All models are fitted on the server at runtime, on the loaded dataset only, and cached under `$DATA_DIR/models/`. No weights are shipped. An optional VAE or GP-VAE (`ucq/`) estimates per-column uncertainty; it is enabled per dataset (`use_ucq`); the default configuration in `backend/datamans/sets.py` enables it only for the blast-furnace sets.
- **Privacy techniques.** None; no personal data is processed.
- **Outside services.** The backend contacts no outside service. The built frontend loads the Roboto font stylesheet from Google Fonts (`fonts.googleapis.com`) in the user's browser, so a visitor's IP address reaches Google. No application data is sent.

## Performance

There is no predictive model whose accuracy is claimed. The contribution is the guided exploration workflow, evaluated in the MLVis 2026 paper through expert interviews on the blast-furnace use case, and on the SciVis Contest 2025 alloy data in the earlier preprint ([arXiv:2509.19202](https://arxiv.org/abs/2509.19202)). Surrogate accuracy is not reported in this repository.

## Known limitations and risks

- **Generalisability.** Evaluated on a small number of materials and process use cases. Behaviour with very few samples, many more dimensions or strongly non-stationary data has not been measured.
- **Failure modes.** t-SNE neighbourhoods are not metric: a path that looks short on screen may be long in parameter space. LightGBM surrogates extrapolate poorly outside the sampled region, and the uncertainty estimate is itself a model. Suggested settings may be physically infeasible for datasets where inputs are not constrained (`inputs_constrained`).
- **Misinterpretation.** `mast` is biomedical in subject matter but entirely in silico; interpolations over it describe a simulation model, never a patient.
- **Privacy.** No personal data is processed and no weights are shipped; no membership-inference test was run, as there is no personal data to protect.
- **Deployment.** The API has no authentication and allows any CORS origin. Any client can read the full loaded tables (`GET /datasets/{set_name}/data/`) and trigger model fitting (`POST /datasets/load/{set_name}`). Only load data you are allowed to publish.

## Responsible use

- **Terms of use.** MIT licence ([LICENSE](LICENSE)). The public demo is read-only: there is no upload path and nothing a user enters is stored.
- **Open pre-release items.** Self-host the Roboto font instead of loading it from Google Fonts.
- **Contact for misuse or vulnerability reports.** Benedikt Kantz, benedikt.kantz@tugraz.at

## Acknowledgement

Funded by the European Union under grant agreement No 101137074 ([HEREDITARY](https://hereditary-project.eu/)).
Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union or the European Health and Digital Executive Agency (HaDEA).
Neither the European Union nor the granting authority can be held responsible for them.
