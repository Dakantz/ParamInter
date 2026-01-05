from sklearn.base import TransformerMixin
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import umap
import lightgbm as lgb

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
class DataMan:
    def __init__(
        self,
        base_dir: str = "data",
        mode="tsne",
        data_file="./alloy_data.txt",
        data_name="Aloy Data",
        short_data_name="scivis",
        input_cols=6,
        output_cols=64,
        time_col: int | None = None,
    ):
        self.base_dir = Path(base_dir)
        self.mode = mode
        self.data_file = data_file
        self.data_name = data_name
        self.short_data_name = short_data_name
        self.input_cols = input_cols
        self.output_cols = output_cols
        self.dataset_path = Path(base_dir) / Path("datasets") / Path(short_data_name)
        self.time_col = time_col

    def load(self):
        print(f"Loading dataset from {self.data_file}...")

        if self.dataset_path.exists() is False:
            os.makedirs(self.dataset_path)

        if self.data_file.endswith(".csv"):
            data = pd.read_csv(self.data_file)
        else:
            data = pd.read_table(self.data_file)

        input_cols = data.columns.to_list()[self.time_col + 1 : self.input_cols + 1]
        output_cols = data.columns.to_list()[
            self.input_cols + 1 : self.input_cols + 1 + self.output_cols
        ]
        cleaned = data[input_cols + output_cols].fillna(0)

        if self.time_col is not None:
            time = data.iloc[:, self.time_col]
        else:
            time = None

        nn = NearestNeighbors(n_neighbors=1)
        nn.fit(cleaned[output_cols].values)

        nn_inputs = NearestNeighbors(n_neighbors=1)
        nn_inputs.fit(cleaned[input_cols].values)

        scaler_outs = StandardScaler()
        scaled_outputs = scaler_outs.fit_transform(cleaned[output_cols].values)

        embedding_subsets: dict[str, np.ndarray] = {}
        dim_reducers: dict[str, TransformerMixin] = {}

        self.column_types_loaded = column_types
        if self.short_data_name != "scivis":
            # For other datasets, use all columns as a single type
            self.column_types_loaded = {
                "Input": input_cols,
                "All": input_cols + output_cols,
                "Output": output_cols,
            }

        for col_name, col_list in tqdm.tqdm(
            self.column_types_loaded.items(), desc="Creating embeddings"
        ):
            data_path = self.dataset_path / Path(f"{col_name}_{self.mode}.npy")
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
                    cleaned[col_list].values
                )
                scaled_tsne = MinMaxScaler().fit_transform(embedded_tsne)
                np.save(data_path, scaled_tsne)
                embedding_subsets[col_name] = scaled_tsne

        model_ensemble: dict[str, lgb.LGBMRegressor] = {}
        models_path = self.dataset_path / Path("models")
        if not models_path.exists():
            os.makedirs(models_path)
        for output_col in tqdm.tqdm(output_cols, desc="Loading models"):
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
                    cleaned[input_cols].values,
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
        self.cleaned = cleaned

        self.input_cols = input_cols
        self.output_cols = output_cols

        self.column_types = self.column_types_loaded


scivis_man = DataMan(
    base_dir=os.getenv("DATA_DIR", "./data"), mode=os.getenv("EMBEDDING", "tsne")
)
# scivis_man.load()

privbayes_man = DataMan(
    base_dir=os.getenv("DATA_DIR", "./data"),
    mode=os.getenv("EMBEDDING", "tsne"),
    data_file="./privbayes_encoded.csv",
    data_name="PrivBayes Data",
    short_data_name="privbayes",
    input_cols=18,
    output_cols=27,
    time_col=0,
)
# privbayes_man.load()


mast_man = DataMan(
    base_dir=os.getenv("DATA_DIR", "./data"),
    mode=os.getenv("EMBEDDING", "tsne"),
    data_file="./data/mast/processed_mast_data.csv",
    data_name="MAST Data",
    short_data_name="mast",
    input_cols=8,
    output_cols=10,
    time_col=0,
)
mast_man.load()

data_man = mast_man
