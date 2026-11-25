"""Conditional prediction with a trained GP-VAE.

Given a subset of columns fixed to a value (or a range), predict the distribution of all other
columns. The GP-VAE (``ucq.models.GP_VAE``) maps a VAE latent ``z`` to a multitask Gaussian over
*all* columns, ``p(x | z) = N(m(z), C(z))`` where ``C(z)`` carries the LMC cross-column
covariance plus the per-column likelihood noise. We approximate the latent prior with a bank of
encoded training rows ``{z_k}`` (the aggregate posterior) and obtain

    p(x | x_o ~= v) ~= sum_k w_k N(x | m_k|o, C_k|o),   w_k  propto  N(v | m_k,o, C_k,oo + R)

i.e. a Gaussian mixture whose components are Gaussian-conditioned on the observed columns.
Range conditions ``[a, b]`` are moment-matched to an observation ``v = (a+b)/2`` with extra
observation variance ``R = (b-a)^2 / 12`` (variance of the uniform), point conditions use a tiny
jitter. Because every bank component is precomputed once, conditioning on any subset is a few
batched ``(K, T, T)`` linear-algebra ops and is fast enough for interactive use.

If the likelihoods collapse onto very few components (effective sample size below
``min_ess``) the weights are tempered (``w propto lik^beta``, ``beta`` found by bisection) to keep
the mixture from becoming over-confident - the GP likelihood is usually sharper than the
coarse latent bank warrants.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import torch as t

from ucq.models.gp_vae import GP_VAE


@dataclass
class Condition:
    column: str
    value: float
    width: float = 0.0  # 0 = point condition, otherwise full width of the range


def _ess(w: t.Tensor) -> float:
    return float(1.0 / (w**2).sum())


class GPVAEConditioner:
    def __init__(
        self,
        model: GP_VAE,
        data: pd.DataFrame,
        bank_size: int = 3000,
        batch_size: int = 64,
        seed: int = 0,
        point_jitter: float = 1e-6,
        min_ess: float = 16.0,
    ):
        self.model = model
        self.columns = list(data.columns)
        self.T = len(self.columns)
        self.mins = data.min().values.astype(np.float64)
        diff = (data.max() - data.min()).values.astype(np.float64)
        maxs = data.max().values.astype(np.float64)
        diff[diff == 0] = maxs[diff == 0]
        diff[diff == 0] = 1.0
        self.diff = diff
        self.point_jitter = point_jitter
        self.min_ess = min_ess
        self.data_mean = data.mean().values.astype(np.float64)
        self.data_std = data.std().values.astype(np.float64)

        normed = (data.values.astype(np.float64) - self.mins) / self.diff
        rng = np.random.default_rng(seed)
        idx = rng.choice(len(normed), size=min(bank_size, len(normed)), replace=False)
        self.bank_rows = np.sort(idx)
        self._build_bank(t.tensor(normed[self.bank_rows], dtype=t.float32), batch_size)

    # ------------------------------------------------------------------ bank
    @t.no_grad()
    def _build_bank(self, x: t.Tensor, batch_size: int):
        model = self.model
        model.eval()
        dev = next(model.vae_model.parameters()).device
        means, covs = [], []
        T = self.T
        for start in range(0, len(x), batch_size):
            xb = x[start : start + batch_size].to(dev)
            _, mu, _ = model.vae_model.encode(xb)
            dist = model.likelihood(model.gp(mu.to(t.float32)))
            B = xb.shape[0]
            m = dist.mean.reshape(B, T)
            full = dist.covariance_matrix  # (B*T, B*T)
            if getattr(dist, "_interleaved", True):
                # index n*T + t
                blocks = full.reshape(B, T, B, T)
                c = blocks[t.arange(B), :, t.arange(B), :]
            else:
                # index t*B + n
                blocks = full.reshape(T, B, T, B)
                c = blocks[:, t.arange(B), :, t.arange(B)]  # advanced idx first -> (B,T,T)
            means.append(m.double().cpu())
            covs.append(c.double().cpu())
        self.bank_mean = t.cat(means)  # (K, T)  normalised space
        cov = t.cat(covs)  # (K, T, T)
        cov = 0.5 * (cov + cov.transpose(1, 2))
        self.bank_cov = cov + 1e-6 * t.eye(T, dtype=cov.dtype)

    # ------------------------------------------------------------ inference
    def _normalise_conditions(self, conditions: list[Condition]):
        obs_idx, v, r = [], [], []
        for c in conditions:
            if c.column not in self.columns:
                raise KeyError(f"Unknown column {c.column}")
            j = self.columns.index(c.column)
            if j in obs_idx:
                continue
            obs_idx.append(j)
            v.append((c.value - self.mins[j]) / self.diff[j])
            w = abs(c.width) / self.diff[j]
            r.append(w**2 / 12.0 + self.point_jitter)
        return obs_idx, t.tensor(v, dtype=t.float64), t.tensor(r, dtype=t.float64)

    def _temper(self, loglik: t.Tensor) -> tuple[t.Tensor, float]:
        w = t.softmax(loglik, 0)
        if _ess(w) >= self.min_ess or len(w) <= self.min_ess:
            return w, 1.0
        lo, hi = 0.0, 1.0
        for _ in range(30):
            mid = 0.5 * (lo + hi)
            if _ess(t.softmax(loglik * mid, 0)) >= self.min_ess:
                lo = mid
            else:
                hi = mid
        return t.softmax(loglik * lo, 0), lo

    def mixture(self, conditions: list[Condition]):
        """Posterior mixture in normalised space: weights (K,), means (K,T), covs (K,T,T)."""
        m, C = self.bank_mean, self.bank_cov
        K = m.shape[0]
        if not conditions:
            return t.full((K,), 1.0 / K, dtype=t.float64), m, C, 1.0
        o, v, r = self._normalise_conditions(conditions)
        o_t = t.tensor(o)
        S = C[:, o_t][:, :, o_t] + t.diag_embed(r).unsqueeze(0)  # (K, o, o)
        L = t.linalg.cholesky(S)
        resid = (v.unsqueeze(0) - m[:, o_t]).unsqueeze(-1)  # (K, o, 1)
        alpha = t.cholesky_solve(resid, L)  # S^-1 (v - m_o)
        logdet = 2 * t.log(t.diagonal(L, dim1=1, dim2=2)).sum(-1)
        maha = (resid * alpha).sum((1, 2))
        loglik = -0.5 * (maha + logdet + len(o) * np.log(2 * np.pi))
        w, beta = self._temper(loglik)

        Kxo = C[:, :, o_t]  # (K, T, o)
        post_mean = m + (Kxo @ alpha).squeeze(-1)
        post_cov = C - Kxo @ t.cholesky_solve(Kxo.transpose(1, 2), L)
        post_cov = 0.5 * (post_cov + post_cov.transpose(1, 2))
        return w, post_mean, post_cov, beta

    @staticmethod
    def _moments(w, means, covs):
        mean = (w[:, None] * means).sum(0)
        second = (w[:, None, None] * (covs + means[:, :, None] * means[:, None, :])).sum(0)
        cov = second - mean[:, None] * mean[None, :]
        return mean, 0.5 * (cov + cov.T)

    def predict(
        self,
        conditions: list[Condition],
        n_samples: int = 64,
        grid_points: int = 80,
        seed: int = 0,
    ) -> dict:
        w, means, covs, beta = self.mixture(conditions)
        mean_n, cov_n = self._moments(w, means, covs)

        # prior (unconditioned) model spread, used to normalise the uncertainty for display
        w0 = t.full((len(self.bank_mean),), 1.0 / len(self.bank_mean), dtype=t.float64)
        _, prior_cov_n = self._moments(w0, self.bank_mean, self.bank_cov)

        diff = t.tensor(self.diff)
        mins = t.tensor(self.mins)
        mean = mean_n * diff + mins
        cov = cov_n * diff[:, None] * diff[None, :]
        std = t.sqrt(t.clamp(t.diagonal(cov), min=0))
        prior_std = t.sqrt(t.clamp(t.diagonal(prior_cov_n), min=0)) * diff
        d = t.clamp(std, min=1e-12)
        corr = cov / (d[:, None] * d[None, :])

        # samples from the mixture (denormalised)
        g = t.Generator().manual_seed(seed)
        comp = t.multinomial(w, n_samples, replacement=True, generator=g)
        Lc = t.linalg.cholesky(covs[comp] + 1e-7 * t.eye(self.T, dtype=t.float64))
        eps = t.randn(n_samples, self.T, 1, generator=g, dtype=t.float64)
        samples_n = means[comp] + (Lc @ eps).squeeze(-1)
        samples = samples_n * diff + mins

        # per column marginal density on a grid (mixture of 1D Gaussians)
        lo = mins - 0.05 * diff
        hi = mins + 1.05 * diff
        grid = lo[:, None] + (hi - lo)[:, None] * t.linspace(0, 1, grid_points, dtype=t.float64)
        mu_c = means * diff + mins  # (K, T)
        sd_c = t.sqrt(t.clamp(t.diagonal(covs, dim1=1, dim2=2), min=1e-12)) * diff  # (K,T)
        z = (grid[None, :, :] - mu_c[:, :, None]) / sd_c[:, :, None]  # (K,T,G)
        pdf = t.exp(-0.5 * z**2) / (sd_c[:, :, None] * np.sqrt(2 * np.pi))
        density = (w[:, None, None] * pdf).sum(0)  # (T, G)

        return {
            "columns": self.columns,
            "conditioned": [c.column for c in conditions],
            "mean": mean.tolist(),
            "std": std.tolist(),
            "prior_std": prior_std.tolist(),
            "data_mean": self.data_mean.tolist(),
            "data_std": self.data_std.tolist(),
            "correlation": corr.tolist(),
            "samples": samples.tolist(),
            "grid": grid.tolist(),
            "density": density.tolist(),
            "ess": _ess(w),
            "temperature": beta,
        }
