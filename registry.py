from loader import load_config, collect_methods


def build_registry(config_path: str) -> dict:
    cfg = load_config(config_path)
    methods = collect_methods(cfg)
    return {ms.tool_name: ms for ms in methods}
