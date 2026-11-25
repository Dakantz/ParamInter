"""Benchmark for input uncertainty attribution mechanisms (iUCAMs).

Simulates (or injects) known heteroscedastic input noise sigma_x(x), trains uncertainty-aware
models on the noisy data, lets every attributor estimate the per-feature input uncertainty of
held-out samples and scores the estimates against the ground truth with ranking metrics
(P/R/F1@k, NDCG@k, AP, Spearman, cell AUROC) and, for magnitude-calibrated methods, the MSE
score s_l2 of Kantz et al., "Input Uncertainty Attribution by Uncertainty Propagation"
(ICASSP 2025).

Run ``python -m benchmark.run --help``.
"""
