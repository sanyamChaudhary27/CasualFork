#!/usr/bin/env python3
"""Build patches/evoke-74d26851-strict-coupling.patch (STAGE-B/C fix round).

Method (per P3 spec):
  1. pristine tree : git archive of pin 74d268516d95c8fceadd2378f91a73f9f187042b -> <base>/sc1-p1
  2. work tree     : same archive -> <base>/sc1-wk ; ALL edits happen ONLY here
                     (new module source copied verbatim from evoke_strict_fork.py.txt)
  3. diff          : git diff --no-index between the two trees; header prefixes
                     normalized to a/ b/ (the ONLY post-processing)
  4. verify        : git apply --check against a FRESH third extract (<base>/sc1-fresh),
                     then really apply and require byte-identity with the work tree
  5. sidecar       : <patch>.sha256 (launchers export it as EVOKE_STRICT_PATCH_SHA256)

Fork-boundary semantics this round (adjudication 2026-08-25):
  * hook moved to the TOP of the chunk loop (before prompt selection :2413,
    warp render :2617 / encode :2628, prepare_latents :2791 - i.e. before ANY
    post-fork stochastic draw);
  * stage context reset to None at every chunk start;
  * R2/R3 emit input/mean/std sha256 diagnostics; R7 rows carry render_call /
    call_ordinal / high / skip_flag and empty domains emit skip rows.

The pinned clone evoke-pin is never modified and never committed to.
Re-run after staging trees:  python patches/make_sc1_patch.py --skip-stage
"""
from __future__ import annotations

import hashlib
import os
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True

BASE = r"C:\Users\HP\AppData\Local\Temp\opencode"
PIN_CLONE = os.path.join(BASE, "evoke-pin")
P1 = os.path.join(BASE, "sc1-p1")
WK = os.path.join(BASE, "sc1-wk")
FRESH = os.path.join(BASE, "sc1-fresh")
HERE = os.path.dirname(os.path.abspath(__file__))
PATCH_OUT = os.path.join(HERE, "evoke-74d26851-strict-coupling.patch")
SF_SRC = os.path.join(HERE, "evoke_strict_fork.py.txt")
CONFIG_ID_SRC = os.path.join(HERE, os.pardir, "harness", "gpu01_config_identity.py")

PIN = "74d268516d95c8fceadd2378f91a73f9f187042b"

PIPELINE = os.path.join("evoke", "pipelines", "pipeline_evoke.py")
DA3CLOUD = os.path.join("evoke", "modules", "geometric_state", "da3_cloud.py")
STRICT_FORK_REL = os.path.join("evoke", "strict_fork.py")
CONFIG_ID_REL = os.path.join("evoke", "gpu01_config_identity.py")

# --- edits: (file, label, anchor, replacement) ---------------------------------
IMPORT_SF = (
    "from ..strict_fork import (\n"
    "    build_live_state_view as _sf_build_live_state_view,\n"
    "    collect_generators as _sf_collect_generators,\n"
    "    fork_mode_active as _sf_fork_active,\n"
    "    gen_state_of as _sf_gen_state,\n"
    "    log_draw as _sf_log_draw,\n"
    "    maybe_fork_boundary as _sf_maybe_fork_boundary,\n"
    "    new_render_call as _sf_new_render_call,\n"
    "    pixel_diag as _sf_pixel_diag,\n"
    "    set_chunk as _sf_set_chunk,\n"
    "    set_stage as _sf_set_stage,\n"
    ")\n"
)

EDITS = [
    (os.path.join("scripts", "inference", "infer_single.py"),
     "import strict engine attestation",
     "# EVOKE_CPU_THREADS: set by infer_batch to core_count // n_shards. The OMP_* env vars it also sets are\n",
     "from evoke.strict_fork import attest_engine_config as _sf_attest_engine_config\n\n"
     "# EVOKE_CPU_THREADS: set by infer_batch to core_count // n_shards. The OMP_* env vars it also sets are\n"),
    (os.path.join("scripts", "inference", "infer_single.py"),
     "attest parsed strict launch before prereqs/model construction",
     "    args = parse_args(argv)\n    _check_prereqs(args)\n",
     "    args = parse_args(argv)\n    _sf_attest_engine_config(vars(args), os.environ)\n    _check_prereqs(args)\n"),
    (PIPELINE, "import strict_fork (pipeline)",
     "from diffusers.utils.torch_utils import randn_tensor\n",
     "from diffusers.utils.torch_utils import randn_tensor\n" + IMPORT_SF),

    (PIPELINE, "R1 per-chunk DiT noise (:371 via :2791)",
     "        latents = randn_tensor(shape, generator=generator, device=device, dtype=dtype)\n"
     "        return latents\n",
     "        _sf_b = _sf_gen_state(generator)\n"
     "        latents = randn_tensor(shape, generator=generator, device=device, dtype=dtype)\n"
     "        _sf_log_draw(\"R1\", latents, generator=generator, gen_before=_sf_b, generator_role=\"main\")\n"
     "        return latents\n"),

    (PIPELINE, "R2 warp first-frame VAE encode (:424) + diagnostics",
     "            first_frame_latent = self.vae.encode(first_frame).latent_dist.sample(generator=generator)\n"
     "            first_frame_latent = (first_frame_latent - latents_mean) * latents_std\n",
     "            _sf_b = _sf_gen_state(generator)\n"
     "            first_frame_latent = self.vae.encode(first_frame).latent_dist.sample(generator=generator)\n"
     "            _sf_log_draw(\"R2\", first_frame_latent, generator=generator, gen_before=_sf_b, generator_role=\"main\",\n"
     "                         extra=_sf_pixel_diag(first_frame, latents_mean, latents_std))\n"
     "            first_frame_latent = (first_frame_latent - latents_mean) * latents_std\n"),

    (PIPELINE, "R3 warp chunk VAE encode (:432) + diagnostics",
     "                chunk_latents = self.vae.encode(video_chunk).latent_dist.sample(generator=generator)\n"
     "                chunk_latents = (chunk_latents - latents_mean) * latents_std\n",
     "                _sf_b = _sf_gen_state(generator)\n"
     "                chunk_latents = self.vae.encode(video_chunk).latent_dist.sample(generator=generator)\n"
     "                _sf_log_draw(\"R3\", chunk_latents, generator=generator, gen_before=_sf_b, generator_role=\"main\",\n"
     "                             extra=dict(_sf_pixel_diag(video_chunk, latents_mean, latents_std) or {}, loop_i=i))\n"
     "                chunk_latents = (chunk_latents - latents_mean) * latents_std\n"),

    (PIPELINE, "R6 stage2 correlated renoise draw (:573 via :1474)",
     "        z = torch.randn(block_number, block_size, generator=generator, device=generator.device).to(device=device)\n"
     "        noise = z @ L.T\n",
     "        _sf_b = _sf_gen_state(generator)\n"
     "        z = torch.randn(block_number, block_size, generator=generator, device=generator.device).to(device=device)\n"
     "        _sf_log_draw(\"R6\", z, generator=generator, gen_before=_sf_b, generator_role=\"main\")\n"
     "        noise = z @ L.T\n"),

    (PIPELINE, "R4 warp frame sigmas torch.rand(9) (:977)",
     "        frame_sigmas = (\n"
     "            torch.rand(chunk_frames, device=device, generator=rand_generator) * (sigma_max - sigma_min) + sigma_min\n"
     "        ).to(dtype=warp_latents.dtype)\n",
     "        _sf_b = _sf_gen_state(rand_generator)\n"
     "        frame_sigmas = (\n"
     "            torch.rand(chunk_frames, device=device, generator=rand_generator) * (sigma_max - sigma_min) + sigma_min\n"
     "        ).to(dtype=warp_latents.dtype)\n"
     "        _sf_log_draw(\"R4\", frame_sigmas, generator=rand_generator, gen_before=_sf_b, generator_role=\"main\")\n"),

    (PIPELINE, "R5 visibility-aware warp noise (:996)",
     "            noise = randn_tensor(warp_latents.shape, generator=generator, device=device, dtype=warp_latents.dtype)\n"
     "            return sigmas * noise + (1.0 - sigmas) * warp_latents\n",
     "            _sf_b = _sf_gen_state(generator)\n"
     "            noise = randn_tensor(warp_latents.shape, generator=generator, device=device, dtype=warp_latents.dtype)\n"
     "            _sf_log_draw(\"R5\", noise, generator=generator, gen_before=_sf_b, generator_role=\"main\")\n"
     "            return sigmas * noise + (1.0 - sigmas) * warp_latents\n"),

    (PIPELINE, "stage context in stage2_sample (:1442)",
     "        for i_s in range(stage2_num_stages):\n",
     "        for i_s in range(stage2_num_stages):\n"
     "            _sf_set_stage(i_s)\n"),

    (PIPELINE, "TRUE fork boundary at TOP of chunk loop (:2367); stage reset; ephemeral live-state view; replaces v1 mid-loop hook",
     "        for k in _chunk_iter:\n",
     "        for k in _chunk_iter:\n"
     "            _sf_set_chunk(int(k))\n"
     "            _sf_set_stage(None)   # [CausalFork SC1] stage context resets every chunk start\n"
     "            # [CausalFork SC1] TRUE fork boundary: TOP of the chunk loop - BEFORE prompt\n"
     "            # selection (:2413), warp render (:2617) / encode (:2628), prepare_latents (:2791):\n"
     "            # zero post-fork stochastic draws can precede capture/restore. No-op unless\n"
     "            # EVOKE_STRICT_FORK_JSON is set. The EPHEMERAL NON-OWNING LiveStateView is\n"
     "            # constructed FIRST (gated to StrictCoupling-active) from THIS iteration's\n"
     "            # locals: history_latents / total_generated_latent_frames were last updated\n"
     "            # by the PREVIOUS chunk iteration (:3019-3020), so the view reflects the\n"
     "            # POST-PREFIX state at the true boundary; it is passed to the hook instead\n"
     "            # of the raw pipeline. Observational-only: references live objects, never\n"
     "            # clones, never mutates, no new persistent aliases on self.\n"
     "            _sf_view = self\n"
     "            if _sf_fork_active():\n"
     "                _sf_view = _sf_build_live_state_view(\n"
     "                    history_latents, total_generated_latent_frames, geo_state, self,\n"
     "                    chunk_index=int(k), event_set_size=len(_event_set),\n"
     "                    forced_off_flags={\n"
     "                        \"use_kv_cache\": bool(use_kv_cache),\n"
     "                        \"use_cfg_zero_star\": bool(use_cfg_zero_star),\n"
     "                        \"use_dmd\": bool(use_dmd),\n"
     "                        \"use_adaptive_anti_drifting\": bool(use_adaptive_anti_drifting),\n"
     "                        \"use_interpolate_prompt\": bool(use_interpolate_prompt),\n"
     "                        \"geo_disable_prev_short\": bool(geo_disable_prev_short),\n"
     "                        \"is_keep_x0\": bool(is_keep_x0),\n"
     "                        \"short_tier_noise_enabled\": bool((getattr(self, \"_short_tier_noise_cfg\", None) or {}).get(\"enabled\", False)),\n"
     "                    })\n"
     "            _sf_maybe_fork_boundary(int(k), _sf_collect_generators(generator, getattr(self, \"_geo_patchdrop_gen\", None)), _sf_view)\n"),

    (DA3CLOUD, "import strict_fork (da3_cloud)",
     "from .depth_backend import reset_stream as _reset_depth_stream\n",
     "from .depth_backend import reset_stream as _reset_depth_stream\n"
     "from ...strict_fork import gen_state_of as _sf_gen_state\n"
     "from ...strict_fork import log_draw as _sf_log_draw\n"
     "from ...strict_fork import new_render_call as _sf_new_render_call\n"),

    (DA3CLOUD, "R7 per-render-call id (da3_cloud.py:1476)",
     "    _cgen = torch.Generator(device=device).manual_seed(int(_wseed)) if _wseed is not None else None\n",
     "    _cgen = torch.Generator(device=device).manual_seed(int(_wseed)) if _wseed is not None else None\n"
     "    _sf_rcall = _sf_new_render_call()   # [CausalFork SC1] isolated-stream witness id\n"),

    (DA3CLOUD, "R7 enumerate gids for complete call_ordinal coverage (:1479-81; "
               "zbuf core only - the ; subpts variants are the unreachable U12/U13 cores)",
     "    P_all = torch.full((len(ids_all), M, 3), FAR, device=device)\n"
     "    for g in ids_all:\n"
     "        d, it, cwi, _ = store[g]; wp = unproject_depth_torch(d, it, cwi).reshape(-1, 3)\n",
     "    P_all = torch.full((len(ids_all), M, 3), FAR, device=device)\n"
     "    for _sf_ci, g in enumerate(ids_all):\n"
     "        d, it, cwi, _ = store[g]; wp = unproject_depth_torch(d, it, cwi).reshape(-1, 3)\n"),

    (DA3CLOUD, "R7 zbuf covis subsample: bracketed draw + high/skip_flag rows (:1485-88)",
     "        if wp.shape[0] > 0:\n"
     "            _idx = (torch.randint(0, wp.shape[0], (M,), device=device, generator=_cgen)\n"
     "                    if _cgen is not None else torch.randint(0, wp.shape[0], (M,), device=device))\n"
     "            P_all[id2row[g]] = wp[_idx]\n",
     "        if wp.shape[0] > 0:\n"
     "            _sf_b = _sf_gen_state(_cgen)\n"
     "            _idx = (torch.randint(0, wp.shape[0], (M,), device=device, generator=_cgen)\n"
     "                    if _cgen is not None else torch.randint(0, wp.shape[0], (M,), device=device))\n"
     "            P_all[id2row[g]] = wp[_idx]\n"
     "            _sf_log_draw(\"R7\", _idx, generator=_cgen, gen_before=_sf_b,\n"
     "                         generator_role=(\"isolated_warp\" if _cgen is not None else \"GLOBAL_FALLBACK\"),\n"
     "                         extra={\"source_gid\": int(g), \"covis_M\": int(M), \"render_call\": _sf_rcall,\n"
     "                                \"call_ordinal\": int(_sf_ci), \"high\": int(wp.shape[0]), \"skip_flag\": False})\n"
     "        else:\n"
     "            _sf_b = _sf_gen_state(_cgen)\n"
     "            _sf_log_draw(\"R7\", None, generator=_cgen, gen_before=_sf_b,\n"
     "                         generator_role=(\"isolated_warp\" if _cgen is not None else \"GLOBAL_FALLBACK\"),\n"
     "                         extra={\"source_gid\": int(g), \"covis_M\": int(M), \"render_call\": _sf_rcall,\n"
     "                                \"call_ordinal\": int(_sf_ci), \"high\": 0, \"skip_flag\": True})\n"),
]


def run(cmd, cwd=None, check=True):
    res = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = res.stdout.decode("utf-8", errors="replace")
    err = res.stderr.decode("utf-8", errors="replace")
    if check and res.returncode != 0:
        raise SystemExit("command failed (%d): %s\n%s\n%s" % (res.returncode, " ".join(cmd), out, err))
    return res.returncode, out + ("\n[stderr]\n" + err if err.strip() else "")


def stage_trees():
    tarball = os.path.join(BASE, "sc1-pin.tar")
    run(["git", "-c", "core.autocrlf=false", "-C", PIN_CLONE, "archive", "--format=tar", "-o", tarball, "HEAD"])
    rc, rev = run(["git", "-C", PIN_CLONE, "rev-parse", "HEAD"])
    assert rev.strip() == PIN, "pin moved: %r" % rev.strip()
    for d in (P1, WK, FRESH):
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d, exist_ok=True)
        run(["tar", "-xf", tarball, "-C", d])
    os.remove(tarball)


def apply_edits():
    cache = {}
    for rel, label, anchor, repl in EDITS:
        path = os.path.join(WK, rel)
        text = cache.setdefault(path, open(path, "r", encoding="utf-8", newline="").read())
        n = text.count(anchor)
        if n != 1:
            raise SystemExit("anchor not unique (%d hits) for %r [%s]" % (n, label, rel))
        cache[path] = text.replace(anchor, repl, 1)
        print("[edit] %-58s -> %s" % (label, rel))
    for path, text in cache.items():
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
    sf = open(SF_SRC, "r", encoding="utf-8").read().replace("\r\n", "\n")
    if not sf.endswith("\n"):
        sf += "\n"
    with open(os.path.join(WK, STRICT_FORK_REL), "w", encoding="utf-8", newline="") as fh:
        fh.write(sf)
    print("[new ] %s (%d lines)" % (STRICT_FORK_REL, sf.count("\n")))
    config_id = open(CONFIG_ID_SRC, "r", encoding="utf-8").read().replace("\r\n", "\n")
    if not config_id.endswith("\n"):
        config_id += "\n"
    with open(os.path.join(WK, CONFIG_ID_REL), "w", encoding="utf-8", newline="") as fh:
        fh.write(config_id)
    if open(CONFIG_ID_SRC, "rb").read().replace(b"\r\n", b"\n") != \
            open(os.path.join(WK, CONFIG_ID_REL), "rb").read():
        raise SystemExit("canonical GPU-01 identity source was not copied byte-identically")
    print("[new ] %s (%d lines; byte-identical canonical source)" %
          (CONFIG_ID_REL, config_id.count("\n")))
    tmp = tempfile.mkdtemp(prefix="sc1-pyc-")
    try:
        for i, rel in enumerate((PIPELINE, DA3CLOUD, STRICT_FORK_REL, CONFIG_ID_REL,
                                 os.path.join("scripts", "inference", "infer_single.py"))):
            py_compile.compile(os.path.join(WK, rel), cfile=os.path.join(tmp, "c%d.pyc" % i), doraise=True)
            print("[pyOK] %s" % rel)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        for root, dirs, _files in os.walk(WK):
            for d in list(dirs):
                if d == "__pycache__":
                    shutil.rmtree(os.path.join(root, d), ignore_errors=True)


def build_patch():
    # `diff` becomes the distributable patch bytes: capture stdout ONLY. Git on
    # Windows may emit autocrlf warnings on stderr; appending those warnings made
    # a technically applyable but contaminated patch artifact.
    stat_p = subprocess.run(
        ["git", "-c", "core.autocrlf=false", "diff", "--no-index", "--stat",
         "--", "sc1-p1", "sc1-wk"], cwd=BASE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stat = stat_p.stdout.decode("utf-8", errors="replace")
    diff_p = subprocess.run(
        ["git", "-c", "core.autocrlf=false", "diff", "--no-index", "--",
         "sc1-p1", "sc1-wk"], cwd=BASE,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    rc = diff_p.returncode
    diff = diff_p.stdout.decode("utf-8", errors="replace")
    if rc != 1:
        raise SystemExit("git diff --no-index returned %d (expected 1); output:\n%s" % (rc, diff))

    def fix_header(line):
        m = re.match(r"^diff --git (\S+) (\S+)$", line)
        if m:
            def tok_rest(tok):
                mm = re.match(r"^[ab]/(?:sc1-p1|sc1-wk)/(.+)$", tok)
                return mm.group(1) if mm else None
            rest = tok_rest(m.group(1)) or tok_rest(m.group(2))
            return "diff --git a/%s b/%s" % (rest, rest)
        line = re.sub(r"^--- a/(?:sc1-p1|sc1-wk)/", "--- a/", line)
        line = re.sub(r"^\+\+\+ b/(?:sc1-p1|sc1-wk)/", "+++ b/", line)
        return line

    lines = []
    added = removed = files = 0
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            line = fix_header(line)
            files += 1
        elif line.startswith(("--- ", "+++ ")) and ("sc1-p1/" in line or "sc1-wk/" in line):
            line = fix_header(line)
        # Upstream has a few blank lines containing one space. A changed hunk
        # can render them as whitespace-only additions (`+ `); normalize those
        # no-content lines so the distributable patch passes diff hygiene.
        if line == "+ ":
            line = "+"
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1
        lines.append(line)
    patch = "\n".join(lines) + "\n"
    with open(PATCH_OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(patch)
    psha = hashlib.sha256(patch.encode("utf-8")).hexdigest()
    with open(PATCH_OUT + ".sha256", "w", encoding="ascii", newline="\n") as fh:
        fh.write(psha + "  evoke-74d26851-strict-coupling.patch\n")
    print(stat)
    print("[patch] wrote %s: %d files, +%d / -%d hunk lines, %d total lines, sha256=%s"
          % (PATCH_OUT, files, added, removed, len(lines) + 1, psha[:16] + "..."))
    return added, removed


def verify_patch():
    res = subprocess.run(["git", "-c", "core.autocrlf=false", "apply", "--check", PATCH_OUT], cwd=FRESH,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    status = "CLEAN" if res.returncode == 0 else "FAILED"
    print("[verify] git apply --check on fresh pin tree: %s" % status)
    if res.stdout: print(res.stdout.decode("utf-8", "replace"))
    if res.stderr: print(res.stderr.decode("utf-8", "replace"))
    if res.returncode != 0:
        raise SystemExit("apply-check FAILED")
    rc, out = run(["git", "apply", "--stat", PATCH_OUT], cwd=FRESH, check=False)
    print(out)
    run(["git", "-c", "core.autocrlf=false", "apply", PATCH_OUT], cwd=FRESH)
    import filecmp
    bad = []
    for rel in (PIPELINE, DA3CLOUD, STRICT_FORK_REL, CONFIG_ID_REL,
                os.path.join("scripts", "inference", "infer_single.py")):
        if not filecmp.cmp(os.path.join(FRESH, rel), os.path.join(WK, rel), shallow=False):
            bad.append(rel)
    if bad:
        raise SystemExit("applied FRESH tree differs from WORK tree for %r" % bad)
    source = open(CONFIG_ID_SRC, "rb").read().replace(b"\r\n", b"\n")
    copied = open(os.path.join(FRESH, CONFIG_ID_REL), "rb").read()
    if source != copied:
        raise SystemExit("applied canonical GPU-01 identity source differs from harness source")
    print("[verify] applied FRESH == edited WORK byte-for-byte; canonical identity copy verified")


def main():
    if "--skip-stage" not in sys.argv:
        stage_trees()
    apply_edits()
    added, removed = build_patch()
    verify_patch()
    print("[done] gate G1-prep artifact ready (+%d/-%d hunk lines)." % (added, removed))


if __name__ == "__main__":
    main()
