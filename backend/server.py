import pandas as pd
import torch as t
import torch.nn as nn
import torch.optim as optim
import numpy as np
from fastapi import FastAPI

from models import DataDescription

data = pd.read_table("./alloy_data.txt")
input_cols= data.columns.to_list()[:6]
output_cols= data.columns.to_list()[6:70]

app = FastAPI()

@app.get("/data_description", response_model=DataDescription)
def get_data_description():
    return DataDescription(
        input_cols=input_cols,
        output_cols=output_cols,
        num_samples=len(data),
        num_features=len(input_cols),
        num_outputs=len(output_cols)
    )   