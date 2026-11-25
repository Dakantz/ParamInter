"""Uncertainty-aware forward model: a shallow heteroscedastic neural network.

One hidden layer (smooth SiLU activations so input gradients are meaningful), two heads for the
mean ``g(x)`` and log-variance of ``y | x``, trained with the Gaussian NLL on standardised data.
The predicted std is calibrated on a held-out calibration split with inductive conformal
prediction (scale factor so that the ``coverage`` central interval of N(g, (c sigma)^2) holds),
mirroring the LightGBM + conformal PI calibration of the ICASSP 2025 SCA paper.
"""

from __future__ import annotations

import numpy as np
import torch as t
import torch.nn as nn
from scipy.stats import norm


class ShallowHeteroscedasticNN(nn.Module):
    def __init__(self, d: int, hidden: int = 64):
        super().__init__()
        self.body = nn.Sequential(nn.Linear(d, hidden), nn.SiLU())
        self.mean_head = nn.Linear(hidden, 1)
        self.logvar_head = nn.Linear(hidden, 1)

    def forward(self, z: t.Tensor) -> tuple[t.Tensor, t.Tensor]:
        h = self.body(z)
        return self.mean_head(h).squeeze(-1), self.logvar_head(h).squeeze(-1)


class UQModel:
    """Wraps the network with input/output standardisation and conformal calibration.

    All gradient-facing methods (`mean_z`, `std_z`) work in *standardised* input space
    ``z = (x - mu_x) / sd_x`` and return standardised outputs, which is the space every
    attributor operates in.
    """

    def __init__(self, hidden=64, epochs=200, lr=3e-3, batch_size=256, seed=0, coverage=0.9):
        self.hidden, self.epochs, self.lr, self.batch_size = hidden, epochs, lr, batch_size
        self.seed, self.coverage = seed, coverage
        self.calib = 1.0

    def fit(self, x: np.ndarray, y: np.ndarray, x_cal=None, y_cal=None):
        t.manual_seed(self.seed)
        self.mu_x, self.sd_x = x.mean(0), x.std(0)
        self.sd_x[self.sd_x == 0] = 1
        self.mu_y, self.sd_y = y.mean(), y.std() or 1.0
        z = t.tensor((x - self.mu_x) / self.sd_x, dtype=t.float32)
        yz = t.tensor((y - self.mu_y) / self.sd_y, dtype=t.float32)
        self.net = ShallowHeteroscedasticNN(x.shape[1], self.hidden)
        opt = t.optim.Adam(self.net.parameters(), lr=self.lr)
        sched = t.optim.lr_scheduler.CosineAnnealingLR(opt, self.epochs)
        n = len(z)
        for epoch in range(self.epochs):
            perm = t.randperm(n)
            # warm-up the mean with MSE, then switch to the heteroscedastic NLL
            for i in range(0, n, self.batch_size):
                b = perm[i : i + self.batch_size]
                m, lv = self.net(z[b])
                if epoch < self.epochs // 5:
                    loss = ((m - yz[b]) ** 2).mean()
                else:
                    loss = nn.functional.gaussian_nll_loss(m, yz[b], lv.exp(), eps=1e-6)
                opt.zero_grad()
                loss.backward()
                opt.step()
            sched.step()
        self.net.eval()
        for p in self.net.parameters():
            p.requires_grad_(False)
        if x_cal is not None:
            self.calibrate(x_cal, y_cal)
        return self

    def calibrate(self, x_cal, y_cal):
        """Inductive conformal calibration of the std scale."""
        self.calib = 1.0
        zc = self.to_z(x_cal)
        with t.no_grad():
            m, s = self.mean_z(zc), self.std_z(zc)
        r = np.abs((y_cal - self.mu_y) / self.sd_y - m.numpy()) / s.numpy()
        n = len(r)
        q = np.quantile(r, min(1.0, np.ceil((n + 1) * self.coverage) / n))
        self.calib = float(q / norm.ppf(0.5 + self.coverage / 2))

    # --------------------------------------------------------------- helpers
    def to_z(self, x: np.ndarray) -> t.Tensor:
        return t.tensor((x - self.mu_x) / self.sd_x, dtype=t.float32)

    def mean_z(self, z: t.Tensor) -> t.Tensor:
        return self.net(z)[0]

    def std_z(self, z: t.Tensor) -> t.Tensor:
        return self.calib * t.exp(0.5 * self.net(z)[1])

    def r2(self, x, y) -> float:
        with t.no_grad():
            m = self.mean_z(self.to_z(x)).numpy() * self.sd_y + self.mu_y
        return float(1 - ((y - m) ** 2).sum() / ((y - y.mean()) ** 2).sum())
