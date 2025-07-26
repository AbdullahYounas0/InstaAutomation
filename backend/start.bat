@echo off
echo.
echo ================================
echo Instagram Daily Post Backend
echo ================================
echo.

echo Checking dependencies...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

echo ✅ Python is installed

REM Check if pip is available
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip is not available
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)

echo ✅ pip is available

REM Install dependencies if requirements.txt exists
if exist "requirements.txt" (
    echo.
    echo Installing Python dependencies...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ Failed to install dependencies
        pause
        exit /b 1
    )
    echo ✅ Dependencies installed
) else (
    echo ⚠️  requirements.txt not found, skipping dependency installation
)

REM Check if Playwright browsers are installed
echo.
echo Checking Playwright browsers...
python -c "from playwright.sync_api import sync_playwright; print('Playwright available')" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Playwright not available
    echo Please install Playwright: pip install playwright
    pause
    exit /b 1
)

REM Install Playwright browsers
echo Installing Playwright browsers...
python -m playwright install chromium
if %errorlevel% neq 0 (
    echo ❌ Failed to install Playwright browsers
    pause
    exit /b 1
)

echo ✅ Playwright browsers installed

REM Test if the app can import successfully
echo.
echo Testing Flask app...
python -c "from app import app; print('Flask app ready')" >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Flask app has import errors
    echo Please check the app.py file for issues
    pause
    exit /b 1
)

echo ✅ Flask app ready

echo.
echo ================================
echo 🚀 Starting Backend Server...
echo ================================
echo.
echo Backend will be available at:
echo   • http://localhost:5000
echo   • http://127.0.0.1:5000
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the Flask app
python app.py
