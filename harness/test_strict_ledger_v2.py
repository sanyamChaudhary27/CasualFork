"""STRICT-LEDGER V2 SEMANTIC SUITE (STAGE-C tests A-P + grammar/preflight/digest).

Binding semantics: fanin/2026-08-25-semantics/adjudication.md.
All CPU, all deterministic; the live-emitter case (O) drives the REAL patched
module source from patches/evoke_strict_fork.py.txt end-to-end and then runs
the full validator on the produced pair - the target-5 regression proof that
zero R-site draws precede the restore at the fork chunk.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import os
import sys
import tempfile
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import strict_coupling as sc          # noqa: E402
import testutil_sc1 as tu             # noqa: E402
import sc1_grammar as gr              # noqa: E402
import sc1_preflight as pf            # noqa: E402
import fork_state_digest as fsd       # noqa: E402
import env_fingerprint as ef          # noqa: E402

RESULTS = []


class BLOCKED(Exception):
    pass


def case(name):
    def deco(fn):
        RESULTS.append((name, fn))
        return fn
    return deco


def lines_of(path):
    with open(path, "r", encoding="utf-8") as fh:
        return [json.loads(x) for x in fh.read().splitlines() if x.strip()]


def rewrite(path, mutator, out_name):
    objs = lines_of(path)
    objs = mutator(objs)
    dst = os.path.join(os.path.dirname(path), out_name)
    with open(dst, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(json.dumps(o, sort_keys=True) for o in objs) + "\n")
    return dst


def remanifest(man, fp, cp, run_f="run-F-fix", run_c="run-C-fix"):
    return tu.make_manifest(
        (fp, cp),
        (man["parent_state_digest"]["path"],
         man["child_state_digest"]["path"]),
        (run_f, run_c), fork_chunk=man["fork_chunk"])


# ------------------------------------------------------------------ A
@case("A same-file/self-pair -> INVALID(SELF_PAIR)")
def t_a():
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td)
        r = sc.validate_pair(fp, fp, man)
        assert not sc.is_pass(r)
        assert any(x.startswith("SELF_PAIR") for x in r["reasons"]), r["reasons"]
        # byte-identical duplicate of ONE branch under a fresh path can
        # never pass either: role label + run-id binding reject it.
        import shutil
        cp3 = os.path.join(td, "dup.jsonl")
        shutil.copyfile(fp, cp3)          # factual bytes in the CF slot
        man3 = remanifest(man, fp, cp3, run_c="run-C-fix")
        r3 = sc.validate_pair(fp, cp3, man3)
        assert not sc.is_pass(r3)
        fatal_families = ("SELF_PAIR", "ROLE_LABEL_MISMATCH",
                          "RUN_ID_MANIFEST_MISMATCH", "RUN_ID_COLLISION")
        assert any(r.startswith(f) for r in r3["reasons"] for f in fatal_families), r3["reasons"][:6]
    return True


# ------------------------------------------------------------------ B
@case("B copied ledger / same run_id -> INVALID(RUN_ID_COLLISION family)")
def t_b():
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td)

        def setrun(objs):
            for o in objs:
                o["run_id"] = "run-SAME"
            return objs

        cf = rewrite(cp, setrun, "same.jsonl")
        ff = rewrite(fp, setrun, "samef.jsonl")
        man4 = tu.make_manifest(
            (ff, cf),
            (man["parent_state_digest"]["path"],
             man["child_state_digest"]["path"]),
            ("run-SAME", "run-SAME"))
        r4 = sc.validate_pair(ff, cf, man4)
        assert not sc.is_pass(r4)
        # identical run_ids declared in the manifest are caught first...
        assert any(x.startswith("RUN_ID_COLLISION") for x in r4["reasons"]), \
            r4["reasons"][:8]
        # ...and a manifest/ledger run-id disagreement is caught too
        def relabel(objs):
            for o in objs:
                if o.get("branch_id"):
                    o["branch_id"] = "counterfactual"
                if o.get("event") == "meta":
                    o["branch_id"] = "counterfactual"
                    o["continuation"] = o.get("continuation")
            return objs
        cf2 = rewrite(cp, relabel, "copied3.jsonl")
        man3 = tu.make_manifest(
            (fp, cf2),
            (man["parent_state_digest"]["path"],
             man["child_state_digest"]["path"]),
            ("run-F-fix", "run-Fix-Typo"))
        r3 = sc.validate_pair(fp, cf2, man3)
        assert not sc.is_pass(r3)
        assert any(x.startswith("RUN_ID_MANIFEST_MISMATCH")
                   for x in r3["reasons"]), r3["reasons"][:6]
    return True


# ------------------------------------------------------------------ C
@case("C two meta headers -> INVALID(MULTI_META_HEADER)")
def t_c():
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td)
        meta_line = json.dumps(lines_of(fp)[0], sort_keys=True)
        with open(fp, encoding="utf-8") as fh:
            body = fh.read()
        fp2 = os.path.join(td, "dupmeta.jsonl")
        with open(fp2, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(meta_line + "\n" + body)
        man2 = remanifest(man, fp2, cp)
        r = sc.validate_pair(fp2, cp, man2)
        assert not sc.is_pass(r)
        assert any(x.startswith("MULTI_META_HEADER:factual") for x in r["reasons"])
    return True


# ------------------------------------------------------------------ D
@case("D stale append from another run -> INVALID(LEDGER_APPEND_MIX)")
def t_d():
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td)
        stale = [o for o in lines_of(fp) if o.get("event") == "draw"][:3]
        for o in stale:
            o["run_id"] = "run-STALE-2026-08-20"

        def append_stale(objs):
            return objs + stale
        fp2 = rewrite(fp, append_stale, "stale.jsonl")
        man2 = remanifest(man, fp2, cp)
        r = sc.validate_pair(fp2, cp, man2)
        assert not sc.is_pass(r)
        assert any(x.startswith("LEDGER_APPEND_MIX:factual") for x in r["reasons"]), \
            r["reasons"][:6]
        assert any(x.startswith("APPEND_MIX_DUPLICATE") or
                   x.startswith("SEQ_REGRESSION") for x in r["reasons"])
    return True


# ------------------------------------------------------------------ E
@case("E profile/config mismatch with no RNG change -> PREFLIGHT ABORT")
def t_e():
    base_args = {
        "seed": 12345,
        "height": 384, "width": 640, "fps": 24,
        "guidance_scale": 1.0,
        "stage2_num_stages": 3, "stage2_steps": [1, 1, 1],
        "event_chunks": [],
        "prompt_schedule": [{"chunk": 1, "text": "baseline"}],
        "image_path": None, "lingbot_pose_path": None, "checkpoint_dir": None,
        "expected_common_config_sha256": pf.canonical_config({"seed": 12345}),
    }
    drifted = dict(base_args)
    drifted["_baseline_args"] = {k: v for k, v in base_args.items()
                                 if k != "expected_common_config_sha256"}
    drifted["prompt_schedule"] = [{"chunk": 1, "text": "[INTERVENTION] neon fox"}]
    rep = pf.preflight(drifted, env={"EVOKE_WARP_SEED": "777"})
    assert rep["status"] == "ABORT"
    codes = [a["code"] for a in rep["aborts"]]
    assert "CONFIG_HASH_MISMATCH" in codes, rep["aborts"]
    hit = next(a for a in rep["aborts"] if a["code"] == "CONFIG_HASH_MISMATCH")
    assert hit["rng_relevant_change_detected"] is False   # prompt-only delta
    ok_args = dict(base_args,
                   expected_common_config_sha256=pf.canonical_config(base_args))
    rep_ok = pf.preflight(ok_args, env={"EVOKE_WARP_SEED": "777"})
    assert not any(a["code"] == "CONFIG_HASH_MISMATCH" for a in rep_ok["aborts"])
    return True


# ------------------------------------------------------------------ F
@case("F symmetric missing final required draw -> INVALID (both branches)")
def t_f():
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td, chunks=3, fork_chunk=1,
                                       variant_f={"drop_last_r6": 2},
                                       variant_c={"drop_last_r6": 2})
        r = sc.validate_pair(fp, cp, man)
        assert not sc.is_pass(r), sc.format_result(r)
        hits = [x for x in r["reasons"]
                if x.startswith("GRAMMAR_FIXED_SITE_COUNT:chunk 2 R6")]
        assert len(hits) >= 2, r["reasons"]      # one per branch
    return True


# ------------------------------------------------------------------ G
@case("G one chunk missing an expected fixed site -> INVALID(GRAMMAR)")
def t_g():
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td,
                                       variant_f={"drop_site_at": ["R4", 1]},
                                       variant_c={"drop_site_at": ["R4", 1]})
        r = sc.validate_pair(fp, cp, man)
        assert not sc.is_pass(r)
        hits = [x for x in r["reasons"]
                if x.startswith("GRAMMAR_FIXED_SITE_COUNT:chunk 1 R4")]
        assert len(hits) == 2, r["reasons"]
    return True


@case("G2 permuted within-chunk order -> INVALID(GRAMMAR_ORDER)")
def t_g2():
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td)
        objs = lines_of(fp)
        fixed0 = [i for i, o in enumerate(objs)
                  if o.get("chunk") == 0 and o.get("site_id") != "R7"]
        i_r1 = next(i for i in fixed0 if objs[i]["site_id"] == "R1")
        i_r2 = next(i for i in fixed0 if objs[i]["site_id"] == "R2")
        objs[i_r1]["seq"], objs[i_r2]["seq"] = \
            objs[i_r2]["seq"], objs[i_r1]["seq"]
        fp2 = os.path.join(td, "perm.jsonl")
        with open(fp2, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(json.dumps(o, sort_keys=True) for o in objs) + "\n")
        man2 = remanifest(man, fp2, cp)
        r = sc.validate_pair(fp2, cp, man2)
        assert not sc.is_pass(r)
        assert any(x.startswith("GRAMMAR_ORDER:chunk 0") for x in r["reasons"]), \
            r["reasons"][:10]


# ------------------------------------------------------------------ H
@case("H R7 state missing -> INVALID(GRAMMAR_R7_STATE_MISSING)")
def t_h():
    def null_r7_states(objs):
        n = 0
        for o in objs:
            if o.get("site_id") == "R7" and n < 1:
                o["generator_state_hash_before"] = None
                o["generator_state_hash_after"] = None
                n += 1
        return objs
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td)
        fp2 = rewrite(fp, null_r7_states, "h7.jsonl")
        man2 = remanifest(man, fp2, cp)
        r = sc.validate_pair(fp2, cp, man2)
        assert not sc.is_pass(r)
        assert any("GRAMMAR_R7_STATE_MISSING" in x for x in r["reasons"])
    return True


# ------------------------------------------------------------------ I
@case("I R7 broken isolated chain -> INVALID(GRAMMAR_R7_CHAIN_BREAK)")
def t_i():
    def break_chain(objs):
        rows = [o for o in objs if o.get("site_id") == "R7"
                and not (o.get("extra") or {}).get("skip_flag")]
        rows[1]["generator_state_hash_before"] = "e" * 64
        return objs
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td)
        fp2 = rewrite(fp, break_chain, "ib7.jsonl")
        man2 = remanifest(man, fp2, cp)
        r = sc.validate_pair(fp2, cp, man2)
        assert not sc.is_pass(r)
        assert any(x.startswith("GRAMMAR_R7_CHAIN_BREAK") for x in r["reasons"]), \
            r["reasons"][:10]
    return True


# ------------------------------------------------------------------ J
@case("J wrong branch labels -> INVALID(ROLE_LABEL_MISMATCH)")
def t_j():
    def swap(objs):
        for o in objs:
            if o.get("branch_id"):
                o["branch_id"] = "factual"
        return objs
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td)
        cp2 = rewrite(cp, swap, "jlab.jsonl")
        man2 = remanifest(man, fp, cp2)
        r = sc.validate_pair(fp, cp2, man2)
        assert not sc.is_pass(r)
        assert any(x.startswith("ROLE_LABEL_MISMATCH:counterfactual")
                   for x in r["reasons"]), r["reasons"][:8]
    return True


# ------------------------------------------------------------------ K
@case("K config mismatch AND state-digest mismatch -> INVALID")
def t_k():
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td)
        man_cfg = copy.deepcopy(man)
        man_cfg["common_config_sha256"] = "configsha" + "1" * 56
        r = sc.validate_pair(fp, cp, man_cfg)
        assert not sc.is_pass(r)
        assert any(x.startswith("META_MISMATCH:common_config_sha256")
                   for x in r["reasons"])
        dp, dc = tu.write_digest_pair(td, tamper_child=True)
        man_d = tu.make_manifest((fp, cp), (dp, dc), ("run-F-fix", "run-C-fix"))
        r2 = sc.validate_pair(fp, cp, man_d)
        assert not sc.is_pass(r2)
        assert any(x.startswith("FORK_STATE_DIGEST_MISMATCH")
                   for x in r2["reasons"]), r2["reasons"][:8]
    return True


# ------------------------------------------------------------------ L
@case("L R1 raw-noise mismatch -> INVALID(TENSOR_MISMATCH)")
def t_l():
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td, variant_c={"flip_tensor": ["R1", 1]})
        r = sc.validate_pair(fp, cp, man)
        assert not sc.is_pass(r)
        assert any(x.startswith("TENSOR_MISMATCH@R1#") for x in r["reasons"])
        fp2, cp2, man2 = tu.standard_pair(td,
                                          variant_c={"flip_tensor": ["R4", 1]})
        r2 = sc.validate_pair(fp2, cp2, man2)
        assert any(x.startswith("TENSOR_MISMATCH@R4#") for x in r2["reasons"])
    return True


# ------------------------------------------------------------------ M
@case("M identical innovation, different mean/std -> stream witness PASSES, "
      "diagnostics recorded")
def t_m():
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td, chunks=3, fork_chunk=1,
                                       variant_c={"flip_r2r3_at": 2})
        r = sc.validate_pair(fp, cp, man)
        assert sc.is_pass(r), sc.format_result(r)
        kinds = [d["kind"] for d in r["diagnostics"]]
        assert kinds.count("R2R3_DIAGNOSTIC_DIVERGENCE") == 4, r["diagnostics"]
        assert all(d["field"] in ("sha256_mean", "sha256_std")
                   for d in r["diagnostics"])
        fp2, cp2, man2 = tu.standard_pair(td, chunks=3, fork_chunk=1,
                                          variant_c={"flip_r2r3_at": 1})
        r2 = sc.validate_pair(fp2, cp2, man2)
        assert not sc.is_pass(r2)
        assert any(x.startswith("DIAGNOSTIC_MISMATCH:") for x in r2["reasons"])
    return True


# ------------------------------------------------------------------ N
@case("N identical stream, different domain high -> explained divergence, "
      "index inequality ignored")
def t_n():
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td, chunks=3, fork_chunk=1,
                                       variant_c={"r7_diverge_at": [1, 1]})
        r = sc.validate_pair(fp, cp, man)
        assert sc.is_pass(r), sc.format_result(r)
        exp = [d for d in r["diagnostics"]
               if d["kind"] == "R7_EXPLAINED_DOMAIN_DIVERGENCE"]
        assert len(exp) == 1 and exp[0]["where"].startswith("R7#"), r["diagnostics"]
        assert not any(d["kind"] == "R7_STATE_DIVERGENCE_UNEXPLAINED"
                       for d in r["diagnostics"])

        def unexplained(objs):
            rows = [o for o in objs if o.get("site_id") == "R7"
                    and not (o.get("extra") or {}).get("skip_flag")]
            rows[0]["generator_state_hash_after"] = "d" * 64
            rows[1]["generator_state_hash_before"] = "d" * 64
            return objs
        fp2 = rewrite(fp, unexplained, "unexp.jsonl")
        man2 = remanifest(man, fp2, cp)
        r2 = sc.validate_pair(fp2, cp, man2)
        assert not sc.is_pass(r2)
    return True

# ------------------------------------------------------- preflight extras
@case("PF preflight pass / forbidden option / PRECOND-1 missing")
def t_pf():
    good = {
        "seed": 7, "guidance_scale": 1.0, "event_chunks": [],
        "geo_warp_vis_cap": 0.0, "geo_warp_patch_drop_ratio": 0.0,
        "use_kv_cache": False, "restrict_self_attn": False,
        "short_tier_noise_enabled": False, "invisible_history_noise": False,
        "use_adaptive_anti_drifting": False, "use_dmd": False,
        "module_training_flags": {"transformer_training": False,
                                  "vae_training": False,
                                  "text_encoder_training": False,
                                  "estimator_training": False},
    }
    env = {"EVOKE_WARP_SEED": "424242"}
    rep = pf.preflight(good, env=env)
    assert rep["status"] == "PASS", rep["aborts"]
    assert rep["preconditions"] == {"PRECOND-1": "MET", "PRECOND-2": "MET"}
    assert len(rep["hashes"]["profile_sha256"]) == 64

    bad = dict(good, geo_warp_vis_cap=0.25, use_kv_cache=True,
               event_chunks=[3])
    rep2 = pf.preflight(bad, env=env)
    assert rep2["status"] == "ABORT"
    opts = {a["option"] for a in rep2["aborts"]}
    assert {"geo_warp_vis_cap", "use_kv_cache", "event_chunks"} <= opts

    rep3 = pf.preflight(good, env={})
    assert rep3["status"] == "ABORT"
    assert any(a["code"] == "PRECOND1_UNMET" for a in rep3["aborts"])

    rep4 = pf.preflight(dict(good, module_training_flags={
        "transformer_training": True}), env=env)
    assert any(a["code"] == "PRECOND2_UNMET" for a in rep4["aborts"])
    return True


# ------------------------------------------------------------ digest unit
@case("DG FORK_STATE_DIGEST: capture/compare/tamper/F15-excluded/advisory")
def t_dg():
    root = tu.make_mock_root()
    gens = tu.make_generators()
    m1 = fsd.capture(root, gens, fork_chunk=1, branch_id="factual")
    m2 = fsd.capture(root, gens, fork_chunk=1, branch_id="counterfactual")
    rep = fsd.compare(m1, m2)
    assert rep["match"], rep
    m3 = copy.deepcopy(m2)
    m3["fields"]["F01"]["group_sha256"] = "0" * 64
    rep2 = fsd.compare(m1, m3)
    assert not rep2["match"]
    root_b = tu.make_mock_root()
    root_b["estimator_stream_digest"] = tu.sha("other-estimator-stream")
    m4 = fsd.capture(root_b, gens, fork_chunk=1, branch_id="counterfactual")
    rep3 = fsd.compare(m1, m4)
    assert rep3["match"] and rep3["advisory_diffs"]
    rep4 = fsd.compare(m1, m4, require_advisory=True)
    assert not rep4["match"]
    blob = json.dumps(fsd.FIELD_SPEC)
    assert "kv_cache" not in blob and "_cgen" not in blob
    assert fsd.EXCLUDED_FIELDS_NOTE.startswith("F15")
    print("      [dg] geo_da3_bank class: %s"
          % type(root["geo_da3_bank"]).__name__)
    with tempfile.TemporaryDirectory() as td:
        p = fsd.save(m1, os.path.join(td, "m.json"))
        assert fsd.compare(fsd.load(p), m2)["match"]
    return True


@case("DG2 harness vs patched-emitter digest implementations agree byte-for-byte")
def t_dg2():
    sf = _load_sf()
    sf.reset_for_tests()
    root = tu.make_mock_root(seed=777)
    gens = tu.make_generators()
    mine = fsd.capture(root, gens, fork_chunk=2, branch_id="b")
    theirs = sf.capture_fork_state_digest(root, gens, fork_chunk=2,
                                          branch_id="b")
    assert fsd.canonical(mine) == sf.digest_canonical(theirs)
    assert mine["manifest_sha256"] == theirs["manifest_sha256"]
    assert fsd.compare(mine, theirs)["match"]
    sf.reset_for_tests()
    return True


# ------------------------------------------------------------ fingerprint
@case("EF environment fingerprint captures runtime identity gracefully")
def t_ef():
    fp = ef.fingerprint(patch_sha="0" * 64)
    assert fp["schema"] == ef.SCHEMA
    assert fp["upstream_pin"] == ef.UPSTREAM_PIN
    assert fp["torch"] and fp["torch"].startswith("2.")
    assert fp["cuda_runtime"] is None and fp["gpu"] is None   # CPU box
    print("      [ef] diffusers=%r transformers=%r numpy=%r"
          % (fp["diffusers"], fp["transformers"], fp["numpy"]))
    return True


# ------------------------------------------------------------ O (live E2E)
SF_SRC = os.path.join(os.path.dirname(HERE), "patches",
                      "evoke_strict_fork.py.txt")


def _load_sf():
    import importlib.machinery
    import importlib.util
    loader = importlib.machinery.SourceFileLoader(
        "evoke_strict_fork_live2", SF_SRC)
    spec = importlib.util.spec_from_file_location(
        "evoke_strict_fork_live2", SF_SRC, loader=loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["evoke_strict_fork_live2"] = mod
    loader.exec_module(mod)
    return mod


_TORCH = None


def _t():
    global _TORCH
    if _TORCH is None:
        import torch
        _TORCH = torch
    return _TORCH


def _live_view(fix, k):
    """Build the REAL emitter LiveStateView from an engine-like fixture."""
    gs, pipe, loc = fix
    return sf.build_live_state_view(
        loc["history_latents"], loc["total_generated_latent_frames"],
        gs, pipe, chunk_index=k, event_set_size=loc["event_set_size"],
        forced_off_flags=loc["forced_off_flags"])


def _iso_gen():
    seed = int(hashlib.sha256(b"7777").hexdigest()[:15], 16)
    return _t().Generator().manual_seed(seed)


def _mock_chunk_draws(sf, k, main, iso, pix):
    """Drive ONE mock chunk through the emitter in the re-audited order."""
    sf.set_chunk(k)
    rcall = sf.new_render_call()
    for ci, high in enumerate((16, 20, 0)):
        b = sf.gen_state_of(iso)
        if high:
            idx = _t().randint(0, high, (2000,), generator=iso)
            sf.log_draw("R7", idx, generator=iso, gen_before=b,
                        generator_role="isolated_warp",
                        extra={"source_gid": 11 + ci, "covis_M": 2000,
                               "render_call": rcall, "call_ordinal": ci,
                               "high": high, "skip_flag": False})
        else:
            sf.log_draw("R7", None, generator=iso, gen_before=b,
                        generator_role="isolated_warp",
                        extra={"source_gid": 13, "covis_M": 2000,
                               "render_call": rcall, "call_ordinal": ci,
                               "high": 0, "skip_flag": True})
    mean = _t().zeros(1, 16, 1, 6, 10)
    std = _t().ones(1, 16, 1, 6, 10)
    diag = sf.pixel_diag(pix, mean, std)
    b = sf.gen_state_of(main)
    sf.log_draw("R2", _t().randn(1, 16, 1, 6, 10, generator=main),
                generator=main, gen_before=b, generator_role="main", extra=diag)
    b = sf.gen_state_of(main)
    sf.log_draw("R3", _t().randn(1, 16, 9, 6, 10, generator=main),
                generator=main, gen_before=b, generator_role="main",
                extra=dict(diag or {}, loop_i=0))
    b = sf.gen_state_of(main)
    sf.log_draw("R4", _t().rand(9, generator=main), generator=main,
                gen_before=b, generator_role="main")
    b = sf.gen_state_of(main)
    sf.log_draw("R5", _t().randn(1, 16, 9, 6, 10, generator=main),
                generator=main, gen_before=b, generator_role="main")
    b = sf.gen_state_of(main)
    sf.log_draw("R1", _t().randn(1, 16, 9, 6, 10, generator=main),
                generator=main, gen_before=b, generator_role="main")
    for stage in (1, 2):
        sf.set_stage(stage)
        b = sf.gen_state_of(main)
        sf.log_draw("R6", _t().randn(96, 40, generator=main), generator=main,
                    gen_before=b, generator_role="main")
    sf.set_stage(None)


@case("O LIVE end-to-end: capture->restore->validator PASS; restore precedes "
      "every R-site draw at fork chunk (target-5 proof)")
def t_o():
    global sf
    sf = _load_sf()
    sf.reset_for_tests()
    old_env = {k: os.environ.get(k) for k in (
        sf.ENV_LEDGER, sf.ENV_FORK, sf.ENV_RUN_ID, sf.ENV_PAIR_ID,
        sf.ENV_WARP_SEED, sf.ENV_PATCH_SHA, sf.ENV_PROFILE_SHA,
        sf.ENV_CONFIG_SHA, sf.ENV_BRANCH)}
    try:
        with tempfile.TemporaryDirectory() as td:
            cap_dir = os.path.join(td, "cap")
            f_base = os.path.join(td, "factual.base.jsonl")
            c_base = os.path.join(td, "cf.base.jsonl")
            os.environ[sf.ENV_WARP_SEED] = "7777"
            os.environ[sf.ENV_PATCH_SHA] = tu.PATCH_SHA
            os.environ[sf.ENV_PROFILE_SHA] = tu.PROFILE_SHA
            os.environ[sf.ENV_CONFIG_SHA] = tu.CONFIG_SHA
            os.environ[sf.ENV_PAIR_ID] = tu.PAIR_ID

            # ---------------- parent (capture) run ---------------------------
            os.environ[sf.ENV_BRANCH] = "factual"
            os.environ[sf.ENV_RUN_ID] = "run-O-f"
            os.environ[sf.ENV_LEDGER] = f_base
            fix_p = tu.make_engine_like_fixture(seed=1000)
            main = _t().Generator().manual_seed(20260826)
            iso = _iso_gen()
            cfg_cap = {"fork_chunk": 1, "mode": "capture", "out_dir": cap_dir}
            os.environ[sf.ENV_FORK] = json.dumps(cfg_cap)
            pix = _t().zeros(1, 3, 33, 48, 80)
            for k in range(3):
                sf.maybe_fork_boundary(k, {"main": main},
                                       pipeline=_live_view(fix_p, k))
                _mock_chunk_draws(sf, k, main, iso, pix)
            sf.reset_for_tests()

            parent_digest = os.path.join(cap_dir,
                                         "fork_state_digest_chunk1.json")
            sidecar = os.path.join(cap_dir, "fork_capture_chunk1.json")
            assert os.path.exists(parent_digest) and os.path.exists(sidecar)

            # ---------------- child (restore) run ----------------------------
            os.environ[sf.ENV_BRANCH] = "counterfactual"
            os.environ[sf.ENV_RUN_ID] = "run-O-c"
            os.environ[sf.ENV_LEDGER] = c_base
            fix_c = tu.make_engine_like_fixture(seed=1000)  # identical boundary
            main2 = _t().Generator().manual_seed(20260826)
            iso2 = _iso_gen()
            cfg_res = {"fork_chunk": 1, "mode": "restore", "sidecar": sidecar,
                       "parent_state_digest": parent_digest}
            os.environ[sf.ENV_FORK] = json.dumps(cfg_res)
            for k in range(3):
                sf.maybe_fork_boundary(k, {"main": main2},
                                       pipeline=_live_view(fix_c, k))
                _mock_chunk_draws(sf, k, main2, iso2, pix)
            sf.reset_for_tests()

            child_digest = os.path.join(
                cap_dir, "fork_state_digest_child_chunk1.json")
            assert os.path.exists(child_digest)

            # -------- ordering regression proof on the CHILD ledger ----------
            c_real = c_base.replace(".jsonl", ".run-O-c.jsonl")
            f_real0 = f_base.replace(".jsonl", ".run-O-f.jsonl")
            c_objs = lines_of(c_real)
            res_seq = min(o["seq"] for o in c_objs
                          if o.get("event") == sc.GENERATOR_STATE_RESTORED)
            early = [o for o in c_objs
                     if o.get("event") == "draw"
                     and isinstance(o.get("chunk"), int) and o["chunk"] >= 1
                     and o["seq"] < res_seq]
            assert not early, \
                "%d post-fork draws preceded the restore" % len(early)
            cap_objs = lines_of(f_real0)
            assert any(o.get("event") == "FORK_CAPTURE" and o.get("chunk") == 1
                       for o in cap_objs)

            # ---------------- full validator on the REAL ledgers -------------
            man = tu.make_manifest((f_real0, c_real),
                                   (parent_digest, child_digest),
                                   ("run-O-f", "run-O-c"),
                                   overrides={"warp_seed_sha256":
                                              hashlib.sha256(b"7777").hexdigest()})
            r = sc.validate_pair(man["artifacts"]["factual_log"]["path"],
                                 man["artifacts"]["counterfactual_log"]["path"],
                                 man)
            assert sc.is_pass(r), (
                sc.format_result(r) + " REASONS=" +
                json.dumps(r.get("reasons", [])[:24], default=str))
            assert r["restored_branches"] == ["counterfactual"]
            assert r["entries_compared"] == 30
    finally:
        sf.reset_for_tests()
        for k, v in old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return True


# ---------------------------------------------------------- byte-neutrality
@case("BN byte-neutrality: AST scan of patched trees + gates-off no-op proof")
def t_bn():
    wk = os.path.join(os.environ.get("TEMP", "/tmp"), "opencode", "sc1-wk")
    pipe = os.path.join(wk, "evoke", "pipelines", "pipeline_evoke.py")
    da3 = os.path.join(wk, "evoke", "modules", "geometric_state",
                       "da3_cloud.py")
    if not os.path.exists(pipe):
        raise BLOCKED("staged work tree %s not found; run make_sc1_patch.py"
                      % wk)
    checked = 0
    for path in (pipe, da3):
        src = open(path, "r", encoding="utf-8").read()
        tree = ast.parse(src)
        for node in ast.walk(tree):
            seg = ast.dump(node)
            if "_sf_" not in seg or isinstance(node, ast.Module):
                continue
            ok_kind = isinstance(node, (ast.Call, ast.Assign, ast.Expr,
                                        ast.For, ast.If, ast.Name,
                                        ast.Attribute))
            if ok_kind:
                checked += 1
            elif hasattr(ast, "unparse"):
                txt = ast.unparse(node)
                if "_sf_" in txt and len(txt) < 400:
                    checked += 1
    assert checked > 20, checked
    print("      [bn] AST nodes referencing instrumentation: %d" % checked)
    # structural: every inserted line mentioning _sf_ in da3/pipeline is an
    # expression statement, an assignment to an _sf_/local name, a comment,
    # an import alias, or the enumerate-loop rename - nothing else.
    bad_lines = []
    for path in (pipe, da3):
        for ln in open(path, encoding="utf-8").read().splitlines():
            s = ln.strip()
            if "_sf_" not in s:
                continue
            legal = (s.startswith("#") or
                     s.startswith("_sf_b =") or
                     s.startswith("_sf_rcall =") or
                     s.startswith("_sf_log_draw(") or
                     s.startswith("_sf_maybe_fork_boundary(") or
                     s.startswith("_sf_view = ") or
                     s.startswith("if _sf_fork_active():") or
                     s.startswith("_sf_set_") or
                     s.startswith("from ...strict_fork") or
                     s.startswith("from ..strict_fork") or
                     "_sf_ci, g in enumerate" in s or
                     "generator_role=(" in s or
                     "extra=dict(_sf_pixel_diag" in s or
                     "extra=_sf_pixel_diag" in s or
                     "call_ordinal" in s or
                     " as _sf_" in s or
                     s.endswith(","))
            if not legal:
                bad_lines.append(s)
            if not legal and ("=" not in s and "(" not in s):
                bad_lines.append(s)
    assert not bad_lines, bad_lines[:5]
    # functional gates-off neutrality on the live module
    sf = _load_sf()
    sf.reset_for_tests()
    g = _t().Generator().manual_seed(11)
    s0 = bytes(g.get_state().numpy().tobytes())
    assert sf.log_draw("R1", _t().zeros(2)) is None
    assert sf.pixel_diag(_t().zeros(2), _t().zeros(1), _t().zeros(1)) is None
    assert sf.maybe_fork_boundary(5, {}, {}) is None
    assert bytes(g.get_state().numpy().tobytes()) == s0
    sf.reset_for_tests()
    return True


# ------------------------------------------------------------------ P
@case("P strict profile JSON parses via plain json.load(utf-8); schema valid")
def t_p():
    path = os.path.abspath(os.path.join(HERE, os.pardir, "profiles",
                                        "sc1_strict_profile.json"))
    raw = open(path, "rb").read()
    assert raw[:3] != b"\xef\xbb\xbf", "UTF-8 BOM present"
    obj = json.load(open(path, encoding="utf-8"))   # NO BOM handling needed
    required = ("$schema", "profile_id", "upstream_pin", "engine_path",
                "fork_definition",
                "byte_identical_operational_definition",
                "required_identical_fields", "forbidden_mechanisms",
                "preconditions_conditional_blockers",
                "option_classification",
                "reachable_post_fork_random_sites_summary")
    for k in required:
        assert k in obj, "missing profile key %r" % k
    assert obj["$schema"] == "causalfork/sc1-strict-profile/v1"
    assert obj["upstream_pin"]["commit"] == tu.PIN
    ids = {p["id"] for p in obj["preconditions_conditional_blockers"]}
    assert ids == {"PRECOND-1", "PRECOND-2"}
    sites_summary = obj["reachable_post_fork_random_sites_summary"]
    assert sites_summary["count"] == 7
    md = open(os.path.join(os.path.dirname(path),
                           "sc1_stochastic_site_inventory.md"),
              encoding="utf-8").read()
    for rid in ("R1", "R2", "R3", "R4", "R5", "R6", "R7"):
        assert ("\n| %s |" % rid) in md, "inventory row %s missing" % rid
    # window/stride distinction frozen in both docs (target 11)
    assert "36 pixel frames" in obj["fork_definition"]["fork_point"]
    md_prof = open(path.replace(".json", ".md"), encoding="utf-8").read()
    assert "rollout/prompt chunk stride** is 36 pixel frames" in md_prof
    assert "chunk-index based" in md_prof
    return True


# =========================================================== FINAL CPU ROUND ==
@case("V1 LIVE adapter: realistic view (real banks) -> digest COMPLETE")
def t_v1():
    global sf
    sf = _load_sf()
    sf.reset_for_tests()
    fix = tu.make_engine_like_fixture(seed=555)
    gs, pipe, loc = fix
    view = _live_view(fix, 1)
    # observational-only: mapped tensors are LIVE references (same storage)
    assert view.history_latents is loc["history_latents"]
    assert view.prev_frame_pix is gs["prev_chunk_last_frame"]
    assert view.geo_da3_bank is gs["da3_bank"]
    try:
        view.history_latents = None
        raise AssertionError("LiveStateView must be read-only")
    except AttributeError:
        pass
    m = sf.capture_fork_state_digest(view, {"main": _t().Generator().manual_seed(3)},
                                     fork_chunk=1, branch_id="factual")
    assert m.get("missing_required_paths") is None, \
        m.get("missing_required_paths")
    # harness implementation agrees field-by-field on group hashes
    import torch
    mh = fsd.capture(view, {"main": torch.Generator().manual_seed(3)},
                     fork_chunk=1, branch_id="factual")
    for fid in ("F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08",
                "F11", "F13", "F14"):
        assert mh["fields"][fid]["group_sha256"] == \
            m["fields"][fid]["group_sha256"], fid
    print("      [v1] real banks: %s / %s"
          % (type(gs["frame_bank"]).__name__, type(gs["da3_bank"]).__name__))
    sf.reset_for_tests()
    return True


@case("V2 adapter: deleting a REQUIRED mapped field fails LOUDLY (never silent)")
def t_v2():
    global sf
    sf = _load_sf()
    sf.reset_for_tests()
    fix = tu.make_engine_like_fixture(seed=777)
    gs, pipe, loc = fix
    del gs["prev_chunk_last_frame"]          # sabotage one mapping source
    view = _live_view(fix, 1)
    m = sf.capture_fork_state_digest(view, {"main": None}, fork_chunk=1,
                                     branch_id="factual")
    assert m.get("missing_required_paths") == ["prev_frame_pix"], \
        m.get("missing_required_paths")
    assert m["fields"]["F02"]["paths"]["prev_frame_pix"]["status"] == "MISSING"
    # harness-side digest reports the same loud miss
    mh = fsd.capture(view, {"main": None}, fork_chunk=1, branch_id="cf")
    assert mh.get("missing_required_paths") == ["prev_frame_pix"]
    # and the capture HOOK aborts the run loudly on such state
    import torch as _t2
    os.environ[sf.ENV_FORK] = json.dumps({"fork_chunk": 1, "mode": "capture",
                                          "out_dir": os.path.join(
                                              tempfile.gettempdir(),
                                              "sc1-v2-negout")})
    try:
        sf.maybe_fork_boundary(1, {"main": _t2.Generator().manual_seed(1)},
                               pipeline=view)
        raise AssertionError("REQUIRED-missing boundary must abort loudly")
    except RuntimeError as exc:
        assert "missing REQUIRED fields" in str(exc) and \
            "prev_frame_pix" in str(exc)
    finally:
        os.environ.pop(sf.ENV_FORK, None)
        sf.reset_for_tests()
    return True


@case("RNG1 strict CPU RNG: two fresh process-equivalent inits agree at fork")
def t_rng1():
    global sf
    sf = _load_sf()

    def fresh_init():
        sf.reset_for_tests()
        old = {k: os.environ.get(k) for k in (sf.ENV_BASE_SEED, sf.ENV_PAIR_ID)}
        os.environ[sf.ENV_BASE_SEED] = "123456"
        os.environ[sf.ENV_PAIR_ID] = tu.PAIR_ID
        try:
            cfg = {"fork_chunk": 1, "mode": "capture", "out_dir": "x"}
            rec = sf.ensure_strict_cpu_rng(cfg, 0)
            return rec, rec["cpu_rng_sha256_after_init"]
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

    rec_a, sha_a = fresh_init()
    rec_b, sha_b = fresh_init()
    assert rec_a["seed"] == rec_b["seed"] and sha_a == sha_b
    assert sha_a == hashlib.sha256(
        __import__("torch").get_rng_state().contiguous().reshape(-1).numpy()
        .tobytes()).hexdigest()
    # derivation excludes branch identity: same inputs -> same seed
    assert sf.derive_strict_cpu_seed("1", 2, "p") == \
        sf.derive_strict_cpu_seed("1", 2, "p")
    assert sf.derive_strict_cpu_seed("1", 2, "p") != \
        sf.derive_strict_cpu_seed("2", 2, "p")
    sf.reset_for_tests()
    return True


@case("RNG2 different derived seed -> F10 CPU-RNG mismatch caught by VALIDATOR")
def t_rng2():
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td)
        # rebuild the CHILD state digest under a DIFFERENT default-CPU stream
        root = tu.make_mock_root()
        gens = tu.make_generators()
        _t().rand(4)                       # perturb the default CPU generator
        child = fsd.capture(root, gens, fork_chunk=1, branch_id="counterfactual")
        cpath = fsd.save(child, os.path.join(td, "child_f10.json"))
        man2 = tu.make_manifest((fp, cp), (man["parent_state_digest"]["path"],
                                           cpath),
                                ("run-F-fix", "run-C-fix"))
        r = sc.validate_pair(fp, cp, man2)
        assert not sc.is_pass(r), sc.format_result(r)
        hits = [x for x in r["reasons"] if x.startswith("FORK_STATE_DIGEST_MISMATCH:F10")]
        assert hits, r["reasons"][:10]
    return True


@case("RNG3 CPU init leaves managed generator bytes + CUDA entry points alone")
def t_rng3():
    sf = _load_sf()
    sf.reset_for_tests()
    g = _t().Generator().manual_seed(20260826)
    s0 = bytes(g.get_state().numpy().tobytes())
    called = {"cuda": []}
    orig_ms, orig_msa = _t().cuda.manual_seed, _t().cuda.manual_seed_all

    def _boom(name):
        def f(*a, **k):
            called["cuda"].append(name)
            raise AssertionError("CUDA global RNG touched: %s" % name)
        return f
    _t().cuda.manual_seed = _boom("manual_seed")
    _t().cuda.manual_seed_all = _boom("manual_seed_all")
    try:
        cfg = {"fork_chunk": 1}
        sf.ensure_strict_cpu_rng(cfg, 0)
    finally:
        _t().cuda.manual_seed = orig_ms
        _t().cuda.manual_seed_all = orig_msa
    assert not called["cuda"], called
    assert bytes(g.get_state().numpy().tobytes()) == s0, \
        "managed main generator was mutated by the CPU init"
    sf.reset_for_tests()
    return True


@case("RNG4 gates unset -> set_rng_state NEVER called (sentinel)")
def t_rng4():
    global sf
    sf = _load_sf()
    sf.reset_for_tests()
    assert os.environ.get(sf.ENV_FORK) is None
    orig = _t().set_rng_state

    def _sentinel(*a, **k):
        raise AssertionError("torch.set_rng_state called with gates unset")

    _t().set_rng_state = _sentinel
    try:
        assert sf.maybe_fork_boundary(5, {}, {}) is None
        assert sf.strict_cpu_rng_record() is None
    finally:
        _t().set_rng_state = orig
    sf.reset_for_tests()
    return True


@case("MALICIOUS meta: fork_chunk None/garbage -> META_MISMATCH, never crash")
def t_mal():
    def poison(objs, val):
        for o in objs:
            if o.get("event") == "meta":
                o["fork_chunk"] = val
        return objs
    with tempfile.TemporaryDirectory() as td:
        for bad in (None, "garbage", [7]):
            fp, cp, man = tu.standard_pair(td)
            fp2 = rewrite(fp, lambda o: poison(o, bad), "mal-f.jsonl")
            man2 = remanifest(man, fp2, cp)
            r = sc.validate_pair(fp2, cp, man2)
            assert not sc.is_pass(r)
            assert any(x.startswith("META_MISMATCH:fork_chunk")
                       for x in r["reasons"]), r["reasons"][:8]
    return True


def _ls_case(field, marker="UNDECLARED"):
    def fn():
        with tempfile.TemporaryDirectory() as td:
            fp, cp, man = tu.standard_pair(td)

            def poison(objs):
                for o in objs:
                    if o.get("event") == "meta":
                        o[field] = marker
                return objs
            cp2 = rewrite(cp, poison, "ls.jsonl")
            man2 = tu.make_manifest((fp, cp2),
                                    (man["parent_state_digest"]["path"],
                                     man["child_state_digest"]["path"]),
                                    ("run-F-fix", "run-C-fix"),
                                    overrides={"launch_strict": True})
            r = sc.validate_pair(fp, cp2, man2)
            assert not sc.is_pass(r), sc.format_result(r)
            hits = [x for x in r["reasons"]
                    if x.startswith("IDENTITY_UNDECLARED:%s:" % field)]
            assert hits, r["reasons"][:10]
            # outside launch-strict the same ledger is only refused for
            # countersigning, not invalid outright
            man3 = tu.make_manifest((fp, cp2),
                                    (man["parent_state_digest"]["path"],
                                     man["child_state_digest"]["path"]),
                                    ("run-F-fix", "run-C-fix"))
            assert sc.refuse_gpu_countersign(r) is True, \
                "IDENTITY_UNDECLARED result must be refused for GPU countersign"
            if field == "diffusers":
                r3 = sc.validate_pair(fp, cp2, man3)
                assert sc.is_pass(r3), sc.format_result(r3)
        return True
    fn.__name__ = "ls_%s_%s" % (field, marker.lower())
    return fn


for _f in ("patch_sha256", "profile_sha256", "common_config_sha256"):
    globals()["t_ls_" + _f.rstrip("_sha256")] = case(
        "LS %s UNDECLARED -> INVALID(IDENTITY_UNDECLARED) in launch-strict" % _f,
    )(_ls_case(_f))
t_ls_diffusers = case(
    "LS diffusers UNDECLARED -> INVALID(IDENTITY_UNDECLARED) in launch-strict",
)(_ls_case("diffusers"))


@case("LS env flag EVOKE_STRICT_LAUNCH=1 activates the identity gate")
def t_ls_env():
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td)

        def poison(objs):
            for o in objs:
                if o.get("event") == "meta":
                    o["patch_sha256"] = "UNDECLARED"
            return objs
        cp2 = rewrite(cp, poison, "lse.jsonl")
        man2 = tu.make_manifest((fp, cp2),
                                (man["parent_state_digest"]["path"],
                                 man["child_state_digest"]["path"]),
                                ("run-F-fix", "run-C-fix"))
        old = os.environ.get(sc.ENV_LAUNCH_STRICT)
        os.environ[sc.ENV_LAUNCH_STRICT] = "1"
        try:
            r = sc.validate_pair(fp, cp2, man2)
        finally:
            if old is None:
                os.environ.pop(sc.ENV_LAUNCH_STRICT, None)
            else:
                os.environ[sc.ENV_LAUNCH_STRICT] = old
        assert not sc.is_pass(r)
        assert any(x.startswith("IDENTITY_UNDECLARED:patch_sha256")
                   for x in r["reasons"]), r["reasons"][:8]
    return True


@case("LS manifest missing counterfactual ledger-artifact hash -> INVALID")
def t_ls_artifact():
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td)
        man2 = copy.deepcopy(man)
        del man2["artifacts"]["counterfactual_log"]
        r = sc.validate_pair(fp, cp, man2)
        assert not sc.is_pass(r)
        assert any(x.startswith("PAIR_MANIFEST_ARTIFACTS:")
                   for x in r["reasons"]), r["reasons"]
        man3 = copy.deepcopy(man)
        man3["artifacts"]["factual_log"] = {"path": man["artifacts"]["factual_log"]["path"]}
        man3.pop("launch_strict", None)
        r3 = sc.validate_pair(fp, cp, man3)
        assert not sc.is_pass(r3)
        assert any(x.startswith("PAIR_MANIFEST_ARTIFACT_SHA:factual_log")
                   for x in r3["reasons"]), r3["reasons"]
    return True


@case("LS TEST_MODE_ONLY ledgers are NEVER GPU-countersignable")
def t_ls_refuse():
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td)
        r = sc.validate_pair(fp, cp, man)
        assert sc.is_pass(r)
        assert sc.refuse_gpu_countersign(r) is False      # clean pass -> allow
        man_t = copy.deepcopy(man)
        man_t["patch_sha256"] = "TEST_MODE_ONLY"
        assert sc.refuse_gpu_countersign(man_t) is True
        man_u = copy.deepcopy(man)
        man_u["common_config_sha256"] = "UNDECLARED"
        assert sc.refuse_gpu_countersign(man_u) is True

        def mark(objs):
            for o in objs:
                if o.get("event") == "meta":
                    o["diffusers"] = "TEST_MODE_ONLY"
            return objs
        cp2 = rewrite(cp, mark, "tmo.jsonl")
        objs = lines_of(cp2)
        tmo_meta = next(o for o in objs if o.get("event") == "meta")
        assert sc.refuse_gpu_countersign({"metas": [tmo_meta]}) is True
    return True


@case("MPF lazy-meta rewrite failure -> META_PATCH_FAILURE event + "
      "INVALID(META_CONTINUATION_UNVERIFIED)")
def t_mpf():
    global sf
    sf = _load_sf()
    sf.reset_for_tests()
    old_env = {k: os.environ.get(k) for k in (
        sf.ENV_LEDGER, sf.ENV_FORK, sf.ENV_RUN_ID, sf.ENV_PAIR_ID)}
    try:
        with tempfile.TemporaryDirectory() as td:
            cap_dir = os.path.join(td, "cap")
            base = os.path.join(td, "mpf.base.jsonl")
            os.environ[sf.ENV_RUN_ID] = "run-MPF"
            os.environ[sf.ENV_PAIR_ID] = tu.PAIR_ID
            os.environ[sf.ENV_LEDGER] = base
            fix = tu.make_engine_like_fixture(seed=42)
            sidecar = None
            parent_digest = None
            cfg_cap = {"fork_chunk": 1, "mode": "capture", "out_dir": cap_dir}
            os.environ[sf.ENV_FORK] = json.dumps(cfg_cap)
            main = _t().Generator().manual_seed(9)
            for k in range(2):
                sf.maybe_fork_boundary(k, {"main": main},
                                       pipeline=_live_view(fix, k))
            sf.reset_for_tests()
            parent_digest = os.path.join(cap_dir,
                                         "fork_state_digest_chunk1.json")
            sidecar = os.path.join(cap_dir, "fork_capture_chunk1.json")
            os.environ[sf.ENV_RUN_ID] = "run-MPF2"
            os.environ[sf.ENV_LEDGER] = base
            cfg_res = {"fork_chunk": 1, "mode": "restore", "sidecar": sidecar,
                       "parent_state_digest": parent_digest}
            os.environ[sf.ENV_FORK] = json.dumps(cfg_res)
            main2 = _t().Generator().manual_seed(9)
            sf.log_draw("R1", _t().zeros(2), generator=main2,
                        gen_before=sf.gen_state_of(main2))   # open ledger+meta
            # force the header rewrite to fail at its read step
            real_open = open
            target = os.path.abspath(base.replace(".jsonl", ".run-MPF2.jsonl"))

            def sabotaged(path, mode="r", *a, **k):
                if mode == "r" and os.path.abspath(str(path)) == target:
                    raise OSError("MPF-simulated read failure")
                return real_open(path, mode, *a, **k)
            import builtins
            builtins.open, saved = sabotaged, builtins.open
            raised = False
            try:
                sf.maybe_fork_boundary(1, {"main": main2},
                                       pipeline=_live_view(fix, 1))
            except RuntimeError as exc:
                raised = True
                assert "META_CONTINUATION_UNVERIFIED" in str(exc)
            finally:
                builtins.open = saved
            assert raised
            assert sf.continuation_verified() is False
            sf.reset_for_tests()
            mpf_path = base.replace(".jsonl", ".run-MPF2.jsonl")
            evs = [json.loads(x) for x in open(mpf_path, encoding="utf-8")
                   if x.strip()]
            assert any(o.get("event") == "META_PATCH_FAILURE" and
                       "MPF-simulated" in (o.get("error") or "")
                       for o in evs), evs[-3:]
    finally:
        sf.reset_for_tests()
        for k, v in old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    # validator-level: a META_PATCH_FAILURE marker poisons the pair
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td)

        def inject(objs):
            objs.append({"event": "META_PATCH_FAILURE",
                         "seq": 99999, "error": "simulated"})
            return objs
        cp2 = rewrite(cp, inject, "mpf2.jsonl")
        man2 = tu.make_manifest((fp, cp2),
                                (man["parent_state_digest"]["path"],
                                 man["child_state_digest"]["path"]),
                                ("run-F-fix", "run-C-fix"))
        r = sc.validate_pair(fp, cp2, man2)
        assert not sc.is_pass(r)
        assert any(x.startswith("META_CONTINUATION_UNVERIFIED:counterfactual")
                   for x in r["reasons"]), r["reasons"][-6:]
    return True


def main():
    fails = blocked = passed = 0
    for name, fn in RESULTS:
        try:
            fn()
            print("PASS  %s" % name)
            passed += 1
        except BLOCKED as exc:
            print("BLOCKED  %s (%s)" % (name, exc))
            blocked += 1
        except Exception as exc:
            print("FAIL  %s (%s)" % (name, exc))
            traceback.print_exc(limit=3)
            fails += 1
    print("---")
    print("passed=%d failed=%d blocked=%d" % (passed, fails, blocked))
    raise SystemExit(1 if fails else 0)


if __name__ == "__main__":
    main()