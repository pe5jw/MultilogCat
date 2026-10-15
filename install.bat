@echo off
echo ============================================
echo  MultiLogCAT - Installatie
echo ============================================
echo.
echo Playwright installeren...
pip install playwright
echo.
echo Chromium browser downloaden...
playwright install chromium
echo.
echo Klaar! Start de app met start.bat
pause
