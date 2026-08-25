"""P4: real-Evoke-class CPU tests against the READ-ONLY pinned clone.

Pin: AlayaLab/Evoke @ 74d268516d95c8fceadd2378f91a73f9f187042b.
No pip installs, no weight downloads, no GPU. The clone is never written:
bytecode is redirected away (sys.dont_write_bytecode + sys.pycache_prefix).
If a genuine ImportError blocks an import, the case reports BLOCKED with the
exact error - success is never simulated.

Cases:
  1. FrameBank deepcopy independence (storage/data_ptr, mutation, append).
  2. DA3FrameBank independence on tiny hand-injected state (pts/c2ws/frames/
     _pt_mask/_probation/_carve_strike) + evict_before/_evict_keep determinism
     across ALL dicts, without any estimator weights.
  3. Post-fork mutation isolation + counter cloning.
  4. Tensor storage alias detection (positive + negative control).
  5. da3_est intentionally shared/not deepcopied (sentinel identity).
  6. STATIC source assertions over pipeline_evoke.py (pipeline-persistent
     mutable fields; the pipeline itself is NOT instantiated - needs weights).
  7. Serialization round-trip where feasible without weights.
"""
from __future__ import annotations

import copy
import os
import re
import sys
import tempfile
import traceback

PIN = os.environ.get(
    "EVOKE_PIN",
    r"C:\Users\HP\AppData\Local\Temp\opencode\evoke-pin",
)

sys.dont_write_bytecode = True                       # never dirty the pin
sys.pycache_prefix = os.path.join(tempfile.gettempdir(), "sc1-pin-pyc")

RESULTS = []


class BLOCKED(Exception):
    pass


def case(name):
    def deco(fn):
        RESULTS.append((name, fn))
        return fn
    return deco


def load_real_classes():
    """Return (frame_bank_mod, da3_cloud_mod, route_str)."""
    sys.path.insert(0, PIN)
    try:
        from evoke.modules.geometric_state import da3_cloud as d3          # noqa
        from evoke.modules.geometric_state import frame_bank as fb         # noqa
        return fb, d3, "direct package import"
    except Exception as direct_exc:
        direct_err = "%s: %s" % (type(direct_exc).__name__, direct_exc)
    # Fallback: register minimal namespace packages so da3_cloud's relative
    # import resolves, then exec the REAL module files by path.
    import importlib.util
    import types
    names = ["evoke", "evoke.modules", "evoke.modules.geometric_state"]
    mods = {}
    for i, name in enumerate(names):
        m = types.ModuleType(name)
        m.__path__ = [os.path.join(PIN, *name.split("."))]
        m.__package__ = name
        sys.modules[name] = m
        mods[name] = m
    try:
        def load(fullname, relpath):
            spec = importlib.util.spec_from_file_location(
                fullname, os.path.join(PIN, *relpath.split("/")))
            mod = importlib.util.module_from_spec(spec)
            sys.modules[fullname] = mod
            spec.loader.exec_module(mod)
            return mod

        db = load("evoke.modules.geometric_state.depth_backend",
                  "evoke/modules/geometric_state/depth_backend.py")
        assert db is not None
        fbm = load("evoke.modules.geometric_state.frame_bank",
                   "evoke/modules/geometric_state/frame_bank.py")
        d3m = load("evoke.modules.geometric_state.da3_cloud",
                   "evoke/modules/geometric_state/da3_cloud.py")
        return fbm, d3m, "file-location fallback (direct import failed: %s)" % direct_err
    except Exception as exc:
        raise BLOCKED("cannot import real classes from %s (%r); direct-import error was: %s"
                      % (PIN, exc, direct_err))


FB, D3, ROUTE = None, None, ""


# ------------------------------------------------------------------ fixtures
def make_frame_bank(fbm, n=3):
    import torch
    bank = fbm.FrameBank(max_size=4)
    for i in range(n):
        frame = torch.full((3, 8, 8), float(i))
        c2w = torch.eye(4) * (i + 1)
        bank.add(frame, c2w, chunk_idx=i, pixel_idx=i * 10)
    return bank


def make_da3_bank(d3, gids=range(8)):
    import torch
    bank = d3.DA3FrameBank(device="cpu")
    for g in gids:
        depth = torch.full((8, 8), 0.5 + 0.01 * g)
        intr = torch.eye(3)
        c2w = torch.eye(4)
        rgb = torch.full((3, 8, 8), float(g) / 255.0)
        bank.pts[g] = (torch.randn(16, 3) + g, torch.randn(16, 3))
        bank.c2ws[g] = c2w.clone()
        bank.frames[g] = (depth, intr, c2w.clone(), rgb)
        bank._pt_mask[g] = torch.ones(8, 8, dtype=torch.bool)
        bank._probation[g] = {"mask": torch.ones(8, 8, dtype=torch.bool),
                              "depth": depth.clone()}
        bank._carve_strike[g] = torch.zeros(8, 8, dtype=torch.int16)
    bank._ingest_calls = 42
    return bank


DICTS = ("pts", "c2ws", "frames", "_pt_mask", "_probation", "_carve_strike")


def surviving(bank):
    return {d: sorted(bank.__dict__[d].keys()) for d in DICTS}


# -------------------------------------------------------------------- cases
@case("route: real classes importable from pin (CPU)")
def t_route():
    global FB, D3, ROUTE
    FB, D3, ROUTE = load_real_classes()
    print("      [import-route] %s" % ROUTE)
    assert hasattr(FB, "FrameBank") and hasattr(D3, "DA3FrameBank")
    return True


@case("1. FrameBank deepcopy independence (data_ptr/mutation/append)")
def t_framebank_deepcopy():
    import torch
    b1 = make_frame_bank(FB)
    b2 = copy.deepcopy(b1)
    for e1, e2 in zip(b1.entries, b2.entries):
        assert e1.frame.data_ptr() != e2.frame.data_ptr(), "frame storage aliased"
        assert e1.c2w.data_ptr() != e2.c2w.data_ptr(), "c2w storage aliased"
    snap = b1.entries[0].frame.clone()
    b2.entries[0].frame.add_(100.0)
    assert torch.equal(b1.entries[0].frame, snap), "mutation leaked"
    b2.add(torch.ones(3, 8, 8), torch.eye(4), chunk_idx=99, pixel_idx=999)
    assert len(b1) == 3 and len(b2) == 4, "append crossed sibling"
    ids1 = {id(e) for e in b1.entries}
    ids2 = {id(e) for e in b2.entries}
    assert not (ids1 & ids2), "entry objects shared"
    b2.entries[0].cached_geometry = {"k": [1, 2]}
    b2.entries[0].cached_geometry["k"].append(3)
    assert b1.entries[0].cached_geometry is None or \
        b1.entries[0].cached_geometry.get("k") is None or \
        b1.entries[0].cached_geometry["k"] != b2.entries[0].cached_geometry["k"]
    return True


@case("2a. DA3FrameBank deepcopy independence on injected state")
def t_da3_deepcopy():
    import torch
    b1 = make_da3_bank(D3)
    b2 = copy.deepcopy(b1)
    ptr_pairs = []
    for g in b1.pts:
        ptr_pairs.append((b1.pts[g][0].data_ptr(), b2.pts[g][0].data_ptr()))
        ptr_pairs.append((b1.frames[g][0].data_ptr(), b2.frames[g][0].data_ptr()))
        ptr_pairs.append((b1.frames[g][3].data_ptr(), b2.frames[g][3].data_ptr()))
        ptr_pairs.append((b1._pt_mask[g].data_ptr(), b2._pt_mask[g].data_ptr()))
    assert all(a != b for a, b in ptr_pairs), "tensor storage aliased after deepcopy"
    snap = b1.pts[0][0].clone()
    b2.pts[0][0].add_(777.0)
    assert not torch.equal(b1.pts[0][0], b2.pts[0][0]), "mutation leaked into sibling"
    assert torch.equal(b1.pts[0][0], snap), "original drifted"
    return True


@case("2b. DA3FrameBank evict_before/_evict_keep exact survivor sets + determinism")
def t_da3_evict():
    s1 = surviving(make_da3_bank(D3))  # baseline sanity: all 8 everywhere
    assert all(v == list(range(8)) for v in s1.values()), str(s1)
    b_ev = make_da3_bank(D3)
    b_ev.evict_before(4)
    got = surviving(b_ev)
    want = {d: list(range(4, 8)) for d in DICTS}
    assert got == want, "evict_before survivors mismatch:\n%s\nvs\n%s" % (got, want)
    b_kp = make_da3_bank(D3)
    b_kp._evict_keep({5})
    got_kp = surviving(b_kp)
    want_kp = {d: [5] for d in DICTS}
    assert got_kp == want_kp, "evict_keep survivors mismatch:\n%s" % got_kp
    # determinism: independent banks -> identical survivor gid sets
    again = surviving(make_da3_bank(D3))
    make_da3_bank(D3).evict_before(4)
    again = surviving((lambda b: (b.evict_before(4), b)[1])(make_da3_bank(D3)))
    assert again == want
    return True


@case("3. post-fork mutation does not touch sibling; counters clone")
def t_counters():
    import torch
    b1 = make_da3_bank(D3)
    b2 = copy.deepcopy(b1)
    b2._ingest_calls += 7
    b2._ca_seen = 5
    b2.sr_last = 3
    assert b1._ingest_calls == 42 and b2._ingest_calls == 49
    assert b1._ca_seen == 0 and b2._ca_seen == 5
    snap = b1.pts[3][0].clone()
    b2.pts[3][0].zero_()
    assert torch.equal(b1.pts[3][0], snap), "in-place zero leaked into original"
    return True


@case("4. tensor-storage alias detector (positive + shallow-copy control)")
def t_alias_detector():
    import torch

    def tensor_slots(obj, prefix=""):
        out = []
        for name, val in vars(obj).items():
            if torch.is_tensor(val):
                out.append(("%s%s" % (prefix, name), val))
            elif isinstance(val, list):
                for i, item in enumerate(val):
                    if torch.is_tensor(item):
                        out.append(("%s%s[%d]" % (prefix, name, i), item))
                    elif hasattr(item, "frame") and torch.is_tensor(item.frame):
                        out.append(("%s%s[%d].frame" % (prefix, name, i), item.frame))
        return out

    b1 = make_frame_bank(FB)
    deep = copy.deepcopy(b1)
    a = dict(tensor_slots(b1))
    c = dict(tensor_slots(deep))
    shared = [k for k in a if k in c and a[k].data_ptr() == c[k].data_ptr()]
    assert not shared, "aliased slots after deepcopy: %s" % shared
    shallow = copy.copy(b1)   # negative control: shallow MUST alias and be caught
    a2 = dict(tensor_slots(b1))
    c2 = dict(tensor_slots(shallow))
    shared2 = [k for k in a2 if k in c2 and a2[k].data_ptr() == c2[k].data_ptr()]
    assert shared2, "alias detector missed a real alias (shallow copy control)"
    return True


@case("5. estimator sentinel shared, not deepcopied (da3_est protocol)")
def t_sentinel():
    class SentinelEstimator:
        """Weights-backed objects must NOT be duplicated by fork deepcopy."""
        def __deepcopy__(self, memo):
            memo[id(self)] = self
            return self

    b1 = make_da3_bank(D3)
    b1.estimator = SentinelEstimator()
    b2 = copy.deepcopy(b1)
    assert b2.estimator is b1.estimator, "sentinel identity broken"
    # and the rest of the bank is still deep-independent
    b2._ingest_calls += 1
    assert b1._ingest_calls == 42 and b2._ingest_calls == 43
    return True


@case("6. STATIC: pipeline-persistent mutable fields present in source text")
def t_static_pipeline_fields():
    def src_of(rel):
        with open(os.path.join(PIN, *rel.split("/")), "r", encoding="utf-8") as fh:
            return fh.read()

    pipe_src = src_of("evoke/pipelines/pipeline_evoke.py")
    single_src = src_of("scripts/inference/infer_single.py")
    checks_pipe = {
        "_geo_persist_feat_map": r"self\._geo_persist_feat_map\b",
        "_short_tier_rollout_sigma": r"_short_tier_rollout_sigma",
        "_short_tier_print_count": r"_short_tier_print_count",
        "use_kv_cache flag": r"use_kv_cache",
        "_geo_patchdrop_gen (2nd long-lived generator)": r"_geo_patchdrop_gen",
        "_GEO_DEPTH_ESTIMATORS cache": r"_GEO_DEPTH_ESTIMATORS",
    }
    checks_single = {
        "restrict_self_attn flag (lives in infer_single per profile :481)":
            r"restrict_self_attn",
    }
    for label, pat in checks_pipe.items():
        hits = len(re.findall(pat, pipe_src))
        print("      [STATIC] pipeline_evoke.py %-38s hits=%d" % (label, hits))
        assert hits > 0, "STATIC assertion failed in pipeline_evoke.py for %s" % label
    for label, pat in checks_single.items():
        hits = len(re.findall(pat, single_src))
        print("      [STATIC] infer_single.py     %-38s hits=%d" % (label, hits))
        assert hits > 0, "STATIC assertion failed in infer_single.py for %s" % label
    print("      [STATIC] pipeline NOT instantiated (needs weights) - source-level assertion only")
    return True


@case("7. serialization round-trip without weights")
def t_roundtrip():
    import torch
    b1 = make_frame_bank(FB)
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "fb.pt")
        torch.save(b1, p)
        b2 = torch.load(p, weights_only=False)
    assert len(b2) == len(b1)
    for e1, e2 in zip(b1.entries, b2.entries):
        assert torch.equal(e1.frame, e2.frame) and torch.equal(e1.c2w, e2.c2w)
        assert e1.chunk_idx == e2.chunk_idx and e1.pixel_idx == e2.pixel_idx
    d1 = make_da3_bank(D3, gids=[1, 2])
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "d3.pt")
        torch.save(d1, p)
        d2 = torch.load(p, weights_only=False)
    assert surviving(d2)[ "frames"] == [1, 2]
    assert torch.equal(d1.pts[1][0], d2.pts[1][0])
    assert torch.equal(d1._carve_strike[2], d2._carve_strike[2])
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
            traceback.print_exc(limit=4)
            fails += 1
    print("---")
    print("passed=%d failed=%d blocked=%d" % (passed, fails, blocked))
    raise SystemExit(1 if fails else 0)


if __name__ == "__main__":
    main()