@echo off
REM FileSorter — PyInstaller build script for Windows
REM Produces: dist\FileSorter\FileSorter.exe  (onedir — faster startup, AV-friendly)
REM
REM NOTE: For a proper Windows installer, use create_installer.bat instead.
REM       This script is for standalone distribution of the folder only.
REM
REM Usage: double-click build.bat (after running setup.py once)

SET "SCRIPT_DIR=%~dp0"
IF "%SCRIPT_DIR:~-1%"=="\" SET "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

SET "VENV=%SCRIPT_DIR%\venv"
SET "PYTHON=%VENV%\Scripts\python.exe"
SET "MAIN=%SCRIPT_DIR%\FileSorter.py"

IF NOT EXIST "%PYTHON%" (
    echo Error: venv not found. Run: python "%SCRIPT_DIR%\setup.py" first.
    pause
    exit /b 1
)

echo.
echo   Building FileSorter with PyInstaller...
echo.

RD /S /Q "%SCRIPT_DIR%\dist"  2>NUL
RD /S /Q "%SCRIPT_DIR%\build" 2>NUL
DEL /F /Q "%SCRIPT_DIR%\FileSorter.spec" 2>NUL

SET "ICON_FLAG="
IF EXIST "%SCRIPT_DIR%\app_icon.ico" (
    SET "ICON_FLAG=--icon=%SCRIPT_DIR%\app_icon.ico"
)

"%PYTHON%" -m PyInstaller ^
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
    echo.
    echo   Build FAILED. See output above for details.
    pause
    exit /b 1
)

echo.
echo   Build complete: dist\FileSorter\FileSorter.exe
echo   You can run FileSorter.exe directly, or use create_installer.bat
echo   to wrap it in a proper Windows installer.
echo.
pause
