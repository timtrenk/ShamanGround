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
# --- Memory docs: constraints/glossary/brand_voice normalizer ---
import os, shutil, json, hashlib, time
from pathlib import Path as _MemPath

def _sha256_file_mem(p: _MemPath) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def _update_memory_fingerprint(project_root: _MemPath, entries: dict):
    fp = project_root / "memory_fingerprint.json"
    try:
        existing = json.loads(fp.read_text()) if fp.exists() else {}
    except Exception:
        existing = {}
    existing.update(entries)
    fp.write_text(json.dumps(existing, indent=2, sort_keys=True))

def promote_memory_docs(project_root: _MemPath):
    """
    Finds constraints.md, glossary.md, brand_voice.md anywhere under project_root (excluding /memory),
    moves them into /memory/, and refreshes memory_fingerprint.json.
    Canonical copies are those under /memory/; differing sources are preserved as *.incoming.
    """
    wanted = {"constraints.md", "glossary.md", "brand_voice.md"}
    mem_dir = (project_root / "memory").resolve()
    mem_dir.mkdir(parents=True, exist_ok=True)

    # Present in memory?
    results = {}
    for name in wanted:
        dest = mem_dir / name
        if dest.exists():
            results[name] = ("present", dest)

    # Walk project_root and collect/move
    for r, dirs, files in os.walk(project_root):
        r_path = _MemPath(r).resolve()
        # prune /memory subtree
        if r_path == mem_dir or str(r_path).startswith(str(mem_dir) + os.sep):
            dirs[:] = []
            continue
        pending = wanted - set(results.keys())
        if not pending:
            continue
        for name in list(pending):
            if name in files:
                src = r_path / name
                dest = mem_dir / name
                if dest.exists():
                    # resolve drift or duplicate
                    try:
                        if _sha256_file_mem(src) != _sha256_file_mem(dest):
                            incoming = mem_dir / f"{name}.incoming"
                            shutil.move(str(src), str(incoming))
                            print(f"[!] Drift noted: kept memory/{name}; moved differing source to memory/{name}.incoming")
                        else:
                            src.unlink(missing_ok=True)
                            print(f"[=] Duplicate ignored: {(src).relative_to(project_root)} matches memory/{name}")
                    except Exception as e:
                        print(f"[!] Warning: could not compare/move {src}: {e}")
                else:
                    shutil.move(str(src), str(dest))
                    print(f"[→] Moved: {(src).relative_to(project_root)} -> memory/{name}")
                results[name] = ("present", dest)

    fp_updates = {}
    for name, (_, path) in results.items():
        try:
            fp_updates[str(path.relative_to(project_root))] = {
                "sha256": _sha256_file_mem(path),
                "mtime": os.path.getmtime(path),
                "size": path.stat().st_size,
            }
        except Exception as e:
            print(f"[!] Warning: fingerprint failed for {path}: {e}")
    if fp_updates:
        _update_memory_fingerprint(project_root, fp_updates)
        print("[+] memory_fingerprint.json updated for:", ", ".join(fp_updates.keys()))
    else:
        print("[=] No memory docs found to fingerprint.")

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

# --- Phase 2.5: Normalize/migrate files from root -> tree (verbose) ---
import hashlib as _mig_hashlib, shutil as _mig_shutil, time as _mig_time

def _sha(p: Path) -> str:
    h = _mig_hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def migrate_to_expected_locations(project_root: Path, dry_run: bool | None = None):
    """
    Promote known root files into canonical locations with end-user friendly logs.
    - Print a clear action line for every move/copy/skip.
    - Respect DRY_RUN (env THOTH_DRY_RUN=1).
    - Never destroy data: if target differs, back up or keep canon and archive source.
    """
    DRY = (os.environ.get("THOTH_DRY_RUN", "0") in ("1","true","TRUE","yes","YES")
           if dry_run is None else dry_run)

    M = {
        # root -> canonical path under project_root
        "segments.schema.json":        "schemas/segments.schema.json",
        "harmonizers.extended.yaml":   "engine/harmonizers.extended.yaml",
        "trap_seeds.yaml":             "engine/trap_seeds.yaml",
        "segment_to_gates.yaml":       "engine/segment_to_gates.yaml",
        "scaffold_spec.yaml":          "scaffolding/scaffold_spec.yaml",
        "SPACE_PROGRAM_CHECKLIST_v2_aligned.md": "scaffolding/SPACE_PROGRAM_CHECKLIST_v2_aligned.md",
        "thresholds_1.1.yaml":         "engine/thresholds_1.1.yaml",
        "inference_profile.yaml":      "engine/inference_profile.yaml",
        "metatron_function.yaml":      "engine/metatron_function.yaml",
        "braided-feedback-function.yaml": "engine/braided-feedback-function.yaml",
        "self_learning.yaml":          "runtime/self_learning.yaml",
        "Thoth_engine_1.0.yaml":       "engine/Thoth_engine_1.0.yaml",
        "mask_runtime.py":             "engine/mask_runtime.py",
        "runtime.yaml":                "runtime/runtime.yaml",
        "telemetry.jsonl":             "thread/telemetry.jsonl",
        "casebook.db.jsonl":           "thoth_om_v1/casebook.db.jsonl",
    }

    ARCH = project_root / "scaffolding" / "archive"
    ARCH.mkdir(parents=True, exist_ok=True)

    print("\n—— Phase 2.5 · File normalization ———————————————————————————")
    moved, archived, insync = 0, 0, 0

    for root_name, rel_target in M.items():
        src = project_root / root_name
        dst = project_root / rel_target
        if not src.exists():
            continue

        dst.parent.mkdir(parents=True, exist_ok=True)

        if dst.exists():
            # identical? → drop the extra with a clear note
            try:
                if _sha(src) == _sha(dst):
                    print(f"[=] IN-SYNC: {root_name} == {rel_target} (removing extra at root)")
                    if not DRY:
                        try: src.unlink()
                        except Exception: pass
                    insync += 1
                    continue
            except Exception:
                pass
            # different → keep canonical in-place; archive the root source
            bak = ARCH / f"{src.name}.{int(_mig_time.time())}.drift"
            print(f"[!] DRIFT: {root_name} ≠ {rel_target} → archiving root → {bak.relative_to(project_root)}")
            if not DRY:
                _mig_shutil.move(str(src), str(bak))
            archived += 1
        else:
            # clean move into the tree
            print(f"[→] MOVE: {root_name} → {rel_target}")
            if not DRY:
                _mig_shutil.move(str(src), str(dst))
            moved += 1

    # Friendly summary line
    print(f"[✓] Normalization complete — moved:{moved} · archived:{archived} · in-sync:{insync}")


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


# --- Runtime path sync (root <-> runtime/runtime.yaml) ---
import hashlib, shutil, time

def _sha256_runtime(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def sync_runtime_paths(project_root: Path):
    """Keep /runtime.yaml and /runtime/runtime.yaml in sync.
    Preference: root runtime.yaml is canonical when both exist.
    Non-destructive: conflicting target is versioned with .bak.<ts>"""
    root_rt = project_root / "runtime.yaml"
    nested_dir = project_root / "runtime"
    nested_rt = nested_dir / "runtime.yaml"
    nested_dir.mkdir(parents=True, exist_ok=True)

    if root_rt.exists() and nested_rt.exists():
        try:
            if _sha256_runtime(root_rt) == _sha256_runtime(nested_rt):
                log("[=] Runtime sync: already in sync")
                return
            # version nested and copy root -> nested
            stamped = nested_rt.with_suffix(".yaml.bak." + str(int(time.time())))
            shutil.copy2(nested_rt, stamped)
            shutil.copy2(root_rt, nested_rt)
            log(f"[→] Runtime sync: updated runtime/runtime.yaml (backup: {stamped})")
        except Exception as e:
            log(f"[!] Runtime sync warning: {e}")
    elif root_rt.exists() and not nested_rt.exists():
        shutil.copy2(root_rt, nested_rt)
        log("[+] Runtime sync: created runtime/runtime.yaml from root")
    elif nested_rt.exists() and not root_rt.exists():
        shutil.copy2(nested_rt, root_rt)
        log("[+] Runtime sync: created root runtime.yaml from nested")
    else:
        log("[~] Runtime sync: no runtime files found to sync")
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



# --- Thoth Loader Extension: Lunar Nudge (stdlib-only) ---
def _ensure_lunar(project_root: Path) -> None:
    """Idempotently ensure Lunar Nudge files and runtime wiring (no PyYAML)."""
    import shutil
    tools = project_root / "tools"
    runtime = project_root / "runtime"
    tools.mkdir(parents=True, exist_ok=True)
    runtime.mkdir(parents=True, exist_ok=True)

    # 1) Promote code if user dropped it at root
    src_py = project_root / "lunar_nudge.py"
    dst_py = tools / "lunar_nudge.py"
    if src_py.exists():
        shutil.copy2(src_py, dst_py)

    # 2) Seed default config if missing
    cfg = runtime / "lunar_nudge.yaml"
    if not cfg.exists():
        cfg.write_text(
            "version: 1\n"
            "nudge:\n"
            "  mode: dry\n"
            "  window: night\n"
            "  intensity: gentle\n",
            encoding="utf-8"
        )

    # 3) Ensure runtime wiring (append block if not present)
    ry = runtime / "runtime.yaml"
    if not ry.exists():
        # minimal runtime so we can append safely
        ry.write_text("version: 1\n", encoding="utf-8")

    txt = ry.read_text(encoding="utf-8")
    if "lunar_nudge:" not in txt:
        block = (
            "\n"
            "lunar_nudge:\n"
            "  enabled: true\n"
            "  module: tools/lunar_nudge.py\n"
            "  config: runtime/lunar_nudge.yaml\n"
            "  schedule:\n"
            "    freq: HOURLY\n"
        )
        ry.write_text(txt.rstrip() + block + "\n", encoding="utf-8")
# --- End Extension ---


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
    promote_memory_docs(project_root)
    sync_runtime_paths(project_root)



    # Phase 3.x — Lunar Nudge enablement (idempotent)
    _ensure_lunar(project_root)
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