# FileSorter

**Windows installer (recommended):** double-click `create_installer.bat` → run `output\FileSorter_Setup.exe`

**Dev / source:** `python setup.py` (works from any directory) — then double-click `run.bat` (Windows) or `run.sh` (Mac)

---

A native desktop file sorting application built with PyQt6. No browser, no server — a real native window that runs on macOS and Windows.

## Features

- **3-step setup wizard** — pick a folder, choose mode, set sort order
- **Sort Mode** — move files into destination folders using keyboard shortcuts (1–9, Q–P) or drag-to-sort
- **Swipe-Only Mode** — swipe/arrow-key left to delete, right to keep
- **File viewers** — images (with zoom/pan), video (with playback controls), audio, PDF (rendered pages via pymupdf), text/code, and a generic viewer for everything else
- **Mouse swipe** — click-hold-drag the file preview left (delete) or right (skip); releases before the threshold snap back with a spring animation; color overlay (red/green) shows intent
- **Keyboard shortcuts** — ← delete · → skip · A prev · D skip · Space play/pause · 1-9 / Q-P move to folder · ⌘Z/Ctrl+Z undo
- **Undo** — one level, works for moves and deletes (files are staged in `._sorter_trash/` until the session ends, then sent to OS trash)
- **Thumbnail strip** — shows upcoming files at the bottom; click any thumbnail to jump
- **Disk Analyzer** — scan any folder (or the whole computer) for the largest files and folders; delete directly from results
- **Session persistence** — saves progress to `sorter_config.json` inside the sorted folder; offers to resume on next launch
- **Live stats** — progress bar, file counter, running total of deleted storage
- **Toast notifications** — every action shows a brief bottom-center toast with undo hint
- **Dark theme** — full custom QSS stylesheet, no default OS widget styling

---

## Quick start

### Option A — Windows installer (no Python required on target PC)

```
double-click  create_installer.bat
```

The script automatically:
1. Checks Python 3.9+ is available on the **build** machine
2. Creates a `venv\` and installs all dependencies
3. Generates `app_icon.ico`
4. Runs PyInstaller → `dist\FileSorter\`
5. Compiles `FileSorter.iss` with Inno Setup → `output\FileSorter_Setup.exe`
6. Opens `output\` so you can find the installer immediately

Distribute `FileSorter_Setup.exe` to any Windows 10/11 machine. When the end-user runs it:
- FileSorter installs silently to `%LOCALAPPDATA%\FileSorter\`
- A **desktop shortcut** is created automatically
- They can click **"Launch FileSorter now"** in the final installer screen
- No Python, no terminal, no configuration needed

> **Inno Setup required on the build machine.** If it isn't installed, the script will display the one-liner to install it via `winget`:
> ```
> winget install JRSoftware.InnoSetup
> ```
> Then re-run `create_installer.bat`.

---

### Option B — Dev / source setup (any OS)

```bash
# Works from any directory — no need to cd first
python "C:\path\to\FileSorter\setup.py"
```

This will:
1. Check Python 3.9+
2. Create `venv/` next to `setup.py` (always resolves to the script's own folder)
3. `pip install` everything from `requirements.txt`
4. Launch FileSorter immediately

### After first-time setup

| Platform | How to launch |
|----------|--------------|
| macOS    | Double-click `run.sh` |
| Windows  | Double-click `run.bat` |

---

## Build a standalone executable (without a full installer)

```bash
# macOS
bash build.sh        # → dist/FileSorter.app

# Windows
build.bat            # → dist\FileSorter\ (folder)
```

The resulting output is self-contained — Python and all dependencies are bundled. Copy `FileSorter.app` to `/Applications` on Mac, or zip the `dist\FileSorter\` folder on Windows.

---

## Requirements

| Dependency | Purpose |
|---|---|
| `PyQt6` | UI framework |
| `PyQt6-Qt6Multimedia` | Video/audio playback |
| `pymupdf` | PDF page rendering |
| `pypdf` | PDF text fallback |
| `Pillow` | Image metadata |
| `send2trash` | OS-native trash (no permanent deletion) |
| `pyinstaller` | Packaging to .app / .exe |

---

## File layout

```
FileSorter/
├── FileSorter.py       ← main application (single file)
├── requirements.txt
├── setup.py            ← one-command install + launch
├── run.sh              ← macOS/Linux double-click launcher
├── run.bat             ← Windows double-click launcher
├── build.sh            ← macOS PyInstaller packaging
├── build.bat           ← Windows PyInstaller packaging
└── README.md
```

---

## Keyboard reference

| Key | Action |
|-----|--------|
| `←` | Delete (send to trash) |
| `→` or `D` | Skip to next file |
| `A` | Go to previous file |
| `Space` | Play / pause video or audio |
| `1`–`9` | Move to destination folder 1–9 |
| `Q`–`P` | Move to destination folder 10–19 |
| `⌘Z` / `Ctrl+Z` | Undo last action |

---

## Notes

- **Video/audio** requires `PyQt6-Qt6Multimedia` and platform media backends. On Windows, ensure Windows Media Player / DirectShow codecs are installed. On macOS, AVFoundation is used automatically.
- **Undo of deletes**: files are moved to a hidden `._sorter_trash/` folder inside the source folder while sorting. They are only permanently trashed when you navigate back or close. This makes delete fully reversible within a session.
- **sorter_config.json** is written to the sorted folder's root. Delete it to reset the session for that folder.
