from fastapi import APIRouter

from backend.dataman import ManagerSettings, SetsManager, sets_manager

sets_router = APIRouter(prefix="/datasets")


@sets_router.get("/")
def get_datasets() -> dict[str, ManagerSettings]:
    managers = sets_manager.get_managers()
    settings = {}
    for name, mgr in managers.items():
        settings[name] = mgr.get_settings()
    return settings


@sets_router.post("/load/{set_name}")
def load_dataset(set_name: str) -> ManagerSettings:
    manager = sets_manager.get_manager(set_name)
    if not manager.loaded:
        manager.load()
    return manager.get_settings()


@sets_router.get("/{set_name}")
def get_set(set_name: str, load: bool = False) -> ManagerSettings:
    manager = sets_manager.get_manager(set_name, load=load)
    return manager.get_settings()
