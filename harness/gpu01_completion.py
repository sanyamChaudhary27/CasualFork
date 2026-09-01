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

def normalized(path):
    return os.path.normcase(os.path.abspath(os.path.normpath(path)))

def engine_ledger_target(base_path, run_id):
    stem, ext = os.path.splitext(base_path)
    return "%s.%s%s" % (stem, run_id, ext or ".jsonl")

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
    extra = {"ledger_path": normalized(path), "ledger_sha256": sha256(path), "event": events[0]}
    if role == "factual":
        capture, digest = events[0].get("sidecar"), events[0].get("state_digest")
        if not capture or not os.path.exists(capture) or not digest or not os.path.exists(digest):
            return FAILED, ["CHILD_FACTUAL_CAPTURE_EVIDENCE_MISSING"], {}
        extra["fork_capture_sidecar"] = {"path": normalized(capture), "sha256": sha256(capture)}
        extra["parent_state_digest"] = {"path": normalized(digest), "sha256": sha256(digest)}
    return COMPLETE, [], extra

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

def load_verified(spec, manifest, role):
    """Load one completion binding and reject stale/mutated evidence."""
    if not isinstance(spec, dict) or not spec.get("path") or not spec.get("sha256"):
        raise ValueError("COMPLETION_MISSING")
    if sha256(spec["path"]) != spec["sha256"]:
        raise ValueError("COMPLETION_SHA_MISMATCH")
    with open(spec["path"], encoding="utf-8") as fh:
        obj = json.load(fh)
    if obj.get("schema") != SCHEMA or obj.get("status") != COMPLETE or obj.get("child_returncode") != 0 or \
            obj.get("pair_id") != manifest.get("pair_id") or obj.get("run_id") != manifest["run_ids"].get(role) or obj.get("role") != role:
        raise ValueError("COMPLETION_IDENTITY_MISMATCH")
    for key in ("ledger_path", "ledger_sha256"):
        if not obj.get(key): raise ValueError("COMPLETION_LEDGER_MISSING")
    if sha256(obj["ledger_path"]) != obj["ledger_sha256"]:
        raise ValueError("COMPLETION_LEDGER_SHA_MISMATCH")
    artifacts = manifest.get("artifacts") or {}
    log = artifacts.get(role + "_log") or {}
    pre = artifacts.get(role + "_prelaunch") or {}
    if normalized(obj["ledger_path"]) != normalized(log.get("path", "")) or \
            obj["ledger_sha256"] != log.get("sha256") or \
            obj.get("invocation_id") != (manifest.get("invocation_ids") or {}).get(role) or \
            obj.get("prelaunch_artifact_sha256") != pre.get("sha256") or \
            obj.get("common_config_sha256") != manifest.get("common_config_sha256") or \
            obj.get("fork_protocol_sha256") != (manifest.get("fork_protocol_sha256") or {}).get(role):
        raise ValueError("COMPLETION_MANIFEST_BIND_MISMATCH")
    if role == "factual":
        for key in ("fork_capture_sidecar", "parent_state_digest"):
            item = obj.get(key) or {}
            if not item.get("path") or not item.get("sha256") or sha256(item["path"]) != item["sha256"]:
                raise ValueError("COMPLETION_FACTUAL_ARTIFACT_MISMATCH")
    return obj
