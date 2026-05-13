@echo off
REM =============================================================================
REM setup.bat -- WGA Fluorescence Analysis Tool -- Windows First-Time Setup
REM
REM Double-click this file once after cloning the repository.
REM It will create a Python virtual environment and install all dependencies.
REM After setup, double-click run.bat to launch the tool.
REM =============================================================================

setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   WGA Fluorescence Analysis Tool -- First-Time Setup
echo ============================================================
echo.

REM -----------------------------------------------------------------------------
REM Check that Python 3 is available
REM -----------------------------------------------------------------------------
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python was not found on your PATH.
    echo.
    echo   Please install Python 3.11 from https://www.python.org/downloads/
    echo   IMPORTANT: Check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo Python found: !PYVER!

REM -----------------------------------------------------------------------------
REM Check that Git is available
REM -----------------------------------------------------------------------------
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git was not found on your PATH.
    echo.
    echo   Please install Git for Windows from https://git-scm.com/download/win
    echo   Use the default options during installation.
    echo.
    pause
    exit /b 1
)

for /f "tokens=1,2,3 delims= " %%a in ('git --version') do set GITVER=%%a %%b %%c
echo Git found: !GITVER!
echo.

REM -----------------------------------------------------------------------------
REM Check that requirements.txt exists
REM -----------------------------------------------------------------------------
if not exist "%~dp0requirements.txt" (
    echo ERROR: requirements.txt not found.
    echo.
    echo   This file is generated automatically by the project's CI system.
    echo   Please ensure you have the latest version of the repository:
    echo     git pull origin main
    echo.
    echo   If the file is still missing, visit the project page on GitHub.
    pause
    exit /b 1
)

REM -----------------------------------------------------------------------------
REM Create the virtual environment (skip if it already exists)
REM -----------------------------------------------------------------------------
if exist "%~dp0.venv\Scripts\activate.bat" (
    echo Virtual environment already exists. Skipping creation.
) else (
    echo Creating virtual environment...
    python -m venv "%~dp0.venv"
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Virtual environment created.
)
echo.

REM -----------------------------------------------------------------------------
REM Install dependencies from requirements.txt
REM -----------------------------------------------------------------------------
echo Installing dependencies (this may take a few minutes)...
"%~dp0.venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
"%~dp0.venv\Scripts\pip.exe" install -r "%~dp0requirements.txt" --quiet
if errorlevel 1 (
    echo ERROR: Dependency installation failed.
    echo   Check your internet connection and try again.
    pause
    exit /b 1
)
echo Dependencies installed successfully.
echo.

REM -----------------------------------------------------------------------------
REM Verify tkinter is available
REM -----------------------------------------------------------------------------
"%~dp0.venv\Scripts\python.exe" -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo WARNING: tkinter is not available in this Python installation.
    echo   The GUI will not work without tkinter.
    echo   Please reinstall Python 3.11 from https://www.python.org/downloads/
    echo   and ensure "tcl/tk and IDLE" is checked during installation.
    echo.
)

REM -----------------------------------------------------------------------------
REM Success
REM -----------------------------------------------------------------------------
echo ============================================================
echo   Setup complete!
echo.
echo   To launch the tool, double-click run.bat
echo ============================================================
echo.
pause
