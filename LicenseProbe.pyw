"""
LicenseProbe 1.0.0 - Windows-Produktschluessel im Klartext anzeigen

Liest die Produktschluessel dieses Rechners aus drei Quellen:

* den OEM-Schluessel, den der Hersteller in der Firmware hinterlegt hat
  (ACPI-Tabelle MSDM),
* den installierten Schluessel, aus DigitalProductId in der Registry
  zurueckgerechnet,
* den von Windows gesicherten Schluessel (BackupProductKeyDefault).

Dazu kommen Edition, Version und Aktivierungsstand. Abgefragt wird nur
lesend; Administratorrechte sind nicht noetig. Die Schluessel werden weder
gespeichert noch uebertragen.

Farbschema, Sprachumschaltung und Aufbau folgen dem uebrigen Hausstil.

Licensed under MIT License
Copyright 2026 Alexander Unverhau
Created with assistance of Claude AI

Benoetigt nur die Standardbibliothek (Tkinter gehoert dazu).
"""

from __future__ import annotations

import json
import locale
import os
import subprocess
import sys
import threading

PROGRAMM = "LicenseProbe"
VERSION = "1.0.0"

# Von gui_starten() belegt, sobald Tkinter geladen ist.
_tk = None
_ttk = None


# --------------------------------------------------------------------------
# Farbschemata
#
# apply_theme() schreibt die Werte der gewaehlten Palette in die
# Modulvariablen - der uebrige Code benutzt einfach BG, CARD, TEXT ... und
# muss vom Umschalten nichts wissen. Ein eigenes Schema entsteht durch eine
# weitere Palette mit denselben Namen.
# --------------------------------------------------------------------------

THEMES = {
    "light": {
        "BG": "#eef1f5",             # Seitenhintergrund
        "CARD": "#ffffff",           # Karten
        "CARD_ALT": "#fbfcfe",       # Text- und Listenflaechen in Karten
        "BORDER": "#d7dce4",
        "TEXT": "#1b2430",
        "MUTED": "#6c7684",          # Nebentext
        "HEADER": "#1d2330",         # Kopfzeile mit Titel und Umschaltern
        "HEADER_TEXT": "#c2cad8",
        "HEADER_TITLE": "#ffffff",
        "HEADER_GROUP": "#69748c",
        "HEADER_HOVER": "#2b3346",
        "ACCENT": "#2f7de1",
        "ACCENT_DARK": "#1f66c4",
        "ON_ACCENT": "#ffffff",      # Schrift auf farbigen Flaechen
        "OK": "#2e9e5b",
        "OK_DARK": "#25864b",
        "WARN": "#e08b1f",
        "WARN_DARK": "#c4770f",
        "DANGER": "#d64545",
        "DANGER_DARK": "#b83a3a",
        "BTN_BG": "#e3e8f0",         # unauffaelliger Schalter
        "BTN_HOVER": "#d2d9e6",
        "BTN_TEXT": "#1b2430",
        "BTN_DISABLED": "#9aa3b0",
        "FIELD_BG": "#ffffff",       # Eingabefelder
        "TROUGH": "#e3e8f0",         # Rille von Schiebereglern
        "TAB_BG": "#e3e8f0",         # nicht gewaehlter Reiter
        "STATUS_BG": "#e4e8ef",
    },
    "dark": {
        "BG": "#12161d",
        "CARD": "#1a1f28",
        "CARD_ALT": "#151a22",
        "BORDER": "#2c3441",
        "TEXT": "#e6eaf0",
        "MUTED": "#98a2b3",
        "HEADER": "#0e1218",
        "HEADER_TEXT": "#b8c2d0",
        "HEADER_TITLE": "#ffffff",
        "HEADER_GROUP": "#6b7688",
        "HEADER_HOVER": "#212a38",
        "ACCENT": "#4a90e8",
        "ACCENT_DARK": "#3a7ad0",
        "ON_ACCENT": "#ffffff",
        "OK": "#3fb972",
        "OK_DARK": "#349b60",
        "WARN": "#e9a23b",
        "WARN_DARK": "#cc8a26",
        "DANGER": "#e05a5a",
        "DANGER_DARK": "#c44a4a",
        "BTN_BG": "#2a323f",
        "BTN_HOVER": "#353f4f",
        "BTN_TEXT": "#e6eaf0",
        "BTN_DISABLED": "#626c7a",
        "FIELD_BG": "#232b36",
        "TROUGH": "#2a323f",
        "TAB_BG": "#232b36",
        "STATUS_BG": "#0e1218",
    },
}

DEFAULT_THEME = "light"
CURRENT_THEME = DEFAULT_THEME


def apply_theme(name):
    """Farbwerte des gewaehlten Schemas in die Modulvariablen schreiben."""
    global CURRENT_THEME
    CURRENT_THEME = name if name in THEMES else DEFAULT_THEME
    globals().update(THEMES[CURRENT_THEME])


apply_theme(DEFAULT_THEME)      # legt BG, CARD, TEXT ... ueberhaupt erst an

FONT = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)
FONT_TINY = ("Segoe UI", 8)
FONT_BOLD = ("Segoe UI", 10, "bold")
FONT_H2 = ("Segoe UI", 12, "bold")
FONT_MONO = ("Consolas", 10)
FONT_MONO_SMALL = ("Consolas", 9)
FONT_SCHLUESSEL = ("Consolas", 13)


# --------------------------------------------------------------------------
# Sprachumschaltung
#
# Deutsch ist die Quellsprache: im Code steht der deutsche Text, _("...")
# sucht ihn zur Laufzeit in der Sprachtabelle TRANSLATIONS (ganz unten in
# dieser Datei). Dort ist auch beschrieben, wie eine weitere Sprache
# dazukommt.
# --------------------------------------------------------------------------

SOURCE_LANGUAGE = "de"
CONFIG_NAME = "licenseprobe.json"


class Uebersetzt(str):
    """Uebersetzter Text, der seinen deutschen Schluessel kennt.

    Verhaelt sich ueberall wie ein gewoehnlicher String. beschriften() liest
    daraus ab, wie sich eine Beschriftung nach einem Sprachwechsel neu bilden
    laesst - samt der Werte, die mit format() eingesetzt wurden.
    """

    def __new__(cls, text, schluessel, werte=None):
        neu = super().__new__(cls, text)
        neu.schluessel = schluessel
        neu.werte = werte or {}
        return neu

    def format(self, *args, **kwargs):
        if args:                             # Positionsargumente nutzt hier niemand
            return str.format(self, *args, **kwargs)
        return Uebersetzt(str.format(self, **kwargs), self.schluessel, kwargs)


class Translator:
    """Uebersetzt einen deutschen Quelltext in die eingestellte Sprache."""

    def __init__(self, language=SOURCE_LANGUAGE):
        self.language = language

    def __call__(self, text):
        if self.language == SOURCE_LANGUAGE:
            return Uebersetzt(text, text)
        return Uebersetzt(TRANSLATIONS.get(self.language, {}).get(text, text), text)

    def available(self):
        """Sprachkuerzel -> Anzeigename, Quellsprache immer zuerst."""
        names = {SOURCE_LANGUAGE: LANGUAGE_NAMES[SOURCE_LANGUAGE]}
        for code in TRANSLATIONS:
            names[code] = LANGUAGE_NAMES.get(code, code)
        return names


_ = Translator()


def neu_bilden(text):
    """Einen gemerkten Text in der aktuellen Sprache neu bilden.

    Werte, die selbst uebersetzte Texte sind, werden mit uebersetzt - so
    folgt etwa "Schluessel „{quelle}“ kopiert." samt Quellenname dem
    Sprachwechsel.
    """
    if not isinstance(text, Uebersetzt):
        return text
    werte = {name: neu_bilden(wert) for name, wert in text.werte.items()}
    neu = _(text.schluessel)
    return neu.format(**werte) if werte else neu


# --------------------------------------------------------------------------
# Einstellungen
# --------------------------------------------------------------------------

def ist_eingefroren() -> bool:
    """Laeuft das Programm als gebuendelte EXE (PyInstaller & Co.)?"""
    return getattr(sys, "frozen", False)


def programm_ordner() -> str:
    """Ordner, in dem das Programm fuer den Anwender sichtbar liegt.

    Als PyInstaller-EXE mit --onefile entpackt sich das Programm in einen
    temporaeren Ordner (sys._MEIPASS), den PyInstaller beim Beenden wieder
    loescht - __file__ zeigt dorthin. Alles, was den Programmlauf ueberdauern
    soll, gehoert deshalb neben die EXE und nicht neben __file__.
    """
    if ist_eingefroren():
        return os.path.dirname(os.path.abspath(sys.executable))
    try:
        return os.path.dirname(os.path.abspath(__file__))
    except NameError:                       # z. B. interaktive Eingabe
        return os.path.expanduser("~")


def config_path():
    """Ablageort der Einstellungen - neben dem Programm."""
    return os.path.join(programm_ordner(), CONFIG_NAME)


def load_config():
    try:
        with open(config_path(), encoding="utf-8") as datei:
            daten = json.load(datei)
        return daten if isinstance(daten, dict) else {}
    except (OSError, ValueError):
        return {}


def save_config(daten):
    try:
        with open(config_path(), "w", encoding="utf-8") as datei:
            json.dump(daten, datei, indent=2)
        return True
    except OSError:
        return False


def detect_language():
    """Sprache des Betriebssystems, falls dafuer eine Tabelle vorliegt."""
    try:
        locale.setlocale(locale.LC_CTYPE, "")
        code = (locale.getlocale()[0] or "").lower()
    except (locale.Error, ValueError):
        code = ""
    bekannt = {SOURCE_LANGUAGE, *TRANSLATIONS}
    kurz = code.split("_")[0]
    if kurz in bekannt:
        return kurz
    for name, sprache in (("german", "de"), ("deutsch", "de"), ("english", "en")):
        if kurz.startswith(name) and sprache in bekannt:
            return sprache
    return SOURCE_LANGUAGE


def startup_language():
    """Gespeicherte Sprache, sonst die des Betriebssystems."""
    gespeichert = load_config().get("language")
    if gespeichert and (gespeichert == SOURCE_LANGUAGE or gespeichert in TRANSLATIONS):
        return gespeichert
    return detect_language()


def startup_theme():
    """Gespeichertes Farbschema, sonst das helle."""
    gespeichert = load_config().get("theme")
    return gespeichert if gespeichert in THEMES else DEFAULT_THEME


# --------------------------------------------------------------------------
# Schluessel lesen
#
# Alles hier liest nur. Die Auswertung der Rohdaten steckt jeweils in einer
# eigenen Funktion ohne Systemzugriff, damit sie sich auch ohne Windows
# pruefen laesst.
# --------------------------------------------------------------------------

ZEICHEN = "BCDFGHJKMPQRTVWXY2346789"          # die 24 Zeichen eines Produktschluessels
REG_VERSION = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
REG_SPP = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform"
WINDOWS_APP_ID = "55c92734-d682-4d71-983e-d6ec3f16059f"

# Allgemeine Installationsschluessel von Microsoft. Steht einer davon in der
# Registry, haengt die eigentliche Lizenz digital an der Hardware (oder am
# Microsoft-Konto) - der Schluessel selbst ist dann keine Lizenz.
ALLGEMEINE_SCHLUESSEL = {
    "VK7JG-NPHTM-C97JM-9MPGT-3V66T": "Pro",
    "2B87N-8KFHP-DKV6R-Y2C8J-PKCKT": "Pro N",
    "YTMG3-N6DKC-DKB77-7M9GH-8HVX7": "Home",
    "4CPRK-NM3K3-X6XXQ-RXX86-WXCHW": "Home N",
    "BT79Q-G7N6G-PGBYW-4YWX6-6F4BT": "Home Single Language",
    "YNMGQ-8RYV3-4PGQ3-C8XTP-7CFBY": "Education",
    "XGVPP-NMH47-7TTHJ-W3FW7-8HV2C": "Enterprise",
    "DXG7C-N36C4-C4HTG-X4T3X-2YV77": "Pro for Workstations",
}

# LicenseStatus aus SoftwareLicensingProduct -> (deutscher Text, Farbrolle)
LIZENZSTATUS = {
    0: ("Nicht lizenziert", "DANGER"),
    1: ("Aktiviert", "OK"),
    2: ("Kulanzzeit vor der Aktivierung", "WARN"),
    3: ("Kulanzzeit nach Hardwareänderung", "WARN"),
    4: ("Kulanzzeit – kein Original", "DANGER"),
    5: ("Benachrichtigungsmodus – nicht aktiviert", "DANGER"),
    6: ("Verlängerte Kulanzzeit", "WARN"),
}
STATUS_UNBEKANNT = ("Stand unbekannt", "WARN")


def _registry_wert(pfad, name):
    """Wert aus HKLM lesen - immer aus der 64-Bit-Ansicht der Registry.

    Ein 32-Bit-Python saehe sonst die umgeleitete WOW6432Node, in der
    DigitalProductId fehlt.
    """
    try:
        import winreg
    except ImportError:                     # kein Windows
        return None
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, pfad, 0,
                            winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as schluessel:
            return winreg.QueryValueEx(schluessel, name)[0]
    except OSError:
        return None


def gruppieren(text: str) -> str:
    """25 Zeichen in fuenf Fuenfergruppen mit Bindestrich."""
    return "-".join(text[i:i + 5] for i in range(0, 25, 5))


def schluessel_entschluesseln(digital_product_id) -> str | None:
    """Produktschlüssel aus DigitalProductId zurückrechnen.

    Ab Windows 8 stehen die 25 Zeichen als Zahl zur Basis 24 in den Bytes
    52 bis 66. Diese Zahl ist kleiner als 2**115; das Bit darueber - Bit 3
    des letzten Bytes - kennzeichnet das neuere Verfahren. Bei ihm steht im
    Schluessel genau ein "N", dessen Stelle die fuehrende Ziffer angibt.
    """
    if not isinstance(digital_product_id, (bytes, bytearray)) or len(digital_product_id) < 67:
        return None
    daten = bytearray(digital_product_id[52:67])
    mit_n = (daten[14] >> 3) & 1
    daten[14] &= 0xF7
    ausgabe = ""
    fuehrend = 0
    for _stelle in range(25):
        rest = 0
        for j in range(14, -1, -1):
            rest = rest * 256 + daten[j]
            daten[j] = rest // 24
            rest %= 24
        ausgabe = ZEICHEN[rest] + ausgabe
        fuehrend = rest
    if mit_n:
        ausgabe = ausgabe[1:fuehrend + 1] + "N" + ausgabe[fuehrend + 1:]
    if ausgabe.strip("B") == "":            # nur Nullen: kein Schluessel hinterlegt
        return None
    return gruppieren(ausgabe)


def schluessel_pruefen(text) -> str | None:
    """Text als Produktschlüssel annehmen, wenn er wie einer aussieht."""
    if not isinstance(text, str):
        return None
    text = text.strip("\0 \r\n").upper()
    gruppen = text.split("-")
    if len(gruppen) == 5 and all(len(g) == 5 and g.isalnum() for g in gruppen):
        return text
    return None


def msdm_auswerten(tabelle) -> str | None:
    """OEM-Schlüssel aus dem Inhalt der ACPI-Tabelle MSDM.

    Nach dem 36 Byte langen ACPI-Kopf folgen 20 Byte Verwaltungsdaten, dann
    ab Byte 56 der Schluessel als 29 Zeichen ASCII.
    """
    if not isinstance(tabelle, (bytes, bytearray)) or len(tabelle) < 85:
        return None
    return schluessel_pruefen(bytes(tabelle[56:85]).decode("ascii", "replace"))


def schluessel_firmware() -> str | None:
    """OEM-Schlüssel aus der Firmware; GetSystemFirmwareTable braucht keine Adminrechte."""
    try:
        import ctypes
        kernel = ctypes.windll.kernel32
        anbieter = int.from_bytes(b"ACPI", "big")
        tabelle = int.from_bytes(b"MSDM", "little")
        groesse = kernel.GetSystemFirmwareTable(anbieter, tabelle, None, 0)
        if groesse < 85:
            return None
        puffer = ctypes.create_string_buffer(groesse)
        if kernel.GetSystemFirmwareTable(anbieter, tabelle, puffer, groesse) != groesse:
            return None
        return msdm_auswerten(puffer.raw)
    except (AttributeError, OSError, ImportError):
        return None


def schluessel_installiert() -> str | None:
    return schluessel_entschluesseln(_registry_wert(REG_VERSION, "DigitalProductId"))


def schluessel_sicherung() -> str | None:
    return schluessel_pruefen(_registry_wert(REG_SPP, "BackupProductKeyDefault"))


def system_angaben() -> dict:
    """Edition, Version und Build aus der Registry."""
    build = str(_registry_wert(REG_VERSION, "CurrentBuild") or "")
    ubr = _registry_wert(REG_VERSION, "UBR")
    name = _registry_wert(REG_VERSION, "ProductName") or "Windows"
    # ProductName lautet auch unter Windows 11 noch "Windows 10 ..."
    if build.isdigit() and int(build) >= 22000:
        name = name.replace("Windows 10", "Windows 11")
    version = (_registry_wert(REG_VERSION, "DisplayVersion")
               or _registry_wert(REG_VERSION, "ReleaseId") or "–")
    if build and ubr is not None:
        build = f"{build}.{ubr}"
    return {"edition": name, "version": str(version), "build": build or "–"}


def aktivierung_auswerten(ausgabe) -> dict | None:
    """Antwort der PowerShell-Abfrage in ein Wörterbuch übersetzen."""
    try:
        daten = json.loads(ausgabe or "null")
    except ValueError:
        return None
    if isinstance(daten, list):              # mehrere Treffer: der erste zaehlt
        daten = daten[0] if daten else None
    if not isinstance(daten, dict):
        return None
    status = daten.get("LicenseStatus")
    return {
        "status": status if isinstance(status, int) else None,
        "teil": str(daten.get("PartialProductKey") or "").upper(),
        "kanal": str(daten.get("Description") or ""),
    }


def aktivierung_abfragen() -> dict | None:
    """Aktivierungsstand und Teilschlüssel über WMI (dauert ein paar Sekunden).

    Laeuft in einem eigenen Thread. CREATE_NO_WINDOW verhindert, dass beim
    Start der PowerShell kurz ein Konsolenfenster aufblitzt.
    """
    befehl = (
        "Get-CimInstance SoftwareLicensingProduct -Filter "
        f"\"ApplicationID='{WINDOWS_APP_ID}' AND PartialProductKey IS NOT NULL\" | "
        "Select-Object -First 1 Description, LicenseStatus, PartialProductKey | "
        "ConvertTo-Json -Compress"
    )
    try:
        ergebnis = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", befehl],
            capture_output=True, text=True, timeout=60,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.SubprocessError):
        return None
    return aktivierung_auswerten(ergebnis.stdout)


# Die drei Schluesselquellen: (Schluessel, Titel, Lesefunktion, Herkunft).
# Titel und Herkunft sind deutsche Texte und zugleich Uebersetzungsschluessel.
QUELLEN = (
    ("firmware", "Firmware (OEM)", "schluessel_firmware",
     "vom Hersteller im BIOS/UEFI hinterlegt"),
    ("installiert", "Installiert", "schluessel_installiert",
     "aus der Registry zurückgerechnet"),
    ("sicherung", "Sicherung", "schluessel_sicherung",
     "von Windows gesicherte Kopie"),
)


def quelle_lesen(lesefunktion: str) -> str | None:
    """Lesefunktion ueber ihren Namen aufrufen - so lassen Tests sie ersetzen."""
    return globals()[lesefunktion]()


# --------------------------------------------------------------------------
# Bausteine der Oberflaeche
#
# faerben() merkt sich zu jedem Widget, welche Rolle seine Farben haben
# ("CARD", "TEXT", ...), beschriften() merkt sich den Uebersetzungsschluessel
# jeder Beschriftung. Sprache und Farbschema lassen sich dadurch umschalten,
# ohne die Oberflaeche neu aufzubauen - nichts blinkt, nichts springt.
# --------------------------------------------------------------------------

FlatButton = None

# (Widget, Rollen) - Rollen ist None bei Widgets, die sich selbst umfaerben.
GEFAERBTE_WIDGETS: list = []


def faerben(widget, **rollen):
    """Widget einfaerben und die Farbrollen fuer spaeteres Umfaerben merken.

    Beispiel:  faerben(label, bg="CARD", fg="TEXT")
    """
    GEFAERBTE_WIDGETS.append((widget, rollen))
    widget.configure(**{option: THEMES[CURRENT_THEME][name] for option, name in rollen.items()})
    return widget


def farben_auffrischen():
    """Alle gemerkten Widgets auf die aktuelle Palette umstellen.

    Zerstoerte Widgets fallen dabei aus der Liste heraus; Tk meldet sie mit
    einem TclError, was hier das Aufraeumkriterium ist.
    """
    palette = THEMES[CURRENT_THEME]
    uebrig = []
    for widget, rollen in GEFAERBTE_WIDGETS:
        try:
            if rollen is None:
                widget.neu_faerben()
            else:
                widget.configure(**{opt: palette[name] for opt, name in rollen.items()})
        except _tk.TclError:                 # Widget existiert nicht mehr
            continue
        uebrig.append((widget, rollen))
    GEFAERBTE_WIDGETS[:] = uebrig


# (Setzfunktion, Schluessel, Werte) - fuer den Sprachwechsel ohne Neuaufbau
BESCHRIFTUNGEN: list = []


def beschriftung_merken(setzen, text):
    """setzen(text) ausfuehren und - stammt der Text aus _() - fuer spaeter merken."""
    setzen(text)
    if isinstance(text, Uebersetzt):
        BESCHRIFTUNGEN.append((setzen, text.schluessel, text.werte))


def beschriften(widget, text, option="text"):
    """Widget beschriften und den Text fuer den Sprachwechsel merken.

    Beispiel:  beschriften(label, _("Edition"))
    """
    beschriftung_merken(lambda neu: widget.configure(**{option: neu}), text)
    return widget


def texte_auffrischen():
    """Alle gemerkten Beschriftungen in die aktuelle Sprache bringen."""
    uebrig = []
    for setzen, schluessel, werte in BESCHRIFTUNGEN:
        text = _(schluessel)
        try:
            setzen(text.format(**werte) if werte else text)
        except _tk.TclError:                 # Widget existiert nicht mehr
            continue
        uebrig.append((setzen, schluessel, werte))
    BESCHRIFTUNGEN[:] = uebrig


def zeichnen_anhalten(fenster_id):
    """Haelt das Zeichnen eines Fensters samt Inhalt an; liefert die Fortsetzung.

    Mit WM_SETREDRAW laesst Windows das alte Bild stehen, bis alle Texte und
    Farben getauscht sind; danach wird in einem Zug neu gezeichnet. Die
    Fortsetzung gehoert in ein try/finally, sonst bliebe das Fenster
    eingefroren.
    """
    if sys.platform != "win32":
        return lambda: None
    try:
        import ctypes
        benutzer = ctypes.windll.user32
        benutzer.SendMessageW(fenster_id, 0x000B, 0, 0)      # WM_SETREDRAW aus
    except (AttributeError, OSError):
        return lambda: None

    def fortsetzen():
        benutzer.SendMessageW(fenster_id, 0x000B, 1, 0)      # WM_SETREDRAW an
        # RDW_INVALIDATE | RDW_ALLCHILDREN | RDW_UPDATENOW
        benutzer.RedrawWindow(fenster_id, None, None, 0x0001 | 0x0080 | 0x0100)
    return fortsetzen


def widgets_bereitstellen():
    """Definiert die Widget-Klassen, sobald Tkinter geladen ist."""
    global FlatButton

    class _FlatButton(_tk.Button):
        """Flacher Button mit Hover-Effekt in mehreren Farbvarianten."""

        @staticmethod
        def styles():
            """Farbvarianten - erst beim Aufruf gelesen, damit das Schema stimmt."""
            return {
                "primary":   (ACCENT, ACCENT_DARK, ON_ACCENT),
                "secondary": (BTN_BG, BTN_HOVER, BTN_TEXT),
                "success":   (OK, OK_DARK, ON_ACCENT),
            }

        def __init__(self, parent, text, command=None, kind="secondary", **kw):
            kw.setdefault("padx", 14)
            kw.setdefault("pady", 6)
            super().__init__(parent, text=text, command=command, relief="flat", bd=0,
                             highlightthickness=0, cursor="hand2", font=FONT_SMALL, **kw)
            self._kind = kind
            beschriften(self, text)                  # merkt sich uebersetzte Texte
            self.neu_faerben()
            self.bind("<Enter>", self._on_enter)
            self.bind("<Leave>", self._on_leave)
            GEFAERBTE_WIDGETS.append((self, None))       # faerbt sich selbst

        def neu_faerben(self):
            """Farben der eigenen Variante aus der aktuellen Palette holen."""
            styles = self.styles()
            bg, hover, fg = styles.get(self._kind, styles["secondary"])
            self._bg, self._hover = bg, hover
            self.configure(bg=bg, fg=fg, activebackground=hover, activeforeground=fg,
                           disabledforeground=BTN_DISABLED)

        def _enabled(self):
            return str(self["state"]) != "disabled"

        def _on_enter(self, _e):
            if self._enabled():
                self.configure(bg=self._hover)

        def _on_leave(self, _e):
            self.configure(bg=self._bg)

    FlatButton = _FlatButton


def make_card(parent, **pack_kw):
    """Karte mit dünnem Rahmen."""
    card = faerben(_tk.Frame(parent, highlightthickness=1),
                   bg="CARD", highlightbackground="BORDER", highlightcolor="BORDER")
    if pack_kw:
        card.pack(**pack_kw)
    return card


def card_title(parent, text):
    etikett = beschriften(faerben(_tk.Label(parent, font=FONT_BOLD, anchor="w"),
                                  bg="CARD", fg="TEXT"), text)
    etikett.pack(fill="x", padx=14, pady=(12, 6))
    return etikett


def px(wert: float) -> int:
    """Pixelmass fuer 96 dpi auf die Bildschirmskalierung umrechnen.

    Schriften wachsen mit der Windows-Skalierung von selbst mit, Pixelangaben
    wie wraplength nicht. Ohne Umrechnung braechen Texte bei 150 % frueher um
    als bei 100 %, und das Fenster saehe je nach Bildschirm anders aus.
    """
    return round(wert * SKALIERUNG)


# Von LicenseProbeApp beim Start gesetzt.
SKALIERUNG = 1.0

# Umbruchbreiten bei 96 dpi: Fliesstext in Karten und Hinweiszeilen
TEXT_BREITE = 470
HINWEIS_BREITE = 380


def card_text(parent, text, rolle="MUTED", font=None, wraplength=None):
    """Fliesstext in einer Karte."""
    etikett = beschriften(faerben(
        _tk.Label(parent, font=font or FONT_SMALL, justify="left", anchor="w",
                  wraplength=wraplength or px(TEXT_BREITE)),
        bg="CARD", fg=rolle), text)
    etikett.pack(fill="x", padx=14, pady=(0, 10))
    return etikett


class Hinweis:
    """Zeile, deren Text und Farbe am Zustand hängen.

    Der Text wird nicht fest gesetzt, sondern von einer Funktion gebildet,
    die beim Sprachwechsel erneut laeuft - so lassen sich auch Saetze aus
    mehreren uebersetzten Teilen zusammensetzen. Die Farbe steckt als Rolle
    ("MUTED", "OK", "WARN" ...) und folgt damit dem Schemawechsel.
    """

    def __init__(self, eltern, font=FONT_TINY, wraplength=None):
        wraplength = wraplength or px(HINWEIS_BREITE)
        self.rolle = "MUTED"
        self.bilden = lambda: ""
        self.label = _tk.Label(eltern, font=font, anchor="w", justify="left",
                               wraplength=wraplength)
        GEFAERBTE_WIDGETS.append((self, None))       # faerbt sich selbst
        self.neu_faerben()

    def setzen(self, bilden, rolle="MUTED"):
        self.bilden = bilden if callable(bilden) else (lambda: bilden)
        self.rolle = rolle
        self.auffrischen()
        self.neu_faerben()

    def auffrischen(self):
        self.label.configure(text=self.bilden())

    def neu_faerben(self):
        self.label.configure(bg=CARD, fg=THEMES[CURRENT_THEME][self.rolle])


# --------------------------------------------------------------------------
# Grafische Oberflaeche
# --------------------------------------------------------------------------

class LicenseProbeApp:
    """Hauptfenster mit den Reitern Lizenz, Erklärungen und Info."""

    def __init__(self, master) -> None:
        self.master = master
        # Das Fenster bleibt verborgen, bis es fertig aufgebaut und an seinem
        # Platz ist. Sonst zeigt Windows es beim ersten update_idletasks() an
        # der Standardposition, und es springt danach sichtbar zur Mitte.
        master.withdraw()

        self.aktiver_reiter = 0
        self.schluessel = {}                 # Quelle -> gelesener Schluessel oder None
        self.aktivierung_daten = None        # Ergebnis der letzten Abfrage
        self.abfrage_laeuft = False
        self.abfrage_nr = 0                  # verwirft Antworten ueberholter Abfragen
        self.antworten = []                  # (Nummer, Daten) aus dem Hintergrund-Thread
        self.abhol_auftrag = None            # laufender after()-Auftrag zum Abholen
        self._status = None                  # zuletzt gezeigte Statusmeldung
        global SKALIERUNG
        self.skalierung = SKALIERUNG = max(1.0, master.winfo_fpixels("1i") / 96.0)
        self.arbeitsflaeche = self._arbeitsflaeche_ermitteln()

        master.title(f"{PROGRAMM} {VERSION}")
        master.configure(bg=BG)
        master.protocol("WM_DELETE_WINDOW", self.schliessen)

        self._variablen_anlegen()
        self._stil_setzen()
        self._aufbauen()
        self._fenster_einpassen()
        master.deiconify()
        self.einlesen()

    # -- Bildschirm und Fenstergroesse -------------------------------------

    def _arbeitsflaeche_ermitteln(self, punkt=None) -> tuple[int, int, int, int] | None:
        """Arbeitsbereich (x, y, Breite, Höhe) eines Monitors ohne Taskleiste.

        Bei mehreren Bildschirmen umfasst winfo_screenwidth() die gesamte
        virtuelle Flaeche; zentriert man danach, landet das Fenster auf der
        Naht zwischen zwei Monitoren. Unter Windows liefert GetMonitorInfo
        deshalb den tatsaechlichen Arbeitsbereich.

        Ohne Punkt zaehlt der Monitor unter dem Mauszeiger. Mit Punkt (der
        gespeicherten Fensterlage) zaehlt der Monitor, auf dem er liegt; liegt
        er auf keinem, ist die Antwort None und der Aufrufer zentriert.
        """
        if sys.platform == "win32":
            try:
                import ctypes
                from ctypes import wintypes

                class MONITORINFO(ctypes.Structure):
                    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", wintypes.RECT),
                                ("rcWork", wintypes.RECT), ("dwFlags", wintypes.DWORD)]

                benutzer = ctypes.windll.user32
                stelle = wintypes.POINT()       # bleibt 0,0, falls die Abfrage scheitert
                if punkt is None:
                    benutzer.GetCursorPos(ctypes.byref(stelle))
                    monitor = benutzer.MonitorFromPoint(stelle, 2)   # naechstgelegener
                else:
                    stelle.x, stelle.y = int(punkt[0]), int(punkt[1])
                    monitor = benutzer.MonitorFromPoint(stelle, 0)   # keiner, wenn daneben
                if not monitor:
                    return None
                info = MONITORINFO()
                info.cbSize = ctypes.sizeof(MONITORINFO)
                if benutzer.GetMonitorInfoW(monitor, ctypes.byref(info)):
                    bereich = info.rcWork
                    return (bereich.left, bereich.top,
                            bereich.right - bereich.left, bereich.bottom - bereich.top)
            except (AttributeError, OSError, ValueError):
                pass
        breite, hoehe = self.master.winfo_screenwidth(), self.master.winfo_screenheight()
        if punkt is not None and not (0 <= punkt[0] < breite and 0 <= punkt[1] < hoehe):
            return None
        return (0, 0, breite, hoehe)

    def _fenster_einpassen(self) -> None:
        """Feste Fenstergröße bestimmen und das Fenster an seinen Platz legen.

        Die Groesse muss in jeder Sprache und fuer jedes Ergebnis reichen,
        denn spaeter soll sich am Fenster nichts mehr aendern - weder beim
        Sprachwechsel noch wenn die Aktivierungsabfrage nach ein paar Sekunden
        ihre Antwort liefert. Deshalb wird die Oberflaeche verborgen mit den
        laengsten moeglichen Hinweisen belegt und durch alle Sprachen
        geschickt; der groesste Bedarf gibt die Groesse vor.
        """
        breite, hoehe = self._groesster_bedarf()
        _rand_x, _rand_y, platz_breite, platz_hoehe = self.arbeitsflaeche
        passt = breite <= platz_breite and hoehe <= platz_hoehe
        breite, hoehe = min(breite, platz_breite), min(hoehe, platz_hoehe)

        x, y = self._startposition(breite, hoehe)
        self.master.geometry(f"{breite}x{hoehe}+{x}+{y}")
        # Nur wenn der Inhalt ausnahmsweise nicht auf den Bildschirm passt,
        # bleibt das Fenster veraenderbar - sonst waere es nicht zu bedienen.
        self.master.resizable(not passt, not passt)
        if not passt:
            self.master.minsize(round(420 * self.skalierung), round(320 * self.skalierung))

    def _groesster_bedarf(self) -> tuple[int, int]:
        """Platzbedarf der Oberfläche über alle Sprachen und Ergebnisse hinweg."""
        start = _.language
        breite = hoehe = 0
        aktiv = {"status": 5, "teil": "WWWWW",
                 "kanal": "Windows(R) Operating System, OEM_DM channel"}
        for code in self.sprachnamen:
            _.language = code
            texte_auffrischen()
            # Umbrochene Hinweise brechen an Wortgrenzen: Ein kuerzerer Text kann
            # eine breitere erste Zeile ergeben. Deshalb zaehlt jede Edition.
            for allgemein in (None, *sorted(set(ALLGEMEINE_SCHLUESSEL.values()))):
                self._hinweise_belegen({q: allgemein for q, *_rest in QUELLEN}, aktiv,
                                      muster=True)
                self.master.update_idletasks()
                breite = max(breite, self.master.winfo_reqwidth())
                hoehe = max(hoehe, self.master.winfo_reqheight())
        _.language = start
        texte_auffrischen()
        self._hinweise_belegen({}, None)
        self.master.update_idletasks()
        return breite, hoehe

    def _startposition(self, breite: int, hoehe: int) -> tuple[int, int]:
        """Gespeicherte Lage, sonst die Bildschirmmitte.

        Eine gespeicherte Lage wird uebernommen, aber so weit hereingerueckt,
        dass das Fenster ganz auf dem Bildschirm liegt.
        """
        fenster = load_config().get("fenster")
        if isinstance(fenster, dict):
            x, y = fenster.get("x"), fenster.get("y")
            if isinstance(x, int) and isinstance(y, int):
                bereich = self._arbeitsflaeche_ermitteln((x, y))
                if bereich:
                    rand_x, rand_y, platz_breite, platz_hoehe = bereich
                    self.arbeitsflaeche = bereich
                    return (max(rand_x, min(x, rand_x + platz_breite - breite)),
                            max(rand_y, min(y, rand_y + platz_hoehe - hoehe)))
        rand_x, rand_y, platz_breite, platz_hoehe = self.arbeitsflaeche
        return (rand_x + max(0, (platz_breite - breite) // 2),
                rand_y + max(0, (platz_hoehe - hoehe) // 2))

    # -- Zustand -----------------------------------------------------------

    def _variablen_anlegen(self) -> None:
        tk = _tk
        self.var_status = tk.StringVar(value="")
        self.var_dunkel = tk.BooleanVar(value=CURRENT_THEME == "dark")
        self.var_system = {k: tk.StringVar(value="–") for k in ("edition", "version", "build")}
        self.var_schluessel = {quelle: tk.StringVar(value="") for quelle, *_rest in QUELLEN}

    def _stil_setzen(self) -> None:
        """ttk-Bedienelemente an das gewählte Farbschema anpassen.

        Beim Schemawechsel genuegt es, diese Methode erneut aufzurufen: ttk
        zeichnet alle betroffenen Bedienelemente selbst neu.
        """
        tk, ttk = _tk, _ttk
        stil = ttk.Style()
        try:
            if stil.theme_use() != "clam":
                stil.theme_use("clam")
        except tk.TclError:
            pass

        # lightcolor/darkcolor sind die 3D-Kanten des clam-Themes - ohne sie
        # zeichnet Tk im dunklen Schema weisse Raender um das Feld
        stil.configure("TCombobox", fieldbackground=FIELD_BG, foreground=TEXT,
                       background=BTN_BG, bordercolor=BORDER,
                       lightcolor=BORDER, darkcolor=BORDER,
                       arrowcolor=TEXT, insertcolor=TEXT, padding=3)
        stil.map("TCombobox",
                 fieldbackground=[("readonly", FIELD_BG), ("disabled", BG)],
                 background=[("readonly", BTN_BG), ("active", BTN_HOVER)],
                 foreground=[("readonly", TEXT), ("disabled", BTN_DISABLED)],
                 bordercolor=[("focus", ACCENT)],
                 lightcolor=[("focus", ACCENT)],
                 darkcolor=[("focus", ACCENT)])

        # Klappliste der Auswahlfelder ist ein klassisches Listenfeld
        self.master.option_add("*TCombobox*Listbox.background", FIELD_BG)
        self.master.option_add("*TCombobox*Listbox.foreground", TEXT)
        self.master.option_add("*TCombobox*Listbox.selectBackground", ACCENT)
        self.master.option_add("*TCombobox*Listbox.selectForeground", ON_ACCENT)

        stil.configure("TNotebook", background=BG, bordercolor=BORDER, borderwidth=0)
        stil.configure("TNotebook.Tab", background=TAB_BG, foreground=MUTED,
                       bordercolor=BORDER, lightcolor=TAB_BG, darkcolor=TAB_BG,
                       padding=(16, 8), font=FONT_SMALL)
        stil.map("TNotebook.Tab",
                 background=[("selected", CARD), ("active", BTN_HOVER)],
                 foreground=[("selected", TEXT)],
                 lightcolor=[("selected", CARD)],
                 darkcolor=[("selected", CARD)])

    # -- Aufbau ------------------------------------------------------------

    def _aufbauen(self) -> None:
        tk, ttk = _tk, _ttk
        GEFAERBTE_WIDGETS.clear()
        BESCHRIFTUNGEN.clear()
        self.aussen = faerben(tk.Frame(self.master), bg="BG")
        self.aussen.pack(fill="both", expand=True)

        self._kopfzeile_bauen(self.aussen)

        self.reiter = ttk.Notebook(self.aussen)
        self.reiter.pack(fill="both", expand=True, padx=16, pady=(12, 0))

        # Alle Seiten werden gleich beim Start gebaut. Erst dadurch wechselt
        # der Reiter ohne Verzoegerung, und das Fenster kennt von Anfang an
        # seinen groessten Platzbedarf.
        for titel, bauen in ((_("Lizenz"), self._seite_lizenz_bauen),
                             (_("Erklärungen"), self._seite_hilfe_bauen),
                             (_("Info & Copyright"), self._seite_info_bauen)):
            seite = faerben(tk.Frame(self.reiter), bg="BG")
            self.reiter.add(seite)
            self._reiter_beschriften(seite, titel)
            bauen(seite)

        self._statusleiste_bauen(self.aussen)

        self.reiter.select(self.aktiver_reiter)
        self.reiter.bind("<<NotebookTabChanged>>",
                         lambda _e: setattr(self, "aktiver_reiter", self.reiter.index("current")))
        self.master.bind("<F5>", lambda _e: self.einlesen())

    def _reiter_beschriften(self, seite, titel) -> None:
        beschriftung_merken(lambda neu: self.reiter.tab(seite, text=f"  {neu}  "), titel)

    def _kopfzeile_bauen(self, eltern) -> None:
        tk, ttk = _tk, _ttk
        kopf = faerben(tk.Frame(eltern), bg="HEADER")
        kopf.pack(fill="x")

        marke = faerben(tk.Frame(kopf), bg="HEADER")
        marke.pack(side="left", padx=18, pady=12)
        faerben(tk.Label(marke, text=PROGRAMM, font=("Segoe UI", 15, "bold"), anchor="w"),
                bg="HEADER", fg="HEADER_TITLE").pack(fill="x")
        beschriften(faerben(tk.Label(marke, font=FONT_TINY, anchor="w"),
                            bg="HEADER", fg="HEADER_GROUP"),
                    _("Version {version}").format(version=VERSION)).pack(fill="x")

        umschalter = faerben(tk.Frame(kopf), bg="HEADER")
        umschalter.pack(side="right", padx=18)
        beschriften(faerben(tk.Label(umschalter, font=("Segoe UI", 8, "bold"), anchor="e"),
                            bg="HEADER", fg="HEADER_GROUP"),
                    _("Sprache & Darstellung")).pack(fill="x", pady=(10, 2))

        zeile = faerben(tk.Frame(umschalter), bg="HEADER")
        zeile.pack(fill="x", pady=(0, 10))
        self.sprachnamen = _.available()
        self.sprachfeld = ttk.Combobox(zeile, state="readonly", font=FONT_SMALL, width=12,
                                       values=list(self.sprachnamen.values()))
        self.sprachfeld.set(self.sprachnamen[_.language])
        self.sprachfeld.pack(side="left")
        self.sprachfeld.bind("<<ComboboxSelected>>", self._sprache_gewaehlt)

        beschriften(faerben(tk.Checkbutton(zeile, variable=self.var_dunkel,
                                           command=self._schema_umgeschaltet, font=FONT_SMALL,
                                           highlightthickness=0, bd=0, cursor="hand2"),
                            bg="HEADER", fg="HEADER_TEXT", activebackground="HEADER",
                            activeforeground="HEADER_TITLE", selectcolor="HEADER_HOVER"),
                    _("Dunkel")).pack(side="left", padx=(8, 0))

    def _statusleiste_bauen(self, eltern) -> None:
        tk = _tk
        leiste = faerben(tk.Frame(eltern), bg="STATUS_BG")
        leiste.pack(side="bottom", fill="x")
        faerben(tk.Label(leiste, textvariable=self.var_status, font=FONT_SMALL, anchor="w"),
                bg="STATUS_BG", fg="MUTED").pack(side="left", padx=14, pady=4)

    def _beschriftung_links(self, gitter, text, reihe, **grid_kw) -> None:
        """Bezeichnung in der linken Spalte eines Gitters."""
        beschriften(faerben(_tk.Label(gitter, font=FONT_SMALL, anchor="w"),
                            bg="CARD", fg="MUTED"), text).grid(
            row=reihe, column=0, sticky=grid_kw.pop("sticky", "w"), padx=(0, 14), **grid_kw)

    # -- Reiter 1: Lizenz --------------------------------------------------

    def _seite_lizenz_bauen(self, eltern) -> None:
        tk = _tk
        raster = faerben(tk.Frame(eltern), bg="BG")
        raster.pack(fill="both", expand=True, padx=14, pady=14)

        # --- System ---
        karte = make_card(raster, fill="x")
        card_title(karte, _("System"))
        gitter = faerben(tk.Frame(karte), bg="CARD")
        gitter.pack(fill="x", padx=14, pady=(0, 12))
        for reihe, (feld, titel) in enumerate((("edition", _("Edition")),
                                               ("version", _("Version")),
                                               ("build", _("Build")))):
            self._beschriftung_links(gitter, titel, reihe, pady=1)
            faerben(tk.Label(gitter, textvariable=self.var_system[feld], font=FONT_MONO,
                             anchor="w"),
                    bg="CARD", fg="TEXT").grid(row=reihe, column=1, sticky="w", pady=1)
        self._beschriftung_links(gitter, _("Aktivierung"), 3, sticky="nw", pady=1)
        self.aktivierung = Hinweis(gitter, font=FONT_SMALL)
        self.aktivierung.label.grid(row=3, column=1, sticky="w", pady=1)
        # Die Spalte ist so breit wie der Umbruch der Hinweise. Dann haengt die
        # Fensterbreite nicht davon ab, wo ein Text gerade umbricht.
        gitter.columnconfigure(1, minsize=px(HINWEIS_BREITE))

        # --- Produktschluessel ---
        karte = make_card(raster, fill="x", pady=(12, 0))
        card_title(karte, _("Produktschlüssel"))
        gitter = faerben(tk.Frame(karte), bg="CARD")
        gitter.pack(fill="x", padx=14, pady=(0, 4))
        gitter.columnconfigure(1, weight=1, minsize=px(HINWEIS_BREITE))
        self.knoepfe = {}
        self.hinweise = {}
        for nummer, (quelle, titel, _lesen, _herkunft) in enumerate(QUELLEN):
            reihe = nummer * 2
            abstand = (8 if nummer else 2, 0)
            self._beschriftung_links(gitter, _(titel), reihe, pady=abstand)
            feld = faerben(tk.Entry(gitter, textvariable=self.var_schluessel[quelle],
                                    font=FONT_SCHLUESSEL, state="readonly", relief="flat",
                                    bd=0, width=30, highlightthickness=0),
                           readonlybackground="CARD", fg="TEXT",
                           selectbackground="ACCENT", selectforeground="ON_ACCENT")
            feld.grid(row=reihe, column=1, sticky="w", pady=abstand)
            knopf = FlatButton(gitter, _("Kopieren"),
                               command=lambda q=quelle: self.kopieren(q), state="disabled")
            knopf.grid(row=reihe, column=2, sticky="e", padx=(8, 0), pady=abstand)
            self.knoepfe[quelle] = knopf
            hinweis = Hinweis(gitter)
            hinweis.label.grid(row=reihe + 1, column=1, columnspan=2, sticky="w")
            self.hinweise[quelle] = hinweis

        knoepfe = faerben(tk.Frame(karte), bg="CARD")
        knoepfe.pack(fill="x", padx=14, pady=(8, 14))
        self.knopf_einlesen = FlatButton(knoepfe, _("Neu einlesen"), self.einlesen,
                                         kind="primary")
        self.knopf_einlesen.pack(side="left")

    # -- Reiter 2: Erklärungen ---------------------------------------------

    def _seite_hilfe_bauen(self, eltern) -> None:
        tk = _tk
        raster = faerben(tk.Frame(eltern), bg="BG")
        raster.pack(fill="both", expand=True, padx=14, pady=14)

        karte = make_card(raster, fill="x")
        card_title(karte, _("Die drei Quellen"))
        card_text(karte, _("Firmware (OEM): Auf Rechnern mit vorinstalliertem Windows "
                           "hinterlegt der Hersteller den Schlüssel im BIOS/UEFI. Windows "
                           "liest ihn bei einer Neuinstallation von selbst."))
        card_text(karte, _("Installiert: der Schlüssel, mit dem das laufende Windows "
                           "installiert ist – aus dem Registry-Wert DigitalProductId "
                           "zurückgerechnet."))
        card_text(karte, _("Sicherung: die Kopie, die der Lizenzdienst von Windows "
                           "selbst aufbewahrt."))

        karte_digital = make_card(raster, fill="x", pady=(12, 0))
        card_title(karte_digital, _("Allgemeine Schlüssel und digitale Lizenz"))
        card_text(karte_digital,
                  _("Viele Rechner haben keinen eigenen Schlüssel mehr. Die Lizenz hängt "
                    "dann digital an der Hardware oder am Microsoft-Konto, und in der "
                    "Registry steht ein allgemeiner Installationsschlüssel von Microsoft. "
                    "LicenseProbe erkennt diese Schlüssel und markiert sie orange: Sie "
                    "sind öffentlich bekannt und keine Lizenz. Eine Neuinstallation "
                    "derselben Edition aktiviert sich trotzdem von selbst."))
        card_text(karte_digital,
                  _("Welcher Schlüssel gerade aktiv ist, verrät Windows nur über seine "
                    "letzten fünf Zeichen. Passt eine Quelle dazu, steht bei ihr "
                    "„derzeit aktiv“."))

        karte_daten = make_card(raster, fill="x", pady=(12, 0))
        card_title(karte_daten, _("Was gespeichert wird"))
        card_text(karte_daten,
                  _("Gespeichert werden nur Sprache, Farbschema und Fensterlage – in der "
                    "Datei {datei} neben dem Programm. Die Schlüssel werden nirgends "
                    "abgelegt und nicht übertragen; gelesen wird ausschließlich auf "
                    "diesem Rechner.").format(datei=CONFIG_NAME))

        karte_tasten = make_card(raster, fill="x", pady=(12, 0))
        card_title(karte_tasten, _("Tasten"))
        card_text(karte_tasten, _("F5 liest alle Angaben neu ein."))

    # -- Reiter 3: Info ----------------------------------------------------

    def _seite_info_bauen(self, eltern) -> None:
        tk = _tk
        raster = faerben(tk.Frame(eltern), bg="BG")
        raster.pack(fill="both", expand=True, padx=14, pady=14)

        karte = make_card(raster, fill="x")
        card_title(karte, f"{PROGRAMM} {VERSION}")
        card_text(karte, _("Zeigt die Windows-Produktschlüssel dieses Rechners im "
                           "Klartext – aus Firmware, Registry und der Sicherung von "
                           "Windows – und dazu den Aktivierungsstand."))
        card_text(karte, "Copyright 2026 Alexander Unverhau", rolle="TEXT")
        card_text(karte, _("Erstellt mit Unterstützung von Claude AI"))
        card_text(karte, _("Veröffentlicht unter der MIT-Lizenz."))

        karte_technik = make_card(raster, fill="x", pady=(12, 0))
        card_title(karte_technik, _("Technisches"))
        gitter = faerben(tk.Frame(karte_technik), bg="CARD")
        gitter.pack(fill="x", padx=14, pady=(0, 12))
        gitter.columnconfigure(1, weight=1)
        zeilen = (
            (_("Python"), sys.version.split()[0]),
            (_("Tkinter"), f"Tk {tk.TkVersion}"),
            (_("Quellen"), "ACPI MSDM · Registry · WMI"),
            (_("Einstellungen"), config_path()),
        )
        for reihe, (name, wert) in enumerate(zeilen):
            self._beschriftung_links(gitter, name, reihe, pady=1)
            # wraplength deckelt die Breite: Der Ablageort der Einstellungen ist
            # ein Dateipfad, und der kann beliebig lang sein - ohne Umbruch zoege
            # er das Fenster in die Breite, je nachdem, wo das Programm liegt.
            faerben(tk.Label(gitter, text=wert, font=FONT_MONO_SMALL, anchor="w",
                             justify="left", wraplength=px(TEXT_BREITE)),
                    bg="CARD", fg="TEXT").grid(row=reihe, column=1, sticky="w")

    # -- Einlesen ----------------------------------------------------------

    def einlesen(self) -> None:
        """Alle Angaben neu lesen; die Aktivierung kommt aus einem Hintergrund-Thread."""
        for feld, wert in system_angaben().items():
            self.var_system[feld].set(wert)
        for quelle, _titel, lesefunktion, _herkunft in QUELLEN:
            self.schluessel[quelle] = quelle_lesen(lesefunktion)
            self.knoepfe[quelle].configure(
                state="normal" if self.schluessel[quelle] else "disabled")
        self.aktivierung_daten = None
        self.abfrage_laeuft = True
        self._ergebnis_zeigen()
        self.status(_("Aktivierungsstand wird abgefragt …"))

        self.abfrage_nr += 1
        nummer = self.abfrage_nr
        threading.Thread(target=self._abfrage_im_hintergrund, args=(nummer,),
                         daemon=True).start()
        self._antwort_abholen()

    def _abfrage_im_hintergrund(self, nummer: int) -> None:
        # Tk ist nicht threadfest; der Hintergrund-Thread legt seine Antwort
        # deshalb nur ab, und der Hauptthread holt sie in _antwort_abholen().
        # Ein after() aus diesem Thread scheiterte, solange keine mainloop laeuft.
        self.antworten.append((nummer, aktivierung_abfragen()))

    def _antwort_abholen(self) -> None:
        """Abgelegte Antworten übernehmen; solange keine da ist, später erneut schauen."""
        self.abhol_auftrag = None
        while self.antworten:
            self.aktivierung_uebernehmen(*self.antworten.pop(0))
        if self.abfrage_laeuft:
            self.abhol_auftrag = self.master.after(100, self._antwort_abholen)

    def aktivierung_uebernehmen(self, nummer: int, daten) -> None:
        """Antwort der Aktivierungsabfrage anzeigen - sofern sie noch aktuell ist."""
        if nummer != self.abfrage_nr:
            return
        self.abfrage_laeuft = False
        self.aktivierung_daten = daten
        self._ergebnis_zeigen()
        if daten is None:
            self.status(_("Bereit – der Aktivierungsstand ist nicht verfügbar."))
        else:
            self.status(_("Bereit – F5 liest neu ein."))

    def _ergebnis_zeigen(self) -> None:
        """Schlüsselfelder und Hinweise aus dem gemerkten Zustand bilden."""
        for quelle, *_rest in QUELLEN:
            wert = self.schluessel.get(quelle)
            self.var_schluessel[quelle].set(wert or _("nicht vorhanden"))
        allgemein = {quelle: ALLGEMEINE_SCHLUESSEL.get(self.schluessel.get(quelle))
                     for quelle, *_rest in QUELLEN}
        aktiv = self.aktivierung_daten if not self.abfrage_laeuft else "laeuft"
        self._hinweise_belegen(allgemein, aktiv)

    def _hinweise_belegen(self, allgemein: dict, aktivierung, muster: bool = False) -> None:
        """Aktivierungszeile und die Hinweise unter den Schlüsseln setzen.

        allgemein ordnet jeder Quelle die Edition eines allgemeinen
        Installationsschluessels zu (oder None). aktivierung ist das Ergebnis
        der Abfrage, None bei einem Fehlschlag oder "laeuft", solange sie
        noch nicht zurueck ist. Mit muster=True gilt jede Quelle als aktiv -
        das ergibt die laengsten Hinweise, nach denen sich die Fenstergroesse
        richtet.
        """
        if aktivierung == "laeuft":
            self.aktivierung.setzen(lambda: _("wird abgefragt …"))
            teil = ""
        elif not aktivierung:
            self.aktivierung.setzen(lambda: _("konnte nicht abgefragt werden"), "DANGER")
            teil = ""
        else:
            text, rolle = LIZENZSTATUS.get(aktivierung["status"], STATUS_UNBEKANNT)
            teil = aktivierung["teil"]
            kanal = aktivierung["kanal"]

            def bilden(text=text, kanal=kanal, teil=teil):
                zeilen = [_(text)]
                if teil:
                    zeilen.append(_("Aktiver Schlüssel endet auf {teil}").format(teil=teil))
                if kanal:
                    zeilen[-1] += f"  ·  {kanal}"
                return "\n".join(zeilen)
            self.aktivierung.setzen(bilden, rolle)

        for quelle, _titel, _lesen, herkunft in QUELLEN:
            wert = self.schluessel.get(quelle) or ""
            edition = allgemein.get(quelle)
            ist_aktiv = muster or (bool(teil) and wert.endswith(teil))

            def bilden(herkunft=herkunft, edition=edition, ist_aktiv=ist_aktiv):
                if edition:
                    text = _("allgemeiner Installationsschlüssel für {edition} – die "
                             "Lizenz ist digital an Hardware oder Microsoft-Konto "
                             "gebunden").format(edition=edition)
                else:
                    text = _(herkunft)
                return f"✓ {_('derzeit aktiv')}  ·  {text}" if ist_aktiv else text
            rolle = "WARN" if edition else ("OK" if ist_aktiv else "MUTED")
            self.hinweise[quelle].setzen(bilden, rolle)

    # -- Kopieren ----------------------------------------------------------

    def kopieren(self, quelle: str) -> None:
        """Schlüssel einer Quelle in die Zwischenablage legen."""
        wert = self.schluessel.get(quelle)
        if not wert:
            return
        self.master.clipboard_clear()
        self.master.clipboard_append(wert)
        self.master.update()                 # uebergibt den Inhalt an Windows
        titel = next(t for q, t, *_rest in QUELLEN if q == quelle)
        self.status(_("Schlüssel „{quelle}“ in die Zwischenablage kopiert.").format(
            quelle=_(titel)))

    def status(self, text) -> None:
        """Statusmeldung zeigen und für einen späteren Sprachwechsel merken."""
        self._status = text
        self.var_status.set(text)

    def _laufende_texte_auffrischen(self) -> None:
        """Texte, die zur Laufzeit entstehen, in die aktuelle Sprache bringen."""
        if self._status is not None:
            self.var_status.set(neu_bilden(self._status))
        self._ergebnis_zeigen()

    # -- Sprache und Farbschema --------------------------------------------

    def _sprache_gewaehlt(self, _ereignis=None) -> None:
        gewaehlt = self.sprachfeld.get()
        for code, name in self.sprachnamen.items():
            if name == gewaehlt:
                self.sprache_setzen(code)
                return

    def sprache_setzen(self, code: str) -> None:
        """Sprache umstellen - die Oberfläche bleibt stehen, nur die Texte wechseln."""
        if code == _.language:
            return
        _.language = code
        self._einstellungen_sichern()

        fortsetzen = zeichnen_anhalten(self.master.winfo_id())
        try:
            texte_auffrischen()
            self._laufende_texte_auffrischen()
            self.sprachfeld.set(self.sprachnamen.get(code, self.sprachfeld.get()))
            self.master.update_idletasks()
        finally:
            fortsetzen()

    def _schema_umgeschaltet(self) -> None:
        self.schema_setzen("dark" if self.var_dunkel.get() else "light")

    def schema_setzen(self, name: str) -> None:
        """Zwischen hellem und dunklem Schema wechseln - ohne Neuaufbau."""
        if name == CURRENT_THEME:
            return
        apply_theme(name)
        self._einstellungen_sichern()

        fortsetzen = zeichnen_anhalten(self.master.winfo_id())
        try:
            self.master.configure(bg=BG)
            self._stil_setzen()
            farben_auffrischen()
            self.master.update_idletasks()
        finally:
            fortsetzen()

    # -- Einstellungen sichern ---------------------------------------------

    def _einstellungen_sichern(self, mit_fenster: bool = False) -> None:
        einstellungen = load_config()
        einstellungen["language"] = _.language
        einstellungen["theme"] = CURRENT_THEME
        if mit_fenster:
            einstellungen["fenster"] = {"x": self.master.winfo_x(), "y": self.master.winfo_y()}
        save_config(einstellungen)

    def schliessen(self) -> None:
        """Einstellungen samt Fensterlage sichern und das Fenster schließen."""
        self.abfrage_nr += 1                 # eine noch laufende Abfrage verfaellt
        if self.abhol_auftrag is not None:
            self.master.after_cancel(self.abhol_auftrag)
            self.abhol_auftrag = None
        self._einstellungen_sichern(mit_fenster=True)
        self.master.destroy()


# --------------------------------------------------------------------------
# Start
# --------------------------------------------------------------------------

def dpi_bewusstsein_aktivieren() -> float:
    """Meldet die Anwendung unter Windows als DPI-bewusst an.

    Ohne diese Anmeldung vergroessert Windows das Fenster nur als Bitmap - die
    Schrift wirkt dann unscharf. Rueckgabe ist die Systemskalierung.
    """
    if sys.platform != "win32":
        return 1.0
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)      # System-DPI beachten
        return ctypes.windll.user32.GetDpiForSystem() / 96.0
    except (AttributeError, OSError):                        # aeltere Windows-Fassungen
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except (AttributeError, OSError, NameError):
            pass
        return 1.0


def symbol_pfad() -> str:
    """Programmsymbol: als EXE steckt es in der EXE, sonst liegt die .ico daneben."""
    if ist_eingefroren():
        return sys.executable
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "licenseprobe.ico")


def startfehler_melden(text: str) -> None:
    """Startfehler auf der Konsole und - wenn moeglich - in einem Fenster zeigen.

    Unter pythonw.exe ist sys.stderr None, ein print() wuerde scheitern.
    """
    if sys.stderr is not None:
        print(text, file=sys.stderr)
    try:
        import tkinter as tk
        from tkinter import messagebox
        wurzel = tk.Tk()
        wurzel.withdraw()
        messagebox.showerror(f"{PROGRAMM} {VERSION}", text)
        wurzel.destroy()
    except Exception:                       # ohne Tkinter bleibt nur die Konsole
        pass


def gui_starten() -> int:
    """Startet die Oberfläche."""
    global _tk, _ttk
    try:
        import tkinter as _tk
        from tkinter import ttk as _ttk
    except ImportError:
        startfehler_melden("Fehler: Tkinter ist nicht verfügbar. / "
                           "Error: Tkinter is not available.")
        return 2

    _.language = startup_language()
    apply_theme(startup_theme())
    widgets_bereitstellen()

    skalierung = dpi_bewusstsein_aktivieren()
    wurzel = _tk.Tk()
    try:
        wurzel.iconbitmap(default=symbol_pfad())
    except _tk.TclError:                    # fehlt oder unlesbar: Voreinstellung
        pass
    if skalierung > 1.0:
        # Schriftgroessen sind in Punkt angegeben und muessen mitwachsen.
        wurzel.tk.call("tk", "scaling", skalierung * 96.0 / 72.0)
    LicenseProbeApp(wurzel)
    wurzel.mainloop()
    return 0


def main() -> int:
    return gui_starten()


# --------------------------------------------------------------------------
# SPRACHTABELLE / LANGUAGE TABLE
#
# Quellsprache ist Deutsch - der deutsche Text im Code ist zugleich der
# Schluessel. Eine weitere Sprache kommt in drei Schritten dazu:
#   1. Kuerzel und Anzeigename in LANGUAGE_NAMES eintragen,
#      z. B.  "fr": "Francais"
#   2. In TRANSLATIONS einen Eintrag "fr": { ... } anlegen und die
#      gewuenschten Zeilen uebersetzen.
#   3. Fertig - die Auswahl oben rechts zeigt die Sprache sofort an.
#
# Nicht uebersetzte Zeilen erscheinen automatisch auf Deutsch, eine
# unvollstaendige Tabelle ist also unproblematisch. Platzhalter in
# geschweiften Klammern - {teil}, {edition}, {datei} ... - muessen in der
# Uebersetzung unveraendert vorkommen; ihre Reihenfolge im Satz ist frei.
# --------------------------------------------------------------------------

LANGUAGE_NAMES = {
    "de": "Deutsch",
    "en": "English",
}

TRANSLATIONS = {
    "en": {
        # Kopfzeile und Reiter
        "Version {version}": "Version {version}",
        "Sprache & Darstellung": "Language & appearance",
        "Dunkel": "Dark",
        "Lizenz": "Licence",
        "Erklärungen": "Explanations",
        "Info & Copyright": "About & copyright",

        # Reiter 1
        "System": "System",
        "Edition": "Edition",
        "Version": "Version",
        "Build": "Build",
        "Aktivierung": "Activation",
        "Produktschlüssel": "Product keys",
        "Firmware (OEM)": "Firmware (OEM)",
        "Installiert": "Installed",
        "Sicherung": "Backup",
        "vom Hersteller im BIOS/UEFI hinterlegt": "stored in the BIOS/UEFI by the manufacturer",
        "aus der Registry zurückgerechnet": "decoded from the registry",
        "von Windows gesicherte Kopie": "copy kept by Windows",
        "Kopieren": "Copy",
        "Neu einlesen": "Read again",
        "nicht vorhanden": "not present",
        "derzeit aktiv": "currently active",
        "allgemeiner Installationsschlüssel für {edition} – die "
        "Lizenz ist digital an Hardware oder Microsoft-Konto "
        "gebunden":
            "generic installation key for {edition} – the licence is tied "
            "digitally to the hardware or a Microsoft account",
        "wird abgefragt …": "querying …",
        "konnte nicht abgefragt werden": "could not be queried",
        "Aktiver Schlüssel endet auf {teil}": "Active key ends in {teil}",
        "Nicht lizenziert": "Unlicensed",
        "Aktiviert": "Activated",
        "Kulanzzeit vor der Aktivierung": "Grace period before activation",
        "Kulanzzeit nach Hardwareänderung": "Grace period after a hardware change",
        "Kulanzzeit – kein Original": "Grace period – not genuine",
        "Benachrichtigungsmodus – nicht aktiviert": "Notification mode – not activated",
        "Verlängerte Kulanzzeit": "Extended grace period",
        "Stand unbekannt": "Status unknown",

        # Statuszeile
        "Aktivierungsstand wird abgefragt …": "Querying the activation status …",
        "Bereit – der Aktivierungsstand ist nicht verfügbar.":
            "Ready – the activation status is not available.",
        "Bereit – F5 liest neu ein.": "Ready – F5 reads everything again.",
        "Schlüssel „{quelle}“ in die Zwischenablage kopiert.":
            "Key “{quelle}” copied to the clipboard.",

        # Reiter 2
        "Die drei Quellen": "The three sources",
        "Firmware (OEM): Auf Rechnern mit vorinstalliertem Windows "
        "hinterlegt der Hersteller den Schlüssel im BIOS/UEFI. Windows "
        "liest ihn bei einer Neuinstallation von selbst.":
            "Firmware (OEM): on computers that came with Windows, the "
            "manufacturer stores the key in the BIOS/UEFI. Windows picks it up "
            "by itself when it is reinstalled.",
        "Installiert: der Schlüssel, mit dem das laufende Windows "
        "installiert ist – aus dem Registry-Wert DigitalProductId "
        "zurückgerechnet.":
            "Installed: the key the running Windows was installed with – "
            "decoded from the registry value DigitalProductId.",
        "Sicherung: die Kopie, die der Lizenzdienst von Windows "
        "selbst aufbewahrt.":
            "Backup: the copy the Windows licensing service keeps for itself.",
        "Allgemeine Schlüssel und digitale Lizenz": "Generic keys and digital licences",
        "Viele Rechner haben keinen eigenen Schlüssel mehr. Die Lizenz hängt "
        "dann digital an der Hardware oder am Microsoft-Konto, und in der "
        "Registry steht ein allgemeiner Installationsschlüssel von Microsoft. "
        "LicenseProbe erkennt diese Schlüssel und markiert sie orange: Sie "
        "sind öffentlich bekannt und keine Lizenz. Eine Neuinstallation "
        "derselben Edition aktiviert sich trotzdem von selbst.":
            "Many computers no longer have a key of their own. The licence is "
            "then tied digitally to the hardware or a Microsoft account, and the "
            "registry holds a generic installation key from Microsoft. "
            "LicenseProbe recognises these keys and marks them in orange: they "
            "are publicly known and not a licence. A reinstall of the same "
            "edition still activates by itself.",
        "Welcher Schlüssel gerade aktiv ist, verrät Windows nur über seine "
        "letzten fünf Zeichen. Passt eine Quelle dazu, steht bei ihr "
        "„derzeit aktiv“.":
            "Windows only reveals the last five characters of the key that is "
            "currently active. A source that matches them is marked "
            "“currently active”.",
        "Was gespeichert wird": "What is stored",
        "Gespeichert werden nur Sprache, Farbschema und Fensterlage – in der "
        "Datei {datei} neben dem Programm. Die Schlüssel werden nirgends "
        "abgelegt und nicht übertragen; gelesen wird ausschließlich auf "
        "diesem Rechner.":
            "Only language, colour scheme and window position are stored, in "
            "the file {datei} next to the program. The keys are never written "
            "down and never sent anywhere; everything is read on this computer "
            "only.",
        "Tasten": "Keys",
        "F5 liest alle Angaben neu ein.": "F5 reads everything again.",

        # Reiter 3
        "Zeigt die Windows-Produktschlüssel dieses Rechners im "
        "Klartext – aus Firmware, Registry und der Sicherung von "
        "Windows – und dazu den Aktivierungsstand.":
            "Shows the Windows product keys of this computer in plain text – "
            "from the firmware, the registry and the backup kept by Windows – "
            "together with the activation status.",
        "Erstellt mit Unterstützung von Claude AI":
            "Created with assistance of Claude AI",
        "Veröffentlicht unter der MIT-Lizenz.": "Released under the MIT licence.",
        "Technisches": "Technical details",
        "Python": "Python",
        "Tkinter": "Tkinter",
        "Quellen": "Sources",
        "Einstellungen": "Settings",
    },
}


if __name__ == "__main__":
    sys.exit(main())
