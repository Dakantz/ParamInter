from fastapi import APIRouter, Body
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from tqdm import tqdm

from backend.models import (
    CostOverview,
    DataPointMinimzer,
    DataPointMinimzerInterpolation,
    FilterCondition,
    InterpolationResult,
)
from backend.routers.sets import sets_manager


minimizer_router = APIRouter(prefix="/minimize")


def get_costs(targets: list[DataPointMinimzer], data: pd.DataFrame) -> np.ndarray:
    costs_dict: dict[str, np.ndarray] = {}
    for target in targets:
        # ((target-min) - (data-min)) => (target - data) / (data.max - data.min)
        diff = data[target.name].max() - data[target.name].min()
        diff = diff if diff > 1e-6 else 1.0
        costs_target = (target.val - data[target.name].to_numpy()) / diff
        costs_dict[target.name] = target.weight * costs_target
    costs = np.empty(
        (
            data.shape[0],
            len(targets),
        )
    )
    for i, cost in enumerate(costs_dict.values()):
        costs[:, i] = cost**2
    costs_sum: np.ndarray = np.sqrt(costs).sum(axis=-1)
    return costs_sum


def apply_filters(
    filters: list[FilterCondition], data: pd.DataFrame
) -> tuple[pd.DataFrame, np.ndarray, pd.Series]:
    dps = data.copy()
    filtered_points = np.ones(len(data), dtype=bool)
    for filter_cond in filters:
        if filter_cond.min is not None:
            filtered_points &= data[filter_cond.name] >= filter_cond.min
        if filter_cond.max is not None:
            filtered_points &= data[filter_cond.name] <= filter_cond.max
    filtered_data = dps[filtered_points]
    lookup_table = data.index.to_series()[filtered_points].reset_index(drop=True)
    return filtered_data, filtered_points, lookup_table


@minimizer_router.post("/cost")
def get_objective_costs(
    q: DataPointMinimzer = Body(DataPointMinimzer),
    set_name: str = None,
) -> CostOverview:
    data_man = sets_manager.get_manager(set_name)

    filtered_data, within_filter, _ = apply_filters(q.filters, data_man.cleaned)
    total_cost_clean = get_costs(q.targets, data_man.cleaned)
    total_cost_clean_normed = (total_cost_clean - total_cost_clean.min()) / (
        total_cost_clean.max() - total_cost_clean.min()
    )
    return CostOverview(
        costs=total_cost_clean_normed.tolist(), within_filter=within_filter.tolist()
    )


@minimizer_router.post("/interpolation")
def get_minimization_interpolation(
    q: DataPointMinimzerInterpolation = Body(DataPointMinimzerInterpolation),
    set_name: str = None,
) -> list[InterpolationResult]:
    data_man = sets_manager.get_manager(set_name)
    filtered_df, within_filter, lookup_table = apply_filters(
        q.min.filters, data_man.cleaned
    )
    costs_sum = get_costs(q.min.targets, filtered_df)
    nn_stacked_X = np.concatenate(
        [
            filtered_df[data_man.input_cols].to_numpy(),
            q.cost_penalty * costs_sum.reshape(-1, 1),
        ],
        axis=1,
    )

    nn_inputs = NearestNeighbors(n_neighbors=1)
    nn_inputs.fit(nn_stacked_X)

    argmin_indexes = np.argsort(costs_sum)[: q.k_options]
    int_results = []
    for argmin_index in argmin_indexes:
        start_dp = data_man.cleaned.iloc[q.start_idx, :][data_man.input_cols].values
        end_dp = filtered_df.iloc[argmin_index, :][data_man.input_cols].values

        inputs_interpolated: np.ndarray = np.linspace(start_dp, end_dp, q.samples)

        outputs_interpolated: np.ndarray = np.empty(
            (q.samples, len(data_man.output_cols))
        )

        for i, cm in enumerate(tqdm(data_man.model_ensemble.items())):
            _, model = cm
            predictions = model.predict(inputs_interpolated)
            outputs_interpolated[:, i] = predictions
        interpolated = np.concatenate(
            [inputs_interpolated, outputs_interpolated], axis=1
        )
        interpolated_data = pd.DataFrame(
            interpolated,
            columns=filtered_df.columns,
        )
        interpolated_costs = get_costs(q.min.targets, interpolated_data)

        nn_stacked_query = np.concatenate(
            [inputs_interpolated, q.cost_penalty * interpolated_costs.reshape(-1, 1)],
            axis=1,
        )

        _, indices = nn_inputs.kneighbors(nn_stacked_query)
        indices = indices.flatten()
        # indices[0] = q.start_idx
        indices[-1] = argmin_index

        uncertainties_interpolated = data_man.uncertainty.loc[indices, :]

        embeddings_nn: dict[str, list] = {}
        indices_global = lookup_table.iloc[indices].tolist()
        for col_name, embedded in data_man.embedding_subsets.items():
            embeddings_nn[col_name] = embedded[indices_global].tolist()
        int_results.append(
            InterpolationResult(
                inputs=inputs_interpolated.tolist(),
                outputs=outputs_interpolated.tolist(),
                knn_inputs=filtered_df[data_man.input_cols].values[indices].tolist(),
                knn_outputs=filtered_df[data_man.output_cols].values[indices].tolist(),
                projected_outputs=embeddings_nn,
                indices=indices_global,
                uncertainties=uncertainties_interpolated.values.tolist(),
            )
        )
    return int_results
