import pandas as pd
import numpy as np
from fastapi import Body, FastAPI

# cors
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sklearn.base import TransformerMixin
import umap
import lightgbm as lgb

from sklearn.preprocessing import MinMaxScaler, StandardScaler

try:
    from cuml.neighbors import NearestNeighbors
    from cuml.manifold.umap import UMAP
    from cuml import TSNE
except ImportError:
    from sklearn.neighbors import NearestNeighbors
    from sklearn.manifold import TSNE
    from umap import UMAP

    print("Cuml not found, using CPU-based libraries.")
    cuml = None

from .col_defs import column_types, input_types
from .models import (
    DataDescription,
    DataPoints,
    DataPoint,
    InterpolationResult,
    SensitivityAnalysisResult,
)

import tqdm
from pathlib import Path


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

data = pd.read_table("./alloy_data.txt")
input_cols = data.columns.to_list()[:6]
output_cols = data.columns.to_list()[6:70]
cleaned = data[input_cols + output_cols].fillna(0)

nn = NearestNeighbors(n_neighbors=1)
nn.fit(cleaned[output_cols].values)

nn_inputs = NearestNeighbors(n_neighbors=1)
nn_inputs.fit(cleaned[input_cols].values)


scaler_outs = StandardScaler()
scaled_outputs = scaler_outs.fit_transform(cleaned[output_cols].values)


modes = {
    "tsne": TSNE,
    "umap": UMAP,
}

mode = "tsne"
embedding_subsets: dict[str, np.ndarray] = {}
dim_reducers: dict[str, TransformerMixin] = {}
for col_name, col_list in tqdm.tqdm(column_types.items(), desc="Creating embeddings"):
    data_path = Path(f"data/{col_name}_{mode}.npy")
    if data_path.exists():
        embedded_tsne = np.load(data_path)
        embedding_subsets[col_name] = embedded_tsne
    else:
        dim_reducers[col_name] = (
            TSNE(
                n_components=2,
                perplexity=40,
            )
            if mode == "tsne"
            else UMAP(
                n_neighbors=15,
            )
        )
        embedded_tsne: np.ndarray = dim_reducers[col_name].fit_transform(
            cleaned[col_list].values
        )
        scaled_tsne = MinMaxScaler().fit_transform(embedded_tsne)
        np.save(data_path, scaled_tsne)
        embedding_subsets[col_name] = scaled_tsne


model_ensemble: dict[str, lgb.LGBMRegressor] = {}
for output_col in tqdm.tqdm(output_cols, desc="Loading models"):
    col_name = output_col.encode("ascii", "ignore").decode("ascii")
    col_name = col_name.replace(" ", "_")
    col_name = col_name.replace(".", "_")
    col_name = col_name.replace("/", "_")
    model = lgb.Booster(
        model_file=f"models/{col_name}_model.txt",
    )
    model_ensemble[output_col] = model

print("Model ensemble loaded with models for outputs:", model_ensemble.keys())


@app.get("/data_description", response_model=DataDescription)
def get_data_description():
    return DataDescription(
        input_cols=input_cols,
        output_cols=output_cols,
        num_samples=len(data),
        num_features=len(input_cols),
        num_outputs=len(output_cols),
        min_values=cleaned[output_cols].min().to_dict(),
        max_values=cleaned[output_cols].max().to_dict(),
        mean_values=cleaned[output_cols].mean().to_dict(),
        std_values=cleaned[output_cols].std().to_dict(),
    )


@app.get("/data")
def get_data() -> DataPoints:
    data_points = DataPoints(
        inputs=cleaned[input_cols].values.tolist(),
        outputs=cleaned[output_cols].values.tolist(),
        projected_outputs=embedded_tsne.tolist(),
    )
    return data_points


@app.get("/data_point/similarity-scores/{index}")
def get_similar_data_point(index: int) -> list[float]:
    if index < 0 or index >= len(data):
        return {"error": "Index out of bounds"}

    input_data = cleaned[input_cols].iloc[index].values

    similarities = np.abs((cleaned[input_cols].values / 100) * (input_data / 100)).sum(
        axis=1
    )
    return similarities


@app.get("/data_point/idx/{index}")
def get_data_point(index: int) -> DataPoint:
    if index < 0 or index >= len(data):
        return None

    input_data = cleaned[input_cols].iloc[index].values.tolist()
    output_data = cleaned[output_cols].iloc[index].values.tolist()
    projected_output = embedded_tsne[index].tolist()

    return DataPoint(
        inputs=input_data,
        outputs=output_data,
        projected_outputs=projected_output,
        index=index,
    )


@app.get("/column_types")
def get_column_types() -> dict[str, list[str]]:
    return column_types


@app.get("/embedding/{col_type}")
def get_embedding(col_type: str) -> list[list[float]]:
    if col_type in embedding_subsets:
        return embedding_subsets[col_type].tolist()
    return []


@app.get("/interpolation")
def get_interpolation(
    from_index: int,
    to_index: int,
    n_samples=128,
    embedding_type: str = "all",
    include_explainations: bool = False,
) -> InterpolationResult:
    dp_idxs = [from_index, to_index]

    inputs = cleaned[input_cols].values[dp_idxs]

    interpolated_inputs = np.linspace(inputs[0], inputs[1], n_samples)

    outputs_interpolated = np.empty((n_samples, len(output_cols)))

    for i, cm in enumerate(tqdm.tqdm(model_ensemble.items())):
        _, model = cm
        predictions = model.predict(interpolated_inputs)
        outputs_interpolated[:, i] = predictions
    outputs_interpolated_scaled = scaler_outs.transform(outputs_interpolated)
    # find closest points in the embedding space   

    nn_out_scaled = NearestNeighbors(n_neighbors=1)
    nn_out_scaled.fit(scaled_outputs)

    _, indices = nn_out_scaled.kneighbors(outputs_interpolated_scaled)
    indices = indices.flatten()
    indices[0] = from_index
    indices[-1] = to_index
    embeddings_nn: dict[str, list] = {}
    if embedding_type == "all":
        # embeddings_nn["full"] = embedded_tsne[indices.flatten()].tolist()
        for col_name, embedded in embedding_subsets.items():
            embeddings_nn[col_name] = embedded[indices].tolist()
    else:
        if embedding_type in embedding_subsets:
            embeddings_nn[embedding_type] = embedding_subsets[embedding_type][
                indices
            ].tolist()
    explanations = np.zeros_like(outputs_interpolated)

    if include_explainations:
        for i in range(outputs_interpolated.shape[0]):
            idx = indices[i]
            explanations_list = explanations_for_dp(
                idx, data=DataPointSensitivity(for_outputs=output_cols, resolution=4)
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
        knn_inputs=cleaned[input_cols].values[indices].tolist(),
        knn_outputs=cleaned[output_cols].values[indices].tolist(),
        projected_outputs=embeddings_nn,
        indices=indices.tolist(),
        explainations=explanations.tolist(),
    )


class DataPointSimilarity(BaseModel):
    values: list[float]
    k: int


@app.post("/data_point/similar")
def get_similar_data_points(
    q: DataPointSimilarity = Body(DataPointSimilarity),
) -> list[DataPoint]:
    if len(q.values) != len(input_cols):
        return []

    values = np.array(q.values).reshape(1, -1)
    nn_inputs = NearestNeighbors(n_neighbors=q.k)
    nn_inputs.fit(cleaned[input_cols].values)
    _, indices = nn_inputs.kneighbors(values, n_neighbors=q.k)
    indices = indices.flatten()
    input_data = cleaned[input_cols].iloc[indices].values.tolist()
    output_data = cleaned[output_cols].iloc[indices].values.tolist()
    projected_output = embedded_tsne[indices].tolist()
    similar_data_points = [
        DataPoint(
            inputs=input_data[i],
            outputs=output_data[i],
            projected_outputs=projected_output[i],
            index=indices[i],
        )
        for i in range(indices.shape[0])
    ]

    return similar_data_points


class DataPointSensitivity(BaseModel):
    for_outputs: list[str] = []
    resolution: int = 16


@app.post("/data_point/explanations/{idx}")
def explanations_for_dp(
    idx: int,
    data: DataPointSensitivity = Body(DataPointSensitivity),
) -> list[SensitivityAnalysisResult]:
    # vary the inputs of the data point at idx
    if idx < 0 or idx >= cleaned.shape[0]:
        return []
    results: list[SensitivityAnalysisResult] = []
    for out_col in data.for_outputs:
        estimator = model_ensemble.get(out_col)
        if not estimator:
            continue
        input_data = cleaned[input_cols].iloc[idx].values
        sensitivities = np.zeros(len(input_cols))
        for i, input_col in enumerate(input_cols):
            # vary the input column by 1%
            perturbed_input = np.empty((data.resolution, len(input_cols)))
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
            dp=DataPoint(
                inputs=cleaned[input_cols].iloc[idx].values.tolist(),
                outputs=cleaned[output_cols].iloc[idx].values.tolist(),
                projected_outputs=embedded_tsne[idx].tolist(),
                index=idx,
            ),
            sensitivity_scores=sensitivities.tolist(),
            out_col=out_col,
        )
        results.append(output_sensitivities)
    return results


class DataPointSuggestions(BaseModel):
    base_index: int = None
    values: list[float] = []
    k: int = 5
    weigh_changes: float = 1.5


@app.post("/data_point/suggestions")
def data_point_suggestions(
    q: DataPointSuggestions = Body(DataPointSuggestions),
) -> list[DataPoint]:
    if len(q.values) != len(output_cols):
        return []
    # base_values = cleaned[output_cols].iloc[q.base_index].values
    values = np.array(q.values)
    weights = np.ones(len(output_cols))
    scaled_values = scaler_outs.transform(values.reshape(1, -1))
    if q.base_index is not None:
        base_values = cleaned[output_cols].iloc[q.base_index].values
        scaled_base_values = scaler_outs.transform(base_values.reshape(1, -1))
        weights = np.where(
            np.abs(scaled_values - scaled_base_values) > 1e-4, q.weigh_changes, 1
        )

    weights = weights / np.linalg.norm(weights)

    def weighted_distance(a, b):
        return np.sqrt(np.mean((weights * np.abs(a - b)) ** 2))

    nn_outs = NearestNeighbors(n_neighbors=q.k, metric=weighted_distance)
    values = values.reshape(1, -1)
    nn_outs.fit(scaled_outputs)
    _, indices = nn_outs.kneighbors(scaled_values, n_neighbors=q.k)
    indices = indices.flatten()
    if q.base_index is not None:
        indices = indices[indices != q.base_index]
    input_data = cleaned[input_cols].iloc[indices].values.tolist()
    output_data = cleaned[output_cols].iloc[indices].values.tolist()
    projected_output = embedded_tsne[indices].tolist()

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
