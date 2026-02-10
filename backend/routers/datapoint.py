from fastapi import APIRouter, Body, Depends
import numpy as np
import pandas as pd
from pydantic import BaseModel
from sklearn.neighbors import NearestNeighbors
from torch import argmin
from torch.onnx.symbolic_opset9 import to
from tqdm import tqdm

from backend.models import (
    DataDescription,
    DataPoint,
    DataPointMinimzer,
    DataPointMinimzerInterpolation,
    DataPointSensitivity,
    DataPointSimilarity,
    DataPointSuggestions,
    DataPoints,
    InterpolationResult,
    SensitivityAnalysisResult,
)

from backend.routers.data import sets_manager
from backend.routers.minimizer import minimizer_router

dp_router = APIRouter(prefix="/data-point")

dp_router.include_router(minimizer_router)


@dp_router.get("/similarity-scores/{index}")
def get_similar_data_point(index: int, set_name: str = None) -> list[float]:
    data_man = sets_manager.get_manager(set_name)
    if index < 0 or index >= len(data_man.data):
        return {"error": "Index out of bounds"}

    input_data = data_man.cleaned[data_man.input_cols].iloc[index].values

    similarities = np.abs(
        (data_man.cleaned[data_man.input_cols].values / 100) * (input_data / 100)
    ).sum(axis=1)
    return similarities


@dp_router.get("/idx/{index}")
def get_data_point(index: int, set_name: str = None) -> DataPoint:

    data_man = sets_manager.get_manager(set_name, load=True)
    if index < 0 or index >= len(data_man.data):
        return None
    return data_man.get_dp(index)


@dp_router.get("/interpolation")
def get_interpolation(
    from_index: int,
    to_index: int,
    n_samples=128,
    embedding_type: str = "all",
    include_explainations: bool = False,
    set_name: str = None,
) -> InterpolationResult:
    data_man = sets_manager.get_manager(set_name)
    dp_idxs = [from_index, to_index]

    inputs = data_man.cleaned[data_man.input_cols].values[dp_idxs]

    interpolated_inputs = np.linspace(inputs[0], inputs[1], n_samples)

    outputs_interpolated = np.empty((n_samples, len(data_man.output_cols)))

    for i, cm in enumerate(tqdm(data_man.model_ensemble.items())):
        _, model = cm
        predictions = model.predict(interpolated_inputs)
        outputs_interpolated[:, i] = predictions
    outputs_interpolated_scaled = data_man.scaler_outs.transform(outputs_interpolated)
    # find closest points in the embedding space

    nn_out_scaled = NearestNeighbors(n_neighbors=1)
    nn_out_scaled.fit(data_man.scaled_outputs)

    _, indices = nn_out_scaled.kneighbors(outputs_interpolated_scaled)
    indices = indices.flatten()
    indices[0] = from_index
    indices[-1] = to_index
    embeddings_nn: dict[str, list] = {}
    if embedding_type == "all":
        # embeddings_nn["full"] = embedded_tsne[indices.flatten()].tolist()
        for col_name, embedded in data_man.embedding_subsets.items():
            embeddings_nn[col_name] = embedded[indices].tolist()
    else:
        if embedding_type in data_man.embedding_subsets:
            embeddings_nn[embedding_type] = data_man.embedding_subsets[embedding_type][
                indices
            ].tolist()
    explanations = np.zeros_like(outputs_interpolated_scaled)

    if include_explainations:
        for i in range(outputs_interpolated_scaled.shape[0]):
            idx = indices[i]
            explanations_list = explanations_for_dp(
                idx,
                data=DataPointSensitivity(
                    for_outputs=data_man.output_cols, resolution=4
                ),
            )
            # for each output column
            explanations[i, :] = np.array(
                [
                    np.array(explanation.sensitivity_scores).mean()
                    for explanation in explanations_list
                ]
            )
    return InterpolationResult(
        inputs=interpolated_inputs.tolist(),
        outputs=outputs_interpolated.tolist(),
        knn_inputs=data_man.cleaned[data_man.input_cols].values[indices].tolist(),
        knn_outputs=data_man.cleaned[data_man.output_cols].values[indices].tolist(),
        projected_outputs=embeddings_nn,
        indices=indices.tolist(),
        explainations=explanations.tolist(),
    )


@dp_router.post("/similar")
def get_similar_data_points(
    q: DataPointSimilarity = Body(DataPointSimilarity),
    set_name: str = None,
) -> list[DataPoint]:
    data_man = sets_manager.get_manager(set_name)
    if len(q.values) != len(data_man.input_cols):
        return []

    values = np.array(q.values).reshape(1, -1)
    nn_inputs = NearestNeighbors(n_neighbors=q.k)
    nn_inputs.fit(data_man.cleaned[data_man.input_cols].values)
    _, indices = nn_inputs.kneighbors(values, n_neighbors=q.k)
    indices = indices.flatten()
    input_data = data_man.cleaned[data_man.input_cols].iloc[indices].values.tolist()
    output_data = data_man.cleaned[data_man.output_cols].iloc[indices].values.tolist()
    projected_output = data_man.embedded_tsne[indices].tolist()
    uc = data_man.uncertainty.iloc[indices].values.tolist()
    similar_data_points = [
        DataPoint(
            inputs=input_data[i],
            outputs=output_data[i],
            projected_outputs=projected_output[i],
            index=indices[i],
            uncertainties=uc[i],
        )
        for i in range(indices.shape[0])
    ]

    return similar_data_points


@dp_router.post("/explanations/{idx}")
def explanations_for_dp(
    idx: int,
    data: DataPointSensitivity = Body(DataPointSensitivity),
    set_name: str = None,
) -> list[SensitivityAnalysisResult]:
    data_man = sets_manager.get_manager(set_name, True)
    # vary the inputs of the data point at idx
    if idx < 0 or idx >= data_man.cleaned.shape[0]:
        return []
    results: list[SensitivityAnalysisResult] = []
    for out_col in data.for_outputs:
        estimator = data_man.model_ensemble.get(out_col)
        if not estimator:
            continue
        input_data = data_man.cleaned[data_man.input_cols].iloc[idx].values
        sensitivities = np.zeros(len(data_man.input_cols))
        for i, input_col in enumerate(data_man.input_cols):
            # vary the input column by 1%
            perturbed_input = np.empty((data.resolution, len(data_man.input_cols)))
            perturbed_input[:] = input_data
            perturb_range = np.linspace(
                input_data[i] - 10, input_data[i] + 10, data.resolution
            )
            perturb_range = np.clip(perturb_range, 0.0, 100)
            perturbed_input[:, i] = perturb_range
            perturbed_output = estimator.predict(perturbed_input)
            sensitivities[i] = (perturbed_output[:-1] - perturbed_output[1:]).mean()
        # normalize sensitivities
        if np.linalg.norm(sensitivities) == 0:
            sensitivities = np.zeros_like(sensitivities)
        else:
            # normalize sensitivities to unit length
            sensitivities = sensitivities / np.linalg.norm(sensitivities)

        output_sensitivities = SensitivityAnalysisResult(
            dp=data_man.get_dp(idx),
            sensitivity_scores=sensitivities.tolist(),
            out_col=out_col,
        )
        results.append(output_sensitivities)
    return results


@dp_router.post("/suggestions")
def data_point_suggestions(
    set_name: str = None,
    q: DataPointSuggestions = Body(DataPointSuggestions),
) -> list[DataPoint]:
    data_man = sets_manager.get_manager(set_name)
    if len(q.values) != len(data_man.output_cols):
        return []
    # base_values = DATAMAN.cleaned[output_cols].iloc[q.base_index].values
    values = np.array(q.values)
    weights = np.ones(len(data_man.output_cols))
    scaled_values = data_man.scaler_outs.transform(values.reshape(1, -1))
    if q.base_index is not None:
        base_values = data_man.cleaned[data_man.output_cols].iloc[q.base_index].values
        scaled_base_values = data_man.scaler_outs.transform(base_values.reshape(1, -1))
        weights = np.where(
            np.abs(scaled_values - scaled_base_values) > 1e-4, q.weigh_changes, 1
        )

    weights = weights / np.linalg.norm(weights)

    def weighted_distance(a, b):
        return np.sqrt(np.mean((weights * np.abs(a - b)) ** 2))

    nn_outs = NearestNeighbors(n_neighbors=q.k, metric=weighted_distance)
    values = values.reshape(1, -1)
    nn_outs.fit(data_man.scaled_outputs)
    _, indices = nn_outs.kneighbors(scaled_values, n_neighbors=q.k)
    indices = indices.flatten()
    if q.base_index is not None:
        indices = indices[indices != q.base_index]
    input_data = data_man.cleaned[data_man.input_cols].iloc[indices].values.tolist()
    output_data = data_man.cleaned[data_man.output_cols].iloc[indices].values.tolist()
    projected_output = data_man.embedded_tsne[indices].tolist()

    suggestions = [
        DataPoint(
            inputs=input_data[i],
            outputs=output_data[i],
            projected_outputs=projected_output[i],
            index=indices[i],
        )
        for i in range(indices.shape[0])
    ]

    return suggestions


@dp_router.get("/posterior/{index}")
def posterior_of_data_point(index: int, set_name: str = None):
    pass
