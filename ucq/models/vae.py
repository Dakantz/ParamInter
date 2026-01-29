import torch as t
import torch.nn as nn
import models.base


# VAE model
class VAE(models.base.BaseUCQModel):
    def __init__(
        self,
        input_size,
        layers=[128, 64, 32],
        norm=nn.BatchNorm1d,
        latent_size=16,
        out_norm=nn.BatchNorm1d,
        samples=16,
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
        std = t.exp(0.5 * logvar)
        eps = t.randn_like(std)
        return mu + eps * std

    def forward(self, x: t.Tensor) -> t.Tensor:
        h = self.encoder(x)
        mu, logvar = (
            h[..., : self.fc_mu.out_features],
            h[..., self.fc_mu.out_features :],
        )
        z = self.reparameterize(mu, logvar)
        x_reconstructed = self.decoder(z)
        if self.out_norm is not None:
            x_reconstructed = self.out_norm(x_reconstructed)
        return x_reconstructed, mu, logvar

    def uncertainty(self, x: t.Tensor) -> t.Tensor:
        self.eval()
        with t.no_grad():
            h = self.encoder(x)
            mu, logvar = (
                h[..., : self.fc_mu.out_features],
                h[..., self.fc_mu.out_features :],
            )
            std = t.exp(0.5 * logvar)

            z_samples = (
                t.randn(self.samples, *std.shape, generator=self.rng).to(x.device) * std
                + mu
            )
            z_samples = z_samples.view(-1, mu.shape[-1])
            x_samples = self.decoder(z_samples)

            if self.out_norm is not None:
                x_samples = self.out_norm(x_samples)

            x_samples = x_samples.view(self.samples, *x.shape)
            std = t.std(x_samples, dim=0)

        return std
