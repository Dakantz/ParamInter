"""API tests against the real routers with a stubbed dataset manager (no dataset loading)."""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client(conditioner):
    from backend import app
    from backend.datamans import sets_manager

    stub = SimpleNamespace(
        cfg=SimpleNamespace(use_ucq=True, vae_mode=SimpleNamespace(value="gpvae")),
        input_cols=["a", "b"],
        output_cols=["c", "d"],
        get_conditioner=lambda: conditioner,
    )
    mp = pytest.MonkeyPatch()
    mp.setattr(sets_manager, "get_manager", lambda name, load=False: stub if name == "toy" else None)
    yield TestClient(app)
    mp.undo()


def test_status(client):
    r = client.get("/datasets/toy/conditioning/status")
    assert r.status_code == 200
    assert r.json()["available"] is True
    assert r.json()["columns"] == ["a", "b", "c", "d"]


def test_predict(client):
    r = client.post(
        "/datasets/toy/conditioning/predict",
        json={"conditions": [{"column": "a", "value": 5.0}], "n_samples": 8, "grid_points": 20},
    )
    assert r.status_code == 200
    d = r.json()
    assert d["conditioned"] == ["a"]
    assert len(d["samples"]) == 8 and len(d["grid"][0]) == 20
    assert d["input_cols"] == ["a", "b"]


def test_attribution(client):
    r = client.post(
        "/datasets/toy/conditioning/attribution",
        json={"conditions": [{"column": "a", "value": 5.0}, {"column": "d", "value": 0, "width": 0.5}], "target": "c"},
    )
    assert r.status_code == 200
    d = r.json()
    assert set(d) == {
        "target", "columns", "conditioned", "kind", "base_std", "remove_std",
        "condition_effect", "add_std", "pin_gain", "explained_share",
    }
    assert d["kind"] == ["conditioned", "free", "target", "conditioned"]
    assert d["remove_std"][1] is None and d["add_std"][1] is not None


def test_errors(client):
    assert client.post("/datasets/toy/conditioning/attribution", json={"target": "nope"}).status_code == 400
    r = client.post(
        "/datasets/toy/conditioning/attribution",
        json={"conditions": [{"column": "nope", "value": 1}], "target": "c"},
    )
    assert r.status_code == 400
    assert client.post("/datasets/toy/conditioning/predict", json={"conditions": [{"column": "nope", "value": 1}]}).status_code == 400
    assert client.post("/datasets/other/conditioning/attribution", json={"target": "c"}).status_code == 404
