from fastapi import APIRouter, Depends

from backend.dataman import data_man
from backend.models import DataDescription, DataPoints

data_router = APIRouter(prefix="/data")


@data_router.get("/description", response_model=DataDescription)
def get_data_description():
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
def get_data() -> DataPoints:
    data_points = DataPoints(
        inputs=data_man.cleaned[data_man.input_cols].values.tolist(),
        outputs=data_man.cleaned[data_man.output_cols].values.tolist(),
        projected_outputs=data_man.embedded_tsne.tolist(),
    )
    return data_points


@data_router.get("/column_types")
def get_column_types() -> dict[str, list[str]]:
    return data_man.column_types


@data_router.get("/embedding/{col_type}")
def get_embedding(col_type: str) -> list[list[float]]:
    if col_type in data_man.embedding_subsets:
        return data_man.embedding_subsets[col_type].tolist()
    return []
