#!/usr/bin/env bash
# FileSorter — PyInstaller packaging script
# Produces:
#   macOS  →  dist/FileSorter.app  (double-clickable .app bundle)
#   Windows → dist/FileSorter.exe  (standalone .exe)
#
# Usage: bash build.sh
# Requirements: run after setup.py so the venv and deps exist.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/venv"
PYTHON="$VENV/bin/python"
PYINSTALLER="$VENV/bin/pyinstaller"
MAIN="$SCRIPT_DIR/FileSorter.py"

if [ ! -f "$PYTHON" ]; then
    echo "Error: venv not found. Run: python setup.py first."
    exit 1
fi

echo ""
echo "  Building FileSorter with PyInstaller…"
echo ""

# Clean previous builds
rm -rf "$SCRIPT_DIR/dist" "$SCRIPT_DIR/build" "$SCRIPT_DIR/FileSorter.spec" 2>/dev/null || true

PLATFORM=$(uname -s)

if [ "$PLATFORM" = "Darwin" ]; then
    "$PYTHON" -m PyInstaller \
        --windowed \
        --onefile \
        --name "FileSorter" \
        --hidden-import "PyQt6.QtMultimedia" \
        --hidden-import "PyQt6.QtMultimediaWidgets" \
        --hidden-import "fitz" \
        --hidden-import "send2trash" \
        --hidden-import "pypdf" \
        --collect-all "fitz" \
        "$MAIN"
    echo ""
    echo "  ✓ Build complete: dist/FileSorter.app"
    echo "  Drag FileSorter.app to your Applications folder to install."
else
    # Linux / other Unix
    "$PYTHON" -m PyInstaller \
        --windowed \
        --onefile \
        --name "FileSorter" \
        --hidden-import "PyQt6.QtMultimedia" \
        --hidden-import "PyQt6.QtMultimediaWidgets" \
        --hidden-import "fitz" \
        --hidden-import "send2trash" \
        --hidden-import "pypdf" \
        --collect-all "fitz" \
        "$MAIN"
    echo ""
    echo "  ✓ Build complete: dist/FileSorter"
fi
