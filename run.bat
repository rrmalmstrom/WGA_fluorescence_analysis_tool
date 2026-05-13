@echo off
REM =============================================================================
REM run.bat -- WGA Fluorescence Analysis Tool -- Windows Daily Launcher
REM
REM Double-click this file each time you want to use the tool.
REM It activates the virtual environment and launches the GUI.
REM =============================================================================

setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   WGA Fluorescence Analysis Tool
echo ============================================================
echo.

REM -----------------------------------------------------------------------------
REM Check that the virtual environment exists
REM -----------------------------------------------------------------------------
if not exist "%~dp0.venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found.
    echo.
    echo   Please run setup.bat first to set up the tool.
    echo.
    pause
    exit /b 1
)

REM -----------------------------------------------------------------------------
REM Activate the virtual environment
REM -----------------------------------------------------------------------------
call "%~dp0.venv\Scripts\activate.bat"
echo Virtual environment: .venv OK
echo.

REM -----------------------------------------------------------------------------
REM Ask the user for the data folder path
REM -----------------------------------------------------------------------------
echo Please enter the path to your data folder.
echo (You can type the full path, or drag and drop the folder into this window.)
echo (Press Enter to skip and launch without a default data folder.)
echo.
set /p DATA_FOLDER="Data folder: "

REM Strip surrounding quotes if the user drag-dropped a folder
set DATA_FOLDER=%DATA_FOLDER:"=%

REM -----------------------------------------------------------------------------
REM Launch the tool
REM -----------------------------------------------------------------------------
cd /d "%~dp0"

if "!DATA_FOLDER!"=="" (
    echo.
    echo Launching without a default data folder...
    echo.
    python launch_gui.py
) else (
    if not exist "!DATA_FOLDER!" (
        echo.
        echo WARNING: The path does not exist or is not a folder.
        echo Launching without a default data folder.
        echo.
        python launch_gui.py
    ) else (
        echo.
        echo Data folder: !DATA_FOLDER!
        echo.
        python launch_gui.py --data-folder "!DATA_FOLDER!"
    )
)
