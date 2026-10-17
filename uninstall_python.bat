@echo off
setlocal enabledelayedexpansion
echo ============================================
echo  MultiLogCAT - Verwijderen (Python versie)
echo ============================================
echo.
echo Dit script verwijdert MultiLogCAT en de bijbehorende Python pakketten.
echo Python zelf wordt NIET verwijderd.
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
echo ── Stap 2: Playwright Chromium browser verwijderen ──────────────────────
echo    De Chromium browser die Playwright heeft gedownload.
echo    (staat in %%USERPROFILE%%\AppData\Local\ms-playwright)
echo.
set /p ANT="  Chromium verwijderen? [j/n]: "
if /i "!ANT!"=="j" (
    python -m playwright uninstall chromium >nul 2>&1
    echo    [OK] Chromium verwijderd.
    if exist "%USERPROFILE%\AppData\Local\ms-playwright" (
        set /p ANT2="  ms-playwright map nog aanwezig, volledig verwijderen? [j/n]: "
        if /i "!ANT2!"=="j" (
            rmdir /s /q "%USERPROFILE%\AppData\Local\ms-playwright"
            echo    [OK] ms-playwright map verwijderd.
        )
    )
) else (
    echo    [Overgeslagen]
)

echo.
echo ── Stap 3: Playwright pip pakket verwijderen ────────────────────────────
echo    Verwijdert Playwright uit Python. Andere programma's die Playwright
echo    gebruiken werken daarna niet meer.
echo.
set /p ANT="  Playwright (pip) verwijderen? [j/n]: "
if /i "!ANT!"=="j" (
    python -m pip uninstall playwright -y >nul 2>&1
    if errorlevel 1 (
        echo    [WAARSCHUWING] Mislukt of al verwijderd.
    ) else (
        echo    [OK] Playwright verwijderd.
    )
) else (
    echo    [Overgeslagen]
)

echo.
echo ── Stap 4: MultiLogCAT programmabestanden verwijderen ───────────────────
echo    Verwijdert multilogcat.py, install.bat en overige bestanden.
echo    De map zelf blijft staan tenzij je stap 5 ook uitvoert.
echo.
set /p ANT="  Programmabestanden verwijderen? [j/n]: "
if /i "!ANT!"=="j" (
    for %%f in (
        "%SCRIPTDIR%\multilogcat.py"
        "%SCRIPTDIR%\install.bat"
        "%SCRIPTDIR%\uninstall_python.bat"
        "%SCRIPTDIR%\start.bat"
        "%SCRIPTDIR%\handleiding.html"
        "%SCRIPTDIR%\install_linux.sh"
        "%SCRIPTDIR%\screenshot.png"
        "%SCRIPTDIR%\README.md"
    ) do (
        if exist %%f (
            del /f %%f
            echo    [OK] %%~nxf verwijderd.
        )
    )
    if exist "%SCRIPTDIR%\__pycache__" (
        rmdir /s /q "%SCRIPTDIR%\__pycache__"
        echo    [OK] __pycache__ verwijderd.
    )
) else (
    echo    [Overgeslagen]
)

echo.
echo ── Stap 5: Volledige map verwijderen ────────────────────────────────────
echo    Pad: %SCRIPTDIR%
echo    Verwijdert de hele map inclusief eventuele overige bestanden.
echo.
set /p ANT="  Volledige map verwijderen? [j/n]: "
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
