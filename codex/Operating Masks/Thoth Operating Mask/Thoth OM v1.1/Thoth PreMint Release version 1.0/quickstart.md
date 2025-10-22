# ⟁ Thoth OM — Quick Start

This is the **minimum path to “on”** for the Builder Edition (mobile/desktop). Keep it tight; everything else is optional.

---

## 0) What you need
- A **ChatGPT Project** (use the side-panel folder).
- The **Thoth OM bundle** (this zip’s contents).

> Scope: State persists across threads **inside this Project** only.

---

## 1) Drop the files
Upload all bundle files into your Project folder. Keep the layout intact:
```
/engine  /runtime  /scripts  /schemas  /memory  (plus top-level files)
```

---

## 2) Activate the sandbox
Run these prompts (exact text) in the Project chat:

1. `thoth_loader.py`  
   - Verifies tree, deploys engine/runtime, patches `runtime.yaml`,
     and appends a vault activation record.
2. `build scaffolding`  
   - Confirms the canonical paths and staged files.
3. `activate thoth`  
   - Finalizes runtime hooks (lunar shipped **disabled**).

You should see: **`⟁ casebook += activation`**

---

## 3) What just happened
- **Canonical tree live:** `/engine`, `/runtime`, `/scripts`, `/schemas`, `/memory`
- **Sandbox vault:** `/mnt/data/thoth_om_v1/casebook.db.jsonl` (append-only)
- **Telemetry:** `/thread/telemetry.jsonl`

---

## 4) (Optional) Lunar Edition
- Edit `/runtime/lunar_nudge.yaml` → set `enabled: true`.
- Planning nudges follow lunar phases with safe caps.

---

## 5) Daily use
- Build normally. Thoth routes your inputs through **segment → gate → braid** with thresholds and adapters.
- To refresh after you edit engine files, just run: `thoth_loader.py` again (idempotent).

---

## 6) Troubleshooting (60s)
- **No activation echo:** rerun `thoth_loader.py` (not dry-run). Ensure `/thoth_om_v1/` exists.
- **Overlays = 0 agents:** confirm `/engine/pantheon12.yaml` is present.
- **Drift creeping in:** tune `brand_voice.md` + `constraints.md`, then re-run loader (re-fingerprint).
- **Lunar warnings:** defaults are `enabled: false` — only flip if you want cadence.

---

## 7) Operator reminders
- Tools read from: `/engine`, `/runtime`, `/scripts`, `/schemas`, `/memory`.
- `thread/stage` is temporary during setup.
- Do **not** store secrets in the casebook; it’s for minimal session metadata.

---

## 8) Support / Donate
If this helps you ship, consider donating to keep development moving.

**BTC:** `bc1qsj8g8p8ds7qlfg67tqdu0n0jcqx8m3ct6clnkl`  
![Donate BTC](./donate_btc_qr.png)
