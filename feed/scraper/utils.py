import json

def build_api_params(raw_params: dict) -> dict:
    # Deep copy the dict so we don’t mutate the config file
    params = raw_params.copy()
    if isinstance(params.get("query"), dict):
        params["query"] = json.dumps(params["query"])
    return params