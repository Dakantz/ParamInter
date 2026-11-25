import numpy as np
import pytest

from benchmark.metrics import rank_metrics


def test_perfect_scores():
    rng = np.random.default_rng(0)
    sigma = rng.uniform(0.01, 1, size=(20, 5))
    # AUROC is pooled over cells while relevance is relative to each row's max, so rows need a
    # common scale for a perfect score to separate the classes perfectly
    sigma /= sigma.max(1, keepdims=True)
    m = rank_metrics(sigma, sigma.copy(), ks=(1, 2, 3))
    for key in ("P@1", "AP", "Hit@1", "Spearman", "AUROC", "NDCG@1", "NDCG@2", "NDCG@3"):
        assert m[key] == pytest.approx(1.0), key
    assert m["s_l2"] == 0.0


def test_zero_scores_are_pessimistic():
    sigma = np.array([[3.0, 2.0, 1.0, 0.1], [0.1, 1.0, 5.0, 0.2]])
    m = rank_metrics(sigma, np.zeros_like(sigma), ks=(1, 2))
    assert m["P@1"] == 0.0
    assert m["Hit@1"] == 0.0
    assert m["Spearman"] == 0.0


def test_hand_checked_example():
    # relevant (>= 0.5 * max = 1.5): features 0 and 1
    sigma = np.array([[3.0, 2.0, 1.0, 0.1]])
    # predicted order: 1, 2, 3, 0 -> relevance T, F, F, T
    score = np.array([[1.0, 4.0, 3.0, 2.0]])
    m = rank_metrics(sigma, score, ks=(1, 2, 3))
    assert m["P@1"] == pytest.approx(1.0)
    assert m["R@1"] == pytest.approx(0.5)
    assert m["F1@1"] == pytest.approx(2 / 3)
    assert m["P@2"] == pytest.approx(0.5)
    assert m["R@2"] == pytest.approx(0.5)
    assert m["F1@2"] == pytest.approx(0.5)
    assert m["P@3"] == pytest.approx(1 / 3)
    assert m["R@3"] == pytest.approx(0.5)
    assert m["F1@3"] == pytest.approx(0.4)
    assert m["AP"] == pytest.approx((1 / 1 + 2 / 4) / 2)
    assert m["Hit@1"] == 0.0
