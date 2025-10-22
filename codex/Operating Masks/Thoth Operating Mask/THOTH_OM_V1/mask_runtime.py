# engine/mask_runtime.py — unified
# - Telemetry logging (finish_turn)
# - Lunar Nudge Hook (compute/apply)
# - Threshold adjust helper + simple CLI

from __future__ import annotations
from pathlib import Path
import os, sys, json, datetime as dt

ROOT = Path(os.environ.get("THOTH_PROJECT_ROOT", "/mnt/data")).resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# --- Telemetry (from self_learning_evaluator) ---
try:
    from self_learning_evaluator import log_telemetry
except Exception:
    # Fallback: write minimal telemetry if evaluator isn't importable
    def log_telemetry(coherence: float, mirror_residual: float, samples: int = 1):
        rec = {
            "timestamp": dt.datetime.utcnow().isoformat()+"Z",
            "coherence": coherence,
            "mirror_residual": mirror_residual,
            "samples": samples,
            "source": "mask_runtime_fallback"
        }
        tp = ROOT/"thread"/"telemetry.jsonl"
        tp.parent.mkdir(parents=True, exist_ok=True)
        with open(tp, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec)+"\n")

def finish_turn(coherence: float, mirror_residual: float, samples: int = 1):
    \"\"\"Call this at the end of a turn to log telemetry.\"\"\"
    log_telemetry(coherence, mirror_residual, samples)

# --- Lunar Nudge Hook (optional) ---
def _load_yaml(path):
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        try:
            import json
            return json.loads(open(path, "r", encoding="utf-8").read())
        except Exception:
            return {}

def compute_lunar_nudges(project_root):
    from pathlib import Path
    cfg_path = Path(project_root)/"runtime"/"lunar_nudge.yaml"
    if not cfg_path.exists():
        return None
    cfg = _load_yaml(cfg_path)
    if not cfg or not cfg.get("enabled", False):
        return None
    try:
        from .lunar_nudge import phase_fraction, phase_name, compute_nudges
    except Exception:
        from lunar_nudge import phase_fraction, phase_name, compute_nudges
    frac = phase_fraction()
    n = compute_nudges(frac)
    caps = cfg.get("caps", {"min":0.85,"max":1.15})
    mn, mx = float(caps.get("min",0.85)), float(caps.get("max",1.15))
    n = {k: max(mn, min(mx, float(v))) for k,v in n.items()}
    # Optional logging toggle
    payload = {"enabled": True, "mode": cfg.get("mode","on_input"),
               "phase_fraction": frac, "phase_name": phase_name(frac), "nudges": n}
    if cfg.get("log", True):
        tp = Path(project_root)/"thread"/"telemetry.jsonl"
        tp.parent.mkdir(parents=True, exist_ok=True)
        with open(tp, "a", encoding="utf-8") as f:
            f.write(json.dumps({"timestamp": dt.datetime.utcnow().isoformat()+"Z",
                                "event": "lunar_nudge", **payload}) + "\n")
    return payload

def apply_lunar_nudges(thresholds: dict, nudges: dict) -> dict:
    import copy
    t = copy.deepcopy(thresholds)
    n = nudges.get("nudges", {}) if nudges else {}
    def bump(val, key):
        try:
            m = float(n.get(key, 1.0))
            if isinstance(val, (int,float)):
                return val * m
        except Exception:
            pass
        return val
    # Meta-gate coherence
    if "meta_gate" in t and "coherence" in t["meta_gate"]:
        c = t["meta_gate"]["coherence"]
        for k in ["warn_below","sever_below","stabilize_above"]:
            if k in c: c[k] = bump(c[k], "coherence")
    # Gate triggers
    if "gates" in t and "triggers" in t["gates"]:
        g = t["gates"]["triggers"]
        if "early_severance_below" in g:
            g["early_severance_below"] = bump(g["early_severance_below"], "severance")
        if "call_harmonizers_below" in g:
            bias = n.get("call_harmonizers_bias",1.0)
            try:
                bias = float(bias)
            except Exception:
                bias = 1.0
            g["call_harmonizers_below"] = g["call_harmonizers_below"] / max(0.5, bias)
    return t

def adjust_thresholds_with_lunar(thresholds: dict, project_root: str | Path = ROOT) -> dict:
    ln = compute_lunar_nudges(project_root)
    if not ln: return thresholds
    mode = ln.get("mode","on_input")
    # Currently same behavior for on_input/per_gate; caller decides frequency
    return apply_lunar_nudges(thresholds, ln)

if __name__ == "__main__":
    import argparse, json, sys
    ap = argparse.ArgumentParser(description="Mask runtime utils")
    ap.add_argument("--log-turn", nargs=2, metavar=("COH","MIR"), help="log a telemetry turn")
    ap.add_argument("--samples", type=int, default=1)
    ap.add_argument("--show-lunar", action="store_true", help="print current lunar nudges")
    ap.add_argument("--adjust-thresholds", metavar="PATH", help="load thresholds (json/yaml) and print adjusted json")
    args = ap.parse_args()

    if args.log_turn:
        coh, mir = map(float, args.log_turn)
        finish_turn(coh, mir, args.samples)
        print(f"[+] Logged turn: coh={coh} mir={mir} samples={args.samples} -> {ROOT/'thread'/'telemetry.jsonl'}")

    if args.show_lunar:
        ln = compute_lunar_nudges(ROOT)
        print(json.dumps(ln or {"enabled": False}, indent=2))

    if args.adjust_thresholds:
        p = Path(args.adjust_thresholds)
        if not p.exists():
            print(f"ERR: thresholds file not found: {p}", file=sys.stderr); sys.exit(2)
        # Read as YAML first; fallback to JSON
        data = None
        try:
            import yaml
            data = yaml.safe_load(p.read_text())
        except Exception:
            data = json.loads(p.read_text())
        adj = adjust_thresholds_with_lunar(data, ROOT)
        print(json.dumps(adj, indent=2))
