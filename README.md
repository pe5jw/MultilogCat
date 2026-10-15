# MultiLogCAT

**Automatisch frequentie, band en mode vanuit de radio invullen in het online [Multilog](https://multilog.endoria.net) logboek.**

Ontwikkeld door PE5JW voor gebruik op JOTA en andere activiteiten met het PA6VLG/J station.

> ⚠️ **Beta / snel gebouwd voor JOTA 2026**
> Deze app is in korte tijd gemaakt voor een specifiek evenement, weinig getest en kan bugs bevatten.
> Gebruik op eigen risico. Feedback en bugmeldingen welkom via [Issues](../../issues).

---

## Wat doet het?

MultiLogCAT verbindt via **Hamlib / rigctld** (CAT-interface) met je radio en leest elke 2 seconden de actuele frequentie en mode uit. Zodra er iets verandert, worden de velden `freq`, `band` en `mode` in het online Multilog logboek automatisch bijgewerkt via een Playwright-gestuurde Chromium browser.

Je logt zelf de QSO's in — MultiLogCAT zorgt dat de frequentie altijd klopt.

---

## Functies

- Ondersteunt seriële (COM/tty) en netwerk (IP:poort) verbindingen
- Directe verbinding met **SparkSDR** (poort 51111), **FLRig** (12345), **SDR Console** (4532) en rigctld
- Grote lijst van Icom, Yaesu, Kenwood en Elecraft radio's
- Multi-user ondersteuning: wachtwoord optioneel opslaan, login-dialoog bij elk starten
- Windows: bouwbaar als EXE (geen Python vereist op doelcomputer)
- Linux: experimentele ondersteuning (niet getest — zie hieronder)

---

## Platform ondersteuning

| Platform | Status |
|---|---|
| Windows 10/11 | ✅ Getest |
| Linux (Ubuntu/Debian/Fedora) | ⚠️ Experimenteel — **niet getest** |
| macOS | ❓ Onbekend — niet getest |

---

## Vereisten

| Software | Versie | Link |
|---|---|---|
| Python | 3.10+ | [python.org](https://www.python.org/downloads/) |
| Playwright | via pip | — |
| Chromium | via playwright | — |
| Hamlib | 4.7.2 (alleen bij COM/tty) | [GitHub releases](https://github.com/Hamlib/Hamlib/releases/tag/4.7.2) |

> **SparkSDR / FLRig gebruikers:** Hamlib is niet nodig. MultiLogCAT verbindt direct via het netwerk.

---

## Installatie — Windows

```powershell
pip install playwright
playwright install chromium
python multilogcat.py
```

Of gebruik `install.bat` voor een begeleide installatie.

## Installatie — Linux ⚠️ experimenteel, niet getest

```bash
chmod +x install_linux.sh
./install_linux.sh
python3 multilogcat.py
```

**Linux-specifieke opmerkingen:**
- Seriële poort: gebruik `/dev/ttyUSB0` of `/dev/ttyS0` (niet `COM3`)
- Rechten seriële poort: `sudo usermod -aG dialout $USER` (daarna uitloggen/inloggen)
- rigctld pad: `which rigctld` geeft het pad

---

## EXE bouwen — Windows (geen Python op doelcomputer)

```bat
build_exe.bat
```

Het script installeert PyInstaller, bouwt de EXE en plaatst Chromium naast de EXE in `dist\MultiLogCAT\ms-playwright\`.
Kopieer de **volledige** map `dist\MultiLogCAT\` en start via `MultiLogCAT_start.bat`.

---

## Hamlib licentie

Hamlib valt onder de **GPL v2** licentie en mag niet meegeleverd worden in andere software.
Gebruik de **⬇ Download Hamlib** link in de app, of download direct van de [Hamlib releases pagina](https://github.com/Hamlib/Hamlib/releases/tag/4.7.2).

---

## Gebruik

1. Start de app
2. Kies je radio model en verbindingstype
3. Vul de Multilog website URL, call en wachtwoord in
4. Klik **▶ Start**
5. De Chromium browser opent en logt automatisch in
6. Draai op je frequentie — freq, band en mode worden automatisch bijgewerkt

---

## Instellingen (config.json)

De configuratie wordt opgeslagen als `config.json` naast de app (of naast de EXE).
Wachtwoord opslaan is optioneel via het vinkje in de app.
`config.json` staat in `.gitignore` en wordt nooit mee gecommit.

---

## Bekende beperkingen / bugs

- Weinig getest — gemaakt voor JOTA 2026 in beperkte tijd
- Linux ondersteuning is niet getest
- De browser blijft open tijdens gebruik (bewust — zodat je de site ook handmatig kunt bedienen)
- Bij trage internetverbinding kan de injectie van freq/band/mode soms een seconde later zijn

---

## Credits

**Multilog 2019 by [PA3TON](https://multilog.endoria.net)**
MultiLogCAT door PE5JW & Claude (Anthropic)

---

## Licentie

MIT — vrij te gebruiken en aan te passen.
