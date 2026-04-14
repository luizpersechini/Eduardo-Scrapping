@echo off
setlocal enabledelayedexpansion
title ANBIMA Fund Scraper

REM Move to the script's own directory so paths are stable regardless of how it's launched
cd /d "%~dp0"

echo ================================================================
echo   ANBIMA Fund Data Scraper - Local Launcher
echo ================================================================
echo.

REM -----------------------------------------------------------------
REM  1. Verify Python is installed and on PATH
REM -----------------------------------------------------------------
where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    echo.
    echo Please install Python 3.11 or newer from:
    echo    https://www.python.org/downloads/windows/
    echo.
    echo IMPORTANT: During installation, check the box
    echo            "Add python.exe to PATH"
    echo.
    pause
    exit /b 1
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PY_VERSION=%%v
echo Detected Python %PY_VERSION%
echo.

REM -----------------------------------------------------------------
REM  2. Verify Chrome is installed (scraper drives a real browser)
REM -----------------------------------------------------------------
set CHROME_FOUND=0
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set CHROME_FOUND=1
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set CHROME_FOUND=1
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set CHROME_FOUND=1

if !CHROME_FOUND! EQU 0 (
    echo [WARNING] Google Chrome was not found in standard locations.
    echo           The scraper requires Google Chrome to run.
    echo           Install it from: https://www.google.com/chrome/
    echo.
    choice /c YN /m "Continue anyway"
    if errorlevel 2 exit /b 1
)

REM -----------------------------------------------------------------
REM  3. First-run setup: create venv and install dependencies
REM -----------------------------------------------------------------
if not exist "venv\Scripts\activate.bat" (
    echo First run detected. Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )

    echo.
    echo Installing dependencies ^(this may take a few minutes the first time^)...
    echo.
    call venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install dependencies. See the output above.
        pause
        exit /b 1
    )
    echo.
    echo Setup complete.
    echo.
) else (
    call venv\Scripts\activate.bat
)

REM -----------------------------------------------------------------
REM  4. Launch the Streamlit app
REM -----------------------------------------------------------------
echo ================================================================
echo   Starting ANBIMA Scraper...
echo   The app will open in your default browser automatically.
echo   To stop the app, close this window or press Ctrl+C.
echo ================================================================
echo.

python -m streamlit run streamlit_app.py --server.headless=false --browser.gatherUsageStats=false

REM If streamlit exits, keep the window open so the user can read any errors
echo.
echo Streamlit has stopped.
pause
endlocal
