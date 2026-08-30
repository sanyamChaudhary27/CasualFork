"""Canonical GPU-01 resolved-config identity shared with the patched engine.

Only an explicit branch/output classification may be omitted. Every other
resolved infer_single option and audited strict environment input is retained.
"""
from __future__ import annotations

import hashlib
import json

SCHEMA = "causalfork/gpu01-config-identity@1"

# These are the only resolved argument names whose values may legitimately
# differ across the prompt-only branch pair or name an output artifact.
ALLOWED_BRANCH_DIVERGENCE = frozenset((
    "prompt", "prompt_schedule", "chunk_prompts", "branch_id", "run_id",
    "ledger_path", "output_folder", "output_path", "output_dir",
))

# Output-only options are a subset of the permitted branch divergence table.
NONCAUSAL_OUTPUT_METADATA = frozenset((
    "ledger_path", "output_folder", "output_path", "output_dir",
    "save_chunk_segments", "dump_geo_intermediates", "bg_postprocess",
    "ref_video_for_viz", "joystick_hud",
))

# Harness-only baseline annotations are not infer_single options and cannot be
# launch inputs. They are retained solely for the preflight comparison API.
IDENTITY_HARNESS_METADATA = frozenset(("expected_common_config_sha256",))

# All resolved arguments not named above are common causal configuration. This
# deliberately includes negative prompt, camera/pose, resolution, seeds,
# steps/stages, GEO/depth backend, event_chunks, and strict-profile options.
COMMON_CAUSAL_CONFIG = "all resolved args except ALLOWED_BRANCH_DIVERGENCE"

# Audited environment inputs that can alter execution or strict control flow.
STRICT_ENV_KEYS = (
    "EVOKE_WARP_SEED", "EVOKE_STRICT_BASE_SEED", "EVOKE_STRICT_LAUNCH",
    "EVOKE_STRICT_FORK_JSON", "EVOKE_CPU_THREADS", "EVOKE_INFER_DEBUG",
    "EVOKE_INFER_PROGRESS", "GEO_HIST_MAX_FRAMES", "OMP_NUM_THREADS",
    "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "CUDA_VISIBLE_DEVICES",
    "CUBLAS_WORKSPACE_CONFIG", "PYTORCH_CUDA_ALLOC_CONF",
)


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


def canonical_gpu01_config(resolved_args, strict_env):
    """Return the canonical, JSON-safe object used for GPU-01 identity."""
    args = dict(resolved_args or {})
    env = dict(strict_env or {})
    common = {str(k): args[k] for k in sorted(args, key=str)
              if k not in ALLOWED_BRANCH_DIVERGENCE and
              k not in NONCAUSAL_OUTPUT_METADATA and
              k not in IDENTITY_HARNESS_METADATA and
              not str(k).startswith("_")}
    audited_env = {key: env.get(key) for key in STRICT_ENV_KEYS
                   if key in env or key in ("EVOKE_WARP_SEED",
                                             "EVOKE_STRICT_BASE_SEED",
                                             "EVOKE_STRICT_LAUNCH")}
    return {"schema": SCHEMA, "resolved_args": common,
            "strict_env": audited_env}


def gpu01_config_sha256(resolved_args, strict_env):
    """SHA-256 of :func:`canonical_gpu01_config`'s canonical JSON."""
    return hashlib.sha256(_json(canonical_gpu01_config(
        resolved_args, strict_env)).encode("utf-8")).hexdigest()
