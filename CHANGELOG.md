# Änderungen

Das Format folgt [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
die Versionsnummern der [semantischen Versionierung](https://semver.org/lang/de/).

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
