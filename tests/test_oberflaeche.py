"""Die Oberfläche: Fenster, Anzeige, Kopieren, Umschalten, Einstellungen.

Braucht einen Bildschirm; ohne Tkinter oder ohne Anzeige werden diese Tests
übersprungen (siehe die Vorrichtung `fenster` in conftest.py). Alle Werte
stammen aus dem erfundenen System der Vorrichtung `system`.
"""

from __future__ import annotations

import json

from conftest import ALLGEMEIN_HOME, OEM_SCHLUESSEL, SYSTEM, farben_sammeln, texte_sammeln


def test_startgroesse_und_lage(lp, fenster):
    app = fenster.bauen()
    wurzel = app.master
    breite, hoehe = wurzel.winfo_width(), wurzel.winfo_height()
    rand_x, rand_y, platz_breite, platz_hoehe = app.arbeitsflaeche
    assert (wurzel.winfo_x(), wurzel.winfo_y()) == (
        rand_x + max(0, (platz_breite - breite) // 2),
        rand_y + max(0, (platz_hoehe - hoehe) // 2))
    assert wurzel.resizable() == (0, 0)
    assert wurzel.title() == f"{lp.PROGRAMM} {lp.VERSION}"


def test_angaben_werden_gezeigt(lp, fenster):
    app = fenster.bauen()
    for feld, wert in SYSTEM.items():
        assert app.var_system[feld].get() == wert
    assert app.var_schluessel["firmware"].get() == OEM_SCHLUESSEL
    assert app.var_schluessel["installiert"].get() == OEM_SCHLUESSEL
    assert app.var_schluessel["sicherung"].get() == "nicht vorhanden"
    assert str(app.knoepfe["firmware"]["state"]) == "normal"
    assert str(app.knoepfe["sicherung"]["state"]) == "disabled"


def test_aktiver_schluessel_wird_gruen_markiert(lp, fenster):
    app = fenster.bauen()
    palette = lp.THEMES[lp.CURRENT_THEME]
    for quelle in ("firmware", "installiert"):
        hinweis = app.hinweise[quelle]
        assert hinweis.label.cget("text").startswith("✓ derzeit aktiv")
        assert str(hinweis.label.cget("fg")) == palette["OK"]
    assert app.hinweise["sicherung"].rolle == "MUTED"
    text = app.aktivierung.label.cget("text")
    assert text.startswith("Aktiviert")
    assert OEM_SCHLUESSEL[-5:] in text
    assert app.aktivierung.rolle == "OK"
    assert app.var_status.get() == "Bereit – F5 liest neu ein."


def test_allgemeiner_schluessel_wird_orange_markiert(lp, fenster, system):
    system["schluessel_firmware"] = None
    system["schluessel_installiert"] = ALLGEMEIN_HOME
    system["aktivierung"] = {"status": 1, "teil": ALLGEMEIN_HOME[-5:], "kanal": ""}
    app = fenster.bauen()
    hinweis = app.hinweise["installiert"]
    assert hinweis.rolle == "WARN"
    assert "Home" in hinweis.label.cget("text")
    assert hinweis.label.cget("text").startswith("✓ derzeit aktiv")
    assert app.var_schluessel["firmware"].get() == "nicht vorhanden"


def test_fehlgeschlagene_abfrage(lp, fenster, system):
    system["aktivierung"] = None
    app = fenster.bauen()
    assert app.aktivierung.rolle == "DANGER"
    assert app.aktivierung.label.cget("text") == "konnte nicht abgefragt werden"
    assert not any(h.label.cget("text").startswith("✓") for h in app.hinweise.values())
    assert app.var_status.get() == "Bereit – der Aktivierungsstand ist nicht verfügbar."


def test_unbekannter_status(lp, fenster, system):
    system["aktivierung"] = {"status": 99, "teil": "", "kanal": ""}
    app = fenster.bauen()
    assert app.aktivierung.label.cget("text") == "Stand unbekannt"
    assert app.aktivierung.rolle == "WARN"


def test_ueberholte_antwort_wird_verworfen(lp, fenster):
    app = fenster.bauen()
    vorher = app.aktivierung.label.cget("text")
    app.aktivierung_uebernehmen(app.abfrage_nr - 1, None)
    assert app.aktivierung.label.cget("text") == vorher


def test_kopieren(lp, fenster):
    app = fenster.bauen()
    app.kopieren("firmware")
    assert app.master.clipboard_get() == OEM_SCHLUESSEL
    assert app.var_status.get() == "Schlüssel „Firmware (OEM)“ in die Zwischenablage kopiert."
    vorher = app.var_status.get()
    app.kopieren("sicherung")                          # nicht vorhanden: nichts geschieht
    assert app.var_status.get() == vorher


def test_neu_einlesen_uebernimmt_aenderungen(lp, fenster, system):
    app = fenster.bauen()
    system["schluessel_sicherung"] = OEM_SCHLUESSEL
    app.einlesen()
    app.master.update()
    assert app.var_schluessel["sicherung"].get() == OEM_SCHLUESSEL
    assert str(app.knoepfe["sicherung"]["state"]) == "normal"


def test_sprachwechsel_aendert_nur_die_texte(lp, fenster):
    app = fenster.bauen()
    app.kopieren("installiert")
    vorher = app.master.geometry()
    app.reiter.select(1)

    app.sprache_setzen("en")
    assert app.master.geometry() == vorher
    assert app.reiter.index("current") == 1
    assert app.var_status.get() == "Key “Installed” copied to the clipboard."

    app.reiter.select(0)
    umgeschaltet = texte_sammeln(app)
    frisch_app, zuruecksetzen = fenster.vergleich("en", "light")
    frisch_app.kopieren("installiert")
    frisch = texte_sammeln(frisch_app)
    zuruecksetzen()
    assert umgeschaltet == frisch


def test_schemawechsel_faerbt_nur_um(lp, fenster):
    app = fenster.bauen()
    vorher = app.master.geometry()

    app.var_dunkel.set(True)
    app._schema_umgeschaltet()
    assert app.master.geometry() == vorher
    assert lp.CURRENT_THEME == "dark"

    umgefaerbt = farben_sammeln(app)
    frisch_app, zuruecksetzen = fenster.vergleich("de", "dark")
    frisch = farben_sammeln(frisch_app)
    zuruecksetzen()
    assert umgefaerbt == frisch


def test_fenster_passt_in_jede_sprache(lp, fenster, system):
    """Die Startgröße muss den Bedarf jeder Sprache und jedes Ergebnisses decken."""
    app = fenster.bauen()
    breite, hoehe = app.master.winfo_width(), app.master.winfo_height()
    for sprache in lp.Translator().available():
        for installiert in (OEM_SCHLUESSEL, ALLGEMEIN_HOME):
            system["schluessel_installiert"] = installiert
            vergleichs_app, zuruecksetzen = fenster.vergleich(sprache, "light")
            vergleichs_app.master.update_idletasks()
            gebraucht = (vergleichs_app.master.winfo_reqwidth(),
                         vergleichs_app.master.winfo_reqheight())
            zuruecksetzen()
            assert gebraucht[0] <= breite and gebraucht[1] <= hoehe, (sprache, installiert)


def test_antwort_der_abfrage_veraendert_das_fenster_nicht(lp, fenster):
    app = fenster.bauen()
    vorher = app.master.geometry()
    app.abfrage_laeuft = True
    app._ergebnis_zeigen()
    app.master.update()
    assert app.master.geometry() == vorher
    app.aktivierung_uebernehmen(app.abfrage_nr, None)
    app.master.update()
    assert app.master.geometry() == vorher


def test_reiterwechsel_veraendert_das_fenster_nicht(lp, fenster):
    app = fenster.bauen()
    for sprache in ("de", "en"):
        app.sprache_setzen(sprache)
        vorher = app.master.geometry()
        for nummer in range(app.reiter.index("end")):
            app.reiter.select(nummer)
            app.master.update()
            assert app.master.geometry() == vorher, (sprache, nummer)
        app.reiter.select(0)


def test_einstellungen_enthalten_keinen_schluessel(lp, fenster, monkeypatch):
    app = fenster.bauen()
    gesichert = {}
    monkeypatch.setattr(lp, "save_config", lambda daten: gesichert.update(daten) or True)
    app._einstellungen_sichern(mit_fenster=True)

    assert set(gesichert) == {"language", "theme", "fenster"}
    assert set(gesichert["fenster"]) == {"x", "y"}
    text = json.dumps(gesichert)
    assert OEM_SCHLUESSEL not in text and OEM_SCHLUESSEL[-5:] not in text


def test_gespeicherte_einstellungen_kommen_zurueck(lp, fenster, monkeypatch):
    monkeypatch.setattr(lp, "load_config", lambda: {"language": "en", "theme": "dark"})
    assert lp.startup_language() == "en"
    assert lp.startup_theme() == "dark"
    app = fenster.bauen("en", "dark")
    assert app.var_dunkel.get() is True
    assert app.sprachfeld.get() == "English"


def test_unsinnige_einstellungen_werden_gefangen(lp, monkeypatch):
    monkeypatch.setattr(lp, "load_config", lambda: {"language": "xx", "theme": "lila"})
    assert lp.startup_theme() == lp.DEFAULT_THEME
    assert lp.startup_language() in lp.Translator().available()


def test_fensterlage_ausserhalb_des_bildschirms_wird_zur_mitte(lp, fenster, monkeypatch):
    monkeypatch.setattr(lp, "load_config", lambda: {"fenster": {"x": 99999, "y": 99999}})
    app = fenster.bauen()
    wurzel = app.master
    breite, hoehe = wurzel.winfo_width(), wurzel.winfo_height()
    rand_x, rand_y, platz_breite, platz_hoehe = app.arbeitsflaeche
    assert (wurzel.winfo_x(), wurzel.winfo_y()) == (
        rand_x + max(0, (platz_breite - breite) // 2),
        rand_y + max(0, (platz_hoehe - hoehe) // 2))
