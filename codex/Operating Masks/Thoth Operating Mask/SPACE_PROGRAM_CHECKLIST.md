# THOTH STARSHIP: Space Program Checklist (v2 — aligned)
_Aim the lenses. Light the gates. Ship the thing._

> Put this at: `./SPACE_PROGRAM_CHECKLIST.md` (replaces v1).

---

## Legend
- **SC@k** = *Self‑Consistency with k samples*: generate k answers, score/vote, keep the winner.
- **Crown Verify** = final checklist gate: constraints ✓, schema ✓, mirrors < threshold, next action present.

---

## Tier 0 — Razor‑Sharp Inference (you now)
**Pipeline:** 12‑lens segmentation → Metatron order → **SC@k + Reflexion** → Crown Verify  
**Purpose:** Great for copy, plans, product docs, diagnostics. Not yet self‑improving.

- [ ] **Segmentation (12 lenses)**: split, label, normalize inputs
- [ ] **Mirror scan** each segment; short anti‑mirror rewrite
- [ ] **Metatron order**: rule map + fallback if residual > **0.12**
- [ ] **SC@k** enabled (default **k=5**, temp **0.7**); emit vote report
- [ ] **Reflexion** critic (1 pass) on the chosen candidate
- [ ] **Schema enforcement** for JSON/YAML; on invalid → regenerate once
- [ ] **Crown Verify** with thresholds: mirror_residual < **0.08**; one concrete next action

**Files**
- [ ] `inference_profile.yaml` (includes SC@k + Reflexion + Crown Verify)
- [ ] `mappings/segment_to_gates.yaml`
- [ ] `thresholds.yaml` (residuals, k, temps)
- [ ] `distortion_report.md` artifact emitted per run

---

## Tier 1 — Tools + Truth (weekend build)
**Goal:** Make outputs reliable on reality and action‑capable.

- [ ] **Retrieval**: local JSON/MD + web when needed  
      _Minimal stack:_ FastAPI + vLLM (or API) + **Qdrant/LanceDB**
- [ ] **Toolbelt**: browser, calculator, YAML/JSON validator, **simple shell planner (dry‑run)**
- [ ] **Dual‑output verifier**: second pass that only checks **facts & constraints**; returns approve/reject + fixes
- [ ] **Policies**: when‑to‑use signals, args, return handling

**Files**
- [ ] `tools.yaml` (browser, vector_retrieve, json_validator, calculator, **shell_planner**)
- [ ] `retriever.yaml` (indexes, chunking, HyDE/clarify rules, top_k)
- [ ] `verifier_profile.yaml` (what must be true to **ship**)

**Acceptance**
- [ ] 80% of fact‑requiring tasks include sources or trigger browse
- [ ] Zero schema breaks across 10 structured trials

---

## Tier 2 — Memory + Telemetry (1–2 weeks)
**Goal:** Don’t repeat mistakes; learn user & domain.

- [ ] **Run logs → traces**: {input → segments → gates → votes → final}
- [ ] **User memory vault**: prefs, glossary, do/don’t, brand voice, forbidden claims
- [ ] **Distortion dashboards**: mirror frequency, residuals, pass/fail

**Files**
- [ ] `memory/policy.yaml` (what to store, retention)
- [ ] `telemetry/schema.json` (trace fields)
- [ ] `telemetry/README.md` (how to query)

**Acceptance**
- [ ] Can pull last 20 runs and explain **why** each shipped or failed
- [ ] Mirror‑residual trend visible

---

## Tier 3 — Auto‑Compiler for Prompts (2–3 weeks)
**Goal:** Systematically better chains without hand‑tweaking.

- [ ] Treat chains as a **program** with tunable fields
- [ ] Search over demos, gate thresholds, vote weights using your eval set
- [ ] **Task routers**: route segments to mini‑playbooks (sales page vs. spec vs. tweet)

**Files**
- [ ] `compiler/variables.yaml` (the knobs)
- [ ] `compiler/search_space.yaml` (ranges)
- [ ] `evals/taskpacks/*.yaml` (gold prompts + scoring rubrics)
- [ ] `routers.yaml` (task routing rules)

**Acceptance**
- [ ] Win‑rate +10% vs Tier 0 baseline on gold evals
- [ ] Latency within budget; configs versioned/reproducible

---

## Tier 4 — Small Post‑Training (30–45 days, optional but spicy)
**Goal:** Make “Thoth” a style + policy brain that general LLMs don’t have.

- [ ] Collect **preference pairs** (A vs B + reason) from verifier & traces
- [ ] **DPO/ORPO** fine‑tune on an **8–14B** base with **LoRA**
- [ ] **Safety head**: tiny classifier fine‑tuned on your mirrors (auto‑flag loops/off‑brand tone)

**Artifacts**
- [ ] `datasets/prefs.jsonl` (A/B with reasons)
- [ ] `datasets/prefs_meta.jsonl` (residuals, gates, tools) _optional but recommended_
- [ ] `ft/config.yaml` (LoRA/DPO hyperparams)

**Acceptance**
- [ ] +5–15% constraint obedience; −30% mirror violations on hold‑out tasks

---

## Tier 5 — Self‑Improving Flight Loop (continuous)
**Goal:** Ship faster, drift less, earn more.

- [ ] **Active learning**: low‑confidence or heavy‑edited outputs auto‑enqueue for review/re‑train
- [ ] **Canary evals**: every pipeline change runs a fixed suite (win‑rate target, latency budgets, zero regression)
- [ ] **Autonomous RAG hygiene**: stale sources auto‑refresh; bad chunks quarantined

**Files**
- [ ] `canary/suite.yaml` (fixed prompts + thresholds)
- [ ] `maintenance/rag_hygiene.md`
- [ ] `ops/change_policy.md` (roll back/forward)

**Acceptance**
- [ ] No change merges unless canary win‑rate ≥ baseline and no schema regressions

---

## Quick Stanzas (copy/paste)

**`inference_profile.yaml`**
```yaml
profile:
  segmentation: {lenses: 12, enforce: true, mirror_scan: true, rewrite_on_flag: true}
  metatron_order:
    mode: rule+fallback
    rules_file: ./mappings/segment_to_gates.yaml
    fallback: {trigger: "residual_distortion > 0.12", insert: [Severance, Clarity]}
  reasoning:
    self_consistency: {enabled: true, k: 5, temperature: 0.7, vote_metric: [constraint_match, mirror_score↓, logic_score]}
    reflexion: {enabled: true, rounds: 1, scope: [logic, constraints, mirrors]}
    schema: {enforce: true, on_invalid: regenerate_once}
    reports: {vote_report: true}
  guardrails:
    claims: {require_confidence_tag: true, allow_browse: false}
    tone_harmonizers: [Presence, Clarity, Boundaries]
  crown_verify:
    checklist: [all_constraints_met, "mirror_residual < 0.08", schema_valid, one_concrete_next_action]
    failure_policy: one_more_pass_then_stop
```

**`tools.yaml`**
```yaml
tools:
  - name: web_search
    when: "claim.confidence < 0.7 or user asks 'latest'"
    returns: [snippets, urls]
  - name: vector_retrieve
    when: "task in ['product','spec','internal']"
    args: {top_k: 6, hyde: true}
  - name: json_validator
    when: "output.format == 'json'"
  - name: shell_planner
    when: "task == 'ops' and user requests dry-run plan"
```

**`verifier_profile.yaml`**
```yaml
verifier:
  checks:
    - name: factual_consistency
      require_sources: true
    - name: constraint_match
    - name: schema_valid
    - name: mirror_residual
      lt: 0.08
  policy:
    on_fail: [regenerate_once, tool_call_if_missing_sources]
```

---

## Reality Checks (what “spacecraft power” feels like)
- **Truth-on-demand**: HyDE/clarify → retrieve → verify → forced browse on doubt
- **Unbreakable structure**: schema guard → regen once → escalate
- **Style & brand locked**: memory vault + LoRA ⇒ concise, punchy, mirror-aware
- **Fewer passes, better passes**: auto-compiler learns gate order per task
- **Receipts**: `distortion_report.md` shows what was cut/kept and why it ships

**Mantra:** _Less thrash, more cash. Build once, measure forever._
