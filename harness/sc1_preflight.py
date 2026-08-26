"""SC1 strict preflight (STAGE-B/C target 7).

Given a RESOLVED args mapping + env mapping, mechanically enforce the frozen
profile (profiles/sc1_strict_profile.json) BEFORE any GPU second is spent:

  * forbidden / DISABLE_FOR_SC1 options present -> abort list entries;
  * PRECOND-1: EVOKE_WARP_SEED exported non-empty;
  * PRECOND-2: training-mode flags all false;
  * common-config hash vs an expected baseline (prompt fields excluded) ->
    CONFIG_HASH_MISMATCH abort when the profile/config drifted with NO
    RNG-relevant change (the exact trap test E guards);
  * emits sha256 placeholders for profile / config / input image / pose /
    checkpoint so the run manifest can pin inputs.

Pure CPU. Returns a structured report; never raises for option problems.
"""
from __future__ import annotations

import hashlib
import json
import os

DEFAULT_PROFILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               os.pardir, "profiles", "sc1_strict_profile.json")
PROMPT_FIELDS = ("prompt", "prompt_schedule", "chunk_prompts")

# (rule_id, arg_key, predicate(value)->True means FORBIDDEN, human reason)
FORBIDDEN_RULES = (
    ("geo_warp_vis_cap", lambda v: v is not None and float(v) > 0.0,
     "Bayer keep_frac becomes visibility-conditioned"),
    ("geo_warp_patch_drop_ratio", lambda v: v is not None and float(v) > 0.0,
     "creates a second long-lived RNG stream (_geo_patchdrop_gen)"),
    ("invisible_history_noise", bool,
     "randn_like on history tiers adds draws"),
    ("short_tier_noise_enabled", bool,
     "variable per-chunk generator drains"),
    ("sigma_lock_per_rollout", bool,
     "rollout-start sigma-lock draw"),
    ("use_adaptive_anti_drifting", bool,
     "drift-triggered RNG insertion = data-dependent control flow"),
    ("use_dmd", bool,
     "different timestep algebra + renoise draw"),
    ("restrict_self_attn", bool,
     "hidden mutable cross-step cache state"),
    ("use_kv_cache", bool,
     "hidden mutable cross-step cache state"),
)
FORBIDDEN_ENV_RULES = (
    ("GEO_HIST_MAX_FRAMES", lambda v: v not in (None, "", "0"),
     "changes DA3 point-cloud bounds -> changes covis draw counts"),
)
PRECOND2_FLAG_KEYS = ("transformer_training", "vae_training",
                      "text_encoder_training", "estimator_training")


def _sha_of_text(t):
    return hashlib.sha256(t.encode("utf-8")).hexdigest()


def canonical_config(args):
    """Config identity: canonical JSON minus prompt-only fields."""
    slim = {k: v for k, v in args.items()
            if k not in PROMPT_FIELDS
            and k not in ("expected_common_config_sha256", "_baseline_args")}
    return _sha_of_text(json.dumps(slim, sort_keys=True, separators=(",", ":")))


def placeholder_sha(args, key):
    v = args.get(key)
    if v in (None, "", "PLACEHOLDER"):
        return None
    if isinstance(v, str) and os.path.exists(v):
        h = hashlib.sha256()
        with open(v, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    return _sha_of_text(repr(v))


def load_profile(path=None):
    path = os.path.abspath(path or DEFAULT_PROFILE)
    with open(path, "rb") as fh:
        raw = fh.read()
    if raw[:3] == b"\xef\xbb\xbf":
        raise ValueError("profile has a UTF-8 BOM; strip it (target 8)")
    return json.loads(raw.decode("utf-8")), _sha_bytes(raw)


def _sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def preflight(args, env=None, profile_path=None):
    """Run every mechanical check. Returns a structured pass/abort report."""
    env = dict(os.environ if env is None else env)
    aborts, warnings = [], []
    profile, profile_sha = load_profile(profile_path)

    # ---- forbidden options ---------------------------------------------------
    for rule_id, pred, why in FORBIDDEN_RULES:
        if rule_id in args and pred(args[rule_id]):
            aborts.append({"code": "FORBIDDEN_OPTION", "option": rule_id,
                           "value": repr(args[rule_id]), "reason": why})
    for env_key, pred, why in FORBIDDEN_ENV_RULES:
        if pred(env.get(env_key)):
            aborts.append({"code": "FORBIDDEN_OPTION", "option": "env:" + env_key,
                           "value": repr(env.get(env_key)), "reason": why})
    ec = args.get("event_chunks")
    if ec:  # empty list [] is the ONLY legal value (forbidden as mechanism)
        aborts.append({"code": "FORBIDDEN_MECHANISM", "option": "event_chunks",
                       "value": repr(ec),
                       "reason": "event_chunks drops warp/static-cam/skips bank; "
                                 "SC1 divergence is prompt-schedule-only"})

    # ---- PRECOND-1 -----------------------------------------------------------
    wseed = env.get("EVOKE_WARP_SEED")
    if not wseed:
        aborts.append({"code": "PRECOND1_UNMET", "option": "EVOKE_WARP_SEED",
                       "value": None,
                       "reason": "zbuf covis subsample would draw from the global "
                                 "CUDA RNG (da3_cloud.py:1475-76); irreproducible"})
    else:
        warnings.append({"code": "PRECOND1_OK",
                         "sha256": _sha_of_text(wseed)})

    # ---- PRECOND-2 -----------------------------------------------------------
    flags = args.get("module_training_flags") or {}
    for k in PRECOND2_FLAG_KEYS:
        if k in flags:
            if flags[k]:
                aborts.append({"code": "PRECOND2_UNMET", "module": k,
                               "value": repr(flags[k]),
                               "reason": "module not in eval() mode"})
        else:
            warnings.append({"code": "PRECOND2_UNKNOWN_MODULE", "module": k,
                             "detail": "flag absent from resolved args; assert at G1"})

    # ---- config-hash baseline (test E trap) ----------------------------------
    cfg_sha = canonical_config(args)
    expected = args.get("expected_common_config_sha256")
    if expected is not None and expected != cfg_sha:
        rng_keys = ("seed", "EVOKE_WARP_SEED", "num_inference_steps",
                    "stage2_steps", "guidance_scale", "height", "width", "fps")
        baseline = args.get("_baseline_args")
        if baseline:
            rng_changed = any(str(args.get(k)) != str(baseline.get(k))
                              for k in rng_keys
                              if k != "EVOKE_WARP_SEED" or env.get("EVOKE_WARP_SEED") != baseline.get("EVOKE_WARP_SEED"))
            # env seed compared separately below
            rng_changed = bool(rng_changed)
        else:
            rng_changed = None   # unknown without a frozen baseline snapshot
        aborts.append({
            "code": "CONFIG_HASH_MISMATCH",
            "expected": expected, "actual": cfg_sha,
            "rng_relevant_change_detected": rng_changed,
            "reason": "resolved config hash differs from the frozen-profile "
                      "baseline; re-freeze the profile before launching",
        })
    else:
        warnings.append({"code": "CONFIG_HASH_OK", "sha256": cfg_sha})

    hashes = {
        "profile_sha256": profile_sha,
        "config_sha256": cfg_sha,
        "input_image_sha256": placeholder_sha(args, "image_path"),
        "pose_sha256": placeholder_sha(args, "lingbot_pose_path"),
        "checkpoint_dir_sha256": placeholder_sha(args, "checkpoint_dir"),
    }
    status = "ABORT" if aborts else "PASS"
    return {
        "status": status,
        "aborts": aborts,
        "warnings": warnings,
        "hashes": hashes,
        "profile_id": profile.get("profile_id"),
        "preconditions": {
            "PRECOND-1": "MET" if wseed else "UNMET",
            "PRECOND-2": "MET" if not any(a["code"] == "PRECOND2_UNMET" for a in aborts)
                         else "UNMET",
        },
    }