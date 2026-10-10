"""Erzeugt das Programmsymbol licenseprobe.ico.

Gezeichnet wird ein Schluessel in Weiss auf einer abgerundeten Flaeche im
Akzentblau des Farbschemas.

Aufruf:  python icon_erzeugen.py
Benoetigt:  pip install Pillow
"""

import os

from PIL import Image, ImageDraw

ZIEL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "licenseprobe.ico")
KANTE = 1024                                  # Vorlage, wird heruntergerechnet
GROESSEN = [16, 24, 32, 48, 64, 128, 256]

BLAU = (47, 125, 225, 255)                    # ACCENT des hellen Schemas
WEISS = (255, 255, 255, 255)


def zeichnen() -> Image.Image:
    bild = Image.new("RGBA", (KANTE, KANTE), (0, 0, 0, 0))
    stift = ImageDraw.Draw(bild)

    rand = KANTE // 16
    stift.rounded_rectangle((rand, rand, KANTE - rand, KANTE - rand),
                            radius=KANTE // 5, fill=BLAU)

    # Reide: Ring links, Mittelloch als Aussparung
    mitte_y = KANTE // 2 - KANTE // 20
    links = int(KANTE * 0.22)
    r = int(KANTE * 0.15)
    kopf_x = links + r
    stift.ellipse((links, mitte_y - r, links + 2 * r, mitte_y + r), fill=WEISS)
    loch = r // 2
    stift.ellipse((kopf_x - loch, mitte_y - loch, kopf_x + loch, mitte_y + loch), fill=BLAU)

    # Halm nach rechts
    dicke = KANTE // 11
    rechts = int(KANTE * 0.78)
    stift.rectangle((kopf_x + r - KANTE // 40, mitte_y - dicke // 2, rechts, mitte_y + dicke // 2),
                    fill=WEISS)

    # Bart: zwei Zaehne nach unten
    zahn = KANTE // 12
    for x, laenge in ((rechts - zahn, KANTE // 7), (rechts - 3 * zahn, KANTE // 10)):
        stift.rectangle((x, mitte_y, x + zahn, mitte_y + dicke // 2 + laenge), fill=WEISS)
    return bild


def main() -> None:
    vorlage = zeichnen()
    vorlage.save(ZIEL, sizes=[(n, n) for n in GROESSEN])
    print("geschrieben:", ZIEL)


if __name__ == "__main__":
    main()
