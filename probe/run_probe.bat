@echo off
REM Insight MQTT Discovery Probe - Windows launcher.
REM Run this from the probe\ directory. Requires Python 3.10+ installed.

cd /d "%~dp0"

REM Prefer the "py" launcher (installed by python.org's Windows installer):
REM on some machines "python"/"python3" resolve to the Microsoft Store stub
REM instead of a real interpreter, which fails silently. Fall back to
REM "python" only if "py" is not available.
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
        echo ^(check "Add python.exe to PATH" during install^) and try again.
        pause
        exit /b 1
    )
)

call .venv\Scripts\activate.bat
python -m pip install -q -r requirements.txt

echo Starting Insight MQTT Discovery Probe...
python -m insight_probe

pause
