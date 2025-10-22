# docs/diagnostics.md
## Diagnostics (on-demand)
- Say "show diagnostics" or end the thread to emit a report that includes:
  - traps_triggered, gates_fired, node_selected
  - braid_quality, residual_index
  - crown_status (pass/fail) and brief rationale

## Crown Verification
- Enforced before export. If it fails, output is contained and a remediation hint is returned.

## Gate Order
- Default: Severance -> Clarity -> NodeGate -> Action (G01->G02->GNN->G12).
- Replace `GNN` with the current node hook.
