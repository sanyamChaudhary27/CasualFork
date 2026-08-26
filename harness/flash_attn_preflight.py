"""Pre-model-load flash-attn environment probe.

This is deliberately separate from SC1 validation: dependency bring-up errors
are reported as ENV_BRINGUP_FAILURE, never as coupling failures.
"""
from __future__ import annotations

import importlib
import json


ENV_BRINGUP_FAILURE = "ENV_BRINGUP_FAILURE"


def probe():
    try:
        module = importlib.import_module("flash_attn")
        version = getattr(module, "__version__", None)
        if not version:
            raise RuntimeError("flash_attn.__version__ is missing/empty")
        return {"status": "PASS", "package": "flash_attn", "version": str(version)}
    except Exception as exc:
        return {
            "status": ENV_BRINGUP_FAILURE,
            "package": "flash_attn",
            "error_type": type(exc).__name__,
            "error": str(exc),
        }


def main():
    report = probe()
    print(json.dumps(report, sort_keys=True))
    raise SystemExit(0 if report["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
