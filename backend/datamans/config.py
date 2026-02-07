from dataclasses import dataclass
import os
from enum import Enum
from ucq.models import RandomBaseline, GP_VAE, VAE, BaseUCQModel
import typing


class VAEOptions(Enum):
    m_GPVAE = "gpvae"
    m_VAE = "vae"

    def toClass(self) -> BaseUCQModel.__class__:
        if self == VAEOptions.m_GPVAE:
            return GP_VAE
        if self == VAEOptions.m_VAE:
            return VAE


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
    vae_mode: VAEOptions = VAEOptions.m_VAE
