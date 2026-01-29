from dataclasses import dataclass
from turtle import shape
from sklearn.base import TransformerMixin
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import umap
import lightgbm as lgb

from backend.models import DataDescription, ManagerSettings
from backend.utils import Singleton


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

from .col_defs import column_types, input_types
import pandas as pd
import numpy as np

import tqdm
from pathlib import Path
import os


# https://stackoverflow.com/questions/6760685/what-is-the-best-way-of-implementing-a-singleton-in-python
@dataclass
class DataConfig:
    base_dir: str = os.getenv("DATA_DIR", "./data")
    mode: str = "tsne"
    data_file: str = "scivis/alloy_data.txt"
    data_name: str = "Alloy Simulation Data (SciVis Contest 2025)"
    short_data_name: str = "scivis"
    input_cols: int = 6
    output_cols: int = 64
    time_col: int | None = None
    inputs_constrained: bool = True
    is_config: bool = True


class DataMan:
    def __init__(
        self,
        config: DataConfig = DataConfig(),
    ):
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
        self.cleaned = cleaned

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
        models_path = self.models_path / Path("lgbms")
        if not models_path.exists():
            os.makedirs(models_path)
        for output_col in tqdm.tqdm(self.output_cols, desc="Loading models"):
            col_name = output_col.encode("ascii", "ignore").decode("ascii")
            col_name = col_name.replace(" ", "_")
            col_name = col_name.replace(".", "_")
            col_name = col_name.replace("/", "_")

            model_path = models_path / Path(f"{col_name}_model.txt")
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
        )


scivis_man = DataConfig(mode=os.getenv("EMBEDDING", "tsne"))

privbayes_man = DataConfig(
    mode=os.getenv("EMBEDDING", "tsne"),
    data_file="privbayes/privbayes_encoded.csv",
    data_name="PrivBayes Data",
    short_data_name="privbayes",
    input_cols=18,
    output_cols=27,
    time_col=0,
)


mast_man = DataConfig(
    mode=os.getenv("EMBEDDING", "tsne"),
    data_file="mast/processed_mast_data.csv",
    data_name="MAST Data",
    short_data_name="mast",
    input_cols=8,
    output_cols=10,
    time_col=0,
)

eaf_man = DataConfig(
    mode=os.getenv("EMBEDDING", "tsne"),
    data_file="eaf/eaf_simulation_data.csv",
    data_name="Electric Arc Furnace Simulation Data",
    short_data_name="eaf",
    input_cols=6,
    output_cols=51,
    time_col=0,
    inputs_constrained=False,
)

cfg_type = dict[str, dict[str, DataConfig] | DataConfig]


class SetsManager:
    def __init__(self, separator: str = "-"):
        configs_json = os.getenv("SETS_CONFIG_JSON", None)
        if configs_json is not None and Path(configs_json).exists():
            self.load_config_file(configs_json)
        else:
            print("Using default dataset configs.")
            self.load_defaults()

        self.managers: dict[str, dict[str, DataMan] | DataMan] = {}
        for name, cfg in self.configs.items():
            if isinstance(cfg, dict):
                self.managers[name] = {}
                for sub_name, sub_cfg in cfg.items():
                    self.managers[name][sub_name] = DataMan(sub_cfg)
            else:
                self.managers[name] = DataMan(cfg)
        self.separator = separator

    def load_config_file(self, path: str):
        print("Loading dataset configs from", path)
        import json

        with open(path, "r") as f:
            configs_root_dict: dict[str] = json.load(f)
        self.configs: cfg_type = {}

        def load_configs(target_dict: cfg_type, cfgs_dict: dict[str]):
            for name, cfg in cfgs_dict.items():
                if isinstance(cfg, dict):
                    if "is_config" in cfg and cfg["is_config"] is True:
                        # leaf config
                        target_dict[name] = DataConfig(**cfg)
                    else:
                        # nested configs
                        target_dict[name] = {}
                        load_configs(target_dict[name], cfg)

        load_configs(self.configs, configs_root_dict)

    def load_defaults(self):
        blast_furnace_sets = {}
        for normalize in {False, True}:
            for out_group in ["slag_alk", "alkper"]:
                for bas in range(2, 5):
                    for split in [0, 1]:
                        # example name: blast_furnace_alkper_BAS2_split_0_normalize_False
                        key = f"blast_furnace_{out_group}_BAS{bas}_split_{split}_normalize_{normalize}"
                        blast_furnace_sets[key] = DataConfig(
                            mode=os.getenv("EMBEDDING", "tsne"),
                            data_file=f"blast_furnace/parts/{key}.csv",
                            data_name=f"Blast Furnace Data Set, BAS{bas}, Split: {split}, Output Group: {out_group}, Normalized: {normalize}",
                            short_data_name=f"blast_furnace_split{split}_bas{bas}_{'norm' if normalize else 'nonorm'}_{out_group}",
                            input_cols=5,
                            output_cols=2,
                            time_col=0,
                            inputs_constrained=False,
                        )
        self.configs: dict[str, dict[str, DataConfig] | DataConfig] = {
            "scivis_2025": scivis_man,
            "privbayes": privbayes_man,
            "mast": mast_man,
            "electric_arc_furnace": eaf_man,
            "blast_furnace": blast_furnace_sets,
        }
        with open("configs.json", "w") as f:
            import json

            json.dump(self.configs, f, default=lambda o: o.__dict__, indent=4)

    def get_manager(self, name: str, load=False) -> DataMan | None:
        part_names = name.split(self.separator)
        manager = self.managers
        for part in part_names:
            if isinstance(manager, dict) and part in manager:
                manager = manager[part]
            else:
                return None
        if isinstance(manager, DataMan):
            if not manager.loaded and load:
                manager.load()
            return manager
        return None

    def get_managers(self) -> dict[str, DataMan]:
        sets: dict[str, DataMan] = {}

        def extract_managers(prefix: str, mgr_dict: dict):
            for key, value in mgr_dict.items():
                if isinstance(value, DataMan):
                    sets[f"{prefix}{key}"] = value
                elif isinstance(value, dict):
                    extract_managers(f"{prefix}{key}{self.separator}", value)

        extract_managers("", self.managers)
        return sets


sets_manager = SetsManager()
