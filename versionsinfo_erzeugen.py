"""Erzeugt versionsinfo.txt, die Versionsangaben für die Windows-EXE.

PyInstaller legt von sich aus keine Versionsressource an: Ohne diese Datei
bleiben Produktname, Version und Urheber in den Dateieigenschaften leer, und
wer die EXE heruntergeladen hat, kann nicht nachsehen, welche Fassung vor ihm
liegt.

Die Angaben stammen aus PROGRAMM und VERSION in LicenseProbe.pyw, gelesen per
Suchausdruck statt per Import. Die erzeugte Datei ist abgeleitet und steht in
.gitignore.

Aufruf:  python versionsinfo_erzeugen.py
"""

from __future__ import annotations

import re
from pathlib import Path

HIER = Path(__file__).resolve().parent
QUELLE = HIER / "LicenseProbe.pyw"
ZIEL = HIER / "versionsinfo.txt"

URHEBER = "Alexander Unverhau"
JAHR = "2026"
BESCHREIBUNG = "LicenseProbe - zeigt die Windows-Produktschluessel"
HINWEIS = "Lizenzen der mitgelieferten Komponenten: DRITTANBIETER-LIZENZEN.md"

# Die Felder bleiben ASCII: PyInstaller liest die Datei als Python-Ausdruck ein,
# und in den Dateieigenschaften sollen keine verstümmelten Umlaute stehen.
SPRACHE = 1031          # Deutsch, die Quellsprache des Programms
ZEICHENSATZ = 1200      # Unicode
GRENZE = 65535          # so weit reicht eine Stelle im Versionsfeld


def aus_quelltext(name: str) -> str:
    """Den Wert einer Konstante holen; Abbruch, wenn sie nicht genau einmal dasteht."""
    text = QUELLE.read_text(encoding="utf-8")
    treffer = re.findall(rf'^{name}\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if len(treffer) != 1:
        raise SystemExit(f"{name} steht {len(treffer)}-mal in {QUELLE.name}, "
                         "erwartet war genau eine Zeile.")
    if not treffer[0].isascii():
        raise SystemExit(f"{name} = {treffer[0]!r} enthält Zeichen außerhalb von ASCII.")
    return treffer[0]


def vierstellig(version: str) -> tuple[int, int, int, int]:
    """Aus "1.0.1" wird (1, 0, 1, 0), denn Windows erwartet immer vier Zahlen."""
    if not re.fullmatch(r"\d+(\.\d+){0,3}", version):
        raise SystemExit(f"VERSION {version!r} muss die Form 1.2.3 haben. Vorabfassungen "
                         "wie 1.2.3rc1 kann die Versionsressource nicht abbilden.")
    zahlen = [int(teil) for teil in version.split(".")]
    if max(zahlen) > GRENZE:
        raise SystemExit(f"VERSION {version!r}: Jede Stelle darf höchstens {GRENZE} sein.")
    return tuple(zahlen + [0] * (4 - len(zahlen)))


def inhalt(name: str, version: str) -> str:
    haupt, neben, flick, bau = vierstellig(version)
    tabelle = f"{SPRACHE:04x}{ZEICHENSATZ:04x}".upper()
    return f"""# Von versionsinfo_erzeugen.py erstellt - nicht von Hand aendern.
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({haupt}, {neben}, {flick}, {bau}),
    prodvers=({haupt}, {neben}, {flick}, {bau}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '{tabelle}',
        [StringStruct('CompanyName', '{URHEBER}'),
        StringStruct('FileDescription', '{BESCHREIBUNG}'),
        StringStruct('FileVersion', {version!r}),
        StringStruct('InternalName', {name!r}),
        StringStruct('LegalCopyright',
                     'Copyright (c) {JAHR} {URHEBER} - MIT-Lizenz - '
                     'Erstellt mit Unterstuetzung von Claude AI'),
        StringStruct('OriginalFilename', '{name}.exe'),
        StringStruct('ProductName', {name!r}),
        StringStruct('ProductVersion', {version!r}),
        StringStruct('Comments', '{HINWEIS}')])
      ]),
    VarFileInfo([VarStruct('Translation', [{SPRACHE}, {ZEICHENSATZ}])])
  ]
)
"""


def main() -> None:
    name = aus_quelltext("PROGRAMM")
    version = aus_quelltext("VERSION")
    ZIEL.write_text(inhalt(name, version), encoding="utf-8", newline="\n")
    print(f"geschrieben: {ZIEL}  ({name} {version})")


if __name__ == "__main__":
    main()
