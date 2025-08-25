

from fastapi import APIRouter, Depends

from backend.dataman import dataman
from backend.models import DataDescription, DataPoints
data_router = APIRouter(prefix='/data')

@data_router.get("/description", response_model=DataDescription)
def get_data_description():
    return DataDescription(
        input_cols=dataman.input_cols,
        output_cols=dataman.output_cols,
        num_samples=len(dataman.data),
        num_features=len(dataman.input_cols),
        num_outputs=len(dataman.output_cols),
        min_values=dataman.cleaned[dataman.output_cols].min().to_dict(),
        max_values=dataman.cleaned[dataman.output_cols].max().to_dict(),
        mean_values=dataman.cleaned[dataman.output_cols].mean().to_dict(),
        std_values=dataman.cleaned[dataman.output_cols].std().to_dict(),
    )


@data_router.get("/")
def get_data() -> DataPoints:
    data_points = DataPoints(
        inputs=dataman.cleaned[dataman.input_cols].values.tolist(),
        outputs=dataman.cleaned[dataman.output_cols].values.tolist(),
        projected_outputs=dataman.embedded_tsne.tolist(),
    )
    return data_points


@data_router.get("/column_types")
def get_column_types() -> dict[str, list[str]]:
    return dataman.column_types



@data_router.get("/embedding/{col_type}")
def get_embedding(col_type: str) -> list[list[float]]:
    if col_type in dataman.embedding_subsets:
        return dataman.embedding_subsets[col_type].tolist()
    return []