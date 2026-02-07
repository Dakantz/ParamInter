import torch as t
from torch.distributions import MultivariateNormal
from torch.utils.data import DataLoader


class BaseUCQModel(t.nn.Module):
    """Base class for UCQ models."""

    def __init__(self):
        super().__init__()

    def forward(self, x: t.Tensor) -> tuple[t.Tensor, ...] | MultivariateNormal:
        raise NotImplementedError("Subclasses must implement the forward method.")

    def reconstruct(self, x: t.Tensor) -> tuple[t.Tensor, ...]:
        rec = self.forward(x)
        if not isinstance(rec, t.tensor):
            raise TypeError(
                "Subcalls did not return tensor during forward call. Please overwrite this method!"
            )
        return rec

    def encode(self, x: t.Tensor) -> tuple[t.Tensor, t.Tensor]:
        raise NotImplementedError("Subclasses must implement the encode method.")

    def uncertainty(self, x: t.Tensor) -> t.Tensor:
        raise NotImplementedError("Subclasses must implement the uncertainty method.")

    def fit(
        self,
        x: DataLoader,
        epochs=10,
        batch_size=64,
        lr=1e-3,
        val_dataloader: DataLoader = None,
        log=False,
    ):
        raise NotImplementedError("Subclasses must implement the fit method.")
