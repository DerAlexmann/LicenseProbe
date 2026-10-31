# LicenseProbe

[![CI](https://github.com/DerAlexmann/LicenseProbe/actions/workflows/ci.yml/badge.svg)](https://github.com/DerAlexmann/LicenseProbe/actions/workflows/ci.yml)

Zeigt die Windows-Produktschlüssel eines Rechners im Klartext – schnell und
ohne Umweg über Eingabeaufforderung oder Registry-Editor. Gelesen wird aus
Firmware, Registry und der Sicherung von Windows; dazu kommen Edition,
Version und Aktivierungsstand. Die Oberfläche ist deutsch und englisch, hell
und dunkel.

*[English version: README.en.md](README.en.md)*

![LicenseProbe im hellen Schema](docs/screenshots/licenseprobe-hell.png)

*Die Schlüssel auf den Bildern sind erfunden beziehungsweise öffentlich
bekannte Installationsschlüssel von Microsoft.*

## Was es kann

- **Drei Quellen auf einen Blick:**
  - **Firmware (OEM)** – der Schlüssel, den der Hersteller eines Rechners mit
    vorinstalliertem Windows im BIOS/UEFI hinterlegt hat (ACPI-Tabelle MSDM);
  - **Installiert** – der Schlüssel des laufenden Windows, aus dem
    Registry-Wert `DigitalProductId` zurückgerechnet;
  - **Sicherung** – die Kopie, die der Lizenzdienst von Windows selbst
    aufbewahrt (`BackupProductKeyDefault`).
- **Aktivierungsstand** samt Lizenzkanal (Retail, OEM, Volumen). Die Quelle,
  deren Schlüssel gerade aktiv ist, wird grün markiert.
- **Digitale Lizenz erkennen:** Steht nur ein allgemeiner
  Installationsschlüssel von Microsoft im System, markiert LicenseProbe ihn
  orange. Die Lizenz hängt dann an der Hardware oder am Microsoft-Konto, und
  der angezeigte Schlüssel ist keine Lizenz.
- **Kopieren** jedes Schlüssels mit einem Klick, **Neu einlesen** mit `F5`.
- **Deutsch und Englisch**, helles und dunkles Schema – beides umschaltbar,
  ohne dass sich das Fenster verändert.
- **Nur lesend und ohne Administratorrechte.** Kein Schlüssel wird
  gespeichert oder übertragen.

![LicenseProbe im dunklen Schema](docs/screenshots/licenseprobe-dunkel.png)

## Starten

**Als Programm:** `LicenseProbe.exe` aus den [Releases](../../releases)
herunterladen und starten. Es wird nichts installiert; die
Einstellungsdatei entsteht daneben, sobald Sprache oder Schema umgestellt
oder das Fenster geschlossen wird.

> **Beim ersten Start**: Die EXE ist nicht signiert. Windows SmartScreen
> fragt deshalb einmalig nach – „Weitere Informationen" → „Trotzdem
> ausführen". Auch ein Virenschutz hält eine frisch heruntergeladene,
> unbekannte Datei gern für ein paar Sekunden fest, während er sie prüft; ein
> Startversuch in dieser Zeit kann mit „Zugriff verweigert" abbrechen.
> Einfach kurz warten und erneut starten. Wer sichergehen will, vergleicht
> vorher die SHA-256-Prüfsumme aus den Release-Notizen.

**Als Skript:** `LicenseProbe.pyw` doppelklicken. Nötig ist nur Python 3.10
oder neuer mit Tkinter, das bei der Windows-Installation dabei ist. Weitere
Pakete braucht das Programm nicht.

```bash
python LicenseProbe.pyw
```

## Tasten

| Taste | Wirkung |
|---|---|
| `F5` | alle Angaben neu einlesen |

## Wie die Schlüssel gelesen werden

- **Installiert:** Windows speichert den Schlüssel nicht im Klartext, sondern
  als Zahl zur Basis 24 in den Bytes 52 bis 66 von `DigitalProductId`.
  LicenseProbe rechnet sie zurück – einschließlich des Verfahrens ab
  Windows 8, bei dem ein „N" an einer verschlüsselten Stelle eingefügt wird.
- **Firmware:** `GetSystemFirmwareTable` liefert die ACPI-Tabelle MSDM; ab
  Byte 56 steht dort der OEM-Schlüssel als Text. Fehlt die Tabelle, hat der
  Rechner keinen hinterlegten Schlüssel.
- **Aktivierung:** eine WMI-Abfrage von `SoftwareLicensingProduct` über die
  PowerShell. Sie dauert ein paar Sekunden und läuft im Hintergrund; Windows
  verrät dabei nur die letzten fünf Zeichen des aktiven Schlüssels.

Keiner dieser Wege braucht Administratorrechte, und keiner ändert etwas am
System. In der Einstellungsdatei `licenseprobe.json` stehen nur Sprache,
Schema und Fensterlage.

## Eine Sprache ergänzen

Deutsch ist die Quellsprache: Der deutsche Text im Code ist zugleich der
Schlüssel. Am Ende von `LicenseProbe.pyw` stehen `LANGUAGE_NAMES` und
`TRANSLATIONS`. Ein Kürzel in `LANGUAGE_NAMES`, ein Abschnitt in
`TRANSLATIONS` – fertig, die Auswahl oben rechts zeigt die Sprache sofort an.
Nicht übersetzte Zeilen erscheinen automatisch auf Deutsch.

## Selbst bauen

```bash
pip install -r requirements-build.txt
build.cmd
```

Das Ergebnis liegt anschließend in `dist\LicenseProbe.exe`. Das
Programmsymbol lässt sich mit `python icon_erzeugen.py` neu erzeugen; dafür
wird Pillow gebraucht.

## Mitmachen

Fehlermeldungen, Vorschläge und Übersetzungen sind willkommen –
[CONTRIBUTING.md](CONTRIBUTING.md) erklärt Aufbau, Stil und Tests. Bitte in
Issues nie einen vollständigen Produktschlüssel posten; die letzten fünf
Zeichen genügen. Sicherheitslücken bitte nicht als Issue, sondern über den
Weg in [SECURITY.md](SECURITY.md).

## Lizenz

[MIT](LICENSE) – Copyright 2026 Alexander Unverhau.
Erstellt mit Unterstützung von Claude AI.

Die EXE enthält Bestandteile anderer Projekte, etwa Python, Tcl/Tk und OpenSSL.
Sie stehen mit Lizenz und Quelle in
[DRITTANBIETER-LIZENZEN.md](DRITTANBIETER-LIZENZEN.md); siehe auch
[NOTICE](NOTICE).
