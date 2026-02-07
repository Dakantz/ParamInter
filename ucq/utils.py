import pandas as pd

import torch as t
from .models.base import BaseUCQModel
from .noise import Noiser
import torch.utils.data as data_utils


def autodevice():
    return (
        "cuda"
        if t.cuda.is_available()
        else "mps"
        if t.backends.mps.is_available()
        else "cpu"
    )


# from https://hunterheidenreich.com/posts/modern-variational-autoencoder-in-pytorch/
def train_vae(
    cleaned: pd.DataFrame,
    vae_model: BaseUCQModel,
    noise_model: Noiser = None,
    val_percent: float = 0.2,
    test_percent: float = 0.1,
    lr: float = 1e-3,
    epochs: int = 3,
    batch_size: int = 128,
    log=False,
    model_kwargs={},
    device: str = None,
):
    if not device:
        device = autodevice()

    diff = cleaned.max() - cleaned.min()
    diff[diff == 0] = cleaned.max()[diff == 0]
    diff[diff == 0] = 1
    data_normed = (cleaned - cleaned.min()) / diff
    data_t = t.tensor(data_normed.values, dtype=t.float32)
    noise_t = t.zeros_like(data_t)
    if noise_model is not None:
        data_t, noise_t = noise_model.add_noise(data_t)
        if log:
            print("Added noise with model:", noise_model.__class__.__name__)

    dataset = data_utils.TensorDataset(data_t, noise_t)

    val_size = int(len(dataset) * val_percent)
    test_size = int(len(dataset) * test_percent)
    train_size = len(dataset) - val_size - test_size
    train_dataset, val_dataset, test_dataset = data_utils.random_split(
        dataset, [train_size, val_size, test_size]
    )

    train_dataloader = data_utils.DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True
    )
    val_dataloader = data_utils.DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False
    )
    model: BaseUCQModel = vae_model(
        input_size=data_t.shape[1],
        **model_kwargs,
    ).to(device)
    model.fit(
        train_dataloader, epochs=epochs, val_dataloader=val_dataloader, log=log, lr=lr
    )
    model.eval()
    return {
        "base_data": data_t,
        "noise_data": noise_t,
        "vae_model": model,
        "training": {
            "data": train_dataset[:][0],
            "noise": train_dataset[:][1],
        },
        "validation": {
            "data": val_dataset[:][0],
            "noise": val_dataset[:][1],
        },
        "test": {
            "data": test_dataset[:][0],
            "noise": test_dataset[:][1],
        },
    }


def minmaxnormed_tensor_of(df: pd.DataFrame):
    diff = df.max() - df.min()
    diff[diff == 0] = df.max()[diff == 0]
    diff[diff == 0] = 1
    data_normed = (df - df.min()) / diff
    data_t = t.tensor(data_normed.values, dtype=t.float32)
    return data_t


def train_vae_noiseless(
    cleaned: pd.DataFrame,
    vae_model: BaseUCQModel,
    lr: float = 1e-3,
    epochs: int = 3,
    batch_size: int = 128,
    log=False,
    model_kwargs={},
    device: str = None,
):

    diff = cleaned.max() - cleaned.min()
    diff[diff == 0] = cleaned.max()[diff == 0]
    diff[diff == 0] = 1
    data_normed = (cleaned - cleaned.min()) / diff
    data_t = t.tensor(data_normed.values, dtype=t.float32)
    noise_t = t.zeros_like(data_t)

    train_dataset = data_utils.TensorDataset(data_t, noise_t)

    train_dataloader = data_utils.DataLoader(
        train_dataset, batch_size=batch_size, shuffle=True
    )
    model: BaseUCQModel = vae_model(
        input_size=data_t.shape[1],
        **model_kwargs,
    ).to(device)
    model.fit(train_dataloader, epochs=epochs, val_dataloader=None, log=log, lr=lr)
    model.eval()
    return model
