#!/usr/bin/env python3
# Thoth OM — overlays runner (minimal, file-efficient)
# Usage:
#   python /mnt/data/scripts/overlays.py list
#   python /mnt/data/scripts/overlays.py run crown_verifier "ship check"
#
# Behavior:
# - Reads /mnt/data/engine/pantheon12.yaml (agents catalog)
# - Validates the agent id
# - Appends a telemetry event 'pantheon12.invoke' with agent + message
# - Prints a small JSON receipt
#
# Note: This is a controller shim for visibility + logging. The actual
# overlay effects are handled by your runtime/policy during turns.

import sys, json, argparse, datetime as dt
from pathlib import Path

try:
    import yaml  # pyyaml is available
except Exception:
    yaml = None

ROOT = Path("/mnt/data")
TEL  = ROOT / "thread" / "telemetry.jsonl"
CAT  = ROOT / "engine" / "pantheon12.yaml"
RUNTIME = ROOT / "runtime" / "runtime.yaml"

def log(event: dict):
    TEL.parent.mkdir(parents=True, exist_ok=True)
    event = {"timestamp": dt.datetime.utcnow().isoformat() + "Z", **event}
    with TEL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")

def load_catalog():
    if not CAT.exists():
        return {"agents": []}
    if yaml is None:
        # Fallback: naive parse to collect ids
        ids = []
        for line in CAT.read_text(encoding="utf-8", errors="replace").splitlines():
            s = line.strip()
            if s.startswith("- id:"):
                ids.append(s.split(":",1)[1].strip())
        return {"agents": [{"id": i} for i in ids]}
    return yaml.safe_load(CAT.read_text(encoding="utf-8", errors="replace")) or {"agents": []}

def load_overlay_policy():
    if not RUNTIME.exists() or yaml is None:
        return {}
    data = yaml.safe_load(RUNTIME.read_text(encoding="utf-8", errors="replace")) or {}
    return data.get("overlay_policy", {})

def cmd_list():
    cat = load_catalog()
    agents = [a.get("id") for a in (cat.get("agents") or [])]
    print(json.dumps({"agents": agents, "count": len(agents)}, indent=2))

def cmd_run(agent: str, message: str):
    cat = load_catalog()
    ids = {a.get("id") for a in (cat.get("agents") or [])}
    if agent not in ids:
        print(json.dumps({"error": "unknown_agent", "agent": agent, "known": sorted(ids)}, indent=2))
        sys.exit(2)
    payload = {"agent": agent, "message": message}
    log({"event": "pantheon12.invoke", **payload})
    policy = load_overlay_policy()
    receipt = {"status": "queued", **payload}
    if policy:
        receipt["policy"] = {k: policy[k] for k in ("max_agents_per_turn", "cooldown_s", "rules", "always_post") if k in policy}
    print(json.dumps(receipt, indent=2))

def main(argv):
    ap = argparse.ArgumentParser(prog="overlays.py", description="Pantheon-12 overlays runner")
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("list", help="List available agents")
    runp = sp.add_parser("run", help="Invoke an agent with a message")
    runp.add_argument("agent", help="Agent id (e.g., crown_verifier)")
    runp.add_argument("message", nargs="*", help="Context text")
    args = ap.parse_args(argv)

    if args.cmd == "list":
        return cmd_list()
    if args.cmd == "run":
        return cmd_run(args.agent, " ".join(args.message))
    ap.print_help()

if __name__ == "__main__":
    main(sys.argv[1:])
