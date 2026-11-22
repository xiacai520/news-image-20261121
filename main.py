#!/usr/bin/env python3
"""news-image-20261121: draw one newspaper front page for 21 Nov 2026.

Pure Python 3 standard library.  The page is painted pixel by pixel
into an RGB buffer with a hand-made 5x7 bitmap typeface, then written
out as a PNG with zlib + struct.  No network, no inputs, no clock:
every run produces the same bytes.

Run:  python3 main.py          (writes /output/entry.png)
      MAKEFUN_OUTPUT_DIR=out python3 main.py   (writes out/entry.png)
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

PAPER = (246, 241, 230)
INK = (23, 26, 36)
RED = (176, 32, 40)
NAVY = (26, 58, 110)
TEAL = (0, 108, 108)
GOLD = (172, 118, 16)
GREEN = (22, 106, 58)
DARK = (52, 54, 60)
WHITE = (250, 248, 242)

# 5x7 typeface.  Each glyph is seven rows of five bits, "1" = ink.
GLYPHS = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01110"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00001", "00001", "00001", "00001", "10001", "01110"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "01010", "00100", "00100", "00100", "01010", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "01100", "01000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "/": ("00001", "00001", "00010", "00100", "01000", "10000", "10000"),
    "'": ("01100", "01100", "01000", "00000", "00000", "00000", "00000"),
    "(": ("00011", "00100", "01000", "01000", "01000", "00100", "00011"),
    ")": ("11000", "00100", "00010", "00010", "00010", "00100", "11000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
}


class Page:
    """An RGB pixel buffer with drawing and text helpers."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(bg) * (w * h)

    def put(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.buf[i:i + len(row)] = row

    def frame(self, x, y, w, h, color, t):
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    def seg(self, x0, y0, x1, y1, color, t=2):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        half = t // 2
        while True:
            self.rect(x0 - half, y0 - half, t, t, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int(math.sqrt(r * r - dy * dy))
            self.rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def ring(self, cx, cy, r, color, t=4):
        steps = max(24, 6 * r)
        half = t // 2
        for i in range(steps + 1):
            a = 2.0 * math.pi * i / steps
            x = int(round(cx + r * math.cos(a)))
            y = int(round(cy + r * math.sin(a)))
            self.rect(x - half, y - half, t, t, color)

    def measure(self, s, scale, track=0):
        if not s:
            return 0
        return len(s) * (6 * scale + track) - track

    def text(self, x, y, s, scale, color, track=0):
        cx = x
        for ch in s.upper():
            glyph = GLYPHS.get(ch, GLYPHS[" "])
            for gy, bits in enumerate(glyph):
                for gx, bit in enumerate(bits):
                    if bit == "1":
                        self.rect(cx + gx * scale, y + gy * scale,
                                  scale, scale, color)
            cx += 6 * scale + track
        return cx - track - x

    def centred(self, y, s, scale, color, track=0):
        x = (self.w - self.measure(s, scale, track)) // 2
        self.text(x, y, s, scale, color, track)

    def wrap(self, s, maxw, scale, track=0):
        lines = []
        cur = ""
        for word in s.split():
            trial = word if not cur else cur + " " + word
            if cur and self.measure(trial, scale, track) > maxw:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        if cur:
            lines.append(cur)
        return lines


def png_bytes(page):
    def chunk(tag, data):
        body = tag + data
        return (struct.pack(">I", len(data)) + body
                + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))

    raw = bytearray()
    stride = page.w * 3
    for yy in range(page.h):
        raw.append(0)
        raw += page.buf[yy * stride:(yy + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", page.w, page.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


# --- pictograms, each drawn inside an 84x84 box at (x, y) ---

def icon_crash(p, x, y, color):
    p.seg(x + 8, y + 8, x + 8, y + 70, INK, 3)
    p.seg(x + 8, y + 70, x + 78, y + 70, INK, 3)
    pts = [(12, 16), (26, 30), (38, 24), (52, 44), (63, 38), (76, 60)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        p.seg(x + ax, y + ay, x + bx, y + by, color, 5)
    p.seg(x + 76, y + 60, x + 62, y + 58, color, 5)
    p.seg(x + 76, y + 60, x + 74, y + 46, color, 5)


def icon_chip(p, x, y):
    p.frame(x + 18, y + 18, 48, 48, INK, 4)
    p.frame(x + 33, y + 33, 18, 18, INK, 3)
    for i in range(3):
        o = 26 + 16 * i
        p.seg(x + o, y + 6, x + o, y + 18, INK, 4)
        p.seg(x + o, y + 66, x + o, y + 78, INK, 4)
        p.seg(x + 6, y + o, x + 18, y + o, INK, 4)
        p.seg(x + 66, y + o, x + 78, y + o, INK, 4)
    p.seg(x + 12, y + 72, x + 72, y + 12, RED, 6)


def icon_cloud(p, x, y):
    p.disc(x + 28, y + 50, 14, TEAL)
    p.disc(x + 46, y + 40, 19, TEAL)
    p.disc(x + 63, y + 50, 13, TEAL)
    p.rect(x + 14, y + 50, 62, 14, TEAL)
    p.rect(x + 22, y + 72, 44, 5, GOLD)
    p.rect(x + 30, y + 80, 28, 5, GOLD)


def icon_gold(p, x, y):
    p.frame(x + 13, y + 54, 27, 15, INK, 3)
    p.rect(x + 16, y + 57, 21, 9, GOLD)
    p.frame(x + 44, y + 54, 27, 15, INK, 3)
    p.rect(x + 47, y + 57, 21, 9, GOLD)
    p.frame(x + 28, y + 37, 27, 15, INK, 3)
    p.rect(x + 31, y + 40, 21, 9, GOLD)
    p.seg(x + 16, y + 10, x + 56, y + 24, RED, 5)
    p.seg(x + 56, y + 24, x + 42, y + 24, RED, 5)
    p.seg(x + 56, y + 24, x + 54, y + 10, RED, 5)


def icon_tank(p, x, y):
    p.rect(x + 8, y + 56, 68, 13, DARK)
    for cx in (20, 42, 64):
        p.disc(x + cx, y + 62, 5, PAPER)
    p.rect(x + 14, y + 42, 56, 14, DARK)
    p.rect(x + 30, y + 30, 26, 12, DARK)
    p.seg(x + 56, y + 34, x + 81, y + 34, DARK, 5)
    p.seg(x + 36, y + 30, x + 36, y + 22, DARK, 4)


def icon_rings(p, x, y):
    p.ring(x + 27, y + 40, 16, GOLD, 5)
    p.ring(x + 55, y + 40, 16, NAVY, 5)
    p.ring(x + 41, y + 56, 16, RED, 5)


ICONS = {
    "crash_red": lambda p, x, y: icon_crash(p, x, y, RED),
    "chip": icon_chip,
    "cloud": icon_cloud,
    "gold": icon_gold,
    "tank": icon_tank,
    "rings": icon_rings,
}


def panel(p, x, y, w, h, tint, kicker, headline, body, icon,
          head_scale=4, body_scale=2, head_track=-2):
    p.frame(x, y, w, h, INK, 3)
    p.rect(x, y, w, 7, tint)
    p.text(x + 14, y + 14, kicker, 3, tint)
    textw = w - 28 - (84 if icon else 0)
    lines = p.wrap(headline, textw, head_scale, head_track)
    ly = y + 39
    for ln in lines:
        p.text(x + 14, ly, ln, head_scale, INK, head_track)
        ly += head_scale * 7 + 2
    by = ly + 2
    for ln in p.wrap(body, textw, body_scale):
        p.text(x + 14, by, ln, body_scale, INK)
        by += body_scale * 7 + 2
    if icon:
        ICONS[icon](p, x + w - 96, y + 44)


def build():
    p = Page(W, H, PAPER)
    mx = 28
    cw = W - 2 * mx

    # masthead
    p.centred(22, "THE WORLD IN ONE IMAGE", 5, RED)
    p.rect(mx, 66, cw, 4, INK)
    p.centred(76, "SATURDAY", 10, INK)
    p.centred(152, "21 NOVEMBER 2026", 8, INK)
    p.rect(mx, 216, cw, 3, INK)
    p.centred(226, "ALL THE NEWS OF ONE DAY, AS IT HAPPENED", 3, DARK)

    # lead story
    panel(p, mx, 258, cw, 150, RED,
          "MARKETS - NEW YORK",
          "NASDAQ ERASES 2026 GAINS",
          "S&P -3.70% TO 6,910.39  DOW -949.73 TO 48,147.33  "
          "BOTH NOW IN CORRECTION.",
          "crash_red", head_scale=5, body_scale=3, head_track=0)

    # two-column rows
    colw = (cw - 12) // 2
    rows = [
        (("MARKETS - ASIA", RED, "ASIA ROUT DEEPENS",
          "TAIEX -6.23%, NIKKEI -5.06%, KOSPI -5.21%.  "
          "TAIEX WORST WEEK SINCE 1991.", "crash_red"),
         ("TECH - CHIPS", NAVY, "NVIDIA SINKS 14% ON SEC PROBE",
          "SEC PROBES ITS ACCOUNTING.  AMD -13.25%, "
          "MICRON -13.89% IN CHIP ROUT.", "chip")),
        (("TECH - IPO", TEAL, "ANTHROPIC SLIDES 8.5%",
          "SECOND DAY DOWN, BACK NEAR ITS $83 IPO PRICE.  "
          "OVER $160B OF VALUE WIPED.", "cloud"),
         ("MARKETS - GLOBAL", GOLD, "GOLD SLUMPS TO $3,514",
          "SPOT GOLD -3% TO A 14-MONTH LOW.  SILVER -7.41% "
          "AS RATE FEARS LIFT DOLLAR.", "gold")),
        (("WAR - EUROPE", DARK, "MISSILES LAND IN POLAND",
          "TWO MISSILES AND A DRONE LAND.  NO INJURIES.  "
          "TUSK CALLS IT PROVOCATION.", "tank"),
         ("CLIMATE - TURKEY", GREEN, "COP31 TALKS IN OVERTIME",
          "ANTALYA TALKS PASS DEADLINE AS DRAFTS DROP "
          "FOSSIL-FUEL PHASE-OUT WORDS.", "rings")),
    ]
    ry = 420
    for left, right in rows:
        panel(p, mx, ry, colw, 156, left[1], left[0], left[2], left[3],
              left[4])
        panel(p, mx + colw + 12, ry, colw, 156, right[1], right[0],
              right[2], right[3], right[4])
        ry += 168

    # ticker
    p.rect(mx, ry + 4, cw, 48, INK)
    p.text(mx + 14, ry + 12,
           "ALSO: VIX +25% TO 35.69 - BITCOIN LOW $55,326 - "
           "EU-INDONESIA DEAL - TRUMP", 2, WHITE)
    p.text(mx + 14, ry + 30,
           "DATA-CENTER TAX THREAT - EU-UK PACT - KRYVYI RIH "
           "2 DEAD - BAYER $7.25B DEAL", 2, WHITE)

    # footer
    p.centred(ry + 66, "SUMMED UP IN ONE IMAGE - 21.11.2026", 3, DARK)
    return p


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(png_bytes(build()))
    print("wrote", path)


if __name__ == "__main__":
    main()
