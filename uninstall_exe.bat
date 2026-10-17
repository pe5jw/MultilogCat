@echo off
setlocal enabledelayedexpansion
echo ============================================
echo  MultiLogCAT - Verwijderen (EXE versie)
echo ============================================
echo.
echo Dit script verwijdert MultiLogCAT van deze pc.
echo Python is NIET nodig en wordt NIET aangeraakt.
echo.
pause

set SCRIPTDIR=%~dp0
set SCRIPTDIR=%SCRIPTDIR:~0,-1%

echo.
echo ── Stap 1: Opgeslagen instellingen verwijderen (config.json) ────────────
echo    Hierin staan je radio-instellingen en eventueel je wachtwoord.
echo    Pad: %SCRIPTDIR%\config.json
echo.
if exist "%SCRIPTDIR%\config.json" (
    set /p ANT="  config.json verwijderen? [j/n]: "
    if /i "!ANT!"=="j" (
        del /f "%SCRIPTDIR%\config.json"
        echo    [OK] config.json verwijderd.
    ) else (
        echo    [Overgeslagen]
    )
) else (
    echo    [config.json niet gevonden]
)

echo.
echo ── Stap 2: Volledige MultiLogCAT map verwijderen ────────────────────────
echo    Pad: %SCRIPTDIR%
echo    Dit verwijdert de EXE, Chromium en alle overige bestanden.
echo    LET OP: dit kan enkele minuten duren (Chromium is groot).
echo.
set /p ANT="  Alles verwijderen? [j/n]: "
if /i "!ANT!"=="j" (
    echo    Verwijdering wordt gestart nadat dit venster sluit...
    start "" /b cmd /c "ping 127.0.0.1 -n 3 >nul & rmdir /s /q ""%SCRIPTDIR%"""
    echo    [OK] Verwijdering gepland.
) else (
    echo    [Overgeslagen]
)

echo.
echo ============================================
echo  Klaar! MultiLogCAT is verwijderd.
echo ============================================
echo.
pause
