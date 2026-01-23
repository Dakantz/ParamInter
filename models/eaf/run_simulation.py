# %%
from random import seed
import torch as pt
from tqdm import tqdm
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from dataclasses import asdict
import os
import pandas as pd

from sklearn.model_selection import ParameterGrid

import scipy.stats.qmc as qm

from system_model import EAFModel, EAFParameters, step_eaf, TakeoutAnalysis
import argparse

# %%
param_grid = {
    "O2_lance": [1.5, 2, 4, 6, 8],
    "P_arc": [30000, 35000, 40000, 55000, 75000],
    "O2_post": [0.5, 0.75, 1, 1.5, 2],
    "C_inj": [0.2, 0.25, 0.3, 0.5, 0.8],
    "FM_inj": [0.75, 1, 1.5, 2, 2.5],
    "DRI_add": [96, 110, 150],
}
sampler = qm.LatinHypercube(
    d=len(param_grid), rng=np.random.Generator(np.random.PCG64(42))
)


def run_sample(params: dict) -> dict:
    test_params = EAFParameters()
    y_values = asdict(test_params)
    y_values = [
        y_val
        for y_val in y_values.keys()
        if y_val.startswith("T_") or y_val.startswith("MX_")
    ]
    eaf_params = EAFParameters()
    for k, v in params.items():
        setattr(eaf_params, k, v)
    eaf_params.x_names = params.keys()

    print(f"Running simulation with params: {params}")
    print(f"Y values to record: {y_values}")
    model = EAFModel(eaf_params)
    for s in tqdm(range(int(model.p.secs // model.p.ts))):
        step_eaf(model)

    result = {
        **params,
        **{
            y: getattr(model.p, y)
            for y in y_values
            if y.startswith("T_") or y.startswith("MX_")
        },
    }
    for k, v in result.items():
        if isinstance(v, pt.Tensor):
            result[k] = v.item()
    return result


parser = argparse.ArgumentParser()
parser.add_argument(
    "--samples",
    type=int,
    default=100,
    help="Number of samples to run",
)
parser.add_argument(
    "--sample",
    type=int,
    default=1,
    help="Sample ID to run",
)
if __name__ == "__main__":
    args = parser.parse_args()
    n_samples = args.samples
    sample_id = args.sample
    print(f"Running sample {sample_id} of {n_samples}")
    samples = sampler.random(n=n_samples)
    samples = qm.scale(
        samples,
        l_bounds=[min(v) for v in param_grid.values()],
        u_bounds=[max(v) for v in param_grid.values()],
    )
    samples_df = pd.DataFrame(samples, columns=list(param_grid.keys()))
    result = run_sample(samples_df.iloc[sample_id].to_dict())

    print(f"Sample {sample_id} result: {result}")

    result_df = pd.DataFrame([result])
    output_file = f"results/eaf_simulation_result_{sample_id}.csv"
    result_df.to_csv(output_file, index=False)
    print(f"Result saved to {output_file}")
