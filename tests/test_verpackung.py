"""Wächter für die Auslieferung: Lizenzen, Versionsangaben, fester Bau, Workflows.

Die Vorkehrungen verfallen sonst still, weil ihr Fehlen nichts rot färbt. Alle
Tests lesen nur Dateien und laufen ohne Oberfläche und ohne PyYAML.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

WURZEL = Path(__file__).resolve().parent.parent
RELEASE = WURZEL / ".github/workflows/release.yml"
CI = WURZEL / ".github/workflows/ci.yml"
LIZENZDATEI = "DRITTANBIETER-LIZENZEN.md"

BESTANDTEILE = (
    "Python", "PyInstaller", "OpenSSL", "libffi", "Tcl/Tk", "libtommath", "zlib",
    "bzip2", "XZ Utils", "Zstandard", "libmpdec", "mimalloc", "Microsoft Visual C++",
)
LIZENZTEXTE = {
    "Python-LICENSE.txt": ("PYTHON SOFTWARE FOUNDATION LICENSE", "Apache License",
                           "libbzip2", "libffi", "Zstandard", "Microsoft Distributable Code",
                           "copyrighted by the Regents of the University"),
    "Python-eingebaute-Bibliotheken.txt": ("libmpdec", "zlib", "mimalloc"),
    "PyInstaller-COPYING.txt": ("Bootloader Exception", "GNU GENERAL PUBLIC LICENSE"),
}


def lesen(pfad: Path | str) -> str:
    return (WURZEL / pfad).read_text(encoding="utf-8")


def ohne_kommentare(text: str) -> str:
    """Ein erwähnender Kommentar darf keinen Wächter zufriedenstellen."""
    return "\n".join(z for z in text.splitlines() if not z.lstrip().startswith(("#", "REM ")))


def jobs(text: str) -> dict[str, str]:
    """Die Jobs einer Workflow-Datei; `on:` kennt gleich tief eingerückte Schlüssel."""
    teil = ohne_kommentare(text).split("\njobs:\n", 1)[1]
    stuecke = re.split(r"^  ([\w-]+):\n", teil, flags=re.MULTILINE)
    return dict(zip(stuecke[1::2], stuecke[2::2], strict=True))


def aktionsschritte(job: str, aktion: str) -> list[str]:
    return [s for s in re.split(r"^      - ", job, flags=re.MULTILINE) if aktion in s]


@pytest.fixture(scope="module")
def versionsinfo():
    pfad = WURZEL / "versionsinfo_erzeugen.py"
    spec = importlib.util.spec_from_file_location("versionsinfo_erzeugen", pfad)
    modul = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modul
    spec.loader.exec_module(modul)
    return modul


# --- Eine Versionsquelle ---------------------------------------------------

def test_pyproject_nennt_die_version_des_programms(lp):
    # Suchausdruck statt tomllib: Das gibt es erst ab Python 3.11.
    treffer = re.findall(r'^version = "([^"]+)"$', lesen("pyproject.toml"), re.MULTILINE)
    assert treffer == [lp.VERSION]


def test_security_nennt_die_aktuelle_reihe(lp):
    haupt, neben = lp.VERSION.split(".")[:2]
    assert re.search(rf"^\| {haupt}\.{neben}\.x \| ja \|$", lesen("SECURITY.md"), re.MULTILINE)


# --- Versionsangaben -------------------------------------------------------

@pytest.mark.parametrize(("version", "erwartet"), [
    ("1.0.1", (1, 0, 1, 0)),
    ("2", (2, 0, 0, 0)),
    ("1.2.3.4", (1, 2, 3, 4)),
])
def test_version_wird_vierstellig(versionsinfo, version, erwartet):
    assert versionsinfo.vierstellig(version) == erwartet


@pytest.mark.parametrize("version", ["1.2.3rc1", "1.2.3.4.5", "1..2", "", "1.70000"])
def test_unbrauchbare_version_wird_abgelehnt(versionsinfo, version):
    with pytest.raises(SystemExit, match="VERSION"):
        versionsinfo.vierstellig(version)


def test_doppelte_konstante_bricht_ab(versionsinfo, tmp_path, monkeypatch):
    quelle = tmp_path / "LicenseProbe.pyw"
    quelle.write_text('VERSION = "1.0.0"\nVERSION = "2.0.0"\n', encoding="utf-8")
    monkeypatch.setattr(versionsinfo, "QUELLE", quelle)
    with pytest.raises(SystemExit, match="2-mal"):
        versionsinfo.aus_quelltext("VERSION")


@pytest.mark.parametrize(("quelltext", "meldung"), [
    ("# keine Version\n", "0-mal"),
    ('VERSION = "1.0.ä"\n', "ASCII"),
])
def test_unbrauchbare_konstante_bricht_ab(versionsinfo, tmp_path, monkeypatch, quelltext, meldung):
    quelle = tmp_path / "LicenseProbe.pyw"
    quelle.write_text(quelltext, encoding="utf-8")
    monkeypatch.setattr(versionsinfo, "QUELLE", quelle)
    with pytest.raises(SystemExit, match=meldung):
        versionsinfo.aus_quelltext("VERSION")


def test_versionsdatei_ist_auswertbar(versionsinfo, tmp_path, monkeypatch):
    """PyInstaller wertet die Datei als Ausdruck aus; Teilstrings beweisen das nicht."""
    quelle = tmp_path / "LicenseProbe.pyw"
    quelle.write_text('PROGRAMM = "Probe"\nVERSION = "1.2.3"\n', encoding="utf-8")
    ziel = tmp_path / "versionsinfo.txt"
    monkeypatch.setattr(versionsinfo, "QUELLE", quelle)
    monkeypatch.setattr(versionsinfo, "ZIEL", ziel)
    versionsinfo.main()

    aufrufe = {}

    def baustein(name):
        def bauen(*args, **kwargs):
            aufrufe[name] = (args, kwargs)
            return name
        return bauen

    namen = ("VSVersionInfo", "FixedFileInfo", "StringFileInfo", "StringTable",
             "StringStruct", "VarFileInfo", "VarStruct")
    assert eval(ziel.read_text(encoding="utf-8"),  # noqa: S307
                {name: baustein(name) for name in namen}) == "VSVersionInfo"
    assert aufrufe["FixedFileInfo"][1]["filevers"] == (1, 2, 3, 0)


def test_versionsdatei_kommt_aus_dem_programm(versionsinfo, lp):
    assert versionsinfo.aus_quelltext("VERSION") == lp.VERSION
    assert versionsinfo.aus_quelltext("PROGRAMM") == lp.PROGRAMM
    text = versionsinfo.inhalt(lp.PROGRAMM, "1.2.3")
    assert text.isascii()
    assert "filevers=(1, 2, 3, 0)" in text
    assert "StringStruct('ProductVersion', '1.2.3')" in text
    assert "Claude AI" in text


def test_versionsdatei_ist_abgeleitet():
    assert "versionsinfo.txt" in lesen(".gitignore").splitlines()


def test_beide_bauwege_nutzen_die_versionsdatei():
    build = ohne_kommentare(lesen("build.cmd"))
    assert "versionsinfo_erzeugen.py" in build
    assert '--version-file "versionsinfo.txt"' in build
    exe = jobs(lesen(RELEASE))["windows-exe"]
    assert "python versionsinfo_erzeugen.py" in exe
    assert "--version-file versionsinfo.txt" in exe


# --- Fester Bau ------------------------------------------------------------

@pytest.mark.parametrize("datei", ["requirements-build.txt", "requirements-stil.txt"])
def test_feste_versionen(datei):
    zeilen = [z for z in ohne_kommentare(lesen(datei)).splitlines() if z.strip()]
    assert zeilen
    assert all(re.fullmatch(r"[\w-]+==[\w.]+", z) for z in zeilen), zeilen


def test_ci_baut_mit_den_festen_fassungen():
    exe = jobs(lesen(RELEASE))["windows-exe"]
    assert "pip install -r requirements-build.txt" in exe
    assert re.search(r'python-version: "\d+\.\d+\.\d+"', exe)
    stil = jobs(lesen(CI))["stil"]
    assert "pip install -r requirements-stil.txt" in stil


def test_ci_testet_die_python_fassung_des_baus():
    fassung = re.search(r'python-version: "(\d+\.\d+)\.\d+"',
                        jobs(lesen(RELEASE))["windows-exe"]).group(1)
    assert f'"{fassung}"' in re.search(r"python: \[(.*)\]", lesen(CI)).group(1)


def test_ci_testet_die_aelteste_erlaubte_python_fassung():
    aelteste = re.search(r'^requires-python = ">=([\d.]+)"$', lesen("pyproject.toml"),
                         re.MULTILINE).group(1)
    assert f'"{aelteste}"' in re.search(r"python: \[(.*)\]", lesen(CI)).group(1)


# --- Release-Workflow ------------------------------------------------------

def test_nur_der_release_job_haengt_am_tag():
    alle = jobs(lesen(RELEASE))
    assert set(alle) == {"quellpaket", "windows-exe", "release"}
    assert "    if: github.ref_type == 'tag'\n" in alle["release"]
    assert "github.ref_type" not in alle["quellpaket"] + alle["windows-exe"]


def test_workflow_ist_probelauffaehig():
    kopf = lesen(RELEASE).split("\njobs:\n")[0]
    assert "workflow_dispatch:" in kopf
    assert "pull_request:" in kopf
    assert 'tags: ["v*"]' in kopf


def gepackte_dateien() -> list[str]:
    befehl = re.search(r"cp -r (.*?) out/LicenseProbe/", jobs(lesen(RELEASE))["quellpaket"], re.S)
    return befehl.group(1).replace("\\", " ").split()


def test_gepackte_dateien_gibt_es():
    assert len(gepackte_dateien()) >= 8
    for name in gepackte_dateien():
        assert (WURZEL / name).exists(), name


@pytest.mark.parametrize("datei", ["build.cmd", "versionsinfo_erzeugen.py",
                                   "requirements-build.txt"])
def test_quellpaket_laesst_sich_bauen(datei):
    assert datei in gepackte_dateien()


def test_schreibrecht_hat_nur_der_release_job():
    text = ohne_kommentare(lesen(RELEASE))
    assert re.search(r"^permissions:\n  contents: read$", text, re.MULTILINE)
    alle = jobs(text)
    assert "contents: write" in alle["release"]
    assert "contents: write" not in alle["quellpaket"] + alle["windows-exe"]


def test_release_bleibt_entwurf_und_ohne_stille_luecken():
    release = jobs(lesen(RELEASE))["release"]
    assert re.search(r"^\s+draft: true\b", release, re.MULTILINE)
    assert re.search(r"^\s+fail_on_unmatched_files: true$", release, re.MULTILINE)


def test_jeder_upload_besteht_auf_seinen_dateien():
    alle = jobs(lesen(RELEASE))
    schritte = [s for j in alle.values() for s in aktionsschritte(j, "actions/upload-artifact")]
    assert len(schritte) == 2
    assert all("if-no-files-found: error" in s for s in schritte)


def test_tag_und_version_werden_verglichen():
    exe = jobs(lesen(RELEASE))["windows-exe"]
    assert "(Get-Item \"dist\\LicenseProbe.exe\").VersionInfo" in exe
    assert ('"v$($info.ProductVersion)" -ne $env:GITHUB_REF_NAME') in exe


def test_rauchtest_verlangt_das_echte_fenster():
    exe = jobs(lesen(RELEASE))["windows-exe"]
    assert "-eq 'TkTopLevel'" in exe
    assert 'throw "Die EXE hat ihr Hauptfenster nicht geöffnet."' in exe


def test_schraegstriche_im_ref_namen_werden_ersetzt():
    assert "${GITHUB_REF_NAME//\\//-}" in jobs(lesen(RELEASE))["quellpaket"]


@pytest.mark.parametrize("datei", ["DRITTANBIETER-LIZENZEN.md", "SHA256SUMS.txt",
                                   "LicenseProbe.exe"])
def test_release_haengt_die_datei_an(datei):
    assert f"artefakte/windows-exe/{datei}" in jobs(lesen(RELEASE))["release"]


@pytest.mark.parametrize("datei", ["NOTICE", LIZENZDATEI, "lizenzen", "LICENSE"])
def test_quellpaket_enthaelt_die_lizenzen(datei):
    assert datei in gepackte_dateien()


# --- Dependabot ------------------------------------------------------------

def test_dependabot_laesst_untergrenzen_in_ruhe():
    text = ohne_kommentare(lesen(".github/dependabot.yml"))
    pip, actions = text.split('package-ecosystem: "github-actions"')
    assert 'package-ecosystem: "pip"' in pip
    assert 'versioning-strategy: "increase-if-necessary"' in pip
    assert 'directory: "/"' in pip
    assert 'directory: "/"' in actions


# --- Lizenzen --------------------------------------------------------------

def sprachteile() -> dict[str, str]:
    teile = re.split(r"^## (Deutsch|English)$", lesen(LIZENZDATEI), flags=re.MULTILINE)
    return dict(zip(teile[1::2], teile[2::2], strict=True))


@pytest.mark.parametrize("sprache", ["Deutsch", "English"])
@pytest.mark.parametrize("bestandteil", BESTANDTEILE)
def test_tabellenzeile_je_bestandteil(sprache, bestandteil):
    zeilen = [z for z in sprachteile()[sprache].splitlines()
              if z.startswith(f"| {bestandteil}")]
    assert len(zeilen) == 1, zeilen
    spalten = [s.strip() for s in zeilen[0].strip("|").split("|")]
    assert len(spalten) == 4
    assert all(spalten)
    assert re.fullmatch(r"<https://\S+>", spalten[3])


def test_keine_tabellenzeile_ohne_waechter():
    for teil in sprachteile().values():
        zeilen = [z for z in teil.splitlines()
                  if z.startswith("| ") and "---" not in z
                  and not z.startswith(("| Bestandteil", "| Component"))]
        assert len(zeilen) == len(BESTANDTEILE)


def test_lizenzdatei_nennt_die_gebauten_fassungen():
    """Hebt Dependabot eine Fassung an, muss die Lizenzdatei mitziehen."""
    pyinstaller = re.search(r"^pyinstaller==([\d.]+)$", lesen("requirements-build.txt"),
                            re.MULTILINE).group(1)
    python = re.search(r'python-version: "(\d+\.\d+)\.\d+"',
                       jobs(lesen(RELEASE))["windows-exe"]).group(1)
    text = lesen(LIZENZDATEI)
    assert f"gebaut mit Python {python} und PyInstaller {pyinstaller.rsplit('.', 1)[0]}" in text
    for teil in sprachteile().values():
        assert f"/tree/v{pyinstaller}/bootloader>" in teil


@pytest.mark.parametrize(("datei", "merkmale"), LIZENZTEXTE.items())
def test_lizenztext_liegt_bei(datei, merkmale):
    text = lesen(f"lizenzen/{datei}")
    for merkmal in merkmale:
        assert merkmal in text


@pytest.mark.parametrize("datei", LIZENZTEXTE)
def test_lizenzdatei_nennt_jeden_text_in_beiden_sprachen(datei):
    for teil in sprachteile().values():
        assert f"`{datei}`" in teil


@pytest.mark.parametrize("datei", ["NOTICE", "README.md", "README.en.md", "CONTRIBUTING.md"])
def test_lizenzdatei_ist_verwiesen(datei):
    assert LIZENZDATEI in lesen(datei)


# --- Erst-Start-Hinweis ----------------------------------------------------

@pytest.mark.parametrize(("datei", "merkmale"), [
    ("README.md", ("SmartScreen", "Virenschutz", "SHA-256")),
    ("README.en.md", ("SmartScreen", "Antivirus", "SHA-256")),
])
def test_erst_start_hinweis(datei, merkmale):
    text = lesen(datei)
    for merkmal in merkmale:
        assert merkmal in text


# --- Oberflächentests als Pflicht ------------------------------------------

def test_windows_ci_macht_die_oberflaeche_zur_pflicht():
    tests = jobs(lesen(CI))["tests"]
    assert "OBERFLAECHE_PFLICHT: ${{ matrix.os == 'windows-latest' && '1' || '0' }}" in tests


def test_job_env_nutzt_keinen_runner_kontext():
    """Dort gibt es `runner` noch nicht; GitHub verwirft sonst die ganze Datei still."""
    for job in jobs(lesen(CI)).values():
        kopf = job.split("    steps:")[0]
        assert "runner." not in kopf


@pytest.mark.parametrize(("wert", "erwartet"), [("1", True), ("0", False), (None, False)])
def test_pflicht_kommt_aus_der_umgebung(monkeypatch, wert, erwartet):
    from conftest import oberflaeche_ist_pflicht

    monkeypatch.delenv("OBERFLAECHE_PFLICHT", raising=False)
    if wert is not None:
        monkeypatch.setenv("OBERFLAECHE_PFLICHT", wert)
    assert oberflaeche_ist_pflicht() is erwartet


def test_pflicht_macht_aus_dem_ueberspringen_einen_fehler(monkeypatch):
    from conftest import tk_wurzel_anlegen

    class Kaputt:
        class TclError(Exception):
            pass

        @classmethod
        def Tk(cls):
            raise cls.TclError("keine Anzeige")

    monkeypatch.setattr("time.sleep", lambda dauer: None)
    tk = SimpleNamespace(Tk=Kaputt.Tk, TclError=Kaputt.TclError)
    # BaseException, weil ein durchrutschendes Skip den Test sonst nur überspränge.
    with pytest.raises(BaseException) as ergebnis:  # noqa: B017, PT011
        tk_wurzel_anlegen(tk, pflicht=True)
    assert ergebnis.type is pytest.fail.Exception
    with pytest.raises(BaseException) as ergebnis:  # noqa: B017, PT011
        tk_wurzel_anlegen(tk)
    assert ergebnis.type is pytest.skip.Exception
