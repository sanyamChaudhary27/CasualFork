"""Shared CPU fixtures for SC1 validator/emitter suites (v1-updated + v2 + final CPU round).

Builds validator-shaped branch logs whose per-chunk draw grammar follows the
RE-AUDITED pin order (sc1_grammar.DERIVATION):

    [hook] R7(rows per render call) | R2 R3 R4 R5 R1 R6(s1) R6(s2)

Deterministic throughout; mutation hooks let each Stage-C case inject exactly
one controlled defect. No GPU, no pip installs; torch only for digests.

FINAL CPU ROUND additions:
  * make_mock_root carries every CANONICAL FIELD_SPEC path (F01-F14 numbering);
  * make_engine_like_fixture() returns an engine-shaped (geo_state, pipeline,
    locals) triple so tests can drive the REAL emitter build_live_state_view.
"""
from __future__ import annotations

import hashlib
import json
import os
import uuid

PIN = "74d268516d95c8fceadd2378f91a73f9f187042b"
PATCH_ID = "evoke-74d26851-strict-coupling"
PROFILE_SHA = "profilesha" + "0" * 56
PATCH_SHA = "patchsha" + "0" * 57
CONFIG_SHA = "configsha" + "0" * 56
WARP_SEED_SHA = "warpseedsha" + "0" * 53
PAIR_ID = "pair-TESTPAIR"

SHAPES = {
    "R1": [1, 16, 9, 48, 80], "R2": [1, 16, 1, 48, 80], "R3": [1, 16, 9, 48, 80],
    "R4": [9], "R5": [1, 16, 9, 48, 80], "R6": [432, 4],
}
R7_SHAPE = [2000]
DIAG_FIELDS = ("sha256_input_pixels", "sha256_mean", "sha256_std")
GENERATOR_STATE_RESTORED = "GENERATOR_STATE_RESTORED"


def sha(text):
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def default_variant():
    return {"flip_r2r3_at": None,
            "flip_tensor": None,
            "r7_diverge_at": None,
            "drop_last_r6": None,
            "drop_site_at": None,
            }


def build_branch(role="factual", run_id="run-x", chunks=3, fork_chunk=1,
                 variant=None):
    """Return (meta, entries, events) for one branch."""
    import copy
    variant = copy.deepcopy(variant or default_variant())
    main_state = sha("boot-main")
    entries, events = [], []
    seq = [0]
    render_call = [0]
    counters = {}

    def nxt(site):
        counters[site] = counters.get(site, 0) + 1
        return counters[site]

    def tensor_sha(site, chunk, ordinal, salt=""):
        return sha("tensor|%s|%s|%d|%s" % (site, chunk, ordinal, salt))

    def emit(site, chunk, stage, role_name, before, after, tsha, shape,
             extra=None):
        seq[0] += 1
        entries.append({
            "event": "draw", "seq": seq[0], "run_id": run_id, "pair_id": PAIR_ID,
            "site_id": site, "ordinal": nxt(site), "branch_id": role,
            "chunk": chunk, "stage": stage, "generator_role": role_name,
            "generator_state_hash_before": before,
            "generator_state_hash_after": after,
            "tensor_sha256": tsha, "shape": shape, "dtype": "torch.float32",
            "extra": extra or {},
        })

    def emit_event(kind, chunk, **kw):
        seq[0] += 1
        ev = {"event": kind, "seq": seq[0], "run_id": run_id, "pair_id": PAIR_ID,
              "branch_id": role, "chunk": chunk}
        ev.update(kw)
        events.append(ev)

    flip_r2r3 = variant.get("flip_r2r3_at")
    for chunk in range(chunks):
        if chunk == fork_chunk:
            if role == "factual":
                emit_event("FORK_CAPTURE", chunk, generators=["main"],
                           sidecar="capture.json")
            else:
                emit_event(GENERATOR_STATE_RESTORED, chunk,
                           restored_generators=["main"], sidecar="capture.json")
        # ---- R7: warp render (isolated generator), BEFORE every fixed site ----
        render_call[0] += 1
        div = variant.get("r7_diverge_at")
        diverged_now = div is not None and div[0] == chunk
        st = sha("boot-iso")
        for ci, (gid, high) in enumerate(((11, 16), (12, 20), (13, 0))):
            if high == 0:
                emit("R7", chunk, None, "isolated_warp", st, st, None, None,
                     extra={"source_gid": gid, "covis_M": 2000,
                            "render_call": render_call[0], "call_ordinal": ci,
                            "high": 0, "skip_flag": True})
                continue
            nb = st
            na = sha(st + "|R7")
            h_eff = high
            if diverged_now and div[1] <= ci:
                na = sha(na + "|domain-diverged")
                h_eff = high + 5
            st = na
            emit("R7", chunk, None, "isolated_warp", nb, na,
                 sha("idx|%s|%s|%d|%d" % (role, chunk, ci, h_eff)), R7_SHAPE,
                 extra={"source_gid": gid, "covis_M": 2000,
                        "render_call": render_call[0], "call_ordinal": ci,
                        "high": h_eff, "skip_flag": False})
        # ---- fixed sites ------------------------------------------------------
        for site, stage in (("R2", None), ("R3", None), ("R4", None),
                            ("R5", None), ("R1", None), ("R6", 1), ("R6", 2)):
            drop = variant.get("drop_site_at")
            if drop and tuple(drop) == (site, chunk):
                continue
            before = main_state
            after = sha(main_state + "|" + site)
            main_state = after
            ordn = counters.get(site, 0)
            salt = ""
            if flip_r2r3 is not None and site in ("R2", "R3") and \
                    flip_r2r3 == chunk and role == "counterfactual":
                salt = "|flipped"
            ft = variant.get("flip_tensor")
            if ft and tuple(ft) == (site, chunk) and role == "counterfactual":
                salt = salt + "|tensorflip"
            extra = {}
            if site in ("R2", "R3"):
                base = {"sha256_input_pixels": sha("pix|%s|%s" % (site, chunk)),
                        "sha256_mean": sha("mean|%s" % chunk),
                        "sha256_std": sha("std|%s" % chunk)}
                if salt:
                    base["sha256_mean"] = sha("mean|%s%s" % (chunk, salt))
                    base["sha256_std"] = sha("std|%s%s" % (chunk, salt))
                if site == "R3":
                    base["loop_i"] = 0
                extra = base
            emit(site, chunk, stage, "main", before, after,
                 tensor_sha(site, chunk, ordn, salt), SHAPES[site], extra)
        if variant.get("drop_last_r6") == chunk:
            r6c = [e for e in entries
                   if e["site_id"] == "R6" and e["chunk"] == chunk]
            last_ord = max(x["ordinal"] for x in r6c)
            entries = [e for e in entries
                       if not (e["site_id"] == "R6" and e["chunk"] == chunk
                               and e["ordinal"] == last_ord)]
            counters["R6"] -= 1

    continuation = GENERATOR_STATE_RESTORED if role == "counterfactual" else None
    import torch
    f10_sha = hashlib.sha256(torch.get_rng_state().contiguous().reshape(
        -1).numpy().tobytes()).hexdigest()
    meta = {
        "event": "meta", "pin": PIN, "patch": PATCH_ID,
        "patch_sha256": PATCH_SHA, "profile_sha256": PROFILE_SHA,
        "common_config_sha256": CONFIG_SHA, "fork_chunk": fork_chunk,
        "torch": "2.10.0+cpu", "diffusers": "0.39.0",
        "warp_seed": {"present": True, "sha256": WARP_SEED_SHA},
        "branch_id": role, "run_id": run_id, "pair_id": PAIR_ID,
        "continuation": continuation, "env_fork_present": True,
        "strict_cpu_rng_policy": "causalfork/sc1-strict-cpu-rng@1",
        "strict_cpu_rng_seed": 20260826,
        "cpu_rng_sha256_after_init": f10_sha,
        "cpu_rng_sha256_at_fork": f10_sha,
    }
    return meta, entries, events


def to_jsonl(meta, entries, events):
    lines = [(meta.get("seq", 0), json.dumps(meta, sort_keys=True))]
    lines += [(e["seq"], json.dumps(e, sort_keys=True)) for e in entries]
    lines += [(ev["seq"], json.dumps(ev, sort_keys=True)) for ev in events]
    lines.sort(key=lambda t: t[0])
    return "\n".join(l for _s, l in lines) + "\n"


def write_branch(dirpath, role, run_id, **kw):
    meta, entries, events = build_branch(role=role, run_id=run_id, **kw)
    path = os.path.join(dirpath, "%s.%s.drawlog.jsonl" % (role, run_id))
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(to_jsonl(meta, entries, events))
    return path


# ---------------------------------------------------------------- digests ---
def load_pin_banks():
    """Return (frame_bank_module, da3_cloud_module) from the READ-ONLY pin, or
    (None, None) when unavailable on this box."""
    try:
        import sys as _sys
        import tempfile as _tf
        pin = os.environ.get(
            "EVOKE_PIN",
            r"C:\Users\HP\AppData\Local\Temp\opencode\evoke-pin")
        if not os.path.isdir(pin):
            return None, None
        _sys.dont_write_bytecode = True
        _sys.pycache_prefix = os.path.join(_tf.gettempdir(), "sc1-util-pyc")
        if pin not in _sys.path:
            _sys.path.insert(0, pin)
        from evoke.modules.geometric_state import frame_bank as fbm
        from evoke.modules.geometric_state import da3_cloud as d3m
        return fbm, d3m
    except Exception:
        return None, None


def make_engine_like_fixture(seed=1000):
    """Engine-shaped boundary state for driving the REAL emitter adapter.

    Returns (geo_state, pipeline_stub, locals_view) where geo_state mirrors the
    audited keys of pipeline_evoke.py _geo_init_state/_geo_da3_setup, the
    pipeline stub mirrors the pipeline-persistent attributes referenced by the
    adapter, and locals_view mirrors the __call__ function-locals passed at the
    true chunk boundary (history latents/counter are post-prefix values).
    REAL FrameBank / DA3FrameBank instances from the pin are attached when
    importable; otherwise lightweight stand-ins are used (recorded honestly).
    """
    import types
    import torch
    g = torch.Generator().manual_seed(seed)

    def t(*shape):
        return torch.randn(*shape, generator=g)

    fbm, d3m = load_pin_banks()
    if fbm is not None:
        fb = fbm.FrameBank(max_size=4)
        for i in range(2):
            fb.add(torch.full((3, 8, 8), float(i)), torch.eye(4),
                   chunk_idx=i, pixel_idx=i * 10)
        bank = d3m.DA3FrameBank(device="cpu")
    else:
        fb = {"entries": [{"frame": t(3, 8, 8), "c2w": torch.eye(4)}]}
        bank = types.SimpleNamespace(
            pts={}, c2ws={}, frames={}, _pt_mask={}, _probation={},
            _carve_strike={}, _win_hist=[], _pinned_wins=[],
            _ingest_calls=0, _sr_ingests=0, _sr_last=-10 ** 9, _ca_seen=0)
    for gid in (1, 2):
        bank.pts[gid] = (t(16, 3), t(16, 3))
        bank.c2ws[gid] = torch.eye(4)
        bank.frames[gid] = (t(8, 8), torch.eye(3), torch.eye(4), t(3, 8, 8))
        bank._pt_mask[gid] = torch.ones(8, 8, dtype=torch.bool)
        bank._probation[gid] = {"mask": torch.ones(8, 8, dtype=torch.bool)}
        bank._carve_strike[gid] = torch.zeros(8, 8, dtype=torch.int16)
    bank._ingest_calls = 42

    class _Est:                                    # stream-state shape of ViGeo
        process_res = 644
        _scale_locked = None
        _anchor_scales = []

    geo_state = {
        # audited live keys (pipeline_evoke.py :589-594/:632-633/:2231-2232/:2289)
        "source_image_pixel": t(3, 33, 48),
        "frame_bank": fb,
        "prev_chunk_last_frame": t(1, 3, 33, 48),
        "prev_chunk_last_decoded_latent": t(1, 16, 1, 6, 10),
        "da3_est": _Est(),
        "da3_bank": bank,
        "da3_K_pix": t(3, 3),
        "da3_pix_stride": 36,
        "da3_lag": 1,
        "da3_is_i2v": True,
        "v2v_chunk0_anchor_pix_idx": None,
    }
    pipeline_stub = types.SimpleNamespace(
        vae=types.SimpleNamespace(_conv_idx=[0]),
        _geo_persist_feat_map=t(1, 8, 4, 6, 10),
        _decode_dump_idx=0,
    )
    locals_view = {
        "history_latents": t(1, 16, 10, 6, 10),   # post-prefix rolling buffer
        "total_generated_latent_frames": 10,       # total_generated_latent_frames
        "event_set_size": 0,
        "forced_off_flags": {
            "use_kv_cache": False, "use_cfg_zero_star": False, "use_dmd": False,
            "use_adaptive_anti_drifting": False, "use_interpolate_prompt": False,
            "geo_disable_prev_short": False, "is_keep_x0": True,
            "short_tier_noise_enabled": False,
        },
    }
    return geo_state, pipeline_stub, locals_view


def make_mock_root(seed=1234, real_banks=True):
    """Mock state-view root carrying every CANONICAL FIELD_SPEC attribute;
    attaches REAL FrameBank / DA3FrameBank instances from the pinned clone when
    importable. Attribute names match the emitter LiveStateView exactly."""
    import torch
    g = torch.Generator().manual_seed(seed)

    def t(*shape):
        return torch.randn(*shape, generator=g)

    root = {
        # F01 history latents + counter (live locals at the boundary)
        "history_latents": t(1, 16, 9, 6, 10),
        "history_latent_counter": 3,
        # F02 prev frame pix + latent (geo_state)
        "prev_frame_pix": t(1, 3, 33, 24, 40),
        "prev_frame_latent": t(1, 16, 1, 6, 10),
        # F08 counters set (audited live counters, dict-valued)
        "counters_set": {
            "da3_bank__ingest_calls": 42, "da3_bank__sr_ingests": 0,
            "da3_bank__sr_last": -10 ** 9, "da3_bank__ca_seen": 0,
        },
        # F07 persistent VAE feature cache + conv idx mirror
        "_geo_persist_feat_map": t(1, 8, 4, 6, 10),
        "_geo_persist_feat_map_conv_idx": [0],
        # F11 config mirrors (geo_state da3_* values)
        "_geo_cfg_mirror_K_pix": t(3, 3),
        "_geo_cfg_mirror_stride": 36,
        "_geo_cfg_mirror_lag": 1,
        # F09 estimator stream digest (ADVISORY)
        "estimator_stream_digest": sha("estimator-stream-%d" % seed),
        # F13 config assertions
        "_geo_source_image_sha": sha("source-image"),
        "_geo_i2v_flag_assert": True,
        "_geo_anchor_pix_idx_assert": None,
        "event_set_empty_assert": True,
        # F14 forced-off flags assertion
        "_geo_forced_off_flags": {
            "use_kv_cache": False, "use_cfg_zero_star": False, "use_dmd": False,
            "use_adaptive_anti_drifting": False, "use_interpolate_prompt": False,
            "geo_disable_prev_short": False, "is_keep_x0": True,
            "short_tier_noise_enabled": False,
        },
    }
    fb = d3 = None
    if real_banks:
        try:
            fbm, d3m = load_pin_banks()
            if fbm is not None:
                bank = fbm.FrameBank(max_size=4)
                for i in range(2):
                    bank.add(torch.full((3, 8, 8), float(i)), torch.eye(4),
                             chunk_idx=i, pixel_idx=i * 10)
                fb = bank
                dbank = d3m.DA3FrameBank(device="cpu")
                for gid in (1, 2):
                    dbank.pts[gid] = (t(16, 3), t(16, 3))
                    dbank.c2ws[gid] = torch.eye(4)
                    dbank.frames[gid] = (t(8, 8), torch.eye(3), torch.eye(4),
                                         t(3, 8, 8))
                    dbank._pt_mask[gid] = torch.ones(8, 8, dtype=torch.bool)
                    dbank._probation[gid] = {"mask": torch.ones(
                        8, 8, dtype=torch.bool)}
                    dbank._carve_strike[gid] = torch.zeros(8, 8,
                                                           dtype=torch.int16)
                d3 = dbank
        except Exception:
            fb = d3 = None
    if fb is None:
        fb = {"entries": [{"frame": t(3, 8, 8), "c2w": torch.eye(4)}]}
    if d3 is None:
        d3 = {
            "pts": {1: (t(16, 3), t(16, 3))}, "c2ws": {1: torch.eye(4)},
            "frames": {1: (t(8, 8),)}, "_pt_mask": {1: torch.ones(8, 8)},
            "_probation": {1: {}}, "_carve_strike": {1: torch.zeros(8, 8)},
            "_win_hist": [], "_pinned_wins": [],
        }
    root["geo_frame_bank"] = fb
    root["geo_da3_bank"] = d3
    return root


def make_generators():
    import torch
    return {"main": torch.Generator().manual_seed(42)}


def write_digest_pair(tmpdir, tamper_child=False):
    import fork_state_digest as fsd
    root = make_mock_root()
    gens = make_generators()
    parent = fsd.capture(root, gens, fork_chunk=1, branch_id="factual")
    ppath = fsd.save(parent, os.path.join(tmpdir, "state_parent.json"))
    child = fsd.capture(root, gens, fork_chunk=1, branch_id="counterfactual")
    if tamper_child:
        child["fields"]["F07"]["group_sha256"] = "0" * 64
        cpath = os.path.join(tmpdir, "state_child.json")
        with open(cpath, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(fsd.canonical(child) + "\n")
    else:
        cpath = fsd.save(child, os.path.join(tmpdir, "state_child.json"))
    return ppath, cpath


# ---------------------------------------------------------------- manifest --
def file_art(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return {"path": path, "sha256": h.hexdigest()}


def make_manifest(log_paths, digest_paths, run_ids, fork_chunk=1,
                  pair_id=PAIR_ID, overrides=None):
    m = {
        "schema": "causalfork/sc1-pair-manifest@2",
        "pair_id": pair_id,
        "run_ids": {"factual": run_ids[0], "counterfactual": run_ids[1]},
        "upstream_pin": PIN,
        "patch_sha256": PATCH_SHA,
        "profile_sha256": PROFILE_SHA,
        "common_config_sha256": CONFIG_SHA,
        "fork_chunk": fork_chunk,
        "warp_seed_sha256": WARP_SEED_SHA,
        "artifacts": {
            "factual_log": file_art(log_paths[0]),
            "counterfactual_log": file_art(log_paths[1]),
        },
        "parent_state_digest": file_art(digest_paths[0]),
        "child_state_digest": file_art(digest_paths[1]),
    }
    if overrides:
        for k, v in overrides.items():
            if k == "__del__":
                for dk in v:
                    m.pop(dk, None)
            else:
                m[k] = v
    return m


def standard_pair(tmpdir, chunks=3, fork_chunk=1, variant_f=None, variant_c=None,
                  run_f="run-F-fix", run_c="run-C-fix"):
    fp = write_branch(tmpdir, "factual", run_f, chunks=chunks,
                      fork_chunk=fork_chunk, variant=variant_f)
    cp = write_branch(tmpdir, "counterfactual", run_c, chunks=chunks,
                      fork_chunk=fork_chunk, variant=variant_c)
    dp, dc = write_digest_pair(tmpdir)
    man = make_manifest((fp, cp), (dp, dc), (run_f, run_c),
                        fork_chunk=fork_chunk)
    return fp, cp, man


def make_gpu01_strict_pair(tmpdir, fork_chunk=1):
    """Canonical fully admissible CPU launch-strict GPU-01 fixture.

    All subsequent strict tests must mutate this evidence rather than recreate
    partial historical archives.
    """
    import gpu01_config_identity as gci
    import gpu01_fork_protocol as gfp
    import gpu01_prelaunch as gp
    args = {"seed": 7, "height": 384, "width": 640,
            "prompt": "ordinary scene", "event_chunks": []}
    env = {"EVOKE_WARP_SEED": "77", "EVOKE_STRICT_BASE_SEED": "7",
           "EVOKE_STRICT_LAUNCH": "1"}
    identity = gci.gpu01_config_sha256(args, env)
    fp, cp, man = standard_pair(tmpdir, fork_chunk=fork_chunk)
    man.update({"launch_strict": True, "patch_sha256": "a" * 64,
                "profile_sha256": "b" * 64, "common_config_sha256": identity,
                "invocation_ids": {}, "fork_protocol_sha256": {}})
    configs = {
        "factual": {"fork_chunk": fork_chunk, "mode": "capture", "out_dir": os.path.join(tmpdir, "capture")},
        "counterfactual": {"fork_chunk": fork_chunk, "mode": "restore", "sidecar": os.path.join(tmpdir, "capture.json"),
                             "parent_state_digest": man["parent_state_digest"]["path"]},
    }
    invocation_ids = {"factual": uuid.uuid4().hex, "counterfactual": uuid.uuid4().hex}
    for role, path in (("factual", fp), ("counterfactual", cp)):
        protocol = gfp.canonical_gpu01_fork_protocol(configs[role], role)
        protocol_sha = gfp.gpu01_fork_protocol_sha256(configs[role], role)
        archive = {"schema": "causalfork/gpu01-prelaunch@1", "status": gp.GPU01_PRELAUNCH_PASS,
                   "pair_id": man["pair_id"], "run_id": man["run_ids"][role], "branch_id": role, "role": role,
                   "pin": PIN, "patch_sha256": man["patch_sha256"], "profile_sha256": man["profile_sha256"],
                   "common_config_sha256": identity, "invocation_id": invocation_ids[role],
                   "fork_protocol_sha256": protocol_sha, "canonical_fork_protocol": protocol,
                   "canonical_config": gci.canonical_gpu01_config(args, env),
                   "argv": ["python", "scripts/inference/infer_single.py", "--seed", "7"]}
        archive["argv_sha256"] = hashlib.sha256(json.dumps(archive["argv"], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        ap = os.path.join(tmpdir, role + ".prelaunch.json")
        with open(ap, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(archive, sort_keys=True) + "\n")
        ah = file_art(ap)["sha256"]
        objs = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
        for obj in objs:
            if obj.get("event") == "meta":
                obj.update(patch_sha256=man["patch_sha256"], profile_sha256=man["profile_sha256"],
                           common_config_sha256=identity, engine_resolved_config_sha256=identity,
                           engine_fork_protocol_sha256=protocol_sha, gpu01_invocation_id=invocation_ids[role],
                           prelaunch_artifact_sha256=ah)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(json.dumps(obj, sort_keys=True) for obj in objs) + "\n")
        man["artifacts"][role + "_log"] = file_art(path)
        man["artifacts"][role + "_prelaunch"] = {"path": ap, "sha256": ah,
                                                     "invocation_id": invocation_ids[role],
                                                     "fork_protocol_sha256": protocol_sha}
        man["invocation_ids"][role] = invocation_ids[role]
        man["fork_protocol_sha256"][role] = protocol_sha
    return fp, cp, man, args, env
