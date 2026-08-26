"""SC1 environment fingerprint (CausalFork STAGE-B/C fix round, target 10).

Captures the software identity a strict-coupling ledger was produced under.
Used by the validator meta check: the values embedded in each ledger meta line
must agree with the pair manifest and across branches. Every probe degrades
gracefully: an absent optional package is recorded as None (never guessed),
so validation remains possible on machines where e.g. diffusers is missing.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys

UPSTREAM_PIN = "74d268516d95c8fceadd2378f91a73f9f187042b"
PATCH_ID = "evoke-74d26851-strict-coupling"
SCHEMA = "causalfork/env-fingerprint@1"


def _try_version(module_name):
    """Best-effort version string; None when the module is not importable."""
    try:
        mod = __import__(module_name)
        return getattr(mod, "__version__", None)
    except Exception:
        return None


def cuda_runtime():
    """CUDA runtime availability via torch; None when torch itself is absent."""
    try:
        import torch
    except Exception:
        return None
    try:
        return str(torch.version.cuda) if torch.version.cuda else None
    except Exception:
        return None


def gpu_name():
    try:
        import torch
    except Exception:
        return None
    try:
        if not torch.cuda.is_available():
            return None
        return torch.cuda.get_device_name(0)
    except Exception:
        return None


def torch_version():
    try:
        import torch
        return str(torch.__version__)
    except Exception:
        return None


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def bytes_sha256(data):
    return hashlib.sha256(data).hexdigest()


def fingerprint(patch_sha=None, upstream_pin=UPSTREAM_PIN):
    """Snapshot of the runtime identity. No timestamps: byte-stable per env."""
    np_ver = _try_version("numpy")
    return {
        "schema": SCHEMA,
        "patch_id": PATCH_ID,
        "upstream_pin": upstream_pin,
        "python": sys.version.split()[0],
        "python_impl": platform.python_implementation(),
        "platform": platform.platform(),
        "torch": torch_version(),
        "cuda_runtime": cuda_runtime(),
        "gpu": gpu_name(),
        "diffusers": _try_version("diffusers"),
        "transformers": _try_version("transformers"),
        "numpy": np_ver,
        "patch_sha256": patch_sha,
    }


def to_json(fp):
    return json.dumps(fp, sort_keys=True, separators=(",", ":"))


def diffusers_string_or_undeclared():
    """Emitter-side helper contract: what goes into a ledger meta line."""
    v = _try_version("diffusers")
    return v if v else "UNDECLARED"