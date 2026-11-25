import numpy as np
import pytest

from benchmark.attributors import SCA, GradientUA, Predict0, SCAOracle
from benchmark.datasets import make_task
from benchmark.uq_models import UQModel


@pytest.fixture(scope="module")
def task_uq():
    task = make_task("polynomial", 0.5, 0, sizes=(300, 50, 50))
    uq = UQModel(epochs=20).fit(task.train.x_noisy, task.train.y, task.cal.x_noisy, task.cal.y)
    return task, uq


@pytest.mark.parametrize(
    "att",
    [SCA("gaussian"), SCA("knn"), SCAOracle(), GradientUA(), Predict0()],
    ids=["sca_gaussian", "sca_knn", "oracle", "gradient", "predict0"],
)
def test_attributor_smoke(task_uq, att):
    task, uq = task_uq
    out = np.asarray(att.attribute(task, uq))
    assert out.shape == (50, 2)
    assert np.all(np.isfinite(out))
    assert np.all(out >= 0)
