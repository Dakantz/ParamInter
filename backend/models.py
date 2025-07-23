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


class DataPoints(BaseModel):
    """
    DataPoint model to represent a single data point.
    """

    inputs: list[list[float]]
    outputs: list[list[float]]
    projected_outputs: list[list[float]] = None


class DataPoint(BaseModel):
    """
    DataPoint model to represent a single data point.
    """

    inputs: list[float]
    outputs: list[float]
    projected_outputs: list[float] = None
    index: int = None


class InterpolationResult(BaseModel):
    """
    InterpolationResult model to represent the result of interpolation.
    """

    inputs: list[list[float]]
    outputs: list[list[float]]
    projected_outputs: dict[str, list[list[float]]]
    indices: list[int]
