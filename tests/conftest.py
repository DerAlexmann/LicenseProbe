"""Gemeinsame Vorrichtungen für die Tests.

Das Programm ist eine einzelne `.pyw`-Datei und damit über den gewöhnlichen
Import nicht erreichbar; geladen wird es deshalb über einen SourceFileLoader.
Gespeichert wird in den Tests nichts: `load_config` und `save_config` sind
ersetzt, sodass keine Einstellungsdatei entsteht.

Gelesen wird in den Tests der Oberfläche ebenfalls nichts vom echten System:
Schlüsselquellen, Systemangaben und Aktivierungsabfrage sind durch erfundene
Werte ersetzt. So bleiben die Tests auf jedem Rechner gleich, und kein echter
Schlüssel landet in einer Testausgabe.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import sys
import time
from pathlib import Path

import pytest

PROGRAMMDATEI = Path(__file__).resolve().parent.parent / "LicenseProbe.pyw"

# Erfundene Schlüssel - sie sehen aus wie echte, gehören aber zu nichts.
OEM_SCHLUESSEL = "TQ4PX-HNKW7-Y3C9R-BG8DM-2JVF6"
ALLGEMEIN_HOME = "YTMG3-N6DKC-DKB77-7M9GH-8HVX7"       # öffentlich, von Microsoft

SYSTEM = {"edition": "Windows 11 Pro", "version": "25H2", "build": "26200.1234"}
AKTIVIERT = {"status": 1, "teil": OEM_SCHLUESSEL[-5:],
             "kanal": "Windows(R) Operating System, OEM_DM channel"}


@pytest.fixture(scope="session")
def lp():
    """Das Programm als Modul."""
    lader = importlib.machinery.SourceFileLoader("licenseprobe", str(PROGRAMMDATEI))
    spec = importlib.util.spec_from_loader("licenseprobe", lader)
    modul = importlib.util.module_from_spec(spec)
    sys.modules["licenseprobe"] = modul
    lader.exec_module(modul)
    modul.save_config = lambda daten: True
    modul.load_config = lambda: {}
    return modul


class SofortThread:
    """Ersatz für threading.Thread, der sein Ziel sofort im selben Thread ausführt."""

    def __init__(self, target, args=(), daemon=None):
        self.target, self.args = target, args

    def start(self):
        self.target(*self.args)


@pytest.fixture
def system(lp, monkeypatch):
    """Erfundenes System; die Werte lassen sich im Test umstellen."""
    lage = {
        "schluessel_firmware": OEM_SCHLUESSEL,
        "schluessel_installiert": OEM_SCHLUESSEL,
        "schluessel_sicherung": None,
        "aktivierung": dict(AKTIVIERT),
    }
    for name in ("schluessel_firmware", "schluessel_installiert", "schluessel_sicherung"):
        monkeypatch.setattr(lp, name, lambda name=name: lage[name])
    monkeypatch.setattr(lp, "system_angaben", lambda: dict(SYSTEM))
    monkeypatch.setattr(lp, "aktivierung_abfragen", lambda: lage["aktivierung"])
    monkeypatch.setattr(lp.threading, "Thread", SofortThread)
    return lage


def oberflaeche_ist_pflicht():
    """In der Windows-CI darf die Oberfläche nicht ausfallen, siehe ci.yml."""
    return os.environ.get("OBERFLAECHE_PFLICHT") == "1"


def tk_wurzel_anlegen(tk, versuche=4, pflicht=False):
    """Eine Tk-Wurzel anlegen, notfalls in mehreren Anläufen.

    Auf den Windows-Läufern der CI schlägt das Anlegen gelegentlich mit
    "Can't find a usable init.tcl ... couldn't read file ...: No error" fehl:
    Die Startdateien von Tcl liegen am richtigen Ort, lassen sich in diesem
    Moment aber nicht lesen. Das ist eine Eigenheit der Umgebung und kein
    Befund über das Programm, deshalb ein paar Anläufe - und wenn es dabei
    bleibt, wird der Test übersprungen statt als Fehler gemeldet. Nur der Anker
    darf mit `pflicht` scheitern: Er entscheidet über alle Tests der Oberfläche.
    """
    letzter = None
    for nummer in range(versuche):
        try:
            return tk.Tk()
        except tk.TclError as fehler:
            letzter = fehler
            time.sleep(0.5 * (nummer + 1))
    if pflicht:
        pytest.fail(f"Tk ließ sich nicht starten: {letzter}")
    pytest.skip(f"Tk ließ sich nicht starten: {letzter}")
    return None                                  # unerreichbar, der Klarheit halber


@pytest.fixture(scope="session")
def tk_anker():
    """Eine Tk-Wurzel, die die ganze Sitzung über bestehen bleibt.

    Sie hält nur den Tcl-Interpreter am Leben: Zerstört man die letzte
    Tk-Instanz und legt gleich darauf eine neue an, findet Tcl auf manchen
    Rechnern seine Startdateien nicht mehr. Lässt sich schon der Anker nicht
    anlegen, gibt es keine Anzeige, und alle Tests der Oberfläche werden
    übersprungen.
    """
    pflicht = oberflaeche_ist_pflicht()
    if pflicht:
        import tkinter as tk
    else:
        tk = pytest.importorskip("tkinter", reason="Tkinter ist nicht verfügbar")
    anker = tk_wurzel_anlegen(tk, pflicht=pflicht)
    anker.withdraw()
    yield anker
    anker.destroy()


@pytest.fixture
def fenster(lp, tk_anker, system):
    """Baut Fenster der Anwendung und räumt sie hinterher weg.

    Die Farb- und Textverzeichnisse des Programms gelten für genau ein
    Fenster - `_aufbauen()` leert sie. Für Vergleiche mit einem frisch
    gebauten Fenster gibt es deshalb `vergleich()`, das die Verzeichnisse
    sichert und danach wiederherstellt.
    """
    import tkinter as tk
    from tkinter import ttk

    lp._tk, lp._ttk = tk, ttk
    lp.widgets_bereitstellen()
    offen = []

    class Werkstatt:
        def bauen(self, sprache="de", schema="light"):
            lp._.language = sprache
            lp.apply_theme(schema)
            wurzel = tk_wurzel_anlegen(tk)
            app = lp.LicenseProbeApp(wurzel)
            wurzel.update()
            offen.append(wurzel)
            return app

        def vergleich(self, sprache, schema):
            """Frisches Fenster bauen, hergeben, danach den alten Zustand zurückholen."""
            gemerkt_farben = list(lp.GEFAERBTE_WIDGETS)
            gemerkt_texte = list(lp.BESCHRIFTUNGEN)
            schema_vorher, sprache_vorher = lp.CURRENT_THEME, lp._.language
            app = self.bauen(sprache, schema)

            def zuruecksetzen():
                app.master.destroy()
                offen.remove(app.master)
                lp.GEFAERBTE_WIDGETS[:] = gemerkt_farben
                lp.BESCHRIFTUNGEN[:] = gemerkt_texte
                lp.apply_theme(schema_vorher)
                lp._.language = sprache_vorher

            return app, zuruecksetzen

    yield Werkstatt()

    for wurzel in offen:
        try:
            wurzel.destroy()
        except tk.TclError:                      # war schon zu
            pass
    lp._.language = lp.SOURCE_LANGUAGE
    lp.apply_theme(lp.DEFAULT_THEME)


def texte_sammeln(app):
    """Alle Beschriftungen samt Reitern, Schlüsselfeldern und Statuszeile."""
    import tkinter as tk

    app.master.update()
    gesammelt = []

    def lauf(widget, pfad):
        try:
            if "text" in widget.keys() and not (
                    "textvariable" in widget.keys() and str(widget.cget("textvariable"))):
                gesammelt.append((pfad, str(widget.cget("text"))))
        except tk.TclError:                      # ttk-Eigenheit, etwa bei Entry
            pass
        for nummer, kind in enumerate(widget.winfo_children()):
            lauf(kind, f"{pfad}/{kind.winfo_class()}{nummer}")

    lauf(app.master, "")
    for nummer in range(app.reiter.index("end")):
        gesammelt.append((f"reiter{nummer}", app.reiter.tab(nummer, "text")))
    gesammelt.append(("status", app.var_status.get()))
    for quelle, variable in app.var_schluessel.items():
        gesammelt.append((quelle, variable.get()))
    return gesammelt


FARBOPTIONEN = ("bg", "fg", "activebackground", "activeforeground",
                "highlightbackground", "highlightcolor", "selectcolor", "selectbackground",
                "selectforeground", "readonlybackground", "disabledbackground",
                "disabledforeground", "insertbackground")


def farben_sammeln(app):
    """Alle Farboptionen aller Widgets."""
    import tkinter as tk

    app.master.update()
    gesammelt = []

    def lauf(widget, pfad):
        for option in FARBOPTIONEN:
            try:
                if option in widget.keys():
                    gesammelt.append((pfad, option, str(widget.cget(option))))
            except tk.TclError:
                pass
        for nummer, kind in enumerate(widget.winfo_children()):
            lauf(kind, f"{pfad}/{kind.winfo_class()}{nummer}")

    lauf(app.master, "")
    return gesammelt
