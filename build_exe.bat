@echo off
REM ============================================================
REM  MultiLogCAT — EXE bouwen met PyInstaller
REM  Voer dit uit in de map waar multilogcat.py staat
REM  Vereist: Python 3.10+, pip
REM ============================================================

echo === MultiLogCAT EXE builder ===
echo.

REM Stap 1: benodigde pakketten installeren
echo [1/3] Pakketten installeren...
pip install playwright pyinstaller --quiet
if errorlevel 1 (
    echo FOUT: pip install mislukt.
    pause & exit /b 1
)

REM Stap 2: EXE bouwen (zonder Chromium meegebundeld)
echo [2/3] EXE bouwen...
pyinstaller ^
  --onedir ^
  --windowed ^
  --name MultiLogCAT ^
  --hidden-import playwright ^
  --hidden-import playwright.sync_api ^
  --collect-all playwright ^
  multilogcat.py

if errorlevel 1 (
    echo FOUT: PyInstaller mislukt.
    pause & exit /b 1
)

REM Stap 3: Chromium installeren IN de dist map
echo [3/3] Chromium downloaden naast de EXE...
set PLAYWRIGHT_BROWSERS_PATH=%CD%\dist\MultiLogCAT\ms-playwright
playwright install chromium

if errorlevel 1 (
    echo FOUT: Chromium download mislukt.
    pause & exit /b 1
)

REM Maak start.bat die de omgevingsvariabele goed zet
(
echo @echo off
echo set PLAYWRIGHT_BROWSERS_PATH=%%~dp0ms-playwright
echo start "" "%%~dp0MultiLogCAT.exe"
) > dist\MultiLogCAT\MultiLogCAT_start.bat

REM Stap 4: Onnodige bestanden opschonen (locales, node.exe, ffmpeg, hyphen-data)
echo [4/4] Dist opschonen...
call cleanup_dist.bat

echo.
echo === Klaar! ===
echo.
echo Distribueer de hele map: dist\MultiLogCAT\
echo Starten via:             dist\MultiLogCAT\MultiLogCAT_start.bat
echo.
echo LET OP: kopieer de map in zijn geheel — de ms-playwright submap
echo         moet naast MultiLogCAT.exe blijven staan.
echo.
pause
