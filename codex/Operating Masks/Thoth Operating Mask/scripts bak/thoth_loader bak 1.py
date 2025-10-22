#!/usr/bin/env python3
"""
Thoth OM — Python Loader (safe + idempotent)

What this does:
1) Detects the project root (default: /mnt/data).
2) Verifies/creates expected folders (non-destructive).
3) Wires known file paths (engine, thresholds, schemas, memory).
4) **Ensures memory/prompts.md exists** (your pinned prompts store).
5) **Registers prompts.md in memory_fingerprint.json** (recomputes combined hash).
6) Prints a concise status summary and exits.

Design goals:
- Idempotent: safe to run multiple times.
- Non-destructive: never deletes or overwrites your existing content.
- Minimal dependencies: stdlib only.
"""

from __future__ import annotations
import os, sys, json, hashlib, time
from pathlib import Path

# --- Thoth Loader Safety Helpers (no-drift) ---
from pathlib import Path as _PathAlias  # alias guard if needed
import datetime as _dt

# Project root (defaults to /mnt/data)
PROJECT_ROOT = Path(os.environ.get("THOTH_PROJECT_ROOT", "/mnt/data")).resolve()

# Dry-run guard (export THOTH_DRY_RUN=1 to preview)
DRY_RUN = os.environ.get("THOTH_DRY_RUN", "0") in ("1","true","TRUE","yes","YES")

def under_root(*parts: str) -> Path:
    return PROJECT_ROOT.joinpath(*parts)

def safe_mkdir(p: Path) -> None:
    if DRY_RUN:
        print(f"[DRY] mkdir -p {p}")
        return
    p.mkdir(parents=True, exist_ok=True)

def safe_write_text(path: Path, content: str, encoding: str = "utf-8") -> bool:
    old = None
    try:
        old = path.read_text(encoding=encoding)
    except FileNotFoundError:
        pass
    if old == content:
        print(f"[OK] unchanged: {path}")
        return False
    if DRY_RUN:
        print(f"[DRY] write: {path} (len={len(content)})")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding=encoding)
    print(f"[WROTE] {path} (len={len(content)})")
    return True
def migrate_to_expected_locations(root: Path) -> None:
    """
    Move root-level engine/schema files into engine/ and schemas/ if found.
    Idempotent. Honors DRY_RUN.
    """
    moves = [
        (root / "Thoth_engine_1.0.yaml",         root / "engine"  / "Thoth_engine_1.0.yaml"),
        (root / "metatron_function.yaml",         root / "engine"  / "metatron_function.yaml"),
        (root / "braided-feedback-function.yaml", root / "engine"  / "braided-feedback-function.yaml"),
        (root / "segments.schema.json",           root / "schemas" / "segments.schema.json"),
        (root / "runtime.yaml",               root / "runtime" / "runtime.yaml"),
        (root / "self_learning.yaml",         root / "runtime" / "self_learning.yaml"),

    ]
    for src, dst in moves:
        if src.exists() and not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            if DRY_RUN:
                log(f"[DRY] move: {src} -> {dst}")
            else:
                src.replace(dst)
                log(f"[→] Moved: {src.name} -> {dst}")
        elif dst.exists():
            log(f"[=] Already placed: {dst}")

def migrate_self_learning_tools(root: Path) -> None:
    """
    Move root-level self-learning tools into engine/ if found.
    Idempotent. Honors DRY_RUN.
    """
    pairs = [
        (root / "self_learning_evaluator.py", root / "engine" / "self_learning_evaluator.py"),
        (root / "mask_runtime.py",            root / "engine" / "mask_runtime.py"),
    ]
    for src, dst in pairs:
        if src.exists() and not dst.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            if DRY_RUN:
                log(f"[DRY] move: {src} -> {dst}")
            else:
                src.replace(dst)
                log(f"[→] Moved: {src.name} -> {dst}")
        elif dst.exists():
            log(f"[=] Already placed: {dst}")

# ---------- Config ----------
DEFAULT_ROOT = "/mnt/data"
EXPECTED_DIRS = [
    "memory",
    "engine",
    "schemas",
    "runtime",   # ← make sure this is present
]

# Files we only *reference* if present (we never create these here)
KNOWN_FILES = {
    "engine/Thoth_engine_1.0.yaml": "engine file",
    "engine/metatron_function.yaml": "metatron catalog",
    "engine/braided-feedback-function.yaml": "braided feedback",
    "thresholds_1.1.yaml": "thresholds",
    "schemas/segments.schema.json": "segments schema",
    "trap_seeds.yaml": "trap seeds",
    "runtime/runtime.yaml": "runtime",
    "runtime/self_learning.yaml": "self-learning policy",
    "memory/constraints.md": "constraints",
    "memory/glossary.md": "glossary",
    "memory/brand_voice.md": "brand voice",
    "memory_fingerprint.json": "memory manifest",

    # self-learning additions
    "engine/self_learning_evaluator.py": "self-learning evaluator",
    "engine/mask_runtime.py": "per-turn runtime hook",
    "thread/telemetry.jsonl": "telemetry stream",
}


PROMPTS_MD_REL = "memory/prompts.md"
MANIFEST_REL   = "memory_fingerprint.json"

# ---------- Helpers ----------
def log(msg: str) -> None:
    print(msg, flush=True)

def sha256sum(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def ensure_dirs(root: Path) -> None:
    for rel in ("instructions", "thread", "scaffolding", "memory", "runtime", "tools", "engine", "schemas"):
        d = root / rel
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            log(f"[+] Created dir: {d}")
        else:
            log(f"[=] Dir exists:  {d}")

def read_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}

def write_json(p: Path, obj: dict) -> None:
    p.write_text(json.dumps(obj, indent=2))

def recompute_combined_manifest_hash(memory_files: list[dict]) -> str:
    pairs = sorted([(it.get("name",""), it.get("sha256","")) for it in memory_files])
    concat = "".join(name + sha for name, sha in pairs).encode("utf-8")
    return hashlib.sha256(concat).hexdigest()

# ---------- Core steps ----------
def init_prompts_md(root: Path) -> Path:
    """Create memory/prompts.md if missing; return its path."""
    prompts_path = root / PROMPTS_MD_REL
    if not prompts_path.exists():
        prompts_path.write_text(
            "# Thoth OM – Prompts Memory\n\n"
            "## Pinned Prompts\n"
            "(Add new prompts at the top. Keep them concise and reusable.)\n\n"
            "### Template\n"
            "**Title:** <give it a short name>  \n"
            "**Tags:** [tag1, tag2]  \n"
            "**Prompt:**  \n"
            "<your prompt here>\n\n"
            "---\n",
            encoding="utf-8"
        )
        log(f"[+] Created {prompts_path}")
    else:
        log(f"[=] Found {prompts_path}")
    return prompts_path

def update_manifest_with_prompts(root: Path, prompts_path: Path) -> None:
    manifest_path = root / MANIFEST_REL
    if not manifest_path.exists():
        log("[!] memory_fingerprint.json not found — skipping manifest update.")
        return

    manifest = read_json(manifest_path)
    memory_files = manifest.get("memory_files", [])
    by_name = {it.get("name"): i for i, it in enumerate(memory_files)}

    entry = {
        "path": str(prompts_path),
        "name": "prompts.md",
        "size": prompts_path.stat().st_size,
        "sha256": sha256sum(prompts_path),
    }

    if "prompts.md" in by_name:
        memory_files[by_name["prompts.md"]] = entry
        log("[=] Updated prompts.md entry in manifest.")
    else:
        memory_files.append(entry)
        log("[+] Added prompts.md to manifest.")

    manifest["memory_files"] = memory_files
    manifest["combined_manifest_sha256"] = recompute_combined_manifest_hash(memory_files)
    manifest["timestamp_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    write_json(manifest_path, manifest)
    log(f"[=] Manifest updated: {manifest_path}")
    log(f"[=] combined_manifest_sha256: {manifest['combined_manifest_sha256']}")

def summarize(root: Path) -> None:
    log("\n--- Thoth Loader Summary ---")
    # Directories
    for rel in EXPECTED_DIRS:
        exists = (root / rel).exists()
        log(f"DIR  {'OK ' if exists else 'MISS'}  {rel}/")

    # Files
    for rel, label in KNOWN_FILES.items():
        exists = (root / rel).exists()
        log(f"FILE {'OK ' if exists else 'MISS'}  {rel:<35}  ({label})")

    # Prompts presence
    prompts_ok = (root / PROMPTS_MD_REL).exists()
    log(f"PROMPTS {'OK ' if prompts_ok else 'MISS'}  {PROMPTS_MD_REL}")


# === Internal Scaffolding (Step 5) ===

# === Self-Learning Policy Seeding (New User Safe Defaults) ===
def ensure_self_learning_policy(root: Path) -> Path:
    """
    Create /runtime/self_learning.yaml with safe defaults if missing.
    Does not overwrite if present. Returns the policy path.
    """
    sl_dir = root / "runtime"
    sl_dir.mkdir(parents=True, exist_ok=True)
    sl_path = sl_dir / "self_learning.yaml"
    if not sl_path.exists():
        sl_path.write_text(
            "version: 1.0\n"
            "label: \"Thoth OM — Self-Learning Policy\"\n"
            "enabled: true\n"
            "schedule:\n"
            "  update_interval: daily\n"
            "  window: 24h\n"
            "signals:\n"
            "  reward: \"coherence >= 0.88 and mirror_residual <= 0.35\"\n"
            "  penalty: \"coherence < 0.55 or mirror_residual > 0.50\"\n"
            "metrics:\n"
            "  source: \"runtime_telemetry\"\n"
            "  min_samples: 20\n"
            "adjustments:\n"
            "  - when: reward\n"
            "    do:\n"
            "      - \"routing.call_harmonizers_below -= 0.02 clamp[0.40,0.70]\"\n"
            "      - \"routing.early_severance_below += 0.01 clamp[0.20,0.35]\"\n"
            "  - when: penalty\n"
            "    do:\n"
            "      - \"routing.force_serial_on_incoherent = true\"\n"
            "      - \"routing.call_harmonizers_below += 0.02 clamp[0.45,0.80]\"\n"
            "safety:\n"
            "  require_manifest_ok: true\n"
            "  dry_run: true\n"
            "  max_delta_per_day:\n"
            "    routing.call_harmonizers_below: 0.04\n"
            "    routing.early_severance_below: 0.02\n"
            "logging:\n"
            "  file: \"/mnt/data/thread/learning_log.md\"\n"
            "  include_snapshot_of: [\"thresholds\", \"routing\", \"safety\"]\n"
            "  keep_last: 50\n",
            encoding="utf-8"
        )
        print(f"[+] Created {sl_path}")
    else:
        print(f"[=] Self-learning policy detected: {sl_path}")
    return sl_path
# === End Self-Learning Policy Seeding ===


def ensure_scaffolding(root: Path) -> None:
    """Create minimal internal scaffolding files if missing (idempotent)."""
    # Directories
    dirs = [
        root / "instructions",
        root / "thread",
        root / "scaffolding"
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    # Instructions files
    instr_prompts = root / "instructions" / "prompts.md"
    if not instr_prompts.exists():
        instr_prompts.write_text(
            "# Thoth OM — Activation Prompts\n\n"
            "- `activate thoth persona=thoth_om_builder_v1`\n"
            "- `run diagnostics`\n"
            "- `build checklist scope=\"current objective\" depth=12`\n", encoding="utf-8")
        print(f"[+] Created {instr_prompts}")

    instr_persona = root / "instructions" / "persona.thoth_om_builder.yaml"
    if not instr_persona.exists():
        instr_persona.write_text(
            "persona:\n"
            "  id: thoth_om_builder_v1\n"
            "  label: \"Strategic Architect (Ni–Te)\"\n"
            "  description: \"Systems-minded builder; concise, coherent, execution-first.\"\n"
            "  sliders:\n"
            "    structure: 88\n"
            "    speed: 70\n"
            "    verbosity: 45\n", encoding="utf-8")
        print(f"[+] Created {instr_persona}")

    # Thread files
    plan = root / "thread" / "plan.md"
    if not plan.exists():
        plan.write_text("# Plan\n\n- Define objective\n- Risks\n- Milestones\n", encoding="utf-8")
        print(f"[+] Created {plan}")

    checklist = root / "thread" / "checklist.md"
    if not checklist.exists():
        checklist.write_text("# Checklist\n\n- [ ] Initialize\n- [ ] Build\n- [ ] Verify\n", encoding="utf-8")
        print(f"[+] Created {checklist}")

    wiring = root / "thread" / "wiring.yaml"
    if not wiring.exists():
        wiring.write_text("wiring:\n  gates: 12\n  harmonizers: default\n", encoding="utf-8")
        print(f"[+] Created {wiring}")

    state = root / "thread" / "state.json"
    if not state.exists():
        state.write_text("{\"coherence\": null, \"last_run\": null}\n", encoding="utf-8")
        print(f"[+] Created {state}")

    logf = root / "thread" / "scaffold_log.md"
    if not logf.exists():
        logf.write_text("# Scaffold Log\n\n- Initialized.\n", encoding="utf-8")
        print(f"[+] Created {logf}")

    # Scaffolding folder seed
    sc_notes = root / "scaffolding" / "README.md"
    if not sc_notes.exists():
        sc_notes.write_text("# Scaffolding\n\nPut templates and checklists here.\n", encoding="utf-8")
        print(f"[+] Created {sc_notes}")

    # Telemetry stream seed (empty JSONL file)
    telemetry = root / "thread" / "telemetry.jsonl"
    if not telemetry.exists():
        telemetry.parent.mkdir(parents=True, exist_ok=True)
        telemetry.write_text("", encoding="utf-8")
        print(f"[+] Created {telemetry}")
# === End Internal Scaffolding ===


def main():
    # 1) Resolve project root
    project_root = Path(os.environ.get("THOTH_PROJECT_ROOT", DEFAULT_ROOT)).resolve()
    log(f"[*] Project root: {project_root}")

    # 2) Ensure dirs
    ensure_dirs(project_root)

    # 2.5) Normalize file locations so checks never mismatch
    migrate_to_expected_locations(project_root)

    # Normalize self-learning tools locations
    migrate_self_learning_tools(project_root)

    # 3) Non-destructive checks for known files
    for rel, label in KNOWN_FILES.items():
        p = project_root / rel
        if p.exists():
            continue
        # We do NOT create these here; just note absence
        # log(f"[~] Optional/expected missing: {rel} ({label})")

    # 4) Ensure prompts.md exists
    prompts_path = init_prompts_md(project_root)

    # 5) Register prompts.md in memory_fingerprint.json (if present)
    update_manifest_with_prompts(project_root, prompts_path)

    # Step 5 — Internal scaffolding
    ensure_scaffolding(project_root)

    # Seed self-learning policy for new users
    ensure_self_learning_policy(project_root)

    # Step 4 — Self-learning policy detection (optional log)
    sl_path = project_root / "runtime" / "self_learning.yaml"
    if sl_path.exists():
        print(f"[=] Self-learning policy detected: {sl_path}")
    else:
        print("[~] Self-learning policy not found (optional).")


    # Optional: run self-learning evaluator in DRY mode on load when flagged
    if os.environ.get("RUN_EVAL_ON_LOAD") in ("1","true","TRUE","yes","YES"):
        eval_path = project_root / "engine" / "self_learning_evaluator.py"
        if eval_path.exists():
            os.system(f"THOTH_PROJECT_ROOT={project_root} APPLY=0 python3 {eval_path}")
        else:
            log("[~] RUN_EVAL_ON_LOAD set, but engine/self_learning_evaluator.py not found.")


    # 6) Print summary
    summarize(project_root)

    log("\n[✓] Thoth loader completed.")

if __name__ == "__main__":
    main()
