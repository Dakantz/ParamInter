from dataclasses import dataclass
import os


@dataclass
class DataConfig:
    base_dir: str = os.getenv("DATA_DIR", "./data")
    mode: str = "tsne"
    data_file: str = "scivis/alloy_data.txt"
    data_name: str = "Alloy Simulation Data (SciVis Contest 2025)"
    short_data_name: str = "scivis"
    input_cols: int = 6
    output_cols: int = 64
    time_col: int | None = None
    inputs_constrained: bool = True
    is_config: bool = True
