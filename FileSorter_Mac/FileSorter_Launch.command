#!/bin/bash
# ============================================================
#  FileSorter — macOS Launcher
#  Double-click this file in Finder to run FileSorter.
#
#  First run: automatically creates a venv and installs deps.
#  Subsequent runs: launches instantly.
# ============================================================

# Always run from the folder this script lives in
cd "$(dirname "$0")"

echo ""
echo "============================================================"
echo "  FileSorter"
echo "============================================================"
echo ""

# ── Check Python 3.9+ ────────────────────────────────────────
PYTHON=""
for candidate in python3 python3.12 python3.11 python3.10 python3.9; do
    if command -v "$candidate" &>/dev/null; then
        VER=$("$candidate" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null)
        MAJOR=$(echo "$VER" | cut -d. -f1)
        MINOR=$(echo "$VER" | cut -d. -f2)
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 9 ]; then
            PYTHON="$candidate"
            break
        fi
    fi
done

if [ -z "$PYTHON" ]; then
    echo "ERROR: Python 3.9 or newer is required but was not found."
    echo ""
    echo "Install it from: https://www.python.org/downloads/"
    echo "Or via Homebrew:  brew install python3"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo "  Using Python: $PYTHON ($VER)"
echo ""

# ── Create venv if needed ────────────────────────────────────
VENV="$(dirname "$0")/venv"
if [ ! -f "$VENV/bin/python" ]; then
    echo "  Setting up virtual environment (first run only)..."
    "$PYTHON" -m venv "$VENV"
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment."
        read -p "Press Enter to exit..."
        exit 1
    fi
    echo "  Virtual environment created."
    echo ""
fi

VENV_PY="$VENV/bin/python"
VENV_PIP="$VENV/bin/pip"

# ── Install / update dependencies ────────────────────────────
REQ="$(dirname "$0")/requirements.txt"
echo "  Installing dependencies (may take a minute on first run)..."
"$VENV_PY" -m pip install --upgrade pip --quiet
"$VENV_PY" -m pip install -r "$REQ" --quiet
if [ $? -ne 0 ]; then
    echo "ERROR: Dependency installation failed."
    echo "Try running this in Terminal:"
    echo "  pip3 install PyQt6 pymupdf pypdf Pillow send2trash"
    read -p "Press Enter to exit..."
    exit 1
fi
echo "  Dependencies ready."
echo ""

# ── Launch FileSorter ─────────────────────────────────────────
echo "  Launching FileSorter..."
echo ""
"$VENV_PY" "$(dirname "$0")/FileSorter.py"
