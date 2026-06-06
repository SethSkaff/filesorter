#!/usr/bin/env bash
# FileSorter launcher for macOS / Linux
# Double-click this file (or run: bash run.sh) after first-time setup.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/venv"
PYTHON="$VENV/bin/python"
MAIN="$SCRIPT_DIR/FileSorter.py"

if [ ! -f "$PYTHON" ]; then
    echo "Virtual environment not found."
    echo "Please run first-time setup: python setup.py"
    # Try to open a terminal with the setup command
    if command -v osascript &>/dev/null; then
        osascript -e "tell application \"Terminal\" to do script \"cd '$SCRIPT_DIR' && python3 setup.py\""
    else
        xterm -e "cd '$SCRIPT_DIR' && python3 setup.py" &
    fi
    exit 1
fi

exec "$PYTHON" "$MAIN" "$@"
