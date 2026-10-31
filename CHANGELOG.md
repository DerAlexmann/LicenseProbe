# Änderungen

Das Format folgt [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
die Versionsnummern der [semantischen Versionierung](https://semver.org/lang/de/).

## Unveröffentlicht

### Hinzugefügt

- Die EXE trägt Versionsangaben: Produktname, Version und Urheber stehen in den
  Dateieigenschaften von Windows.
- `DRITTANBIETER-LIZENZEN.md`, `NOTICE` und der Ordner `lizenzen/` nennen die
  Fremdbestandteile der EXE samt Lizenz, Quelle und Lizenztext.
- Ein Release-Workflow baut EXE und Quellpaket auf GitHub, prüft die fertige EXE
  und legt bei einem Tag einen Entwurf an. Am Release hängen künftig auch
  Prüfsumme, Quellpaket und Lizenzdatei.
- Dependabot schlägt monatlich neue Fassungen vor; die Untergrenzen bleiben.

### Geändert

- Der Bau legt PyInstaller und Python auf genaue Versionen fest. Mitgezogene
  Abhängigkeiten sind nicht festgelegt, Hash-Pins gibt es nicht, und der Bau ist
  nicht Bit für Bit reproduzierbar.
- Die CI testet zusätzlich mit Python 3.14, der Fassung des Baus. Unter Windows
  darf der Start der Oberflächentests nicht mehr still übersprungen werden.

### Behoben

- `pyproject.toml` nennt die Version wieder passend zum Programm; ein Test hält
  beide Angaben gleich.

## [1.0.1] – 2026-10-11

### Sicherheit

- Die PowerShell für die Abfrage des Aktivierungsstands wird jetzt mit
  vollständigem Pfad aus dem Systemordner gestartet. Bisher genügte der Name
  `powershell.exe`; Windows sucht dann zuerst im Programmordner und im
  aktuellen Ordner. Lag dort eine fremde Datei dieses Namens – etwa im
  Download-Ordner, aus dem die EXE gestartet wurde –, wäre sie an Stelle der
  echten PowerShell ausgeführt worden.

## [1.0.0] – 2026-10-10

Erste Fassung.

- Produktschlüssel aus drei Quellen im Klartext: Firmware (OEM-Schlüssel aus
  der ACPI-Tabelle MSDM), Installiert (aus `DigitalProductId` in der Registry
  zurückgerechnet) und Sicherung (`BackupProductKeyDefault`).
- Edition, Version, Build und Aktivierungsstand samt Lizenzkanal. Die Quelle,
  deren Schlüssel gerade aktiv ist, wird grün markiert.
- Allgemeine Installationsschlüssel von Microsoft werden erkannt und orange
  markiert, mit dem Hinweis auf die digitale Lizenz.
- Jeder Schlüssel mit einem Klick in die Zwischenablage, Neu einlesen mit `F5`.
- Deutsch und Englisch, helles und dunkles Schema – umschaltbar, ohne dass
  sich Fenstergröße, Fensterlage oder der gewählte Reiter ändern.
- Sprache, Schema und Fensterlage bleiben bis zum nächsten Start erhalten;
  die Schlüssel selbst werden nirgends gespeichert.
