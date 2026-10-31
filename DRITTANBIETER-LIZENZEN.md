# Lizenzen der Drittanbieter / Third-party licenses

Stand: LicenseProbe 1.0.1, gebaut mit Python 3.14 und PyInstaller 6.22 /
built with Python 3.14 and PyInstaller 6.22.

## Deutsch

### Gesamtwerk

`LicenseProbe.pyw` steht unter der [MIT-Lizenz](LICENSE). Das Skript braucht
keine fremden Pakete, nur Python mit Tkinter.

Auch die EXE wird als Gesamtwerk unter der MIT-Lizenz weitergegeben. Im Bündel
liegt kein Bestandteil, dessen Lizenz das verhindert: Der Bootloader von
PyInstaller steht zwar unter der GPL, deren Ausnahme erlaubt aber ausdrücklich,
ihn in beliebige Programme einzubetten, ohne dass die GPL für das Programm gilt.
Die Bestandteile unten behalten ihre eigenen Lizenzen.

### Enthaltene Bestandteile

Die Liste entstand aus den Dateien, die tatsächlich in der EXE liegen.

| Bestandteil | Datei in der EXE | Lizenz | Quelle |
|---|---|---|---|
| Python | `python314.dll`, Erweiterungsmodule | PSF-2.0 | <https://github.com/python/cpython> |
| PyInstaller-Bootloader | Startprogramm der EXE | GPL-2.0-or-later mit Bootloader-Ausnahme | <https://github.com/pyinstaller/pyinstaller/tree/v6.22.3/bootloader> |
| OpenSSL | `libcrypto-3.dll`, `libssl-3.dll` | Apache-2.0 | <https://github.com/openssl/openssl> |
| libffi | `libffi-8.dll` | MIT | <https://github.com/libffi/libffi> |
| Tcl/Tk | `tcl90.dll`, `tcl9tk90.dll` | TCL-Lizenz (BSD-artig) | <https://www.tcl-lang.org/software/tcltk/license.html> |
| libtommath | `libtommath.dll` | Unlicense | <https://github.com/libtom/libtommath> |
| zlib | `zlib1.dll` | Zlib | <https://zlib.net/zlib_license.html> |
| bzip2 | in `_bz2.pyd` | bzip2-Lizenz (BSD-artig) | <https://sourceware.org/bzip2/> |
| XZ Utils (liblzma) | in `_lzma.pyd` | 0BSD beziehungsweise gemeinfrei | <https://github.com/tukaani-project/xz> |
| Zstandard | in `_zstd.pyd` | BSD-3-Clause | <https://github.com/facebook/zstd> |
| libmpdec | in `_decimal.pyd` | BSD-2-Clause | <https://www.bytereef.org/mpdecimal/> |
| mimalloc | in `python314.dll` | MIT | <https://github.com/microsoft/mimalloc> |
| Microsoft Visual C++ Runtime und Universal CRT | `VCRUNTIME140.dll`, `ucrtbase.dll`, `api-ms-win-*.dll` | Microsoft-Bedingungen für weitergebbaren Code | <https://learn.microsoft.com/en-us/cpp/windows/determining-which-dlls-to-redistribute> |

Kleinere Teile, die Python selbst enthält, führt dessen eigene Lizenzdatei auf.

### Lizenztexte

Die Texte liegen im Ordner `lizenzen/` und damit auch im Quellpaket jedes
Release:

- `Python-LICENSE.txt`: Python, die Bedingungen für den Microsoft-Code, bzip2,
  libffi, Zstandard, der Text der Apache-2.0-Lizenz für OpenSSL, Tcl und Tk.
- `Python-eingebaute-Bibliotheken.txt`: libmpdec, zlib und mimalloc.
- `PyInstaller-COPYING.txt`: die Lizenz von PyInstaller samt Bootloader-Ausnahme;
  seine zusätzlichen Laufzeitmodule stehen unter Apache-2.0.

### Quellcode der GPL-Bestandteile

Einziger GPL-Bestandteil ist der Bootloader von PyInstaller. Sein Quellcode
steht in der Tabelle; er wurde unverändert übernommen.

### Windows-Systembibliotheken

`KERNEL32.dll`, `USER32.dll`, `ADVAPI32.dll`, `GDI32.dll` und `COMCTL32.dll`
stehen in der EXE nur als Name. Sie gehören zu Windows und werden nicht
mitgeliefert. Dasselbe gilt für die PowerShell, die das Programm aufruft.

### Ohne Fremdbestandteile

Wer nichts Gebündeltes möchte, startet `LicenseProbe.pyw` mit dem eigenen Python.

## English

### The work as a whole

`LicenseProbe.pyw` is under the [MIT License](LICENSE). The script needs no
third-party packages, only Python with Tkinter.

The executable as a whole is also distributed under the MIT License. Nothing in
the bundle prevents that: the PyInstaller bootloader is under the GPL, but its
exception explicitly allows embedding it in any program without the GPL applying
to that program. The components below keep their own licenses.

### Included components

This list was made from the files actually inside the executable.

| Component | File in the executable | License | Source |
|---|---|---|---|
| Python | `python314.dll`, extension modules | PSF-2.0 | <https://github.com/python/cpython> |
| PyInstaller bootloader | startup code of the executable | GPL-2.0-or-later with bootloader exception | <https://github.com/pyinstaller/pyinstaller/tree/v6.22.3/bootloader> |
| OpenSSL | `libcrypto-3.dll`, `libssl-3.dll` | Apache-2.0 | <https://github.com/openssl/openssl> |
| libffi | `libffi-8.dll` | MIT | <https://github.com/libffi/libffi> |
| Tcl/Tk | `tcl90.dll`, `tcl9tk90.dll` | TCL license (BSD-style) | <https://www.tcl-lang.org/software/tcltk/license.html> |
| libtommath | `libtommath.dll` | Unlicense | <https://github.com/libtom/libtommath> |
| zlib | `zlib1.dll` | Zlib | <https://zlib.net/zlib_license.html> |
| bzip2 | in `_bz2.pyd` | bzip2 license (BSD-style) | <https://sourceware.org/bzip2/> |
| XZ Utils (liblzma) | in `_lzma.pyd` | 0BSD or public domain | <https://github.com/tukaani-project/xz> |
| Zstandard | in `_zstd.pyd` | BSD-3-Clause | <https://github.com/facebook/zstd> |
| libmpdec | in `_decimal.pyd` | BSD-2-Clause | <https://www.bytereef.org/mpdecimal/> |
| mimalloc | in `python314.dll` | MIT | <https://github.com/microsoft/mimalloc> |
| Microsoft Visual C++ Runtime and Universal CRT | `VCRUNTIME140.dll`, `ucrtbase.dll`, `api-ms-win-*.dll` | Microsoft terms for distributable code | <https://learn.microsoft.com/en-us/cpp/windows/determining-which-dlls-to-redistribute> |

Smaller parts contained in Python itself are listed in its own license file.

### License texts

The texts are in the folder `lizenzen/` and therefore also in the source package
of every release:

- `Python-LICENSE.txt`: Python, the terms for the Microsoft code, bzip2, libffi,
  Zstandard, the Apache-2.0 text for OpenSSL, Tcl and Tk.
- `Python-eingebaute-Bibliotheken.txt`: libmpdec, zlib and mimalloc.
- `PyInstaller-COPYING.txt`: the PyInstaller license with its bootloader exception;
  its additional run-time modules are under Apache-2.0.

### Source code of the GPL components

The only GPL component is the PyInstaller bootloader. Its source is linked in the
table; it is used unchanged.

### Windows system libraries

`KERNEL32.dll`, `USER32.dll`, `ADVAPI32.dll`, `GDI32.dll` and `COMCTL32.dll`
appear in the executable by name only. They belong to Windows and are not
shipped. The same goes for PowerShell, which the program calls.

### Without third-party components

If you want nothing bundled, run `LicenseProbe.pyw` with your own Python.
