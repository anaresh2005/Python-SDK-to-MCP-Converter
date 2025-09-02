import inspect, json


def _jsonable(obj):
    try:
        json.dumps(obj)
    except Exception:
        try:
            raw = getattr(obj, "raw_data", None) or getattr(obj, "raw_attributes", None)
            if raw is not None:
                json.dumps(raw)
                return raw
        except Exception:
            pass
    return repr(obj)


def call_tool(method_spec, payload: dict):
    payload = dict(payload or {})
    dry_run = bool(payload.pop("dry_run", False))
    confirm = bool(payload.pop("confirm", False))
    if method_spec.mode == "write" and not (dry_run or confirm):
        return {
            "error": "This tool is 'write' mode. Provide {'confirm': true} (or 'dry_run': true) to proceed."
        }
    sig = method_spec.signature
    try:
        bound = sig.bind_partial(**payload)
        bound.apply_defaults()
    except TypeError as e:
        return {"error": f"Argument binding failed: {e}"}
    if dry_run:
        return {
            "dry_run": True,
            "tool": method_spec.tool_name,
            "would_call": f"{method_spec.fn.__qualname__}({', '.join(f'{k}={v!r}' for k,v in bound.arguments.items())})",
        }
    try:
        result = method_spec.fn(**bound.arguments)
    except Exception as e:
        return {"error": f"SDK call raised: {type(e).__name__}: {e}"}
    try:
        return {"ok": True, "data": _jsonable(result)}
    except Exception as e:
        return {
            "ok": True,
            "data": repr(result),
            "warning": f"Result not fully JSON-serializable: {e}",
        }
