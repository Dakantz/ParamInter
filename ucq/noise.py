import torch as t


class Noiser:
    def __init__(self, noise_level=0.1):
        self.noise_level = noise_level

    def add_noise(self, data: t.Tensor) -> tuple[t.Tensor, t.Tensor]:
        raise NotImplementedError


class ColumnBasedNoiser(Noiser):
    def __init__(self, noise_level=0.1, seed=42):
        super().__init__(noise_level)
        self.rng = t.Generator().manual_seed(seed)

    def add_noise(self, data: t.Tensor) -> tuple[t.Tensor, t.Tensor]:
        base_data = data.clone()
        # uniform noise per column
        noise_per_column = t.abs(t.randn(data.shape[1], generator=self.rng))
        noise_per_column = self.noise_level * noise_per_column / noise_per_column.max()
        noise_levels = noise_per_column.unsqueeze(0).expand_as(data)
        noise_total = t.randn_like(data, generator=self.rng) * noise_levels

        base_data += noise_total
        return base_data, noise_levels


class SingleModeColumnNoiser(Noiser):
    def __init__(self, noise_level=0.1, seed=42, mode_width=0.1):
        super().__init__(noise_level)
        self.rng = t.Generator().manual_seed(seed)
        self.mode_width = mode_width

    def add_noise(self, data: t.Tensor) -> t.Tensor:
        base_data = data.clone()
        n_rows, n_cols = data.shape
        # again once per column
        noise_per_column = t.abs(t.randn(data.shape[1], generator=self.rng))
        noise_per_column = self.noise_level * noise_per_column / noise_per_column.max()

        noise_total = t.zeros_like(data)
        noise_levels = t.zeros_like(data)
        for col in range(n_cols):
            # then select a random mode
            mode_idx = t.randint(0, n_rows, (1,), generator=self.rng).item()
            mode_value = data[mode_idx, col]

            # compute noise levels based on distance from mode
            noise_levels_col = t.exp(
                -0.5 * ((data[:, col] - mode_value) / (self.mode_width)) ** 2
            )
            noise_levels_col = noise_levels_col / noise_levels_col.max()
            noise_levels[:, col] = noise_levels_col
            # generate noise with scaled levels
            noise = (
                t.randn(n_rows, generator=self.rng)
                * noise_per_column[col]
                * noise_levels[:, col]
            )
            noise_total[:, col] += noise
        base_data += noise_total
        return base_data, noise_levels


class MultiModeColumnNoiser(Noiser):
    def __init__(self, noise_level=0.1, seed=42, mode_width=0.1, n_modes=3):
        super().__init__(noise_level)
        self.rng = t.Generator().manual_seed(seed)
        self.mode_width = mode_width
        self.n_modes = n_modes

    def add_noise(self, data: t.Tensor) -> tuple[t.Tensor, t.Tensor]:
        base_data = data.clone()
        n_rows, n_cols = data.shape
        # again once per column
        noise_per_column = t.abs(t.randn(data.shape[1], generator=self.rng))
        noise_per_column = self.noise_level * noise_per_column / noise_per_column.max()
        noise_total = t.zeros_like(data)
        noise_levels = t.zeros_like(data)
        for col in range(n_cols):
            # select multiple random modes
            mode_indices = t.randint(0, n_rows, (self.n_modes,), generator=self.rng)
            mode_values = data[mode_indices, col]

            # compute noise levels based on distance from nearest mode
            noise_levels_col = t.zeros(n_rows)
            for mode_value in mode_values:
                noise_levels_col += t.exp(
                    -0.5 * ((data[:, col] - mode_value) / (self.mode_width)) ** 2
                )
            noise_levels_col = noise_levels_col / noise_levels_col.max()
            noise_levels[:, col] = noise_levels_col
            # generate noise with scaled levels
            noise = (
                t.randn(n_rows, generator=self.rng)
                * noise_per_column[col]
                * noise_levels_col
            )
            noise_total[:, col] += noise
        base_data += noise_total

        return base_data, noise_levels


class SingleModeGlobalNoiser(Noiser):
    def __init__(self, noise_level=0.1, seed=42, mode_width=0.1):
        super().__init__(noise_level)
        self.rng = t.Generator().manual_seed(seed)
        self.mode_width = mode_width

    def add_noise(self, data: t.Tensor) -> tuple[t.Tensor, t.Tensor]:
        base_data = data.clone()
        n_rows, n_cols = data.shape

        # select a random mode in the full space
        mode_idx = t.randint(0, n_rows, (1,), generator=self.rng).item()
        mode_value = data[mode_idx, :]

        # compute noise levels based on distance from mode
        distances = data - mode_value
        noise_levels = t.exp(-0.5 * (distances / (self.mode_width)) ** 2)
        noise_levels = noise_levels / noise_levels.max()

        # generate noise with scaled levels
        noise_total = (
            t.randn_like(data, generator=self.rng) * noise_levels * self.noise_level
        )

        base_data += noise_total
        return base_data, noise_levels


class MultiModeGlobalNoiser(Noiser):
    def __init__(self, noise_level=0.1, seed=42, mode_width=0.1, n_modes=3):
        super().__init__(noise_level)
        self.rng = t.Generator().manual_seed(seed)
        self.mode_width = mode_width
        self.n_modes = n_modes

    def add_noise(self, data: t.Tensor) -> tuple[t.Tensor, t.Tensor]:
        base_data = data.clone()
        n_rows, n_cols = data.shape

        # select multiple random modes in the full space
        mode_indices = t.randint(0, n_rows, (self.n_modes,), generator=self.rng)
        mode_values = data[mode_indices, :]

        # compute noise levels based on distance from nearest mode
        noise_levels = t.zeros_like(data)
        for mode_value in mode_values:
            distances = data - mode_value
            noise_levels += t.exp(-0.5 * (distances / (self.mode_width)) ** 2)
        noise_levels = noise_levels / noise_levels.max()

        # generate noise with scaled levels
        noise_total = (
            t.randn_like(data, generator=self.rng) * noise_levels * self.noise_level
        )

        base_data += noise_total
        return base_data, noise_levels
