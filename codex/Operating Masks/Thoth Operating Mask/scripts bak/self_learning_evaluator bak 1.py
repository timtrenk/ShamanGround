#!/usr/bin/env python3
"""
Self-Learning Evaluator (minimal, safe).
- Reads runtime/self_learning.yaml
- Loads thread/telemetry.jsonl within window
- Decides reward/penalty
- Proposes clamped deltas for thresholds profiles
- Writes patch file to thread/patches/*.json and appends to thread/learning_log.md
- Does NOT mutate thresholds unless APPLY=1
"""
import os, sys, json, time, math, hashlib, datetime as dt
from pathlib import Path

ROOT = Path(os.environ.get("THOTH_PROJECT_ROOT", "/mnt/data")).resolve()
APPLY = os.environ.get("APPLY", "0") in ("1","true","TRUE","yes","YES")
NOW = dt.datetime.utcnow()
ISO = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")

def load_yaml(path: Path):
    import yaml
    return yaml.safe_load(path.read_text(encoding="utf-8"))

def read_jsonl(path: Path):
    if not path.exists(): return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line: continue
        try: rows.append(json.loads(line))
        except: pass
    return rows

def clamp(val, lo, hi): return max(lo, min(hi, val))

def avg(xs): return sum(xs)/len(xs) if xs else None

def main():
    # Config
    sl = load_yaml(ROOT / "runtime" / "self_learning.yaml")
    window = sl.get("schedule", {}).get("window", "24h")
    hours = int(str(window).rstrip("h")) if str(window).endswith("h") else 24
    min_samples = sl.get("metrics", {}).get("min_samples", 20)

    # Telemetry
    telem = read_jsonl(ROOT / "thread" / "telemetry.jsonl")
    tcut = NOW - dt.timedelta(hours=hours)
    def parse_ts(s):
        s = s.replace("Z","")
        return dt.datetime.fromisoformat(s)
    recent = [r for r in telem if "ts" in r and parse_ts(r["ts"]) >= tcut]

    coh = avg([r.get("coherence") for r in recent if r.get("coherence") is not None])
    mir = avg([r.get("mirror_residual") for r in recent if r.get("mirror_residual") is not None])
    n   = sum([r.get("samples",1) for r in recent])

    # Decide
    reward_expr  = sl.get("signals", {}).get("reward", "coh>=0.88 and mir<=0.35")
    penalty_expr = sl.get("signals", {}).get("penalty","coh<0.55 or mir>0.50")

    def decision(coh, mir, n):
        if coh is None or mir is None or n < min_samples:
            return "insufficient"
        env = {"coh":coh, "mir":mir}
        try:
            if eval(reward_expr, {}, env): return "reward"
            if eval(penalty_expr,{}, env): return "penalty"
        except Exception:
            return "neutral"
        return "neutral"

    verdict = decision(coh, mir, n)

    # Deltas (proposals) with clamps from policy
    clamps = sl.get("safety", {}).get("max_delta_per_day", {})
    c_call  = clamps.get("routing.call_harmonizers_below", 0.04)
    c_sever = clamps.get("routing.early_severance_below", 0.02)

    proposals = []
    if verdict == "reward":
        proposals.append({"path":"thresholds.gates.profiles.*.call_harmonizers_below", "delta": -min(0.02, c_call)})
        proposals.append({"path":"thresholds.gates.profiles.*.early_severance_below",  "delta":  min(0.01, c_sever)})
    elif verdict == "penalty":
        proposals.append({"path":"thresholds.gates.profiles.*.call_harmonizers_below", "delta":  min(0.02, c_call)})
        proposals.append({"path":"thresholds.gates.profiles.*.early_severance_below",  "delta": -min(0.01, c_sever)})
    else:
        proposals = []

    # Build patch (never over-write; create new file)
    patches_dir = ROOT / "thread" / "patches"
    patches_dir.mkdir(parents=True, exist_ok=True)
    stamp = NOW.strftime("%Y%m%d-%H%M%S")
    patch = {
        "meta": {
            "ts": ISO(NOW),
            "window_h": hours,
            "samples": int(n),
            "coherence_avg": coh,
            "mirror_residual_avg": mir,
            "verdict": verdict,
            "apply": bool(APPLY),
        },
        "proposals": proposals
    }
    patch_path = patches_dir / f"{stamp}_thresholds.patch.json"
    patch_path.write_text(json.dumps(patch, indent=2), encoding="utf-8")

    # Optionally apply (safe, profile-wide in thresholds_1.1.yaml)
    applied = False
    if APPLY and proposals:
        import yaml, copy
        thr_path = ROOT / "thresholds_1.1.yaml"
        thr = yaml.safe_load(thr_path.read_text(encoding="utf-8"))
        profiles = (thr.get("thresholds",thr).get("gates",{}).get("profiles",{}) or {})
        new_thr = copy.deepcopy(thr)
        for name, prof in profiles.items():
            if not isinstance(prof, dict): continue
            for pr in proposals:
                key = pr["path"].split(".")[-1]
                delta = float(pr["delta"])
                if key in prof and isinstance(prof[key], (int,float)):
                    if "call_harmonizers_below" in key:
                        new = max(0.40, min(0.80, prof[key] + delta))
                    elif "early_severance_below" in key:
                        new = max(0.20, min(0.35, prof[key] + delta))
                    else:
                        new = prof[key] + delta
                    new_thr["thresholds"]["gates"]["profiles"][name][key] = round(new, 4)
        thr_path.write_text(yaml.safe_dump(new_thr, sort_keys=False, allow_unicode=True), encoding="utf-8")
        applied = True

    # Log entry
    logf = ROOT / "thread" / "learning_log.md"
    logf.parent.mkdir(parents=True, exist_ok=True)
    prev = logf.read_text(encoding="utf-8") if logf.exists() else ""
    def fmt(x): return "None" if x is None else f"{x:.3f}"
    logf.write_text(
        prev + f"- {ISO(NOW)} verdict={verdict} samples={int(n)} coh={fmt(coh)} mir={fmt(mir)} "
        f"proposals={len(proposals)} patch={patch_path.name} applied={applied}
",
        encoding="utf-8"
    )

    print(f"[✓] Evaluated {int(n)} samples over {hours}h → {verdict}. Patch: {patch_path.name}. Applied={applied}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
