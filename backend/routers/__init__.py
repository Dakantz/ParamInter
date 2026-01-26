from fastapi import APIRouter
from .sets import sets_router
from .data import data_router
from .datapoint import dp_router


grouped_sets_router = APIRouter(prefix="/datasets/{set_name}")
grouped_sets_router.include_router(data_router)
grouped_sets_router.include_router(dp_router)
