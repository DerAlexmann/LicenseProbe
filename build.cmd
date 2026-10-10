@echo off
REM ---------------------------------------------------------------------
REM Baut LicenseProbe.exe neu; das Ergebnis liegt anschliessend in
REM dist\LicenseProbe.exe.
REM
REM Voraussetzung:  pip install pyinstaller
REM Das Symbol entsteht bei Bedarf mit:  python icon_erzeugen.py
REM ---------------------------------------------------------------------
setlocal
cd /d "%~dp0"

REM Python finden: bevorzugt ueber den Windows-Starter py, sonst python
set "PY=py -3"
py -3 --version >nul 2>nul || set "PY=python"

%PY% -m PyInstaller --noconfirm --onefile --windowed --clean ^
  --name "LicenseProbe" ^
  --icon "licenseprobe.ico" ^
  "LicenseProbe.pyw"

if errorlevel 1 (
  echo.
  echo Der Bau ist fehlgeschlagen. Fehlt PyInstaller?
  echo     pip install pyinstaller
  pause
  exit /b 1
)

echo.
echo Fertig: dist\LicenseProbe.exe
pause
