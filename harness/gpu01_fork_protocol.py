"""Canonical role-specific GPU-01 fork protocol, shared with patched EVOKE."""
from __future__ import annotations

import hashlib
import json
import os

SCHEMA = "causalfork/gpu01-fork-protocol@1"


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def load_gpu01_fork_json(value):
    """Parse inline JSON or a JSON file exactly as the engine does."""
    if isinstance(value, dict):
        obj = value
    elif isinstance(value, str) and value.lstrip().startswith("{"):
        obj = json.loads(value)
    elif isinstance(value, str):
        with open(value, "r", encoding="utf-8") as fh:
            obj = json.load(fh)
    else:
        raise ValueError("FORK_JSON_REQUIRED")
    if not isinstance(obj, dict):
        raise ValueError("FORK_JSON_OBJECT_REQUIRED")
    return obj


def canonical_gpu01_fork_protocol(fork_cfg, role):
    cfg = load_gpu01_fork_json(fork_cfg)
    mode = cfg.get("mode")
    semantic = {"role": role, "fork_chunk": cfg.get("fork_chunk"), "mode": mode}
    operational = {}
    if role == "factual" and mode == "capture":
        operational["out_dir"] = cfg.get("out_dir")
    elif role == "counterfactual" and mode == "restore":
        operational["sidecar"] = cfg.get("sidecar")
        operational["parent_state_digest"] = cfg.get("parent_state_digest")
    else:
        raise ValueError("FORK_ROLE_MODE_INVALID")
    if not isinstance(semantic["fork_chunk"], int):
        raise ValueError("FORK_CHUNK_REQUIRED")
    if role == "factual" and not operational["out_dir"]:
        raise ValueError("FORK_CAPTURE_OUT_DIR_REQUIRED")
    if role == "counterfactual":
        if not operational["sidecar"]:
            raise ValueError("FORK_RESTORE_SIDECAR_REQUIRED")
        if not operational["parent_state_digest"]:
            raise ValueError("FORK_RESTORE_PARENT_STATE_DIGEST_REQUIRED")
    return {"schema": SCHEMA, "semantic": semantic, "operational": operational}


def gpu01_fork_protocol_sha256(fork_cfg, role):
    # Operational paths intentionally do not define semantic protocol identity.
    protocol = canonical_gpu01_fork_protocol(fork_cfg, role)
    return hashlib.sha256(_json({"schema": SCHEMA, "semantic": protocol["semantic"]}).encode("utf-8")).hexdigest()
