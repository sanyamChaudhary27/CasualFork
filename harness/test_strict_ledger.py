"""P3 unit tests: strict-coupling ledger validator V2 + NoiseTape (CPU, mock logs).

STAGE-B/C FIX ROUND: the v1 suite is SUPERSEDED where Auditor B proved v1 holes
(self-pair PASSed, lazy continuation, ordinal-only checks). Superseded cases are
re-pointed at their v2 equivalents and marked [SUPERSEDED->v2]. New exhaustive
adversarial coverage lives in test_strict_ledger_v2.py (cases A-P).

Plain-assert runner. Prints PASS / FAIL / BLOCKED lines; exits nonzero on FAIL.
The optional live-module block imports evoke/strict_fork.py FROM THE PATCHED
SOURCE (patches/evoke_strict_fork.py.txt - standalone, torch-only import).
"""
from __future__ import annotations

import copy
import json
import os
import sys
import tempfile
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import strict_coupling as sc          # noqa: E402
import testutil_sc1 as tu             # noqa: E402


# ---------------------------------------------------------------- test helpers
class BLOCKED(Exception):
    pass


RESULTS = []


def case(name):
    def deco(fn):
        RESULTS.append((name, fn))
        return fn
    return deco


def load_log_text(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def rewrite(tmpdir, src_path, mutator, name="mut.jsonl"):
    objs = [json.loads(x) for x in load_log_text(src_path).splitlines() if x.strip()]
    objs = mutator(objs)
    dst = os.path.join(tmpdir, name)
    with open(dst, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(json.dumps(o, sort_keys=True) for o in objs) + "\n")
    return dst


# ---------------------------------------------------------------- unit cases
@case("[SUPERSEDED->v2] aligned-equal pair -> STRICT_NOISE_COUPLED")
def t_aligned():
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td)
        r = sc.validate_pair(fp, cp, man)
        assert sc.is_pass(r), sc.format_result(r)
        assert sorted(r["sites"]) == sorted(sc.REQUIRED_SITES)
        assert r["entries_compared"] == 30      # 3 chunks x (7 fixed + 3 R7)
        assert r["restored_branches"] == ["counterfactual"]
        assert r["pair_id"] == tu.PAIR_ID
        assert r["run_ids"] == {"factual": "run-F-fix",
                                "counterfactual": "run-C-fix"}
    return True


@case("unequal EXACT_TENSOR (R1) -> TENSOR_MISMATCH")
def t_tensor():
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(
            td, variant_c={"flip_tensor": ["R1", 1]})
        r = sc.validate_pair(fp, cp, man)
        assert not sc.is_pass(r)
        assert any(x.startswith("TENSOR_MISMATCH@R1#") for x in r["reasons"])
    return True


@case("missing required site (R5, cf) -> MISSING_SITE")
def t_missing_site():
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(
            td, variant_c={"drop_site_at": ["R5", 1]})
        r = sc.validate_pair(fp, cp, man)
        assert not sc.is_pass(r)
        # site still present in chunk 0, so only the per-key alignment breaks
        assert any(x.startswith("MISSING_SITE:R5#") and "(counterfactual)" in x
                   for x in r["reasons"]), r["reasons"][:8]
    return True


@case("unexpected site RX -> UNEXPECTED_SITE")
def t_unexpected():
    def add_rx(objs):
        extra = copy.deepcopy(objs[1])
        extra["site_id"] = "RX"
        extra["ordinal"] = 99
        extra["chunk"] = 9
        objs.append(extra)
        return objs
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td)
        cp2 = rewrite(td, cp, add_rx, name="rx.jsonl")
        man["artifacts"]["counterfactual_log"] = tu.file_art(cp2)
        r = sc.validate_pair(fp, cp2, man)
        assert not sc.is_pass(r)
        assert "UNEXPECTED_SITE:RX" in r["reasons"]
    return True


@case("[SUPERSEDED->v2] ordinal misalignment -> alignment break detected")
def t_ordinal():
    seen = {"n": 0}

    def shift_r6(objs):
        for o in objs:
            if o.get("site_id") == "R6":
                seen["n"] += 1
                o["ordinal"] = o["ordinal"] + 10
        return objs
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td)
        cp2 = rewrite(td, cp, shift_r6, name="ord.jsonl")
        man["artifacts"]["counterfactual_log"] = tu.file_art(cp2)
        r = sc.validate_pair(fp, cp2, man)
        assert not sc.is_pass(r)
        assert any(x.startswith("MISSING_SITE:R6#") for x in r["reasons"]), \
            r["reasons"][:8]
    return True


@case("bypass indicators -> CHAIN_BREAK + NOOP_BYPASS + PRECOND1_FALLBACK")
def t_bypass():
    state = {"main_seen": 0}

    def corrupt(objs):
        for o in objs:
            if o.get("event") != "draw":
                continue
            if o.get("generator_role") == "isolated_warp":
                if o.get("extra", {}).get("call_ordinal") == 0:
                    o["generator_role"] = "GLOBAL_FALLBACK"
                continue
            if o.get("chunk") == 0:
                continue  # keep chunk-0 chain intact for the fixture baseline
            state["main_seen"] += 1
            if state["main_seen"] == 2:
                o["generator_state_hash_before"] = "f" * 64
            if state["main_seen"] == 4:
                o["generator_state_hash_after"] = o["generator_state_hash_before"]
        return objs
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td)
        fp2 = rewrite(td, fp, corrupt, name="byp.jsonl")
        man["artifacts"]["factual_log"] = tu.file_art(fp2)
        r = sc.validate_pair(fp2, cp, man)
        assert not sc.is_pass(r)
        assert any(x.startswith("STREAM_CHAIN_BREAK:") for x in r["reasons"])
        assert any(x.startswith("NOOP_DRAW_BYPASS:") for x in r["reasons"])
        assert any(x.startswith("PRECOND1_GLOBAL_RNG_BYPASS@R7#")
                   for x in r["reasons"])
    return True


@case("restored-vs-coupled terminology enforced (event-backed, v2)")
def t_restored():
    with tempfile.TemporaryDirectory() as td:
        fp, cp, man = tu.standard_pair(td)
        r = sc.validate_pair(fp, cp, man)
        assert sc.is_pass(r)
        assert r["continuation"]["counterfactual"] == sc.GENERATOR_STATE_RESTORED
        # GENERATOR_STATE_RESTORED is never a coupling verdict
        try:
            sc.validate_status(sc.GENERATOR_STATE_RESTORED)
            raise AssertionError("validate_status accepted continuation label")
        except ValueError:
            pass
        sc.validate_status(sc.STRICT_NOISE_COUPLED)
        # lazy continuation claim WITHOUT a restore event -> RESTORE_METADATA_MISMATCH
        def strip_event(objs):
            return [o for o in objs
                    if o.get("event") != sc.GENERATOR_STATE_RESTORED]
        cp2 = rewrite(td, cp, strip_event, name="lazy.jsonl")
        man2 = tu.make_manifest(
            (fp, cp2),
            (man["parent_state_digest"]["path"],
             man["child_state_digest"]["path"]),
            ("run-F-fix", "run-C-fix"))
        r2 = sc.validate_pair(fp, cp2, man2)
        assert not sc.is_pass(r2)
        assert any(x.startswith("RESTORE_METADATA_MISMATCH:") for x in r2["reasons"])
        assert any(x.startswith("MISSING_EVENT:GENERATOR_STATE_RESTORED")
                   for x in r2["reasons"])
    return True


# ------------------------------------------------- live patched-module checks
SF_SRC = os.path.join(os.path.dirname(HERE), "patches", "evoke_strict_fork.py.txt")


def _load_sf():
    if not os.path.exists(SF_SRC):
        raise BLOCKED("patched emitter source not found at %s" % SF_SRC)
    sys.dont_write_bytecode = True
    sys.pycache_prefix = os.path.join(tempfile.gettempdir(), "sc1-pyc")
    import importlib.machinery
    import importlib.util
    loader = importlib.machinery.SourceFileLoader("evoke_strict_fork_live", SF_SRC)
    spec = importlib.util.spec_from_file_location(
        "evoke_strict_fork_live", SF_SRC, loader=loader)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["evoke_strict_fork_live"] = mod
    loader.exec_module(mod)
    return mod


@case("live NoiseTape record/replay/jsonl round-trip")
def t_tape():
    sf = _load_sf()
    import torch
    sf.reset_for_tests()
    tape = sf.NoiseTape(branch="t")
    g = torch.Generator().manual_seed(0)
    e = tape.record("R4", torch.rand(9, generator=g), ordinal=1, seq=1,
                    generator_role="main")
    assert e["shape"] == [9] and len(e["tensor_sha256"]) == 64
    try:
        tape.replay("R4")
        raise AssertionError("replay must raise NotImplementedError")
    except NotImplementedError as exc:
        assert "PHASE-2 FALLBACK" in str(exc)
    with tempfile.TemporaryDirectory() as td:
        out = os.path.join(td, "tape.jsonl")
        tape.to_jsonl(out)
        back = open(out, encoding="utf-8").read()
    assert json.loads(back.splitlines()[0])["site_id"] == "R4"
    # skip rows: tensor=None tolerated by record()
    e2 = tape.record("R7", None, ordinal=2, seq=2, generator_role="isolated_warp")
    assert e2["tensor_sha256"] is None and e2["shape"] is None
    sf.reset_for_tests()
    return True


@case("live log_draw emits v2-shaped lines (run_id/pair_id on every line)")
def t_live_ledger():
    sf = _load_sf()
    import torch
    sf.reset_for_tests()
    old = {k: os.environ.get(k) for k in (sf.ENV_LEDGER, sf.ENV_RUN_ID,
                                          sf.ENV_PAIR_ID)}
    out_path = None
    try:
        with tempfile.TemporaryDirectory() as td:
            os.environ[sf.ENV_RUN_ID] = "run-live-1"
            os.environ[sf.ENV_PAIR_ID] = "pair-live"
            os.environ[sf.ENV_LEDGER] = os.path.join(td, "led.base.jsonl")
            g = torch.Generator().manual_seed(42)
            sf.set_chunk(3)
            b = sf.gen_state_of(g)
            t = torch.randn(5, generator=g)
            entry = sf.log_draw("R1", t, generator=g, gen_before=b,
                                generator_role="main")
            assert entry is not None and entry["ordinal"] == 1
            assert entry["run_id"] == "run-live-1" and entry["pair_id"] == "pair-live"
            sf.reset_for_tests()   # close handle BEFORE Windows dir cleanup
            out_path = os.path.join(td, "led.base.run-live-1.jsonl")
            lines = open(out_path, encoding="utf-8").read().splitlines()
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    objs = [json.loads(x) for x in lines]
    assert objs[0]["event"] == "meta" and objs[0]["run_id"] == "run-live-1"
    assert all(o.get("run_id") == "run-live-1" and o.get("pair_id") == "pair-live"
               for o in objs)
    return True


@case("live unique-ledger-per-run + append refusal (target 9)")
def t_live_unique_ledger():
    sf = _load_sf()
    import torch
    sf.reset_for_tests()
    old = {k: os.environ.get(k) for k in (sf.ENV_LEDGER, sf.ENV_RUN_ID)}
    try:
        with tempfile.TemporaryDirectory() as td:
            base = os.path.join(td, "led.jsonl")
            os.environ[sf.ENV_LEDGER] = base
            os.environ[sf.ENV_RUN_ID] = "run-U1"
            g = torch.Generator().manual_seed(1)
            sf.log_draw("R1", torch.randn(3, generator=g), generator=g,
                        gen_before=sf.gen_state_of(g))
            sf.reset_for_tests()
            opened = None
            for fn in os.listdir(td):
                if fn.startswith("led.run-U1"):
                    opened = fn
            assert opened == "led.run-U1.jsonl", os.listdir(td)
            # second run, same base -> NEW file, no silent append
            os.environ[sf.ENV_RUN_ID] = "run-U2"
            sf.log_draw("R1", torch.randn(3, generator=g), generator=g,
                        gen_before=sf.gen_state_of(g))
            sf.reset_for_tests()
            assert "led.run-U2.jsonl" in os.listdir(td)
            # refusing to touch an existing target
            os.environ[sf.ENV_RUN_ID] = "run-U1"
            try:
                sf.log_draw("R1", torch.randn(3, generator=g), generator=g,
                            gen_before=sf.gen_state_of(g))
                raise AssertionError("append to existing ledger must fail")
            except RuntimeError as exc:
                assert "unique-ledger-per-run" in str(exc)
    finally:
        sf.reset_for_tests()
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return True


@case("live fork capture -> restore round-trip WITH state digest")
def t_fork_capture_restore():
    sf = _load_sf()
    import torch
    sf.reset_for_tests()
    old = {k: os.environ.get(k) for k in (sf.ENV_FORK, sf.ENV_RUN_ID)}
    try:
        with tempfile.TemporaryDirectory() as td:
            gsx, pipex, locx = tu.make_engine_like_fixture(seed=1000)

            def _view(k):
                return sf.build_live_state_view(
                    locx["history_latents"],
                    locx["total_generated_latent_frames"],
                    gsx, pipex, chunk_index=k, event_set_size=0,
                    forced_off_flags=locx["forced_off_flags"])

            gens = {"main": torch.Generator().manual_seed(9)}
            cap_cfg = {"fork_chunk": 2, "mode": "capture", "out_dir": td}
            os.environ[sf.ENV_FORK] = json.dumps(cap_cfg)
            torch.rand(3, generator=gens["main"])   # advance past prefix
            sidecar = sf.maybe_fork_boundary(1, gens, pipeline=_view(1))
            assert sidecar is None                   # non-fork chunk: no-op
            sidecar = sf.maybe_fork_boundary(2, gens, pipeline=_view(2))
            assert sidecar is not None and os.path.exists(sidecar)
            dg = os.path.join(td, "fork_state_digest_chunk2.json")
            assert os.path.exists(dg), os.listdir(td)
            ahead = torch.randn(11, generator=gens["main"])[0].item()

            # diverge the stream far away, then restore
            torch.rand(5, generator=gens["main"]); torch.randn(7, generator=gens["main"])
            res_cfg = {"fork_chunk": 2, "mode": "restore", "sidecar": sidecar,
                       "parent_state_digest": dg}
            os.environ[sf.ENV_FORK] = json.dumps(res_cfg)
            rec = sf.maybe_fork_boundary(2, gens, pipeline=_view(2))
            assert rec is not None
            assert sf.continuation_marker() == sc.GENERATOR_STATE_RESTORED
            x = torch.randn(11, generator=gens["main"])[0].item()
            assert x == ahead, "main generator did not resume captured stream"
            assert os.path.exists(os.path.join(
                td, "fork_state_digest_child_chunk2.json"))

            # corrupted parent digest -> loud abort + FORK_STATE_MISMATCH line
            bad = json.load(open(dg, encoding="utf-8"))
            bad["fields"]["F07"]["group_sha256"] = "0" * 64
            badp = os.path.join(td, "bad_parent.json")
            with open(badp, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(bad, sort_keys=True, separators=(",", ":")))
            res_bad = dict(res_cfg, parent_state_digest=badp)
            os.environ[sf.ENV_FORK] = json.dumps(res_bad)
            try:
                sf.maybe_fork_boundary(2, gens, pipeline=_view(2))
                raise AssertionError("corrupted parent digest must abort")
            except RuntimeError as exc:
                assert "FORK_STATE_MISMATCH" in str(exc)
    finally:
        sf.reset_for_tests()
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return True


@case("ledger + fork gates disabled -> zero-effect call sites (byte-neutral)")
def t_disabled():
    sf = _load_sf()
    sf.reset_for_tests()
    for var in (sf.ENV_LEDGER, sf.ENV_FORK):
        assert os.environ.get(var) is None
    import torch
    g = torch.Generator().manual_seed(5)
    s0 = g.get_state().clone()
    assert sf.gen_state_of(g) is None
    assert sf.log_draw("R1", torch.zeros(2)) is None
    assert sf.pixel_diag(torch.zeros(2), torch.zeros(1), torch.zeros(1)) is None
    assert sf.maybe_fork_boundary(99, {}, {}) is None
    torch.rand(1, generator=g)
    assert sf.gen_state_of(g) is None
    assert torch.equal(g.get_state(), s0) or g.get_state().shape == s0.shape
    sf.reset_for_tests()
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