import math
from itertools import combinations
from typing import Iterable

import numpy as np
import pandas as pd
import shap
from fastapi import APIRouter, Body, HTTPException

from backend.datamans.modelman import ModelManager
from backend.models import (
    BeeswarmResult,
    EffectsRequest,
    InteractionCombo,
    InteractionForRowsRequest,
    InteractionRequest,
    InteractionResult,
)
from backend.routers.sets import sets_manager

effects_router = APIRouter(prefix="/effects")

# 2**order model evaluations per Monte-Carlo permutation per combination for order >= 3, so keep
# this small.
MAX_ORDER = 6
# For order >= 3 we enumerate every C(pool, order) combination from the candidate pool, each
# needing its own Monte-Carlo estimate, so the pool must stay small there.
MAX_POOL_FOR_HIGH_ORDER = 10
MAX_COMBOS = 3000
MAX_TOP_K = 50


def _get_manager(set_name: str | None) -> ModelManager:
    data_man = sets_manager.get_manager(set_name, load=True)
    if data_man is None:
        raise HTTPException(status_code=404, detail=f"Dataset not found: {set_name}")
    return data_man


def _validate_output(data_man: ModelManager, output_col: str):
    if output_col not in data_man.output_cols:
        raise HTTPException(
            status_code=400, detail=f"Unknown output column: {output_col}"
        )


def _resolve_pool(data_man: ModelManager, features: list[str], order: int) -> list[str]:
    """Candidate feature pool to enumerate order-`order` combinations from (empty = all input
    columns), validated against the combinatorial cost of computing every combination."""
    pool = list(dict.fromkeys(features)) if features else list(data_man.input_cols)
    unknown = [f for f in pool if f not in data_man.input_cols]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown input column(s): {unknown}")
    if order < 1 or order > MAX_ORDER:
        raise HTTPException(status_code=400, detail=f"order must be between 1 and {MAX_ORDER}")
    if order > len(pool):
        raise HTTPException(
            status_code=400,
            detail=f"order ({order}) can't exceed the candidate pool size ({len(pool)})",
        )
    if order >= 3 and len(pool) > MAX_POOL_FOR_HIGH_ORDER:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Narrow the feature pool to at most {MAX_POOL_FOR_HIGH_ORDER} features for "
                "order >= 3 (Monte-Carlo cost grows combinatorially with the pool size)"
            ),
        )
    if math.comb(len(pool), order) > MAX_COMBOS:
        raise HTTPException(
            status_code=400,
            detail=f"{math.comb(len(pool), order)} combinations is too many; narrow the feature pool",
        )
    return pool


def _sample_indices(data_man: ModelManager, max_samples: int, seed: int) -> np.ndarray:
    n = data_man.cleaned.shape[0]
    if max_samples >= n:
        return np.arange(n)
    rng = np.random.default_rng(seed)
    return np.sort(rng.choice(n, size=max_samples, replace=False))


def _tree_explainer(data_man: ModelManager, output_col: str) -> shap.TreeExplainer:
    model = data_man.model_ensemble.get(output_col)
    if model is None:
        raise HTTPException(
            status_code=400, detail=f"No trained model for output column '{output_col}'"
        )
    return shap.TreeExplainer(model)


def _powerset(items: list[int]) -> Iterable[tuple[int, ...]]:
    for r in range(len(items) + 1):
        yield from combinations(items, r)


def _shapley_interaction_mc(
    data_man: ModelManager,
    output_col: str,
    features: list[str],
    foreground: np.ndarray,
    n_permutations: int,
    seed: int,
) -> np.ndarray:
    """
    Monte-Carlo estimate of the generalized Shapley interaction index for the coalition
    `features` (order >= 3), following Owen's sampling scheme: for a random permutation of the
    features *not* in the coalition, pick a random prefix T, then take the signed sum over all
    subsets W of the coalition of f(x with T u W taken from the foreground row, rest from a
    random background row). Averaging over many (permutation, background) draws converges to the
    exact interaction index; TreeSHAP itself only computes this efficiently up to order 2.
    """
    model = data_man.model_ensemble[output_col]
    input_cols = data_man.input_cols
    col_index = {c: i for i, c in enumerate(input_cols)}
    s_idx = [col_index[f] for f in features]
    other_idx = [i for i in range(len(input_cols)) if i not in s_idx]
    k = len(s_idx)
    n = foreground.shape[0]
    background_pool = data_man.cleaned[input_cols].to_numpy(dtype=np.float32)

    rng = np.random.default_rng(seed)
    subsets = list(_powerset(list(range(k))))
    signs = [(-1) ** (k - len(w)) for w in subsets]

    total = np.zeros(n, dtype=np.float64)
    for _ in range(n_permutations):
        bg_row = background_pool[rng.integers(0, background_pool.shape[0])]
        perm = rng.permutation(other_idx) if other_idx else np.array([], dtype=int)
        r = rng.integers(0, len(other_idx) + 1)
        t_idx = perm[:r]

        base = np.tile(bg_row, (n, 1))
        if len(t_idx):
            base[:, t_idx] = foreground[:, t_idx]

        delta = np.zeros(n, dtype=np.float64)
        for sign, subset in zip(signs, subsets):
            rows = base if not subset else base.copy()
            if subset:
                s_cols = [s_idx[w] for w in subset]
                rows[:, s_cols] = foreground[:, s_cols]
            delta += sign * np.asarray(model.predict(rows))
        total += delta
    return total / n_permutations


def _top_interactions(
    data_man: ModelManager,
    output_col: str,
    pool: list[str],
    order: int,
    foreground: pd.DataFrame,
    top_k: int,
    n_permutations: int,
    seed: int,
) -> list[InteractionCombo]:
    """Every order-`order` combination of `pool`, ranked by mean |Shapley interaction value|."""
    col_index = {c: i for i, c in enumerate(data_man.input_cols)}
    combos: list[tuple[tuple[str, ...], np.ndarray]] = []

    if order == 1:
        explanation = _tree_explainer(data_man, output_col)(foreground)
        values = np.asarray(explanation.values)
        for f in pool:
            combos.append(((f,), values[:, col_index[f]]))
    elif order == 2:
        interaction = np.asarray(
            _tree_explainer(data_man, output_col).shap_interaction_values(foreground)
        )
        for fi, fj in combinations(pool, 2):
            combos.append(((fi, fj), interaction[:, col_index[fi], col_index[fj]]))
    else:
        foreground_arr = foreground.to_numpy(dtype=np.float32)
        for combo in combinations(pool, order):
            values = _shapley_interaction_mc(
                data_man, output_col, list(combo), foreground_arr, n_permutations, seed
            )
            combos.append((combo, values))

    ranked = sorted(combos, key=lambda c: float(np.mean(np.abs(c[1]))), reverse=True)
    top_k = max(1, min(top_k, MAX_TOP_K, len(ranked)))
    return [
        InteractionCombo(
            features=list(feats),
            mean_abs=float(np.mean(np.abs(values))),
            values=np.asarray(values).tolist(),
        )
        for feats, values in ranked[:top_k]
    ]


@effects_router.post("/beeswarm")
def get_beeswarm(
    req: EffectsRequest = Body(EffectsRequest),
    set_name: str = None,
) -> BeeswarmResult:
    """First-order SHAP values for every input feature, for a sample of the dataset."""
    data_man = _get_manager(set_name)
    _validate_output(data_man, req.output_col)

    indices = _sample_indices(data_man, req.max_samples, req.seed)
    rows = data_man.cleaned[data_man.input_cols].iloc[indices]
    explanation = _tree_explainer(data_man, req.output_col)(rows)

    values = np.asarray(explanation.values)
    feature_values = rows.to_numpy()

    return BeeswarmResult(
        output_col=req.output_col,
        features=data_man.input_cols,
        indices=indices.tolist(),
        shap_values={
            col: values[:, i].tolist() for i, col in enumerate(data_man.input_cols)
        },
        feature_values={
            col: feature_values[:, i].tolist() for i, col in enumerate(data_man.input_cols)
        },
        base_value=float(np.asarray(explanation.base_values).mean()),
    )


@effects_router.post("/interaction")
def get_interaction(
    req: InteractionRequest = Body(InteractionRequest),
    set_name: str = None,
) -> InteractionResult:
    """
    Every order-`req.order` combination of features drawn from `req.features` (or, if empty, every
    input column), ranked by mean |Shapley interaction value| over a sample of the dataset, top
    `req.top_k` returned.
    """
    data_man = _get_manager(set_name)
    _validate_output(data_man, req.output_col)
    pool = _resolve_pool(data_man, req.features, req.order)

    indices = _sample_indices(data_man, req.max_samples, req.seed)
    rows = data_man.cleaned[data_man.input_cols].iloc[indices]
    combos = _top_interactions(
        data_man, req.output_col, pool, req.order, rows, req.top_k, req.n_permutations, req.seed
    )

    used_features = sorted({f for combo in combos for f in combo.features})
    return InteractionResult(
        output_col=req.output_col,
        order=req.order,
        indices=indices.tolist(),
        combinations=combos,
        feature_values={col: rows[col].to_numpy().tolist() for col in used_features},
    )


@effects_router.post("/interaction-for-rows")
def get_interaction_for_rows(
    req: InteractionForRowsRequest = Body(InteractionForRowsRequest),
    set_name: str = None,
) -> InteractionResult:
    """
    Same as `/interaction`, but evaluated on arbitrary, caller-supplied input rows (e.g. the path
    of an interpolation between two data points) instead of a sample of the dataset.
    """
    data_man = _get_manager(set_name)
    _validate_output(data_man, req.output_col)
    pool = _resolve_pool(data_man, req.features, req.order)

    n_cols = len(data_man.input_cols)
    if any(len(row) != n_cols for row in req.inputs):
        raise HTTPException(
            status_code=400, detail=f"Each input row must have {n_cols} values"
        )

    rows = pd.DataFrame(req.inputs, columns=data_man.input_cols)
    combos = _top_interactions(
        data_man, req.output_col, pool, req.order, rows, req.top_k, req.n_permutations, req.seed
    )

    used_features = sorted({f for combo in combos for f in combo.features})
    return InteractionResult(
        output_col=req.output_col,
        order=req.order,
        indices=[],
        combinations=combos,
        feature_values={col: rows[col].to_numpy().tolist() for col in used_features},
    )
