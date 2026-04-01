@echo off
REM Deployment script for Link1Die (Windows)

setlocal enabledelayedexpansion

echo.
echo 🚀 Link1Die Deployment Script
echo.

REM Check prerequisites
echo Checking prerequisites...
where docker >nul 2>nul
if errorlevel 1 (
    echo ❌ Docker is not installed
    exit /b 1
)

where docker-compose >nul 2>nul
if errorlevel 1 (
    echo ❌ Docker Compose is not installed
    exit /b 1
)

echo ✓ Docker and Docker Compose found
echo.

REM Load environment variables
if exist .env (
    echo ✓ Environment file found
) else (
    echo ❌ .env file not found
    exit /b 1
)

REM Build services
echo Building services...
docker-compose -f docker/docker-compose.yml build
if errorlevel 1 (
    echo ❌ Build failed
    exit /b 1
)

REM Start services
echo Starting services...
docker-compose -f docker/docker-compose.yml up -d
if errorlevel 1 (
    echo ❌ Failed to start services
    exit /b 1
)

REM Wait for services
echo Waiting for services to be healthy...
timeout /t 5 /nobreak

REM Run migrations
echo Running database migrations...
docker-compose -f docker/docker-compose.yml exec -T api alembic upgrade head

REM Display service status
echo.
echo Service Status:
docker-compose -f docker/docker-compose.yml ps

echo.
echo ✅ Deployment Complete!
echo.
echo Services Available:
echo   API: http://localhost:8000
echo   Docs: http://localhost:8000/docs
echo   Web: http://localhost:80
echo   Database: localhost:5432 (postgres:password)
echo   Redis: localhost:6379
echo.
echo Useful Commands:
echo   View logs: docker-compose -f docker/docker-compose.yml logs -f api
echo   Stop services: docker-compose -f docker/docker-compose.yml down
