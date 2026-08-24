#!/usr/bin/env python3
"""Static + optional live verifier for the CausalFork OpenCode company kit."""
from pathlib import Path
import argparse
import json
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ROOT = [
    "AGENTS.md", "COMPANY.md", "RESEARCH.md", "SPEC.md", "EXPERIMENTS.md",
    "CLAIMS.md", "DECISIONS.md", "RUNBOOK.md", "opencode.json",
]
KNOWN_PERMISSION_KEYS = {
    "read", "edit", "glob", "grep", "list", "bash", "task",
    "external_directory", "todowrite", "question", "webfetch", "websearch",
    "lsp", "doom_loop", "skill",
}
REQUIRED_AGENTS = {
    "orchestrator", "research-lead", "world-model-researcher",
    "causal-metrics-researcher", "data-rl-researcher", "gpu-engineer",
    "experimenter", "reviewer", "novelty-red-team", "demo-director",
}
REQUIRED_SKILLS = {
    "research-paper-audit", "upstream-repo-audit", "colab-gpu-debug",
    "oom-recovery", "experiment-reproduction", "world-model-evaluation",
    "causal-counterfactual-eval", "evidence-gate", "demo-export",
    "git-worktree-isolation",
}
REQUIRED_COMMANDS = {"company-check", "research-preflight", "red-team", "gate", "delegate"}


def die(msg: str):
    print(f"ERROR: {msg}")
    raise SystemExit(1)


def frontmatter(text: str, path: Path):
    if not re.match(r"^---\r?\n", text):
        die(f"missing YAML frontmatter: {path.relative_to(ROOT)}")
    end = re.search(r"\r?\n---\r?\n", text[4:])
    if not end:
        die(f"unterminated YAML frontmatter: {path.relative_to(ROOT)}")
    return text[4 : 4 + end.start()]


def strip_jsonc(text: str) -> str:
    out, i, in_str = [], 0, False
    while i < len(text):
        c = text[i]
        if in_str:
            if c == "\\" and i + 1 < len(text):
                out.append(text[i : i + 2]); i += 2; continue
            if c == '"':
                in_str = False
            out.append(c); i += 1; continue
        if c == '"':
            in_str = True; out.append(c); i += 1; continue
        if c == "/" and i + 1 < len(text) and text[i + 1] == "/":
            j = text.find("\n", i)
            i = len(text) if j < 0 else j
            continue
        out.append(c); i += 1
    return "".join(out)


def load_config(path: Path):
    try:
        return json.loads(strip_jsonc(path.read_text(encoding="utf-8")))
    except Exception as e:
        die(f"{path.name} is not valid JSON/JSONC: {e}")


def field(fm: str, key: str):
    m = re.search(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$", fm)
    return m.group(1).strip().strip('"\'') if m else None


def static_check():
    for rel in REQUIRED_ROOT:
        if not (ROOT / rel).is_file():
            die(f"missing {rel}")

    cfg = load_config(ROOT / "opencode.json")
    if cfg.get("default_agent") != "orchestrator":
        die("default_agent must be orchestrator")
    perm = cfg.get("permission")
    if not isinstance(perm, dict):
        die("top-level 'permission' must be an object keyed by tool name")
    if "permissions" in cfg or "warming" in cfg:
        die("legacy keys 'permissions'/'warming' detected; use the 'permission' object form")
    for tool, rule in perm.items():
        if isinstance(rule, dict):
            for pattern in rule:
                if not isinstance(pattern, str) or not pattern.strip():
                    die(f"permission.{tool} has an invalid pattern: {pattern!r}")
    unknown = set(perm) - KNOWN_PERMISSION_KEYS
    if unknown:
        print(f"WARNING: non-standard permission tools (schema tolerates them): {sorted(unknown)}")

    agent_dir = ROOT / ".opencode/agents"
    found_agents = set()
    for p in agent_dir.glob("*.md"):
        found_agents.add(p.stem)
        fm = frontmatter(p.read_text(encoding="utf-8"), p)
        if not field(fm, "description"):
            die(f"agent missing description: {p.name}")
        mode = field(fm, "mode")
        if mode not in {"primary", "subagent", "all"}:
            die(f"invalid agent mode {mode!r}: {p.name}")
        if "permissions:" in fm:
            die(f"legacy 'permissions' list in {p.name}; use the 'permission' map")
    missing = REQUIRED_AGENTS - found_agents
    if missing:
        die(f"missing agents: {sorted(missing)}")

    skill_dir = ROOT / ".opencode/skills"
    found_skills = set()
    for d in skill_dir.iterdir():
        if not d.is_dir():
            continue
        p = d / "SKILL.md"
        if not p.is_file():
            die(f"skill directory missing SKILL.md: {d.name}")
        fm = frontmatter(p.read_text(encoding="utf-8"), p)
        name = field(fm, "name")
        desc = field(fm, "description")
        if name != d.name:
            die(f"skill name mismatch: dir={d.name}, frontmatter={name}")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name or ""):
            die(f"invalid skill id: {name}")
        if not desc:
            die(f"skill missing description: {name}")
        found_skills.add(name)
    missing = REQUIRED_SKILLS - found_skills
    if missing:
        die(f"missing skills: {sorted(missing)}")

    cmd_dir = ROOT / ".opencode/commands"
    found_commands = set()
    for p in cmd_dir.glob("*.md"):
        fm = frontmatter(p.read_text(encoding="utf-8"), p)
        if not field(fm, "description"):
            die(f"command missing description: {p.name}")
        found_commands.add(p.stem)
    missing = REQUIRED_COMMANDS - found_commands
    if missing:
        die(f"missing commands: {sorted(missing)}")

    print(f"root files: {len(REQUIRED_ROOT)} OK")
    print("permission: object form OK")
    print(f"agents: {len(found_agents)} OK")
    print(f"skills: {len(found_skills)} OK")
    print(f"commands: {len(found_commands)} OK")
    print("COMPANY_STATIC_OK")


def live_check():
    exe = shutil.which("opencode")
    if not exe:
        die("opencode not found on PATH; static kit is fine, install/upgrade OpenCode then rerun --live")
    ver = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=20)
    print("opencode version:", (ver.stdout or ver.stderr).strip())
    if ver.returncode != 0:
        die("opencode --version failed")
    agents = subprocess.run([exe, "agent", "list"], cwd=ROOT, capture_output=True, text=True, timeout=60)
    if agents.returncode != 0:
        print(agents.stdout)
        print(agents.stderr, file=sys.stderr)
        die("opencode agent list failed")
    text = agents.stdout + "\n" + agents.stderr
    missing = [a for a in REQUIRED_AGENTS if a not in text]
    if missing:
        die(f"OpenCode did not discover agents: {missing}")
    print("OpenCode discovered all required company agents")
    print("COMPANY_LIVE_OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", action="store_true", help="also query installed OpenCode")
    args = ap.parse_args()
    static_check()
    if args.live:
        live_check()

if __name__ == "__main__":
    main()
