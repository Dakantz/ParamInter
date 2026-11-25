from fastapi import APIRouter, HTTPException

from backend.datamans import sets_manager
from backend.models import ConditionRequest, ConditionResult, ConditionerStatus
from ucq.conditioning import Condition

conditioning_router = APIRouter(prefix="/conditioning")


def _manager(set_name: str):
    manager = sets_manager.get_manager(set_name)
    if manager is None:
        raise HTTPException(404, f"Unknown dataset {set_name}")
    return manager


@conditioning_router.get("/status")
def get_conditioner_status(set_name: str) -> ConditionerStatus:
    """Builds (training the GP-VAE if it is not cached yet) the conditioner for this dataset.
    Unlike the other views this does not need the dataset's embeddings to be `load`ed."""
    manager = _manager(set_name)
    if not manager.cfg.use_ucq or manager.cfg.vae_mode.value != "gpvae":
        return ConditionerStatus(
            available=False, reason="Dataset is not configured with use_ucq + gpvae."
        )
    cond = manager.get_conditioner()
    return ConditionerStatus(
        available=True, columns=cond.columns, bank_size=len(cond.bank_rows)
    )


@conditioning_router.post("/predict")
def predict_conditioned(set_name: str, req: ConditionRequest) -> ConditionResult:
    manager = _manager(set_name)
    cond = manager.get_conditioner()
    if cond is None:
        raise HTTPException(400, "Dataset has no GP-VAE conditioner (use_ucq + gpvae).")
    try:
        res = cond.predict(
            [Condition(c.column, c.value, c.width) for c in req.conditions],
            n_samples=req.n_samples,
            grid_points=req.grid_points,
            seed=req.seed,
        )
    except KeyError as e:
        raise HTTPException(400, str(e))
    return ConditionResult(
        input_cols=manager.input_cols, output_cols=manager.output_cols, **res
    )
