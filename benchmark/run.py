"""Run the iUCAM benchmark.

Example (quick):
    python -m benchmark.run --datasets polynomial,styblinski_tang:4 --levels 0.3,0.6 --seeds 2

Full:
    python -m benchmark.run --datasets polynomial,polynomial_gmm,styblinski_tang:4,\
styblinski_tang:8,gas_turbine --levels 0.2,0.4,0.6,0.8 --seeds 5 --methods all

Writes ``<out>/results.jsonl`` (one row per dataset x level x seed x method, all metrics) and
``<out>/summary.md`` (mean +- std over seeds per dataset / level / method).
"""

from __future__ import annotations

import argparse
import json
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

from benchmark.attributors import REGISTRY
from benchmark.datasets import make_task
from benchmark.metrics import rank_metrics
from benchmark.uq_models import UQModel

DEFAULT_METHODS = "sca_gaussian,sca_knn,sca_oracle,gradient,shap,vae,gpvae,gpvae_cond,predict0,random"
SUMMARY_METRICS = ["F1@1", "F1@2", "P@2", "R@2", "NDCG@3", "AP", "Hit@1", "Spearman", "AUROC", "s_l2"]


def run(args) -> pd.DataFrame:
    methods = DEFAULT_METHODS.split(",") if args.methods == "all" else args.methods.split(",")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    with open(out / "results.jsonl", "w") as fh:
        for spec in args.datasets.split(","):
            for level in [float(v) for v in args.levels.split(",")]:
                for seed in range(args.seeds):
                    task = make_task(spec, level, seed, sizes=(args.n_train, args.n_cal, args.n_test))
                    t0 = time.time()
                    uq = UQModel(epochs=args.nn_epochs, hidden=args.hidden, seed=seed).fit(
                        task.train.x_noisy, task.train.y, task.cal.x_noisy, task.cal.y
                    )
                    r2 = uq.r2(task.test.x_noisy, task.test.y)
                    print(f"[{task.name} l={level} seed={seed}] NN R2={r2:.3f} calib={uq.calib:.2f} "
                          f"({time.time() - t0:.1f}s)", flush=True)
                    sigma_z = task.test.sigma_x / task.x_std
                    for m in methods:
                        att = REGISTRY[m]()
                        if att.needs_oracle and task.g_torch is None:
                            continue
                        t0 = time.time()
                        try:
                            score = att.attribute(task, uq)
                        except Exception:
                            traceback.print_exc()
                            continue
                        met = rank_metrics(sigma_z, score, ks=args.ks, rel_threshold=args.rel_threshold)
                        if not att.calibrated:
                            met["s_l2"] = float("nan")
                        row = {
                            "dataset": task.name, "level": level, "seed": seed, "method": att.name,
                            "calibrated": att.calibrated, "nn_r2": r2, "seconds": time.time() - t0, **met,
                        }
                        rows.append(row)
                        fh.write(json.dumps(row) + "\n")
                        fh.flush()
                        print(f"    {att.name:32s} F1@1={met.get('F1@1', np.nan):.3f} "
                              f"AP={met['AP']:.3f} Spearman={met['Spearman']:.3f} "
                              f"s_l2={met['s_l2']:.4f} ({row['seconds']:.1f}s)", flush=True)
    df = pd.DataFrame(rows)
    if df.empty:
        print("No results (every attributor failed?)")
        return df
    write_summary(df, out / "summary.md")
    return df


def write_summary(df: pd.DataFrame, path: Path):
    metrics = [m for m in SUMMARY_METRICS if m in df.columns]
    lines = ["# iUCAM benchmark summary", "",
             "Mean ± std over seeds. Ranking metrics use standardised input units; "
             "s_l2 (MSE vs. true sigma_x) only for calibrated methods.", ""]
    for (ds, level), g in df.groupby(["dataset", "level"], sort=False):
        lines += [f"## {ds} — noise level {level}", "",
                  "| method | " + " | ".join(metrics) + " |",
                  "|---|" + "---|" * len(metrics)]
        agg = g.groupby("method", sort=False)[metrics].agg(["mean", "std"])
        for method in agg.index:
            cells = []
            for m in metrics:
                mu, sd = agg.loc[method, (m, "mean")], agg.loc[method, (m, "std")]
                cells.append("–" if np.isnan(mu) else f"{mu:.3f}" + ("" if np.isnan(sd) else f" ± {sd:.3f}"))
            lines.append(f"| {method} | " + " | ".join(cells) + " |")
        lines.append("")
    path.write_text("\n".join(lines))
    print(f"Summary written to {path}")


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--datasets", default="polynomial,polynomial_gmm,styblinski_tang:4")
    p.add_argument("--levels", default="0.3,0.6")
    p.add_argument("--seeds", type=int, default=3)
    p.add_argument("--methods", default="all", help=f"comma list of {','.join(REGISTRY)} or 'all'")
    p.add_argument("--ks", type=lambda s: [int(v) for v in s.split(",")], default=[1, 2, 3])
    p.add_argument("--rel-threshold", type=float, default=0.5)
    p.add_argument("--n-train", type=int, default=5000)
    p.add_argument("--n-cal", type=int, default=500)
    p.add_argument("--n-test", type=int, default=500)
    p.add_argument("--nn-epochs", type=int, default=150)
    p.add_argument("--hidden", type=int, default=64)
    p.add_argument("--out", default="benchmark/results")
    run(p.parse_args())


if __name__ == "__main__":
    main()
