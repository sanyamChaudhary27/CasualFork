"""Machine-readable per-chunk draw grammar for SC1 (STAGE-B/C target 3).

DERIVATION - re-audited directly in the pinned source on 2026-08-25
(pin 74d268516d95c8fceadd2378f91a73f9f187042b; do NOT trust prose):

  chunk loop body, evoke/pipelines/pipeline_evoke.py:
    :2367  for k in _chunk_iter:                      <- fork hook must sit HERE
    :2413-2420 prompt selection (no RNG)
    :2617      _geo_render_chunk(...)                 -> R7 rows (da3_cloud
               :1486-87 covis randint; _cgen re-seeded per render call :1474-76;
               one row per gid over sorted(ids_all); wp.shape[0]==0 -> skip row)
    :2628      _geo_encode_warp_to_latents(...)
    :966         prepare_video_latents -> R2 (:424 first frame), R3 (:432 chunk)
    :977         R4 frame sigmas torch.rand(9)
    :997         R5 visibility-aware noise randn_tensor (active branch)
    :2791      prepare_latents                        -> R1
    :2868      stage2_sample: for i_s in range(3): if i_s > 0 (:1460):
               sample_block_noise (:1474)             -> R6 @ stage i_s (x2)

  => fixed-site order inside EVERY post-fork chunk:
        R2, R3, R4, R5, R1, R6(stage=1), R6(stage=2)
     with ALL R7 rows of the chunk strictly BEFORE the first fixed site.
  (The v1 prose put R7 between R5 and R1: WRONG. This module is the binding form.)

Violations surface as INVALID(GRAMMAR_*).
"""
from __future__ import annotations

CHUNK_SITE_SEQUENCE = ("R2", "R3", "R4", "R5", "R1", "R6", "R6")
FIXED_MULTIPLICITY = {"R1": 1, "R2": 1, "R3": 1, "R4": 1, "R5": 1, "R6": 2}
R6_STAGE_VALUES = (1, 2)
ISOLATED_SITE = "R7"

DERIVATION = {
    "pin": "74d268516d95c8fceadd2378f91a73f9f187042b",
    "chunk_loop_head": "pipeline_evoke.py:2367 for k in _chunk_iter",
    "prompt_selection_no_rng": "pipeline_evoke.py:2413-2420",
    "r7_warp_render": "pipeline_evoke.py:2617 -> da3_cloud.py:1486-87 (fresh _cgen per call :1474-76)",
    "r2_r3_r4_r5": "pipeline_evoke.py:2628 -> :966/:424/:432/:977/:997",
    "r1": "pipeline_evoke.py:2791 -> :371",
    "r6_x2": "pipeline_evoke.py:2868 -> :1442 loop, :1460 i_s>0 gate, :1474 call",
}


def _seq(e):
    return e.get("seq", 0)


def validate_chunk(chunk_draws, chunk_index=None, label=""):
    """Validate ONE chunk's draws (single branch). Returns GRAMMAR_* reasons."""
    reasons = []
    where = "chunk%s" % ("" if chunk_index is None else " %s" % chunk_index)
    if label:
        where += " [%s]" % label

    fixed = [e for e in chunk_draws if e.get("site_id") != ISOLATED_SITE]
    iso = [e for e in chunk_draws if e.get("site_id") == ISOLATED_SITE]

    # ---- fixed-site multiplicity + order ------------------------------------
    counts = {}
    for e in fixed:
        counts[e.get("site_id")] = counts.get(e.get("site_id"), 0) + 1
    for site, want in FIXED_MULTIPLICITY.items():
        got = counts.get(site, 0)
        if got != want:
            reasons.append("GRAMMAR_FIXED_SITE_COUNT:%s %s expected %d got %d"
                           % (where, site, want, got))
    for site in sorted(set(counts) - set(FIXED_MULTIPLICITY)):
        reasons.append("GRAMMAR_UNEXPECTED_FIXED_SITE:%s %s" % (where, site))

    seq_order = [e.get("site_id") for e in sorted(fixed, key=_seq)]
    if seq_order and seq_order != list(CHUNK_SITE_SEQUENCE):
        reasons.append(
            "GRAMMAR_ORDER:%s observed %s expected %s"
            % (where, "".join(seq_order), "".join(CHUNK_SITE_SEQUENCE)))

    # ---- R6 stage values -----------------------------------------------------
    r6 = [e for e in sorted(fixed, key=_seq) if e.get("site_id") == "R6"]
    stages = [e.get("stage") for e in r6]
    if len(stages) == len(R6_STAGE_VALUES) and stages != list(R6_STAGE_VALUES):
        reasons.append("GRAMMAR_R6_STAGES:%s observed %s expected %s"
                       % (where, stages, list(R6_STAGE_VALUES)))

    # ---- R7 structure: complete gid/ordinal coverage per render call ---------
    calls = {}
    for e in iso:
        ex = e.get("extra") or {}
        rc = ex.get("render_call")
        if rc is None:
            reasons.append("GRAMMAR_R7_NO_RENDER_CALL:%s ordinal=%r"
                           % (where, e.get("ordinal")))
            continue
        calls.setdefault(rc, []).append(e)
    for rc in sorted(calls, key=repr):
        rows = sorted(calls[rc], key=lambda e: (e.get("extra") or {}).get("call_ordinal", -1))
        ordinals = [(r.get("extra") or {}).get("call_ordinal") for r in rows]
        if ordinals != list(range(len(rows))):
            reasons.append("GRAMMAR_R7_COVERAGE:%s render_call=%r ordinals=%s"
                           % (where, rc, ordinals))
        for r in rows:
            skip = bool((r.get("extra") or {}).get("skip_flag"))
            high = (r.get("extra") or {}).get("high")
            if r.get("generator_state_hash_before") is None or \
               r.get("generator_state_hash_after") is None:
                reasons.append("GRAMMAR_R7_STATE_MISSING:%s render_call=%r call_ordinal=%r"
                               % (where, rc, (r.get("extra") or {}).get("call_ordinal")))
            if skip:
                if high not in (0, None):
                    reasons.append("GRAMMAR_R7_SKIP_HIGH:%s render_call=%r high=%r"
                                   % (where, rc, high))
                if r.get("tensor_sha256") is not None:
                    reasons.append("GRAMMAR_R7_SKIP_INDEX_PRESENT:%s render_call=%r"
                                   % (where, rc))
            else:
                if not high or int(high) <= 0:
                    reasons.append("GRAMMAR_R7_DRAW_HIGH:%s render_call=%r high=%r"
                                   % (where, rc, high))
                if r.get("tensor_sha256") is None:
                    reasons.append("GRAMMAR_R7_DRAW_INDEX_MISSING:%s render_call=%r"
                                   % (where, rc))
        # within-call chaining (isolated stream integrity)
        prev_after = None
        for r in rows:
            b = r.get("generator_state_hash_before")
            a = r.get("generator_state_hash_after")
            if b is None or a is None:
                continue  # already flagged above
            if prev_after is not None and b != prev_after:
                reasons.append("GRAMMAR_R7_CHAIN_BREAK:%s render_call=%r call_ordinal=%r"
                               % (where, rc, (r.get("extra") or {}).get("call_ordinal")))
            prev_after = a

    # ---- R7 must precede all fixed sites of the chunk ------------------------
    if fixed and iso:
        max_iso = max(_seq(e) for e in iso)
        min_fixed = min(_seq(e) for e in fixed)
        if max_iso > min_fixed:
            reasons.append("GRAMMAR_R7_POSITION:%s R7 rows must precede the "
                           "first fixed-site draw (re-audit: warp render :2617 "
                           "precedes encode :2628)" % where)
    return reasons


def validate_ledger(entries, fork_chunk=None):
    """Validate a WHOLE ledger's draw entries (single branch).

    Returns (reasons, chunks_checked). Chunks present must be contiguous from 0.
    Grammar applies to every logged chunk; fork_chunk is accepted for callers
    that need it but does not change the structural rules.
    """
    reasons = []
    by_chunk = {}
    for e in entries:
        by_chunk.setdefault(e.get("chunk"), []).append(e)
    if not by_chunk:
        return ["GRAMMAR_EMPTY_LEDGER"], 0
    chunks = sorted(c for c in by_chunk if c is not None)
    if chunks != list(range(len(chunks))):
        reasons.append("GRAMMAR_CHUNK_GAPS: observed %s" % chunks)
    for c in chunks:
        reasons.extend(validate_chunk(by_chunk[c], c))
    return reasons, len(chunks)