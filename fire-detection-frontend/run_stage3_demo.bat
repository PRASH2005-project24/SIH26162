@echo off
REM =====================================================
REM Fire Intelligence Dashboard - Stage 3 Test Batch File
REM =====================================================
REM
REM This batch file sets up and runs the Stage 3 dashboard
REM in demo mode for testing and verification.
REM
REM Usage: Double-click this file or run from command prompt
REM

setlocal enabledelayedexpansion

REM =====================================================
REM COLORS AND FORMATTING
REM =====================================================

echo.
echo =====================================================
echo  FIRE INTELLIGENCE DASHBOARD - STAGE 3
echo  Testing & Verification Batch Script
echo =====================================================
echo.

REM =====================================================
REM CHECK SYSTEM REQUIREMENTS
REM =====================================================

echo [STEP 1/5] Checking system requirements...
echo.

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python is installed
    for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
    echo     Version: !PYTHON_VERSION!
) else (
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Please install Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

REM =====================================================
REM VERIFY PROJECT STRUCTURE
REM =====================================================

echo.
echo [STEP 2/5] Verifying project structure...
echo.

if not exist "index.html" (
    echo [ERROR] index.html not found in current directory
    echo Please run this batch file from the project root directory
    pause
    exit /b 1
)

if not exist "style.css" (
    echo [ERROR] style.css not found
    pause
    exit /b 1
)

if not exist "script.js" (
    echo [ERROR] script.js not found
    pause
    exit /b 1
)

if not exist "src\config.js" (
    echo [ERROR] src\config.js not found
    pause
    exit /b 1
)

if not exist "src\adapters\mockAdapter.js" (
    echo [ERROR] src\adapters\mockAdapter.js not found
    pause
    exit /b 1
)

echo [OK] All required files found:
echo     - index.html
echo     - style.css
echo     - script.js
echo     - src\config.js
echo     - src\adapters\mockAdapter.js
echo     - src\services\*.js

REM =====================================================
REM SELECT PORT
REM =====================================================

echo.
echo [STEP 3/5] Checking available ports...
echo.

set PORT=8080
set DEFAULT_PORT=8080

REM Check if port 8080 is in use
netstat -ano | findstr ":8080" >nul 2>&1
if %errorlevel% equ 0 (
    echo [WARNING] Port 8080 is already in use
    echo.
    set /p PORT="Enter alternative port (default 8000): "
    if "!PORT!"=="" set PORT=8000
) else (
    echo [OK] Port 8080 is available
    set PORT=8080
)

echo Using port: !PORT!

REM =====================================================
REM DISPLAY CONFIGURATION
REM =====================================================

echo.
echo [STEP 4/5] Configuration Summary
echo =====================================================
echo.
echo Application: Fire Intelligence Dashboard - Stage 3
echo Mode: DEMO (Using mock data)
echo.
echo Demo Data Includes:
echo   - 5 Thermal Events
echo   - All 5 Fire Classifications
echo   - Complete Enrichment Data
echo   - ML Predictions with Confidence
echo   - Satellite Metadata
echo   - Dynamic World Land Cover Data
echo.
echo Features Enabled:
echo   - Interactive India Map
echo   - Risk-based Markers
echo   - Selected Detection Panel
echo   - Quick Summary Cards
echo   - Dynamic World Donut Chart
echo   - Satellite Preview
echo   - Dark Mode
echo   - Settings Page
echo   - Fully Responsive Design
echo.
echo Backend Integration (Ready for Later):
echo   - Stage 1/1B API Adapter (ready for real backend)
echo   - Stage 2 ML Adapter (ready for ML service)
echo   - Configurable API URLs (in Settings)
echo   - PostgreSQL/PostGIS NOT required for demo
echo.
echo =====================================================

REM =====================================================
REM START HTTP SERVER
REM =====================================================

echo.
echo [STEP 5/5] Starting HTTP Server...
echo.
echo =====================================================
echo  Server Information
echo =====================================================
echo.
echo Local URL: http://localhost:!PORT!/
echo.
echo Press Ctrl+C to stop the server
echo.
echo =====================================================
echo.

REM Start Python HTTP server
python -m http.server !PORT! --directory .

REM If Python server fails, try alternative
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to start Python HTTP server
    echo Trying alternative method...
    echo.
    python -m SimpleHTTPServer !PORT!
)

pause
