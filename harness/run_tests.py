#!/usr/bin/env python
"""CausalFork Phase C self-tests for the model-free fork harness.

Run from anywhere:
    python harness/run_tests.py

Prints one PASS/FAIL line per test, a summary, writes an auditable example
twin-run manifest under harness/artifacts/example/ on success, and exits
nonzero if any test fails.
"""

import json
import os
import shutil
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fork_harness as fh  # noqa: E402

SEED = 20260824
FORK_STEP = 3
TOTAL_STEPS = 7
ART_ROOT = os.path.join(HERE, "artifacts", "_selftest")


# ---------------------------------------------------------------- helpers --

def base_cfg():
    return fh.default_config()


def fresh_twin(**kw):
    return fh.twin_run(fh.default_config(), SEED, FORK_STEP, TOTAL_STEPS, **kw)


def make_fork_fixture():
    """Shared prefix + snapshot + factual continuation, from primitives."""
    cfg = base_cfg()
    gen, rec, world = fh.make_prefix(cfg, SEED, FORK_STEP)
    snap = fh.BranchSnapshot.capture(gen, world, rec, cfg, FORK_STEP)
    f_rec = fh.DrawRecorder()
    fh.run_steps(gen, f_rec, cfg, world, range(FORK_STEP, TOTAL_STEPS))
    return cfg, snap, world, f_rec


class TempDir:
    def __init__(self):
        os.makedirs(ART_ROOT, exist_ok=True)
        self.path = os.path.join(ART_ROOT, uuid.uuid4().hex)
        os.makedirs(self.path)

    def file(self, name):
        return os.path.join(self.path, name)

    def close(self):
        shutil.rmtree(self.path, ignore_errors=True)


# ------------------------------------------------------------------ tests --

def test_rng_state_restoration_equality():
    # unit: snapshot state -> identical subsequent draws
    g = fh.ManagedRandom(7)
    g.randn(5, "probe-a")
    st = g.state()
    b = g.randn(5, "probe-b")
    g2 = fh.ManagedRandom(99999)  # different seed; only state matters now
    g2.set_state(st)
    b2 = g2.randn(5, "probe-b")
    assert fh.tensor_hash(b) == fh.tensor_hash(b2), "restored RNG diverged"

    # integration: full continuation from restored fork snapshot reproduces
    # the factual branch's noise stream and output bitwise
    cfg, snap, world, f_rec = make_fork_fixture()
    factual_out = fh.tensor_hash(world["frame"])
    w2 = snap.world_clone()
    r2 = fh.DrawRecorder()
    fh.run_steps(snap.fresh_generator(), r2, cfg, w2,
                 range(FORK_STEP, TOTAL_STEPS))
    assert fh.tensor_hash(w2["frame"]) == factual_out, \
        "continuation from restored state != factual continuation"
    cmp_res = fh.compare_draw_logs(f_rec.log, r2.log)
    assert cmp_res["status"] == "ALIGNED_EQUAL", cmp_res
    assert cmp_res["n_draws"] == TOTAL_STEPS - FORK_STEP


def test_explicit_noise_injection_modes():
    # mode A (coupled): replay-injected known noise == factual draws bitwise
    ra = fresh_twin(mode="coupled")
    assert ra.seed_policy == "strict-coupled"
    assert ra.comparison["status"] == "ALIGNED_EQUAL", ra.comparison
    assert ra.comparison["n_draws"] == TOTAL_STEPS - FORK_STEP
    fm = [r for r in ra.factual_log if r.managed]
    cm = [r for r in ra.cf_log if r.managed]
    for fa, cb in zip(fm, cm):
        assert fa.hash == cb.hash, "per-draw hash mismatch under coupling"
        assert fa.tag == cb.tag
    assert ra.factual_output_hash == ra.cf_output_hash, \
        "bitwise-identical future noise must give bitwise-identical output"

    # mode B (uncoupled): fresh generator state -> every draw differs
    rb = fresh_twin(mode="uncoupled")
    assert rb.seed_policy == "uncontrolled"
    assert rb.comparison["status"] == "NOISE_MISMATCH", rb.comparison
    n_expected = TOTAL_STEPS - FORK_STEP
    assert len(rb.comparison["mismatches"]) == n_expected, rb.comparison
    assert rb.factual_output_hash != rb.cf_output_hash
    # neither mode may silently desync: draw order stayed aligned in both
    assert "DESYNC" not in ra.comparison["status"]
    assert "DESYNC" not in rb.comparison["status"]


def test_branch_isolation_and_divergence():
    cfg, snap, world, _f_rec = make_fork_fixture()

    # mutating a deep clone leaves the snapshot untouched
    fp_before = fh.world_fingerprint(snap.world)
    clone = snap.world_clone()
    assert fh.shared_references([snap.world], [clone]) == []
    fh.mutate_world_probe(clone)
    assert fh.world_fingerprint(snap.world) == fp_before, \
        "clone mutation leaked into original snapshot"
    assert fh.world_fingerprint(clone) != fp_before

    # two continued branches diverge and share no storage
    res = fresh_twin(mode="uncoupled")
    assert res.factual_output_hash != res.cf_output_hash
    assert fh.shared_references([res.factual_world], [res.cf_world]) == [], \
        "branch worlds share mutable objects"
    assert fh.storage_overlaps([res.factual_world], [res.cf_world]) == [], \
        "branch worlds share numpy storage"


def test_full_rerun_reproduces_manifests():
    tmp = TempDir()
    try:
        d1, d2 = tmp.file("run-a"), tmp.file("run-b")
        m1 = fh.save_twins(fresh_twin(mode="coupled"), d1)
        m2 = fh.save_twins(fresh_twin(mode="coupled"), d2)
        s1 = json.dumps(m1, sort_keys=True)
        s2 = json.dumps(m2, sort_keys=True)
        assert s1 == s2, "manifest not reproducible across fresh reruns"
        for a1, a2 in zip(m1["artifacts"], m2["artifacts"]):
            assert a1["path"] == a2["path"]
            assert a1["sha256"] == a2["sha256"], \
                "artifact %s differs between runs" % a1["path"]
    finally:
        tmp.close()


def test_snapshot_serialization_round_trip():
    tmp = TempDir()
    try:
        cfg, snap, world, f_rec = make_fork_fixture()
        factual_out = fh.tensor_hash(world["frame"])

        spath = tmp.file("fork-snapshot.json")
        snap.save(spath)
        snap2 = fh.BranchSnapshot.load(spath)

        # future-noise log saved/reloaded too (mode A through disk)
        lpath = tmp.file("future-drawlog.json")
        with open(lpath, "w", encoding="utf-8") as fo:
            json.dump(fh.log_to_json(f_rec.log), fo)
        with open(lpath, "r", encoding="utf-8") as fi:
            loaded_log = fh.log_from_json(json.load(fi))

        # continuation from reloaded state matches in-memory continuation
        w2 = snap2.world_clone()
        r2 = fh.DrawRecorder()
        fh.run_steps(snap2.fresh_generator(), r2, snap2.cfg, w2,
                     range(FORK_STEP, TOTAL_STEPS))
        assert fh.tensor_hash(w2["frame"]) == factual_out

        # coupled replay driven entirely by disk-loaded artifacts
        w3 = snap2.world_clone()
        r3 = fh.DrawRecorder()
        replay_gen = fh.ReplayingRandom(snap2.rng_state,
                                        [r for r in loaded_log if r.managed])
        fh.run_steps(replay_gen, r3, snap2.cfg, w3,
                     range(FORK_STEP, TOTAL_STEPS))
        assert fh.tensor_hash(w3["frame"]) == factual_out, \
            "disk round-trip broke bitwise continuation"
        assert fh.compare_draw_logs(f_rec.log, r3.log)["status"] == "ALIGNED_EQUAL"
    finally:
        tmp.close()


def test_shallow_copy_alias_detected():
    cfg = base_cfg()
    gen, rec, world = fh.make_prefix(cfg, SEED, FORK_STEP)

    # deliberately buggy fixture: shallow top-level copy
    bad = dict(world)

    conf = fh.shared_references([world], [bad])
    assert conf, "alias detector failed to flag a shallow copy"
    flagged_types = {c["type"] for c in conf}
    assert flagged_types & {"dict", "list", "MiniArray", "ndarray"}, conf

    # behavioral proof of the leak the detector caught
    fp_before = fh.world_fingerprint(world)
    fh.mutate_world_probe(bad)
    assert fh.world_fingerprint(world) != fp_before, \
        "expected shallow-copy mutation to leak into original"

    # storage-level check flags the shared frame buffer when numpy is present
    if fh.BACKEND == "numpy":
        ov = fh.storage_overlaps([world], [bad])
        assert ov, "storage-overlap detector missed shared frame buffer"


def test_draw_order_desync_detected():
    # unit 1: same length, tag divergence at draw #0
    ra, rb = fh.DrawRecorder(), fh.DrawRecorder()
    arr = fh.zeros(4)
    ra.record("managed", "gauss:t4", arr, managed=True)
    rb.record("managed", "gauss:t5", arr, managed=True)  # skipped a chunk
    cmp_res = fh.compare_draw_logs(ra.log, rb.log)
    assert cmp_res["status"] == "DESYNC_DRAW_ORDER", cmp_res
    assert cmp_res["first_index"] == 0

    # unit 2: extra consumed draw -> count mismatch
    rc, rd = fh.DrawRecorder(), fh.DrawRecorder()
    rc.record("managed", "gauss:t4", arr, managed=True)
    rd.record("managed", "rogue:event-chunk", arr, managed=True)
    rd.record("managed", "gauss:t4", arr, managed=True)
    cmp_res = fh.compare_draw_logs(rc.log, rd.log)
    assert cmp_res["status"] == "DESYNC_DRAW_ORDER", cmp_res
    assert fh.comparison_flagged(cmp_res)

    # integration: branch consumes ONE extra random draw after the fork;
    # comparator must FLAG it, never compare misaligned hashes silently
    cfg, snap, world, f_rec = make_fork_fixture()
    factual_out = fh.tensor_hash(world["frame"])
    cworld = snap.world_clone()
    cgen = snap.fresh_generator()
    c_rec = fh.DrawRecorder()
    cgen.randn(cfg["dim"], "rogue:event-chunk-skip", rec=c_rec)  # the bug
    fh.run_steps(cgen, c_rec, cfg, cworld, range(FORK_STEP, TOTAL_STEPS))
    cmp_res = fh.compare_draw_logs(f_rec.log, c_rec.log)
    assert cmp_res["status"] == "DESYNC_DRAW_ORDER", cmp_res
    assert fh.comparison_flagged(cmp_res)
    assert cmp_res.get("detail"), "desync must carry a diagnostic"
    # and the desynced branch's output really did change
    assert fh.tensor_hash(cworld["frame"]) != factual_out

    # replay-based coupling refuses misalignment loudly instead of guessing
    replay_gen = fh.ReplayingRandom(snap.rng_state,
                                    [r for r in f_rec.log if r.managed])
    bad_rec = fh.DrawRecorder()
    raised = False
    try:
        replay_gen.randn(cfg["dim"], "unexpected:first", rec=bad_rec)
    except fh.DesyncError:
        raised = True
    assert raised, "replay must reject out-of-order draws with DesyncError"


def test_unseeded_hazard_caught():
    # hazard draws bypass the managed generator AFTER the fork (prefix stays
    # deterministic); strict-coupled policy must flag both branches even
    # though the managed noise streams remain perfectly aligned. This proves
    # noise-hash equality alone cannot certify coupling when global-RNG
    # bypass exists -- our instrumentation catches it via the ledger.
    res = fresh_twin(mode="coupled", hazard_continuation=True)
    assert res.comparison["status"] == "ALIGNED_EQUAL", res.comparison
    assert res.factual_output_hash != res.cf_output_hash, \
        "unseeded hazard should have perturbed outputs"
    assert len(res.policy_violations) == 2, res.policy_violations
    branches = sorted(v["branch"] for v in res.policy_violations)
    assert branches == ["counterfactual", "factual"]
    assert all(v["unmanaged_draws"] >= 1 for v in res.policy_violations)


# ----------------------------------------------------------------- runner --

TESTS = [
    test_rng_state_restoration_equality,
    test_explicit_noise_injection_modes,
    test_branch_isolation_and_divergence,
    test_full_rerun_reproduces_manifests,
    test_snapshot_serialization_round_trip,
    test_shallow_copy_alias_detected,
    test_draw_order_desync_detected,
    test_unseeded_hazard_caught,
]


def main():
    print("CausalFork Phase C fork-harness self-tests")
    print("backend=%s python=%s harness=%s"
          % (fh.BACKEND, ".".join(map(str, sys.version_info[:3])), fh.__version__))
    failures = []
    for t in TESTS:
        try:
            t()
            print("PASS: %s" % t.__name__)
        except Exception as exc:  # noqa: BLE001 - report and continue
            failures.append(t.__name__)
            print("FAIL: %s -- %s: %s" % (t.__name__, type(exc).__name__, exc))
    print("-" * 60)
    print("%d/%d tests passed" % (len(TESTS) - len(failures), len(TESTS)))
    if failures:
        print("FAILED: %s" % ", ".join(failures))
        sys.exit(1)

    example = os.path.join(HERE, "artifacts", "example")
    shutil.rmtree(example, ignore_errors=True)
    manifest = fh.save_twins(fresh_twin(mode="coupled"), example)
    print("example twin-run written: %s (exp_id=%s)"
          % (os.path.join(example, "manifest.json"), manifest["exp_id"]))
    sys.exit(0)


if __name__ == "__main__":
    main()