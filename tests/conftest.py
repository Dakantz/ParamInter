"""Shared fixtures. Nothing here needs the cached gas_turbine model or any dataset on disk:
the backend's module-level ``sets_manager`` is pointed at an empty config before ``backend`` is
imported, and the GP-VAE is a tiny model trained on a synthetic table."""

import json
import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import torch as t

_empty_cfg = Path(tempfile.mkdtemp()) / "empty_sets.json"
_empty_cfg.write_text(json.dumps({}))
os.environ["SETS_CONFIG_JSON"] = str(_empty_cfg)


@pytest.fixture(scope="session")
def synthetic_df() -> pd.DataFrame:
    """300 rows: b, c strongly (linearly) depend on a; d is independent."""
    rng = np.random.default_rng(0)
    n = 300
    a = rng.uniform(0, 10, n)
    b = 2 * a + rng.normal(0, 0.3, n)
    c = b - 0.5 * a + rng.normal(0, 0.3, n)
    d = rng.uniform(-1, 1, n)
    return pd.DataFrame(dict(a=a, b=b, c=c, d=d))


@pytest.fixture(scope="session")
def tiny_gpvae(synthetic_df):
    from ucq.models.gp_vae import GP_VAE
    from ucq.utils import train_vae_noiseless

    t.manual_seed(0)
    return train_vae_noiseless(
        synthetic_df,
        GP_VAE,
        epochs=25,
        model_kwargs=dict(latent_size=2, n_inducing=32),
        device="cpu",
    )


@pytest.fixture(scope="session")
def conditioner(tiny_gpvae, synthetic_df):
    from ucq.conditioning import GPVAEConditioner

    return GPVAEConditioner(tiny_gpvae, synthetic_df, bank_size=200, min_ess=4)
