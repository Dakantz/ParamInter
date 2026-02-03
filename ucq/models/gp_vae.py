# from gpytorch.models.gplvm.latent_variable import *
from ast import Mult
from gpytorch import ExactMarginalLogLikelihood
from gpytorch import variational
from gpytorch.models import ApproximateGP, ExactGP
from gpytorch.models.gplvm import VariationalLatentVariable
from gpytorch.models.gplvm.bayesian_gplvm import BayesianGPLVM


from gpytorch.means import (
    ConstantMean,
    ConstantMeanGrad,
    LinearMean,
    LinearMeanGrad,
    Mean,
    MultitaskMean,
    ZeroMean,
)
from gpytorch.mlls import VariationalELBO
from gpytorch.priors import NormalPrior
from gpytorch.likelihoods import GaussianLikelihood, MultitaskGaussianLikelihood
from gpytorch.variational import (
    LMCVariationalStrategy,
    MultitaskVariationalStrategy,
    VariationalStrategy,
)
from gpytorch.variational import CholeskyVariationalDistribution
from gpytorch.kernels import MultitaskKernel, ScaleKernel, RBFKernel
from gpytorch.distributions import MultitaskMultivariateNormal, MultivariateNormal

from numba import np
import torch as t
import torch.nn as nn
from torch.utils.data import DataLoader
from umap.layouts import tqdm

import models.base
from models.vae import VAE


class MultitaskGP(ApproximateGP):
    def __init__(
        self,
        likelihood,
        num_tasks,
        input_size,
        gp_latent_size=176,
        n_inducing=512,
    ):
        inducing_points = t.randn(gp_latent_size, n_inducing, input_size)
        variational_distribution = CholeskyVariationalDistribution(
            num_inducing_points=n_inducing, batch_shape=t.Size([gp_latent_size])
        )
        variational_strategy = LMCVariationalStrategy(
            VariationalStrategy(
                self,
                inducing_points=inducing_points,
                variational_distribution=variational_distribution,
                learn_inducing_locations=True,
            ),
            num_tasks=num_tasks,
            num_latents=gp_latent_size,
            latent_dim=-1,
        )
        super(MultitaskGP, self).__init__(variational_strategy)
        self.inducing_points = inducing_points
        self.input_size = input_size
        self.latent_size = gp_latent_size
        print(
            "Initializing MultitaskGP with input size",
            input_size,
            "and latent size",
            gp_latent_size,
            "and n_inducing",
            n_inducing,
        )
        print("Inducing points shape:", inducing_points.shape)
        self.mean_module = ConstantMean(
            batch_shape=t.Size([gp_latent_size]), input_size=input_size
        )

        self.covar_module = ScaleKernel(
            RBFKernel(batch_shape=t.Size([gp_latent_size])),
            batch_shape=t.Size([gp_latent_size]),
        )
        self.norm = nn.BatchNorm1d(gp_latent_size)
        self.linear = nn.Linear(gp_latent_size, gp_latent_size)

    def forward(self, x):
        # mean_x = self.linear(x.T).T
        mean_x = self.mean_module(x)
        # mean_x = self.norm(mean_x.T).T
        covar_x = self.covar_module(x)
        return MultivariateNormal(mean_x, covar_x)


# https://docs.gpytorch.ai/en/stable/examples/045_GPLVM/Gaussian_Process_Latent_Variable_Models_with_Stochastic_Variational_Inference.html
# gGPLVM model
class GP_VAE(models.base.BaseUCQModel):
    def __init__(
        self,
        input_size: int,
        latent_size: int,
        n_inducing=512,
        vae_model: VAE = None,
        retrain_vae=True,
        **kwargs,
    ):
        self.retrain_vae = retrain_vae
        self.latent_size = latent_size
        self.input_size = input_size
        self.n_inducing = n_inducing
        super().__init__()
        self.vae_model: VAE = vae_model
        self.rng = t.Generator().manual_seed(42)
        self.gp: ExactGP = None

    def reinit(self):
        pass

    def forward(self, X):
        z, mu, logvar = self.vae_model.encode(X)
        dist = self.likelihood(self.gp(mu))
        return dist

    def _get_batch_idx(self, batch_size):
        valid_indices = t.arange(self.N)
        batch_indices = t.randperm(self.N)[:batch_size]
        return t.sort(batch_indices).values

    def fit(
        self,
        x: DataLoader[t.Tensor],
        epochs=10,
        batch_size=64,
        lr=1e-3,
        val_dataloader=None,
        log=False,
    ):
        Y = x.dataset[:][0]
        N = Y.shape[0]
        self.N = N
        self.reinit()

        dev = next(self.vae_model.parameters()).device

        # 2 steps!
        # first: optimize VAE
        self.vae_model.to(dev)
        if self.retrain_vae:
            self.vae_model.fit(
                x,
                epochs=epochs,
                batch_size=batch_size,
                lr=lr,
                val_dataloader=val_dataloader,
                log=log,
            )
        self.vae_model.eval()
        self.vae_model.requires_grad_(False)
        latents: t.Tensor = self.vae_model.encode(Y.to(dev))
        if isinstance(latents, tuple):
            latents = latents[1].detach()
        elif hasattr(latents, "rsample"):
            latents = latents.rsample()
        self.inducing_inputs = latents
        self.likelihood = MultitaskGaussianLikelihood(num_tasks=self.input_size).to(dev)

        self.gp = MultitaskGP(
            likelihood=self.likelihood,
            input_size=self.latent_size,
            gp_latent_size=int(self.latent_size / 2),
            num_tasks=self.input_size,
            n_inducing=self.n_inducing,
        ).to(dev)

        mll = VariationalELBO(self.likelihood, self.gp, num_data=Y.shape[0])

        # second: optimize bGPLVM with VAE latent samples
        # Likelihood

        optimizer = t.optim.Adam(
            [
                {"params": self.gp.parameters()},
                {"params": self.likelihood.parameters()},
            ],
            lr=lr,
        )
        loss_list = []
        gen = tqdm(total=epochs * len(x)) if log else None
        for epoch in range(epochs):
            for batch_data in enumerate(x):
                Y = batch_data[1][0].to(dev)
                latent = self.vae_model.encode(Y)
                if isinstance(latent, tuple):
                    sample_batch = latent[0].detach()
                else:
                    sample_batch = latent.rsample()
                optimizer.zero_grad()
                output_batch = self.gp(sample_batch.to(dev))
                loss = -mll(output_batch, Y).sum()
                loss_list.append(loss.item())
                if log:
                    gen.set_description(
                        f"Epoch {epoch + 1}/{epochs} | Loss: {loss.item():.4f} "
                    )
                    gen.update(1)
                loss.backward()
                optimizer.step()

    def uncertainty(self, x: t.Tensor) -> t.Tensor:
        self.eval()
        with t.no_grad():
            z, mu, logvar = self.vae_model.encode(x)

            dist = self.likelihood(self.gp(mu))
            std = dist.variance.sqrt()

        return std
