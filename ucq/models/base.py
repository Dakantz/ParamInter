import torch as t


class BaseUCQModel(t.nn.Module):
    """Base class for UCQ models."""

    def __init__(self):
        super().__init__()

    def forward(self, x: t.Tensor) -> t.Tensor:
        raise NotImplementedError("Subclasses must implement the forward method.")

    def uncertainty(self, x: t.Tensor) -> t.Tensor:
        raise NotImplementedError("Subclasses must implement the uncertainty method.")
