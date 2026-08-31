"""Mandatory non-shell GPU-01 launch wrapper.

The wrapper resolves the actual infer_single argv without model construction,
archives a prelaunch decision, and invokes a child only after PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone

import gpu01_config_identity as config_identity
import gpu01_fork_protocol as fork_protocol
import gpu01_prelaunch as prelaunch
import gpu01_completion as completion
import sc1_preflight

SCHEMA = "causalfork/gpu01-prelaunch@1"
VERSION = "gpu01-launch@1"


def _sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("utf-8")


def _load_manifest(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def resolve_evoke_args(child_argv, evoke_pin):
    """Use EVOKE's current infer_single parser, without calling ``main``."""
    script_index = next((i for i, arg in enumerate(child_argv)
                         if os.path.basename(arg) == "infer_single.py"), None)
    if script_index is None:
        raise ValueError("CHILD_INFER_SINGLE_REQUIRED")
    script = child_argv[script_index]
    if not os.path.isabs(script):
        script = os.path.join(evoke_pin, script)
    if not os.path.isfile(script):
        raise ValueError("CHILD_INFER_SINGLE_NOT_FOUND")
    old_path = list(sys.path)
    try:
        if evoke_pin not in sys.path:
            sys.path.insert(0, evoke_pin)
        spec = importlib.util.spec_from_file_location("gpu01_infer_single_parser", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return vars(module.parse_args(child_argv[script_index + 1:]))
    finally:
        sys.path[:] = old_path


def _artifact(report, manifest, resolved_args, env, child_argv, patch_path,
              profile_path, pair_id, run_id, role, invocation_id, protocol, protocol_sha):
    config = config_identity.canonical_gpu01_config(resolved_args, env)
    config_sha = config_identity.gpu01_config_sha256(resolved_args, env)
    return {
        "schema": SCHEMA, "version": VERSION, "status": report["status"],
        "reasons": list(report.get("reasons", [])),
        "experiment_id": "GPU-01", "proposal_id": "GPU-01",
        "pair_id": pair_id, "run_id": run_id, "branch_id": role, "role": role,
        "invocation_id": invocation_id,
        "pin": prelaunch.PIN,
        "patch_sha256": prelaunch.file_sha256(patch_path) if os.path.isfile(patch_path) else None,
        "profile_sha256": prelaunch.file_sha256(profile_path) if os.path.isfile(profile_path) else None,
        "common_config_sha256": config_sha, "canonical_config": config,
        "fork_protocol_sha256": protocol_sha, "canonical_fork_protocol": protocol,
        "argv": list(child_argv), "argv_sha256": _sha_bytes(_canonical_json(list(child_argv))),
        "strict_env": config["strict_env"],
        "strict_env_sha256": _sha_bytes(_canonical_json(config["strict_env"])),
        "manifest_common_config_sha256": manifest.get("common_config_sha256"),
        "fingerprint": report.get("fingerprint"), "flash_attn": report.get("flash_attn"),
        "cudnn": (report.get("fingerprint") or {}).get("cudnn"),
        "created_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
    }


def _bind_artifact(manifest_path, manifest, role, artifact_path, artifact_sha, invocation_id, protocol_sha):
    """Archive the exact prelaunch bytes under the branch's manifest binding."""
    artifacts = manifest.setdefault("artifacts", {})
    artifacts[role + "_prelaunch"] = {"path": artifact_path, "sha256": artifact_sha,
                                        "invocation_id": invocation_id,
                                        "fork_protocol_sha256": protocol_sha}
    manifest.setdefault("invocation_ids", {})[role] = invocation_id
    manifest.setdefault("fork_protocol_sha256", {})[role] = protocol_sha
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n")


def launch(pair_manifest_path, patch_path, profile_path, evoke_pin, artifact_path,
           child_argv, env=None, resolver=resolve_evoke_args,
           validator=prelaunch.validate_prelaunch, runner=subprocess.run):
    """Archive decision then run the exact child list iff prelaunch passes."""
    env = dict(os.environ if env is None else env)
    report = None
    manifest = {}
    resolved_args = {}
    pair_id = env.get("EVOKE_STRICT_PAIR_ID")
    run_id = env.get("EVOKE_STRICT_RUN_ID")
    role = env.get("EVOKE_STRICT_BRANCH_ID")
    invocation_id = uuid.uuid4().hex
    protocol, protocol_sha = None, None
    try:
        manifest = _load_manifest(pair_manifest_path)
        pair_id = pair_id or manifest.get("pair_id")
        run_ids = manifest.get("run_ids") or {}
        role = role or next((r for r in ("factual", "counterfactual")
                             if run_ids.get(r) == run_id), None)
        run_id = run_id or (run_ids.get(role) if role else None)
        if role not in ("factual", "counterfactual") or not run_id or not pair_id:
            raise ValueError("PAIR_RUN_ROLE_REQUIRED")
        existing = ((manifest.get("artifacts") or {}).get(role + "_prelaunch") or {})
        if existing.get("invocation_id"):
            raise ValueError("PRELAUNCH_ALREADY_BOUND")
        if os.path.exists(artifact_path):
            raise ValueError("PRELAUNCH_ARTIFACT_EXISTS")
        if os.path.exists(artifact_path + ".completion.json"):
            raise ValueError("COMPLETION_ARTIFACT_EXISTS")
        resolved_args = resolver(list(child_argv), evoke_pin)
        base_ledger = env.get("EVOKE_STRICT_LEDGER_PATH")
        declared_ledger = ((manifest.get("artifacts") or {}).get(role + "_log") or {}).get("path")
        if not base_ledger or not declared_ledger or completion.normalized(completion.engine_ledger_target(base_ledger, run_id)) != completion.normalized(declared_ledger):
            raise ValueError("ENGINE_LEDGER_TARGET_MISMATCH")
        env["EVOKE_STRICT_PATCH_SHA256"] = prelaunch.file_sha256(patch_path)
        env["EVOKE_STRICT_PROFILE_SHA256"] = prelaunch.file_sha256(profile_path)
        env["EVOKE_STRICT_PAIR_ID"] = pair_id
        env["EVOKE_STRICT_RUN_ID"] = run_id
        env["EVOKE_STRICT_BRANCH_ID"] = role
        env["EVOKE_STRICT_LAUNCH"] = "1"
        env["EVOKE_GPU01_INVOCATION_ID"] = invocation_id
        protocol = fork_protocol.canonical_gpu01_fork_protocol(env.get("EVOKE_STRICT_FORK_JSON"), role)
        if protocol["semantic"]["fork_chunk"] != int(manifest.get("fork_chunk")):
            raise ValueError("FORK_CHUNK_MANIFEST_MISMATCH")
        protocol_sha = fork_protocol.gpu01_fork_protocol_sha256(env.get("EVOKE_STRICT_FORK_JSON"), role)
        config_sha = config_identity.gpu01_config_sha256(resolved_args, env)
        env["EVOKE_STRICT_CONFIG_SHA256"] = config_sha
        pf = sc1_preflight.preflight(resolved_args, env=env, profile_path=profile_path)
        if pf["status"] != "PASS":
            report = {"status": prelaunch.GPU01_PRELAUNCH_REFUSED,
                      "reasons": ["SC1_PREFLIGHT_ABORT"] +
                      [a["code"] for a in pf["aborts"]]}
        else:
            report = validator(manifest, patch_path, profile_path, evoke_pin, env=env,
                               experiment_id="GPU-01", proposal_id="GPU-01",
                               config_sha=config_sha)
    except Exception as exc:
        report = {"status": prelaunch.GPU01_PRELAUNCH_REFUSED,
                  "reasons": [str(exc) if isinstance(exc, ValueError) else
                              "LAUNCH_RESOLUTION_FAILED:%s" % type(exc).__name__]}
    record = _artifact(report, manifest, resolved_args, env, child_argv, patch_path,
                       profile_path, pair_id, run_id, role, invocation_id, protocol, protocol_sha)
    if os.path.exists(artifact_path):
        record["status"] = prelaunch.GPU01_PRELAUNCH_REFUSED
        record["reasons"] = list(record.get("reasons", [])) + ["PRELAUNCH_ARTIFACT_EXISTS"]
        return record
    prelaunch.write_artifact(artifact_path, record, exclusive=True)
    artifact_sha = prelaunch.file_sha256(artifact_path)
    if report["status"] != prelaunch.GPU01_PRELAUNCH_PASS:
        return record
    _bind_artifact(pair_manifest_path, manifest, role, artifact_path, artifact_sha, invocation_id, protocol_sha)
    sealed_env = dict(env)
    sealed_env.update({
        "EVOKE_STRICT_CONFIG_SHA256": record["common_config_sha256"],
        "EVOKE_STRICT_LAUNCH": "1",
        "EVOKE_GPU01_PRELAUNCH_ARTIFACT": os.path.abspath(artifact_path),
        "EVOKE_GPU01_PRELAUNCH_ARTIFACT_SHA256": artifact_sha,
        "EVOKE_STRICT_PAIR_ID": pair_id,
        "EVOKE_STRICT_RUN_ID": run_id,
        "EVOKE_STRICT_BRANCH_ID": role,
        "EVOKE_GPU01_INVOCATION_ID": invocation_id,
        "EVOKE_GPU01_FORK_PROTOCOL_SHA256": protocol_sha,
    })
    result = runner(list(child_argv), env=sealed_env, shell=False, check=False)
    record["child_returncode"] = getattr(result, "returncode", result)
    record["prelaunch_artifact_path"] = os.path.abspath(artifact_path)
    record["prelaunch_artifact_sha256"] = artifact_sha
    completion_path = os.path.abspath(artifact_path + ".completion.json")
    completion_record = completion.make(record, manifest, role)
    completion.write(completion_path, completion_record)
    record["completion_path"] = completion_path
    record["completion_status"] = completion_record["status"]
    if completion_record["status"] == completion.COMPLETE:
        manifest = _load_manifest(pair_manifest_path)
        artifacts = manifest.setdefault("artifacts", {})
        artifacts[role + "_log"]["sha256"] = completion_record["ledger_sha256"]
        artifacts[role + "_completion"] = {"path": completion_path,
                                              "sha256": completion.sha256(completion_path),
                                              "invocation_id": invocation_id}
        if role == "factual":
            artifacts["factual_fork_capture"] = completion_record["fork_capture_sidecar"]
            manifest["parent_state_digest"] = completion_record["parent_state_digest"]
        _bind_artifact(pair_manifest_path, manifest, role, artifact_path, artifact_sha, invocation_id, protocol_sha)
    return record


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair-manifest", required=True)
    parser.add_argument("--patch", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--evoke-pin", required=True)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("child_argv", nargs=argparse.REMAINDER)
    ns = parser.parse_args(argv)
    child = ns.child_argv[1:] if ns.child_argv[:1] == ["--"] else ns.child_argv
    if not child:
        parser.error("child argv is required after --")
    record = launch(ns.pair_manifest, ns.patch, ns.profile, ns.evoke_pin,
                    ns.artifact, child)
    print(json.dumps(record, sort_keys=True, separators=(",", ":")))
    return 0 if record.get("completion_status") == completion.COMPLETE else 1


if __name__ == "__main__":
    raise SystemExit(main())
