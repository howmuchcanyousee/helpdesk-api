@echo off
setlocal

cd /d "%~dp0"

where docker >nul 2>nul
if errorlevel 1 (
    echo Docker was not found. Install and start Docker Desktop first.
    pause
    exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
    echo Docker Engine is not running. Start Docker Desktop and try again.
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

findstr /b /c:"POSTGRES_PASSWORD=" ".env" >nul
if errorlevel 1 (
    echo POSTGRES_PASSWORD is missing in .env. Update it from .env.example.
    pause
    exit /b 1
)

findstr /b /c:"DATABASE_URL=" ".env" >nul
if errorlevel 1 (
    echo DATABASE_URL is missing in .env. Update it from .env.example.
    pause
    exit /b 1
)

findstr /c:"replace_with_a_local_development_password" ".env" >nul
if not errorlevel 1 (
    echo Replace the PostgreSQL password in POSTGRES_PASSWORD and DATABASE_URL.
    pause
    exit /b 1
)

findstr /b /c:"SECRET_KEY=" ".env" >nul
if errorlevel 1 (
    echo SECRET_KEY is missing in .env. Update it from .env.example.
    pause
    exit /b 1
)

findstr /b /c:"SECRET_KEY=replace_" ".env" >nul
if not errorlevel 1 (
    echo Replace SECRET_KEY in .env with a random value of at least 32 characters.
    pause
    exit /b 1
)

echo Starting Helpdesk API...
docker compose up --build

pause
