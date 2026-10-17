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

REM Stap 4: Uninstall script kopiëren naar dist (voor clients)
echo [4/6] Uninstall script kopiëren...
copy /y uninstall_exe.bat dist\MultiLogCAT\uninstall.bat >nul
echo      uninstall.bat gekopieerd naar dist\MultiLogCAT\

REM Stap 5: Hamlib downloaden en meebundelen
echo [5/6] Hamlib downloaden en meebundelen...
set HAMLIB_ZIP=hamlib-w64-4.7.2.zip
set HAMLIB_URL=https://github.com/Hamlib/Hamlib/releases/download/4.7.2/hamlib-w64-4.7.2.zip
set HAMLIB_DIST=dist\MultiLogCAT\hamlib

powershell -NoProfile -Command ^
  "if (-not (Test-Path '%HAMLIB_ZIP%')) { Write-Host '     Downloaden...'; Invoke-WebRequest -Uri '%HAMLIB_URL%' -OutFile '%HAMLIB_ZIP%' } else { Write-Host '     Al aanwezig, overgeslagen.' }"

powershell -NoProfile -Command ^
  "Write-Host '     Uitpakken...'; Expand-Archive -Path '%HAMLIB_ZIP%' -DestinationPath '_hamlib_tmp' -Force; New-Item -ItemType Directory -Force -Path '%HAMLIB_DIST%' | Out-Null; Copy-Item '_hamlib_tmp\hamlib-w64-4.7.2\bin\rigctld.exe'        '%HAMLIB_DIST%\' -Force; Copy-Item '_hamlib_tmp\hamlib-w64-4.7.2\bin\libhamlib-4.dll'     '%HAMLIB_DIST%\' -Force; Copy-Item '_hamlib_tmp\hamlib-w64-4.7.2\bin\libgcc_s_seh-1.dll'  '%HAMLIB_DIST%\' -Force; Copy-Item '_hamlib_tmp\hamlib-w64-4.7.2\bin\libwinpthread-1.dll' '%HAMLIB_DIST%\' -Force; Copy-Item '_hamlib_tmp\hamlib-w64-4.7.2\bin\libusb-1.0.dll'       '%HAMLIB_DIST%\' -Force; Copy-Item '_hamlib_tmp\hamlib-w64-4.7.2\COPYING.LIB.txt'        '%HAMLIB_DIST%\' -Force; Copy-Item '_hamlib_tmp\hamlib-w64-4.7.2\LICENSE.txt'             '%HAMLIB_DIST%\' -Force; Remove-Item '_hamlib_tmp' -Recurse -Force; Write-Host '     Hamlib meegezet in hamlib\ (rigctld.exe + DLLs + licentie).'"

if errorlevel 1 (
    echo WAARSCHUWING: Hamlib bundelen mislukt. Handmatig kopiëren naar dist\MultiLogCAT\hamlib\
)

REM Stap 6: Onnodige bestanden opschonen (locales, node.exe, ffmpeg, hyphen-data)
echo [6/6] Dist opschonen...
call cleanup_dist.bat

echo.
echo === Klaar! ===
echo.
echo Distribueer de hele map: dist\MultiLogCAT\
echo Starten via:             dist\MultiLogCAT\MultiLogCAT_start.bat
echo Verwijderen via:         dist\MultiLogCAT\uninstall.bat
echo Hamlib (rigctld):        dist\MultiLogCAT\hamlib\rigctld.exe
echo.
echo LET OP: kopieer de map in zijn geheel — de ms-playwright submap
echo         moet naast MultiLogCAT.exe blijven staan.
echo.
pause
