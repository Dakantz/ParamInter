from ucq.models.base import BaseUCQModel
import torch as t

from torch.utils.data import DataLoader


class RandomBaseline(BaseUCQModel):
    def __init__(self, input_size: int, seed=42, latent_size=16, **kwargs):
        super(RandomBaseline, self).__init__()
        self.input_size = input_size
        self.latent_size = latent_size
        self.rng = t.Generator().manual_seed(seed)

    def forward(self, x: t.Tensor) -> t.Tensor:
        batch_size = x.shape[0]
        preds = t.randn(batch_size, self.input_size, generator=self.rng).to(x.device)
        mus = t.randn(batch_size, self.latent_size, generator=self.rng).to(x.device)
        sigmas = t.abs(t.randn(batch_size, self.latent_size, generator=self.rng)).to(
            x.device
        )
        return (preds, mus, sigmas)

    def uncertainty(self, x: t.Tensor) -> t.Tensor:
        batch_size = x.shape[0]

        return t.abs(t.randn(batch_size, self.input_size, generator=self.rng)).to(
            x.device
        )

    def fit(
        self,
        x: DataLoader,
        epochs=10,
        batch_size=64,
        lr=1e-3,
        val_dataloader: DataLoader = None,
        log=False,
    ):
        pass
