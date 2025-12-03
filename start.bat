@echo off
echo ========================================
echo   RyanRent Intelligence Bot - Docker
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Check if .env exists
if not exist .env (
    echo ERROR: .env file not found!
    echo.
    echo Please create a .env file with your API keys:
    echo   ANTHROPIC_API_KEY=your_key_here
    echo   OPENAI_API_KEY=your_key_here
    echo.
    pause
    exit /b 1
)

echo Starting RyanRent Intelligence Bot...
echo.

docker-compose up --build

pause
