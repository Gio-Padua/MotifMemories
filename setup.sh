#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if command -v python >/dev/null 2>&1; then
  SYSTEM_PYTHON="python"
elif command -v python3 >/dev/null 2>&1; then
  SYSTEM_PYTHON="python3"
else
  echo "Python 3.11 or newer is required. Install Python, then reopen Git Bash." >&2
  exit 1
fi

"$SYSTEM_PYTHON" -c 'import sys; assert sys.version_info >= (3, 11), "Python 3.11 or newer is required."'

if [[ ! -f ptbth/Scripts/python.exe && ! -f ptbth/bin/python ]]; then
  echo "Creating virtual environment in ptbth/..."
  "$SYSTEM_PYTHON" -m venv ptbth
fi

if [[ -f ptbth/Scripts/python.exe ]]; then
  VENV_PYTHON="$ROOT_DIR/ptbth/Scripts/python.exe"
else
  VENV_PYTHON="$ROOT_DIR/ptbth/bin/python"
fi

"$VENV_PYTHON" -c 'import sys; assert sys.version_info >= (3, 11), "The existing ptbth environment uses Python older than 3.11. Remove ptbth and rerun setup.sh."'

echo "Installing the Motif Moments backend from ./photobooth-app..."
"$VENV_PYTHON" -m pip install -r requirements.txt

CONFIG_FILE="$ROOT_DIR/photobooth-data/config/config.json"
if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "Initializing booth data and kiosk presets..."
  mkdir -p photobooth-data
  (
    cd photobooth-data
    "$VENV_PYTHON" -c 'from photobooth.appconfig import appconfig; appconfig.persist()'
  )
  "$VENV_PYTHON" photobooth-frontend/scripts/install-kiosk-presets.py
else
  echo "Existing booth configuration found; preserving runtime data and operator settings."
fi

"$VENV_PYTHON" -m pip check

echo
echo "Setup complete. Start Motif Moments with:"
echo "  cd photobooth-data"
if [[ -f ptbth/Scripts/photobooth.exe ]]; then
  echo "  ../ptbth/Scripts/photobooth.exe"
else
  echo "  ../ptbth/bin/photobooth"
fi
echo "Then open http://localhost:8000"
