import os
import typing
from dataclasses import dataclass, field
from enum import Enum

from ucq.models import GP_VAE, VAE, BaseUCQModel, RandomBaseline


class VAEOptions(str, Enum):
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
    modes: list[str] | str = field(default_factory=lambda: ["tsne", "pca", "umap"])
    data_file: str = "scivis/alloy_data.txt"
    data_name: str = "Alloy Simulation Data (SciVis Contest 2025)"
    short_data_name: str = "scivis"
    input_cols: int = 6
    output_cols: int = 64
    time_col: int | None = None
    inputs_constrained: bool = True
    is_config: bool = True
    use_ucq: bool = False
    vae_mode: VAEOptions = VAEOptions.m_GPVAE
    # training epochs + extra constructor kwargs for the UCQ model (e.g. latent_size,
    # gp_latent_size, n_inducing); latent_size defaults to sqrt(#columns)
    ucq_epochs: int = 3
    ucq_model_kwargs: dict = field(default_factory=dict)

    def __post_init__(self):
        self.vae_mode = VAEOptions(self.vae_mode)
        if isinstance(self.modes, str):
            self.modes = [self.modes]
