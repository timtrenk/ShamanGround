#!/usr/bin/env python3
"""
Thoth OM — Python Loader (no-drift) with --theater mode

Adds:
- --theater : cinematic output (ASCII banners, timers, hash diffs, progress ticks)
- -v/--verbose, --trace, --dry-run as before
"""

from __future__ import annotations
from pathlib import Path
import os, sys, json, hashlib, time, shutil
from datetime import datetime

PROJECT_ROOT = Path(os.environ.get("THOTH_PROJECT_ROOT", "/mnt/data")).resolve()

TEMPLATE_PROMPTS = """# Thoth OM — prompts.md
# This file pins your activation prompts and quick commands.
# Add your activation script, diagnostics, and adapters here.
"""

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def mtime(p: Path) -> float:
    try:
        return p.stat().st_mtime
    except FileNotFoundError:
        return 0.0


def write_if_missing(path: Path, content: str, verbose=False, dry=False):
    if path.exists():
        if verbose:
            print(f"= keep   {path} (exists)")
        return False
    if verbose:
        print(f"+ create {path}")
    if not dry:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return True

def ensure_dir(path: Path, verbose=False, dry=False):
    if not dry:
        path.mkdir(parents=True, exist_ok=True)
    if verbose:
        print(f"📁 ensure {path}" + (" (dry-run)" if dry else ""))

def copy_into(src: Path, dst: Path, verbose=False, dry=False, trace=False, theater=False, prefer_newer=False):
    if not src.exists():
        if verbose:
            print(f"! skip   {src} (missing)")
        return False, None, None, None
    if not dry:
        dst.parent.mkdir(parents=True, exist_ok=True)
    src_hash = sha256_file(src) if (trace or theater) else None
    if dst.exists():
        dst_hash = sha256_file(dst) if (trace or theater) else None
        if verbose:
            print(f"= keep   {dst} (exists)")
        if theater and src_hash and dst_hash:
            eq = "✓ match" if src_hash == dst_hash else "≠ diff"
            print(f"   ↳ hash src:{src_hash[:10]} dst:{dst_hash[:10]}  {eq}")
        # prefer-newer resolution if requested and hashes differ
        if prefer_newer and (src_hash is not None) and (dst_hash is not None) and src_hash != dst_hash:
            src_newer = mtime(src) > mtime(dst)
            if src_newer:
                if verbose:
                    print(f"→ stage  {src.name} -> {dst} [prefer-newer: src newer]" + (" (dry-run)" if dry else ""))
                if not dry:
                    shutil.copy2(src, dst)
                return True, src_hash, dst_hash, "prefer-newer-src"
            else:
                if verbose:
                    print(f"= keep   {dst} [prefer-newer: dst newer]")
                return False, src_hash, dst_hash, "prefer-newer-dst"
        return False, src_hash, dst_hash, None
    if verbose:
        print(f"→ stage  {src.name} -> {dst}" + (" (dry-run)" if dry else ""))
    if not dry:
        shutil.copy2(src, dst)
    # after copy, get dst hash if real write
    dst_hash = sha256_file(dst) if (trace and dst.exists()) else None
    if theater and src_hash and dst_hash:
        eq = "✓ match" if src_hash == dst_hash else "≠ diff"
        print(f"   ↳ hash src:{src_hash[:10]} dst:{dst_hash[:10]}  {eq}")
    return True, src_hash, dst_hash, None

def pretty_header(title: str, theater=False):
    if theater:
        bar = "═" * max(20, len(title) + 6)
        print(f"\n╔{bar}╗")
        print(f"║  ⟁ {title}".ljust(len(bar)+1) + "║")
        print(f"╚{bar}╝")
    else:
        bar = "─" * max(8, len(title) + 2)
        print(f"\n⟁ {title}\n{bar}")

class StepTimer:
    def __init__(self, name:str, theater=False):
        self.name = name
        self.theater = theater
    def __enter__(self):
        self.t0 = time.time()
        if self.theater:
            print(f"⏱  {self.name} ...")
        return self
    def __exit__(self, exc_type, exc, tb):
        dt = time.time() - self.t0
        if self.theater:
            print(f"    done in {dt:.3f}s")

def progress_tick(i:int, n:int, label:str):
    width = 24
    filled = int(width * (i+1)/n) if n else width
    bar = "█"*filled + "░"*(width-filled)
    print(f"   [{bar}] {i+1}/{n} {label}", end="\r")
    if i+1==n:
        print()  # newline

def main(argv):
    import argparse
    ap = argparse.ArgumentParser(description="Thoth OM — Loader (theater-capable, no-drift)")
    ap.add_argument("-v","--verbose", action="store_true", help="Show each major step")
    ap.add_argument("--trace", action="store_true", help="Show file-level actions and hashes")
    ap.add_argument("--dry-run", action="store_true", help="Plan only; no writes")
    ap.add_argument("--theater", action="store_true", help="Cinematic output with banners/timers/hash diffs")
    ap.add_argument("--prefer-newer", action="store_true", help="When hashes differ, keep the newer file (default behavior)")
    args = ap.parse_args(argv)

    verbose = args.verbose or args.trace or args.theater
    trace = args.trace
    dry = args.dry_run
    theater = args.theater
    # default: prefer newer unless explicitly disabled later
    prefer_newer = getattr(args, 'prefer_newer', False) or True

    start = time.time()

    pretty_header("Session", theater=theater)
    print(f"time: {datetime.now().isoformat(sep=' ', timespec='seconds')}")
    print(f"root: {PROJECT_ROOT}")
    print(f"mode: {'DRY-RUN' if dry else 'WRITE'}  verbose:{verbose}  trace:{trace}  theater:{theater}  prefer_newer:{prefer_newer}")

    # Layout
    pretty_header("Ensure Directory Layout", theater=theater)
    dirs = {
        "engine": PROJECT_ROOT / "engine",
        "runtime": PROJECT_ROOT / "runtime",
        "scripts": PROJECT_ROOT / "scripts",
        "schemas": PROJECT_ROOT / "schemas",
        "scaffolding": PROJECT_ROOT / "scaffolding",
        "memory": PROJECT_ROOT / "memory",
        "thread": PROJECT_ROOT / "thread",
        "thoth_om_v1": PROJECT_ROOT / "thoth_om_v1",
    }
    with StepTimer("mkdirs", theater=theater):
        for k,p in dirs.items():
            ensure_dir(p, verbose=verbose, dry=dry)

    # Manifest (source->dest)
    pretty_header("Stage Known Files", theater=theater)
    manifest = [
        # engine files
        (PROJECT_ROOT/"thresholds_1.1.yaml",          dirs["engine"]/ "thresholds_1.1.yaml"),
        (PROJECT_ROOT/"trap_seeds.yaml",               dirs["engine"]/ "trap_seeds.yaml"),
        (PROJECT_ROOT/"braided-feedback-function.yaml",dirs["engine"]/ "braided-feedback-function.yaml"),
        (PROJECT_ROOT/"segment_to_gates.yaml",         dirs["engine"]/ "segment_to_gates.yaml"),
        (PROJECT_ROOT/"metatron_function.yaml",        dirs["engine"]/ "metatron_function.yaml"),
        (PROJECT_ROOT/"harmonizers.extended.yaml",     dirs["engine"]/ "harmonizers.extended.yaml"),
        (PROJECT_ROOT/"Thoth_engine_1.0.yaml",         dirs["engine"]/ "Thoth_engine_1.0.yaml"),
        # runtime
        (PROJECT_ROOT/"runtime.yaml",                  dirs["runtime"]/ "runtime.yaml"),
        (PROJECT_ROOT/"self_learning.yaml",            dirs["runtime"]/ "self_learning.yaml"),
        (PROJECT_ROOT/"inference_profile.yaml",        dirs["runtime"]/ "inference_profile.yaml"),
        (PROJECT_ROOT/"lunar_nudge.yaml",              dirs["runtime"]/ "lunar_nudge.yaml"),
        # scripts
        (PROJECT_ROOT/"mask_runtime.py",               dirs["scripts"]/ "mask_runtime.py"),
        (PROJECT_ROOT/"lunar_nudge.py",                dirs["scripts"]/ "lunar_nudge.py"),
        (PROJECT_ROOT/"self_learning_evaluator.py",    dirs["scripts"]/ "self_learning_evaluator.py"),
        (PROJECT_ROOT/"thoth_loader.py",               dirs["scripts"]/ "thoth_loader.py"),
        # scaffolding + schemas
        (PROJECT_ROOT/"scaffold_spec.yaml",            dirs["schemas"]/ "scaffold_spec.yaml"),
        (PROJECT_ROOT/"segments.schema.json",          dirs["schemas"]/ "segments.schema.json"),
        (PROJECT_ROOT/"SPACE_PROGRAM_CHECKLIST_v2_aligned.md", dirs["scaffolding"]/ "SPACE_PROGRAM_CHECKLIST_v2_aligned.md"),
        # memory
        (PROJECT_ROOT/"brand_voice.md",                dirs["memory"]/ "brand_voice.md"),
        (PROJECT_ROOT/"constraints.md",                dirs["memory"]/ "constraints.md"),
        (PROJECT_ROOT/"glossary.md",                   dirs["memory"]/ "glossary.md"),
        (PROJECT_ROOT/"memory_fingerprint.json",       dirs["memory"]/ "memory_fingerprint.json"),
    ]
    staged = 0
    kept = 0
    with StepTimer("stage", theater=theater):
        n = len(manifest)
        for i,(src,dst) in enumerate(manifest):
            if theater:
                progress_tick(i, n, src.name)
            created, src_h, dst_h, _ = copy_into(src, dst, verbose=True, dry=dry, trace=trace, theater=theater, prefer_newer=prefer_newer, prefer_newer=prefer_newer)
            if created: staged += 1
            else: kept += 1

    # Memory pins
    pretty_header("Seed Memory Pins", theater=theater)
    prompts_md = dirs["memory"] / "prompts.md"
    with StepTimer("prompts", theater=theater):
        created_prompts = write_if_missing(prompts_md, TEMPLATE_PROMPTS, verbose=True, dry=dry)

    # Fingerprint recompute
    pretty_header("Recompute Memory Fingerprint", theater=theater)
    memory_parts = [prompts_md, dirs["memory"]/ "constraints.md", dirs["memory"]/ "glossary.md", dirs["memory"]/ "brand_voice.md"]
    with StepTimer("fingerprint", theater=theater):
        combined = hashlib.sha256()
        for p in memory_parts:
            if p.exists():
                combined.update(p.read_bytes())
                if verbose:
                    print(f"∴ add {p.name}")
            else:
                if verbose:
                    print(f"∴ skip {p.name} (missing)")
        fp = combined.hexdigest()
        if verbose:
            print(f"→ memory_fingerprint: {fp}")
        if not dry:
            (dirs["memory"]/ "memory_fingerprint.json").write_text(json.dumps({"memory_fingerprint": fp, "timestamp": datetime.utcnow().isoformat()+"Z"}, indent=2))

    # Telemetry + casebook
    pretty_header("Ensure Telemetry + Casebook", theater=theater)
    with StepTimer("telemetry", theater=theater):
        telemetry = PROJECT_ROOT / "thread" / "telemetry.jsonl"
        if not telemetry.exists() and not dry:
            telemetry.write_text("", encoding="utf-8")
        print(f"= ensure {telemetry}" + (" (dry-run)" if dry else ""))

        casebook_dir = PROJECT_ROOT / "thoth_om_v1"
        ensure_dir(casebook_dir, verbose=verbose, dry=dry)
        casebook = casebook_dir / "casebook.db.jsonl"
        if not casebook.exists() and not dry:
            casebook.write_text("", encoding="utf-8")
        print(f"= ensure {casebook}" + (" (dry-run)" if dry else ""))

    # Runtime patch
    pretty_header("Patch runtime.yaml (if needed)", theater=theater)
    with StepTimer("patch-runtime", theater=theater):
        runtime_path = dirs["runtime"]/ "runtime.yaml"
        if runtime_path.exists():
            y = runtime_path.read_text(encoding="utf-8")
            changed = False
            if 'casebook.db.jsonl' not in y:
                y += "\n# cross-thread memory IO\nmemory_io:\n  load.jsonl:\n    file: \"/mnt/data/thoth_om_v1/casebook.db.jsonl\"\n    record: \"${thread.casebook}\"\n  save.jsonl:\n    file: \"/mnt/data/thoth_om_v1/casebook.db.jsonl\"\n    record: \"${thread.casebook}\"\n"
                changed = True
                if verbose: print("→ add casebook IO block")
            if 'lunar_nudge' not in y:
                y += "\n# lunar nudge policy hook\nlunar_nudge:\n  enabled: true\n  policy: \"/mnt/data/runtime/lunar_nudge.yaml\"\n"
                changed = True
                if verbose: print("→ add lunar_nudge hook")
            if changed and not dry:
                runtime_path.write_text(y, encoding="utf-8")
                print(f"✓ patched {runtime_path.name}")
            else:
                print(f"= no patch required")
        else:
            print("! runtime.yaml missing — skipped patch")

    # Summary
    pretty_header("Summary", theater=theater)
    elapsed = time.time() - start
    print(json.dumps({
        "root": str(PROJECT_ROOT),
        "staged_new_files": staged,
        "kept_existing_files": kept,
        "prompts_created": bool(created_prompts),
        "elapsed_sec": round(elapsed, 3),
        "dry_run": dry,
        "trace": trace,
        "theater": theater
    }, indent=2))

    if theater:
        print("\n╭────────────────────────────────────────────────────────╮")
        print("│  ⟁  All systems preflight complete.                   │")
        print("│      Run without --dry-run to commit changes.         │")
        print("╰────────────────────────────────────────────────────────╯")
    else:
        print("\n⟁ Done. Use -v or --trace for more detail.")

if __name__ == "__main__":
    main(sys.argv[1:])
