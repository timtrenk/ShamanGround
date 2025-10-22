# -*- coding: utf-8 -*-
"""
lunar_nudge.py — fast, dependency‑free lunar phase + gentle nudge policy

Design goals
- Zero deps · UTC‑safe · branch‑light · numerically stable
- Compatible with existing hooks: phase_fraction(), phase_name(), compute_nudges()
- Deterministic CLI for testing and telemetry

Phase model
- Mean synodic month = 29.530588853 days
- Reference new moon: 2000‑01‑06 18:14:00Z (Meeus)
- Fraction ∈ [0,1): 0=new · 0.5=full

Public API
- phase_fraction(ts: datetime|None) -> float
- phase_name(frac: float) -> str
- compute_nudges(frac: float) -> dict[str,float]
- sample(ts: datetime|None) -> dict (phase+nudges snapshot)

CLI
- `python lunar_nudge.py`        → JSON snapshot now
- `python lunar_nudge.py --iso 2025-10-19T12:00:00Z`
- `python lunar_nudge.py --caps 0.9 1.1`
"""
from __future__ import annotations

import math
import sys
import json
import datetime as dt
from typing import Dict, Tuple

# --- Constants (module‑level for speed) ---
SYNODIC: float = 29.530588853
# Known new moon (Meeus); timezone aware (UTC)
REF_NEW_MOON = dt.datetime(2000, 1, 6, 18, 14, tzinfo=dt.timezone.utc)

PHASE_NAMES = (
    "New Moon",
    "Waxing Crescent",
    "First Quarter",
    "Waxing Gibbous",
    "Full Moon",
    "Waning Gibbous",
    "Last Quarter",
    "Waning Crescent",
)

__all__ = [
    "SYNODIC",
    "REF_NEW_MOON",
    "PHASE_NAMES",
    "phase_fraction",
    "phase_name",
    "compute_nudges",
    "sample",
]

# --- Core phase functions ---
def _to_utc(ts: dt.datetime | None) -> dt.datetime:
    if ts is None:
        return dt.datetime.now(dt.timezone.utc)
    if ts.tzinfo is None:
        # assume naive time is UTC to avoid slow local conversions
        return ts.replace(tzinfo=dt.timezone.utc)
    return ts.astimezone(dt.timezone.utc)

def phase_fraction(ts: dt.datetime | None = None) -> float:
    """
    Compute mean synodic phase fraction in [0,1).
    Fast path: uses modulo on total seconds to avoid large float loss.
    """
    t = _to_utc(ts)
    delta_s: float = (t - REF_NEW_MOON).total_seconds()
    # Convert to days with a single division; keep precision
    d: float = delta_s / 86400.0
    # Python's % is well‑defined for floats; ensures [0,SYNODIC)
    return (d % SYNODIC) / SYNODIC

def phase_name(frac: float) -> str:
    # Map to 8 bins symmetrically; add 0.5 step then wrap
    # int(x) is faster than floor for positive values
    i = int(frac * 8.0 + 0.5) & 7  # bitwise wrap for speed
    return PHASE_NAMES[i]

# --- Nudge policy (gentle, clampable, branch‑light) ---
def _clamp(x: float, lo: float, hi: float) -> float:
    return hi if x > hi else (lo if x < lo else x)

def _nudges_for(name: str) -> Dict[str, float]:
    # Defaults: 1.0 (no change)
    n = {
        "severance": 1.0,
        "harmonizers": 1.0,
        "voice_clarity": 1.0,
        "coherence": 1.0,
        "integration": 1.0,
        "translation": 1.0,
        "grounding": 1.0,
        "sealing": 1.0,
        "call_harmonizers_bias": 1.0,
    }
    # Phase‑specific micro‑biases (keep deltas small; stacking stays tame)
    if name == "New Moon":
        n["severance"] = 1.10; n["harmonizers"] = 0.95; n["grounding"] = 1.05
    elif name == "Waxing Crescent":
        n["voice_clarity"] = 1.05; n["translation"] = 1.03
    elif name == "First Quarter":
        n["coherence"] = 1.05; n["grounding"] = 1.03
    elif name == "Waxing Gibbous":
        n["integration"] = 1.05; n["coherence"] = 1.02
    elif name == "Full Moon":
        n["severance"] = 0.90; n["harmonizers"] = 1.10; n["call_harmonizers_bias"] = 1.12
    elif name == "Waning Gibbous":
        n["translation"] = 1.05; n["integration"] = 1.02
    elif name == "Last Quarter":
        n["grounding"] = 1.07; n["voice_clarity"] = 0.98
    else:  # Waning Crescent
        n["sealing"] = 1.05; n["severance"] = 1.03
    return n

def compute_nudges(frac: float, caps: Tuple[float, float] | None = None) -> Dict[str, float]:
    """
    Return nudges keyed by conceptual levers. Optional (lo,hi) caps.
    """
    n = _nudges_for(phase_name(frac))
    if caps:
        lo, hi = float(caps[0]), float(caps[1])
        for k, v in n.items():
            n[k] = _clamp(float(v), lo, hi)
    return n

def sample(ts: dt.datetime | None = None, caps: Tuple[float, float] | None = None) -> Dict[str, object]:
    f = phase_fraction(ts)
    return {
        "phase_fraction": f,
        "phase_name": phase_name(f),
        "nudges": compute_nudges(f, caps=caps),
        "timestamp": _to_utc(ts).isoformat(),
    }

# --- CLI ---
def _parse_iso(s: str) -> dt.datetime:
    # Accept 'Z' suffix; avoid heavy parsing libs
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return dt.datetime.fromisoformat(s)

if __name__ == "__main__":
    # Tiny, fast CLI for testing + telemetry sampling
    ts = None
    caps = None
    i = 1
    argv = sys.argv
    n = len(argv)
    while i < n:
        a = argv[i]
        if a == "--iso" and i + 1 < n:
            ts = _parse_iso(argv[i + 1]); i += 2; continue
        if a == "--caps" and i + 2 < n:
            caps = (float(argv[i + 1]), float(argv[i + 2])); i += 3; continue
        if a in ("-h", "--help"):
            print("usage: python lunar_nudge.py [--iso 2025-10-19T12:00:00Z] [--caps 0.9 1.1]")
            sys.exit(0)
        i += 1

    print(json.dumps(sample(ts, caps=caps), indent=2))
