from fastapi import APIRouter, Body
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from tqdm import tqdm

from backend.models import (
    DataPointMinimzer,
    DataPointMinimzerInterpolation,
    InterpolationResult,
)
from backend.routers.sets import sets_manager


minimizer_router = APIRouter(prefix="/minimize")


@minimizer_router.post("/cost")
def get_objective_costs(
    q: DataPointMinimzer = Body(DataPointMinimzer),
    set_name: str = None,
) -> list[float]:
    data_man = sets_manager.get_manager(set_name)
    costs: dict[str, np.ndarray] = {}
    for target in q.targets:
        costs_target = data_man.cleaned[target.name].to_numpy() - target.val
        costs[target.name] = target.weight * costs_target
    total_cost = np.empty((len(q.targets), data_man.cleaned.shape[0]))
    for i, cost in enumerate(costs.values()):
        total_cost[i, :] = cost**2

    total_cost_clean: np.ndarray = np.sqrt(total_cost).sum(axis=0)
    total_cost_clean_normed = (total_cost_clean - total_cost_clean.min()) / (
        total_cost_clean.max() - total_cost_clean.min()
    )
    return total_cost_clean_normed.tolist()


def get_costs(targets: list[DataPointMinimzer], data: pd.DataFrame) -> np.ndarray:
    costs_dict: dict[str, np.ndarray] = {}
    for target in targets:
        costs_target = data[target.name].to_numpy() - target.val
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


@minimizer_router.post("/interpolation")
def get_minimization_interpolation(
    q: DataPointMinimzerInterpolation = Body(DataPointMinimzerInterpolation),
    set_name: str = None,
) -> list[InterpolationResult]:
    data_man = sets_manager.get_manager(set_name)
    costs_sum = get_costs(q.min.targets, data_man.cleaned)
    nn_stacked_X = np.concatenate(
        [
            data_man.cleaned[data_man.input_cols].to_numpy(),
            q.cost_penalty * costs_sum.reshape(-1, 1),
        ],
        axis=1,
    )

    nn_inputs = NearestNeighbors(n_neighbors=1)
    nn_inputs.fit(nn_stacked_X)

    argmin_index = np.argsort(costs_sum)[: q.k_options]
    int_results = []
    for argmin_index in argmin_index:
        dp_idxs = [q.start_idx, argmin_index]

        inputs = data_man.cleaned[data_man.input_cols].values[dp_idxs]

        inputs_interpolated: np.ndarray = np.linspace(inputs[0], inputs[1], q.samples)

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
            columns=data_man.cleaned.columns,
        )
        interpolated_costs = get_costs(q.min.targets, interpolated_data)

        nn_stacked_query = np.concatenate(
            [inputs_interpolated, q.cost_penalty * interpolated_costs.reshape(-1, 1)],
            axis=1,
        )

        _, indices = nn_inputs.kneighbors(nn_stacked_query)
        indices = indices.flatten()
        indices[0] = q.start_idx
        indices[-1] = argmin_index

        uncertainties_interpolated = data_man.uncertainty.loc[indices, :]

        embeddings_nn: dict[str, list] = {}

        for col_name, embedded in data_man.embedding_subsets.items():
            embeddings_nn[col_name] = embedded[indices].tolist()
        int_results.append(
            InterpolationResult(
                inputs=inputs_interpolated.tolist(),
                outputs=outputs_interpolated.tolist(),
                knn_inputs=data_man.cleaned[data_man.input_cols]
                .values[indices]
                .tolist(),
                knn_outputs=data_man.cleaned[data_man.output_cols]
                .values[indices]
                .tolist(),
                projected_outputs=embeddings_nn,
                indices=indices.tolist(),
                uncertainties=uncertainties_interpolated.values.tolist(),
            )
        )
    return int_results
