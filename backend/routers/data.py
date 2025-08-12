

from fastapi import APIRouter, Depends

from backend.dataman import DATAMAN
from backend.models import DataDescription, DataPoints
data_router = APIRouter(prefix='/data')

@data_router.get("/description", response_model=DataDescription)
def get_data_description():
    return DataDescription(
        input_cols=DATAMAN.input_cols,
        output_cols=DATAMAN.output_cols,
        num_samples=len(DATAMAN.data),
        num_features=len(DATAMAN.input_cols),
        num_outputs=len(DATAMAN.output_cols),
        min_values=DATAMAN.cleaned[DATAMAN.output_cols].min().to_dict(),
        max_values=DATAMAN.cleaned[DATAMAN.output_cols].max().to_dict(),
        mean_values=DATAMAN.cleaned[DATAMAN.output_cols].mean().to_dict(),
        std_values=DATAMAN.cleaned[DATAMAN.output_cols].std().to_dict(),
    )


@data_router.get("/")
def get_data() -> DataPoints:
    data_points = DataPoints(
        inputs=DATAMAN.cleaned[DATAMAN.input_cols].values.tolist(),
        outputs=DATAMAN.cleaned[DATAMAN.output_cols].values.tolist(),
        projected_outputs=DATAMAN.embedded_tsne.tolist(),
    )
    return data_points


@data_router.get("/column_types")
def get_column_types() -> dict[str, list[str]]:
    return DATAMAN.column_types



@data_router.get("/embedding/{col_type}")
def get_embedding(col_type: str) -> list[list[float]]:
    if col_type in DATAMAN.embedding_subsets:
        return DATAMAN.embedding_subsets[col_type].tolist()
    return []