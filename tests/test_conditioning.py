import numpy as np
import pytest

from ucq.conditioning import Condition


def test_no_conditions_uniform(conditioner):
    w, means, covs, beta = conditioner.mixture([])
    K = len(conditioner.bank_rows)
    assert w.shape == (K,)
    assert np.allclose(w.numpy(), 1.0 / K)
    assert beta == 1.0
    res = conditioner.predict([])
    assert res["ess"] == pytest.approx(K)
    assert res["conditioned"] == []


def test_point_condition_pins_column(conditioner):
    j = conditioner.columns.index("a")
    res = conditioner.predict([Condition("a", 5.0)])
    assert res["mean"][j] == pytest.approx(5.0, abs=0.05 * conditioner.diff[j])
    assert res["std"][j] < 0.01 * conditioner.diff[j]
    assert res["conditioned"] == ["a"]


def test_range_condition_between_point_and_prior(conditioner):
    j = conditioner.columns.index("a")
    point = conditioner.predict([Condition("a", 5.0)])["std"][j]
    rng = conditioner.predict([Condition("a", 5.0, width=4.0)])["std"][j]
    prior = conditioner.predict([])["std"][j]
    assert point < rng < prior


def test_densities_integrate_to_one(conditioner):
    for conds in ([], [Condition("a", 5.0, width=4.0)]):
        res = conditioner.predict(conds, grid_points=200)
        grid, dens = np.array(res["grid"]), np.array(res["density"])
        mass = np.trapezoid(dens, grid, axis=1)
        assert np.all(np.abs(mass - 1) < 0.1), mass


def test_unknown_column_raises(conditioner):
    with pytest.raises(KeyError):
        conditioner.mixture([Condition("nope", 1.0)])
