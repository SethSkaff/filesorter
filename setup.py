#!/usr/bin/env python3
"""
FileSorter — One-command setup script
Usage: python setup.py

What this does:
  1. Checks Python version (requires 3.9+)
  2. Creates a virtual environment in ./venv
  3. Installs all dependencies from requirements.txt
  4. Launches FileSorter immediately
"""

import sys
import os
import subprocess
import platform
from pathlib import Path

# Resolve the project root from *this file's* location, not the cwd.
# This means `python C:\any\path\setup.py` works no matter what the
# current working directory is.
HERE    = Path(os.path.abspath(__file__)).parent
VENV    = HERE / "venv"
REQ     = HERE / "requirements.txt"
MAIN    = HERE / "FileSorter.py"
IS_WIN  = platform.system() == "Windows"
IS_MAC  = platform.system() == "Darwin"

PYTHON  = sys.executable

# Change into the project directory so any relative-path code that may
# run later (e.g. PyInstaller hooks) finds the right files.
os.chdir(str(HERE))

def banner(msg: str):
    print(f"\n{'─'*60}\n  {msg}\n{'─'*60}")

def run(cmd: list, **kwargs):
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        print(f"\n  ERROR: command exited with code {result.returncode}")
        sys.exit(result.returncode)
    return result

def check_python():
    banner("Step 1 — Checking Python version")
    major, minor = sys.version_info[:2]
    print(f"  Python {major}.{minor} detected")
    if (major, minor) < (3, 9):
        print(f"\n  ERROR: Python 3.9+ is required. You have {major}.{minor}.")
        print("  Download the latest Python from https://python.org")
        sys.exit(1)
    print("  ✓ Python version OK")

def create_venv():
    banner("Step 2 — Creating virtual environment")
    if VENV.exists():
        print("  venv/ already exists — skipping creation")
    else:
        run([PYTHON, "-m", "venv", str(VENV)])
        print("  ✓ Virtual environment created at ./venv")

def venv_python() -> Path:
    if IS_WIN:
        return VENV / "Scripts" / "python.exe"
    else:
        return VENV / "bin" / "python"

def venv_pip() -> Path:
    if IS_WIN:
        return VENV / "Scripts" / "pip.exe"
    else:
        return VENV / "bin" / "pip"

def install_deps():
    banner("Step 3 — Installing dependencies")
    pip = venv_pip()
    run([str(pip), "install", "--upgrade", "pip"])
    run([str(pip), "install", "-r", str(REQ)])
    print("  ✓ All dependencies installed")

def launch_app():
    banner("Step 4 — Launching FileSorter")
    py = venv_python()
    print(f"  Launching {MAIN.name} …\n")
    # Use os.execv so the app replaces this process (cleaner on Mac)
    try:
        os.execv(str(py), [str(py), str(MAIN)])
    except AttributeError:
        # Windows fallback (os.execv can behave oddly on Windows)
        subprocess.run([str(py), str(MAIN)])

def main():
    print("\n  FileSorter Setup\n")
    check_python()
    create_venv()
    install_deps()
    launch_app()

if __name__ == "__main__":
    main()
