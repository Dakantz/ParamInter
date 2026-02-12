import os
from pathlib import Path
from .modelman import ModelManager
from .config import DataConfig


cfg_type = dict[str, dict[str, DataConfig] | DataConfig]


scivis_man = DataConfig(mode=os.getenv("EMBEDDING", "tsne"))

privbayes_man = DataConfig(
    mode=os.getenv("EMBEDDING", "tsne"),
    data_file="privbayes/privbayes_encoded.csv",
    data_name="PrivBayes Data",
    short_data_name="privbayes",
    input_cols=18,
    output_cols=27,
    time_col=0,
)


mast_man = DataConfig(
    mode=os.getenv("EMBEDDING", "tsne"),
    data_file="mast/processed_mast_data.csv",
    data_name="MAST Data",
    short_data_name="mast",
    input_cols=8,
    output_cols=10,
    time_col=0,
)

eaf_man = DataConfig(
    mode=os.getenv("EMBEDDING", "tsne"),
    data_file="eaf/eaf_simulation_data.csv",
    data_name="Electric Arc Furnace Simulation Data",
    short_data_name="eaf",
    input_cols=6,
    output_cols=51,
    time_col=0,
    inputs_constrained=False,
)


class SetsManager:
    def __init__(self, separator: str = "-"):
        configs_json = os.getenv("SETS_CONFIG_JSON", None)
        if configs_json is not None and Path(configs_json).exists():
            self.load_config_file(configs_json)
        else:
            print("Using default dataset configs.")
            self.load_defaults()

        self.managers: dict[str, dict[str,] | ModelManager] = {}
        for name, cfg in self.configs.items():
            if isinstance(cfg, dict):
                self.managers[name] = {}
                for sub_name, sub_cfg in cfg.items():
                    self.managers[name][sub_name] = ModelManager(sub_cfg)
            else:
                self.managers[name] = ModelManager(cfg)
        self.separator = separator

    def load_config_file(self, path: str):
        print("Loading dataset configs from", path)
        import json

        with open(path, "r") as f:
            configs_root_dict: dict[str] = json.load(f)
        self.configs: cfg_type = {}

        def load_configs(target_dict: cfg_type, cfgs_dict: dict[str]):
            for name, cfg in cfgs_dict.items():
                if isinstance(cfg, dict):
                    if "is_config" in cfg and cfg["is_config"] is True:
                        # leaf config
                        target_dict[name] = DataConfig(**cfg)
                    else:
                        # nested configs
                        target_dict[name] = {}
                        load_configs(target_dict[name], cfg)

        load_configs(self.configs, configs_root_dict)

    def load_defaults(self):
        blast_furnace_sets = {}
        for normalize in {False, True}:
            for out_group in ["slag_alk", "alkper"]:
                for bas in range(2, 5):
                    for split in [0, 1]:
                        # example name: blast_furnace_alkper_BAS2_split_0_normalize_False
                        key = f"blast_furnace_{out_group}_BAS{bas}_split_{split}_normalize_{normalize}"
                        blast_furnace_sets[key] = DataConfig(
                            mode=os.getenv("EMBEDDING", "tsne"),
                            data_file=f"blast_furnace/parts/{key}.csv",
                            data_name=f"Blast Furnace Data Set, BAS{bas}, Split: {split}, Output Group: {out_group}, Normalized: {normalize}",
                            short_data_name=f"blast_furnace_split{split}_bas{bas}_{'norm' if normalize else 'nonorm'}_{out_group}",
                            input_cols=6,
                            output_cols=2,
                            time_col=0,
                            inputs_constrained=False,
                            use_ucq=True,
                        )
        self.configs: dict[str, dict[str, DataConfig] | DataConfig] = {
            "scivis_2025": scivis_man,
            "privbayes": privbayes_man,
            "mast": mast_man,
            "electric_arc_furnace": eaf_man,
            "blast_furnace": blast_furnace_sets,
        }
        with open("configs.json", "w") as f:
            import json

            json.dump(
                self.configs,
                f,
                default=lambda o: o.__dict__ if isinstance(o, DataConfig) else o,
                indent=4,
            )

    def get_manager(self, name: str, load=False) -> ModelManager | None:
        part_names = name.split(self.separator)
        manager = self.managers
        for part in part_names:
            if isinstance(manager, dict) and part in manager:
                manager = manager[part]
            else:
                return None
        if isinstance(manager, ModelManager):
            if not manager.loaded and load:
                manager.load()
            return manager
        return None

    def get_managers(self) -> dict[str, ModelManager]:
        sets: dict[str, ModelManager] = {}

        def extract_managers(prefix: str, mgr_dict: dict):
            for key, value in mgr_dict.items():
                if isinstance(value, ModelManager):
                    sets[f"{prefix}{key}"] = value
                elif isinstance(value, dict):
                    extract_managers(f"{prefix}{key}{self.separator}", value)

        extract_managers("", self.managers)
        return sets


sets_manager = SetsManager()
