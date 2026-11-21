#!/usr/bin/env python3
"""Sum up 21 November 2026's world news in one image.

Pure Python 3 standard library: draws a newspaper-style front page
(1024x1024 PNG) with a tiny 5x7 bitmap font and writes it to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png).
Deterministic: no clock, no randomness, no network, no files read.
"""

import os
import struct
import zlib

W = 1024
H = 1024

# ---------------------------------------------------------------- palette
CREAM = (247, 242, 231)
PAPER = (255, 253, 247)
INK = (18, 22, 30)
RED = (178, 34, 44)
BLUE = (24, 62, 122)
GOLD = (176, 128, 20)
GREEN = (22, 102, 66)
TEAL = (10, 110, 120)
GREY = (92, 96, 104)
LIGHT = (232, 224, 205)

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 bits, written as strings so they stay readable.
_FONT_SRC = {
    "A": "01110 10001 10001 11111 10001 10001 10001",
    "B": "11110 10001 10001 11110 10001 10001 11110",
    "C": "01110 10001 10000 10000 10000 10001 01110",
    "D": "11100 10010 10001 10001 10001 10010 11100",
    "E": "11111 10000 10000 11110 10000 10000 11111",
    "F": "11111 10000 10000 11110 10000 10000 10000",
    "G": "01110 10001 10000 10111 10001 10001 01111",
    "H": "10001 10001 10001 11111 10001 10001 10001",
    "I": "01110 00100 00100 00100 00100 00100 01110",
    "J": "00111 00010 00010 00010 00010 10010 01100",
    "K": "10001 10010 10100 11000 10100 10010 10001",
    "L": "10000 10000 10000 10000 10000 10000 11111",
    "M": "10001 11011 10101 10101 10001 10001 10001",
    "N": "10001 10001 11001 10101 10011 10001 10001",
    "O": "01110 10001 10001 10001 10001 10001 01110",
    "P": "11110 10001 10001 11110 10000 10000 10000",
    "Q": "01110 10001 10001 10001 10101 10010 01101",
    "R": "11110 10001 10001 11110 10100 10010 10001",
    "S": "01111 10000 10000 01110 00001 00001 11110",
    "T": "11111 00100 00100 00100 00100 00100 00100",
    "U": "10001 10001 10001 10001 10001 10001 01110",
    "V": "10001 10001 10001 10001 10001 01010 00100",
    "W": "10001 10001 10001 10101 10101 10101 01010",
    "X": "10001 01010 00100 00100 00100 01010 10001",
    "Y": "10001 01010 00100 00100 00100 00100 00100",
    "Z": "11111 00001 00010 00100 01000 10000 11111",
    "0": "01110 10001 10011 10101 11001 10001 01110",
    "1": "00100 01100 00100 00100 00100 00100 01110",
    "2": "01110 10001 00001 00010 00100 01000 11111",
    "3": "11111 00010 00100 00010 00001 10001 01110",
    "4": "00010 00110 01010 10010 11111 00010 00010",
    "5": "11111 10000 11110 00001 00001 10001 01110",
    "6": "00110 01000 10000 11110 10001 10001 01110",
    "7": "11111 00001 00010 00100 01000 01000 01000",
    "8": "01110 10001 10001 01110 10001 10001 01110",
    "9": "01110 10001 10001 01111 00001 00010 01100",
    " ": "00000 00000 00000 00000 00000 00000 00000",
    ".": "00000 00000 00000 00000 00000 01100 01100",
    ",": "00000 00000 00000 00000 01100 00100 01000",
    "'": "00100 00100 01000 00000 00000 00000 00000",
    "-": "00000 00000 00000 01110 00000 00000 00000",
    "$": "00100 01111 10100 01110 00101 11110 00100",
    "%": "11001 11010 00010 00100 01000 01011 10011",
    "+": "00000 00100 00100 01110 00100 00100 00000",
    ":": "00000 01100 01100 00000 01100 01100 00000",
    "/": "00001 00010 00010 00100 01000 01000 10000",
    "(": "00010 00100 01000 01000 01000 00100 00010",
    ")": "01000 00100 00010 00010 00010 00100 01000",
    "!": "00100 00100 00100 00100 00100 00000 00100",
    "?": "01110 10001 00001 00110 00100 00000 00100",
    "&": "01100 10010 10100 01000 10101 10010 01101",
}

FONT = {}
for _ch, _rows in _FONT_SRC.items():
    FONT[_ch] = [int(r, 2) for r in _rows.split()]


def text_width(text, scale):
    """Pixel width of a string at the given integer scale."""
    return len(text) * 6 * scale - scale


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def frame(self, x, y, w, h, color, t=3):
        self.rect(x, y, w, t, color)
        self.rect(x, y + h - t, w, t, color)
        self.rect(x, y, t, h, color)
        self.rect(x + w - t, y, t, h, color)

    def circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, color)

    def ring(self, cx, cy, r, color, t=4):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - t) ** 2 < d <= r * r:
                    self.set(xx, yy, color)

    def line(self, x0, y0, x1, y1, color, t=3):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(steps + 1):
            x = x0 + (x1 - x0) * i // steps
            y = y0 + (y1 - y0) * i // steps
            self.rect(x - t // 2, y - t // 2, t, t, color)

    def text(self, x, y, text, scale, color):
        """Draw text with the 5x7 font; returns the x after the text."""
        cx = x
        for ch in text.upper():
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits & (1 << (4 - col)):
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx

    def text_center(self, cx, y, text, scale, color):
        x = cx - text_width(text, scale) // 2
        self.text(x, y, text, scale, color)

    def text_wrap(self, x, y, text, scale, color, max_px, line_gap=4):
        """Word-wrap text to max_px width; returns y after the last line."""
        words = text.upper().split()
        lines = []
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if text_width(trial, scale) <= max_px:
                cur = trial
            else:
                lines.append(cur)
                cur = word
        if cur:
            lines.append(cur)
        for ln in lines:
            self.text(x, y, ln, scale, color)
            y += 7 * scale + line_gap
        return y


# ---------------------------------------------------------------- icons
def icon_summit(c, x, y):
    """Three overlapping rings: three leaders at one table."""
    c.ring(x + 22, y + 26, 17, RED, 5)
    c.ring(x + 46, y + 26, 17, GOLD, 5)
    c.ring(x + 34, y + 44, 17, BLUE, 5)


def icon_chart(c, x, y):
    """Rising bars and an arrow: a record listing."""
    base = y + 52
    for i, hgt in enumerate((14, 24, 34, 46)):
        c.rect(x + 4 + i * 15, base - hgt, 10, hgt, GREEN)
    c.line(x + 4, base - 18, x + 58, base - 52, RED, 4)
    c.line(x + 44, base - 54, x + 60, base - 54, RED, 4)
    c.line(x + 60, base - 54, x + 60, base - 38, RED, 4)


def icon_bank(c, x, y):
    """Columns and a pediment: a central bank."""
    c.line(x + 4, y + 18, x + 32, y + 2, BLUE, 4)
    c.line(x + 32, y + 2, x + 60, y + 18, BLUE, 4)
    c.rect(x + 2, y + 20, 60, 5, BLUE)
    for i in range(4):
        c.rect(x + 7 + i * 14, y + 29, 7, 24, BLUE)
    c.rect(x + 2, y + 55, 60, 5, BLUE)


def icon_scales(c, x, y):
    """Scales of justice for the court story."""
    cx = x + 32
    c.rect(cx - 2, y + 8, 4, 40, INK)
    c.rect(x + 8, y + 12, 48, 4, INK)
    for sx in (x + 12, x + 44):
        c.line(sx, y + 16, sx + 8, y + 34, INK, 3)
        c.line(sx + 16, y + 16, sx + 8, y + 34, INK, 3)
        c.line(sx, y + 36, sx + 16, y + 36, INK, 4)
    c.rect(x + 18, y + 50, 28, 5, INK)
    c.circle(cx, y + 6, 5, INK)


def icon_tank(c, x, y):
    """A simple tank silhouette."""
    c.rect(x + 8, y + 34, 50, 12, (70, 74, 60))
    c.rect(x + 22, y + 24, 24, 11, (70, 74, 60))
    c.rect(x + 44, y + 27, 20, 4, (70, 74, 60))
    for i in range(4):
        c.circle(x + 15 + i * 12, y + 48, 5, INK)
    c.rect(x + 4, y + 44, 58, 4, INK)


def icon_flags(c, x, y):
    """Two flags: a trade deal between two sides."""
    c.rect(x + 6, y + 6, 3, 50, INK)
    c.rect(x + 9, y + 6, 24, 16, BLUE)
    c.circle(x + 21, y + 14, 4, GOLD)
    c.rect(x + 38, y + 6, 3, 50, INK)
    c.rect(x + 41, y + 6, 24, 8, RED)
    c.rect(x + 41, y + 14, 24, 8, PAPER)


def icon_gold(c, x, y):
    """Gold bars and a falling arrow."""
    c.rect(x + 20, y + 8, 24, 9, GOLD)
    c.rect(x + 10, y + 20, 24, 9, GOLD)
    c.rect(x + 36, y + 20, 24, 9, GOLD)
    c.line(x + 6, y + 36, x + 56, y + 54, RED, 4)
    c.line(x + 42, y + 56, x + 58, y + 56, RED, 4)
    c.line(x + 58, y + 56, x + 58, y + 40, RED, 4)


def icon_fall(c, x, y):
    """Falling bars and a down arrow: a market rout."""
    base = y + 52
    for i, hgt in enumerate((46, 34, 24, 14)):
        c.rect(x + 4 + i * 15, base - hgt, 10, hgt, RED)
    c.line(x + 4, base - 50, x + 58, base - 16, RED, 4)
    c.line(x + 44, base - 14, x + 60, base - 14, RED, 4)
    c.line(x + 60, base - 14, x + 60, base - 30, RED, 4)


def icon_chip(c, x, y):
    """A chip with pins: export controls on semiconductors."""
    c.rect(x + 14, y + 14, 36, 36, BLUE)
    c.rect(x + 24, y + 24, 16, 16, PAPER)
    for i in range(4):
        c.rect(x + 18 + i * 9, y + 6, 4, 8, BLUE)
        c.rect(x + 18 + i * 9, y + 50, 4, 8, BLUE)
        c.rect(x + 6, y + 18 + i * 9, 8, 4, BLUE)
        c.rect(x + 50, y + 18 + i * 9, 8, 4, BLUE)
    c.line(x + 8, y + 8, x + 56, y + 56, RED, 4)


def icon_cloud(c, x, y):
    """A cloud: cloud computing earnings."""
    c.circle(x + 24, y + 30, 13, TEAL)
    c.circle(x + 40, y + 26, 15, TEAL)
    c.rect(x + 12, y + 30, 42, 14, TEAL)
    c.line(x + 20, y + 50, x + 46, y + 50, GOLD, 4)
    c.line(x + 20, y + 56, x + 46, y + 56, GOLD, 4)


def icon_bridge(c, x, y):
    """A bridge with a broken span: the Crimea bridge strike."""
    c.rect(x + 8, y + 44, 20, 5, INK)
    c.rect(x + 36, y + 44, 20, 5, INK)
    c.rect(x + 12, y + 18, 4, 26, INK)
    c.rect(x + 48, y + 18, 4, 26, INK)
    c.line(x + 14, y + 18, x + 28, y + 40, INK, 3)
    c.line(x + 50, y + 18, x + 36, y + 40, INK, 3)
    cx, cy = x + 32, y + 34
    c.circle(cx, cy, 6, RED)
    for dx, dy in ((-10, -8), (0, -12), (10, -8), (-12, 0),
                   (12, 0), (-10, 8), (0, 12), (10, 8)):
        c.line(cx, cy, cx + dx, cy + dy, RED, 3)


# ---------------------------------------------------------------- content
LEAD = {
    "kicker": "MARKETS - NEW YORK",
    "color": RED,
    "headline": "NASDAQ ERASES 2026 GAINS",
    "sub": ("S&P -3.70% TO 6,910.39; DOW -949.73 TO 48,147.33; "
            "BOTH NOW IN CORRECTION."),
    "icon": icon_fall,
}

STORIES = [
    {
        "kicker": "MARKETS - ASIA",
        "color": RED,
        "headline": "ASIA ROUT DEEPENS",
        "sub": ("TAIEX -6.23%, NIKKEI -5.06%, KOSPI -5.21%; TAIEX "
                "WORST WEEK SINCE 1991."),
        "icon": icon_fall,
    },
    {
        "kicker": "TECH - CHIPS",
        "color": BLUE,
        "headline": "NVIDIA SINKS 14% ON SEC PROBE",
        "sub": ("SEC PROBES ITS ACCOUNTING; AMD -13.25%, MICRON "
                "-13.89% IN CHIP ROUT."),
        "icon": icon_chip,
    },
    {
        "kicker": "TECH - IPO",
        "color": TEAL,
        "headline": "ANTHROPIC SLIDES 8.5%",
        "sub": ("SECOND DAY DOWN, BACK NEAR ITS $83 IPO PRICE; "
                "OVER $160B OF VALUE WIPED."),
        "icon": icon_cloud,
    },
    {
        "kicker": "MARKETS - GLOBAL",
        "color": GOLD,
        "headline": "GOLD SLUMPS TO $3,514",
        "sub": ("SPOT GOLD -3% TO A 14-MONTH LOW; SILVER -7.41% AS "
                "RATE FEARS LIFT DOLLAR."),
        "icon": icon_gold,
    },
    {
        "kicker": "WAR - EUROPE",
        "color": INK,
        "headline": "MISSILES LAND IN POLAND",
        "sub": ("TWO MISSILES AND A DRONE LAND; NO INJURIES. TUSK "
                "CALLS IT PROVOCATION."),
        "icon": icon_tank,
    },
    {
        "kicker": "CLIMATE - TURKEY",
        "color": GREEN,
        "headline": "COP31 TALKS IN OVERTIME",
        "sub": ("ANTALYA TALKS PASS DEADLINE AS DRAFTS DROP "
                "FOSSIL-FUEL PHASE-OUT WORDS."),
        "icon": icon_summit,
    },
]

TICKER = ("ALSO: VIX +25% TO 35.69 - BITCOIN LOW $55,326 - "
          "EU-INDONESIA DEAL - TRUMP DATA-CENTER TAX THREAT - "
          "EU-UK PACT - KRYVYI RIH 2 DEAD - BAYER $7.25B DEAL")


# ---------------------------------------------------------------- drawing
def draw_panel(c, x, y, w, h, story, headline_scale=3):
    c.rect(x, y, w, h, PAPER)
    c.frame(x, y, w, h, INK, 3)
    c.rect(x, y, w, 8, story["color"])
    tx = x + 18
    tw = w - 36 - 76  # leave room for the icon at the right
    ky = y + 18
    c.text(tx, ky, story["kicker"], 2, story["color"])
    hy = ky + 20
    hy = c.text_wrap(tx, hy, story["headline"], headline_scale, INK,
                     tw, line_gap=5)
    c.text_wrap(tx, hy + 4, story["sub"], 2, GREY, tw, line_gap=4)
    story["icon"](c, x + w - 84, y + h - 76)


def draw():
    c = Canvas(W, H, CREAM)

    # masthead
    c.text_center(W // 2, 28, "THE WORLD IN ONE IMAGE", 4, RED)
    c.rect(36, 74, W - 72, 4, INK)
    c.text_center(W // 2, 84, "SATURDAY", 9, INK)
    c.text_center(W // 2, 156, "21 NOVEMBER 2026", 8, INK)
    c.rect(36, 222, W - 72, 4, INK)
    c.text_center(W // 2, 230, "ALL THE NEWS OF ONE DAY, AS IT HAPPENED",
                  2, GREY)

    # lead story
    draw_panel(c, 36, 256, W - 72, 150, LEAD)

    # grid of six
    gx, gy = 36, 418
    gw, gh, gap = (W - 72 - 10) // 2, 156, 10
    for i, story in enumerate(STORIES):
        px = gx + (i % 2) * (gw + gap)
        py = gy + (i // 2) * (gh + gap)
        draw_panel(c, px, py, gw, gh, story)

    # ticker band
    ty = gy + 3 * gh + 2 * gap + 12
    c.rect(36, ty, W - 72, 54, INK)
    c.text_wrap(54, ty + 10, TICKER, 2, CREAM, W - 108, line_gap=4)

    # footer
    c.text_center(W // 2, ty + 66, "SUMMED UP IN ONE IMAGE - 21.11.2026",
                  2, GREY)
    return c


# ---------------------------------------------------------------- png out
def png_bytes(canvas):
    raw = bytearray()
    row_bytes = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        start = y * row_bytes
        raw += canvas.px[start:start + row_bytes]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(out_dir, exist_ok=True)
    data = png_bytes(draw())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as fh:
        fh.write(data)
    print("wrote", path, len(data), "bytes")


if __name__ == "__main__":
    main()
