import os, importlib, inspect, yaml
from dataclasses import dataclass


@dataclass
class MethodSpec:
    tool_name: str
    mode: str
    fn: callable
    signature: inspect.Signature
    doc: str | None
    arg_hints: dict


def load_config(path: str) -> dict:
    with open(path, "r") as f:
        return yaml.safe_load(f)


def build_client(provider_cfg) -> object:
    mod = importlib.import_module(provider_cfg["import"])
    ctor = provider_cfg["construct"]

    obj = eval(f"mod.{ctor}")
    if "auth" in provider_cfg and "env:" in provider_cfg["auth"]:
        env_name = provider_cfg["auth"].split("env:")[1].strip()
        return obj(os.environ.get(env_name))
    return obj() if callable(obj) else obj


def collect_methods(cfg) -> list[MethodSpec]:
    methods = []
    for p in cfg["providers"]:
        client = build_client(p)
        for m in p["methods"]:
            fn = getattr(client, m["name"])
            methods.append(
                MethodSpec(
                    tool_name=m.get("rename", m["name"]),
                    mode=m.get("mode", "read"),
                    fn=fn,
                    signature=inspect.signature(fn),
                    doc=inspect.getdoc(fn),
                    arg_hints=m.get("args", {}),
                )
            )
    return methods
