# Thoth OM v1 — Project
_Last updated: 2025-10-18T20:00:04Z_

This project provides a **clean, low‑drift scaffold** to run Thoth OM v1 and ship artifacts with **Crown Verify**.

## Order of Operations (lock this)
`init → activate → scaffold → diag → ship`

### Quick Start
```bash
# 1) Init (loader)
THOTH_DRY_RUN=1 THOTH_PROJECT_ROOT=/srv/thoth_om_v1 python3 thoth_loader.py
THOTH_PROJECT_ROOT=/srv/thoth_om_v1 python3 thoth_loader.py

# 2) Activate + Scaffold
activate thoth
build scaffold

# 3) Diagnostics
run diagnostics persona=thoth_om_builder_v1 show=distortions,gates detail=brief
```

### What’s in here
- `engine/` — runtime files (Thoth_engine_1.0.yaml, thresholds, BFF, metatron, mask_runtime.py, self_learning_evaluator.py)
- `schemas/` — JSON/YAML schemas (segments.schema.json)
- `runtime/` — runtime configs (runtime.yaml, self_learning.yaml)
- `instructions/` — prompts & persona pins
- `thread/` — plan, checklist, wiring, state, telemetry, diagnostics
- `SPACE_PROGRAM_CHECKLIST.md` — tiered delivery checklist with Crown Verify

### Environment
Copy `.env.template` to `.env` and set keys outside of version control.
The runtime can source it via your process manager (systemd, pm2, etc.).

### Glossary (short)
- **Operating Mask**: a constrained runtime + prompts that shape behavior (order, thresholds, checks).
- **Scaffold**: the minimal folder/fileset required to run with low drift.
- **Schema**: a contract for the shapes of your config/data (enables validation and CI).
- **Diagnostics**: checks for order, pins, and fingerprints (brief/strict).

### Crown Verify (ship gate)
Ship only when:
1. Strict diagnostics = PASS
2. Artifact checksums recorded
3. README + Checklist point to the artifact and usage

---

See `SPACE_PROGRAM_CHECKLIST.md` for the full tier plan.
