@echo off
TITLE RyanRent Eindafrekening Generator

REM ==========================================
REM RyanRent Eindafrekening Generator - Launcher
REM ==========================================

REM 1. Ga naar de map waar dit script staat
cd /d "%~dp0"

echo 🚀 RyanRent Generator wordt gestart...
echo 📂 Werkmap: %CD%

REM 2. Activeer Virtual Environment (als die bestaat)
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo ⚠️  Geen 'venv' map gevonden. We proberen de standaard python...
)

REM 3. Check of input bestand bestaat (in root map)
if not exist "input_template.xlsx" (
    echo ❌ FOUT: 'input_template.xlsx' niet gevonden!
    echo    Zorg dat dit bestand in de map '%CD%' staat.
    pause
    exit /b 1
)

REM 4. Start de generator (vanuit src map)
REM --no-pause: Zodat we hieronder zelf de pause kunnen beheren
REM --auto-open: Open browser automatisch
python src/generate.py --no-pause --auto-open

REM 5. Einde
echo.
pause
