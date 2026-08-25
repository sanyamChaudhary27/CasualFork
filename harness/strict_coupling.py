"""SC1 strict-coupling validator (CausalFork pre-GPU phase P3, item C).

Compares two stochastic-site ledger files produced by the patched Evoke tree
(patches/evoke-74d26851-strict-coupling.patch, evoke/strict_fork.py) and decides,
with machine-readable reasons, whether a factual/counterfactual branch pair is

    STRICT_NOISE_COUPLED        every reachable post-fork site drew byte-identical
                                noise from identically-evolving generators, with no
                                bypass indicators; or
    STRICT_COUPLING_INVALID     any violation whatsoever (reason codes listed below).

GENERATOR_STATE_RESTORED is NOT a coupling verdict. It is the continuation label
for a branch that resumed from captured generator states at the fork boundary;
it appears only under result["continuation"] / result["restored_branches"] and is
rejected if anyone tries to use it as a coupling status (validate_status()).

Reason codes
------------
MISSING_SITE:<site>            required reachable site absent from a branch log
MISSING_SITE:<site>#<ord>      aligned draw absent in one branch
UNEXPECTED_SITE:<site>         site outside the required inventory appeared
ORDINAL_MISMATCH:<site>        per-site ordinal sets differ across branches
FIELD_MISMATCH:<f>@<k>         aligned metadata differs (chunk/stage/shape/dtype/
                               generator_state_hash_*/generator_role)
TENSOR_MISMATCH@<k>            tensor_sha256 differs for an aligned draw
STREAM_CHAIN_BREAK:<k>         declared generator stream did not evolve contiguously
NOOP_DRAW_BYPASS:<k>           recorded draw left its generator state unchanged
PRECOND1_GLOBAL_RNG_BYPASS@<k> R7 drew from the global RNG (EVOKE_WARP_SEED unset)
GLOBAL_RNG_DIVERGENCE@<k>      global-RNG digest differs across aligned draws
RESTORE_METADATA_MISMATCH      continuation claim malformed/inconsistent
TERMINOLOGY_VIOLATION          continuation label misused / unknown status string
"""

from __future__ import annotations

import json

STRICT_NOISE_COUPLED = "STRICT_NOISE_COUPLED"
STRICT_COUPLING_INVALID = "STRICT_COUPLING_INVALID"
GENERATOR_STATE_RESTORED = "GENERATOR_STATE_RESTORED"

COUPLING_STATUSES = (STRICT_NOISE_COUPLED, STRICT_COUPLING_INVALID)

REQUIRED_SITES = ("R1", "R2", "R3", "R4", "R5", "R6", "R7")
MAIN_STREAM_SITES = ("R1", "R2", "R3", "R4", "R5", "R6")
ISOLATED_SITES = ("R7",)

REQUIRED_ENTRY_FIELDS = (
    "site_id", "ordinal", "tensor_sha256", "shape", "dtype",
    "generator_state_hash_before", "generator_state_hash_after", "generator_role",
)

COMPARED_FIELDS = (
    "chunk", "stage", "shape", "dtype", "tensor_sha256",
    "generator_state_hash_before", "generator_state_hash_after",
    "generator_role", "global_rng_sha256",
)


def validate_status(status):
    """Guard terminology: only coupling verdicts are legal statuses."""
    if status not in COUPLING_STATUSES:
        raise ValueError(
            "illegal coupling status %r; use STRICT_NOISE_COUPLED / "
            "STRICT_COUPLING_INVALID (GENERATOR_STATE_RESTORED is a continuation "
            "label, never a coupling verdict)" % (status,)
        )
    return status


def _read_lines(source):
    if hasattr(source, "read"):
        return source.read().splitlines()
    if isinstance(source, str):
        import os
        if os.path.exists(source):
            with open(source, "r", encoding="utf-8") as fh:
                return fh.read().splitlines()
        if source.lstrip().startswith("{"):
            return source.splitlines()
        raise ValueError("ledger source not found and not JSONL text: %r" % source[:80])
    raise TypeError("unsupported ledger source: %r" % type(source))


def load_log(source):
    """Return (meta_dict, entries, events). Raises ValueError on parse errors."""
    meta, entries, events = {}, [], []
    for lineno, line in enumerate(_read_lines(source), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception as exc:
            raise ValueError("parse error at line %d: %s" % (lineno, exc))
        event = obj.get("event")
        if event == "meta":
            meta = obj
        elif event == "draw":
            entries.append(obj)
        elif event is not None:
            events.append(obj)
    return meta, entries, events


def _key(entry):
    return (entry.get("site_id"), entry.get("ordinal"))


def _continuation_of(meta, explicit, branch_label, reasons):
    """Resolve the continuation claim for one branch; enforce terminology."""
    value = explicit if explicit is not None else meta.get("continuation")
    if value is None:
        return None
    if value != GENERATOR_STATE_RESTORED:
        reasons.append("TERMINOLOGY_VIOLATION:%s continuation=%r" % (branch_label, value))
        reasons.append("RESTORE_METADATA_MISMATCH:%s" % branch_label)
        return None
    return value


CORE_ENTRY_FIELDS = ("site_id", "ordinal", "tensor_sha256", "shape", "dtype")
STREAM_ENTRY_FIELDS = ("generator_state_hash_before", "generator_state_hash_after")


def _intra_log_checks(entries, branch_label, reasons):
    seen_pairs = set()
    ordered = sorted(entries, key=lambda e: e.get("seq", 0))
    last_main_after = None
    for e in ordered:
        site = e.get("site_id")
        ordinal = e.get("ordinal")
        k = "%s#%s" % (site, ordinal)
        for f in CORE_ENTRY_FIELDS:
            if e.get(f) is None:
                reasons.append("FIELD_MISMATCH:none@%s (%s missing in %s)" % (k, f, branch_label))
        pair = (site, ordinal)
        if pair in seen_pairs:
            reasons.append("ORDINAL_MISMATCH:%s duplicate ordinal %r in %s"
                           % (site, ordinal, branch_label))
        seen_pairs.add(pair)
        if site in ISOLATED_SITES:
            if e.get("generator_role") != "isolated_warp":
                reasons.append("PRECOND1_GLOBAL_RNG_BYPASS@%s role=%r"
                               % (k, e.get("generator_role")))
            continue  # isolated stream: excluded from the main-stream chain
        for f in STREAM_ENTRY_FIELDS:
            if e.get(f) is None:
                reasons.append("FIELD_MISMATCH:none@%s (%s missing in %s)" % (k, f, branch_label))
        before = e.get("generator_state_hash_before")
        after = e.get("generator_state_hash_after")
        if before is not None and after is not None:
            if before == after:
                reasons.append("NOOP_DRAW_BYPASS:%s" % k)
            if last_main_after is not None and before != last_main_after:
                reasons.append("STREAM_CHAIN_BREAK:%s" % k)
        last_main_after = after if after is not None else last_main_after


def compare_coupling_logs(factual_log, cf_log, factual_meta=None, cf_meta=None):
    """Compare factual vs counterfactual strict-coupling ledgers.

    Returns a dict; NEVER mutates inputs. The overall verdict is under "status".
    """
    reasons = []
    try:
        f_meta, f_entries, f_events = load_log(factual_log)
    except ValueError as exc:
        return _invalid(["LEDGER_PARSE_ERROR:factual:%s" % exc])
    try:
        c_meta, c_entries, c_events = load_log(cf_log)
    except ValueError as exc:
        return _invalid(["LEDGER_PARSE_ERROR:counterfactual:%s" % exc])

    continuation = {
        "factual": _continuation_of(f_meta, factual_meta, "factual", reasons),
        "counterfactual": _continuation_of(c_meta, cf_meta, "counterfactual", reasons),
    }
    restored_branches = [b for b, v in continuation.items() if v == GENERATOR_STATE_RESTORED]

    # ---- coverage / alignment ------------------------------------------------
    f_keys = [_key(e) for e in f_entries]
    c_keys = [_key(e) for e in c_entries]
    f_set, c_set = set(f_keys), set(c_keys)

    f_sites = {s for s, _ in f_set}
    c_sites = {s for s, _ in c_set}
    for site in REQUIRED_SITES:
        if site not in f_sites:
            reasons.append("MISSING_SITE:%s (factual)" % site)
        if site not in c_sites:
            reasons.append("MISSING_SITE:%s (counterfactual)" % site)
    for site in sorted((f_sites | c_sites) - set(REQUIRED_SITES)):
        reasons.append("UNEXPECTED_SITE:%s" % site)

    for key in sorted(f_set - c_set):
        reasons.append("MISSING_SITE:%s#%s (counterfactual)" % key)
    for key in sorted(c_set - f_set):
        reasons.append("MISSING_SITE:%s#%s (factual)" % key)
    for site in sorted(f_sites & c_sites):
        f_ords = sorted(o for s, o in f_set if s == site)
        c_ords = sorted(o for s, o in c_set if s == site)
        if f_ords != c_ords:
            reasons.append("ORDINAL_MISMATCH:%s factual=%s counterfactual=%s"
                           % (site, f_ords, c_ords))

    # ---- aligned field equality ---------------------------------------------
    f_by_key = {_key(e): e for e in f_entries}
    c_by_key = {_key(e): e for e in c_entries}
    compared = 0
    for key in sorted(f_set & c_set):
        fe, ce = f_by_key[key], c_by_key[key]
        label = "%s#%s" % key
        for field in COMPARED_FIELDS:
            fv, cv = fe.get(field), ce.get(field)
            if fv != cv:
                if field == "tensor_sha256":
                    reasons.append("TENSOR_MISMATCH@%s" % label)
                elif field == "global_rng_sha256":
                    reasons.append("GLOBAL_RNG_DIVERGENCE@%s" % label)
                else:
                    reasons.append("FIELD_MISMATCH:%s@%s" % (field, label))
        compared += 1

    # ---- intra-log stream integrity -----------------------------------------
    _intra_log_checks(f_entries, "factual", reasons)
    _intra_log_checks(c_entries, "counterfactual", reasons)

    status = STRICT_NOISE_COUPLED if not reasons else STRICT_COUPLING_INVALID
    validate_status(status)
    return {
        "status": status,
        "reasons": reasons,
        "entries_compared": compared,
        "sites": sorted(f_sites & c_sites),
        "continuation": continuation,
        "restored_branches": restored_branches,
    }


def _invalid(reasons):
    return {
        "status": STRICT_COUPLING_INVALID,
        "reasons": reasons,
        "entries_compared": 0,
        "sites": [],
        "continuation": {"factual": None, "counterfactual": None},
        "restored_branches": [],
    }


def is_pass(result):
    return result.get("status") == STRICT_NOISE_COUPLED


def format_result(result):
    lines = ["%s (%d draws compared)" % (result["status"], result["entries_compared"])]
    if result["restored_branches"]:
        lines.append("continuation: %s -> %s"
                     % (", ".join(result["restored_branches"]), GENERATOR_STATE_RESTORED))
    for r in result["reasons"]:
        lines.append("  - %s" % r)
    return "\n".join(lines)


if __name__ == "__main__":  # pragma: no cover - tiny CLI convenience
    import sys
    if len(sys.argv) != 3:
        print("usage: python strict_coupling.py FACTUAL.jsonl COUNTERFACTUAL.jsonl")
        raise SystemExit(2)
    res = compare_coupling_logs(sys.argv[1], sys.argv[2])
    print(format_result(res))
    raise SystemExit(0 if is_pass(res) else 1)