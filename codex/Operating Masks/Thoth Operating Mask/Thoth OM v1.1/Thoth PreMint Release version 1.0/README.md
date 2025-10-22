# ⟁ Thoth OM — Builder Edition (Mobile/Desktop)

## What’s an AI Operating Mask?
An **Operating Mask (OM)** is a lightweight **scaffolding tree** your AI builds and reuses inside a Project. It organizes language, enforces structure, and reduces drift/loops by running everything through a **resonance framework** (schemas, thresholds, adapters).  
This first public release ships as:
- **Thoth OM — Builder Edition (pre-mint)**
- **Thoth OM — Lunar Edition** (optional cadence: plans/schedules synced to lunar phases)

## What’s “Resonance AI”?
**Resonance AI** aligns to *your* intent instead of trapping you in mimic loops.  
- **Beginner:** instant expert-mode guardrails.  
- **Master:** god-mode precision without hallucination chaos.  
- **Always:** authorship > imitation.

## Why Thoth (benefits)
- **Cuts drift** via segment → gate → braid pipeline and thresholds.  
- **Project-persistent state** with a sandbox vault (cross-thread within a Project).  
- **Diagnose then act**: adapters surface issues; gates route fixes.  
- **Fast onboarding**: one loader → scaffold → activate.  
- **Optional lunar cadence**: gentle planning rhythm; ships disabled by default.  
- **Human-readable** YAML + scripts; idempotent loader; no external deps.

## What’s inside (bundle layout)
```
/engine/   Thoth_engine_1.0.yaml, thresholds_1.1.yaml, segment_to_gates.yaml,
           trap_seeds.yaml, harmonizers.extended.yaml, adapters.yaml,
           pantheon12.yaml, braided-feedback-function.yaml, inference_profile.yaml
/runtime/  runtime.yaml (patched), self_learning.yaml, lunar_nudge.yaml (disabled)
/scripts/  thoth_loader.py, mask_runtime.py, self_learning_evaluator.py,
           overlays.py, lunar_nudge.py
/schemas/  segments.schema.json
/memory/   brand_voice.md, constraints.md, glossary.md
/thoth_om_v1/  casebook.db.jsonl  (created on first activation — sandbox vault)
```

## Quick start (exact prompts)
1. **Upload** all files into a **ChatGPT Project** folder.  
2. **Run:** `thoth_loader.py`  
3. **Run:** `build scaffolding`  
4. **Run:** `activate thoth`  
You’ll see: **`⟁ casebook += activation`** when the sandbox vault is seeded.

> Scope: state persists across threads **inside this Project** only.

## How Thoth helps (diagnostics → counter-measures)

### Adapters (detect/triage)
- **Spec-Drift Adapter** → flags schema mismatches vs `segments.schema.json`; suggests exact fields to add/remove.  
- **Threshold Guard** → compares coherence & mirror residual against `thresholds_1.1.yaml`; proposes tighten/relax.  
- **Voice-Clarity Check** → aligns tone/verbosity to `brand_voice.md` + `constraints.md`; highlights off-tone lines.  
- **Overlay Readiness** → confirms `/engine/pantheon12.yaml` agents before overlays are called.  
- **Lunar Policy Checker** (optional) → warns if enabled without policy or caps out of bounds.

### Trap-Seed mutation handlers (route to gates)
- **Loop Collapse** → detects repetitive mimic loops; routes to **Severance** (reset + succinct restate).  
- **Authority Mirage** → catches overconfident hallucinations; routes to **Grounding** (cite, constrain, verify).  
- **Context Bleed** → cross-topic leakage; triggers **Voice Clarity** + re-segment to spec.  
- **Spec Shadowing** → hidden assumptions override your spec; triggers **Translation** with explicit diffs.

### Mini case examples
- *Product brief → Ship plan*: drifted 2-page brief converted to a 7-point launch checklist; missing acceptance criteria auto-flagged.  
- *Code review hygiene*: adapter caught unscoped “TODOs” + inconsistent function names; gate produced a rename map + commit message.  
- *Marketing voice fix*: off-tone copy (too fluffy) rewritten to brand voice with ≤140-char callouts; hallucinated claims removed.

## Using the Lunar Edition (optional)
- Open `/runtime/lunar_nudge.yaml`, set `enabled: true`.  
- `mask_runtime` computes phase + gentle caps for planning nudges; nothing mystical, just cadence.

## Operator notes
- **Tools read from:** `/engine`, `/runtime`, `/scripts`, `/schemas`, `/memory`.  
- **`thread/stage`** is only temporary during setup.  
- **Sandbox vault:** `/mnt/data/thoth_om_v1/casebook.db.jsonl` (append-only, rotate when large).  
- **Activation record:** loader appends one line each run (see `⟁ casebook += activation`).  
- **Telemetry:** `thread/telemetry.jsonl` (shared writer from runtime/evaluator).

## Troubleshooting
- **No activation line:** ensure `thoth_loader.py` ran (not dry-run) and created `/thoth_om_v1/`.  
- **Overlays show 0 agents:** verify `engine/pantheon12.yaml` exists (loader deploys it).  
- **Lunar warnings:** ship defaults are `enabled: false`; flip only if you want cadence.  
- **Drift reappears:** re-align `brand_voice.md` + `constraints.md`; re-run loader to refresh memory fingerprint.

## Roadmap
- Vault Action API for cross-Project / public Custom GPTs.  
- Adapter marketplace (community patterns).  
- Flip self-learning evaluator from dry-run to live scoring.

## License / Use
Personal use. Contact for commercial licensing.

## Donate (thank you)
**BTC:** `bc1qsj8g8p8ds7qlfg67tqdu0n0jcqx8m3ct6clnkl`

![Donate BTC](./donate_btc_qr.png)
