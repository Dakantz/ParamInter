import torch as t
import torch.nn as nn
from torch.utils.data import DataLoader
from torchmetrics.functional import r2_score
from umap.layouts import tqdm
from ucq.models.base import BaseUCQModel


# VAE model
class VAE(BaseUCQModel):
    def __init__(
        self,
        input_size,
        layers=[128, 64, 32],
        norm=nn.BatchNorm1d,
        latent_size=16,
        out_norm=nn.BatchNorm1d,
        samples=16,
        **kwargs,
    ):
        super(VAE, self).__init__()
        _layers = [input_size] + layers + [latent_size * 2]
        encoder_layers = []
        for i in range(len(_layers) - 1):
            in_size = _layers[i]
            out_size = _layers[i + 1]
            encoder_layers.append(nn.Linear(in_size, out_size))
            encoder_layers.append(nn.ReLU())
            if norm:
                encoder_layers.append(norm(out_size))
        self.encoder = nn.Sequential(*encoder_layers)
        self.fc_mu = nn.Linear(layers[-1], latent_size)
        self.fc_logvar = nn.Linear(layers[-1], latent_size)
        decoder_layers = []
        out_layers = _layers[::-1]
        for i in range(len(out_layers) - 1):
            if i == 0:
                in_size = latent_size
            else:
                in_size = out_layers[i]
            out_size = out_layers[i + 1]
            decoder_layers.append(nn.Linear(in_size, out_size))
            decoder_layers.append(nn.ReLU())
            if norm:
                decoder_layers.append(norm(out_size))
        self.decoder = nn.Sequential(*decoder_layers)
        if out_norm is not None:
            self.out_norm = out_norm(input_size)
        else:
            self.out_norm = None
        self.samples = samples
        self.rng = t.Generator().manual_seed(42)

    def reparameterize(self, mu, logvar):
        logvar_softplus = t.nn.functional.sigmoid(logvar)
        eps = t.randn_like(logvar_softplus)
        return mu + eps * logvar_softplus

    def encode(self, x: t.Tensor) -> tuple[t.Tensor, t.Tensor]:
        h = self.encoder(x)
        mu, logvar = (
            h[..., : self.fc_mu.out_features],
            h[..., self.fc_mu.out_features :],
        )
        z = self.reparameterize(mu, logvar)
        return z, mu, logvar

    def forward(self, x: t.Tensor) -> tuple[t.Tensor, t.Tensor, t.Tensor]:
        z, mu, logvar = self.encode(x)
        x_reconstructed = self.decoder(z)
        if self.out_norm is not None:
            x_reconstructed = self.out_norm(x_reconstructed)
        return x_reconstructed, mu, logvar

    def fit(
        self,
        x: DataLoader,
        epochs=10,
        batch_size=64,
        lr=1e-3,
        val_dataloader=None,
        log=False,
    ):
        optimizer = t.optim.Adam(self.parameters(), lr=lr)
        device = next(self.decoder[0].parameters()).device

        # log mse loss
        def log_mse_loss(recon_x, x):
            mse_loss = nn.MSELoss()(recon_x, x)
            return t.log(mse_loss + 1e-8)

        def kld_loss(mu, logvar, eps=1e-8):
            KLD = mu.pow(2) + logvar.pow(2) - 1 - t.log(logvar.pow(2) + eps)
            return KLD.mean()

        def vae_loss(recon_x, x, mu, logvar) -> t.Tensor:
            mse_loss = log_mse_loss(recon_x, x)
            return mse_loss - kld_loss(mu, logvar)

        self.train()
        loss_train = []
        gen = tqdm(total=epochs * len(x)) if log else None
        for epoch in range(epochs):
            for i, batch_inputs in enumerate(x):
                batch_inputs = batch_inputs[0].to(device)
                optimizer.zero_grad()
                outputs, mu, logvar = self(batch_inputs)
                loss = vae_loss(outputs, batch_inputs, mu, logvar)
                loss.backward()
                optimizer.step()
                loss_train.append(loss.item())
                if log:
                    gen.set_description(
                        f"Epoch {epoch + 1}/{epochs} | Batch {i + 1}/{len(x)} | Train Loss: {loss.item():.4f} "
                    )
                    gen.update(1)
            loss_metrics_epoch = []
            if val_dataloader is not None:
                for val_batch in val_dataloader:
                    val_inputs = val_batch[0].to(device)
                    with t.no_grad():
                        val_outputs, val_mu, val_logvar = self(val_inputs)
                        val_loss = vae_loss(val_outputs, val_inputs, val_mu, val_logvar)
                    r2_score_val = r2_score(val_outputs, val_inputs)

                    loss_metrics_epoch.append(
                        {"loss": val_loss.item(), "r2_score": r2_score_val.item()}
                    )
                avg_val_loss = {
                    key: t.mean(t.tensor([m[key] for m in loss_metrics_epoch]))
                    .mean()
                    .item()
                    for key in loss_metrics_epoch[0]
                }
            if log:
                print(
                    f"Epoch {epoch + 1}/{epochs}, Train Loss: {loss.item():.4f}",
                )
                if val_dataloader is not None:
                    print(
                        f"           Val Loss: {avg_val_loss['loss']:.4f}, Val R2 Score: {avg_val_loss['r2_score']:.4f}"
                    )

    def uncertainty(self, x: t.Tensor) -> t.Tensor:
        self.eval()
        with t.no_grad():
            h = self.encoder(x)
            mu, logvar = (
                h[..., : self.fc_mu.out_features],
                h[..., self.fc_mu.out_features :],
            )
            logvar = t.nn.functional.sigmoid(logvar)

            z_samples = (
                t.randn(self.samples, *logvar.shape, generator=self.rng).to(x.device)
                * logvar
                + mu
            )
            z_samples = z_samples.view(-1, mu.shape[-1])
            x_samples = self.decoder(z_samples)

            if self.out_norm is not None:
                x_samples = self.out_norm(x_samples)

            x_samples = x_samples.view(self.samples, *x.shape)
            std = t.std(x_samples, dim=0)

        return std
