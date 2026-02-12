from sklearn.base import TransformerMixin
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import lightgbm as lgb

from ucq.models import BaseUCQModel

from backend.models import DataDescription, ManagerSettings, DataPoint

from sklearn.neighbors import NearestNeighbors

try:
    from cuml.neighbors import NearestNeighbors
    from cuml.manifold.umap import UMAP
    from cuml import TSNE
except ImportError:
    print("Cuml not found, using CPU-based libraries.")
    cuml = None
    from sklearn.manifold import TSNE
    from umap import UMAP

from backend.col_defs import column_types
import pandas as pd
import numpy as np
from .config import DataConfig
import tqdm
from pathlib import Path
import os
import pickle

from ucq.utils import (
    train_vae_noiseless,
    minmaxnormed_tensor_of,
    autodevice,
)
# https://stackoverflow.com/questions/6760685/what-is-the-best-way-of-implementing-a-singleton-in-python


class ModelManager:
    def __init__(
        self,
        config: DataConfig = DataConfig(),
    ):
        self.cfg = config
        self.base_dir = Path(config.base_dir)
        self.mode = config.mode
        self.data_file = config.data_file
        self.data_name = config.data_name
        self.short_data_name = config.short_data_name
        self.input_cols_num = config.input_cols
        self.output_cols_num = config.output_cols
        self.dataset_path_base = Path(config.base_dir) / Path("datasets")
        self.models_path = (
            Path(config.base_dir) / Path("models") / Path(config.short_data_name)
        )
        if self.models_path.exists() is False:
            os.makedirs(self.models_path)
        self.time_col = config.time_col
        self.inputs_constrained = config.inputs_constrained
        self.loaded = False
        self.sanity_check()
        self.data = None
        self.load_data_file()

        self.vae_model: BaseUCQModel = None
        self.dev = autodevice()
        self.embedded_tsne: np.ndarray = None

    def dataset_path(self) -> str:
        return str(self.dataset_path_base / Path(self.data_file))

    def sanity_check(self):
        if Path(self.dataset_path()).exists() is False:
            print("WARNING: Data file does not exist:", self.dataset_path())

    def load_data_file(self):
        if self.data is not None:
            return self.data
        print(f"Reading data file from {self.dataset_path()}...")
        if self.dataset_path().endswith(".csv"):
            data = pd.read_csv(self.dataset_path())
        elif self.dataset_path().endswith(".txt") or self.dataset_path().endswith(
            ".tsv"
        ):
            data = pd.read_table(self.dataset_path())
        else:
            raise ValueError("Unsupported data file format.: ", self.dataset_path())
        data = data.replace([np.inf, -np.inf], np.nan).fillna(0).dropna()
        self.data = data

        time_col_offset = 1 if self.time_col is not None else 0
        input_cols = data.columns.to_list()[
            time_col_offset : self.input_cols_num + time_col_offset
        ]
        output_cols = data.columns.to_list()[
            self.input_cols_num + time_col_offset : self.input_cols_num
            + time_col_offset
            + self.output_cols_num
        ]

        self.input_cols = input_cols
        self.output_cols = output_cols

        cleaned = data[self.input_cols + self.output_cols].fillna(0).astype(np.float32)
        self.cleaned: pd.DataFrame = cleaned

        self.column_types_loaded = column_types
        if "scivis" not in self.short_data_name:
            # For other datasets, use all columns as a single type
            self.column_types_loaded = {
                "Input": self.input_cols,
                "All": self.input_cols + self.output_cols,
                "Output": self.output_cols,
            }
        self.col_defs = self.column_types_loaded
        return data

    def load(self):
        print(f"Loading dataset from {self.dataset_path()}...")
        data = self.load_data_file()
        cleaned = self.cleaned
        inputs = cleaned[self.input_cols].values.astype(np.float32)
        outputs = cleaned[self.output_cols].values.astype(np.float32)
        if self.time_col is not None:
            time = data.iloc[:, self.time_col]
        else:
            time = None

        nn = NearestNeighbors(n_neighbors=1)
        nn.fit(outputs)

        nn_inputs = NearestNeighbors(n_neighbors=1)
        nn_inputs.fit(inputs)

        scaler_outs = StandardScaler()
        scaled_outputs = scaler_outs.fit_transform(outputs)

        embedding_subsets: dict[str, np.ndarray] = {}
        dim_reducers: dict[str, TransformerMixin] = {}

        for col_name, col_list in tqdm.tqdm(
            self.column_types_loaded.items(), desc="Creating embeddings"
        ):
            data_path = self.models_path / Path(f"{col_name}_{self.mode}.npy")
            if len(col_list) == 2:
                # for 2D subsets, use the original data as "embedding"
                embedding_subsets[col_name] = MinMaxScaler().fit_transform(
                    cleaned[col_list].values.astype(np.float32)
                )
                continue
            if data_path.exists():
                embedded_tsne = np.load(data_path)
                embedding_subsets[col_name] = embedded_tsne
            else:
                dim_reducers[col_name] = (
                    TSNE(
                        n_components=2,
                        perplexity=40,
                    )
                    if self.mode == "tsne"
                    else UMAP(
                        n_neighbors=15,
                    )
                )
                embedded_tsne: np.ndarray = dim_reducers[col_name].fit_transform(
                    cleaned[col_list].values.astype(np.float32)
                )
                scaled_tsne = MinMaxScaler().fit_transform(embedded_tsne)
                np.save(data_path, scaled_tsne)
                embedding_subsets[col_name] = scaled_tsne

        model_ensemble: dict[str, lgb.LGBMRegressor] = {}

        lgbms_paths = self.models_path / Path("lgbms")
        if not lgbms_paths.exists():
            os.makedirs(lgbms_paths)
        for output_col in tqdm.tqdm(self.output_cols, desc="Loading models"):
            col_name = output_col.encode("ascii", "ignore").decode("ascii")
            col_name = col_name.replace(" ", "_")
            col_name = col_name.replace(".", "_")
            col_name = col_name.replace("/", "_")

            model_path = lgbms_paths / Path(f"{col_name}_model.txt")
            if not model_path.exists():
                print(f"Model file {model_path} does not exist. Skipping.")
                # train model here if needed
                model = lgb.LGBMRegressor()
                model.fit(
                    cleaned[self.input_cols].values,
                    cleaned[output_col].values,
                )
                model.booster_.save_model(str(model_path))

            model = lgb.Booster(
                model_file=str(model_path),
            )
            model_ensemble[output_col] = model

        print("Model ensemble loaded with models for outputs:", model_ensemble.keys())
        self.vae_model_path = (
            self.models_path / f"vae_model_{self.cfg.vae_mode.name}.pckle"
        )
        self.vae_model = None
        if self.cfg.use_ucq:
            if self.vae_model_path.exists():
                print("Loading VAE model from", self.vae_model_path)
                with open(self.vae_model_path, "rb") as f:
                    self.vae_model = pickle.load(f)

            if self.vae_model is None:
                print("Training VAE model, no model @", self.vae_model_path)
                self.vae_model = train_vae_noiseless(
                    self.cleaned,
                    self.cfg.vae_mode.toClass(),
                    epochs=3,
                    log=True,
                    model_kwargs={"latent_size": int(np.sqrt(self.cleaned.shape[1]))},
                )

                with open(self.vae_model_path, "wb") as f:
                    pickle.dump(self.vae_model.cpu(), f)

            self.vae_model = self.vae_model.to(self.dev)
        self.eval_uncertainties()
        self.model_ensemble = model_ensemble
        self.scaler_outs = scaler_outs
        self.scaled_outputs = scaled_outputs
        self.nn = nn
        self.nn_inputs = nn_inputs
        self.embedded_tsne = embedded_tsne
        self.embedding_subsets = embedding_subsets
        self.dim_reducers = dim_reducers
        self.data = data

        self.column_types = self.column_types_loaded
        self.loaded = True

    def eval_uncertainties(self):
        if self.vae_model is None:
            self.uncertainty = pd.DataFrame(
                data=np.zeros_like(self.cleaned), columns=self.cleaned.columns
            )
            return
        cleaned_minmax = minmaxnormed_tensor_of(self.cleaned).to(self.dev)
        noise = self.vae_model.uncertainty(cleaned_minmax.to())
        noise_df = pd.DataFrame(data=noise.cpu().numpy(), columns=self.cleaned.columns)
        self.uncertainty = noise_df * (self.cleaned.max() - self.cleaned.min())

    def get_settings(self) -> ManagerSettings:
        return ManagerSettings(
            data_description=DataDescription(
                input_cols=self.input_cols,
                output_cols=self.output_cols,
                num_samples=self.data.shape[0],
                num_features=len(self.input_cols),
                num_outputs=len(self.output_cols),
                min_values=self.cleaned.min().to_dict(),
                max_values=self.cleaned.max().to_dict(),
                mean_values=self.cleaned.mean().to_dict(),
                std_values=self.cleaned.std().to_dict(),
                all_columns=self.cleaned.columns.tolist(),
                inputs_constrained=self.inputs_constrained,
            ),
            mode=self.mode,
            data_name=self.data_name,
            short_data_name=self.short_data_name,
            input_cols=len(self.input_cols),
            output_cols=len(self.output_cols),
            time_col=self.time_col,
            inputs_constrained=self.inputs_constrained,
            col_defs=self.column_types_loaded,
            loaded=self.loaded,
            use_ucq=self.cfg.use_ucq,
        )

    def get_dp(self, idx):
        return DataPoint(
            inputs=self.cleaned[self.input_cols].iloc[idx].values.tolist(),
            outputs=self.cleaned[self.output_cols].iloc[idx].values.tolist(),
            projected_outputs=self.embedded_tsne[idx].tolist(),
            index=idx,
            uncertainties=self.uncertainty.loc[idx, :].to_list(),
        )
