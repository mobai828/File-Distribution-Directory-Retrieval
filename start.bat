@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
title Start - Document Search App

set "HOST=127.0.0.1"
set "PORT=8000"
set "URL=http://%HOST%:%PORT%/"

echo =========================================
echo Starting app...
echo =========================================

set "PYTHON=python"
if exist ".venv\Scripts\python.exe" set "PYTHON=.venv\Scripts\python.exe"
if exist "venv\Scripts\python.exe" set "PYTHON=venv\Scripts\python.exe"

%PYTHON% -V >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found.
    echo Install Python 3.11/3.12 and enable PATH, or create .venv.
    echo.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment .venv ...
    %PYTHON% -m venv .venv >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Failed to create .venv.
        echo.
        pause
        exit /b 1
    )
    set "PYTHON=.venv\Scripts\python.exe"
)

%PYTHON% -m pip -V >nul 2>&1
if errorlevel 1 (
    echo Fixing pip with ensurepip ...
    %PYTHON% -m ensurepip --upgrade >nul 2>&1
)

%PYTHON% -m pip -V >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip unavailable.
    echo.
    pause
    exit /b 1
)

%PYTHON% -c "import fastapi,uvicorn" >nul 2>&1
if errorlevel 1 (
    echo Installing requirements...
    %PYTHON% -m pip install -r requirements.txt
)

%PYTHON% -c "import fastapi,uvicorn" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Dependency install failed.
    echo Run: %PYTHON% -m pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

netstat -ano | findstr :%PORT% | findstr LISTENING >nul
if not errorlevel 1 (
    echo [WARN] Port %PORT% is already in use.
    echo Open %URL% directly, or run stop.bat first.
    echo.
    pause
    exit /b
)

echo [1/2] Starting backend on %PORT%...
start "App Backend" cmd /k ""%PYTHON%" -m uvicorn main:app --host %HOST% --port %PORT% --reload"

echo Waiting for service: %URL%
powershell -NoProfile -Command "$u='%URL%'; $ok=$false; for($i=0;$i -lt 60;$i++){ try{ Invoke-WebRequest -UseBasicParsing -Uri $u -TimeoutSec 1 ^| Out-Null; $ok=$true; break } catch { Start-Sleep -Milliseconds 500 } }; if(-not $ok){ exit 1 }"
set "WAIT_ERROR=%errorlevel%"

echo [2/2] Opening browser...
start "" "%URL%"

echo.
if "%WAIT_ERROR%"=="0" (
    echo =========================================
    echo Startup success.
    echo Service URL: %URL%
    echo Stop with stop.bat
    echo =========================================
) else (
    echo =========================================
    echo Browser opened, but backend may not be ready.
    echo Check the "App Backend" window for details.
    echo =========================================
)
timeout /t 3 >nul