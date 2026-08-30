"""Immutable post-child GPU-01 completion evidence."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone

SCHEMA = "causalfork/gpu01-completion@1"
COMPLETE = "GPU01_CHILD_COMPLETE"
FAILED = "GPU01_CHILD_FAILED"

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(65536), b""):
            h.update(block)
    return h.hexdigest()

def _meta(path):
    import strict_coupling
    parsed = strict_coupling.load_log(path)
    if len(parsed["metas"]) != 1:
        raise ValueError("CHILD_LEDGER_PARSE_ERROR")
    return parsed, parsed["metas"][0]

def verify(record, manifest, role):
    """Return (status, reasons, additions); never runs pair validation."""
    if record.get("child_returncode") != 0:
        return FAILED, ["CHILD_NONZERO"], {}
    spec = ((manifest.get("artifacts") or {}).get(role + "_log") or {})
    path = spec.get("path")
    if not path or not os.path.exists(path):
        return FAILED, ["CHILD_LEDGER_MISSING"], {}
    try:
        parsed, meta = _meta(path)
    except Exception:
        return FAILED, ["CHILD_LEDGER_PARSE_ERROR"], {}
    expected = {"pair_id": record["pair_id"], "run_id": record["run_id"],
                "branch_id": role, "gpu01_invocation_id": record["invocation_id"],
                "prelaunch_artifact_sha256": record["prelaunch_artifact_sha256"],
                "common_config_sha256": record["common_config_sha256"],
                "engine_resolved_config_sha256": record["common_config_sha256"],
                "engine_fork_protocol_sha256": record["fork_protocol_sha256"]}
    if any(meta.get(k) != v for k, v in expected.items()):
        return FAILED, ["CHILD_LEDGER_IDENTITY_MISMATCH"], {}
    event = "FORK_CAPTURE" if role == "factual" else "GENERATOR_STATE_RESTORED"
    events = [e for e in parsed["events"] if e.get("event") == event and e.get("chunk") == manifest.get("fork_chunk")]
    if len(events) != 1:
        return FAILED, ["CHILD_LEDGER_EVENT_MISSING"], {}
    return COMPLETE, [], {"ledger_path": path, "ledger_sha256": sha256(path), "event": events[0]}

def write(path, data):
    with open(path, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n")

def make(record, manifest, role):
    status, reasons, extra = verify(record, manifest, role)
    return {"schema": SCHEMA, "status": status, "reasons": reasons,
            "pair_id": record.get("pair_id"), "run_id": record.get("run_id"),
            "branch_id": role, "role": role, "invocation_id": record.get("invocation_id"),
            "prelaunch_artifact_path": record.get("prelaunch_artifact_path"),
            "prelaunch_artifact_sha256": record.get("prelaunch_artifact_sha256"),
            "child_returncode": record.get("child_returncode"), "fork_chunk": manifest.get("fork_chunk"),
            "common_config_sha256": record.get("common_config_sha256"),
            "fork_protocol_sha256": record.get("fork_protocol_sha256"),
            "completed_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(), **extra}
