"""CPU-testable GPU-01 launch guard. It never imports EVOKE or constructs a model."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess

import env_fingerprint
import flash_attn_preflight
import gpu01_config_identity as config_identity

GPU01_PRELAUNCH_PASS = "GPU01_PRELAUNCH_PASS"
ENV_BRINGUP_FAILURE = "ENV_BRINGUP_FAILURE"
GPU01_PRELAUNCH_REFUSED = "GPU01_PRELAUNCH_REFUSED"
PIN = "74d268516d95c8fceadd2378f91a73f9f187042b"
IDENTITY_MARKERS = ("UNDECLARED", "TEST_MODE_ONLY")


def file_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_sha256(value):
    return isinstance(value, str) and len(value) == 64 and \
        all(ch in "0123456789abcdefABCDEF" for ch in value)


def pin_revision(path):
    return subprocess.check_output(["git", "-C", path, "rev-parse", "HEAD"],
                                   text=True).strip()


def _literal_true(manifest):
    return isinstance(manifest, dict) and manifest.get("launch_strict") is True


def _identity_reasons(manifest, env, patch_path, profile_path, config_sha=None):
    reasons = []
    supplied = (("patch_sha256", patch_path, "EVOKE_STRICT_PATCH_SHA256"),
                ("profile_sha256", profile_path, "EVOKE_STRICT_PROFILE_SHA256"))
    for field, path, env_key in supplied:
        actual = file_sha256(path) if path and os.path.isfile(path) else None
        declared = env.get(env_key)
        archived = manifest.get(field) if isinstance(manifest, dict) else None
        if not actual:
            reasons.append("IDENTITY_PATH_MISSING:%s" % field)
        elif declared != actual:
            reasons.append("IDENTITY_ENV_HASH_MISMATCH:%s" % field)
        elif archived != actual:
            reasons.append("IDENTITY_MANIFEST_HASH_MISMATCH:%s" % field)
    for field in ("patch_sha256", "profile_sha256", "common_config_sha256"):
        value = manifest.get(field) if isinstance(manifest, dict) else None
        if value in IDENTITY_MARKERS or not is_sha256(value):
            reasons.append("IDENTITY_NOT_REAL:%s" % field)
    if config_sha is not None and manifest.get("common_config_sha256") != config_sha:
        reasons.append("IDENTITY_MANIFEST_HASH_MISMATCH:common_config_sha256")
    if config_sha is not None and env.get("EVOKE_STRICT_CONFIG_SHA256") != config_sha:
        reasons.append("IDENTITY_ENV_HASH_MISMATCH:common_config_sha256")
    return reasons


def validate_prelaunch(manifest, patch_path, profile_path, evoke_pin_path,
                       env=None, experiment_id=None, proposal_id=None,
                       pin_resolver=pin_revision, flash_probe=flash_attn_preflight.probe,
                       torch_module=None, fingerprint=env_fingerprint.fingerprint,
                       run_id_is_fresh=None, config_sha=None):
    """Return one guard report; collaborators may inject every external probe."""
    env = dict(os.environ if env is None else env)
    reasons = []
    if experiment_id != "GPU-01" or proposal_id != "GPU-01":
        reasons.append("GPU01_ID_REQUIRED")
    try:
        if pin_resolver(evoke_pin_path) != PIN:
            reasons.append("EVOKE_PIN_MISMATCH")
    except Exception as exc:
        reasons.append("EVOKE_PIN_UNVERIFIED:%s" % type(exc).__name__)
    if env.get("EVOKE_STRICT_LAUNCH") != "1":
        reasons.append("STRICT_LAUNCH_ENV_REQUIRED")
    if not _literal_true(manifest):
        reasons.append("LAUNCH_STRICT_LITERAL_TRUE_REQUIRED")
    reasons.extend(_identity_reasons(manifest, env, patch_path, profile_path,
                                     config_sha=config_sha))
    if not env.get("EVOKE_WARP_SEED"):
        reasons.append("WARP_SEED_REQUIRED")
    if not env.get("EVOKE_STRICT_BASE_SEED"):
        reasons.append("BASE_SEED_REQUIRED")
    run_ids = manifest.get("run_ids") if isinstance(manifest, dict) else None
    pair_id = manifest.get("pair_id") if isinstance(manifest, dict) else None
    if not isinstance(pair_id, str) or not pair_id:
        reasons.append("PAIR_ID_REQUIRED")
    if not isinstance(run_ids, dict):
        reasons.append("RUN_IDS_REQUIRED")
    else:
        factual, counterfactual = run_ids.get("factual"), run_ids.get("counterfactual")
        if not isinstance(factual, str) or not factual or \
                not isinstance(counterfactual, str) or not counterfactual:
            reasons.append("RUN_IDS_REQUIRED")
        elif factual == counterfactual:
            reasons.append("RUN_IDS_NOT_DISTINCT")
        else:
            if run_id_is_fresh is None:
                artifacts = manifest.get("artifacts") if isinstance(manifest, dict) else None
                paths = []
                for role in ("factual", "counterfactual"):
                    spec = artifacts.get(role + "_log") if isinstance(artifacts, dict) else None
                    paths.append(spec.get("path") if isinstance(spec, dict) else None)
                fresh = all(isinstance(path, str) and path and not os.path.exists(path)
                            for path in paths)
            else:
                fresh = run_id_is_fresh(factual, counterfactual)
            if not fresh:
                reasons.append("RUN_IDS_NOT_FRESH")
    if reasons:
        return {"status": GPU01_PRELAUNCH_REFUSED, "reasons": reasons}

    probe = flash_probe()
    if probe.get("status") != "PASS":
        return {"status": ENV_BRINGUP_FAILURE, "reasons": ["FLASH_ATTN_PREFLIGHT_FAILED"],
                "flash_attn": probe}
    try:
        if torch_module is None:
            import torch as torch_module
        torch_module.backends.cudnn.benchmark = False
        torch_module.backends.cudnn.deterministic = True
        resolved_cudnn = {"benchmark": bool(torch_module.backends.cudnn.benchmark),
                          "deterministic": bool(torch_module.backends.cudnn.deterministic)}
    except Exception as exc:
        return {"status": ENV_BRINGUP_FAILURE, "reasons": ["CUDNN_CONFIG_FAILED"],
                "error_type": type(exc).__name__}
    fp = fingerprint(patch_sha=file_sha256(patch_path), upstream_pin=PIN)
    fp["cudnn"] = resolved_cudnn
    return {"status": GPU01_PRELAUNCH_PASS, "reasons": [], "fingerprint": fp,
            "flash_attn": probe}


def write_artifact(path, report):
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--pair-manifest", required=True)
    parser.add_argument("--patch", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--evoke-pin", required=True)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--experiment-id", required=True)
    parser.add_argument("--proposal-id", required=True)
    args = parser.parse_args(argv)
    try:
        with open(args.pair_manifest, "r", encoding="utf-8") as fh:
            manifest = json.load(fh)
    except Exception as exc:
        manifest = {}
        report = {"status": GPU01_PRELAUNCH_REFUSED,
                  "reasons": ["PAIR_MANIFEST_PARSE_ERROR:%s" % type(exc).__name__]}
    else:
        report = validate_prelaunch(manifest, args.patch, args.profile, args.evoke_pin,
                                    experiment_id=args.experiment_id,
                                    proposal_id=args.proposal_id)
    write_artifact(args.artifact, report)
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0 if report["status"] == GPU01_PRELAUNCH_PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())
