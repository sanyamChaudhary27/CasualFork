"""FORK_STATE_DIGEST v1 (STAGE-B/C target 6; binding spec: adjudication 2026-08-25;
canonical F-numbering: FINAL CPU ROUND 2026-08-26, mapped 1:1 onto the LIVE engine
state via patches/evoke_strict_fork.py.txt build_live_state_view - see
profiles/sc1_launcher_binding.md for the F-id -> live-source table).

Prefix hash + RNG restore are NECESSARY, NOT SUFFICIENT. This module captures a
canonical digest of the full boundary state so a child branch can prove, before
its first chunk-c* draw, that it resumed the parent's world exactly.

Field ids (canonical numbering, aligned to the live adapter):
  F01 history latents + counter                       REQUIRED
      (engine: function-local rolling buffer, pipeline_evoke.py:2299 created,
       :2502-2504/:2738/:3019-3021 consumed; counter = total_generated_latent_frames
       :2140/:2310/:2319/:3019)
  F02 prev frame pix + latent                         REQUIRED
      (geo_state["prev_chunk_last_frame"] :3088; ["prev_chunk_last_decoded_latent"]
       :2211 init / :3125 update)
  F03 Pi3X FrameBank                                  REQUIRED (geo_state["frame_bank"], :587-591)
  F04 DA3 point/frame stores pts/c2ws/frames          REQUIRED (da3_cloud.py:601-603)
  F05 DA3 masks (_pt_mask)                            REQUIRED (da3_cloud.py:606)
  F06 DA3 bank side-state _probation/_carve_strike/
      _win_hist/_pinned_wins                          REQUIRED (da3_cloud.py:530/:557/:598/:597)
  F07 persistent VAE feature cache (+conv idx)        REQUIRED (pipeline_evoke.py:467-473/:516;
                                                      conv idx = vae._conv_idx :474/:502)
  F08 counters set                                    REQUIRED (audited live counters)
  F09 estimator stream digest                         ADVISORY (REQUIRED post-O4)
  F10 DEFAULT CPU RNG state (global torch RNG)        REQUIRED (strict seeded policy, see B)
  F11 config mirrors da3_K_pix/pix_stride/lag         REQUIRED (pipeline_evoke.py:724/:725/:730)
  F12 managed generator states evidence               REQUIRED (generators= argument)
  F13 source/i2v/v2v-anchor/event_set config
      assertions                                      REQUIRED
  F14 forced-off flags assertion                      REQUIRED (all falsy under profile)
  F15 kv-cache/scheduler/_cgen/print counters         EXCLUDED (never walked)

Hashing: SHA-256 over raw contiguous bytes with a "shape|dtype|" prefix for
tensors - byte-compatible with the emitter's tensor_sha256. Manifests are
sorted-key canonical JSON; manifest_sha256 covers every field entry.

CPU-testable: `capture` walks any object exposing the declared attribute paths.
The EMITTER constructs an ephemeral non-owning LiveStateView AT THE TRUE CHUNK
BOUNDARY whose attributes map 1:1 onto the live objects above; tests attach REAL
FrameBank/DA3FrameBank instances from the pinned clone where importable; missing
attributes on a mock root are recorded honestly as MISSING.
"""
from __future__ import annotations

import hashlib
import json

SCHEMA = "causalfork/fork-state-digest@1"

# (field_id, required, [dotted attribute paths relative to the state view root])
# CANONICAL NUMBERING (2026-08-26): F01-F14 as documented in the module docstring.
# MUST stay byte-for-byte mirrored by STATE_DIGEST_FIELD_SPEC in
# patches/evoke_strict_fork.py.txt (enforced by tests DG/DG2 in
# harness/test_strict_ledger_v2.py).
FIELD_SPEC = [
    ("F01", True, ("history_latents", "history_latent_counter")),
    ("F02", True, ("prev_frame_pix", "prev_frame_latent")),
    ("F03", True, ("geo_frame_bank",)),
    ("F04", True, ("geo_da3_bank.pts", "geo_da3_bank.c2ws",
                   "geo_da3_bank.frames")),
    ("F05", True, ("geo_da3_bank._pt_mask",)),
    ("F06", True, ("geo_da3_bank._probation", "geo_da3_bank._carve_strike",
                   "geo_da3_bank._win_hist", "geo_da3_bank._pinned_wins")),
    ("F07", True, ("_geo_persist_feat_map", "_geo_persist_feat_map_conv_idx")),
    ("F08", True, ("counters_set",)),
    ("F09", False, ("estimator_stream_digest",)),
    ("F11", True, ("_geo_cfg_mirror_K_pix", "_geo_cfg_mirror_stride",
                   "_geo_cfg_mirror_lag")),
    ("F13", True, ("_geo_source_image_sha", "_geo_i2v_flag_assert",
                   "_geo_anchor_pix_idx_assert", "event_set_empty_assert")),
    ("F14", True, ("_geo_forced_off_flags",)),
]
ADVISORY_FIELDS = ("F09",)
EXCLUDED_FIELDS_NOTE = "F15 kv-cache/scheduler/_cgen/print counters excluded by ruling"
REQUIRED_FIELDS = tuple(f[0] for f in FIELD_SPEC if f[1])


def _sha_bytes(raw):
    return hashlib.sha256(raw).hexdigest()


def _tensor_entry(t):
    import torch
    tb = t.detach().contiguous().cpu()
    shape_s, dtype_s = str(list(tb.shape)), str(tb.dtype)
    try:
        raw = tb.view(torch.uint8).reshape(-1).numpy().tobytes()
    except Exception:
        raw = tb.reshape(-1).to(torch.float64).numpy().tobytes()
    h = hashlib.sha256()
    h.update(shape_s.encode()); h.update(b"|"); h.update(dtype_s.encode()); h.update(b"|")
    h.update(raw)
    return {"status": "OK", "kind": "tensor", "sha256": h.hexdigest(),
            "shape": shape_s, "dtype": dtype_s}


def digest_value(v):
    """Structural digest of an arbitrary Python value -> {status, kind, sha256,...}.

    Deterministic and dependency-light; mirrors the emitter implementation in
    evoke/strict_fork.py byte-for-byte (tested by test_strict_ledger_v2).
    """
    import torch

    def walk(o):
        if o is None:
            return "N:"
        if isinstance(o, torch.Tensor):
            e = _tensor_entry(o)
            return "T:%s:%s:%s" % (e["shape"], e["dtype"], e["sha256"])
        if isinstance(o, torch.Generator):
            st = o.get_state().contiguous().reshape(-1).numpy().tobytes()
            return "GEN:" + _sha_bytes(st)
        if isinstance(o, bool):
            return "B:" + repr(o)
        if isinstance(o, (int, float, str)):
            return "P:" + repr(o)
        if isinstance(o, dict):
            parts = ";".join("%s=%s" % (repr(k), walk(o[k])) for k in sorted(o, key=repr))
            return "D{%s}" % parts
        if isinstance(o, (list, tuple)):
            return "L[%s]" % ";".join(walk(x) for x in o)
        if isinstance(o, (set, frozenset)):
            return "S{%s}" % ";".join(sorted(repr(x) for x in o))
        d = getattr(o, "__dict__", None)
        if d is not None:
            inner = ";".join("%s=%s" % (k, walk(d[k])) for k in sorted(d))
            return "O<%s>{%s}" % (type(o).__name__, inner)
        return "X:" + repr(o)

    payload = walk(v)
    return {"status": "OK", "kind": type(v).__name__,
            "sha256": _sha_bytes(payload.encode("utf-8"))}


def _resolve(root, dotted):
    cur = root
    for part in dotted.split("."):
        if isinstance(cur, dict):
            if part not in cur:
                return False, None
            cur = cur[part]
        else:
            if not hasattr(cur, part):
                return False, None
            cur = getattr(cur, part)
    return True, cur


def capture(root, generators=None, fork_chunk=None, branch_id=None,
            pin="74d268516d95c8fceadd2378f91a73f9f187042b"):
    """Build a FORK_STATE_DIGEST manifest from a pipeline-like root object."""
    fields = {}
    missing_required = []
    for fid, required, paths in FIELD_SPEC:
        entries = {}
        values = []
        for path in paths:
            ok, v = _resolve(root, path)
            if ok:
                e = digest_value(v)
                e["path"] = path
                entries[path] = e
                values.append("%s=%s" % (path, e["sha256"]))
            else:
                entries[path] = {"status": "MISSING", "path": path}
        group_sha = _sha_bytes((";".join(values)).encode("utf-8"))
        present = all(entries[p]["status"] == "OK" for p in paths)
        fields[fid] = {"required": required, "paths": entries,
                       "group_sha256": group_sha, "present": present}
        if required and not present:
            missing_required.extend(p for p in paths if entries[p]["status"] == "MISSING")

    # F12 managed generator states evidence (REQUIRED).
    gens = {}
    for name in sorted(generators or {}):
        g = generators[name]
        if g is None:
            gens[name] = {"status": "MISSING"}
        else:
            import torch
            st = g.get_state().contiguous().reshape(-1).numpy().tobytes()
            gens[name] = {"status": "OK", "sha256": _sha_bytes(st), "nbytes": len(st)}
    fields["F12"] = {"required": True, "generators": gens}
    # F10 DEFAULT CPU RNG state (REQUIRED). Policy evidence (derived seed /
    # init sha / at-fork sha) lives in the LEDGER META and FORK_CAPTURE sidecar,
    # never in this manifest, so the harness and patched-emitter implementations
    # stay byte-compatible given identical inputs (test DG2).
    import torch
    try:
        gst = torch.get_rng_state().contiguous().reshape(-1).numpy().tobytes()
        global_cpu = _sha_bytes(gst)
    except Exception:
        global_cpu = None
    fields["F10"] = {"required": True, "global_cpu_rng_sha256": global_cpu}

    manifest = {
        "schema": SCHEMA,
        "pin": pin,
        "branch_id": branch_id,
        "fork_chunk": fork_chunk,
        "fields": fields,
        "excluded_note": EXCLUDED_FIELDS_NOTE,
    }
    body = json.dumps(manifest, sort_keys=True, separators=(",", ":"))
    manifest["manifest_sha256"] = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if missing_required:
        manifest["missing_required_paths"] = sorted(missing_required)
    return manifest


def canonical(manifest):
    m = dict(manifest)
    m.pop("manifest_sha256", None)
    return json.dumps(m, sort_keys=True, separators=(",", ":"))


def save(manifest, path):
    """Write the FULL manifest including manifest_sha256 (sorted-key JSON)."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n")
    return path


def load(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def compare(parent, child, require_advisory=False):
    """parent/child: manifest dicts (or JSON strings). Returns a match report."""
    if isinstance(parent, str):
        parent = json.loads(parent)
    if isinstance(child, str):
        child = json.loads(child)
    mismatches, missing, advisory = [], [], []
    pf, cf = parent.get("fields", {}), child.get("fields", {})
    # structural sanity first
    p_ok = parent.get("manifest_sha256") and \
        hashlib.sha256(canonical(parent).encode("utf-8")).hexdigest() == parent["manifest_sha256"]
    c_ok = child.get("manifest_sha256") and \
        hashlib.sha256(canonical(child).encode("utf-8")).hexdigest() == child["manifest_sha256"]
    if not p_ok:
        mismatches.append({"field": "<manifest>", "reason": "PARENT_DIGEST_CORRUPT"})
    if not c_ok:
        mismatches.append({"field": "<manifest>", "reason": "CHILD_DIGEST_CORRUPT"})

    for fid in sorted(set(pf) | set(cf)):
        pv, cv = pf.get(fid), cf.get(fid)
        if pv is None or cv is None:
            missing.append({"field": fid,
                            "side": "child" if pv else "parent"})
            continue
        pg = pv.get("group_sha256")
        cg = cv.get("group_sha256")
        if pg is not None and cg is not None:
            same = (pg == cg)
        else:  # F10/F12-style fields without group hash
            same = json.dumps({k: v for k, v in sorted(pv.items()) if k != "required"},
                              sort_keys=True) == \
                   json.dumps({k: v for k, v in sorted(cv.items()) if k != "required"},
                              sort_keys=True)
        if not same:
            rec = {"field": fid}
            if fid in ADVISORY_FIELDS:
                advisory.append(rec)
            else:
                mismatches.append(dict(rec, reason="VALUE_MISMATCH"))
        for side_name, side in (("parent_missing_path", pv), ("child_missing_path", cv)):
            for p, e in (side.get("paths") or {}).items():
                if e.get("status") == "MISSING":
                    if fid in ADVISORY_FIELDS:
                        advisory.append({"field": fid, side_name: p})
                    else:
                        missing.append({"field": fid, "path": p})

    report = {
        "match": not mismatches and not missing and
                 (not require_advisory or not advisory),
        "mismatches": mismatches,
        "missing": missing,
        "advisory_diffs": advisory,
        "require_advisory": require_advisory,
    }
    return report