# Codex Engine v0 — Release Readiness Checklist

Use this to confirm v0 is shippable.

## ✅ Core Files Present & Valid
- [x] `Codex_Engine_v0.yaml` — parsed without errors
- [x] `Codex_Engine_v0.runtime.yaml` — parsed without errors
- [x] `Codex_Engine_v0.diagnostics.yaml` — parsed without errors

## 🔧 Sanity Checks
- [ ] Version string present (e.g., `engine.version`)
- [ ] Runtime sets diagnostics to **on-demand only** (emit on thread end or explicit request)
- [ ] Default Clarity levels mapped (Middle School / High School / University / Master)
- [ ] Threshold → Severance → Clarity → Action flow verified on sample input
- [ ] Safety guard: refuse political advocacy & self-harm edge cases gracefully
- [ ] Deterministic seed or run-id in logs for reproducibility

## 📦 Packaging
- [ ] Include this checklist
- [ ] Include `README.md` with quickstart + example prompts
- [ ] Include `CHANGELOG.md` (v0 initial)
- [ ] Include `LICENSE` (choose one) and simple TOS for commercial use
- [ ] Provide example inputs/outputs (two JSONL fixtures)

## 🧪 Tests
- [ ] Unit: YAML schema keys exist (`mirrors`, `functions`, `engine`, etc.)
- [ ] Scenario: “New society / messiah spiral” → engine produces Diagnostics only at end
- [ ] Scenario: benign productivity loop → clean severance + actionable step
- [ ] Fuzz: random long prompt → no crash, graceful clarity output

## 🛡️ Productization
- [ ] Clear disclaimer (not clinical or legal advice)
- [ ] Version + hash printed on first run
- [ ] Optional telemetry flag default **off**

## 📣 Launch
- [ ] One-page product sheet (value, how it works, example)
- [ ] Support email or GitHub Issues link
- [ ] Pricing & delivery flow tested end-to-end

---
Generated automatically on first lint.
