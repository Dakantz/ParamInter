from sklearn.base import TransformerMixin
from sklearn.preprocessing import MinMaxScaler, StandardScaler
import umap
import lightgbm as lgb

from backend.utils import Singleton


try:
    from cuml.neighbors import NearestNeighbors
    from cuml.manifold.umap import UMAP
    from cuml import TSNE
except ImportError:
    from sklearn.neighbors import NearestNeighbors
    from sklearn.manifold import TSNE
    from umap import UMAP

    print("Cuml not found, using CPU-based libraries.")
    cuml = None

from .col_defs import column_types, input_types
import pandas as pd
import numpy as np

import tqdm
from pathlib import Path


# https://stackoverflow.com/questions/6760685/what-is-the-best-way-of-implementing-a-singleton-in-python
class DataMan:
    def __init__(self, data_table: str = "./alloy_data.txt", mode="tsne"):
        self.data_table = data_table
        self.mode = mode

    def load(self):
        data = pd.read_table(self.data_table)
        input_cols = data.columns.to_list()[:6]
        output_cols = data.columns.to_list()[6:70]
        cleaned = data[input_cols + output_cols].fillna(0)

        nn = NearestNeighbors(n_neighbors=1)
        nn.fit(cleaned[output_cols].values)

        nn_inputs = NearestNeighbors(n_neighbors=1)
        nn_inputs.fit(cleaned[input_cols].values)

        scaler_outs = StandardScaler()
        scaled_outputs = scaler_outs.fit_transform(cleaned[output_cols].values)

        embedding_subsets: dict[str, np.ndarray] = {}
        dim_reducers: dict[str, TransformerMixin] = {}
        for col_name, col_list in tqdm.tqdm(
            column_types.items(), desc="Creating embeddings"
        ):
            data_path = Path(f"data/{col_name}_{self.mode}.npy")
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
        for output_col in tqdm.tqdm(output_cols, desc="Loading models"):
            col_name = output_col.encode("ascii", "ignore").decode("ascii")
            col_name = col_name.replace(" ", "_")
            col_name = col_name.replace(".", "_")
            col_name = col_name.replace("/", "_")
            model = lgb.Booster(
                model_file=f"models/{col_name}_model.txt",
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
        
        self.column_types = column_types

dataman = DataMan()
dataman.load()