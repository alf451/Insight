@echo off
REM Insight Mock Metal Detector Simulator - Windows launcher.
REM Run this from the simulator\ directory. Requires Python 3.10+ installed.
REM Usage: run_simulator.bat [extra args passed to insight_simulator, e.g. --broker 192.168.1.10]

cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    set PYEXE=py
) else (
    set PYEXE=python
)

if not exist ".venv" (
    echo Creating virtual environment using %PYEXE% ...
    %PYEXE% -m venv .venv
    if not exist ".venv\Scripts\activate.bat" (
        echo.
        echo ERROR: could not create a virtual environment with "%PYEXE%".
        echo Install Python 3.10+ from https://www.python.org/downloads/windows/
        pause
        exit /b 1
    )
)

call .venv\Scripts\activate.bat
python -m pip install -q -r requirements.txt

python -m insight_simulator %*
