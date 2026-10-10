# Mitmachen

Fehlermeldungen, Verbesserungsvorschläge und Übersetzungen sind willkommen.
Dieses Projekt ist klein und bleibt es gern – eine Änderung sollte das
Programm einfacher zu bedienen machen, nicht umfangreicher.

*English: this file is in German, but issues and pull requests in English are
just as welcome.*

## Einen Fehler melden

Ein [Issue](../../issues) mit Version (steht in der Kopfzeile und auf dem
Reiter „Info & Copyright"), Betriebssystem und dem, was du erwartet hast.
Sicherheitslücken gehören nicht ins Issue, sondern in eine private Meldung –
siehe [SECURITY.md](SECURITY.md).

## Das Projekt im Überblick

| Datei | Inhalt |
|---|---|
| `LicenseProbe.pyw` | das ganze Programm, eine Datei |
| `tests/` | Tests für die Auswertung der Schlüssel, die Sprachtabelle und die Oberfläche |
| `build.cmd`, `icon_erzeugen.py` | EXE und Programmsymbol erzeugen |

Die Programmdatei ist von oben nach unten gegliedert: Farbschemata,
Sprachumschaltung, Einstellungen, Schlüssel lesen, Bausteine der Oberfläche,
die Klasse `LicenseProbeApp`, der Start – und ganz am Ende die Sprachtabelle.

## Entwickeln

```bash
pip install -r requirements-dev.txt
python -m pytest tests -q
python -m ruff check .
```

Das Programm selbst braucht keine Pakete, nur Python mit Tkinter.

Die Tests der Oberfläche brauchen einen Bildschirm; ohne Anzeige überspringt
`pytest` sie von selbst. Sie schreiben keine Einstellungsdatei und lesen
nichts vom echten System: Schlüssel, Systemangaben und Aktivierungsstand
kommen dort aus erfundenen Werten (`tests/conftest.py`). Die Auswertung der
Rohdaten – `DigitalProductId`, MSDM-Tabelle, Antwort der WMI-Abfrage – steckt
in eigenen Funktionen ohne Systemzugriff und läuft deshalb auch unter Linux.

## Stil

- **Deutsch** in Kommentaren, Docstrings und Bezeichnern; englische Begriffe
  nur, wo sie die eingeführten sind (`FlatButton`, `pack`, `widget`).
- **Zeilenlänge 100**, vier Leerzeichen, keine Tabs. `ruff` prüft das.
- **Kommentare erklären das Warum**, nicht das Was. Eine Zeile, die
  offensichtlich ist, braucht keinen Kommentar; eine Zeile, die überrascht,
  braucht einen.
- **Neue Texte** immer durch `_("…")` führen, sonst fehlen sie in der anderen
  Sprache. Ein Test achtet darauf.
- **Farben** nie direkt hinschreiben, sondern über die Rollen der
  Farbschemata (`faerben(widget, bg="CARD", fg="TEXT")`). Sonst bleibt beim
  Umschalten etwas in der falschen Farbe stehen – auch dafür gibt es einen
  Test.
- **Beschriftungen** über `beschriften(widget, _("…"))` setzen, damit sie den
  Sprachwechsel mitmachen.

## Eine Sprache ergänzen

Deutsch ist die Quellsprache: Der deutsche Text im Code ist zugleich der
Schlüssel. Am Ende von `LicenseProbe.pyw`:

1. Kürzel und Anzeigename in `LANGUAGE_NAMES` eintragen, etwa
   `"fr": "Français"`.
2. In `TRANSLATIONS` einen Abschnitt `"fr": { … }` anlegen und übersetzen.
   Platzhalter in geschweiften Klammern – `{teil}`, `{edition}`, `{datei}` –
   müssen unverändert vorkommen; ihre Stellung im Satz ist frei.
3. `python -m pytest tests/test_uebersetzungen.py` sagt dir, was noch fehlt.

Nicht übersetzte Zeilen erscheinen automatisch auf Deutsch, eine
unvollständige Tabelle ist also kein Problem.

Neue Texte dürfen das Fenster nicht sprengen: Die Fenstergröße wird beim Start
über alle Sprachen hinweg ermittelt und ändert sich danach nicht mehr. Wird
eine Beschriftung deutlich länger als die deutsche, wächst das Fenster für
alle. Der Test `test_fenster_passt_in_jede_sprache` prüft das.

## Pull Requests

- Eine Änderung pro Pull Request, mit kurzer Begründung.
- Tests und `ruff` müssen durchlaufen; die CI prüft beides.
- Für sichtbare Änderungen einen Eintrag in `CHANGELOG.md` unter
  „Unveröffentlicht" ergänzen.
- Bildschirmfotos zeigen ausschließlich das Programmfenster – kein Desktop,
  keine anderen Fenster, keine persönlichen Pfade und **keine echten
  Produktschlüssel**. Für Bilder die Lesefunktionen durch erfundene Werte
  ersetzen, wie es die Tests tun.

## Lizenz

Mit deinem Beitrag stimmst du zu, dass er unter der [MIT-Lizenz](LICENSE)
steht.
