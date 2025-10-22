#!/usr/bin/env python3
"""
Thoth OM — Python Loader (no-drift, idempotent, hardened)

What this does (single run):
0) Detects project root (env THOTH_PROJECT_ROOT or /mnt/data).
1) Ensures directory skeleton exists (non-destructive).
2) *Staging pass*: if core files exist anywhere under root but not at ROOT, copy them to ROOT first.
3) *Normalization pass*: move files from ROOT to canonical locations (engine/, runtime/, schemas/, scaffolding/, memory/).
   - HARDENED: never overwrite a file that already exists in the canonical location.
4) Ensures memory/prompts.md exists and computes memory_fingerprint.json (combined SHA-256).
5) Ensures thread telemetry file exists.
6) Validates/patches minimal lunar nudge wiring in runtime/runtime.yaml if present.
7) Prints a concise status report and exits.
"""
from __future__ import annotations
import os, sys, json, hashlib, time, shutil
from pathlib import Path

# ----------------- constants -----------------
PROJECT_ROOT = Path(os.environ.get("THOTH_PROJECT_ROOT", "/mnt/data")).resolve()

DIRS = [
    "instructions", "thread", "scaffolding", "memory",
    "runtime", "tools", "engine", "schemas"
]

# Files we want to stage at ROOT first if they exist elsewhere under the tree
STAGE_FIRST = [
    # schemas / specs
    "segments.schema.json",
    "scaffold_spec.yaml",
    # engine configs
    "harmonizers.extended.yaml",
    "trap_seeds.yaml",
    "segment_to_gates.yaml",
    "thresholds_1.1.yaml",
    "metatron_function.yaml",
    "braided-feedback-function.yaml",
    # engine code
    "mask_runtime.py",
    "self_learning_evaluator.py",
    "lunar_nudge.py",
    # runtime configs (also mirror root copies)
    "runtime.yaml",
    "self_learning.yaml",
    "lunar_nudge.yaml",
    # memory docs (root mirrors for convenience)
    "constraints.md",
    "glossary.md",
    "brand_voice.md",
    "prompts.md",
]

# Canonical destinations relative to PROJECT_ROOT
CANON = {
    "segments.schema.json": ("schemas", "segments.schema.json"),
    "scaffold_spec.yaml": ("scaffolding", "scaffold_spec.yaml"),
    "harmonizers.extended.yaml": ("engine", "harmonizers.extended.yaml"),
    "trap_seeds.yaml": ("engine", "trap_seeds.yaml"),
    "segment_to_gates.yaml": ("engine", "segment_to_gates.yaml"),
    "thresholds_1.1.yaml": ("engine", "thresholds_1.1.yaml"),
    "metatron_function.yaml": ("engine", "metatron_function.yaml"),
    "braided-feedback-function.yaml": ("engine", "braided-feedback-function.yaml"),
    "mask_runtime.py": ("engine", "mask_runtime.py"),
    "self_learning_evaluator.py": ("engine", "self_learning_evaluator.py"),
    "lunar_nudge.py": ("engine", "lunar_nudge.py"),
    "runtime.yaml": ("runtime", "runtime.yaml"),
    "self_learning.yaml": ("runtime", "self_learning.yaml"),
    "lunar_nudge.yaml": ("runtime", "lunar_nudge.yaml"),
    "constraints.md": ("memory", "constraints.md"),
    "glossary.md": ("memory", "glossary.md"),
    "brand_voice.md": ("memory", "brand_voice.md"),
    "prompts.md": ("memory", "prompts.md"),
}

MEMORY_DOCS = [
    PROJECT_ROOT / "memory" / "constraints.md",
    PROJECT_ROOT / "memory" / "glossary.md",
    PROJECT_ROOT / "memory" / "brand_voice.md",
    PROJECT_ROOT / "memory" / "prompts.md",
]

FINGERPRINT_FILE = PROJECT_ROOT / "memory_fingerprint.json"

# ----------------- helpers -----------------
def _print(msg: str):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()

def ensure_dirs():
    _print(f"[*] Project root: {PROJECT_ROOT}")
    for d in DIRS:
        p = PROJECT_ROOT / d
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)
            _print(f"[+] Created dir: {p}")
    return True

def _rglob_first(name: str) -> Path | None:
    for p in PROJECT_ROOT.rglob(name):
        return p
    return None

def stage_files_to_root():
    staged = []
    missing = []
    # special mirrors from canonical locations if root copy is missing
    special_mirrors = [
        ("runtime/runtime.yaml", "runtime.yaml"),
        ("runtime/self_learning.yaml", "self_learning.yaml"),
        ("runtime/lunar_nudge.yaml", "lunar_nudge.yaml"),
        ("engine/mask_runtime.py", "mask_runtime.py"),
        ("engine/self_learning_evaluator.py", "self_learning_evaluator.py"),
        ("engine/lunar_nudge.py", "lunar_nudge.py"),
        ("memory/constraints.md", "constraints.md"),
        ("memory/glossary.md", "glossary.md"),
        ("memory/brand_voice.md", "brand_voice.md"),
        ("memory/prompts.md", "prompts.md"),
    ]
    # mirror if present
    for src_rel, dst_rel in special_mirrors:
        src = PROJECT_ROOT / src_rel
        dst = PROJECT_ROOT / dst_rel
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)
            staged.append(f"STAGED {dst_rel} from {src_rel} -> {dst_rel}")
    # general stage pass
    for fname in STAGE_FIRST:
        root_target = PROJECT_ROOT / fname
        if root_target.exists():
            continue
        src = _rglob_first(fname)
        if src:
            shutil.copy2(src, root_target)
            staged.append(f"STAGED {fname} from {src.relative_to(PROJECT_ROOT)} -> {fname}")
        else:
            missing.append(fname)
    if staged:
        _print("—— Phase 1 · Root staging ————————————————————————————")
        for s in staged:
            _print(f"[→] {s}")
    return staged, missing

def normalize_moves():
    _print("—— Phase 2 · Normalization ————————————————————————————")
    for src_name, (dst_dir, dst_name) in CANON.items():
        src = PROJECT_ROOT / src_name
        dst = PROJECT_ROOT / dst_dir / dst_name
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                _print(f"[skip] {dst_dir}/{dst_name} exists; leaving canonical file intact.")
            else:
                shutil.move(str(src), str(dst))
                _print(f"[→] MOVE: {src_name} → {dst_dir}/{dst_name}")

def ensure_memory_docs():
    # create prompts.md if missing
    prompts = PROJECT_ROOT / "memory" / "prompts.md"
    if not prompts.exists():
        prompts.write_text("# Thoth OM — Prompts\n\n- Activate: `activate thoth persona=thoth_om_builder_v1`\n", encoding="utf-8")
        _print("[+] Created memory/prompts.md (seed)")
    # compute fingerprint
    sha = hashlib.sha256()
    present = []
    for f in MEMORY_DOCS:
        if f.exists():
            data = f.read_bytes()
            sha.update(data)
            present.append(f.name)
    FINGERPRINT_FILE.write_text(json.dumps({
        "updated": int(time.time()),
        "files": present,
        "sha256": sha.hexdigest()
    }, indent=2), encoding="utf-8")
    _print("PROMPTS OK   memory/prompts.md")
    _print("FINGERPRINT  memory_fingerprint.json")

def ensure_thread_telemetry():
    telem = PROJECT_ROOT / "thread" / "telemetry.jsonl"
    if not telem.exists():
        telem.write_text("", encoding="utf-8")
        _print("[+] Created thread/telemetry.jsonl")

def patch_runtime_for_lunar():
    rt = PROJECT_ROOT / "runtime" / "runtime.yaml"
    if not rt.exists():
        _print("RUNTIME WARN runtime/runtime.yaml not found; lunar wiring skipped.")
        return
    content = rt.read_text(encoding="utf-8", errors="ignore")
    if ("lunar_nudge" in content) and ("lunar_nudge.yaml" in content):
        _print("RUNTIME OK   lunar nudge already referenced.")
        return
    patch = """
# — lunar nudge wiring —
lunar_nudge:
  enabled: true
  policy_file: "/mnt/data/runtime/lunar_nudge.yaml"
""".lstrip("\n")
    content += ("\n" + patch)
    rt.write_text(content, encoding="utf-8")
    _print("RUNTIME FIX  added lunar nudge reference to runtime/runtime.yaml")

def status_check():
    checks = [
        ("schemas/segments.schema.json", "segments schema"),
        ("engine/trap_seeds.yaml", "trap seeds"),
        ("engine/harmonizers.extended.yaml", "harmonizers"),
        ("engine/segment_to_gates.yaml", "segment→gates"),
        ("engine/thresholds_1.1.yaml", "thresholds"),
        ("engine/metatron_function.yaml", "metatron function"),
        ("engine/braided-feedback-function.yaml", "braided feedback"),
        ("engine/mask_runtime.py", "mask runtime"),
        ("engine/self_learning_evaluator.py", "self-learning evaluator"),
        ("engine/lunar_nudge.py", "lunar nudge code"),
        ("runtime/runtime.yaml", "runtime"),
        ("runtime/self_learning.yaml", "self-learning policy"),
        ("runtime/lunar_nudge.yaml", "lunar nudge policy"),
        ("memory/constraints.md", "constraints"),
        ("memory/glossary.md", "glossary"),
        ("memory/brand_voice.md", "brand voice"),
        ("memory/prompts.md", "prompts"),
        ("thread/telemetry.jsonl", "telemetry stream"),
        ("memory_fingerprint.json", "memory manifest"),
    ]
    for rel, label in checks:
        p = PROJECT_ROOT / rel
        if p.exists():
            _print(f"FILE OK   {rel:<35} ({label})")
        else:
            _print(f"FILE MISS {rel:<35} ({label})")

def main():
    ensure_dirs()
    stage_files_to_root()
    normalize_moves()
    ensure_memory_docs()
    ensure_thread_telemetry()
    patch_runtime_for_lunar()
    status_check()
    _print("\n[✓] Thoth loader completed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
