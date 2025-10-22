#!/usr/bin/env python3
import json, sys, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SENT = ROOT/".thoth"/"activation_ready.json"
FP = ROOT/"memory_fingerprint.json"
MEM = ROOT/"memory"/"prompts.md"

def fail(msg, code=2):
    print(f"[thoth][guard] ✖ {msg}")
    sys.exit(code)

# Sentinel optional; if missing, still validate memory pins
if FP.exists() and MEM.exists():
    try:
        fp = json.loads(FP.read_text())
        recorded = fp.get("files",{}).get("memory/prompts.md",{}).get("sha256")
        actual = hashlib.sha256(MEM.read_bytes()).hexdigest()
        if not recorded or recorded != actual:
            fail("memory_fingerprint mismatch. Re-run loader.")
    except Exception as e:
        fail(f"fingerprint parse error: {e}")
else:
    fail("memory pins missing. Run loader (init) first.")

print("[thoth][guard] ✓ Preflight OK")
