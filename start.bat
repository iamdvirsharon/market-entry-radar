@echo off
title Market Entry Radar
echo.
echo  =============================================
echo   Market Entry Radar - Starting Web UI...
echo  =============================================
echo.

cd /d "%~dp0"

echo Installing dependencies (first run only)...
pip install -r requirements.txt --quiet 2>nul

echo.
echo Launching app in your browser...
echo (Keep this window open while using the app)
echo.

python -m streamlit run app.py

if %errorlevel% neq 0 (
    echo.
    echo  ERROR: Something went wrong. Make sure Python 3.10+ is installed.
    echo  Download Python: https://www.python.org/downloads/
    echo.
    pause
)
