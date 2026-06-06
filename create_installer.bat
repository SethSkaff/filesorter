@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul 2>&1

:: ============================================================
::  FileSorter — create_installer.bat
::  Single-command Windows installer builder.
::
::  What this does (fully automated):
::    1. Checks Python 3.9+
::    2. Creates / reuses venv\
::    3. pip-installs all requirements
::    4. Generates the app icon (app_icon.ico)
::    5. Runs PyInstaller  →  dist\FileSorter\
::    6. Locates Inno Setup (or offers to download it)
::    7. Compiles the .iss script  →  output\FileSorter_Setup.exe
::    8. Opens the output\ folder so you can find the installer
::
::  Run from any directory:
::    create_installer.bat
::  or
::    "C:\path\to\project\create_installer.bat"
:: ============================================================

:: Always resolve paths relative to THIS script, not the cwd.
SET "SCRIPT_DIR=%~dp0"
:: Remove trailing backslash
IF "%SCRIPT_DIR:~-1%"=="\" SET "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

SET "VENV=%SCRIPT_DIR%\venv"
SET "REQ=%SCRIPT_DIR%\requirements.txt"
SET "MAIN=%SCRIPT_DIR%\FileSorter.py"
SET "ISS=%SCRIPT_DIR%\FileSorter.iss"
SET "OUTDIR=%SCRIPT_DIR%\output"
SET "DISTDIR=%SCRIPT_DIR%\dist\FileSorter"
SET "ICON_SCRIPT=%SCRIPT_DIR%\generate_icon.py"

CALL :header "FileSorter — Windows Installer Builder"
echo.
echo   Project folder: %SCRIPT_DIR%
echo.

:: ── Step 1: Python ───────────────────────────────────────────────────────────
CALL :step "1" "Checking Python"

python --version >nul 2>&1
IF ERRORLEVEL 1 (
    CALL :error "Python is not installed or not in PATH."
    echo   Download Python 3.9+ from: https://www.python.org/downloads/
    echo   Make sure to check 'Add Python to PATH' during installation.
    CALL :pause_exit
)

FOR /F "tokens=2 delims= " %%V IN ('python --version 2^>^&1') DO SET "PY_VER=%%V"
FOR /F "tokens=1,2 delims=." %%A IN ("%PY_VER%") DO (
    SET "PY_MAJ=%%A"
    SET "PY_MIN=%%B"
)
IF %PY_MAJ% LSS 3 (
    CALL :error "Python 3.9+ required. Found %PY_VER%."
    CALL :pause_exit
)
IF %PY_MAJ% EQU 3 IF %PY_MIN% LSS 9 (
    CALL :error "Python 3.9+ required. Found %PY_VER%."
    CALL :pause_exit
)
CALL :ok "Python %PY_VER%"

:: ── Step 2: Virtual environment ──────────────────────────────────────────────
CALL :step "2" "Setting up virtual environment"

IF NOT EXIST "%VENV%\Scripts\python.exe" (
    echo   Creating venv ...
    python -m venv "%VENV%"
    IF ERRORLEVEL 1 (
        CALL :error "Failed to create virtual environment."
        CALL :pause_exit
    )
    CALL :ok "venv created at %VENV%"
) ELSE (
    CALL :ok "venv already exists — reusing"
)

SET "VENV_PY=%VENV%\Scripts\python.exe"
SET "VENV_PIP=%VENV%\Scripts\pip.exe"

:: ── Step 3: Install dependencies ─────────────────────────────────────────────
CALL :step "3" "Installing Python dependencies"

echo   Upgrading pip ...
"%VENV_PIP%" install --upgrade pip --quiet
IF ERRORLEVEL 1 (
    CALL :error "pip upgrade failed."
    CALL :pause_exit
)

echo   Installing from requirements.txt (this may take a few minutes) ...
"%VENV_PIP%" install -r "%REQ%" --quiet
IF ERRORLEVEL 1 (
    CALL :error "Dependency installation failed. See output above."
    CALL :pause_exit
)
CALL :ok "All dependencies installed"

:: ── Step 4: Generate icon ─────────────────────────────────────────────────────
CALL :step "4" "Generating application icon"

IF EXIST "%SCRIPT_DIR%\app_icon.ico" (
    CALL :ok "app_icon.ico already exists — skipping"
) ELSE (
    "%VENV_PY%" "%ICON_SCRIPT%"
    IF ERRORLEVEL 1 (
        echo   [WARN] Icon generation failed — installer will use default icon.
    ) ELSE (
        CALL :ok "app_icon.ico created"
    )
)

:: ── Step 5: PyInstaller build ─────────────────────────────────────────────────
CALL :step "5" "Building FileSorter.exe with PyInstaller"

:: Clean previous build artefacts
IF EXIST "%SCRIPT_DIR%\dist"  RD /S /Q "%SCRIPT_DIR%\dist"
IF EXIST "%SCRIPT_DIR%\build" RD /S /Q "%SCRIPT_DIR%\build"
IF EXIST "%SCRIPT_DIR%\FileSorter.spec" DEL /F /Q "%SCRIPT_DIR%\FileSorter.spec"

:: Determine icon flag
SET "ICON_FLAG="
IF EXIST "%SCRIPT_DIR%\app_icon.ico" (
    SET "ICON_FLAG=--icon=%SCRIPT_DIR%\app_icon.ico"
)

echo   Running PyInstaller ...
"%VENV_PY%" -m PyInstaller ^
    --windowed ^
    --onedir ^
    --name "FileSorter" ^
    %ICON_FLAG% ^
    --hidden-import "PyQt6.QtMultimedia" ^
    --hidden-import "PyQt6.QtMultimediaWidgets" ^
    --hidden-import "PyQt6.QtOpenGL" ^
    --hidden-import "fitz" ^
    --hidden-import "send2trash" ^
    --hidden-import "pypdf" ^
    --collect-all "fitz" ^
    --noconfirm ^
    --distpath "%SCRIPT_DIR%\dist" ^
    --workpath "%SCRIPT_DIR%\build" ^
    --specpath "%SCRIPT_DIR%" ^
    "%MAIN%"

IF ERRORLEVEL 1 (
    CALL :error "PyInstaller build failed. See output above."
    CALL :pause_exit
)

IF NOT EXIST "%DISTDIR%\FileSorter.exe" (
    CALL :error "Expected dist\FileSorter\FileSorter.exe not found after build."
    CALL :pause_exit
)
CALL :ok "Built: dist\FileSorter\FileSorter.exe"

:: ── Step 6: Locate Inno Setup ─────────────────────────────────────────────────
CALL :step "6" "Locating Inno Setup"

SET "ISCC="

:: Check common install locations (Inno Setup 6 and 5, 32/64-bit Program Files)
FOR %%P IN (
    "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
    "%ProgramFiles%\Inno Setup 6\ISCC.exe"
    "%ProgramFiles(x86)%\Inno Setup 5\ISCC.exe"
    "%ProgramFiles%\Inno Setup 5\ISCC.exe"
    "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
) DO (
    IF EXIST %%P (
        SET "ISCC=%%P"
        GOTO :iscc_found
    )
)

:: Also try PATH
WHERE ISCC >nul 2>&1
IF NOT ERRORLEVEL 1 (
    SET "ISCC=ISCC"
    GOTO :iscc_found
)

:: Not found — offer automatic download via winget or manual download
echo.
echo   Inno Setup was not found on this machine.
echo.
echo   Option A (Automatic — requires winget):
echo     Run this command in a terminal, then re-run create_installer.bat:
echo.
echo       winget install JRSoftware.InnoSetup
echo.
echo   Option B (Manual):
echo     1. Go to  https://jrsoftware.org/isdl.php
echo     2. Download and run the Inno Setup installer
echo     3. Re-run create_installer.bat
echo.
echo   Alternatively, the raw PyInstaller output is already at:
echo     %DISTDIR%
echo   You can zip that folder and distribute it without an installer.
echo.
CALL :pause_exit

:iscc_found
CALL :ok "Found: %ISCC%"

:: ── Step 7: Compile installer ─────────────────────────────────────────────────
CALL :step "7" "Compiling Windows installer"

IF NOT EXIST "%OUTDIR%" MKDIR "%OUTDIR%"

:: If the icon was generated, patch the .iss to enable the SetupIconFile line.
:: We do this by writing a tiny override .iss that #includes the main one.
IF EXIST "%SCRIPT_DIR%\app_icon.ico" (
    SET "ICON_ISS_LINE=#define UseIcon 1"
) ELSE (
    SET "ICON_ISS_LINE="
)

"%ISCC%" ^
    /DMyAppSrcDir="%DISTDIR%" ^
    /O"%OUTDIR%" ^
    "%ISS%"

IF ERRORLEVEL 1 (
    CALL :error "Inno Setup compilation failed. See output above."
    CALL :pause_exit
)

IF NOT EXIST "%OUTDIR%\FileSorter_Setup.exe" (
    CALL :error "output\FileSorter_Setup.exe not found after compilation."
    CALL :pause_exit
)

:: ── Done ──────────────────────────────────────────────────────────────────────
echo.
CALL :header "Build complete"
echo.
echo   Installer: %OUTDIR%\FileSorter_Setup.exe
echo.

:: Show file size
FOR %%F IN ("%OUTDIR%\FileSorter_Setup.exe") DO (
    SET /A "SIZE_MB=%%~zF / 1048576"
    echo   Size: !SIZE_MB! MB
)

echo.
echo   Share FileSorter_Setup.exe with anyone — no Python required on their PC.
echo   When they double-click it:
echo     - FileSorter installs silently to %%LOCALAPPDATA%%\FileSorter\
echo     - A desktop shortcut is created automatically
echo     - They can launch the app immediately
echo.

:: Open the output folder
explorer "%OUTDIR%"

GOTO :EOF

:: ── Helpers ───────────────────────────────────────────────────────────────────

:header
echo.
echo ============================================================
echo   %~1
echo ============================================================
GOTO :EOF

:step
echo.
echo [Step %~1] %~2 ...
GOTO :EOF

:ok
echo   OK  %~1
GOTO :EOF

:error
echo.
echo   ERROR: %~1
echo.
GOTO :EOF

:pause_exit
echo Press any key to exit ...
pause >nul
exit /b 1
