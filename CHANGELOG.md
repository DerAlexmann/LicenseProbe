# Änderungen

Das Format folgt [Keep a Changelog](https://keepachangelog.com/de/1.1.0/),
die Versionsnummern der [semantischen Versionierung](https://semver.org/lang/de/).

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
