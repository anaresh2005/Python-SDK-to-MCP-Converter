import os, importlib, inspect
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class MethodSpec:
    tool_name: str
    fn: Callable[..., Any]
    signature: inspect.Signature
    doc: str | None
    mode: str | None = None


HINTS = {
    "github": {
        "construct": "Github",
        "auth": "env: GITHUB_TOKEN",
    },
    "kubernetes": {
        "setup": "config.load_kube_config",
        "construct": "client.CoreV1Api",
    },
    "azure.storage.blob": {
        "construct": "BlobServiceClient.from_connection_string",
        "auth_env": ["AZURE_STORAGE_CONNECTION_STRING"],
    },
}


def _safe_signature(obj) -> inspect.Signature:
    try:
        return inspect.signature(obj)
    except Exception:
        return inspect.Signature(parameters=[])


def _tool_name(pkg: str, qual: str) -> str:
    return f"{pkg}.{qual}".replace(" ", "_").replace(".", "_")


def _collect_top_level_functions(pkg: str, mod):
    out = []
    for name, fn in inspect.getmembers(mod, inspect.isfunction):
        if name.startswith("_"):
            continue
        out.append(
            MethodSpec(
                tool_name=_tool_name(pkg, name),
                fn=fn,
                signature=_safe_signature(fn),
                doc=inspect.getdoc(fn),
            )
        )
    return out


def _collect_methods_from_instance(pkg: str, inst):
    out = []
    for name, member in inspect.getmembers(inst, predicate=callable):
        if name.startswith("_"):
            continue
        out.append(
            MethodSpec(
                tool_name=_tool_name(pkg, f"{inst.__class__.__name__}.{name}"),
                fn=member,
                signature=_safe_signature(member),
                doc=inspect.getdoc(member),
            )
        )
    return out


def _resolve_attr(root, dotted: str):
    obj = root
    for part in dotted.split("."):
        obj = getattr(obj, part)
    return obj


def _instantiate_hinted_client(pkg: str, mod):
    hint = HINTS.get(pkg)
    if not hint:
        return None
    setup_path = hint.get("setup")
    if setup_path:
        try:
            setup_fn = _resolve_attr(mod, setup_path)
            setup_fn()
        except Exception:
            pass

    construct_path = hint.get("construct")
    if not construct_path:
        return None
    try:
        ctor = _resolve_attr(mod, construct_path)
    except Exception:
        return None

    auth_env = hint.get("auth_env", [])
    if (
        not auth_env
        and isinstance(hint.get("auth"), str)
        and hint["auth"].startswith("env:")
    ):
        auth_env = [hint["auth"].split("env:", 1)[1].strip()]

    arg = next((os.environ.get(e) for e in auth_env if os.environ.get(e)), None)

    try:
        return ctor(arg) if arg is not None else ctor()
    except Exception:
        return None


def _zero_arg_instances(mod, max_instances: int = 3):
    out = []
    for name, cls in inspect.getmembers(mod, inspect.isclass):
        if name.startswith("_"):
            continue
        try:
            sig = inspect.signature(cls)
            if all(
                p.default is not inspect._empty
                or p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
                for p in sig.parameters.values()
            ):
                try:
                    out.append(cls())
                    if len(out) >= max_instances:
                        break
                except Exception:
                    pass
        except Exception:
            continue
    return out


def build_registry_from_package(package: str) -> dict[str, MethodSpec]:
    mod = importlib.import_module(package)
    reg: dict[str, MethodSpec] = {}

    for ms in _collect_top_level_functions(package, mod):
        reg[ms.tool_name] = ms

    hinted = _instantiate_hinted_client(package, mod)
    if hinted:
        for ms in _collect_methods_from_instance(package, hinted):
            reg[ms.tool_name] = ms

    for inst in _zero_arg_instances(mod):
        for ms in _collect_methods_from_instance(package, inst):
            reg[ms.tool_name] = ms

    return reg
