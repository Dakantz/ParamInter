"""Data-generating processes with known heteroscedastic input noise.

Each task provides clean inputs ``x``, the ground-truth per-cell input noise std ``sigma_x``,
the noisy (observed) inputs ``x_noisy = x + sigma_x * eps`` and targets ``y = g*(x)`` computed
from the *clean* inputs, so a model trained on ``(x_noisy, y)`` sees aleatoric output
uncertainty ``sigma_g^2 ~= (grad g*)^2 . sigma_x^2`` (uncertainty propagation).

Synthetic sets follow the ICASSP 2025 SCA paper (polynomial, polynomial-GMM, modified
Styblinski-Tang); ``gas_turbine`` injects the same kind of noise into the real UCI gas turbine
inputs (no analytic g*, so the SCA oracle is unavailable there).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import torch as t


@dataclass
class Split:
    x: np.ndarray  # clean inputs (n, d)
    x_noisy: np.ndarray  # observed inputs (n, d)
    sigma_x: np.ndarray  # ground-truth input noise std (n, d)
    y: np.ndarray  # targets (n,)


@dataclass
class Task:
    name: str
    feature_names: list[str]
    train: Split
    cal: Split
    test: Split
    g_torch: Callable[[t.Tensor], t.Tensor] | None = None  # ground truth g*(x) if known
    meta: dict = field(default_factory=dict)

    @property
    def d(self) -> int:
        return self.train.x.shape[1]

    @property
    def x_std(self) -> np.ndarray:
        s = self.train.x_noisy.std(0)
        s[s == 0] = 1.0
        return s


# ------------------------------------------------------------------- noise model
class HeteroscedasticNoise:
    """sigma_x[i, j] = level * scale * range_j * s_j * (floor + (1-floor) * h_j(x_i)).

    ``s_j`` is 1 for ``n_noisy`` randomly chosen "noisy" features and ``clean_ratio`` for the
    rest; ``h_j`` is a Gaussian bump around a random mode in (min-max normalised) input space,
    which makes the noise depend on the location of the sample (heteroscedastic) and gives
    every sample its own ranking of which inputs are uncertain.
    """

    def __init__(
        self,
        d: int,
        level: float,
        rng: np.random.Generator,
        n_noisy: int | None = None,
        scale: float = 0.1,
        clean_ratio: float = 0.1,
        mode_width: float = 0.35,
        floor: float = 0.05,
    ):
        self.level = level
        self.scale = scale
        self.floor = floor
        self.mode_width = mode_width
        n_noisy = n_noisy if n_noisy is not None else max(1, d // 2)
        self.s = np.full(d, clean_ratio)
        self.s[rng.choice(d, size=n_noisy, replace=False)] = 1.0
        self.modes = rng.uniform(0, 1, size=(d, d))  # one mode (in R^d) per feature

    def fit(self, x: np.ndarray):
        self.lo = x.min(0)
        self.range = x.max(0) - self.lo
        self.range[self.range == 0] = 1.0
        return self

    def sigma(self, x: np.ndarray) -> np.ndarray:
        u = (x - self.lo) / self.range  # (n, d)
        dist2 = ((u[:, None, :] - self.modes[None, :, :]) ** 2).sum(-1)  # (n, d)
        h = np.exp(-0.5 * dist2 / self.mode_width**2)
        return (
            self.level
            * self.scale
            * self.range[None, :]
            * self.s[None, :]
            * (self.floor + (1 - self.floor) * h)
        )


def _make_split(x, y, noise: HeteroscedasticNoise, rng) -> Split:
    sigma = noise.sigma(x)
    x_noisy = x + sigma * rng.standard_normal(x.shape)
    return Split(x=x, x_noisy=x_noisy, sigma_x=sigma, y=y)


def _from_generator(name, feature_names, sample_x, g_torch, level, seed, sizes, n_noisy):
    rng = np.random.default_rng(seed)
    n_total = sum(sizes)
    x = sample_x(rng, n_total)
    with t.no_grad():
        y = g_torch(t.tensor(x, dtype=t.float64)).numpy()
    noise = HeteroscedasticNoise(x.shape[1], level, rng, n_noisy=n_noisy).fit(x)
    a, b = sizes[0], sizes[0] + sizes[1]
    return Task(
        name=name,
        feature_names=feature_names,
        train=_make_split(x[:a], y[:a], noise, rng),
        cal=_make_split(x[a:b], y[a:b], noise, rng),
        test=_make_split(x[b:], y[b:], noise, rng),
        g_torch=g_torch,
        meta={"noise_level": level, "seed": seed, "noisy_features": noise.s.tolist()},
    )


def polynomial(level, seed, sizes=(5000, 500, 500), gmm=False, **_):
    rng = np.random.default_rng(seed + 10_000)
    k = t.tensor(rng.uniform(0, 1, 6))

    def g(x):
        x1, x2 = x[:, 0], x[:, 1]
        return k[0] * x1**2 + k[1] * x2**2 + k[2] * x1 * x2 + k[3] * x1 + k[4] * x2 + k[5]

    if gmm:
        centers = rng.uniform(-4, 2, size=(2, 2))  # (component, dim)

        def sample(r, n):
            comp = r.integers(0, 2, size=(n, 2))
            return centers[comp, np.arange(2)[None, :]] + 0.7 * r.standard_normal((n, 2))

    else:

        def sample(r, n):
            return r.uniform(-5, 2, size=(n, 2))

    name = "polynomial_gmm" if gmm else "polynomial"
    return _from_generator(name, ["x1", "x2"], sample, g, level, seed, sizes, n_noisy=1)


def styblinski_tang(level, seed, d=4, sizes=(5000, 500, 500), **_):
    rng = np.random.default_rng(seed + 20_000)
    k = t.tensor(rng.uniform(0, 1, d))

    def g(x):
        return 0.5 * (k * (x**4 - 16 * x**2 + 5 * x)).sum(-1)

    def sample(r, n):
        return r.uniform(-5, 5, size=(n, d))

    return _from_generator(
        f"styblinski_tang_d{d}",
        [f"x{j + 1}" for j in range(d)],
        sample,
        g,
        level,
        seed,
        sizes,
        n_noisy=max(1, d // 2),
    )


def gas_turbine(level, seed, sizes=(5000, 500, 500), target="NOX", **_):
    """Real industrial inputs (UCI id 551) with injected heteroscedastic noise. ``y`` is the
    *measured* emission, so g* is unknown (no oracle) and the real inputs' own noise adds to the
    simulated one - the ranking is still dominated by the injected noise."""
    path = Path(os.getenv("DATA_DIR", "./data")) / "datasets/gas_turbine/gas_turbine.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} missing, run scripts/prepare_gas_turbine.py first")
    df = pd.read_csv(path)
    inputs = ["AT", "AP", "AH", "AFDP", "GTEP", "TIT", "TAT", "TEY", "CDP"]
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(df), size=sum(sizes), replace=False)
    x = df[inputs].values[idx].astype(np.float64)
    y = df[target].values[idx].astype(np.float64)
    noise = HeteroscedasticNoise(x.shape[1], level, rng).fit(x)
    a, b = sizes[0], sizes[0] + sizes[1]
    return Task(
        name=f"gas_turbine_{target.lower()}",
        feature_names=inputs,
        train=_make_split(x[:a], y[:a], noise, rng),
        cal=_make_split(x[a:b], y[a:b], noise, rng),
        test=_make_split(x[b:], y[b:], noise, rng),
        g_torch=None,
        meta={"noise_level": level, "seed": seed, "noisy_features": noise.s.tolist()},
    )


def make_task(spec: str, level: float, seed: int, **kw) -> Task:
    """``spec`` examples: polynomial, polynomial_gmm, styblinski_tang:8, gas_turbine,
    gas_turbine:CO"""
    name, _, arg = spec.partition(":")
    if name == "polynomial":
        return polynomial(level, seed, **kw)
    if name == "polynomial_gmm":
        return polynomial(level, seed, gmm=True, **kw)
    if name == "styblinski_tang":
        return styblinski_tang(level, seed, d=int(arg or 4), **kw)
    if name == "gas_turbine":
        return gas_turbine(level, seed, target=arg or "NOX", **kw)
    raise ValueError(f"unknown dataset {spec}")
