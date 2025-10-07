#!/usr/bin/env python3
"""
Local test harness for Codex Engine 2.1 Braid Core.
Simulates a single run using local YAML schemas.
"""

import yaml, uuid, time, random
from datetime import datetime
from pathlib import Path

# ────────────────────────────────────────────────────────────────
# Utility
# ────────────────────────────────────────────────────────────────
def load_yaml(path):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def rand(n=1.0):
    return round(random.random() * n, 3)

# ────────────────────────────────────────────────────────────────
# Load engine config
# ────────────────────────────────────────────────────────────────
codex_dir = Path(__file__).parent / "codex"
engine = load_yaml(codex_dir / "engine_2.1_braid.yaml")
meta_gate = load_yaml(codex_dir / "meta-gate-fields.yaml")
harmonizers = load_yaml(codex_dir / "harmonizers.yaml")
bff = load_yaml(codex_dir / "braided-feedback-function.yaml")

print(f"\n🧠 Loaded Codex Engine 2.1 — {engine['name']}")
print(f"Flow mode default: {engine['defaults']['flow_mode']}")
print("─────────────────────────────────────────────")

# ────────────────────────────────────────────────────────────────
# Mock input data
# ────────────────────────────────────────────────────────────────
session_id = str(uuid.uuid4())
run_context = {
    "session_id": session_id,
    "timestamp": datetime.utcnow().isoformat(),
    "vault_user": "test_user",
    "glyph_id": "GLYPH-001",
    "flow_mode": engine["defaults"]["flow_mode"]
}

trap_snapshot = [
    {"id": f"TRAP-{i}", "severity": rand(), "family": f"FAM-{i%12}"}
    for i in range(5)
]
family_activity = [rand() for _ in range(12)]

# ────────────────────────────────────────────────────────────────
# Simulate Meta-Gate stage
# ────────────────────────────────────────────────────────────────
print("⚙️  Meta-Gate composing gate plan...")
gate_plan = [{"gate_id": f"G{i+1}", "sensitivity": rand(), "cooldown": rand(2)} for i in range(7)]
time.sleep(0.3)

# Fake harmonizer activity seeds
harmonizer_states = []
for axis in harmonizers["harmonizers"]["axes"]:
    harmonizer_states.append({
        "axis_name": axis,
        "lift": rand(0.2),
        "attenuation": rand(0.2),
        "residual_pre": rand(),
        "residual_post": rand()
    })

# ────────────────────────────────────────────────────────────────
# Simulate Harmonizer balance
# ────────────────────────────────────────────────────────────────
print("🎛  Harmonizers balancing field...")
time.sleep(0.2)
field_axes = [rand() for _ in range(7)]

# ────────────────────────────────────────────────────────────────
# Simulate BFF synthesis
# ────────────────────────────────────────────────────────────────
print("🧵  BFF synthesizing braid signature...")
axial_coherence = rand()
radial_balance = rand()
clarity = rand()
braid_quality = random.choice(["excellent", "stable", "shaky", "incoherent"])

bff_signature = {
    "axial_coherence": axial_coherence,
    "radial_balance": radial_balance,
    "clarity": clarity,
    "braid_quality": braid_quality,
    "return_note": "mock run complete"
}

learning_deltas = {
    "sensitivity_shift": round((random.random() - 0.5) * 0.1, 3),
    "aggressiveness_shift": round((random.random() - 0.5) * 0.1, 3),
    "applied_now": run_context["flow_mode"] == "resonant"
}

# ────────────────────────────────────────────────────────────────
# Create run receipt
# ────────────────────────────────────────────────────────────────
run_receipt = {
    "session_id": session_id,
    "timestamp": run_context["timestamp"],
    "flow_mode": run_context["flow_mode"],
    "traps_detected": len(trap_snapshot),
    "families_active": sum(1 for f in family_activity if f > 0.5),
    "gates_fired": [g["gate_id"] for g in gate_plan],
    "harmonizers_applied": [h["axis_name"] for h in harmonizer_states[:4]],
    "bff_signature": bff_signature,
    "learning_deltas": learning_deltas,
    "duration_ms": int(random.uniform(500, 900)),
    "cost_units": round(random.uniform(0.05, 0.12), 3)
}

# ────────────────────────────────────────────────────────────────
# Output summary
# ────────────────────────────────────────────────────────────────
print("\n🧩  RUN RECEIPT")
print("─────────────────────────────────────────────")
for k, v in run_receipt.items():
    print(f"{k}: {v}")

# Write to logs/
logs = Path(__file__).parent / "logs"
logs.mkdir(exist_ok=True)
out_file = logs / f"run_receipt_{session_id[:8]}.yaml"
with open(out_file, "w", encoding="utf-8") as f:
    yaml.safe_dump(run_receipt, f)

print(f"\n✅  Mock run complete. Receipt saved to {out_file}")
