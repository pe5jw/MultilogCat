# MultiLogCAT

**Automatisch frequentie, band en mode vanuit de radio invullen in het online [Multilog](https://multilog.endoria.net) logboek.**

Ontwikkeld door PE5JW voor gebruik op JOTA en andere activiteiten met het PA6VLG/J station.

---

## Wat doet het?

MultiLogCAT verbindt via **Hamlib / rigctld** (CAT-interface) met je radio en leest elke 2 seconden de actuele frequentie en mode uit. Zodra er iets verandert, worden de velden `freq`, `band` en `mode` in het online Multilog logboek automatisch bijgewerkt via een Playwright-gestuurde Chromium browser.

Je logt zelf de QSO's in — MultiLogCAT zorgt dat de frequentie altijd klopt.

---

## Functies

- Ondersteunt seriële (COM) en netwerk (IP:poort) verbindingen
- Directe verbinding met **SparkSDR** (poort 51111), **FLRig** (12345), **SDR Console** (4532) en rigctld
- Grote lijst van Icom, Yaesu, Kenwood en Elecraft radio's
- Multi-user ondersteuning: wachtwoord optioneel opslaan, login-dialoog bij elk starten
- Bouwbaar als Windows EXE (geen Python vereist op doelcomputer)

---

## Vereisten

| Software | Versie | Link |
|---|---|---|
| Python | 3.10+ | [python.org](https://www.python.org/downloads/) |
| Playwright | via pip | — |
| Chromium | via playwright | — |
| Hamlib | 4.7.2 (alleen bij COM) | [GitHub releases](https://github.com/Hamlib/Hamlib/releases/tag/4.7.2) |

> **SparkSDR / FLRig gebruikers:** Hamlib is niet nodig. MultiLogCAT verbindt direct via het netwerk.

---

## Installatie

```powershell
pip install playwright
playwright install chromium
python multilogcat.py
```

---

## EXE bouwen (zonder Python op doelcomputer)

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

---

## Credits

**Multilog 2019 by [PA3TON](https://multilog.endoria.net)**  
MultiLogCAT door PE5JW & Claude (Anthropic)

---

## Licentie

MIT — vrij te gebruiken en aan te passen.
