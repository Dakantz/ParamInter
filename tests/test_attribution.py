import numpy as np
import pytest

from ucq.conditioning import Condition


@pytest.fixture(scope="module")
def att(conditioner):
    return conditioner.attribute([Condition("a", 5.0), Condition("d", 0.0, width=0.5)], "c")


def test_schema(att, conditioner):
    T = len(conditioner.columns)
    assert att["target"] == "c"
    assert att["columns"] == conditioner.columns
    assert att["conditioned"] == ["a", "d"]
    for key in ("kind", "remove_std", "condition_effect", "add_std", "pin_gain", "explained_share"):
        assert len(att[key]) == T, key


def test_kinds_and_nulls(att):
    assert att["kind"] == ["conditioned", "free", "target", "conditioned"]
    for i, k in enumerate(att["kind"]):
        assert (att["remove_std"][i] is not None) == (k == "conditioned")
        assert (att["condition_effect"][i] is not None) == (k == "conditioned")
        assert (att["add_std"][i] is not None) == (k == "free")
        assert (att["pin_gain"][i] is not None) == (k == "free")
    for i, k in enumerate(att["kind"]):
        if k == "conditioned":
            assert att["condition_effect"][i] == pytest.approx(att["remove_std"][i] - att["base_std"])
        if k == "free":
            assert att["pin_gain"][i] == pytest.approx(att["base_std"] - att["add_std"][i])


def test_base_std_matches_predict(att, conditioner):
    res = conditioner.predict([Condition("a", 5.0), Condition("d", 0.0, width=0.5)])
    assert att["base_std"] == pytest.approx(res["std"][conditioner.columns.index("c")], rel=1e-6)


def test_removing_correlated_condition_increases_std(att):
    assert att["remove_std"][0] >= 0.99 * att["base_std"]


def test_pinning_correlated_column_helps(conditioner):
    res = conditioner.attribute([Condition("d", 0.0)], "c")
    for k in ("a", "b"):
        i = res["columns"].index(k)
        assert res["pin_gain"][i] >= -0.02 * res["base_std"]


def test_explained_share(att, conditioner):
    share = np.array(att["explained_share"])
    assert np.all((share >= 0) & (share <= 1))
    assert share[2] == 1.0
    assert share[0] == 0.0  # point conditioned
    unc = conditioner.attribute([], "c")
    assert unc["kind"] == ["free", "free", "target", "free"]
    assert unc["explained_share"][unc["columns"].index("b")] > 0.1


def test_unknown_target_or_column(conditioner):
    with pytest.raises(KeyError):
        conditioner.attribute([], "nope")
    with pytest.raises(KeyError):
        conditioner.attribute([Condition("nope", 1.0)], "c")
