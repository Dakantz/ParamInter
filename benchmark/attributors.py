"""Input uncertainty attribution mechanisms (iUCAMs).

Every attributor returns a non-negative ``(n_test, d)`` array of per-feature input uncertainty
scores in *standardised* input units (std of the noisy training inputs), so features with
different physical scales are comparable for ranking. ``calibrated`` marks attributors whose
scores are estimates of sigma_x itself (and are therefore also scored with s_l2 = MSE).

Implemented
-----------
* ``SCA``          Smoothness Constrained Attribution (Kantz et al., ICASSP 2025) on top of the
                   shallow heteroscedastic NN: SmoothGrad input gradients Phi(g, x_h) over a
                   neighbourhood {x_h} (Gaussian samples around x or kNN), output variances
                   sigma_g^2(x_h) from the calibrated UQ model, and inversion of the uncertainty
                   propagation sigma_g^2 = (Phi^2)^T sigma_x^2 with an l2-regularised least squares
                   a = sqrt((B^T B + lambda I)^-1 B^T s).
* ``SCAOracle``    SCA with the true gradient of g* and the true propagated output variance (no
                   ML model) - upper reference, only on synthetic tasks.
* ``GradientUA``   XAI baseline: |SmoothGrad of the predicted std| (gradient-based uncertainty
                   attribution, Wang et al. CVPR 2023).
* ``ShapUA``       XAI baseline: |SHAP values| of the predicted std (Iversen et al. 2024).
* ``VAEUA`` / ``GPVAEUA``  The app's UCQ models (ucq/models): trained on the joint table
                   [x_noisy, y] and read out per-cell reconstruction uncertainty for the inputs.
* ``GPVAECondUA``  GP-VAE + ucq/conditioning.py: posterior std of x_j given all other columns.
* ``Predict0`` / ``RandomUA``  worst-case / chance baselines.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import torch as t

from benchmark.datasets import Task
from benchmark.uq_models import UQModel


class Attributor:
    name = "base"
    calibrated = False
    needs_oracle = False

    def attribute(self, task: Task, uq: UQModel) -> np.ndarray:
        raise NotImplementedError


# ------------------------------------------------------------------ helpers
def smoothgrad(fn, z: t.Tensor, sigma: float, n_samples: int, seed: int = 0) -> t.Tensor:
    """SmoothGrad of scalar fn over points z (..., d): mean_m grad fn(z + sigma * eps_m)."""
    g = t.Generator().manual_seed(seed)
    eps = t.randn(n_samples, *z.shape, generator=g) * sigma
    zs = (z.unsqueeze(0) + eps).detach().requires_grad_(True)
    out = fn(zs.reshape(-1, z.shape[-1])).sum()
    (grad,) = t.autograd.grad(out, zs)
    return grad.mean(0)


def sca_solve(B: t.Tensor, s: t.Tensor, lam: float) -> t.Tensor:
    """Batched SCA inversion. B: (n, K, d) squared gradients, s: (n, K) output variances.
    Returns sigma_x (n, d) = sqrt(max(0, (B^T B + lam' I)^-1 B^T s)), lam' relative to the
    mean diagonal of B^T B so lambda is scale free."""
    BtB = B.transpose(1, 2) @ B
    d = BtB.shape[-1]
    scale = t.diagonal(BtB, dim1=1, dim2=2).mean(-1).clamp(min=1e-12)
    reg = lam * scale[:, None, None] * t.eye(d, dtype=B.dtype)
    var = t.linalg.solve(BtB + reg, (B.transpose(1, 2) @ s.unsqueeze(-1))).squeeze(-1)
    return var.clamp(min=0).sqrt()


def knn_indices(query: np.ndarray, pool: np.ndarray, k: int) -> np.ndarray:
    from sklearn.neighbors import NearestNeighbors

    return NearestNeighbors(n_neighbors=k).fit(pool).kneighbors(query)[1]


# --------------------------------------------------------------- attributors
class SCA(Attributor):
    calibrated = True

    def __init__(
        self,
        neighborhood: str = "gaussian",
        k: int | None = None,
        sigma_s: float = 0.1,
        sg_sigma: float = 0.1,
        sg_samples: int = 16,
        lam: float = 1e-2,
        seed: int = 0,
    ):
        self.neighborhood, self.k, self.sigma_s = neighborhood, k, sigma_s
        self.sg_sigma, self.sg_samples, self.lam, self.seed = sg_sigma, sg_samples, lam, seed
        self.name = f"SCA {'Gaussian' if neighborhood == 'gaussian' else 'kNN'} (NN+SG)"

    def neighbours(self, task: Task, uq: UQModel, z: t.Tensor) -> t.Tensor:
        K = self.k or max(task.d**2, task.d + 1)
        if self.neighborhood == "gaussian":
            g = t.Generator().manual_seed(self.seed + 1)
            eps = t.randn(z.shape[0], K, z.shape[1], generator=g) * self.sigma_s
            eps[:, 0] = 0  # keep the test sample itself
            return z[:, None, :] + eps
        pool = uq.to_z(task.train.x_noisy)
        idx = knn_indices(z.numpy(), pool.numpy(), K - 1)
        return t.cat([z[:, None, :], pool[idx]], 1)

    def attribute(self, task, uq):
        z = uq.to_z(task.test.x_noisy)
        zh = self.neighbours(task, uq, z)  # (n, K, d)
        phi = smoothgrad(uq.mean_z, zh, self.sg_sigma, self.sg_samples, self.seed)
        with t.no_grad():
            s = uq.std_z(zh.reshape(-1, z.shape[1])).reshape(zh.shape[:2]) ** 2
        return sca_solve(phi.double() ** 2, s.double(), self.lam).numpy()


class SCAOracle(Attributor):
    """Reference: true gradients + true propagated output variance at the kNN neighbours."""

    name = "SCA Oracle"
    calibrated = True
    needs_oracle = True

    def __init__(self, k: int | None = None, lam: float = 1e-2):
        self.k, self.lam = k, lam

    def attribute(self, task, uq):
        sd_x = task.x_std
        K = self.k or max(task.d**2, task.d + 1)
        pool_x = np.concatenate([task.train.x, task.test.x])
        pool_sigma = np.concatenate([task.train.sigma_x, task.test.sigma_x])
        idx = knn_indices(task.test.x / sd_x, pool_x / sd_x, K)  # includes the sample itself
        xh = t.tensor(pool_x[idx], dtype=t.float64).requires_grad_(True)
        (grad,) = t.autograd.grad(task.g_torch(xh.reshape(-1, task.d)).sum(), xh)
        grad_z = grad * t.tensor(sd_x)  # d g / d z
        sig_z = t.tensor(pool_sigma[idx] / sd_x)
        B = grad_z**2
        s = (B * sig_z**2).sum(-1)
        return sca_solve(B, s, self.lam).numpy()


class GradientUA(Attributor):
    name = "Gradient-based (SG on sigma)"

    def __init__(self, sg_sigma=0.1, sg_samples=32, seed=0):
        self.sg_sigma, self.sg_samples, self.seed = sg_sigma, sg_samples, seed

    def attribute(self, task, uq):
        z = uq.to_z(task.test.x_noisy)
        return smoothgrad(uq.std_z, z, self.sg_sigma, self.sg_samples, self.seed).abs().numpy()


class ShapUA(Attributor):
    name = "SHAP on sigma"

    def __init__(self, n_background=50, max_test=None, seed=0):
        self.n_background, self.max_test, self.seed = n_background, max_test, seed

    def attribute(self, task, uq):
        import shap

        rng = np.random.default_rng(self.seed)
        zb = uq.to_z(task.train.x_noisy).numpy()
        bg = zb[rng.choice(len(zb), self.n_background, replace=False)]
        z = uq.to_z(task.test.x_noisy).numpy()

        def f(a):
            with t.no_grad():
                return uq.std_z(t.tensor(a, dtype=t.float32)).numpy()

        explainer = shap.PermutationExplainer(f, bg)
        vals = explainer(z, max_evals=2 * task.d + 1, silent=True).values
        return np.abs(vals)


class _JointUCQ(Attributor):
    """Shared plumbing for the app's UCQ models on the joint [x_noisy, y] table."""

    calibrated = True
    model_cls = None

    def __init__(self, epochs=10, seed=0, **model_kwargs):
        self.epochs, self.seed, self.model_kwargs = epochs, seed, model_kwargs

    def _table(self, split):
        return pd.DataFrame(np.column_stack([split.x_noisy, split.y]))

    def fit_model(self, task):
        from ucq.utils import train_vae_noiseless

        t.manual_seed(self.seed)
        train = self._table(task.train)
        T = train.shape[1]
        latent = max(2, int(np.ceil(np.sqrt(T))))
        kw = {"latent_size": latent}
        if self.model_cls.__name__ == "GP_VAE":
            kw.update(gp_latent_size=latent, n_inducing=128)
        kw.update(self.model_kwargs)
        model = train_vae_noiseless(
            train, self.model_cls, epochs=self.epochs, model_kwargs=kw, device="cpu"
        )
        self.lo = train.min().values
        diff = (train.max() - train.min()).values.copy()
        diff[diff == 0] = 1
        self.diff = diff
        return model, train

    def normed_test(self, task):
        test = self._table(task.test).values
        return t.tensor((test - self.lo) / self.diff, dtype=t.float32)

    def attribute(self, task, uq):
        model, _ = self.fit_model(task)
        with t.no_grad():
            u = model.uncertainty(self.normed_test(task)).numpy()
        return u[:, : task.d] * self.diff[: task.d] / task.x_std


class VAEUA(_JointUCQ):
    name = "VAE (UCQ)"

    @property
    def model_cls(self):
        from ucq.models import VAE

        return VAE


class GPVAEUA(_JointUCQ):
    name = "GP-VAE (UCQ)"

    @property
    def model_cls(self):
        from ucq.models import GP_VAE

        return GP_VAE


class GPVAECondUA(GPVAEUA):
    """Posterior std of each input given all other columns (inputs + y), from the GP-VAE
    mixture conditioner used by the app's conditioning view."""

    name = "GP-VAE leave-one-out cond."

    def __init__(self, bank_size=400, **kw):
        super().__init__(**kw)
        self.bank_size = bank_size

    def attribute(self, task, uq):
        from ucq.conditioning import GPVAEConditioner

        model, train = self.fit_model(task)
        cond = GPVAEConditioner(model, train, bank_size=self.bank_size, min_ess=4)
        x = self.normed_test(task).double()  # same normalisation as the conditioner
        n, T = x.shape
        m, C = cond.bank_mean, cond.bank_cov
        out = np.zeros((n, task.d))
        r = cond.point_jitter
        for j in range(task.d):
            o = t.tensor([i for i in range(T) if i != j])
            S = C[:, o][:, :, o] + r * t.eye(len(o), dtype=C.dtype)  # (K, o, o)
            L = t.linalg.cholesky(S)
            resid = (x[:, None, o] - m[None, :, o]).unsqueeze(-1)  # (n, K, o, 1)
            alpha = t.cholesky_solve(resid, L.unsqueeze(0))
            logdet = 2 * t.log(t.diagonal(L, dim1=1, dim2=2)).sum(-1)
            loglik = -0.5 * ((resid * alpha).sum((2, 3)) + logdet[None])  # (n, K)
            k_jo = C[:, j, o].unsqueeze(-1)  # (K, o, 1)
            mu = m[None, :, j] + (k_jo.transpose(1, 2).unsqueeze(0) @ alpha).squeeze(-1).squeeze(-1)
            var = C[:, j, j] - (k_jo.transpose(1, 2) @ t.cholesky_solve(k_jo, L)).squeeze()
            for i in range(n):  # tempered mixture weights per test sample
                w, _ = cond._temper(loglik[i])
                mean = (w * mu[i]).sum()
                out[i, j] = float(((w * (var + mu[i] ** 2)).sum() - mean**2).clamp(min=0).sqrt())
        return out * self.diff[: task.d] / task.x_std


class Predict0(Attributor):
    name = "Predict 0"
    calibrated = True

    def attribute(self, task, uq):
        return np.zeros_like(task.test.x)


class RandomUA(Attributor):
    name = "Random"

    def __init__(self, seed=0):
        self.seed = seed

    def attribute(self, task, uq):
        return np.random.default_rng(self.seed).uniform(size=task.test.x.shape)


REGISTRY = {
    "sca_gaussian": lambda: SCA("gaussian"),
    "sca_knn": lambda: SCA("knn"),
    "sca_oracle": SCAOracle,
    "gradient": GradientUA,
    "shap": ShapUA,
    "vae": VAEUA,
    "gpvae": GPVAEUA,
    "gpvae_cond": GPVAECondUA,
    "predict0": Predict0,
    "random": RandomUA,
}
