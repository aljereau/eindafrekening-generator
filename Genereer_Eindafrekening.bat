@echo off
REM RyanRent Eindafrekening Generator - Easy Launcher (Windows)
REM Double-click this file to generate eindafrekening

cd /d "%~dp0"

cls
echo ================================================================
echo      RyanRent Eindafrekening Generator
echo ================================================================
echo.
echo Bezig met genereren...
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo FOUT: Virtual environment niet gevonden!
    echo Neem contact op met de developer.
    echo.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if input_template.xlsx exists
if not exist "input_template.xlsx" (
    echo FOUT: input_template.xlsx niet gevonden!
    echo Zorg dat het Excel bestand in deze map staat.
    echo.
    pause
    exit /b 1
)

REM Run the generator with auto-open browser flag
python generate.py --no-pause --auto-open

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Generatie voltooid!
    echo De HTML bestanden zijn geopend in je browser.
    echo Gebruik Ctrl+P om te printen of op te slaan als PDF.
    echo.
) else (
    echo.
    echo Er is een fout opgetreden tijdens het genereren.
    echo Controleer het Excel bestand en probeer opnieuw.
    echo.
)

pause
