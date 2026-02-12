from fastapi import APIRouter, Depends

from backend.models import DataDescription, DataPoints, HistogramData
from backend.routers.sets import sets_manager
import numpy as np
import pandas as pd

data_router = APIRouter(prefix="/data")


@data_router.get("/description", response_model=DataDescription)
def get_data_description(set_name: str = None) -> DataDescription:
    data_man = sets_manager.get_manager(set_name)
    return DataDescription(
        input_cols=data_man.input_cols,
        output_cols=data_man.output_cols,
        num_samples=len(data_man.data),
        num_features=len(data_man.input_cols),
        num_outputs=len(data_man.output_cols),
        min_values=data_man.cleaned.min().to_dict(),
        max_values=data_man.cleaned.max().to_dict(),
        mean_values=data_man.cleaned.mean().to_dict(),
        std_values=data_man.cleaned.std().to_dict(),
        all_columns=data_man.cleaned.columns.tolist(),
        inputs_constrained=data_man.inputs_constrained,
    )


@data_router.get("/")
def get_data(set_name: str = None) -> DataPoints:
    data_man = sets_manager.get_manager(set_name)
    data_points = DataPoints(
        inputs=data_man.cleaned[data_man.input_cols].values.tolist(),
        outputs=data_man.cleaned[data_man.output_cols].values.tolist(),
        projected_outputs=data_man.embedded_tsne.tolist(),
    )
    return data_points


@data_router.get("/hist")
def get_histogram(col_name: str, set_name: str = None, bins: int = 10) -> HistogramData:
    data_man = sets_manager.get_manager(set_name, True)

    if col_name not in data_man.cleaned.columns:
        return HistogramData(bins=[], counts=[], relative=[])
    col_data = data_man.cleaned[col_name].dropna()
    hist, bin_edges = np.histogram(col_data, bins=bins)
    relative = hist / hist.sum() if hist.sum() > 0 else np.zeros_like(hist)
    return HistogramData(
        bins=bin_edges.tolist(), counts=hist.tolist(), relative=relative.tolist()
    )


@data_router.get("/column_types")
def get_column_types(set_name: str = None) -> dict[str, list[str]]:
    data_man = sets_manager.get_manager(set_name)
    return data_man.column_types


@data_router.get("/embedding/{col_type}")
def get_embedding(col_type: str, set_name: str = None) -> list[list[float]]:
    data_man = sets_manager.get_manager(set_name)
    if col_type in data_man.embedding_subsets:
        return data_man.embedding_subsets[col_type].tolist()
    return []
