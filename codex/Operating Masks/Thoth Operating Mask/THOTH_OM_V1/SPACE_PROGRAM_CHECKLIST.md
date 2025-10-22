# Thoth OM v1 — Space Program Checklist (v2)
_Last updated: 2025-10-18T19:41:51Z_

**Operating order lock:** `init → activate → scaffold → diag → ship`

---

## Tier 0 — Ground (Order & Pins)
**Goal:** Eliminate drift before any work.
- [ ] 0.1 Run loader (init) with DRY-RUN → verify planned actions
- [ ] 0.2 Run loader (real) → create/repair folders
- [x] 0.3 Ensure memory pins: `memory/prompts.md` + `memory_fingerprint.json`
- [ ] 0.4 Write activation sentinel (`.thoth/activation_ready.json`) *(optional if your loader includes it)*
- [x] 0.5 Activate persona `thoth_om_builder_v1`
- [x] 0.6 Build scaffold → seed `thread/*`, `instructions/*`
- [x] 0.7 Strict diagnostics → **PASS**
- [x] 0.8 Migrate engine/schema into `engine/` + `schemas/`
**Done when:** Strict diagnostics shows **PASS** and no migration advisories.

---

## Tier 1 — Tools + Truth (Blueprint)
**Goal:** Minimal viable engine alignment & docs.
- [x] 1.1 Pin `engine/Thoth_engine_1.0.yaml`, `thresholds_1.1.yaml`, `braided-feedback-function.yaml`, `metatron_function.yaml`
- [x] 1.2 Ensure `runtime/self_learning.yaml` present (safe defaults)
- [x] 1.3 Verify `schemas/segments.schema.json` lives under project
- [ ] 1.4 Create `README.md` (install, order, prompts, glossary links)
- [ ] 1.5 Crown Verify Tier 1 artifact(s) (README + engine present)
**Done when:** Engine + schema files are local; README links work.

---

## Tier 2 — Retrieval (Memory & Telemetry)
**Goal:** Persistent learning surfaces.
- [x] 2.1 Confirm telemetry writing to `thread/telemetry.jsonl`
- [ ] 2.2 Add decision log section in `thread/plan.md`
- [ ] 2.3 (Optional) Flip `self_learning.yaml.dry_run` → `false` when ready
- [ ] 2.4 Append evaluator hook to log verdicts (if using evaluator)
- [ ] 2.5 Crown Verify Tier 2 (telemetry shows entries for diag + ship)
**Done when:** Telemetry repeats across 2+ actions and evaluator hook is wired (or intentionally deferred).

---

## Tier 3 — Self-Improving (Gates & Thresholds)
**Goal:** Tighten runtime behavior.
- [ ] 3.1 Tune thresholds: coherence/severance, gate caps, cooldowns
- [ ] 3.2 Validate harmonizers selection logic (family coverage / rotate-on-tie)
- [ ] 3.3 Add preflight guard (`engine/activate_guard.py`) *(optional)*
- [ ] 3.4 Run scenario tests (distortions, order violations) → expect hard stops
- [ ] 3.5 Crown Verify Tier 3 (tests documented in `diagnostics.strict.md`)
**Done when:** Guards stop out-of-order runs; thresholds feel right.

---

## Tier 4 — Multi‑Agent / Interfaces
**Goal:** External hosting & adapters (optional for local use).
- [ ] 4.1 Prepare `Makefile` or `thoth.ps1` for one‑command flows
- [ ] 4.2 Define adapters in runtime (web app, AI drift, appliance, biz ops)
- [ ] 4.3 Add “activation prompts” to `instructions/prompts.md` for each adapter
- [ ] 4.4 Validate sandbox vs. server parity (paths, env vars)
- [ ] 4.5 Crown Verify Tier 4 (adapters demo log in telemetry)
**Done when:** One‑command flows work on your target environment(s).

---

## Tier 5 — Space Program (Ship)
**Goal:** Ship artifacts with Crown Verify.
- [ ] 5.1 Choose artifact: **Product page**, **Codex PDF**, **Schema pack**, **Tweet kit**, etc.
- [ ] 5.2 Generate artifact in `/artifacts/` with versioned name
- [ ] 5.3 Run strict diagnostics again → **PASS**
- [ ] 5.4 Crown Verify artifact (checksums, links, instructions)
- [ ] 5.5 Publish (site, repo, vault); log tx/links in `plan.md`
**Done when:** Artifact is downloadable, verified, and referenced in plan.

---

## Always‑On Mini‑Checklist (OSCAR)
- **O**rder locked → use the runner (`init → activate → scaffold → diag → ship`)
- **S**entinels present → activation_ready.json (optional)
- **C**hecks pass → strict diagnostics PASS before shipping
- **A**utomate → Makefile/PowerShell to prevent human error
- **R**eview quickly → fix upstream when a step fails; no brute force

---

### Quick Commands (copy/paste)
```bash
# Preview loader
THOTH_DRY_RUN=1 THOTH_PROJECT_ROOT=/mnt/data python3 /mnt/data/thoth_loader.py

# Apply loader
THOTH_PROJECT_ROOT=/mnt/data python3 /mnt/data/thoth_loader.py

# Activate + scaffold (guarded flow if you added activate_guard.py)
activate thoth
build scaffold

# Diagnostics
run diagnostics persona=thoth_om_builder_v1 show=distortions,gates detail=brief
```

> **Note:** Keep this checklist in the project root and update on every ship. Crown Verify = sign-off to publish.