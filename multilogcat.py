"""
MultiLogCAT - CAT interface voor multilog.endoria.net
Leest frequentie, band en mode van de radio via Hamlib/rigctld
en vult deze in op de multilog website via Playwright.
"""

import json
import os
import queue
import socket
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import webbrowser


def open_url(url):
    """Open URL in standaard browser — werkt ook als webbrowser.open faalt."""
    try:
        webbrowser.open(url)
    except Exception:
        pass
    else:
        return
    # Fallback voor Windows zonder standaard browser instelling
    try:
        if sys.platform == "win32":
            os.startfile(url)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", url])
        else:
            subprocess.Popen(["xdg-open", url])
    except Exception as e:
        messagebox.showerror("Link openen mislukt",
                             f"Kan browser niet openen.\nOpen handmatig:\n{url}\n\nFout: {e}")

# Wanneer gebouwd als EXE via PyInstaller: zet Playwright Chromium pad
# zodat de browser naast de EXE gevonden wordt (ms-playwright submap)
if getattr(sys, "frozen", False):
    _exe_dir = Path(sys.executable).parent
    _pw_dir = _exe_dir / "ms-playwright"
    if _pw_dir.exists():
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(_pw_dir)
    # Zet ook PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD zodat Playwright niet
    # opnieuw probeert te downloaden naar %APPDATA%
    os.environ.setdefault("PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD", "1")

# ── Config ──────────────────────────────────────────────────────────────────

# In EXE (PyInstaller frozen): gebruik map van de EXE, niet van _MEIPASS
if getattr(sys, "frozen", False):
    SCRIPT_DIR = Path(sys.executable).parent
else:
    SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "config.json"

RADIO_MODELS = [
    # ── Icom ──────────────────────────────────────────────────────────────────
    ("Icom IC-705",               "3081"),
    ("Icom IC-7100",              "3075"),
    ("Icom IC-7300",              "3073"),
    ("Icom IC-7300MK2",           "3094"),
    ("Icom IC-7610",              "3078"),
    ("Icom IC-7700",              "3070"),
    ("Icom IC-7800",              "3060"),
    ("Icom IC-9700",              "3080"),
    ("Icom IC-9700 v2022+",       "3081"),
    # ── Yaesu ─────────────────────────────────────────────────────────────────
    ("Yaesu FT-817",              "1021"),
    ("Yaesu FT-818",              "1059"),
    ("Yaesu FT-897",              "1023"),
    ("Yaesu FT-897D",             "1043"),
    ("Yaesu FT-950",              "1028"),
    ("Yaesu FT-991A",             "1053"),
    ("Yaesu FT-2000",             "1029"),
    ("Yaesu FT-DX10",             "1061"),
    ("Yaesu FT-DX101D",           "1057"),
    ("Yaesu FT-DX3000",           "1039"),
    # ── Kenwood ───────────────────────────────────────────────────────────────
    ("Kenwood TS-480",            "2016"),
    ("Kenwood TS-590S",           "2022"),
    ("Kenwood TS-590SG",          "2031"),
    ("Kenwood TS-890S",           "2039"),
    ("Kenwood TS-990S",           "2038"),
    ("Kenwood TS-2000",           "2014"),
    # ── Elecraft ──────────────────────────────────────────────────────────────
    ("Elecraft K3",               "2029"),
    ("Elecraft K3S",              "2033"),
    ("Elecraft K4",               "2047"),
    ("Elecraft KX3",              "2028"),
    # ── SDR / Software ────────────────────────────────────────────────────────
    ("SparkSDR / NET rigctl",     "2"),
    ("FLRig",                     "4"),
    ("SDR Console / rigctld",     "2"),
    # ── Handmatig ─────────────────────────────────────────────────────────────
    ("Anders (handmatig model nr.)", "0"),
]

# Bekende netwerk poorten per software
NETWORK_PORTS = {
    "SparkSDR":   "51111",
    "FLRig":      "12345",
    "rigctld":    "4532",
    "SDR Console":"4532",
}

BAUDS = ["1200","2400","4800","9600","19200","38400","57600","115200"]

# Verbindingstype radio
PORT_TYPE_SERIAL = "Serieel (COM)"
PORT_TYPE_NET    = "Netwerk (IP:poort)"

BAND_PLAN = [
    (1_800_000,   2_000_000,  "160m"),
    (3_500_000,   4_000_000,  "80m"),
    (5_250_000,   5_450_000,  "60m"),
    (7_000_000,   7_300_000,  "40m"),
    (10_100_000,  10_150_000, "30m"),
    (14_000_000,  14_350_000, "20m"),
    (18_068_000,  18_168_000, "17m"),
    (21_000_000,  21_450_000, "15m"),
    (24_890_000,  24_990_000, "12m"),
    (28_000_000,  29_700_000, "10m"),
    (50_000_000,  54_000_000, "6m"),
    (144_000_000, 148_000_000,"2m"),
    (430_000_000, 440_000_000,"70cm"),
]

def freq_to_band(freq_hz):
    for lo, hi, band in BAND_PLAN:
        if lo <= freq_hz <= hi:
            return band
    return "?"

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=4)

# ── Hamlib ───────────────────────────────────────────────────────────────────

class RigCtld:
    def __init__(self, host="127.0.0.1", port=4532):
        self.host = host
        self.port = int(port)
        self._sock = None

    def connect(self):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.settimeout(3)
        self._sock.connect((self.host, self.port))

    def disconnect(self):
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None

    def _cmd(self, cmd):
        self._sock.sendall((cmd + "\n").encode())
        resp = b""
        while True:
            chunk = self._sock.recv(1024)
            resp += chunk
            if b"\n" in chunk:
                break
        return resp.decode().strip()

    def get_freq(self):
        r = self._cmd("f")
        lines = [l for l in r.splitlines() if not l.startswith("RPRT")]
        return int(lines[0]) if lines else None

    def get_mode(self):
        r = self._cmd("m")
        lines = [l for l in r.splitlines() if not l.startswith("RPRT")]
        return lines[0] if lines else "?"


# ── Playwright browser vulling ────────────────────────────────────────────────

class MultilogFiller:
    """
    Vult frequentie, band en mode in op de multilog website.
    Draait Playwright in een eigen thread om threading-conflicten te vermijden.
    Communicatie via een queue.
    """
    def __init__(self, cfg):
        self.cfg = cfg
        self._last_error = None
        self._cmd_queue = queue.Queue()
        self._result_queue = queue.Queue()
        self._thread = None
        self._ready = threading.Event()
        self._start_error = None

    def start(self):
        """Start Playwright in een aparte thread en wacht tot ingelogd."""
        self._thread = threading.Thread(target=self._browser_thread, daemon=True)
        self._thread.start()
        # Wacht max 30 sec op klaar-signaal
        if not self._ready.wait(timeout=30):
            raise RuntimeError(self._start_error or "Browser timeout — inloggen duurde te lang")
        if self._start_error:
            raise RuntimeError(self._start_error)

    def _browser_thread(self):
        """Draait volledig in eigen thread — Playwright mag hier alles doen."""
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                # Geef duidelijke foutmelding als Chromium niet gevonden wordt
                try:
                    browser = pw.chromium.launch(headless=False, args=["--start-maximized"])
                except Exception as e:
                    if "Executable doesn't exist" in str(e) or "chrome" in str(e).lower():
                        raise RuntimeError(
                            "Chromium browser niet gevonden.\n\n"
                            "Voer eenmalig uit in PowerShell:\n"
                            "  playwright install chromium\n\n"
                            f"(technisch: {e})"
                        )
                    raise
                ctx = browser.new_context(no_viewport=True)
                page = ctx.new_page()
                self._login(page)
                self._ready.set()  # Login geslaagd — poll loop mag starten

                # Verwerk commando's uit de queue totdat STOP binnenkomt
                while True:
                    try:
                        cmd = self._cmd_queue.get(timeout=1)
                    except queue.Empty:
                        continue
                    if cmd is None:  # stop-signaal
                        break
                    freq_hz, mode = cmd
                    result, err = self._do_fill(page, freq_hz, mode)
                    self._result_queue.put((result, err))

                browser.close()
        except Exception as e:
            self._start_error = str(e)
            self._ready.set()  # Zorg dat start() niet eeuwig wacht

    def _login(self, page):
        w = self.cfg["website"]
        page.goto(w["url"])
        try:
            page.wait_for_selector("input[name='call']", timeout=4000)
            page.fill("input[name='call']", w["username"])
            page.fill("input[name='password']", w["password"])
            page.click("input[type='submit']")
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass  # Al ingelogd
        try:
            page.wait_for_selector("#lb_freq", timeout=6000)
        except Exception:
            raise RuntimeError("Logboekformulier niet gevonden na inloggen. Controleer URL/wachtwoord.")

        self._inject_credit(page)

    def _inject_credit(self, page):
        """Injecteer credit-tekst naast 'PA3TON' — werkt ook na page refresh en in EXE."""
        try:
            # Wacht tot body beschikbaar is (extra veiligheid in EXE / langzame start)
            page.wait_for_selector("body", timeout=5000)
        except Exception:
            pass
        page.evaluate("""
            (function injectCredit() {
                if(document.getElementById('_mlcat_credit')) return;
                var walker = document.createTreeWalker(
                    document.body, NodeFilter.SHOW_TEXT, null, false);
                var textNode = null;
                while(walker.nextNode()) {
                    if(walker.currentNode.textContent.indexOf('PA3TON') >= 0) {
                        textNode = walker.currentNode; break;
                    }
                }
                if(textNode) {
                    var span = document.createElement('span');
                    span.id = '_mlcat_credit';
                    span.textContent = ' met MultilogCAT door PE5JW & Claude';
                    span.style.cssText = 'font-size:inherit;color:inherit;';
                    textNode.parentNode.appendChild(span);
                } else {
                    // Probeer nog eens na 500ms als DOM nog niet klaar was
                    setTimeout(injectCredit, 500);
                }
            })();
        """)

    def _do_fill(self, page, freq_hz, mode_hamlib):
        freq_khz = str(int(freq_hz / 1000))
        # Band naam uit onze eigen bandplan — betrouwbaarder dan de site-index
        band_name = freq_to_band(freq_hz)  # bijv. "20m"
        try:
            # Terug naar logboekpagina als we zijn afgedwaald
            base_url = self.cfg["website"]["url"].split("?")[0]
            if base_url not in page.url:
                page.goto(self.cfg["website"]["url"])
                page.wait_for_load_state("networkidle", timeout=10000)

            if page.query_selector("#lb_freq") is None:
                return False, "Veld lb_freq niet gevonden — sessie verlopen?"

            result = page.evaluate(f"""
                new Promise((resolve) => {{
                    var bandName = "{band_name}";
                    var hamMode  = "{mode_hamlib}".toUpperCase();

                    function setBand() {{
                        var elBand = document.getElementById("lb_band");
                        if(!elBand) return;
                        var matched = false;
                        for(var i=0; i<elBand.options.length; i++) {{
                            var t = elBand.options[i].text.toLowerCase().trim();
                            if(t === bandName.toLowerCase() || t.indexOf(bandName.toLowerCase()) >= 0) {{
                                elBand.selectedIndex = i; matched = true; break;
                            }}
                        }}
                        elBand.dispatchEvent(new Event('change'));
                    }}

                    function setMode() {{
                        var elMode = document.getElementById("lb_mode");
                        if(!elMode) return;
                        for(var i=0; i<elMode.options.length; i++) {{
                            if(elMode.options[i].text.toUpperCase() === hamMode ||
                               elMode.options[i].value.toUpperCase() === hamMode) {{
                                elMode.selectedIndex = i; break;
                            }}
                        }}
                        elMode.dispatchEvent(new Event('change'));
                    }}

                    // Stap 1: freq invullen
                    var elFreq = document.getElementById("lb_freq");
                    if(elFreq) elFreq.value = "{freq_khz}";

                    // Stap 2: searchFreq aanroepen (site's eigen logica)
                    var xhr = new XMLHttpRequest();
                    xhr.open("GET", "searchFreq.php?freq={freq_khz}");
                    xhr.timeout = 5000;
                    xhr.onreadystatechange = function() {{
                        if(this.readyState==4) {{
                            if(this.status==200) {{
                                var lines = this.responseText.split("\\n");
                                if(lines.length >= 3) {{
                                    // Laat site eerst z'n eigen band/mode zetten
                                    document.getElementById("lb_band").selectedIndex = parseInt(lines[1]);
                                    document.getElementById("lb_mode").selectedIndex = parseInt(lines[2]);
                                }}
                            }}
                            // Stap 3: na korte vertraging overschrijven met onze eigen match
                            setTimeout(function() {{
                                setBand();
                                setMode();
                                var elB = document.getElementById("lb_band");
                                var elM = document.getElementById("lb_mode");
                                var selBand = elB ? elB.options[elB.selectedIndex].text : '?';
                                var selMode = elM ? elM.options[elM.selectedIndex].text : '?';
                                resolve("OK|band=" + selBand + "|mode=" + selMode);
                            }}, 300);
                        }}
                    }};
                    xhr.ontimeout = function() {{
                        setTimeout(function() {{ setBand(); setMode(); resolve("OK|timeout-fallback"); }}, 0);
                    }};
                    xhr.send();
                }})
            """)

            if result and result.startswith("OK|"):
                self._inject_credit(page)
                return True, None
            else:
                return False, f"searchFreq: {result}"
        except Exception as e:
            return False, str(e)[:100]

    def fill_freq_band_mode(self, freq_hz, mode_hamlib):
        """Stuur opdracht naar browser-thread en wacht op resultaat."""
        self._cmd_queue.put((freq_hz, mode_hamlib))
        try:
            ok, err = self._result_queue.get(timeout=10)
            self._last_error = err
            return ok
        except queue.Empty:
            self._last_error = "Timeout — geen reactie van browser"
            return False

    def get_last_error(self):
        return self._last_error

    def stop(self):
        try:
            self._cmd_queue.put(None)  # stop-signaal
            if self._thread:
                self._thread.join(timeout=5)
        except Exception:
            pass


# ── GUI ──────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MultiLogCAT  —  PE5JW")
        self.resizable(True, True)
        self.minsize(480, 400)
        self.cfg = load_config()
        self._rigctld_proc = None
        self._rig = None
        self._poll_thread = None
        self._running = False
        self._filler = None
        self._last_freq = None
        self._last_mode = None

        self._build_ui()
        self._load_cfg_to_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI bouw ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        pad = dict(padx=8, pady=4)

        # ── Radio config ─────────────────────────────────────────────────────
        rf = ttk.LabelFrame(self, text="Radio instellingen")
        rf.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=6)

        ttk.Label(rf, text="Radio model:").grid(row=0, column=0, sticky="w", **pad)
        self.var_model = tk.StringVar()
        frm_model = ttk.Frame(rf)
        frm_model.grid(row=0, column=1, columnspan=2, sticky="w")
        self.cb_model = ttk.Combobox(frm_model, textvariable=self.var_model, width=28,
                                     values=[m[0] for m in RADIO_MODELS], state="readonly")
        self.cb_model.pack(side="left")
        self.cb_model.bind("<<ComboboxSelected>>", self._on_model_select)
        # Link naar Hamlib modellen lijst
        lnk = ttk.Label(frm_model, text="  🔗 Hamlib lijst", foreground="#0066cc",
                        cursor="hand2", font=("Arial", 8, "underline"))
        lnk.pack(side="left")
        lnk.bind("<Button-1>", lambda e: open_url(
            "https://github.com/Hamlib/Hamlib/wiki/Supported-Radios"))

        # Handmatig modelnummer (alleen zichtbaar bij "Anders")
        self.lbl_manual = ttk.Label(rf, text="Model nr.:")
        self.var_manual_model = tk.StringVar()
        self.entry_manual = ttk.Entry(rf, textvariable=self.var_manual_model, width=10)
        # worden zichtbaar via _on_model_select

        # Verbindingstype: serieel of netwerk
        ttk.Label(rf, text="Verbinding:").grid(row=1, column=0, sticky="w", **pad)
        self.var_port_type = tk.StringVar(value=PORT_TYPE_SERIAL)
        frm_type = ttk.Frame(rf)
        frm_type.grid(row=1, column=1, sticky="w")
        ttk.Radiobutton(frm_type, text="Serieel (COM)", variable=self.var_port_type,
                        value=PORT_TYPE_SERIAL, command=self._toggle_port_type).pack(side="left", padx=(0,10))
        ttk.Radiobutton(frm_type, text="Netwerk (IP:poort)", variable=self.var_port_type,
                        value=PORT_TYPE_NET, command=self._toggle_port_type).pack(side="left")

        # Serieel velden
        self.lbl_com = ttk.Label(rf, text="COM poort:")
        self.lbl_com.grid(row=2, column=0, sticky="w", **pad)
        self.var_port = tk.StringVar()
        self.cb_port = ttk.Combobox(rf, textvariable=self.var_port, width=10,
                                    values=[f"COM{i}" for i in range(1, 17)])
        self.cb_port.grid(row=2, column=1, sticky="w", **pad)

        self.lbl_baud = ttk.Label(rf, text="Baudrate:")
        self.lbl_baud.grid(row=3, column=0, sticky="w", **pad)
        self.var_baud = tk.StringVar()
        self.cb_baud = ttk.Combobox(rf, textvariable=self.var_baud, width=10,
                                    values=BAUDS, state="readonly")
        self.cb_baud.grid(row=3, column=1, sticky="w", **pad)

        # Netwerk velden (IP:poort)
        self.lbl_net = ttk.Label(rf, text="IP adres:")
        self.lbl_net.grid(row=4, column=0, sticky="w", **pad)
        self.var_net_ip = tk.StringVar(value="127.0.0.1")
        frm_net = ttk.Frame(rf)
        frm_net.grid(row=4, column=1, columnspan=2, sticky="w")
        self.entry_net_ip = ttk.Entry(frm_net, textvariable=self.var_net_ip, width=18)
        self.entry_net_ip.pack(side="left")
        ttk.Label(frm_net, text="  (127.0.0.1 = zelfde PC, of bijv. 192.168.1.50)",
                  foreground="gray", font=("Arial", 8)).pack(side="left")

        self.lbl_net_port = ttk.Label(rf, text="Poort:")
        self.lbl_net_port.grid(row=5, column=0, sticky="w", **pad)
        self.var_net_port = tk.StringVar(value="51111")
        frm_port = ttk.Frame(rf)
        frm_port.grid(row=5, column=1, columnspan=2, sticky="w")
        self.entry_net_port = ttk.Entry(frm_port, textvariable=self.var_net_port, width=8)
        self.entry_net_port.pack(side="left", padx=(0, 6))
        # Snelknoppen voor bekende poorten — alleen nummer
        for port in ["19090", "51111", "12345", "4532"]:
            ttk.Button(frm_port, text=port, width=7,
                       command=lambda p=port: self.var_net_port.set(p)
                       ).pack(side="left", padx=2)

        self._toggle_port_type()  # initiële staat

        # ── Hamlib pad ───────────────────────────────────────────────────────
        hf = ttk.LabelFrame(self, text="Hamlib")
        hf.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=6)

        rigctld_label = "rigctld.exe pad:" if sys.platform == "win32" else "rigctld pad:"
        ttk.Label(hf, text=rigctld_label).grid(row=0, column=0, sticky="w", **pad)
        self.var_hamlib = tk.StringVar()
        frm_hamlib = ttk.Frame(hf)
        frm_hamlib.grid(row=0, column=1, columnspan=2, sticky="w")
        ttk.Entry(frm_hamlib, textvariable=self.var_hamlib, width=38).pack(side="left")

        def _browse_hamlib():
            exe_name = "rigctld.exe" if sys.platform == "win32" else "rigctld"
            if sys.platform == "win32":
                filetypes = [("rigctld", "rigctld.exe"), ("Alle bestanden", "*.*")]
            else:
                filetypes = [("rigctld", "rigctld"), ("Alle bestanden", "*")]
            pad_huidig = self.var_hamlib.get()
            init_dir = str(Path(pad_huidig).parent) if pad_huidig else "/"
            gekozen = filedialog.askopenfilename(
                title=f"Kies {exe_name}",
                initialdir=init_dir,
                filetypes=filetypes,
            )
            if gekozen:
                self.var_hamlib.set(gekozen)

        ttk.Button(frm_hamlib, text="📂", width=3, command=_browse_hamlib).pack(side="left", padx=(4, 0))
        lnk_hamlib = ttk.Label(frm_hamlib, text="  ⬇ Download Hamlib",
                               foreground="#0066cc", cursor="hand2", font=("Arial", 8, "underline"))
        lnk_hamlib.pack(side="left")
        lnk_hamlib.bind("<Button-1>", lambda e: open_url(
            "https://github.com/Hamlib/Hamlib/releases/tag/4.7.2"))

        # ── Website ──────────────────────────────────────────────────────────
        wf = ttk.LabelFrame(self, text="Website login")
        wf.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=6)

        ttk.Label(wf, text="URL:").grid(row=0, column=0, sticky="w", **pad)
        self.var_url = tk.StringVar()
        ttk.Entry(wf, textvariable=self.var_url, width=48).grid(row=0, column=1, **pad)

        ttk.Label(wf, text="Call (gebruikersnaam):").grid(row=1, column=0, sticky="w", **pad)
        self.var_user = tk.StringVar()
        ttk.Entry(wf, textvariable=self.var_user, width=20).grid(row=1, column=1, sticky="w", **pad)

        ttk.Label(wf, text="Wachtwoord:").grid(row=2, column=0, sticky="w", **pad)
        self.var_pass = tk.StringVar()
        frm_pass = ttk.Frame(wf)
        frm_pass.grid(row=2, column=1, sticky="w")
        ttk.Entry(frm_pass, textvariable=self.var_pass, width=20, show="*").pack(side="left")
        self.var_save_pass = tk.BooleanVar(value=True)
        ttk.Checkbutton(frm_pass, text="wachtwoord opslaan", variable=self.var_save_pass
                        ).pack(side="left", padx=8)

        # ── Live data ────────────────────────────────────────────────────────
        lf = ttk.LabelFrame(self, text="Live radio data")
        lf.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=6)

        for i, lbl in enumerate(["Frequentie:", "Band:", "Mode:"]):
            ttk.Label(lf, text=lbl).grid(row=i, column=0, sticky="w", **pad)

        self.lbl_freq = ttk.Label(lf, text="—", font=("Courier", 12, "bold"), foreground="blue")
        self.lbl_freq.grid(row=0, column=1, sticky="w", **pad)
        self.lbl_band = ttk.Label(lf, text="—", font=("Courier", 12, "bold"), foreground="blue")
        self.lbl_band.grid(row=1, column=1, sticky="w", **pad)
        self.lbl_mode = ttk.Label(lf, text="—", font=("Courier", 12, "bold"), foreground="blue")
        self.lbl_mode.grid(row=2, column=1, sticky="w", **pad)

        # Laatste update naar site
        self.lbl_last_fill = ttk.Label(lf, text="Nog niet bijgewerkt", foreground="gray", font=("Arial", 9))
        self.lbl_last_fill.grid(row=3, column=0, columnspan=2, sticky="w", **pad)

        # ── Status ───────────────────────────────────────────────────────────
        self.lbl_status = ttk.Label(self, text="Gestopt", foreground="gray")
        self.lbl_status.grid(row=4, column=0, columnspan=2, pady=4)

        # ── Knoppen ──────────────────────────────────────────────────────────
        bf = ttk.Frame(self)
        bf.grid(row=5, column=0, columnspan=2, pady=8)

        self.btn_save = ttk.Button(bf, text="💾 Opslaan", command=self._save)
        self.btn_save.pack(side="left", padx=6)

        self.btn_start = ttk.Button(bf, text="▶ Start", command=self._start)
        self.btn_start.pack(side="left", padx=6)

        self.btn_stop = ttk.Button(bf, text="⏹ Stop", command=self._stop, state="disabled")
        self.btn_stop.pack(side="left", padx=6)

        ttk.Button(bf, text="✖ Afsluiten", command=self._on_close).pack(side="left", padx=6)

        # ── Info label ───────────────────────────────────────────────────────
        ttk.Label(self, text="Frequentie, band en mode worden automatisch ingevuld via searchFreq.php",
                  foreground="gray", font=("Arial", 8)).grid(row=6, column=0, columnspan=2, pady=(0,6))

    # ── Poorttype toggle ─────────────────────────────────────────────────────

    def _toggle_port_type(self):
        is_serial = (self.var_port_type.get() == PORT_TYPE_SERIAL)
        state_ser = "normal" if is_serial else "disabled"
        self.cb_port.config(state=state_ser)
        self.cb_baud.config(state="readonly" if is_serial else "disabled")
        state_net = "normal" if not is_serial else "disabled"
        self.entry_net_ip.config(state=state_net)
        self.entry_net_port.config(state=state_net)

    def _on_model_select(self, event=None):
        selected = self.var_model.get()
        is_manual = selected.startswith("Anders")
        if is_manual:
            self.lbl_manual.grid(row=1, column=2, sticky="w", padx=(4, 0), pady=4)
            self.entry_manual.grid(row=1, column=3, sticky="w", pady=4)
        else:
            self.lbl_manual.grid_remove()
            self.entry_manual.grid_remove()

    # ── Config laden/opslaan ─────────────────────────────────────────────────

    def _load_cfg_to_ui(self):
        r = self.cfg.get("radio", {})

        # Herstel radio model: probeer eerst op naam, dan op nummer
        saved_name = r.get("model_name", "")
        saved_nr   = r.get("model", "3073")
        model_name = next((m[0] for m in RADIO_MODELS if m[0] == saved_name), None)
        if model_name is None:
            model_name = next((m[0] for m in RADIO_MODELS if m[1] == saved_nr), RADIO_MODELS[0][0])
        self.var_model.set(model_name)

        # Handmatig modelnummer (bij keuze "Anders")
        self.var_manual_model.set(r.get("manual_model", ""))

        self.var_port.set(r.get("port", "COM3"))
        self.var_baud.set(r.get("baudrate", "9600"))

        port_type = r.get("port_type", PORT_TYPE_SERIAL)
        self.var_port_type.set(port_type)
        self.var_net_ip.set(r.get("net_ip", "127.0.0.1"))
        self.var_net_port.set(r.get("net_port", "51111"))
        self._toggle_port_type()
        self._on_model_select()

        h = self.cfg.get("hamlib", {})
        self.var_hamlib.set(h.get("path", r"C:\dev\multilogcat\hamlib-w64-4.7.2\bin\rigctld.exe"))

        w = self.cfg.get("website", {})
        self.var_url.set(w.get("url", "https://multilog.endoria.net/index.php"))
        self.var_user.set(w.get("username", ""))
        save_pass = w.get("save_password", True)
        self.var_save_pass.set(save_pass)
        self.var_pass.set(w.get("password", "") if save_pass else "")

    def _save(self):
        model_name = self.var_model.get()
        model_nr = next((m[1] for m in RADIO_MODELS if m[0] == model_name), "0")
        if model_nr == "0":  # Handmatig
            model_nr = self.var_manual_model.get().strip() or "3073"
        self.cfg = {
            "radio": {
                "model": model_nr,
                "model_name": model_name,
                "manual_model": self.var_manual_model.get().strip(),
                "port_type": self.var_port_type.get(),
                "port": self.var_port.get(),
                "baudrate": self.var_baud.get(),
                "data_bits": "8",
                "stop_bits": "1",
                "parity": "N",
                "net_ip": self.var_net_ip.get(),
                "net_port": self.var_net_port.get(),
            },
            "hamlib": {
                "path": self.var_hamlib.get(),
                "host": "127.0.0.1",
                "port": "4532"
            },
            "website": {
                "url": self.var_url.get(),
                "username": self.var_user.get(),
                "save_password": self.var_save_pass.get(),
                "password": self.var_pass.get() if self.var_save_pass.get() else ""
            },
            "poll_interval": 2
        }
        save_config(self.cfg)
        self.lbl_status.config(text="Config opgeslagen ✓", foreground="green")

    # ── Start / Stop ─────────────────────────────────────────────────────────

    def _start(self):
        self._save()

        # Controleer of playwright geïnstalleerd is
        try:
            import playwright
        except ImportError:
            messagebox.showerror("Fout", "Playwright niet geïnstalleerd.\n\nVoer uit:\n  pip install playwright\n  playwright install chromium")
            return

        h = self.cfg["hamlib"]
        r = self.cfg["radio"]
        exe = h["path"]

        # Serieel of netwerk verbinding opbouwen
        if r.get("port_type") == PORT_TYPE_NET:
            # Netwerk: verbind direct met de server (SparkSDR, FLRig, enz.)
            # rigctld.exe is NIET nodig — de software is zelf de server
            net_host = r.get("net_ip", "127.0.0.1")
            net_port = int(r.get("net_port", "4532"))
            self._rig = RigCtld(net_host, net_port)
            try:
                self._rig.connect()
            except Exception as e:
                messagebox.showerror("Fout", f"Kan niet verbinden met {net_host}:{net_port}\n\n{e}\n\nIs SparkSDR / FLRig gestart?")
                self._stop()
                return
            self._rigctld_proc = None
        else:
            # Serieel: start rigctld.exe als achtergrondproces
            cmd = [
                exe,
                "-m", r["model"],
                "-r", r["port"],
                "-s", r["baudrate"],
                "-t", str(h["port"]),
            ]
            try:
                self._rigctld_proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except FileNotFoundError:
                messagebox.showerror("Fout", f"rigctld.exe niet gevonden:\n{exe}")
                return

            time.sleep(1.5)

            self._rig = RigCtld(h["host"], h["port"])
            try:
                self._rig.connect()
            except Exception as e:
                messagebox.showerror("Fout", f"Kan niet verbinden met rigctld:\n{e}\n\nControleer COM-poort en baudrate.")
                self._stop()
                return

        # Als wachtwoord niet opgeslagen is, vraag het nu
        if not self.cfg["website"].get("password"):
            pw = self._ask_login()
            if pw is None:
                self._stop()
                return
            self.cfg["website"]["password"] = pw

        # Start Playwright browser in aparte thread
        self._filler = MultilogFiller(self.cfg)
        self.lbl_status.config(text="Browser openen en inloggen...", foreground="orange")
        self.update()

        try:
            self._filler.start()
        except Exception as e:
            messagebox.showerror("Fout", f"Browser fout:\n{e}")
            self._stop()
            return

        self._running = True
        self.btn_start.config(state="disabled")
        self.btn_stop.config(state="normal")
        self.lbl_status.config(text="Verbonden ✓ — polling radio...", foreground="green")

        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

    def _ask_login(self):
        """Toon login dialoog als wachtwoord niet opgeslagen is. Geeft wachtwoord terug of None bij annuleren."""
        dlg = tk.Toplevel(self)
        dlg.title("Inloggen")
        dlg.resizable(False, False)
        dlg.grab_set()
        dlg.transient(self)

        pad = dict(padx=10, pady=6)
        ttk.Label(dlg, text="Inloggen op multilog website", font=("Arial", 10, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(12, 4))

        user = self.cfg["website"].get("username", "")
        ttk.Label(dlg, text="Call:").grid(row=1, column=0, sticky="e", **pad)
        var_u = tk.StringVar(value=user)
        entry_u = ttk.Entry(dlg, textvariable=var_u, width=20)
        entry_u.grid(row=1, column=1, sticky="w", **pad)

        ttk.Label(dlg, text="Wachtwoord:").grid(row=2, column=0, sticky="e", **pad)
        var_p = tk.StringVar()
        entry_p = ttk.Entry(dlg, textvariable=var_p, width=20, show="*")
        entry_p.grid(row=2, column=1, sticky="w", **pad)

        result = [None]

        def ok():
            # Eventueel username bijwerken als gebruiker het aanpaste
            self.cfg["website"]["username"] = var_u.get()
            self.var_user.set(var_u.get())
            result[0] = var_p.get()
            dlg.destroy()

        def cancel():
            dlg.destroy()

        bf = ttk.Frame(dlg)
        bf.grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(bf, text="Inloggen", command=ok).pack(side="left", padx=8)
        ttk.Button(bf, text="Annuleren", command=cancel).pack(side="left", padx=8)

        entry_p.bind("<Return>", lambda e: ok())
        if user:
            entry_p.focus_set()
        else:
            entry_u.focus_set()

        self.wait_window(dlg)
        return result[0]

    def _stop(self):
        self._running = False
        if self._rig:
            self._rig.disconnect()
            self._rig = None
        if self._rigctld_proc:
            self._rigctld_proc.terminate()
            self._rigctld_proc = None
        if self._filler:
            self._filler.stop()
            self._filler = None
        self._last_freq = None
        self._last_mode = None
        self.btn_start.config(state="normal")
        self.btn_stop.config(state="disabled")
        self.lbl_status.config(text="Gestopt", foreground="gray")
        self.lbl_freq.config(text="—")
        self.lbl_band.config(text="—")
        self.lbl_mode.config(text="—")
        self.lbl_last_fill.config(text="Nog niet bijgewerkt")

    def _on_close(self):
        self._stop()
        self.destroy()

    # ── Poll loop ─────────────────────────────────────────────────────────────

    def _poll_loop(self):
        interval = self.cfg.get("poll_interval", 2)
        while self._running:
            try:
                freq = self._rig.get_freq()
                mode = self._rig.get_mode()
                band = freq_to_band(freq) if freq else "?"
                freq_mhz = f"{freq / 1_000_000:.6f} MHz" if freq else "?"

                # Alleen bijwerken als frequentie of mode veranderd is
                changed = (freq != self._last_freq or mode != self._last_mode)

                self.after(0, lambda f=freq_mhz, b=band, m=mode: self._update_display(f, b, m))

                if changed and freq and self._filler:
                    ok = self._filler.fill_freq_band_mode(freq, mode)
                    ts = time.strftime("%H:%M:%S")
                    if ok:
                        self.after(0, lambda t=ts, f=freq_mhz: self.lbl_last_fill.config(
                            text=f"Laatste update: {t}  ({f})", foreground="green"))
                    else:
                        err = self._filler.get_last_error() or "onbekende fout"
                        self.after(0, lambda e=err: self.lbl_last_fill.config(
                            text=f"Fout bij invullen: {e}", foreground="red"))

                    self._last_freq = freq
                    self._last_mode = mode

            except Exception as e:
                self.after(0, lambda err=str(e): self.lbl_status.config(
                    text=f"Fout: {err}", foreground="red"))
                break

            time.sleep(interval)

    def _update_display(self, freq_str, band, mode):
        self.lbl_freq.config(text=freq_str)
        self.lbl_band.config(text=band)
        self.lbl_mode.config(text=mode)


# ── Installatie helper ────────────────────────────────────────────────────────

def check_install():
    """Controleer of playwright beschikbaar is, anders toon instructies."""
    missing = []
    try:
        import playwright
    except ImportError:
        missing.append("playwright")

    if missing:
        print("=" * 50)
        print("Ontbrekende pakketten — voer uit in PowerShell:")
        print()
        print("  pip install playwright")
        print("  playwright install chromium")
        print("=" * 50)
        print()


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    check_install()
    app = App()
    app.mainloop()
