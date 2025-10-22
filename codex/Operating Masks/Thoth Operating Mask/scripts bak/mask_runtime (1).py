# Thoth OM mask runtime shim\n\n
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
    return {"enabled": True, "mode": cfg.get("mode","on_input"),
            "phase_fraction": frac, "phase_name": phase_name(frac), "nudges": n}

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
    if "meta_gate" in t and "coherence" in t["meta_gate"]:
        c = t["meta_gate"]["coherence"]
        for k in ["warn_below","sever_below","stabilize_above"]:
            if k in c: c[k] = bump(c[k], "coherence")
    if "gates" in t and "triggers" in t["gates"]:
        g = t["gates"]["triggers"]
        if "early_severance_below" in g:
            g["early_severance_below"] = bump(g["early_severance_below"], "severance")
        if "call_harmonizers_below" in g:
            bias = float(n.get("call_harmonizers_bias",1.0))
            g["call_harmonizers_below"] = g["call_harmonizers_below"] / max(0.5, bias)
    return t
# --- End Lunar Nudge Hook ---
