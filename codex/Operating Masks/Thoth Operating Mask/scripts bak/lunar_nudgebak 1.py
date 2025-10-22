from __future__ import annotations
import math, datetime as dt, json
from typing import Dict

SYNODIC = 29.530588853
REF_NEW_MOON = dt.datetime(2000, 1, 6, 18, 14, tzinfo=dt.timezone.utc)

PHASE_NAMES = [
    "New Moon","Waxing Crescent","First Quarter","Waxing Gibbous",
    "Full Moon","Waning Gibbous","Last Quarter","Waning Crescent"
]

def phase_fraction(ts: dt.datetime | None = None) -> float:
    if ts is None:
        ts = dt.datetime.now(dt.timezone.utc)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=dt.timezone.utc)
    delta_days = (ts - REF_NEW_MOON).total_seconds() / 86400.0
    return (delta_days % SYNODIC) / SYNODIC

def phase_name(frac: float) -> str:
    idx = int((frac * 8.0) + 0.5) % 8
    return PHASE_NAMES[idx]

def compute_nudges(frac: float) -> Dict[str, float]:
    name = phase_name(frac)
    n = {
        "severance":1.0,"harmonizers":1.0,"voice_clarity":1.0,"coherence":1.0,
        "integration":1.0,"translation":1.0,"grounding":1.0,"sealing":1.0,
        "call_harmonizers_bias":1.0
    }
    if name=="New Moon":
        n.update(severance=1.10,harmonizers=0.95,grounding=1.05)
    elif name=="Waxing Crescent":
        n.update(voice_clarity=1.05,translation=1.03)
    elif name=="First Quarter":
        n.update(coherence=1.05,grounding=1.03)
    elif name=="Waxing Gibbous":
        n.update(integration=1.05,coherence=1.02)
    elif name=="Full Moon":
        n.update(severance=0.90,harmonizers=1.10,call_harmonizers_bias=1.12)
    elif name=="Waning Gibbous":
        n.update(translation=1.05,integration=1.02)
    elif name=="Last Quarter":
        n.update(grounding=1.07,voice_clarity=0.98)
    elif name=="Waning Crescent":
        n.update(sealing=1.05,severance=1.03)
    return n

def sample(ts: dt.datetime | None = None):
    frac = phase_fraction(ts)
    return {
        "phase_fraction": frac,
        "phase_name": phase_name(frac),
        "nudges": compute_nudges(frac),
        "timestamp": (ts or dt.datetime.now(dt.timezone.utc)).isoformat(),
    }

if __name__ == "__main__":
    print(json.dumps(sample(), indent=2))