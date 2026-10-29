@echo off
cd /d "%~dp0.."
if not exist .venv\Scripts\python.exe (
  echo Δεν βρέθηκε .venv. Τρέξε πρώτα: py -3.12 -m venv .venv ^&^& .venv\Scripts\pip install -r requirements.txt
  pause & exit /b 1
)
start "" .venv\Scripts\pythonw.exe tooldock.pyw
