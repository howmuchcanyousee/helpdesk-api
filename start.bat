@echo off
setlocal

cd /d "%~dp0"

where docker >nul 2>nul
if errorlevel 1 (
    echo Docker was not found. Install and start Docker Desktop first.
    pause
    exit /b 1
)

docker compose version >nul 2>nul
if errorlevel 1 (
    echo Docker Compose is not available. Update Docker Desktop and try again.
    pause
    exit /b 1
)

if not exist ".env" (
    copy /y ".env.example" ".env" >nul
    echo Created .env from .env.example.
)

echo Starting Helpdesk API...
docker compose up --build

pause
