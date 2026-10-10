"""Auswertung der Rohdaten - ohne Oberfläche und ohne Systemzugriff, läuft überall."""

from __future__ import annotations

import json
import random

import pytest


def kodieren(lp, schluessel: str, laenge: int = 164) -> bytes:
    """Gegenstück zu schluessel_entschluesseln(): baut eine DigitalProductId.

    Enthält der Schlüssel ein "N", wird es entfernt, seine Stelle als führende
    Ziffer vorangestellt und das Kennzeichen des neueren Verfahrens gesetzt.
    """
    zeichen = schluessel.replace("-", "")
    mit_n = "N" in zeichen
    if mit_n:
        stelle = zeichen.index("N")
        zeichen = lp.ZEICHEN[stelle] + zeichen[:stelle] + zeichen[stelle + 1:]
    zahl = 0
    for z in zeichen:
        zahl = zahl * 24 + lp.ZEICHEN.index(z)
    nutzlast = bytearray(zahl.to_bytes(15, "little"))
    if mit_n:
        nutzlast[14] |= 0x08
    return bytes(52) + bytes(nutzlast) + bytes(laenge - 67)


def zufallsschluessel(zufall, mit_n=True) -> str:
    zeichen = [zufall.choice("BCDFGHJKMPQRTVWXY2346789") for _ in range(24 if mit_n else 25)]
    if mit_n:
        zeichen.insert(zufall.randrange(24), "N")
    text = "".join(zeichen)
    return "-".join(text[i:i + 5] for i in range(0, 25, 5))


def test_allgemeine_schluessel_hin_und_zurueck(lp):
    for schluessel in lp.ALLGEMEINE_SCHLUESSEL:
        assert lp.schluessel_entschluesseln(kodieren(lp, schluessel)) == schluessel


def test_zufaellige_schluessel_hin_und_zurueck(lp):
    """Das "N" an jeder möglichen Stelle - auch dort, wo das letzte Byte groß wird."""
    zufall = random.Random(4711)
    for _wiederholung in range(500):
        schluessel = zufallsschluessel(zufall)
        assert lp.schluessel_entschluesseln(kodieren(lp, schluessel)) == schluessel


def test_n_an_jeder_stelle(lp):
    zufall = random.Random(2)
    for stelle in range(24):
        zeichen = [zufall.choice(lp.ZEICHEN) for _ in range(24)]
        zeichen.insert(stelle, "N")
        text = "".join(zeichen)
        schluessel = "-".join(text[i:i + 5] for i in range(0, 25, 5))
        assert lp.schluessel_entschluesseln(kodieren(lp, schluessel)) == schluessel


def test_aelteres_verfahren_ohne_n(lp):
    zufall = random.Random(7)
    for _wiederholung in range(50):
        schluessel = zufallsschluessel(zufall, mit_n=False)
        assert lp.schluessel_entschluesseln(kodieren(lp, schluessel)) == schluessel


@pytest.mark.parametrize("roh", [None, b"", bytes(66), "kein bytes", 12345])
def test_unbrauchbare_daten(lp, roh):
    assert lp.schluessel_entschluesseln(roh) is None


def test_lauter_nullen_ist_kein_schluessel(lp):
    assert lp.schluessel_entschluesseln(bytes(164)) is None


def test_gruppieren(lp):
    assert lp.gruppieren("BCDFGHJKMPQRTVWXY23467892") == "BCDFG-HJKMP-QRTVW-XY234-67892"


@pytest.mark.parametrize("text, erwartet", [
    ("tq4px-hnkw7-y3c9r-bg8dm-2jvf6", "TQ4PX-HNKW7-Y3C9R-BG8DM-2JVF6"),
    ("  TQ4PX-HNKW7-Y3C9R-BG8DM-2JVF6\0\0", "TQ4PX-HNKW7-Y3C9R-BG8DM-2JVF6"),
    ("TQ4PX-HNKW7-Y3C9R-BG8DM", None),
    ("TQ4PX-HNKW7-Y3C9R-BG8DM-2JVF", None),
    ("TQ4PXHNKW7Y3C9RBG8DM2JVF6XXXX", None),
    ("TQ4P!-HNKW7-Y3C9R-BG8DM-2JVF6", None),
    ("", None),
    (None, None),
    (42, None),
])
def test_schluessel_pruefen(lp, text, erwartet):
    assert lp.schluessel_pruefen(text) == erwartet


def msdm_tabelle(schluessel: bytes) -> bytes:
    """ACPI-Tabelle MSDM: 36 Byte Kopf, 20 Byte Verwaltung, dann der Schlüssel."""
    kopf = b"MSDM" + (85).to_bytes(4, "little") + bytes(28)
    return kopf + bytes(20) + schluessel


def test_msdm_liefert_den_schluessel(lp):
    tabelle = msdm_tabelle(b"TQ4PX-HNKW7-Y3C9R-BG8DM-2JVF6")
    assert len(tabelle) == 85
    assert lp.msdm_auswerten(tabelle) == "TQ4PX-HNKW7-Y3C9R-BG8DM-2JVF6"


@pytest.mark.parametrize("tabelle", [
    None, b"", bytes(84), bytes(85), b"MSDM" + bytes(81),
])
def test_msdm_ohne_schluessel(lp, tabelle):
    assert lp.msdm_auswerten(tabelle) is None


def test_aktivierung_auswerten(lp):
    ausgabe = json.dumps({"Description": "Windows(R) Operating System, RETAIL channel",
                          "LicenseStatus": 1, "PartialProductKey": "abcde"})
    assert lp.aktivierung_auswerten(ausgabe) == {
        "status": 1, "teil": "ABCDE", "kanal": "Windows(R) Operating System, RETAIL channel"}


def test_aktivierung_mit_mehreren_treffern(lp):
    ausgabe = json.dumps([{"LicenseStatus": 5, "PartialProductKey": "XYZ12"},
                          {"LicenseStatus": 1, "PartialProductKey": "AAAAA"}])
    assert lp.aktivierung_auswerten(ausgabe)["status"] == 5


@pytest.mark.parametrize("ausgabe", [None, "", "null", "[]", "kein json", "17", '"text"'])
def test_aktivierung_ohne_antwort(lp, ausgabe):
    assert lp.aktivierung_auswerten(ausgabe) is None


def test_aktivierung_mit_luecken(lp):
    daten = lp.aktivierung_auswerten('{"LicenseStatus": "eins"}')
    assert daten == {"status": None, "teil": "", "kanal": ""}


def test_jeder_status_hat_text_und_farbe(lp):
    for text, rolle in (*lp.LIZENZSTATUS.values(), lp.STATUS_UNBEKANNT):
        assert text
        for schema in lp.THEMES.values():
            assert schema[rolle].startswith("#")


def test_system_angaben_unter_windows_11(lp, monkeypatch):
    werte = {"CurrentBuild": "26200", "UBR": 1234, "ProductName": "Windows 10 Pro",
             "DisplayVersion": "25H2"}
    monkeypatch.setattr(lp, "_registry_wert", lambda pfad, name: werte.get(name))
    assert lp.system_angaben() == {
        "edition": "Windows 11 Pro", "version": "25H2", "build": "26200.1234"}


def test_system_angaben_unter_windows_10(lp, monkeypatch):
    werte = {"CurrentBuild": "19045", "ProductName": "Windows 10 Home", "ReleaseId": "2009"}
    monkeypatch.setattr(lp, "_registry_wert", lambda pfad, name: werte.get(name))
    assert lp.system_angaben() == {
        "edition": "Windows 10 Home", "version": "2009", "build": "19045"}


def test_system_angaben_ohne_registry(lp, monkeypatch):
    monkeypatch.setattr(lp, "_registry_wert", lambda pfad, name: None)
    assert lp.system_angaben() == {"edition": "Windows", "version": "–", "build": "–"}


def test_lesefunktionen_scheitern_leise(lp):
    """Auf jedem System - auch ohne Windows - kommt ein Schlüssel oder None zurück."""
    for _quelle, _titel, lesefunktion, _herkunft in lp.QUELLEN:
        wert = lp.quelle_lesen(lesefunktion)
        assert wert is None or lp.schluessel_pruefen(wert) == wert
