
from pydantic import BaseModel

class DataDescription(BaseModel):
    """
    DataDescription model to describe the data structure.
    """
    input_cols: list[str]
    output_cols: list[str]
    num_samples: int
    num_features: int
    num_outputs: int

class DataPoint(BaseModel):
    """
    DataPoint model to represent a single data point.
    """
    inputs: list[float]
    outputs: list[float]
    projected_outputs: list[float] = None
    
