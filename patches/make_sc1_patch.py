#!/usr/bin/env python3
"""Build patches/evoke-74d26851-strict-coupling.patch (SC1 strict coupling, P3).

Method (per P3 spec):
  1. pristine tree : git archive of pin 74d268516d95c8fceadd2378f91a73f9f187042b -> <base>/sc1-p1
  2. work tree     : same archive -> <base>/sc1-wk ; ALL edits happen ONLY here
                     (new module source copied verbatim from evoke_strict_fork.py.txt)
  3. diff          : git diff --no-index between the two trees; a/sc1-p1/ b/sc1-wk/
                     header prefixes mechanically normalized to a/ b/ (the ONLY
                     post-processing; hunks untouched)
  4. verify        : git apply --check against a FRESH third extract (<base>/sc1-fresh)

The pinned clone evoke-pin is never modified and never committed to.
Re-run after staging trees:  python patches/make_sc1_patch.py --skip-stage
"""
from __future__ import annotations

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

PIN = "74d268516d95c8fceadd2378f91a73f9f187042b"

PIPELINE = os.path.join("evoke", "pipelines", "pipeline_evoke.py")
DA3CLOUD = os.path.join("evoke", "modules", "geometric_state", "da3_cloud.py")
STRICT_FORK_REL = os.path.join("evoke", "strict_fork.py")

# --- edits: (file, anchor, replacement, label) --------------------------------
IMPORT_SF = (
    "from ..strict_fork import (\n"
    "    collect_generators as _sf_collect_generators,\n"
    "    gen_state_of as _sf_gen_state,\n"
    "    log_draw as _sf_log_draw,\n"
    "    maybe_fork_boundary as _sf_maybe_fork_boundary,\n"
    "    set_chunk as _sf_set_chunk,\n"
    "    set_stage as _sf_set_stage,\n"
    ")\n"
)

EDITS = [
    ("import strict_fork (pipeline)", PIPELINE,
     "from diffusers.utils.torch_utils import randn_tensor\n",
     "from diffusers.utils.torch_utils import randn_tensor\n" + IMPORT_SF),

    ("R1 per-chunk DiT noise (:371 via :2791)", PIPELINE,
     "        latents = randn_tensor(shape, generator=generator, device=device, dtype=dtype)\n"
     "        return latents\n",
     "        _sf_b = _sf_gen_state(generator)\n"
     "        latents = randn_tensor(shape, generator=generator, device=device, dtype=dtype)\n"
     "        _sf_log_draw(\"R1\", latents, generator=generator, gen_before=_sf_b, generator_role=\"main\")\n"
     "        return latents\n"),

    ("R2 warp first-frame VAE encode (:424)", PIPELINE,
     "            first_frame_latent = self.vae.encode(first_frame).latent_dist.sample(generator=generator)\n"
     "            first_frame_latent = (first_frame_latent - latents_mean) * latents_std\n",
     "            _sf_b = _sf_gen_state(generator)\n"
     "            first_frame_latent = self.vae.encode(first_frame).latent_dist.sample(generator=generator)\n"
     "            _sf_log_draw(\"R2\", first_frame_latent, generator=generator, gen_before=_sf_b, generator_role=\"main\")\n"
     "            first_frame_latent = (first_frame_latent - latents_mean) * latents_std\n"),

    ("R3 warp chunk VAE encode (:432)", PIPELINE,
     "                chunk_latents = self.vae.encode(video_chunk).latent_dist.sample(generator=generator)\n"
     "                chunk_latents = (chunk_latents - latents_mean) * latents_std\n",
     "                _sf_b = _sf_gen_state(generator)\n"
     "                chunk_latents = self.vae.encode(video_chunk).latent_dist.sample(generator=generator)\n"
     "                _sf_log_draw(\"R3\", chunk_latents, generator=generator, gen_before=_sf_b, generator_role=\"main\", extra={\"loop_i\": i})\n"
     "                chunk_latents = (chunk_latents - latents_mean) * latents_std\n"),

    ("R6 stage2 correlated renoise draw (:573 via :1474)", PIPELINE,
     "        z = torch.randn(block_number, block_size, generator=generator, device=generator.device).to(device=device)\n"
     "        noise = z @ L.T\n",
     "        _sf_b = _sf_gen_state(generator)\n"
     "        z = torch.randn(block_number, block_size, generator=generator, device=generator.device).to(device=device)\n"
     "        _sf_log_draw(\"R6\", z, generator=generator, gen_before=_sf_b, generator_role=\"main\")\n"
     "        noise = z @ L.T\n"),

    ("R4 warp frame sigmas torch.rand(9) (:977)", PIPELINE,
     "        frame_sigmas = (\n"
     "            torch.rand(chunk_frames, device=device, generator=rand_generator) * (sigma_max - sigma_min) + sigma_min\n"
     "        ).to(dtype=warp_latents.dtype)\n",
     "        _sf_b = _sf_gen_state(rand_generator)\n"
     "        frame_sigmas = (\n"
     "            torch.rand(chunk_frames, device=device, generator=rand_generator) * (sigma_max - sigma_min) + sigma_min\n"
     "        ).to(dtype=warp_latents.dtype)\n"
     "        _sf_log_draw(\"R4\", frame_sigmas, generator=rand_generator, gen_before=_sf_b, generator_role=\"main\")\n"),

    ("R5 visibility-aware warp noise (:996)", PIPELINE,
     "            noise = randn_tensor(warp_latents.shape, generator=generator, device=device, dtype=warp_latents.dtype)\n"
     "            return sigmas * noise + (1.0 - sigmas) * warp_latents\n",
     "            _sf_b = _sf_gen_state(generator)\n"
     "            noise = randn_tensor(warp_latents.shape, generator=generator, device=device, dtype=warp_latents.dtype)\n"
     "            _sf_log_draw(\"R5\", noise, generator=generator, gen_before=_sf_b, generator_role=\"main\")\n"
     "            return sigmas * noise + (1.0 - sigmas) * warp_latents\n"),

    ("stage context in stage2_sample (:1442)", PIPELINE,
     "        for i_s in range(stage2_num_stages):\n",
     "        for i_s in range(stage2_num_stages):\n"
     "            _sf_set_stage(i_s)\n"),

    ("chunk context in __call__ loop (:2367)", PIPELINE,
     "        for k in _chunk_iter:\n",
     "        for k in _chunk_iter:\n"
     "            _sf_set_chunk(int(k))\n"),

    ("fork boundary hook before prepare_latents call (:2791)", PIPELINE,
     "            latents = self.prepare_latents(\n"
     "                batch_size,\n"
     "                num_channels_latents,\n"
     "                height,\n"
     "                width,\n"
     "                window_num_frames,\n",
     "            # [CausalFork SC1] chunk-boundary fork hook: snapshot/restore every long-lived\n"
     "            # generator reachable under the strict profile. No-op unless EVOKE_STRICT_FORK_JSON is set.\n"
     "            _sf_maybe_fork_boundary(int(k), _sf_collect_generators(generator, getattr(self, \"_geo_patchdrop_gen\", None)))\n"
     "            latents = self.prepare_latents(\n"
     "                batch_size,\n"
     "                num_channels_latents,\n"
     "                height,\n"
     "                width,\n"
     "                window_num_frames,\n"),

    ("import strict_fork (da3_cloud)", DA3CLOUD,
     "from .depth_backend import reset_stream as _reset_depth_stream\n",
     "from .depth_backend import reset_stream as _reset_depth_stream\n"
     "from ...strict_fork import gen_state_of as _sf_gen_state\n"
     "from ...strict_fork import log_draw as _sf_log_draw\n"),

    ("R7 zbuf covis subsample randint (da3_cloud.py:1486-87)", DA3CLOUD,
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
     "                         extra={\"source_gid\": int(g), \"covis_M\": int(M)})\n"),
]


def run(cmd, cwd=None, check=True):
    res = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out = res.stdout.decode("utf-8", errors="replace")
    err = res.stderr.decode("utf-8", errors="replace")
    if check and res.returncode != 0:
        raise SystemExit("command failed (%d): %s\n%s\n%s" % (res.returncode, " ".join(cmd), out, err))
    return res.returncode, out + ("\n[stderr]\n" + err if err.strip() and "--keep-stderr" in sys.argv else "")


def stage_trees():
    tarball = os.path.join(BASE, "sc1-pin.tar")
    run(["git", "-c", "core.autocrlf=false", "-C", PIN_CLONE, "archive", "--format=tar", "-o", tarball, "HEAD"])
    rc, rev = run(["git", "-C", PIN_CLONE, "rev-parse", "HEAD"])
    assert rev.strip() == PIN, "pin moved: %r" % rev.strip()
    import shutil as _sh
    for d in (P1, WK, FRESH):
        _sh.rmtree(d, ignore_errors=True)
        os.makedirs(d, exist_ok=True)
        run(["tar", "-xf", tarball, "-C", d])
    os.remove(tarball)


def apply_edits():
    cache = {}
    for label, rel, anchor, repl in EDITS:
        path = os.path.join(WK, rel)
        text = cache.setdefault(path, open(path, "r", encoding="utf-8", newline="").read())
        n = text.count(anchor)
        if n != 1:
            raise SystemExit("anchor not unique (%d hits) for %r" % (n, label))
        cache[path] = text.replace(anchor, repl, 1)
        print("[edit] %s -> %s" % (label, rel))
    for path, text in cache.items():
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(text)
    sf = open(SF_SRC, "r", encoding="utf-8").read().replace("\r\n", "\n")
    with open(os.path.join(WK, STRICT_FORK_REL), "w", encoding="utf-8", newline="") as fh:
        fh.write(sf)
    print("[new ] %s (%d lines)" % (STRICT_FORK_REL, sf.count("\n") + 1))
    tmp = tempfile.mkdtemp(prefix="sc1-pyc-")
    try:
        for i, rel in enumerate((PIPELINE, DA3CLOUD, STRICT_FORK_REL)):
            py_compile.compile(os.path.join(WK, rel), cfile=os.path.join(tmp, "c%d.pyc" % i), doraise=True)
            print("[pyOK] %s" % rel)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        for root, dirs, _files in os.walk(WK):
            for d in list(dirs):
                if d == "__pycache__":
                    shutil.rmtree(os.path.join(root, d), ignore_errors=True)


def build_patch():
    rc, stat = run(["git", "diff", "--no-index", "--stat", "--", "sc1-p1", "sc1-wk"], cwd=BASE, check=False)
    rc, diff = run(["git", "diff", "--no-index", "--", "sc1-p1", "sc1-wk"], cwd=BASE, check=False)
    if rc != 1:
        raise SystemExit("git diff --no-index returned %d (expected 1=differences); output:\n%s" % (rc, diff))
    def _tok_rest(tok):
        m = re.match(r"^[ab]/(?:sc1-p1|sc1-wk)/(.+)$", tok)
        return m.group(1) if m else None

    def fix_header(line):
        m = re.match(r"^diff --git (\S+) (\S+)$", line)
        if m:
            rest = _tok_rest(m.group(1)) or _tok_rest(m.group(2))
            return "diff --git a/%s b/%s" % (rest, rest)
        line = re.sub(r"^--- a/(?:sc1-p1|sc1-wk)/", "--- a/", line)
        line = re.sub(r"^\+\+\+ b/(?:sc1-p1|sc1-wk)/", "+++ b/", line)
        return line

    lines = []
    added = removed = files = 0
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            line = fix_header(line)
        elif line.startswith(("--- ", "+++ ")) and ("sc1-p1/" in line or "sc1-wk/" in line):
            line = fix_header(line)
        lines.append(line)
    patch = "\n".join(lines) + "\n"
    with open(PATCH_OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(patch)
    for line in lines:
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1
        elif line.startswith("diff --git "):
            files += 1
    print(stat)
    print("[patch] wrote %s: %d files touched, +%d / -%d hunk lines, %d total lines"
          % (PATCH_OUT, files, added, removed, len(lines) + 1))


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
    # strongest check: really apply onto FRESH and require byte-identity with the edited work tree
    run(["git", "-c", "core.autocrlf=false", "apply", PATCH_OUT], cwd=FRESH)
    import filecmp
    bad = []
    for rel in (PIPELINE, DA3CLOUD, STRICT_FORK_REL):
        if not filecmp.cmp(os.path.join(FRESH, rel), os.path.join(WK, rel), shallow=False):
            bad.append(rel)
    if bad:
        raise SystemExit("applied FRESH tree differs from WORK tree for %r" % bad)
    print("[verify] applied FRESH == edited WORK byte-for-byte for all 3 files")


def main():
    if "--skip-stage" not in sys.argv:
        stage_trees()
    apply_edits()
    build_patch()
    verify_patch()
    print("[done] gate G1-prep artifact ready.")


if __name__ == "__main__":
    main()