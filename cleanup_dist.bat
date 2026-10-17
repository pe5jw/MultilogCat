@echo off
echo ============================================
echo  MultiLogCAT - Dist opschonen na build
echo ============================================
echo.
echo Dit script verwijdert onnodige bestanden uit dist\MultiLogCAT
echo om de distributiemap en ZIP zo klein mogelijk te maken.
echo.

set "DIST=%~dp0dist\MultiLogCAT"
set "CHROME=%DIST%\ms-playwright\chromium-1248\chrome-win64"

if not exist "%DIST%" (
    echo [FOUT] dist\MultiLogCAT niet gevonden. Voer eerst build_exe.bat uit.
    pause
    exit /b 1
)

:: ── Grootte voor opschonen ───────────────────────────────────────────────────
echo Grootte voor opschonen:
powershell -NoProfile -Command "$d='%DIST%'; '{0:N0} MB' -f ((Get-ChildItem $d -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB)"
echo.

:: ── 1. Chromium headless shell ───────────────────────────────────────────────
echo [1/5] Chromium headless shell controleren...
powershell -NoProfile -Command "$d='%DIST%\ms-playwright'; $found=$false; Get-ChildItem $d -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'chromium_headless_shell-*' } | ForEach-Object { Remove-Item $_.FullName -Recurse -Force; Write-Host '     Verwijderd:' $_.Name; $found=$true }; if (-not $found) { Write-Host '     Niet aanwezig, overgeslagen.' }"

:: ── 2. Locales — alleen nl en en-US bewaren ──────────────────────────────────
echo [2/5] Locales opschonen (bewaar nl.pak + en-US.pak)...
powershell -NoProfile -Command "$loc='%CHROME%\locales'; if (Test-Path $loc) { $del=0; Get-ChildItem $loc -Filter '*.pak' | Where-Object { $_.BaseName -ne 'nl' -and $_.BaseName -ne 'en-US' } | ForEach-Object { Remove-Item $_.FullName -Force; $del++ }; Write-Host '    ' $del 'locale bestanden verwijderd.' } else { Write-Host '     Locales map niet gevonden, overgeslagen.' }"

:: ── 3. node.exe ──────────────────────────────────────────────────────────────
echo [3/5] node.exe verwijderen uit playwright driver...
powershell -NoProfile -Command "$f='%DIST%\_internal\playwright\driver\node.exe'; if (Test-Path $f) { Remove-Item $f -Force; Write-Host '     node.exe verwijderd (~91 MB).' } else { Write-Host '     node.exe niet gevonden, overgeslagen.' }"

:: ── 4. ffmpeg ─────────────────────────────────────────────────────────────────
echo [4/5] ffmpeg verwijderen...
powershell -NoProfile -Command "$d='%DIST%\ms-playwright'; $found=$false; Get-ChildItem $d -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -like 'ffmpeg-*' } | ForEach-Object { Remove-Item $_.FullName -Recurse -Force; Write-Host '     Verwijderd:' $_.Name; $found=$true }; if (-not $found) { Write-Host '     Niet aanwezig, overgeslagen.' }"

:: ── 5. hyphen-data ───────────────────────────────────────────────────────────
echo [5/5] hyphen-data verwijderen...
powershell -NoProfile -Command "$d='%CHROME%\hyphen-data'; if (Test-Path $d) { Remove-Item $d -Recurse -Force; Write-Host '     hyphen-data verwijderd (~2 MB).' } else { Write-Host '     Niet aanwezig, overgeslagen.' }"

:: ── Grootte na opschonen ─────────────────────────────────────────────────────
echo.
echo Grootte na opschonen:
powershell -NoProfile -Command "$d='%DIST%'; '{0:N0} MB' -f ((Get-ChildItem $d -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB)"
echo.
echo ============================================
echo  Klaar! Je kunt nu de ZIP maken:
echo  Compress-Archive -Path dist\MultiLogCAT\* -DestinationPath MultiLogCAT-v1.1.0-windows-x64.zip -Force
echo ============================================
echo.
pause
