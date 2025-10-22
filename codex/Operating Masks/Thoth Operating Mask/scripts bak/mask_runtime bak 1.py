# engine/mask_runtime.py
from pathlib import Path
import os, sys, json, datetime as dt

ROOT = Path(os.environ.get("THOTH_PROJECT_ROOT", "/mnt/data")).resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import the per-turn logger from your evaluator
from self_learning_evaluator import log_telemetry

def finish_turn(coherence: float, mirror_residual: float, samples: int = 1):
    """Call this at the end of a turn to log telemetry."""
    log_telemetry(coherence, mirror_residual, samples)

# Optional: simple CLI to log a turn quickly
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Mask runtime turn logger (telemetry writer)")
    ap.add_argument("coherence", type=float, help="coherence score 0..1")
    ap.add_argument("mirror_residual", type=float, help="mirror residual 0..1 (lower is better)")
    ap.add_argument("--samples", type=int, default=1, help="sample count (default 1)")
    args = ap.parse_args()
    finish_turn(args.coherence, args.mirror_residual, args.samples)
    print(f"[+] Logged turn: coh={args.coherence} mir={args.mirror_residual} samples={args.samples} -> {ROOT/'thread'/'telemetry.jsonl'}")
