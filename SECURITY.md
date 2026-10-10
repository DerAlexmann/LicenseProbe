# Sicherheit

## Eine Lücke melden

Bitte **kein öffentliches Issue** für Sicherheitslücken. Melde sie über
GitHub: Reiter **Security** → **Report a vulnerability**
([private Sicherheitsmeldung](../../security/advisories/new)). Die Meldung ist
nur für die Projektbetreuung sichtbar.

Hilfreich sind: eine Beschreibung des Problems, die Version des Programms (sie
steht in der Kopfzeile und auf dem Reiter „Info & Copyright"), das
Betriebssystem und, wenn möglich, eine Anleitung zum Nachstellen.

**Bitte in keiner Meldung – auch nicht in einem gewöhnlichen Issue – einen
vollständigen Produktschlüssel oder ein Bildschirmfoto davon mitschicken.**
Die letzten fünf Zeichen genügen immer.

Eine Antwort kommt in der Regel innerhalb einer Woche.

## Unterstützte Versionen

Gepflegt wird jeweils die neueste veröffentlichte Version.

| Version | Unterstützt |
|---|---|
| 1.0.x | ja |
| älter | nein |

## Wie das Programm mit den Schlüsseln umgeht

- **Gelesen** wird ausschließlich: aus der Registry (`HKLM`, nur lesend), aus
  der Firmware über `GetSystemFirmwareTable` und über eine
  WMI-Abfrage (`SoftwareLicensingProduct`) mit der PowerShell. Das Programm
  ändert nichts am System und braucht keine Administratorrechte.
- **Gespeichert** wird kein Schlüssel – weder in der Einstellungsdatei noch
  sonst auf der Festplatte. In `licenseprobe.json` stehen nur Sprache,
  Farbschema und Fensterlage.
- **Übertragen** wird nichts. Das Programm baut keine Netzwerkverbindungen auf
  und lädt nichts nach.
- **In die Zwischenablage** gelangt ein Schlüssel nur auf ausdrücklichen
  Wunsch, per Schalter „Kopieren". Was dort liegt, können andere Programme
  lesen – das ist der Sinn der Zwischenablage.
- **Auf dem Bildschirm** stehen die Schlüssel offen lesbar. Wer über die
  Schulter schauen kann oder ein Bildschirmfoto bekommt, kann sie mitlesen.

## Die veröffentlichte EXE

Die EXE ist nicht signiert. Prüfe nach dem Herunterladen die SHA-256-Summe
gegen die Angabe in den Release-Notizen:

```powershell
Get-FileHash .\LicenseProbe.exe -Algorithm SHA256
```

Wer lieber nichts Fertiges ausführt: Das Programm ist eine einzige lesbare
Python-Datei und lässt sich mit `build.cmd` selbst bauen.
