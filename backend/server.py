import pandas as pd
import numpy as np
from fastapi import Body, FastAPI

# cors
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from sklearn.preprocessing import MinMaxScaler, StandardScaler

from backend.models import DataPointSensitivity

from .models import (
    DataDescription,
    DataPoints,
    DataPoint,
    InterpolationResult,
    SensitivityAnalysisResult,
)
from .routers import data_router, dp_router


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data_router)
app.include_router(dp_router)