@echo off
REM FileSorter launcher for Windows
REM Double-click this file after first-time setup.

SET SCRIPT_DIR=%~dp0
SET VENV=%SCRIPT_DIR%venv
SET PYTHON=%VENV%\Scripts\python.exe
SET MAIN=%SCRIPT_DIR%FileSorter.py

IF NOT EXIST "%PYTHON%" (
    echo Virtual environment not found.
    echo Please run first-time setup: python setup.py
    echo.
    pause
    exit /b 1
)

"%PYTHON%" "%MAIN%" %*
