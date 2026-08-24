"""
CausalFork Phase C -- model-free fork harness (backend-agnostic).

Purpose (EXPERIMENTS.md GF0 rule 3): prove that OUR infrastructure can hold
future noise equal across restored branches before any backend claim. This is
the adapter contract that the EVOKE backend must satisfy later:

  1. one factual prefix from a toy stochastic chain;
  2. snapshot = RNG state + world-state dict + prefix draw log (deepcopied);
  3. exact RNG-state clone/restore;
  4. factual continuation;
  5. restore fork snapshot exactly;
  6. counterfactual continuation under:
       mode "coupled"   -> policy "strict-coupled": restored RNG state AND
                           explicit replay-injection of the factual branch's
                           recorded future noise draws (bitwise);
       mode "uncoupled" -> policy "uncontrolled": fresh generator state;
  7. coupling asserted on logged NOISE hashes in draw order (never pixels,
     never seeds alone);
  8. draw-order divergence is DETECTABLE (DESYNC_DRAW_ORDER), never silently
     misaligned;
  9. aliasing / cross-branch leakage detection (id-walk, numpy storage
     overlap, mutation probe);
 10. "unseeded hazard" simulation: draws bypassing the managed generator are
     ledgered unmanaged and flagged as policy violations under coupling;
 11. auditable JSON branch manifest (branch ids, parent, fork point, seed
     policy in {strict-coupled, prefix-shared-seed-matched, uncontrolled},
     per-draw noise hashes in draw order, config-hash proof that configs are
     byte-identical except the prompt schedule, artifact paths+sha256).

Determinism contract: given identical (config, seed, fork_step, total_steps,
mode, hazard flag) the entire twin-run -- including manifest bytes -- is
reproducible. Manifests contain no timestamps and no absolute paths; artifact
paths are relative to the artifact directory chosen at save time.

Randomness backend: stdlib random.Random (Mersenne Twister) stands in for the
upstream torch.Generator; small float64 vectors stand in for torch tensors.
numpy is used when importable, otherwise a tiny pure-Python MiniArray
fallback keeps this module dependency-free. No network, no GPU.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import math
import os
import random
import struct
import sys
from collections import deque

__version__ = "0.1.0"

SCHEMA_MANIFEST = "causalfork/fork-manifest@1"
SCHEMA_SNAPSHOT = "causalfork/branch-snapshot@1"
PROMPT_KEY = "prompt_schedule"
SEED_POLICIES = ("strict-coupled", "prefix-shared-seed-matched", "uncontrolled")
MODE_POLICY = {"coupled": "strict-coupled", "uncoupled": "uncontrolled"}

# --------------------------------------------------------------------------
# tiny tensor layer (numpy if available, else pure Python)
# --------------------------------------------------------------------------

try:
    import numpy as _np
    BACKEND = "numpy"
except Exception:  # pragma: no cover - exercised only without numpy
    _np = None
    BACKEND = "python"


class MiniArray:
    """Minimal fixed-length float64 vector standing in for torch.Tensor."""

    __slots__ = ("d",)

    def __init__(self, data):
        self.d = [float(x) for x in data]

    def __len__(self):
        return len(self.d)

    def __repr__(self):
        return "MiniArray(%r)" % (self.d,)


def zeros(n):
    if _np is None:
        return MiniArray([0.0] * n)
    return _np.zeros(n, dtype=_np.float64)


def from_list(xs):
    if _np is None:
        return MiniArray(xs)
    return _np.asarray(list(xs), dtype=_np.float64)


def a_add(a, b):
    if _np is None:
        return MiniArray([x + y for x, y in zip(a.d, b.d)])
    return a + b


def a_scale(a, s):
    if _np is None:
        return MiniArray([x * s for x in a.d])
    return a * s


def a_tanh(a):
    if _np is None:
        return MiniArray([math.tanh(x) for x in a.d])
    return _np.tanh(a)


def a_copy(a):
    if _np is None:
        return MiniArray(list(a.d))
    return _np.array(a, dtype=_np.float64, copy=True)


def is_array(o):
    return isinstance(o, MiniArray) or (_np is not None and isinstance(o, _np.ndarray))


def a_bytes(a):
    """Canonical little-endian float64 bytes (portable, hash-stable)."""
    if _np is not None and isinstance(a, _np.ndarray):
        return a.astype("<f8", copy=False).tobytes()
    return struct.pack("<%dd" % len(a), *a.d)


def tensor_hash(a):
    h = hashlib.sha256()
    h.update(b"cfarr<f8:%d>" % len(a))
    h.update(a_bytes(a))
    return "sha256:" + h.hexdigest()


# --------------------------------------------------------------------------
# deterministic JSON encode/decode (arrays -> base64 float64)
# --------------------------------------------------------------------------

def arr_to_json(a):
    return {"__arr__": {"n": len(a),
                        "b64": base64.b64encode(a_bytes(a)).decode("ascii")}}


def arr_from_json(o):
    meta = o["__arr__"]
    raw = base64.b64decode(meta["b64"])
    vals = struct.unpack("<%dd" % meta["n"], raw)
    return from_list(vals)


_PRIMITIVES = (str, int, float, bool, type(None))
_IMMUTABLE_TYPES = _PRIMITIVES + (tuple,)


def enc_json(o):
    if is_array(o):
        return arr_to_json(o)
    if isinstance(o, dict):
        return {k: enc_json(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [enc_json(v) for v in o]
    if isinstance(o, _PRIMITIVES):
        return o
    raise TypeError("cannot JSON-encode %r" % (type(o),))


def dec_json(o):
    if isinstance(o, dict):
        if "__arr__" in o:
            return arr_from_json(o)
        return {k: dec_json(v) for k, v in o.items()}
    if isinstance(o, list):
        return [dec_json(v) for v in o]
    return o


def canon_json(o):
    return json.dumps(enc_json(o), sort_keys=True, separators=(",", ":"))


def sha256_text(s):
    return "sha256:" + hashlib.sha256(s.encode("utf-8")).hexdigest()


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


# --------------------------------------------------------------------------
# errors
# --------------------------------------------------------------------------

class HarnessError(Exception):
    pass


class DesyncError(HarnessError):
    """Draw-order divergence detected while replaying coupled noise."""


class AliasingError(HarnessError):
    """Branch state shares mutable storage with its source."""


class ConfigDivergenceError(HarnessError):
    """Branch configs differ beyond the prompt schedule (forbidden)."""


# --------------------------------------------------------------------------
# managed randomness + draw ledger
# --------------------------------------------------------------------------

class DrawRec:
    __slots__ = ("i", "kind", "tag", "managed", "n", "values", "hash")

    def __init__(self, i, kind, tag, managed, n, values, hash_):
        self.i = i
        self.kind = kind
        self.tag = tag
        self.managed = managed
        self.n = n
        self.values = values      # array (always present in this harness)
        self.hash = hash_


class DrawRecorder:
    """Ledger of every random draw, in draw order, managed or not."""

    def __init__(self):
        self.log = []

    def record(self, kind, tag, values, managed):
        rec = DrawRec(len(self.log), kind, tag, bool(managed),
                      len(values), values, tensor_hash(values))
        self.log.append(rec)
        return rec

    @property
    def managed(self):
        return [r for r in self.log if r.managed]

    @property
    def unmanaged_count(self):
        return sum(1 for r in self.log if not r.managed)


_system_random = random.SystemRandom()


def unseeded_gauss(n, tag, rec):
    """Simulate randomness BYPASSING the seeded generator (global-RNG hazard).

    SystemRandom cannot be seeded/restored -- exactly the upstream failure
    mode of global-RNG draws. It is still ledgered (managed=False) so our
    instrumentation proves such draws do not go unnoticed.
    """
    vals = [_system_random.gauss(0.0, 1.0) for _ in range(n)]
    arr = from_list(vals)
    rec.record("system-gauss", tag, arr, managed=False)
    return arr


def coerce_rng_state(st):
    """Accept an in-memory getstate() tuple or its JSON form."""
    if isinstance(st, dict):
        g = st["gauss_next"]
        return (int(st["version"]), tuple(int(x) for x in st["keys"]),
                tuple(float(x) for x in g) if g else None)
    ver, ints, gauss = st
    ints = tuple(int(x) for x in ints)
    if isinstance(gauss, list):
        gauss = tuple(gauss)
    return (int(ver), ints, gauss)


class ManagedRandom:
    """Seeded generator; every legitimate draw goes through here."""

    kind = "managed"

    def __init__(self, seed):
        self.seed = seed
        self._rng = random.Random(seed)

    def state(self):
        return copy.deepcopy(self._rng.getstate())

    def set_state(self, st):
        self._rng.setstate(coerce_rng_state(st))

    def randn(self, n, tag, rec=None):
        vals = [self._rng.gauss(0.0, 1.0) for _ in range(n)]
        arr = from_list(vals)
        if rec is not None:
            rec.record(self.kind, tag, arr, managed=True)
        return arr


class ReplayingRandom:
    """Mode-A noise source: restores RNG state AND replays recorded future
    draws bitwise. Any request not matching the recorded sequence in
    order/tag/shape raises DesyncError -- draw-order divergence is loud."""

    kind = "replay"

    def __init__(self, base_state, replay_records):
        self._inner = ManagedRandom(0)          # seed irrelevant; state below
        self._inner.set_state(base_state)
        self._queue = deque((r.tag, r.n, a_copy(r.values)) for r in replay_records)
        self.consumed = 0

    def state(self):
        return self._inner.state()

    def set_state(self, st):
        self._inner.set_state(st)

    def randn(self, n, tag, rec=None):
        if not self._queue:
            raise DesyncError(
                "draw-order desync: branch requested extra draw %r after the "
                "recorded future-noise stream was exhausted" % (tag,))
        rtag, rn, rvals = self._queue.popleft()
        self.consumed += 1
        if rtag != tag:
            raise DesyncError(
                "draw-order desync at replay draw #%d: expected tag %r, got %r"
                % (self.consumed, rtag, tag))
        if rn != n:
            raise DesyncError(
                "draw-shape desync at replay draw #%d (%r): expected n=%d, got n=%d"
                % (self.consumed, rtag, rn, n))
        if rec is not None:
            rec.record(self.kind, tag, rvals, managed=True)
        return a_copy(rvals)


# --------------------------------------------------------------------------
# toy stochastic pipeline (stands in for the world model)
# --------------------------------------------------------------------------

def default_config():
    return {
        "dim": 12,
        "shift": 0.03,
        "gain": 1.02,
        "squash": True,
        "meta_version": "phaseC-toy-v1",
        PROMPT_KEY: [{"step": 0, "text": "calm morning over the old bridge"}],
    }


def cfg_without_prompt(cfg):
    return {k: v for k, v in cfg.items() if k != PROMPT_KEY}


def cfg_common_hash(cfg):
    """Hash of everything EXCEPT the prompt schedule."""
    return sha256_text(canon_json(cfg_without_prompt(cfg)))


def cfg_prompt_hash(cfg):
    return sha256_text(canon_json(cfg.get(PROMPT_KEY)))


def initial_world(cfg):
    return {
        "t": 0,
        "frame": zeros(cfg["dim"]),
        "trace": [],                       # per-step frame hashes (prefix artifacts)
        "meta": {"camera": [0.0, 0.0, 0.0],
                 "flags": {"squash": bool(cfg.get("squash")), "hazard": False}},
    }


def run_steps(gen, rec, cfg, world, steps, hazard=False):
    """Advance the toy world. Each step consumes exactly one managed noise
    draw (tagged by absolute step) plus, in hazard mode, periodic unseeded
    draws that bypass the generator."""
    for _s in steps:
        world["t"] += 1
        t = world["t"]
        frame = world["frame"]
        d = len(frame)
        frame = a_add(frame, from_list([cfg["shift"]] * d))
        frame = a_scale(frame, cfg["gain"])
        noise = gen.randn(d, tag="gauss:t%d" % t, rec=rec)
        frame = a_add(frame, noise)
        if cfg.get("squash"):
            frame = a_tanh(frame)
        if hazard and t % 2 == 0:
            hz = unseeded_gauss(d, "hazard:t%d" % t, rec)
            frame = a_add(frame, hz)
        world["frame"] = frame
        world["trace"].append(tensor_hash(frame))
    world["meta"]["flags"]["hazard"] = bool(hazard)
    return world


# --------------------------------------------------------------------------
# aliasing / leakage detection
# --------------------------------------------------------------------------

def _trackable(node):
    return not isinstance(node, _IMMUTABLE_TYPES)


def iter_nodes(obj, path="$"):
    yield path, obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from iter_nodes(v, "%s.%s" % (path, k))
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            yield from iter_nodes(v, "%s[%d]" % (path, i))
    elif isinstance(obj, DrawRec):
        yield from iter_nodes(obj.values, path + ".values")


def _id_map(roots):
    m = {}
    for ri, root in enumerate(roots):
        for p, node in iter_nodes(root):
            if _trackable(node):
                entry = m.setdefault(id(node), (type(node).__name__, []))
                entry[1].append("root%d:%s" % (ri, p))
    return m


def shared_references(roots_a, roots_b):
    """Object-identity conflicts between two groups of state trees."""
    ma, mb = _id_map(roots_a), _id_map(roots_b)
    return [{"type": ma[k][0], "path": ma[k][1][0], "shared_with": mb[k][1]}
            for k in ma if k in mb]


def storage_overlaps(roots_a, roots_b):
    """numpy buffer overlap check ('storage identity where applicable')."""
    if _np is None:
        return []

    def spans(roots):
        out = []
        for ri, root in enumerate(roots):
            for p, node in iter_nodes(root):
                if isinstance(node, _np.ndarray) and node.size:
                    ptr = node.__array_interface__["data"][0]
                    out.append((ptr, ptr + node.nbytes, "root%d:%s" % (ri, p)))
        return out

    sa, sb = spans(roots_a), spans(roots_b)
    conf = []
    for pa, pb, na in sa:
        for qa, qb, nb in sb:
            if pa < qb and qa < pb:
                conf.append({"a": na, "b": nb})
    return conf


def bump_first(arr):
    """In-place first-element mutation, backend-neutral."""
    if _np is not None and isinstance(arr, _np.ndarray):
        arr[0] = arr[0] + 731.5
    else:
        arr.d[0] = arr.d[0] + 731.5


def mutate_world_probe(world):
    """Aggressive deep mutation used by isolation probes/tests."""
    world["meta"]["camera"][0] += 913.25
    world["trace"].append("PROBE-MUTATION")
    world["meta"]["probe_key"] = "MUTATED"
    bump_first(world["frame"])
    return world


def world_fingerprint(world):
    return sha256_text(canon_json(world))


# --------------------------------------------------------------------------
# branch snapshot
# --------------------------------------------------------------------------

def rec_to_json(rec, include_values=True):
    o = {"i": rec.i, "kind": rec.kind, "tag": rec.tag,
         "managed": rec.managed, "n": rec.n, "hash": rec.hash}
    if include_values:
        o["values"] = arr_to_json(rec.values)
    return o


def rec_from_json(o, verify=True):
    vals = dec_json(o["values"]) if "values" in o else None
    rec = DrawRec(int(o["i"]), o["kind"], o["tag"], bool(o["managed"]),
                  int(o["n"]), vals, o["hash"])
    if verify and vals is not None and tensor_hash(vals) != rec.hash:
        raise HarnessError("draw record %r failed hash verification on load" % (rec.tag,))
    return rec


def rng_state_to_json(st):
    ver, ints, gauss = coerce_rng_state(st)
    return {"version": ver, "keys": list(ints),
            "gauss_next": list(gauss) if gauss else None}


class BranchSnapshot:
    """Everything needed to resume a branch at the fork point: RNG state,
    deep-copied world state, config copy, ordered prefix draw log."""

    def __init__(self, label, fork_step, rng_state, world, cfg, draw_log,
                 prefix_frame_hash):
        self.label = label
        self.fork_step = int(fork_step)
        self.rng_state = coerce_rng_state(copy.deepcopy(rng_state))
        self.world = copy.deepcopy(world)          # NO aliasing with live state
        self.cfg = copy.deepcopy(cfg)
        self.draw_log = copy.deepcopy(draw_log)
        self.prefix_frame_hash = prefix_frame_hash

    # ---- construction ----
    @classmethod
    def capture(cls, gen, world, recorder, cfg, fork_step, label="fork"):
        snap = cls(label, fork_step, gen.state(), world, cfg,
                   recorder.log, tensor_hash(world["frame"]))
        conf = shared_references([world, cfg, recorder.log],
                                 [snap.world, snap.cfg, snap.draw_log])
        if conf:
            raise AliasingError("snapshot aliases live state: %r" % (conf,))
        return snap

    # ---- cloning ----
    def world_clone(self):
        clone = copy.deepcopy(self.world)
        conf = shared_references([self.world], [clone])
        if conf:
            raise AliasingError("cloned branch state aliases snapshot: %r" % (conf,))
        return clone

    def fresh_generator(self):
        g = ManagedRandom(0)                       # seed overridden by state
        g.set_state(self.rng_state)
        return g

    # ---- persistence ----
    def to_json(self):
        return {
            "schema": SCHEMA_SNAPSHOT,
            "harness_version": __version__,
            "label": self.label,
            "fork_step": self.fork_step,
            "prefix_frame_hash": self.prefix_frame_hash,
            "rng_state": rng_state_to_json(self.rng_state),
            "world": enc_json(self.world),
            "config": enc_json(self.cfg),
            "draw_log": [rec_to_json(r) for r in self.draw_log],
        }

    @classmethod
    def from_json(cls, obj):
        if obj.get("schema") != SCHEMA_SNAPSHOT:
            raise HarnessError("unexpected snapshot schema %r" % (obj.get("schema"),))
        return cls(obj["label"], obj["fork_step"],
                   coerce_rng_state(obj["rng_state"]),
                   dec_json(obj["world"]), dec_json(obj["config"]),
                   [rec_from_json(r) for r in obj["draw_log"]],
                   obj["prefix_frame_hash"])

    def save(self, path):
        d = os.path.dirname(os.path.abspath(path))
        if d:
            os.makedirs(d, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_json(), f, sort_keys=True, indent=2)
        return path

    @classmethod
    def load(cls, path):
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_json(json.load(f))


# --------------------------------------------------------------------------
# draw-log comparison (noise-hash coupling assertion)
# --------------------------------------------------------------------------

def compare_draw_logs(log_a, log_b):
    """Compare managed noise streams IN DRAW ORDER.

    Statuses:
      ALIGNED_EQUAL      -- same length, same tags, same per-draw hashes
      NOISE_MISMATCH     -- aligned but some hashes differ (uncoupled noise)
      DESYNC_DRAW_ORDER  -- different lengths or tag divergence: the streams
                            misaligned; pairwise hash comparison would be
                            MEANINGLESS and is reported as such, not silent.
    Unmanaged entries are excluded from alignment but remain visible in logs.
    """
    a = [r for r in log_a if r.managed]
    b = [r for r in log_b if r.managed]
    if len(a) != len(b):
        return {"status": "DESYNC_DRAW_ORDER",
                "detail": "different managed draw counts: %d vs %d"
                          % (len(a), len(b)),
                "first_index": min(len(a), len(b))}
    mismatches = []
    for i, (ra, rb) in enumerate(zip(a, b)):
        if ra.tag != rb.tag:
            return {"status": "DESYNC_DRAW_ORDER",
                    "detail": "tag divergence at draw #%d: %r != %r"
                              % (i, ra.tag, rb.tag),
                    "first_index": i}
        if ra.hash != rb.hash:
            mismatches.append({"index": i, "tag": ra.tag,
                               "a": ra.hash, "b": rb.hash})
    if mismatches:
        return {"status": "NOISE_MISMATCH", "first_mismatch": mismatches[0],
                "mismatches": mismatches}
    return {"status": "ALIGNED_EQUAL", "n_draws": len(a)}


def comparison_flagged(cmp_result):
    return cmp_result["status"] != "ALIGNED_EQUAL"


# --------------------------------------------------------------------------
# twin-run orchestration
# --------------------------------------------------------------------------

class TwinRunResult:
    def __init__(self, **kw):
        self.__dict__.update(kw)


def make_prefix(cfg, seed, fork_step):
    gen = ManagedRandom(seed)
    rec = DrawRecorder()
    world = initial_world(cfg)
    run_steps(gen, rec, cfg, world, range(fork_step), hazard=False)
    return gen, rec, world


def derive_counterfactual_config(cfg):
    cf = copy.deepcopy(cfg)
    cf[PROMPT_KEY] = [dict(p, text="[INTERVENTION] " + str(p.get("text", "")))
                      for p in (cfg.get(PROMPT_KEY) or [])]
    if canon_json(cf[PROMPT_KEY]) == canon_json(cfg.get(PROMPT_KEY)):
        raise ConfigDivergenceError("intervention produced an identical prompt schedule")
    if cfg_common_hash(cf) != cfg_common_hash(cfg):
        raise ConfigDivergenceError("non-prompt config drift between branches")
    return cf


def twin_run(cfg, seed, fork_step, total_steps, mode,
             hazard_continuation=False, exp_label="phaseC"):
    """Full twin-run: shared prefix -> snapshot -> both continuations ->
    noise-coupling comparison. Deterministic given fixed inputs (except the
    explicit unseeded-hazard mode, nondeterministic BY DESIGN)."""
    if not (0 < fork_step < total_steps):
        raise ValueError("need 0 < fork_step < total_steps")
    if mode not in MODE_POLICY:
        raise ValueError("mode must be one of %s" % (sorted(MODE_POLICY),))

    cf_cfg = derive_counterfactual_config(cfg)

    # 1-2. factual prefix + fork snapshot
    gen, pre_rec, world = make_prefix(cfg, seed, fork_step)
    prefix_hash = tensor_hash(world["frame"])
    snap = BranchSnapshot.capture(gen, world, pre_rec, cfg, fork_step)

    # 4. factual continuation
    f_rec = DrawRecorder()
    run_steps(gen, f_rec, cfg, world, range(fork_step, total_steps),
              hazard=hazard_continuation)
    factual_out = tensor_hash(world["frame"])

    # 5-6. counterfactual continuation from the restored snapshot
    cworld = snap.world_clone()
    if mode == "coupled":
        cgen = ReplayingRandom(snap.rng_state,
                               [r for r in f_rec.log if r.managed])
    else:  # uncoupled: fresh generator state
        cgen = ManagedRandom((seed * 1000003 + 12345) % (2 ** 31 - 1))
    c_rec = DrawRecorder()
    run_steps(cgen, c_rec, cf_cfg, cworld, range(fork_step, total_steps),
              hazard=hazard_continuation)
    cf_out = tensor_hash(cworld["frame"])

    # 7-8. assert coupling on logged noise hashes, in draw order
    comparison = compare_draw_logs(f_rec.log, c_rec.log)

    # 10. unseeded-hazard ledger -> strict-coupling violations
    violations = []
    for name, r in (("factual", f_rec), ("counterfactual", c_rec)):
        if r.unmanaged_count:
            violations.append({
                "branch": name,
                "unmanaged_draws": r.unmanaged_count,
                "detail": "randomness bypassed the managed generator; "
                          "strict-coupled policy violated",
            })

    exp_id = "%s-%s-s%d-k%d-n%d-%s%s" % (
        exp_label, cfg_common_hash(cfg)[7:17], seed, fork_step, total_steps,
        mode, "-hazard" if hazard_continuation else "")

    return TwinRunResult(
        exp_id=exp_id, seed=seed, mode=mode,
        seed_policy=MODE_POLICY[mode],
        fork_step=fork_step, total_steps=total_steps,
        hazard=hazard_continuation,
        cfg=cfg, cf_cfg=cf_cfg,
        prefix_hash=prefix_hash,
        snapshot=snap,
        factual_world=world, factual_log=f_rec.log,
        factual_output_hash=factual_out,
        cf_world=cworld, cf_log=c_rec.log,
        cf_output_hash=cf_out,
        comparison=comparison,
        policy_violations=violations,
    )


# --------------------------------------------------------------------------
# manifest build / save
# --------------------------------------------------------------------------

def _branch_manifest(branch_id, parent, res, log, output_hash, prompt_hash):
    draws = [{"i": r.i, "kind": r.kind, "tag": r.tag,
              "managed": r.managed, "hash": r.hash} for r in log]
    return {
        "branch_id": branch_id,
        "parent": parent,
        "fork_point": (None if parent is None else
                       {"parent_branch": parent, "step": res.fork_step,
                        "prefix_frame_hash": res.prefix_hash}),
        "seed_policy": res.seed_policy,
        "prompt_sha256": prompt_hash,
        "draws_in_order": draws,
        "unmanaged_draws": sum(1 for r in log if not r.managed),
        "output_frame_hash": output_hash,
    }


def build_manifest(res):
    return {
        "schema": SCHEMA_MANIFEST,
        "harness_version": __version__,
        "backend": BACKEND,
        "python_version": sys.version.split()[0],
        "exp_id": res.exp_id,
        "seed_policy": res.seed_policy,
        "mode": res.mode,
        "hazard_mode": bool(res.hazard),
        "seed": {"value": res.seed,
                 "note": "single managed generator; mode=coupled restores its "
                         "state at the fork and additionally replay-injects "
                         "recorded noise; mode=uncoupled uses a fresh state"},
        "fork_point": {"step": res.fork_step,
                       "prefix_frame_hash": res.prefix_hash,
                       "prefix_drawlog_digest":
                           sha256_text(canon_json(
                               [rec_to_json(r, include_values=False)
                                for r in res.snapshot.draw_log]))},
        "config_invariant": {
            "common_sha256": cfg_common_hash(res.cfg),
            "byte_identical_except_prompt": True,
            "prompt_sha256": {"factual": cfg_prompt_hash(res.cfg),
                              "counterfactual": cfg_prompt_hash(res.cf_cfg)},
            "assertion": "branches share one config object; only "
                         + PROMPT_KEY + " differs, proven by the two hashes",
        },
        "config_factual": enc_json(res.cfg),
        "branches": [
            _branch_manifest("factual", None, res, res.factual_log,
                             res.factual_output_hash, cfg_prompt_hash(res.cfg)),
            _branch_manifest("counterfactual", "factual", res, res.cf_log,
                             res.cf_output_hash, cfg_prompt_hash(res.cf_cfg)),
        ],
        "comparison": res.comparison,
        "policy_violations": res.policy_violations,
    }


def save_twins(res, out_dir):
    """Write auditable artifacts, then the manifest referencing them.

    All artifact paths stored in the manifest are RELATIVE to out_dir, so
    manifest bytes are independent of where they are saved (reproducibility).
    """
    os.makedirs(out_dir, exist_ok=True)
    br_dir = os.path.join(out_dir, "branches")
    os.makedirs(br_dir, exist_ok=True)

    artifacts = []

    def write_json(relpath, obj):
        path = os.path.join(out_dir, relpath)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, sort_keys=True, indent=2)
        artifacts.append({"path": relpath, "sha256": file_sha256(path),
                          "bytes": os.path.getsize(path)})
        return relpath

    write_json("fork-snapshot.json", res.snapshot.to_json())
    for bid, world, log, out_hash, cfg in (
            ("factual", res.factual_world, res.factual_log,
             res.factual_output_hash, res.cfg),
            ("counterfactual", res.cf_world, res.cf_log,
             res.cf_output_hash, res.cf_cfg)):
        write_json("branches/%s.frame.json" % bid,
                   {"schema": SCHEMA_MANIFEST + "#frame", "branch_id": bid,
                    "frame_hash": out_hash, "frame": enc_json(world["frame"])})
        write_json("branches/%s.drawlog.json" % bid,
                   {"schema": SCHEMA_MANIFEST + "#drawlog", "branch_id": bid,
                    "draws_in_order": [
                        {"i": r.i, "kind": r.kind, "tag": r.tag,
                         "managed": r.managed, "hash": r.hash} for r in log]})

    manifest = build_manifest(res)
    manifest["artifacts"] = artifacts
    mpath = os.path.join(out_dir, "manifest.json")
    with open(mpath, "w", encoding="utf-8") as f:
        json.dump(manifest, f, sort_keys=True, indent=2)
    return manifest


def load_snapshot(path):
    return BranchSnapshot.load(path)


def log_to_json(log):
    return [rec_to_json(r, include_values=True) for r in log]


def log_from_json(obj):
    return [rec_from_json(r) for r in obj]