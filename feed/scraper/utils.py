import json
from pathlib import Path
from typing import Any, Union

def build_api_params(raw_params: dict) -> dict:
    # Deep copy the dict so we don’t mutate the config file
    params = raw_params.copy()
    if isinstance(params.get("query"), dict):
        params["query"] = json.dumps(params["query"])
    return params

def load_config(path: Union[str, Path]) -> Any:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)