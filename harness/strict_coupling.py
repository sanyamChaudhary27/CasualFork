"""SC1 STRICT-COUPLING VALIDATOR V2 (STAGE-B/C fix round; supersedes v1).

Binding inputs: fanin/2026-08-25-semantics/adjudication.md (sealed 3-way,
2026-08-25). v1 verdicts are BARRED from gate evidence (Auditor B ruling);
v2 closes every v1 hole and adds site-aware comparison semantics.

Verdicts
--------
STRICT_NOISE_COUPLED      every reachable post-fork stochastic site behaved
                          exactly as its adjudicated class requires.
STRICT_COUPLING_INVALID   any violation whatsoever (machine-readable reasons).

Entry point
-----------
    validate_pair(factual_log, cf_log, pair_manifest,
                  factual_role="factual", cf_role="counterfactual")

The PAIR MANIFEST (third argument) is REQUIRED: it binds both ledgers to one
pair_id, distinct run_ids, the profile/patch/config hashes, fork_chunk and the
FORK_STATE_DIGEST artifacts. compare_coupling_logs() is kept as a thin alias.

Site comparison policy (adjudication table, binding):
  R1 R4 R5 R6  EXACT_TENSOR             tensor_sha256 equality required
  R2 R3        STREAM_WITNESS           gen-state bracket + shape/count;
                                        diagnostics sha256_input_pixels/mean/std
                                        byte-equal at chunk<=fork_chunk;
                                        recorded-only after divergence begins;
                                        z-tensor equality NOT required there
  R7           ISOLATED_STREAM_WITNESS  per-draw state chain per render call;
                                        chains must match until the first
                                        EXPLAINED domain divergence (high/skip
                                        difference); index tensor NEVER compared

v1 holes closed: self-pair guard, explicit roles+label enforcement, distinct
run_ids/pair_id, single meta header, full meta comparison (pin, patch sha,
profile sha, torch/diffusers strings, warp seed, common config, fork_chunk),
event validation (FORK_CAPTURE / GENERATOR_STATE_RESTORED at fork_chunk before
any post-fork draw), lazy continuation fix (restored_branches come from real
restore events), pair-manifest binding with artifact hashes, unique-ledger /
append-mixing detection via run_id/pair_id on every line.
"""
from __future__ import annotations

import hashlib
import json
import os

STRICT_NOISE_COUPLED = "STRICT_NOISE_COUPLED"
STRICT_COUPLING_INVALID = "STRICT_COUPLING_INVALID"
GENERATOR_STATE_RESTORED = "GENERATOR_STATE_RESTORED"
COUPLING_STATUSES = (STRICT_NOISE_COUPLED, STRICT_COUPLING_INVALID)

REQUIRED_SITES = ("R1", "R2", "R3", "R4", "R5", "R6", "R7")
MAIN_STREAM_SITES = ("R1", "R2", "R3", "R4", "R5", "R6")
ISOLATED_SITES = ("R7",)
EXACT_TENSOR_SITES = ("R1", "R4", "R5", "R6")
STREAM_WITNESS_SITES = ("R2", "R3")

MANIFEST_SCHEMA = "causalfork/sc1-pair-manifest@2"
MANIFEST_REQUIRED_FIELDS = (
    "schema", "pair_id", "run_ids", "upstream_pin", "patch_sha256",
    "profile_sha256", "common_config_sha256", "fork_chunk",
    "parent_state_digest", "child_state_digest",
)

CORE_ENTRY_FIELDS = ("site_id", "ordinal", "tensor_sha256", "shape", "dtype")
STREAM_ENTRY_FIELDS = ("generator_state_hash_before", "generator_state_hash_after")
COMPARED_FIELDS = ("chunk", "stage", "shape", "dtype")

R2_R3_DIAG_FIELDS = ("sha256_input_pixels", "sha256_mean", "sha256_std")

# FINAL CPU ROUND additions ----------------------------------------------------
# Identity fields whose literal "UNDECLARED"/"TEST_MODE_ONLY" values are illegal
# once the archived manifest declares literal launch_strict=true. Such ledgers
# can never be GPU-countersigned either
# (see refuse_gpu_countersign).
IDENTITY_META_FIELDS = ("patch_sha256", "profile_sha256",
                        "common_config_sha256", "diffusers")
IDENTITY_MARKERS = ("UNDECLARED", "TEST_MODE_ONLY")
ENV_LAUNCH_STRICT = "EVOKE_STRICT_LAUNCH"
# Emitter-side lazy-meta rewrite failure marker (condition 4/E).
META_PATCH_FAILURE = "META_PATCH_FAILURE"
# Strict CPU RNG evidence recorded by the emitter meta (condition B); both
# branches must carry identical values because the seed derivation excludes
# branch identity.
STRICT_CPU_META_FIELDS = ("strict_cpu_rng_policy", "strict_cpu_rng_seed",
                          "cpu_rng_sha256_after_init",
                          "cpu_rng_sha256_at_fork")


def validate_status(status):
    """Guard terminology: only coupling verdicts are legal statuses."""
    if status not in COUPLING_STATUSES:
        raise ValueError(
            "illegal coupling status %r; use STRICT_NOISE_COUPLED / "
            "STRICT_COUPLING_INVALID (GENERATOR_STATE_RESTORED is a continuation "
            "label, never a coupling verdict)" % (status,)
        )
    return status


def is_pass(result):
    return result.get("status") == STRICT_NOISE_COUPLED


# ---------------------------------------------------------------- ledger I/O --
def _read_text(source):
    """Resolve a log source (path | JSONL text | file handle) to text."""
    if hasattr(source, "read"):
        return source.read()
    if isinstance(source, str):
        if os.path.exists(source):
            with open(source, "r", encoding="utf-8") as fh:
                return fh.read()
        if source.lstrip().startswith("{"):
            return source
        raise ValueError("ledger source not found and not JSONL text: %r"
                         % source[:80])
    raise TypeError("unsupported ledger source: %r" % type(source))


def load_log(source):
    """Parse one ledger -> dict(metas=[...], entries=[...], events=[...], text=...).

    Raises ValueError on JSON parse errors. Does NOT decide multi-meta here.
    """
    text = _read_text(source)
    metas, entries, events = [], [], []
    for lineno, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception as exc:
            raise ValueError("parse error at line %d: %s" % (lineno, exc))
        if not isinstance(obj, dict):
            raise ValueError("parse error at line %d: JSON value must be an object"
                             % lineno)
        event = obj.get("event")
        if event == "meta":
            metas.append(obj)
        elif event == "draw":
            entries.append(obj)
        elif event is not None:
            events.append(obj)
    return {"metas": metas, "entries": entries, "events": events, "text": text}


def _key(e):
    return (e.get("site_id"), e.get("ordinal"), e.get("chunk"))


def _invalid(reasons, extra=None):
    res = {
        "status": STRICT_COUPLING_INVALID,
        "reasons": list(reasons),
        "entries_compared": 0,
        "sites": [],
        "continuation": {"factual": None, "counterfactual": None},
        "restored_branches": [],
        "diagnostics": [],
        "grammar_violations": [],
        "pair_id": None,
        "run_ids": None,
    }
    res.update(extra or {})
    validate_status(res["status"])
    return res


# ------------------------------------------------------------- manifest ------
def resolve_manifest(manifest):
    if isinstance(manifest, dict):
        return dict(manifest)
    txt = _read_text(manifest) if isinstance(manifest, str) else None
    try:
        obj = json.loads(txt)
    except Exception:
        raise ValueError("pair manifest is neither a dict nor JSON/path: %r"
                         % (manifest,))
    if not isinstance(obj, dict):
        raise ValueError("pair manifest must decode to an object")
    return obj


def check_manifest(m):
    missing = [k for k in MANIFEST_REQUIRED_FIELDS if k not in m]
    if missing:
        return ["PAIR_MANIFEST_INCOMPLETE: missing %s" % ",".join(missing)]
    if m["schema"] != MANIFEST_SCHEMA:
        return ["PAIR_MANIFEST_SCHEMA:%r != %r" % (m["schema"], MANIFEST_SCHEMA)]
    run_ids = m["run_ids"]
    if not isinstance(run_ids, dict) or \
            any(r not in run_ids for r in ("factual", "counterfactual")):
        return ["PAIR_MANIFEST_RUN_IDS: need entries for factual+counterfactual"]
    def null_or_empty(value):
        return value is None or (hasattr(value, "__len__") and len(value) == 0)

    required_values = ("pair_id", "upstream_pin", "patch_sha256",
                       "profile_sha256", "common_config_sha256",
                       "parent_state_digest", "child_state_digest")
    for key in required_values:
        if null_or_empty(m.get(key)):
            return ["PAIR_MANIFEST_REQUIRED_VALUE:%s is null/empty" % key]
    for role in ("factual", "counterfactual"):
        if null_or_empty(run_ids.get(role)):
            return ["PAIR_MANIFEST_REQUIRED_VALUE:run_ids.%s is null/empty" % role]
    if run_ids["factual"] == run_ids["counterfactual"]:
        return ["RUN_ID_COLLISION: manifest declares identical run_ids"]
    try:
        int(m["fork_chunk"])
    except Exception:
        return ["PAIR_MANIFEST_FORK_CHUNK: not an int"]
    # Ledger-artifact hash bindings are MANDATORY for both roles so a pair can
    # always be re-verified against its exact bytes (condition 3/D).
    arts = m.get("artifacts")
    if not isinstance(arts, dict) or \
            any(k not in arts for k in ("factual_log", "counterfactual_log")):
        return ["PAIR_MANIFEST_ARTIFACTS: need factual_log+counterfactual_log "
                "artifact bindings"]
    for rk in ("factual_log", "counterfactual_log"):
        spec = arts[rk]
        if not isinstance(spec, dict) or not spec.get("sha256"):
            return ["PAIR_MANIFEST_ARTIFACT_SHA:%s missing sha256 binding" % rk]
    # GPU evidence is opt-in only via a literal JSON true. Ordinary CPU fixtures
    # remain valid without prelaunch archives; GPU archives must bind both bytes.
    if m.get("launch_strict") is True:
        for role in ("factual", "counterfactual"):
            key = role + "_prelaunch"
            spec = arts.get(key)
            if not isinstance(spec, dict) or not spec.get("path") or \
                    not _is_sha256(spec.get("sha256")) or not spec.get("invocation_id") or \
                    not _is_sha256(spec.get("fork_protocol_sha256")):
                return ["GPU01_PRELAUNCH_EVIDENCE_MISSING:%s" % key]
            if (m.get("invocation_ids") or {}).get(role) != spec.get("invocation_id") or \
                    (m.get("fork_protocol_sha256") or {}).get(role) != spec.get("fork_protocol_sha256"):
                return ["GPU01_PRELAUNCH_EVIDENCE_MISSING:%s:manifest_binding" % key]
    return []


def file_sha256(path):
    hh = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            hh.update(chunk)
    return hh.hexdigest()


def _safe_int(v):
    """int() that never raises: returns None for None/garbage (condition 2/C)."""
    try:
        if isinstance(v, bool):
            return int(v)
        return int(v)
    except Exception:
        return None


def _artifact_sha(spec):
    path = spec.get("path")
    h = spec.get("sha256")
    if path and h is None:
        h = file_sha256(path)
    return path, h


def _is_sha256(value):
    return isinstance(value, str) and len(value) == 64 and \
        all(ch in "0123456789abcdefABCDEF" for ch in value)


def _validate_prelaunch_artifact(spec, manifest, ledger_meta, role):
    """Validate one immutable wrapper archive against its ledger and manifest."""
    try:
        path, want = _artifact_sha(spec)
        if not path or not want or file_sha256(path) != want:
            return ["GPU01_PRELAUNCH_EVIDENCE_MISSING:%s:artifact_hash" % role]
        with open(path, "r", encoding="utf-8") as fh:
            artifact = json.load(fh)
        if not isinstance(artifact, dict) or \
                artifact.get("schema") != "causalfork/gpu01-prelaunch@1" or \
                artifact.get("status") != "GPU01_PRELAUNCH_PASS":
            return ["GPU01_PRELAUNCH_EVIDENCE_MISSING:%s:status" % role]
        expected = {
            "pair_id": manifest.get("pair_id"), "run_id": manifest["run_ids"].get(role),
            "branch_id": role, "role": role, "pin": ledger_meta.get("pin"),
            "patch_sha256": manifest.get("patch_sha256"),
            "profile_sha256": manifest.get("profile_sha256"),
            "common_config_sha256": manifest.get("common_config_sha256"),
            "invocation_id": (manifest.get("invocation_ids") or {}).get(role),
            "fork_protocol_sha256": (manifest.get("fork_protocol_sha256") or {}).get(role),
        }
        if any(artifact.get(k) != v for k, v in expected.items()):
            return ["GPU01_PRELAUNCH_EVIDENCE_MISSING:%s:identity" % role]
        config = artifact.get("canonical_config")
        argv = artifact.get("argv")
        canonical_argv = json.dumps(argv, sort_keys=True, separators=(",", ":"),
                                   ensure_ascii=True).encode("utf-8")
        if not isinstance(config, dict) or not isinstance(argv, list) or \
                artifact.get("argv_sha256") != hashlib.sha256(canonical_argv).hexdigest():
            return ["GPU01_PRELAUNCH_EVIDENCE_MISSING:%s:structural" % role]
        common = artifact.get("common_config_sha256")
        if common != ledger_meta.get("engine_resolved_config_sha256") or \
                common != ledger_meta.get("common_config_sha256"):
            return ["GPU01_PRELAUNCH_EVIDENCE_MISSING:%s:config_binding" % role]
        if artifact.get("invocation_id") != ledger_meta.get("gpu01_invocation_id"):
            return ["GPU01_PRELAUNCH_EVIDENCE_MISSING:%s:invocation_binding" % role]
        if artifact.get("fork_protocol_sha256") != ledger_meta.get("engine_fork_protocol_sha256"):
            return ["GPU01_PRELAUNCH_EVIDENCE_MISSING:%s:fork_protocol_binding" % role]
        if ledger_meta.get("prelaunch_artifact_sha256") != want:
            return ["GPU01_PRELAUNCH_EVIDENCE_MISSING:%s:ledger_archive_sha" % role]
    except Exception:
        return ["GPU01_PRELAUNCH_EVIDENCE_MISSING:%s:load" % role]
    return []


def validate_loaded_boundary_digest(manifest, ledger_meta, role):
    """Validate the loaded digest's F10/F12 evidence for one branch.

    ``role`` is the corresponding factual/counterfactual ledger role; ledger_meta
    is that run's header. This intentionally validates each
    artifact before the cross-artifact comparison so equal forged values cannot
    stand in for per-run boundary evidence.
    """
    reasons = []
    fields = manifest.get("fields") if isinstance(manifest, dict) else None
    if not isinstance(fields, dict):
        return ["F10_DIGEST_MISSING:%s" % role,
                "F12_DIGEST_MISSING:%s" % role]

    f10 = fields.get("F10")
    if not isinstance(f10, dict) or "global_cpu_rng_sha256" not in f10:
        reasons.append("F10_DIGEST_MISSING:%s" % role)
    else:
        digest_sha = f10.get("global_cpu_rng_sha256")
        if digest_sha is None:
            reasons.append("F10_DIGEST_NULL:%s" % role)
        elif not _is_sha256(digest_sha):
            reasons.append("F10_DIGEST_INVALID:%s" % role)
        else:
            ledger_sha = ledger_meta.get("cpu_rng_sha256_at_fork") \
                if isinstance(ledger_meta, dict) else None
            if ledger_sha is None:
                reasons.append("F10_LEDGER_MISSING:%s" % role)
            elif not _is_sha256(ledger_sha):
                reasons.append("F10_LEDGER_INVALID:%s" % role)
            elif digest_sha != ledger_sha:
                reasons.append("F10_LEDGER_BIND_MISMATCH:%s" % role)

    f12 = fields.get("F12")
    if not isinstance(f12, dict):
        reasons.append("F12_DIGEST_MISSING:%s" % role)
    else:
        generators = f12.get("generators")
        if not isinstance(generators, dict):
            reasons.append("F12_GENERATORS_MISSING:%s" % role)
        elif "main" not in generators:
            reasons.append("F12_MAIN_MISSING:%s" % role)
        else:
            main = generators["main"]
            if not isinstance(main, dict):
                reasons.append("F12_MAIN_INVALID:%s" % role)
            else:
                if main.get("status") != "OK":
                    reasons.append("F12_MAIN_STATUS_INVALID:%s" % role)
                if not _is_sha256(main.get("sha256")):
                    reasons.append("F12_MAIN_SHA256_INVALID:%s" % role)
                nbytes = main.get("nbytes")
                if isinstance(nbytes, bool) or not isinstance(nbytes, int) or nbytes <= 0:
                    reasons.append("F12_MAIN_NBYTES_INVALID:%s" % role)
    return reasons


# ------------------------------------------------------------- main entry ----
def validate_pair(factual_log, cf_log, pair_manifest,
                  factual_role="factual", cf_role="counterfactual"):
    reasons = []
    # -- roles ---------------------------------------------------------------
    if factual_role == cf_role:
        return _invalid(["ROLES_NOT_DISTINCT:%r" % factual_role])
    try:
        m = resolve_manifest(pair_manifest)
    except ValueError as exc:
        return _invalid(["PAIR_MANIFEST_REQUIRED:%s" % exc])
    mreasons = check_manifest(m)
    if mreasons:
        return _invalid(mreasons)
    fork_chunk = int(m["fork_chunk"])

    # -- self-pair guard -----------------------------------------------------
    same_source = False
    if isinstance(factual_log, str) and isinstance(cf_log, str):
        fa = os.path.abspath(factual_log) if os.path.exists(factual_log) else None
        ca = os.path.abspath(cf_log) if os.path.exists(cf_log) else None
        if fa and ca:
            same_source = (fa == ca)
    try:
        F = load_log(factual_log)
        C = load_log(cf_log)
    except ValueError as exc:
        return _invalid(["LEDGER_PARSE_ERROR:%s" % exc])
    if same_source or F["text"] == C["text"]:
        return _invalid(["SELF_PAIR:factual and counterfactual logs are "
                         "identical sources"])

    # -- artifact binding ------------------------------------------------------
    for role_key, parsed in ((factual_role, F), (cf_role, C)):
        art = (m.get("artifacts") or {}).get("%s_log" % role_key)
        if art:
            _p, want = _artifact_sha(art)
            got = hashlib.sha256(parsed["text"].encode("utf-8")).hexdigest()
            if want and want != got:
                reasons.append("ARTIFACT_HASH_MISMATCH:%s_log" % role_key)

    # -- meta headers ----------------------------------------------------------
    out = {}
    for role, parsed in ((factual_role, F), (cf_role, C)):
        if len(parsed["metas"]) == 0:
            reasons.append("MISSING_META_HEADER:%s" % role)
        elif len(parsed["metas"]) > 1:
            reasons.append("MULTI_META_HEADER:%s count=%d" % (role, len(parsed["metas"])))
        else:
            meta = parsed["metas"][0]
            out[role] = meta
            if meta.get("branch_id") != role:
                reasons.append("ROLE_LABEL_MISMATCH:%s branch_id=%r"
                               % (role, meta.get("branch_id")))
    fm, cm = out.get(factual_role), out.get(cf_role)
    if fm is None or cm is None:
        return _invalid(reasons)

    # -- run_ids / pair binding ----------------------------------------------
    f_run, c_run = fm.get("run_id"), cm.get("run_id")
    if f_run is None or c_run is None:
        reasons.append("RUN_ID_MISSING:both ledgers must carry run_id in meta")
    if m["run_ids"].get(factual_role) != f_run:
        reasons.append("RUN_ID_MANIFEST_MISMATCH:%s meta=%r manifest=%r"
                       % (factual_role, f_run, m["run_ids"].get(factual_role)))
    if m["run_ids"].get(cf_role) != c_run:
        reasons.append("RUN_ID_MANIFEST_MISMATCH:%s meta=%r manifest=%r"
                       % (cf_role, c_run, m["run_ids"].get(cf_role)))
    if f_run is not None and f_run == c_run:
        reasons.append("RUN_ID_COLLISION:same run_id in both ledgers (%r)" % f_run)

    # -- append-mixing detection ---------------------------------------------
    for role, parsed in ((factual_role, F), (cf_role, C)):
        rid = fm.get("run_id") if role == factual_role else cm.get("run_id")
        pid = m["pair_id"]
        seen_keys = set()
        seq_prev = -1
        lines = ([parsed["metas"][0]] + parsed["entries"] + parsed["events"]) \
            if len(parsed["metas"]) == 1 else []
        for ln in lines:
            if ln.get("run_id") is not None and ln.get("run_id") != rid:
                reasons.append("LEDGER_APPEND_MIX:%s line run_id=%r != header %r"
                               % (role, ln.get("run_id"), rid))
            if ln.get("pair_id") is not None and ln.get("pair_id") != pid:
                reasons.append("PAIR_ID_MISMATCH:%s line pair_id=%r != manifest %r"
                               % (role, ln.get("pair_id"), pid))
            if ln.get("event") == "draw":
                kk = _key(ln)
                if kk in seen_keys:
                    reasons.append("APPEND_MIX_DUPLICATE:%s %s#%s@chunk%s"
                                   % ((role,) + kk))
                seen_keys.add(kk)
                sv = ln.get("seq", 0)
                if isinstance(sv, int):
                    if sv <= seq_prev:
                        reasons.append("SEQ_REGRESSION:%s at seq=%r after %d"
                                       % (role, sv, seq_prev))
                    seq_prev = sv

    # -- meta comparison (across branches AND against the manifest) -----------
    META_CHECKS = (
        ("pin", "upstream_pin"), ("patch_sha256", "patch_sha256"),
        ("profile_sha256", "profile_sha256"),
        ("common_config_sha256", "common_config_sha256"),
    )
    for meta_field, man_field in META_CHECKS:
        fv, cv = fm.get(meta_field), cm.get(meta_field)
        mv = m.get(man_field)
        if mv is not None:
            if fv != mv:
                reasons.append("META_MISMATCH:%s factual=%r manifest=%r"
                               % (meta_field, fv, mv))
            if cv != mv:
                reasons.append("META_MISMATCH:%s counterfactual=%r manifest=%r"
                               % (meta_field, cv, mv))
        elif fv != cv:
            reasons.append("META_MISMATCH:%s across branches" % meta_field)
    fc_f, fc_c = _safe_int(fm.get("fork_chunk")), _safe_int(cm.get("fork_chunk"))
    if fc_f is None or fc_c is None or fc_f != fork_chunk or fc_c != fork_chunk:
        reasons.append("META_MISMATCH:fork_chunk factual=%r cf=%r manifest=%r "
                       "(malformed/missing numeric meta -> META_MISMATCH, "
                       "never a crash)" %
                       (fm.get("fork_chunk"), cm.get("fork_chunk"),
                        m.get("fork_chunk")))
    for soft in ("torch", "diffusers"):
        fv, cv = fm.get(soft), cm.get(soft)
        if fv != cv:
            if soft == "diffusers" and any(x in (fv, cv)
                                           for x in IDENTITY_MARKERS):
                continue  # graceful when diffusers absent locally/emitter-side;
                          # launch-strict re-flags it below and the GPU
                          # countersign helper refuses it unconditionally
            reasons.append("META_MISMATCH:%s across branches" % soft)
    fw, cw = fm.get("warp_seed"), cm.get("warp_seed")
    if not isinstance(fw, dict) or not isinstance(cw, dict):
        reasons.append("META_MISMATCH:warp_seed factual=%r cf=%r (expected object)"
                       % (fw, cw))
        fw, cw = {}, {}
    elif fw != cw:
        reasons.append("META_MISMATCH:warp_seed factual=%r cf=%r" % (fw, cw))
    if fw.get("present") is not True:
        reasons.append("PRECOND1_GLOBAL_RNG_BYPASS:meta warp_seed absent")
    mw = m.get("warp_seed_sha256")
    if mw and fw.get("sha256") != mw:
        reasons.append("META_MISMATCH:warp_seed_sha vs manifest")

    # -- strict CPU RNG evidence (condition B) --------------------------------
    for sfield in STRICT_CPU_META_FIELDS:
        sv, cv_ = fm.get(sfield), cm.get(sfield)
        if sv is None or cv_ is None:
            reasons.append("F10_EVIDENCE_MISSING:%s factual=%r cf=%r"
                           % (sfield, sv, cv_))
        elif sv != cv_:
            reasons.append("META_MISMATCH:%s factual=%r cf=%r "
                           "(derived seed is branch-independent)"
                           % (sfield, sv, cv_))

    # -- launch-strict identity gate (condition 3/D) ---------------------------
    launch_strict = m.get("launch_strict") is True
    if launch_strict:
        for role_key, meta_r in ((factual_role, fm), (cf_role, cm)):
            for idf in IDENTITY_META_FIELDS:
                iv = meta_r.get(idf)
                if iv is None or iv in IDENTITY_MARKERS:
                    reasons.append(
                        "IDENTITY_UNDECLARED:%s:%s value=%r (literal UNDECLARED/"
                        "TEST_MODE_ONLY identity is ILLEGAL in launch-strict mode)"
                         % (idf, role_key, iv))
        for role_key, meta_r in ((factual_role, fm), (cf_role, cm)):
            spec = (m.get("artifacts") or {}).get(role_key + "_prelaunch")
            reasons.extend(_validate_prelaunch_artifact(spec, m, meta_r, role_key))
        # Fork protocol is role-specific by design: capture vs restore must differ,
        # while fork chunk is shared and common causal config is equal above.
        try:
            import gpu01_fork_protocol as _fp
            for role_key, meta_r in ((factual_role, fm), (cf_role, cm)):
                spec = (m.get("artifacts") or {}).get(role_key + "_prelaunch")
                with open(spec["path"], "r", encoding="utf-8") as fh:
                    artifact = json.load(fh)
                protocol = artifact.get("canonical_fork_protocol")
                semantic = (protocol or {}).get("semantic")
                if not isinstance(semantic, dict) or semantic.get("role") != role_key or \
                        semantic.get("fork_chunk") != fork_chunk or \
                        semantic.get("mode") != ("capture" if role_key == factual_role else "restore"):
                    reasons.append("GPU01_FORK_PROTOCOL_INVALID:%s" % role_key)
                if role_key == factual_role and not (protocol.get("operational") or {}).get("out_dir"):
                    reasons.append("GPU01_FORK_PROTOCOL_INVALID:%s:out_dir" % role_key)
                if role_key == cf_role and (not (protocol.get("operational") or {}).get("sidecar") or
                                            not (protocol.get("operational") or {}).get("parent_state_digest")):
                    reasons.append("GPU01_FORK_PROTOCOL_INVALID:%s:restore_evidence" % role_key)
        except Exception:
            reasons.append("GPU01_FORK_PROTOCOL_INVALID:load")

    # -- lazy-meta rewrite failure marker (condition 4/E) ----------------------
    for role_key, parsed in ((factual_role, F), (cf_role, C)):
        if any(e.get("event") == META_PATCH_FAILURE for e in parsed["events"]):
            reasons.append("META_CONTINUATION_UNVERIFIED:%s ledger carries a %s "
                           "event; strict certification aborts"
                           % (role_key, META_PATCH_FAILURE))

    # -- events at the fork boundary ------------------------------------------
    f_cap = [e for e in F["events"]
             if e.get("event") == "FORK_CAPTURE" and e.get("chunk") == fork_chunk]
    c_res = [e for e in C["events"]
             if e.get("event") == GENERATOR_STATE_RESTORED and e.get("chunk") == fork_chunk]
    if not f_cap:
        reasons.append("MISSING_EVENT:FORK_CAPTURE@%d (%s)" % (fork_chunk, factual_role))
    if not c_res:
        reasons.append("MISSING_EVENT:GENERATOR_STATE_RESTORED@%d (%s)"
                       % (fork_chunk, cf_role))
    restored_branches = []
    if c_res:
        restored_branches.append(cf_role)
        first_post = min((e.get("seq", 1 << 60) for e in C["entries"]
                          if isinstance(e.get("chunk"), int) and e["chunk"] >= fork_chunk),
                         default=None)
        res_seq = min(e.get("seq", 1 << 60) for e in c_res)
        if first_post is not None and res_seq > first_post:
            reasons.append("RESTORE_AFTER_POSTFORK_DRAW:restore seq=%s > first "
                           "post-fork draw seq=%s" % (res_seq, first_post))
        if cm.get("continuation") != GENERATOR_STATE_RESTORED:
            reasons.append("RESTORE_METADATA_MISMATCH:restore event present but "
                           "meta.continuation=%r" % cm.get("continuation"))
    elif len(C["metas"]) == 1 and cm.get("continuation") == GENERATOR_STATE_RESTORED:
        # lazy-continuation bug (v1): claim without a real restore event
        reasons.append("RESTORE_METADATA_MISMATCH:meta claims %s without a "
                       "GENERATOR_STATE_RESTORED event" % GENERATOR_STATE_RESTORED)
    if f_cap and fm.get("continuation") is not None:
        reasons.append("RESTORE_METADATA_MISMATCH:factual parent must not claim "
                       "continuation=%r" % fm.get("continuation"))

    # -- coverage / alignment ---------------------------------------------------
    def build_map(entries, role_label):
        d = {}
        for e in entries:
            kk = _key(e)
            if kk in d:
                reasons.append("APPEND_MIX_DUPLICATE:%s %s#%s@chunk%s"
                               % ((role_label,) + kk))
            d[kk] = e
        return d

    fd = build_map(F["entries"], factual_role)
    cd = build_map(C["entries"], cf_role)
    f_sites = {kk[0] for kk in fd}
    c_sites = {kk[0] for kk in cd}
    for site in REQUIRED_SITES:
        if site not in f_sites:
            reasons.append("MISSING_SITE:%s (%s)" % (site, factual_role))
        if site not in c_sites:
            reasons.append("MISSING_SITE:%s (%s)" % (site, cf_role))
    for site in sorted((f_sites | c_sites) - set(REQUIRED_SITES)):
        reasons.append("UNEXPECTED_SITE:%s" % site)
    for key in sorted(set(fd) - set(cd)):
        reasons.append("MISSING_SITE:%s#%s@chunk%s (%s)" % (key + (cf_role,)))
    for key in sorted(set(cd) - set(fd)):
        reasons.append("MISSING_SITE:%s#%s@chunk%s (%s)" % (key + (factual_role,)))

    # -- grammar -----------------------------------------------------------------
    import sc1_grammar
    grammar_violations = []
    for role, parsed in ((factual_role, F), (cf_role, C)):
        gres, _n = sc1_grammar.validate_ledger(parsed["entries"], fork_chunk)
        grammar_violations.extend(gres)
    reasons.extend(grammar_violations)

    # -- aligned comparisons ------------------------------------------------------
    compared = 0
    diagnostics = []
    for key in sorted(set(fd) & set(cd)):
        fe, ce = fd[key], cd[key]
        label = "%s#%s@chunk%s" % key
        site = key[0]
        chunk = key[2] if isinstance(key[2], int) else -1
        pre_divergence = chunk <= fork_chunk
        for field in COMPARED_FIELDS:
            if fe.get(field) != ce.get(field):
                reasons.append("FIELD_MISMATCH:%s@%s" % (field, label))
        if site in EXACT_TENSOR_SITES:
            if fe.get("tensor_sha256") != ce.get("tensor_sha256"):
                reasons.append("TENSOR_MISMATCH@%s" % label)
            if fe.get("generator_state_hash_before") != ce.get("generator_state_hash_before"):
                reasons.append("FIELD_MISMATCH:generator_state_hash_before@%s" % label)
            if fe.get("generator_state_hash_after") != ce.get("generator_state_hash_after"):
                reasons.append("FIELD_MISMATCH:generator_state_hash_after@%s" % label)
        elif site in STREAM_WITNESS_SITES:
            for fld in STREAM_ENTRY_FIELDS:
                if fe.get(fld) != ce.get(fld):
                    reasons.append("FIELD_MISMATCH:%s@%s" % (fld, label))
            fx = fe.get("extra") or {}
            cx = ce.get("extra") or {}
            for dfld in R2_R3_DIAG_FIELDS:
                fv2, cv2 = fx.get(dfld), cx.get(dfld)
                if fv2 is None or cv2 is None:
                    if pre_divergence:
                        reasons.append("DIAGNOSTIC_MISSING:%s@%s" % (dfld, label))
                    continue
                if fv2 == cv2:
                    continue
                if pre_divergence:
                    reasons.append("DIAGNOSTIC_MISMATCH:%s@%s (byte-equality "
                                   "required at chunk<=fork_chunk)"
                                   % (dfld, label))
                else:
                    diagnostics.append({
                        "kind": "R2R3_DIAGNOSTIC_DIVERGENCE", "field": dfld,
                        "where": label,
                        "factual": fv2, "counterfactual": cv2,
                        "note": "recorded only; exogenous coupling unaffected",
                    })
            # tensor equality intentionally NOT compared here (adjudicated)
        compared += 1

    # -- intra-log stream integrity (main sites) ----------------------------------
    for role, parsed in ((factual_role, F), (cf_role, C)):
        ordered = sorted(parsed["entries"], key=lambda e: e.get("seq", 0))
        last_main_after = None
        for e in ordered:
            site = e.get("site_id")
            kk = "%s#%s" % (site, e.get("ordinal"))
            if site in ISOLATED_SITES:
                if e.get("generator_role") != "isolated_warp":
                    reasons.append("PRECOND1_GLOBAL_RNG_BYPASS@%s role=%r"
                                   % (kk, e.get("generator_role")))
                continue
            before = e.get("generator_state_hash_before")
            after = e.get("generator_state_hash_after")
            if before is None or after is None:
                reasons.append("FIELD_MISMATCH:none@%s (%s)" % (kk, role))
            else:
                if before == after:
                    reasons.append("NOOP_DRAW_BYPASS:%s [%s]" % (kk, role))
                if last_main_after is not None and before != last_main_after:
                    reasons.append("STREAM_CHAIN_BREAK:%s [%s]" % (kk, role))
                last_main_after = after
            if after is not None:
                last_main_after = after

    # -- R7 cross-branch isolated-stream witness ----------------------------------
    r7_diags, r7_bad = _r7_cross_branch(fd, cd)
    diagnostics.extend(r7_diags)
    reasons.extend(r7_bad)

    # -- FORK_STATE_DIGEST artifacts ------------------------------------------------
    loaded_digests = {}
    for side, spec_name in (("parent", "parent_state_digest"),
                            ("child", "child_state_digest")):
        spec = m[spec_name]
        try:
            path, want = _artifact_sha(spec) if isinstance(spec, dict) else (None, None)
            if path is None:
                reasons.append("STATE_DIGEST_LOAD_ERROR:%s (%s): no path"
                               % (side, spec_name))
                continue
            if want:
                if file_sha256(path) != want:
                    reasons.append("ARTIFACT_HASH_MISMATCH:%s" % spec_name)
            import fork_state_digest as fsd
            man = fsd.load(path)
            loaded_digests[side] = man
            ledger_meta = fm if side == "parent" else cm
            ledger_role = factual_role if side == "parent" else cf_role
            reasons.extend(validate_loaded_boundary_digest(man, ledger_meta,
                                                            ledger_role))
            if man.get("missing_required_paths"):
                reasons.append("STATE_DIGEST_MISSING_REQUIRED:%s %s"
                               % (side, man["missing_required_paths"]))
        except Exception as exc:
            reasons.append("STATE_DIGEST_LOAD_ERROR:%s (%s): %s"
                           % (side, spec_name, exc))
    if len(loaded_digests) == 2:
        import fork_state_digest as fsd
        rep = fsd.compare(loaded_digests["parent"], loaded_digests["child"])
        for mm in rep["mismatches"]:
            reasons.append("FORK_STATE_DIGEST_MISMATCH:%s reason=%s"
                           % (mm.get("field"), mm.get("reason")))
        for ms in rep["missing"]:
            reasons.append("FORK_STATE_DIGEST_MISSING:%s %s"
                           % (ms.get("field"), ms.get("path", "")))

    status = STRICT_NOISE_COUPLED if not reasons else STRICT_COUPLING_INVALID
    result = {
        "status": status,
        "reasons": reasons,
        "entries_compared": compared,
        "sites": sorted(f_sites & c_sites),
        "continuation": {
            factual_role: GENERATOR_STATE_RESTORED if f_cap else None,
            cf_role: GENERATOR_STATE_RESTORED if c_res else None,
        },
        "restored_branches": restored_branches,
        "diagnostics": diagnostics,
        "grammar_violations": grammar_violations,
        "pair_id": m.get("pair_id"),
        "run_ids": {"factual": f_run, "counterfactual": c_run},
        "launch_strict": m.get("launch_strict"),
    }
    validate_status(status)
    return result


def _r7_cross_branch(fd, cd):
    """Walk R7 rows in parallel; chain equality holds until the first EXPLAINED
    domain divergence (high/skip difference). Index tensors NEVER compared."""
    diags, bad = [], []
    f_rows = {kk: v for kk, v in fd.items() if kk[0] == "R7"}
    c_rows = {kk: v for kk, v in cd.items() if kk[0] == "R7"}
    diverged = False
    for key in sorted(set(f_rows) | set(c_rows)):
        fe, ce = f_rows.get(key), c_rows.get(key)
        label = "R7#%s@chunk%s" % (key[1], key[2])
        if fe is None or ce is None:
            continue  # already reported as MISSING_SITE
        fex, cex = fe.get("extra") or {}, ce.get("extra") or {}
        fhigh, chigh = fex.get("high"), cex.get("high")
        fskip, cskip = bool(fex.get("skip_flag")), bool(cex.get("skip_flag"))
        if not diverged:
            domain_equal = (fhigh == chigh) and (fskip == cskip)
            if not domain_equal:
                diverged = True
                diags.append({
                    "kind": "R7_EXPLAINED_DOMAIN_DIVERGENCE", "where": label,
                    "high_factual": fhigh, "high_counterfactual": chigh,
                    "skip_factual": fskip, "skip_counterfactual": cskip,
                    "note": "index inequality ignored by ruling; state "
                            "differences after this point are tolerated",
                })
                continue
            for fld in STREAM_ENTRY_FIELDS:
                if fe.get(fld) != ce.get(fld):
                    bad.append("R7_STATE_DIVERGENCE_UNEXPLAINED:%s %s "
                               "(domains still equal)" % (label, fld))
        else:
            diags.append({
                "kind": "R7_POST_DIVERGENCE_ROW", "where": label,
                "note": "tolerated after explained divergence; index ignored",
            })
    return diags, bad


def refuse_gpu_countersign(result_or_manifest):
    """Return True when the result/manifest may NEVER be GPU-countersigned.

    Hard-refuses unless archival ``launch_strict`` is literally true, whenever
    an identity field (patch/profile/config sha256,
    diffusers string) carries the literal "UNDECLARED" or the explicit local-CPU
    "TEST_MODE_ONLY" marker, or when a validation result already carries
    IDENTITY_UNDECLARED reasons. Such ledgers prove only that a harness ran on a
    box without the real dependency stack; they cannot anchor a GPU-01 run.
    """
    blockers = []

    if not isinstance(result_or_manifest, dict) or \
            result_or_manifest.get("launch_strict") is not True:
        blockers.append("launch_strict is not true")

    def scan(o, path):
        if isinstance(o, dict):
            for k, v in o.items():
                p = "%s.%s" % (path, k)
                if isinstance(v, str) and v in IDENTITY_MARKERS and \
                        any(t in str(k) for t in
                            ("diffusers", "sha256", "config", "profile",
                             "patch")):
                    blockers.append("%s=%r" % (p, v))
                else:
                    scan(v, p)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                scan(v, "%s[%d]" % (path, i))
        elif isinstance(o, tuple):
            for i, v in enumerate(o):
                scan(v, "%s(%d)" % (path, i))
        elif isinstance(o, str):
            if o == "TEST_MODE_ONLY":
                blockers.append("%s=TEST_MODE_ONLY" % path)

    scan(result_or_manifest, "$")
    reasons_ = getattr(result_or_manifest, "get", lambda *_: None)("reasons") \
        if isinstance(result_or_manifest, dict) else None
    for r in reasons_ or []:
        if isinstance(r, str) and r.startswith("IDENTITY_UNDECLARED"):
            blockers.append("reason:" + r)
    return bool(blockers)


def compare_coupling_logs(factual_log, cf_log, pair_manifest=None,
                          factual_role="factual", cf_role="counterfactual"):
    """Backward-compatible alias; the pair manifest is now REQUIRED."""
    return validate_pair(factual_log, cf_log, pair_manifest,
                         factual_role=factual_role, cf_role=cf_role)


def format_result(result):
    lines = ["%s (%d draws compared)" % (result["status"], result["entries_compared"])]
    if result.get("restored_branches"):
        lines.append("continuation: %s -> %s"
                     % (", ".join(result["restored_branches"]),
                        GENERATOR_STATE_RESTORED))
    for r in result.get("reasons", []):
        lines.append("  - %s" % r)
    for d in result.get("diagnostics", []):
        lines.append("  ~ diagnostic %s @ %s" % (d.get("kind"), d.get("where")))
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover
    import sys
    if len(sys.argv) != 4:
        print("usage: python strict_coupling.py FACTUAL.jsonl CF.jsonl PAIR_MANIFEST.json")
        raise SystemExit(2)
    res = validate_pair(sys.argv[1], sys.argv[2], sys.argv[3])
    print(format_result(res))
    raise SystemExit(0 if is_pass(res) else 1)
