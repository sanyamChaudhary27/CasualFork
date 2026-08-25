"""P3 unit tests: strict-coupling ledger validator + NoiseTape (pure CPU, mock logs).

Plain-assert runner. Prints PASS / FAIL / BLOCKED lines; exits nonzero on FAIL.
The optional live-module block imports evoke/strict_fork.py FROM THE PATCHED WORK
TREE (temp copy the patch was authored in) via importlib - no pip installs, no
weights, no GPU. If that tree is absent, those cases report BLOCKED honestly.
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

import strict_coupling as sc  # noqa: E402


# ---------------------------------------------------------------- mock ledgers
def _sha(b):
    import hashlib
    return hashlib.sha256(b).hexdigest()


def simulate_branch(n_chunks=2):
    """Replay the SC1 per-chunk draw order through two REAL cpu Generators and
    emit validator-shaped entries (same code paths as evoke.strict_fork.log_draw)."""
    import torch
    main = torch.Generator(device="cpu").manual_seed(1234)
    iso = torch.Generator(device="cpu").manual_seed(777)
    order = ["R2", "R3", "R4", "R5", "R7", "R1", "R6", "R6"]
    shapes = {"R1": (1, 16, 9, 48, 80), "R2": (1, 16, 1, 48, 80), "R3": (1, 16, 9, 48, 80),
              "R4": (9,), "R5": (1, 16, 9, 48, 80), "R6": (432, 4), "R7": (2000,)}
    seq = 0
    meta = {"event": "meta", "pin": "74d268516d95c8fceadd2378f91a73f9f187042b",
            "branch_id": "factual", "continuation": None}
    entries = []
    for chunk in range(n_chunks):
        for site in order:
            seq += 1
            role = "isolated_warp" if site == "R7" else "main"
            gen = iso if site == "R7" else main
            before = _sha(gen.get_state().numpy().tobytes())
            t = torch.randn(*shapes[site], generator=gen)
            after = _sha(gen.get_state().numpy().tobytes())
            ord_key = (site, "iso") if site == "R7" else site
            entries.append({
                "event": "draw", "seq": seq, "site_id": site,
                "ordinal": sum(1 for e in entries if e["site_id"] == site) + 1,
                "branch_id": "factual", "chunk": chunk,
                "stage": 1 if site == "R6" else None,
                "generator_role": role,
                "generator_state_hash_before": before,
                "generator_state_hash_after": after,
                "tensor_sha256": sc.tensor_sha256(t) if hasattr(sc, "tensor_sha256") else _sha(t.numpy().tobytes()),
                "shape": list(t.shape), "dtype": str(t.dtype),
                "global_rng_sha256": "g%03d" % seq,
            })
    return meta, entries


def to_jsonl(meta, entries):
    return "\n".join([json.dumps(meta, sort_keys=True)] +
                     [json.dumps(e, sort_keys=True) for e in entries]) + "\n"


def make_pair():
    fm, fe = simulate_branch()
    cm, ce = copy.deepcopy(simulate_branch())
    cm["branch_id"] = "counterfactual"
    for e in ce:
        e["branch_id"] = "counterfactual"
    return (to_jsonl(fm, fe), to_jsonl(cm, ce))


# ---------------------------------------------------------------- test helpers
class BLOCKED(Exception):
    pass


RESULTS = []


def case(name):
    def deco(fn):
        RESULTS.append((name, fn))
        return fn
    return deco


# ---------------------------------------------------------------- unit cases
@case("aligned-equal pair -> STRICT_NOISE_COUPLED")
def t_aligned():
    f, c = make_pair()
    r = sc.compare_coupling_logs(f, c)
    assert sc.is_pass(r), sc.format_result(r)
    assert r["status"] == sc.STRICT_NOISE_COUPLED
    assert not r["reasons"], r["reasons"]
    assert sorted(r["sites"]) == sorted(sc.REQUIRED_SITES)
    assert r["entries_compared"] == 16
    return True


@case("unequal tensor -> STRICT_COUPLING_INVALID (TENSOR_MISMATCH)")
def t_tensor():
    f, c = make_pair()
    lines = c.splitlines()
    objs = [json.loads(x) for x in lines]
    for o in objs:
        if o.get("site_id") == "R1":
            o["tensor_sha256"] = "0" * 64
            break
    c2 = "\n".join(json.dumps(o, sort_keys=True) for o in objs) + "\n"
    r = sc.compare_coupling_logs(f, c2)
    assert not sc.is_pass(r)
    assert any(x.startswith("TENSOR_MISMATCH@R1#") for x in r["reasons"]), r["reasons"]
    return True


@case("missing required site -> INVALID (MISSING_SITE)")
def t_missing_site():
    f, c = make_pair()
    lines = [x for x in c.splitlines() if '"R5"' not in x]
    c2 = "\n".join(lines) + "\n"
    r = sc.compare_coupling_logs(f, c2)
    assert not sc.is_pass(r)
    assert "MISSING_SITE:R5 (counterfactual)" in r["reasons"], r["reasons"]
    assert any(x.startswith("MISSING_SITE:R5#") for x in r["reasons"])
    return True


@case("unexpected site -> INVALID (UNEXPECTED_SITE)")
def t_unexpected():
    f, c = make_pair()
    objs = [json.loads(x) for x in c.splitlines()]
    extra = dict(objs[1])
    extra["site_id"] = "RX"
    extra["ordinal"] = 1
    objs.append(extra)
    c2 = "\n".join(json.dumps(o, sort_keys=True) for o in objs) + "\n"
    r = sc.compare_coupling_logs(f, c2)
    assert not sc.is_pass(r)
    assert "UNEXPECTED_SITE:RX" in r["reasons"], r["reasons"]
    return True


@case("ordinal misalignment -> INVALID (ORDINAL_MISMATCH)")
def t_ordinal():
    f, c = make_pair()
    objs = [json.loads(x) for x in c.splitlines()]
    seen = 0
    for o in objs:
        if o.get("site_id") == "R6":
            seen += 1
            o["ordinal"] = seen + 1  # shift 1,2 -> 2,3
    c2 = "\n".join(json.dumps(o, sort_keys=True) for o in objs) + "\n"
    r = sc.compare_coupling_logs(f, c2)
    assert not sc.is_pass(r)
    assert any(x.startswith("ORDINAL_MISMATCH:R6 ") for x in r["reasons"]), r["reasons"]
    return True


@case("bypass indicators -> INVALID (STREAM_CHAIN_BREAK + PRECOND1_GLOBAL_RNG_BYPASS)")
def t_bypass():
    f, c = make_pair()
    objs = [json.loads(x) for x in f.splitlines()]
    main_seen = 0
    for o in objs:
        if o.get("site_id") in ("R1", "R2", "R3", "R4", "R5", "R6"):
            main_seen += 1
            if main_seen == 2:   # break the chain at a NON-first draw so the
                o["generator_state_hash_before"] = "f" * 64   # predecessor link is checked
            if main_seen == 4:
                o["generator_state_hash_after"] = o["generator_state_hash_before"]  # noop draw
        if o.get("site_id") == "R7":
            o["generator_role"] = "GLOBAL_FALLBACK"
    f2 = "\n".join(json.dumps(o, sort_keys=True) for o in objs) + "\n"
    r = sc.compare_coupling_logs(f2, c)
    assert not sc.is_pass(r)
    assert any(x.startswith("STREAM_CHAIN_BREAK:") for x in r["reasons"]), r["reasons"]
    assert any(x.startswith("NOOP_DRAW_BYPASS:") for x in r["reasons"]), r["reasons"]
    assert any(x.startswith("PRECOND1_GLOBAL_RNG_BYPASS@R7#") for x in r["reasons"]), r["reasons"]
    return True


@case("restored-vs-coupled terminology enforced")
def t_restored():
    f, c = make_pair()
    # continuation label recorded, data still coupled -> PASS with restoration noted
    objs = [json.loads(x) for x in c.splitlines()]
    objs[0]["continuation"] = sc.GENERATOR_STATE_RESTORED
    c2 = "\n".join(json.dumps(o, sort_keys=True) for o in objs) + "\n"
    r = sc.compare_coupling_logs(f, c2)
    assert sc.is_pass(r), sc.format_result(r)
    assert r["continuation"]["counterfactual"] == sc.GENERATOR_STATE_RESTORED
    assert r["restored_branches"] == ["counterfactual"]
    # GENERATOR_STATE_RESTORED is never a coupling verdict
    try:
        sc.validate_status(sc.GENERATOR_STATE_RESTORED)
        raise AssertionError("validate_status accepted GENERATOR_STATE_RESTORED")
    except ValueError:
        pass
    sc.validate_status(sc.STRICT_NOISE_COUPLED)
    sc.validate_status(sc.STRICT_COUPLING_INVALID)
    # bogus continuation label -> TERMINOLOGY_VIOLATION + RESTORE_METADATA_MISMATCH
    objs[0]["continuation"] = "RESTORED"
    c3 = "\n".join(json.dumps(o, sort_keys=True) for o in objs) + "\n"
    r2 = sc.compare_coupling_logs(f, c3)
    assert not sc.is_pass(r2)
    assert any(x.startswith("TERMINOLOGY_VIOLATION:") for x in r2["reasons"]), r2["reasons"]
    assert any(x.startswith("RESTORE_METADATA_MISMATCH") for x in r2["reasons"])
    return True


# ------------------------------------------------- live patched-module checks
WORK_TREE = os.environ.get(
    "EVOKE_PATCH_WORK",
    os.path.join(os.environ.get("TEMP", "/tmp"), "opencode", "sc1-wk"),
)
SF_PATH = os.path.join(WORK_TREE, "evoke", "strict_fork.py")


def _load_sf():
    if not os.path.exists(SF_PATH):
        raise BLOCKED("patched work tree not found at %s (set EVOKE_PATCH_WORK)" % SF_PATH)
    sys.dont_write_bytecode = True
    sys.pycache_prefix = os.path.join(tempfile.gettempdir(), "sc1-pyc")
    import importlib.util
    spec = importlib.util.spec_from_file_location("evoke_strict_fork_live", SF_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
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
    assert len(tape.entries) == 1
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
    sf.reset_for_tests()
    return True


@case("live log_draw -> validator-compatible ledger (self-pair PASS)")
def t_live_ledger():
    sf = _load_sf()
    import torch
    sf.reset_for_tests()
    old = os.environ.get("EVOKE_STRICT_LEDGER_PATH")
    with tempfile.TemporaryDirectory() as td:
        os.environ["EVOKE_STRICT_LEDGER_PATH"] = os.path.join(td, "led.jsonl")
        try:
            g = torch.Generator().manual_seed(42)
            sf.set_chunk(3)
            b = sf.gen_state_of(g)
            t = torch.randn(5, generator=g)
            entry = sf.log_draw("R1", t, generator=g, gen_before=b, generator_role="main")
            assert entry is not None and entry["ordinal"] == 1
        finally:
            sf.reset_for_tests()   # closes the ledger handle BEFORE Windows dir cleanup
            if old is None:
                os.environ.pop("EVOKE_STRICT_LEDGER_PATH", None)
            else:
                os.environ["EVOKE_STRICT_LEDGER_PATH"] = old
        text = open(os.path.join(td, "led.jsonl"), encoding="utf-8").read()
    r = sc.compare_coupling_logs(text, text)
    # A 1-draw smoke ledger cannot satisfy full 7-site coverage, so the verdict is
    # INVALID - but the ONLY reasons must be coverage gaps: format parses cleanly,
    # fields align, hashes chain, i.e. the patched tree emits validator-shaped ledgers.
    assert all(x.startswith("MISSING_SITE:") for x in r["reasons"]), r["reasons"]
    assert r["entries_compared"] == 1
    full = sc.compare_coupling_logs(*make_pair())
    assert sc.is_pass(full)
    sf.reset_for_tests()
    return True


@case("live fork capture -> restore round-trip (GENERATOR_STATE_RESTORED)")
def t_fork_capture_restore():
    sf = _load_sf()
    import torch
    sf.reset_for_tests()
    with tempfile.TemporaryDirectory() as td:
        cap_cfg = {"fork_chunk": 2, "mode": "capture", "out_dir": td}
        os.environ["EVOKE_STRICT_FORK_JSON"] = json.dumps(cap_cfg)
        try:
            g = torch.Generator().manual_seed(9)
            pd = torch.Generator().manual_seed(10)
            torch.rand(3, generator=g)   # advance
            gens = sf.collect_generators(g, pd)
            sidecar = sf.maybe_fork_boundary(1, gens)      # not fork chunk -> no-op
            assert sidecar is None
            sidecar = sf.maybe_fork_boundary(2, gens)      # capture
            assert sidecar is not None and os.path.exists(sidecar)
            meta = json.load(open(sidecar, encoding="utf-8"))
            assert set(meta["generators"]) == {"geo_patchdrop", "main"}
            h_main = meta["generators"]["main"]["sha256"]

            # continuation immediately after capture (draws from the captured state):
            g_ahead = torch.randn(11, generator=g)[0].item()
            pd_ahead = torch.rand(2, generator=pd)[0].item()
            # now diverge BOTH streams far away from the captured states:
            torch.rand(5, generator=pd)
            torch.randn(7, generator=g)
            res_cfg = {"fork_chunk": 2, "mode": "restore", "sidecar": sidecar}
            os.environ["EVOKE_STRICT_FORK_JSON"] = json.dumps(res_cfg)
            rec = sf.maybe_fork_boundary(2, gens)
            assert rec is not None and sf.continuation_marker() == sc.GENERATOR_STATE_RESTORED
            x = torch.randn(11, generator=g)[0].item()     # replayed draw post-restore
            px = torch.rand(2, generator=pd)[0].item()
            y = float(torch.randn(11, generator=torch.Generator().manual_seed(0))[0])
            assert x == g_ahead, "main generator did not resume captured stream"
            assert px == pd_ahead, "patchdrop generator did not resume captured stream"
            assert x != y
            assert h_main and len(h_main) == 64
        finally:
            os.environ.pop("EVOKE_STRICT_FORK_JSON", None)
    sf.reset_for_tests()
    return True


@case("ledger disabled -> zero-effect call sites")
def t_disabled():
    sf = _load_sf()
    sf.reset_for_tests()
    assert os.environ.get("EVOKE_STRICT_FORK_JSON") is None
    assert os.environ.get("EVOKE_STRICT_LEDGER_PATH") is None
    import torch
    g = torch.Generator().manual_seed(5)
    assert sf.gen_state_of(g) is None          # observation short-circuits when off
    assert sf.log_draw("R1", torch.zeros(2)) is None
    assert sf.maybe_fork_boundary(99, {}) is None
    s0 = g.get_state().clone()
    torch.rand(1, generator=g)
    assert sf.gen_state_of(g) is None
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