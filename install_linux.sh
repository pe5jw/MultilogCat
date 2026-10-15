#!/bin/bash
# ============================================================
#  MultiLogCAT — Linux installatie script
#  Getest op: NIET getest — gebruik op eigen risico
#  Werkt vermoedelijk op Ubuntu 22.04+, Debian 12+, Fedora 38+
# ============================================================

set -e

echo "=== MultiLogCAT Linux installatie ==="
echo ""
echo "⚠️  LET OP: MultiLogCAT is ontwikkeld en getest op Windows."
echo "    Linux ondersteuning is experimenteel en NIET getest."
echo "    Gebruik op eigen risico."
echo ""

# Detecteer package manager
if command -v apt-get &>/dev/null; then
    PKG="apt"
elif command -v dnf &>/dev/null; then
    PKG="dnf"
elif command -v pacman &>/dev/null; then
    PKG="pacman"
else
    echo "Onbekende package manager. Installeer handmatig:"
    echo "  python3, python3-tk, python3-pip, hamlib"
    PKG="unknown"
fi

echo "[1/4] Systeem pakketten installeren..."
if [ "$PKG" = "apt" ]; then
    sudo apt-get update -q
    sudo apt-get install -y python3 python3-tk python3-pip hamlib-utils
elif [ "$PKG" = "dnf" ]; then
    sudo dnf install -y python3 python3-tkinter python3-pip hamlib
elif [ "$PKG" = "pacman" ]; then
    sudo pacman -Sy --noconfirm python tk python-pip hamlib
fi

echo ""
echo "[2/4] Python pakketten installeren..."
pip3 install playwright --break-system-packages 2>/dev/null || pip3 install playwright

echo ""
echo "[3/4] Chromium downloaden voor Playwright..."
playwright install chromium

echo ""
echo "[4/4] Controleren..."
python3 -c "import tkinter; print('  tkinter: OK')"
python3 -c "import playwright; print('  playwright: OK')"
which rigctld &>/dev/null && echo "  rigctld: OK ($(which rigctld))" || echo "  rigctld: NIET gevonden (optioneel bij seriële verbinding)"

echo ""
echo "=== Klaar! ==="
echo ""
echo "Starten:"
echo "  python3 multilogcat.py"
echo ""
echo "⚠️  Linux-specifieke opmerkingen:"
echo "  - rigctld pad: gebruik 'which rigctld' om het pad te vinden"
echo "  - Seriële poort: /dev/ttyUSB0 of /dev/ttyS0 (niet COM3)"
echo "  - Rechten seriële poort: sudo usermod -aG dialout \$USER (daarna uitloggen)"
echo ""
