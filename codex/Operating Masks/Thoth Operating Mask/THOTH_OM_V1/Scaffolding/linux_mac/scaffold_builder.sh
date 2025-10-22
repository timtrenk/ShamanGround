#!/usr/bin/env bash
# linux_mac/scaffold_builder.sh
set -euo pipefail
if [ ! -f "./scaffold_spec.yaml" ]; then echo "ERROR: scaffold_spec.yaml not found."; exit 1; fi
if ! command -v python3 >/dev/null 2>&1; then echo "ERROR: python3 required."; exit 1; fi
python3 - <<'PY'
import sys
try:
    import yaml
except Exception:
    sys.exit(2)
PY
if [ $? -eq 2 ]; then
  echo "Installing PyYAML..."
  pip3 install --user pyyaml
fi
python3 ./server/scaffold_builder.py
