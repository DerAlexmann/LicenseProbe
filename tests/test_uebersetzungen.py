"""Die Sprachtabelle - vollständig, mit passenden Platzhaltern, ohne Karteileichen."""

from __future__ import annotations

import ast
import re

from conftest import PROGRAMMDATEI


def schluessel_im_quelltext():
    """Alle Texte, die im Code mit _("...") übersetzt werden."""
    baum = ast.parse(PROGRAMMDATEI.read_text(encoding="utf-8"))
    gefunden = set()
    for knoten in ast.walk(baum):
        if (isinstance(knoten, ast.Call) and isinstance(knoten.func, ast.Name)
                and knoten.func.id == "_" and knoten.args):
            erstes = knoten.args[0]
            if isinstance(erstes, ast.Constant) and isinstance(erstes.value, str):
                gefunden.add(erstes.value)
    return gefunden


def alle_schluessel(lp):
    """Feste Schlüssel aus dem Quelltext plus die zur Laufzeit gebildeten."""
    laufzeit = {titel for _q, titel, _l, _h in lp.QUELLEN}
    laufzeit |= {herkunft for _q, _t, _l, herkunft in lp.QUELLEN}
    laufzeit |= {text for text, _rolle in lp.LIZENZSTATUS.values()}
    laufzeit.add(lp.STATUS_UNBEKANNT[0])
    return schluessel_im_quelltext() | laufzeit


def test_jede_sprache_ist_vollstaendig(lp):
    erwartet = alle_schluessel(lp)
    for sprache, tabelle in lp.TRANSLATIONS.items():
        fehlend = sorted(schluessel for schluessel in erwartet if schluessel not in tabelle)
        assert not fehlend, f"{sprache}: {fehlend}"


def test_keine_karteileichen(lp):
    erwartet = alle_schluessel(lp)
    for sprache, tabelle in lp.TRANSLATIONS.items():
        ueberzaehlig = sorted(schluessel for schluessel in tabelle if schluessel not in erwartet)
        assert not ueberzaehlig, f"{sprache}: {ueberzaehlig}"


def test_platzhalter_bleiben_erhalten(lp):
    for sprache, tabelle in lp.TRANSLATIONS.items():
        for deutsch, uebersetzt in tabelle.items():
            assert (set(re.findall(r"{(\w+)}", deutsch))
                    == set(re.findall(r"{(\w+)}", uebersetzt))), f"{sprache}: {deutsch!r}"


def test_jede_sprache_hat_einen_namen(lp):
    for sprache in lp.TRANSLATIONS:
        assert sprache in lp.LANGUAGE_NAMES
    assert lp.SOURCE_LANGUAGE in lp.LANGUAGE_NAMES


def test_uebersetzer_faellt_auf_deutsch_zurueck(lp):
    uebersetzer = lp.Translator("en")
    unbekannt = "Ein Text, den niemand übersetzt hat"
    assert uebersetzer(unbekannt) == unbekannt


def test_uebersetzt_merkt_schluessel_und_werte(lp):
    uebersetzer = lp.Translator("en")
    text = uebersetzer("Aktiver Schlüssel endet auf {teil}").format(teil="ABCDE")
    assert text.schluessel == "Aktiver Schlüssel endet auf {teil}"
    assert text.werte == {"teil": "ABCDE"}
    assert text == "Active key ends in ABCDE"


def test_neu_bilden_uebersetzt_auch_eingesetzte_texte(lp):
    vorher = lp._.language
    try:
        lp._.language = "de"
        text = lp._("Schlüssel „{quelle}“ in die Zwischenablage kopiert.").format(
            quelle=lp._("Sicherung"))
        lp._.language = "en"
        assert lp.neu_bilden(text) == "Key “Backup” copied to the clipboard."
    finally:
        lp._.language = vorher


def test_quellsprache_gibt_den_text_zurueck(lp):
    uebersetzer = lp.Translator(lp.SOURCE_LANGUAGE)
    assert uebersetzer("Sicherung") == "Sicherung"
    assert uebersetzer("Sicherung").schluessel == "Sicherung"


def test_verfuegbare_sprachen_beginnen_mit_der_quellsprache(lp):
    namen = list(lp.Translator().available())
    assert namen[0] == lp.SOURCE_LANGUAGE
    assert set(namen) == {lp.SOURCE_LANGUAGE, *lp.TRANSLATIONS}
