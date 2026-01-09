from pydantic import BaseModel


class DataDescription(BaseModel):
    """
    DataDescription model to describe the data structure.
    """

    input_cols: list[str]
    output_cols: list[str]
    all_columns: list[str]
    num_samples: int
    num_features: int
    num_outputs: int

    min_values: dict[str, float]
    max_values: dict[str, float]
    mean_values: dict[str, float]
    std_values: dict[str, float]
    inputs_constrained: bool = True


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


class SensitivityAnalysisResult(BaseModel):
    """
    SensitivityAnalysisResult model to represent the result of sensitivity analysis.
    """

    dp: DataPoint
    sensitivity_scores: list[float]
    out_col: str


class InterpolationResult(BaseModel):
    """
    InterpolationResult model to represent the result of interpolation.
    """

    inputs: list[list[float]]
    outputs: list[list[float]]
    knn_inputs: list[list[float]]
    knn_outputs: list[list[float]]
    projected_outputs: dict[str, list[list[float]]]
    indices: list[int]
    explainations: list[list[float]] = None


class DataPointSensitivity(BaseModel):
    for_outputs: list[str] = []
    resolution: int = 16


class DataPointSimilarity(BaseModel):
    values: list[float]
    k: int


class LinearTarget(BaseModel):
    name: str
    weight: float
    val: float


class DataPointMinimzer(BaseModel):
    targets: list[LinearTarget] = []


class DataPointMinimzerInterpolation(BaseModel):
    min: DataPointMinimzer
    start_idx: int
    samples: int = 256
    div_penalty: float = 0.25
    cost_penalty: float = 0.25


class DataPointSuggestions(BaseModel):
    base_index: int = None
    values: list[float] = []
    k: int = 5
    weigh_changes: float = 1.5
