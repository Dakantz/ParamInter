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


class DataSample(BaseModel):
    """
    A random sample of raw input rows (indices into the dataset), for client-side plots that
    need real rows without paying for the full dataset (which also carries every output column).
    """

    indices: list[int]
    inputs: list[list[float]]


class HistogramData(BaseModel):
    bins: list[float]
    counts: list[int]
    relative: list[float]


class DataPoint(BaseModel):
    """
    DataPoint model to represent a single data point.
    """

    inputs: list[float]
    outputs: list[float]
    projected_outputs: list[float] = None
    uncertainties: list[float] = None
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
    uncertainties: list[list[float]] = None


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


class FilterCondition(BaseModel):
    name: str
    min: float = None
    max: float = None


class DataPointMinimzer(BaseModel):
    targets: list[LinearTarget] = []
    filters: list[FilterCondition] = []


class CostOverview(BaseModel):
    costs: list[float]
    within_filter: list[bool]


class DataPointMinimzerInterpolation(BaseModel):
    min: DataPointMinimzer
    start_idx: int
    samples: int = 256
    div_penalty: float = 0.25
    cost_penalty: float = 0.25
    k_options: int = 3


class DataPointSuggestions(BaseModel):
    base_index: int = None
    values: list[float] = []
    k: int = 5
    weigh_changes: float = 1.5


class EffectsRequest(BaseModel):
    output_col: str
    max_samples: int = 200
    seed: int = 0


class BeeswarmResult(BaseModel):
    """
    Per-feature SHAP values (first order) for a sample of the dataset, for one output column.
    """

    output_col: str
    features: list[str]
    indices: list[int]
    shap_values: dict[str, list[float]]
    feature_values: dict[str, list[float]]
    base_value: float


class InteractionRequest(BaseModel):
    output_col: str
    features: list[str] = []  # candidate pool to search within; empty = every input column
    order: int = 2
    top_k: int = 10
    max_samples: int = 200
    n_permutations: int = 64
    seed: int = 0


class InteractionForRowsRequest(BaseModel):
    output_col: str
    features: list[str] = []  # candidate pool to search within; empty = every input column
    order: int = 2
    top_k: int = 10
    inputs: list[list[float]]
    n_permutations: int = 64
    seed: int = 0


class InteractionCombo(BaseModel):
    features: list[str]
    mean_abs: float
    values: list[float]


class InteractionResult(BaseModel):
    """
    The top `top_k` combinations of size `order`, drawn from a candidate feature pool and ranked
    by mean |Shapley interaction value|, evaluated over either a sample of the dataset or
    caller-supplied rows: order 1 is the plain SHAP value, order 2 the pairwise SHAP interaction
    value (both exact, from a single TreeSHAP call covering every combination at once), and
    order >= 3 a Monte-Carlo estimate of the generalized Shapley interaction index per combination.
    """

    output_col: str
    order: int
    indices: list[int] = []
    combinations: list[InteractionCombo]
    feature_values: dict[str, list[float]]


class InteractionBackgroundRequest(BaseModel):
    output_col: str
    var1: str
    var2: str
    resolution: int = 40
    k_neighbors: int = 5


class InteractionBackgroundResult(BaseModel):
    """
    A `resolution` x `resolution` heatmap over the (var1, var2) plane, meant as a background layer
    behind a scatterplot of those two variables: each grid cell's full input vector is an
    inverse-distance-weighted average of its `k_neighbors` nearest dataset rows in the (var1, var2)
    subspace, then run through the output model and the SHAP explainer - giving a smooth
    interpolated view of both the model's output and its overall SHAP attribution strength in
    regions between real samples. See hilti_exp.py's "Nearest Neighbors for Interpolated Inputs +
    Output views" section for the exploratory version this is based on.
    """

    output_col: str
    var1: str
    var2: str
    x: list[float]
    y: list[float]
    predictions: list[list[float]]  # [len(y)][len(x)]
    shap_effect: list[list[float]]  # [len(y)][len(x)], sum |SHAP value| across all inputs


class ManagerSettings(BaseModel):
    data_description: DataDescription
    mode: str = "tsne"
    data_name: str = "Aloy Data"
    short_data_name: str = "scivis"
    input_cols: int = 6
    output_cols: int = 64
    time_col: int | None = None
    inputs_constrained: bool = True
    col_defs: dict[str, list[str]] = {}
    loaded: bool = False
    use_ucq: bool = False
