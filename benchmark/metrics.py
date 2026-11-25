"""Ranking metrics for per-sample input uncertainty attributions.

Ground truth: ``sigma`` (n, d) true input noise std, ``score`` (n, d) attribution, both in
standardised input units. Per sample ``i`` the *relevant* (uncertain) features are

    R_i = { j : sigma_ij >= rel_threshold * max_j sigma_ij }

and the predicted ranking is the descending order of ``score_i``. Ties in the score (e.g. the
"Predict 0" baseline) are broken pessimistically, so constant predictions do not get lucky.

Per sample metrics (averaged over samples):
  P@k, R@k, F1@k  - precision / recall / F1 of the top-k predicted features vs R_i
  NDCG@k          - graded relevance sigma_ij
  AP              - average precision of the full ranking vs R_i
  Hit@1           - is the top predicted feature the most uncertain one
  Spearman        - rank correlation between score_i and sigma_i
Global:
  AUROC           - cell-level separation of relevant vs non-relevant (i, j) cells
  s_l2            - MSE between score and sigma (only meaningful for calibrated methods)
"""

from __future__ import annotations

import numpy as np
from scipy.stats import rankdata, spearmanr
from sklearn.metrics import roc_auc_score


def _pessimistic_order(score: np.ndarray, sigma: np.ndarray) -> np.ndarray:
    # sort by score desc; among ties put the *least* relevant first
    return np.lexsort((sigma, -score))


def rank_metrics(
    sigma: np.ndarray, score: np.ndarray, ks=(1, 2, 3), rel_threshold: float = 0.5
) -> dict[str, float]:
    sigma = np.asarray(sigma, dtype=np.float64)
    score = np.nan_to_num(np.asarray(score, dtype=np.float64), nan=0.0)
    n, d = sigma.shape
    rel = sigma >= rel_threshold * sigma.max(1, keepdims=True)
    ks = [k for k in ks if k <= d]
    acc: dict[str, list[float]] = {}

    def add(key, val):
        acc.setdefault(key, []).append(val)

    for i in range(n):
        order = _pessimistic_order(score[i], sigma[i])
        r = rel[i]
        n_rel = r.sum()
        for k in ks:
            hits = r[order[:k]].sum()
            p, rc = hits / k, hits / n_rel
            add(f"P@{k}", p)
            add(f"R@{k}", rc)
            add(f"F1@{k}", 0.0 if p + rc == 0 else 2 * p * rc / (p + rc))
            gains = sigma[i, order[:k]]
            ideal = np.sort(sigma[i])[::-1][:k]
            disc = 1 / np.log2(np.arange(2, k + 2))
            add(f"NDCG@{k}", float((gains * disc).sum() / max((ideal * disc).sum(), 1e-12)))
        hits_cum = np.cumsum(r[order])
        add("AP", float((hits_cum / np.arange(1, d + 1))[r[order]].sum() / n_rel))
        add("Hit@1", float(order[0] == np.argmax(sigma[i])))
        if np.ptp(score[i]) > 0 and np.ptp(sigma[i]) > 0:
            add("Spearman", float(spearmanr(score[i], sigma[i]).statistic))
        else:
            add("Spearman", 0.0)

    out = {k: float(np.mean(v)) for k, v in acc.items()}
    flat_rel = rel.ravel()
    if flat_rel.any() and not flat_rel.all():
        # pessimistic tie handling for AUROC via ranks with jitter-free average ranks
        out["AUROC"] = float(roc_auc_score(flat_rel, rankdata(score.ravel())))
    out["s_l2"] = float(((score - sigma) ** 2).mean())
    return out
