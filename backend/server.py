import pandas as pd
import torch as t
import torch.nn as nn
import torch.optim as optim
import numpy as np
from fastapi import FastAPI

import umap
import lightgbm as lgb

from models import DataDescription, DataPoints, DataPoint

data = pd.read_table("./alloy_data.txt")
input_cols = data.columns.to_list()[:6]
output_cols = data.columns.to_list()[6:70]

app = FastAPI()


embedding_model = umap.UMAP(
    n_neighbors=15, n_components=2, min_dist=0.1, metric="euclidean", random_state=42
)
embedding_model.fit(data[output_cols].values)
embedded_data = embedding_model.transform(data[output_cols].values)


@app.get("/data_description", response_model=DataDescription)
def get_data_description():
    return DataDescription(
        input_cols=input_cols,
        output_cols=output_cols,
        num_samples=len(data),
        num_features=len(input_cols),
        num_outputs=len(output_cols),
    )


@app.get("/data")
def get_data():
    data_points = DataPoints(
        inputs=data[input_cols].values.tolist(),
        outputs=data[output_cols].values.tolist(),
        projected_outputs=embedded_data.tolist(),
    )
    return data_points
