@echo off
echo RyanRent Eindafrekening Generator
echo =================================
echo.

REM Check if python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Fout: Python is niet gevonden!
    echo Installeer Python van https://www.python.org/downloads/
    pause
    exit /b
)

REM Check if requirements are installed (simple check)
pip show openpyxl >nul 2>&1
if %errorlevel% neq 0 (
    echo Eerste keer opstarten: bibliotheken installeren...
    pip install -r requirements.txt
)

REM Run the script
python generate.py

echo.
pause
