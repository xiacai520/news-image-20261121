#!/usr/bin/env python3
"""news-image-20261121: one image summing up the world news of
Saturday 21 November 2026, drawn as a newspaper front page.

Pure Python 3 standard library only: an RGB canvas, a hand-built
stroke typeface (every glyph is a set of polylines on a 5x7 grid,
drawn with Bresenham lines), simple charts and pictograms, and a
small PNG writer (zlib + struct). No files are read, no network,
no clock, no randomness, so every run writes byte-identical output.

Stories, all as reported on 21 November 2026:
  * Anthropic's IPO: $81.3B raised at $83 a share, valuation past
    $2T on debut -- the largest IPO on record, topping SpaceX.
  * Taiwan stocks: TAIEX lost 7,642 points (-17.5%) in a week, the
    worst weekly fall in 35 years; Friday alone fell 2,394 to 36,033.
  * APEC in Shenzhen: Trump and Xi met for a third time, agreed to
    work together on AI safety rules; a US-China-Russia summit
    issued a peace declaration.
  * Taiwan's legislature passed a NT$20,000 cash handout, 50-46.
  * Ticker: ICJ finds Myanmar guilty of Rohingya genocide; a
    Russian missile hit a Kyiv bridge, 3 dead; European youth
    marched against war and living costs.

Run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import hashlib
import os
import struct
import sys
import zlib

SIZE = 1024

# --- palette: newsprint paper, ink, one red and one blue accent ---
PAPER = (247, 243, 234)
INK = (22, 22, 22)
RED = (178, 38, 30)
BLUE = (29, 78, 137)
GREY = (110, 105, 94)
FAINT = (196, 190, 176)
DARK = (30, 30, 32)
WHITE = (250, 248, 243)

# --- stroke typeface -------------------------------------------------------
# Each glyph is a tuple of strokes; a stroke is a tuple of (x, y) points on
# a 5-wide by 7-tall grid (y grows downwards). Single-point strokes draw
# a dot. Space is an empty tuple. Anything unknown renders as a box.
FONT = {
    "A": (((0, 6), (2, 0), (4, 6)), ((1, 4), (3, 4))),
    "B": (((0, 0), (0, 6)), ((0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)),
          ((0, 3), (3, 3), (4, 4), (4, 5), (3, 6), (0, 6))),
    "C": (((4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5)),),
    "D": (((0, 0), (0, 6)), ((0, 0), (3, 0), (4, 1), (4, 5), (3, 6), (0, 6))),
    "E": (((0, 0), (0, 6)), ((0, 0), (4, 0)), ((0, 3), (3, 3)), ((0, 6), (4, 6))),
    "F": (((0, 0), (0, 6)), ((0, 0), (4, 0)), ((0, 3), (3, 3))),
    "G": (((4, 1), (3, 0), (1, 0), (0, 1), (0, 5), (1, 6), (3, 6), (4, 5),
           (4, 3), (2, 3)),),
    "H": (((0, 0), (0, 6)), ((4, 0), (4, 6)), ((0, 3), (4, 3))),
    "I": (((2, 0), (2, 6)), ((1, 0), (3, 0)), ((1, 6), (3, 6))),
    "J": (((4, 0), (4, 5), (3, 6), (1, 6), (0, 5)),),
    "K": (((0, 0), (0, 6)), ((4, 0), (0, 3), (4, 6))),
    "L": (((0, 0), (0, 6)), ((0, 6), (4, 6))),
    "M": (((0, 6), (0, 0), (2, 3), (4, 0), (4, 6)),),
    "N": (((0, 6), (0, 0), (4, 6), (4, 0)),),
    "O": (((1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1),
           (1, 0)),),
    "P": (((0, 0), (0, 6)), ((0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3))),
    "Q": (((1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1),
           (1, 0)), ((3, 4), (4, 6))),
    "R": (((0, 0), (0, 6)), ((0, 0), (3, 0), (4, 1), (4, 2), (3, 3), (0, 3)),
          ((2, 3), (4, 6))),
    "S": (((4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (3, 3), (4, 4),
           (4, 5), (3, 6), (1, 6), (0, 5)),),
    "T": (((0, 0), (4, 0)), ((2, 0), (2, 6))),
    "U": (((0, 0), (0, 5), (1, 6), (3, 6), (4, 5), (4, 0)),),
    "V": (((0, 0), (2, 6), (4, 0)),),
    "W": (((0, 0), (1, 6), (2, 3), (3, 6), (4, 0)),),
    "X": (((0, 0), (4, 6)), ((4, 0), (0, 6))),
    "Y": (((0, 0), (2, 3), (4, 0)), ((2, 3), (2, 6))),
    "Z": (((0, 0), (4, 0), (0, 6), (4, 6)),),
    "0": (((1, 0), (3, 0), (4, 1), (4, 5), (3, 6), (1, 6), (0, 5), (0, 1),
           (1, 0)), ((1, 5), (3, 1))),
    "1": (((1, 1), (2, 0), (2, 6)), ((0, 6), (4, 6))),
    "2": (((0, 1), (1, 0), (3, 0), (4, 1), (4, 3), (0, 6), (4, 6)),),
    "3": (((0, 0), (4, 0)), ((4, 0), (4, 2)), ((1, 3), (4, 3)),
          ((4, 3), (4, 6)), ((0, 6), (4, 6))),
    "4": (((0, 0), (0, 3), (4, 3)), ((3, 0), (3, 6))),
    "5": (((4, 0), (0, 0), (0, 3), (3, 3), (4, 4), (4, 5), (3, 6), (0, 6)),),
    "6": (((3, 0), (1, 0), (0, 2), (0, 5), (1, 6), (3, 6), (4, 5), (4, 3),
           (3, 2), (1, 2)),),
    "7": (((0, 0), (4, 0)), ((4, 0), (1, 6))),
    "8": (((1, 0), (3, 0), (4, 1), (4, 2), (3, 3), (1, 3), (0, 2), (0, 1),
           (1, 0)),
          ((1, 3), (3, 3), (4, 4), (4, 5), (3, 6), (1, 6), (0, 5), (0, 4),
           (1, 3))),
    "9": (((1, 0), (3, 0), (4, 1), (4, 4), (3, 5), (1, 5), (0, 4), (0, 1),
           (1, 0)), ((4, 1), (4, 6))),
    " ": (),
    ".": (((2, 6), (2, 6)),),
    ",": (((2, 4), (2, 6), (1, 6)),),
    ":": (((2, 1), (2, 1)), ((2, 5), (2, 5))),
    ";": (((2, 1), (2, 1)), ((2, 3), (2, 6), (1, 6))),
    "-": (((0, 3), (4, 3)),),
    "%": (((1, 0), (2, 0), (2, 1), (1, 1), (1, 0)),
          ((3, 5), (4, 5), (4, 6), (3, 6), (3, 5)), ((0, 6), (4, 0))),
    "$": (((4, 1), (3, 0), (1, 0), (0, 1), (0, 2), (1, 3), (3, 3), (4, 4),
           (4, 5), (3, 6), (1, 6), (0, 5)), ((2, 0), (2, 6))),
    "(": (((3, 0), (1, 2), (1, 4), (3, 6)),),
    ")": (((1, 0), (3, 2), (3, 4), (1, 6)),),
    "'": (((2, 0), (1, 2)),),
    "/": (((0, 6), (4, 0)),),
    "+": (((2, 0), (2, 6)), ((0, 3), (4, 3))),
    "=": (((0, 2), (4, 2)), ((0, 4), (4, 4))),
    "!": (((2, 0), (2, 4)), ((2, 6), (2, 6))),
    "?": (((1, 0), (3, 0), (4, 1), (4, 2), (3, 3), (2, 3)),
          ((2, 5), (2, 5))),
    '"': (((1, 0), (1, 2)), ((3, 0), (3, 2))),
    "_": (((0, 6), (4, 6)),),
}

BOX_GLYPH = (((0, 0), (4, 0), (4, 6), (0, 6), (0, 0)),)


def glyph_strokes(ch):
    return FONT.get(ch, BOX_GLYPH)


def text_width(text, scale):
    """Pixel width of text at a scale (each glyph is 6 grid units wide)."""
    if not text:
        return 0
    return len(text) * 6 * scale - scale


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    lines, current = [], ""
    for word in text.split(" "):
        trial = word if not current else current + " " + word
        if text_width(trial, scale) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# --- canvas ------------------------------------------------------------------
class Canvas:
    def __init__(self, size, bg):
        self.size = size
        self.buf = bytearray(bg) * (size * size)

    def _off(self, x, y):
        return (y * self.size + x) * 3

    def px(self, x, y, color):
        if 0 <= x < self.size and 0 <= y < self.size:
            o = self._off(x, y)
            self.buf[o:o + 3] = bytes(color)

    def dot(self, cx, cy, w, color):
        half = w // 2
        for dy in range(-half, w - half):
            for dx in range(-half, w - half):
                self.px(cx + dx, cy + dy, color)

    def fill_rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.size, x + w), min(self.size, y + h)
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            o = self._off(x0, yy)
            self.buf[o:o + len(row)] = row

    def hline(self, x, y, w, color, t=1):
        self.fill_rect(x, y, w, t, color)

    def vline(self, x, y, h, color, t=1):
        self.fill_rect(x, y, t, h, color)

    def rect(self, x, y, w, h, color, t=1):
        self.hline(x, y, w, color, t)
        self.hline(x, y + h - t, w, color, t)
        self.vline(x, y, h, color, t)
        self.vline(x + w - t, y, h, color, t)

    def line(self, x0, y0, x1, y1, color, w=1):
        """Bresenham line with a square brush of side w."""
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        x, y = x0, y0
        while True:
            self.dot(x, y, w, color)
            if x == x1 and y == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def polyline(self, points, color, w=1):
        for (ax, ay), (bx, by) in zip(points, points[1:]):
            self.line(ax, ay, bx, by, color, w)

    def circle(self, cx, cy, r, color, w=1):
        import math
        pts = []
        steps = max(24, r * 4)
        for i in range(steps + 1):
            a = 2 * math.pi * i / steps
            pts.append((cx + int(round(r * math.cos(a))),
                        cy + int(round(r * math.sin(a)))))
        self.polyline(pts, color, w)

    def ellipse_arc(self, cx, cy, rx, ry, a0, a1, color, w=1):
        import math
        pts = []
        steps = 24
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            pts.append((cx + int(round(rx * math.cos(a))),
                        cy + int(round(ry * math.sin(a)))))
        self.polyline(pts, color, w)

    # --- text ---
    def glyph(self, ch, x, y, scale, color, weight):
        for stroke in glyph_strokes(ch):
            pts = [(x + px * scale, y + py * scale) for (px, py) in stroke]
            if len(pts) == 1:
                self.dot(pts[0][0], pts[0][1], weight, color)
            else:
                self.polyline(pts, color, weight)

    def text(self, s, x, y, scale, color, weight=None, align="left"):
        if weight is None:
            weight = max(1, (scale + 1) // 2)
        if align == "center":
            x -= text_width(s, scale) // 2
        elif align == "right":
            x -= text_width(s, scale)
        cx = x
        for ch in s:
            self.glyph(ch, cx, y, scale, color, weight)
            cx += 6 * scale
        return cx

    def paragraph(self, s, x, y, scale, color, max_width, leading, weight=None):
        for line in wrap_text(s, scale, max_width):
            self.text(line, x, y, scale, color, weight)
            y += 7 * scale + leading
        return y


# --- PNG writer --------------------------------------------------------------
def write_png(path, canvas):
    raw = bytearray()
    stride = canvas.size * 3
    for y in range(canvas.size):
        raw.append(0)  # filter: none
        raw += canvas.buf[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", canvas.size, canvas.size,
                                      8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)
    return len(png)


# --- layout ------------------------------------------------------------------
M = 36            # outer margin
RIGHT = SIZE - M  # 988
CW = RIGHT - M    # 952 content width


def masthead(c):
    c.hline(M, 34, CW, INK, 4)
    c.text("SATURDAY - 21 NOVEMBER 2026", 512, 50, 3, RED, align="center")
    c.text("THE DAY IN NEWS", 512, 80, 9, INK, align="center")
    c.text("FOUR STORIES THAT DEFINED THE DAY - IN ONE IMAGE",
           512, 150, 2, GREY, weight=2, align="center")
    c.hline(M, 168, CW, INK, 2)
    c.hline(M, 173, CW, INK, 1)


def lead_story(c):
    """Anthropic IPO: the day's biggest story, left column."""
    x, y, w = M, 190, 564
    c.text("MARKETS - IPO", x, y, 2, RED, weight=2)
    c.text("ANTHROPIC", x, y + 24, 5, INK)
    c.text("MAKES HISTORY", x, y + 64, 5, INK)
    c.paragraph(
        "CLAUDE MAKER RAISES $81.3B IN THE BIGGEST IPO EVER. "
        "VALUATION TOPS $2 TRILLION ON ITS FIRST DAY OF TRADING.",
        x, y + 116, 2, INK, w - 24, 6, weight=2)
    stats = [("RAISED", "$81.3B"), ("PRICE", "$83"), ("PEAK VALUE", "$2.1T")]
    bx, by, bw, bh = x, y + 196, 180, 76
    for i, (label, value) in enumerate(stats):
        sx = bx + i * (bw + 12)
        c.rect(sx, by, bw, bh, INK, 2)
        c.text(label, sx + bw // 2, by + 10, 2, GREY, weight=2, align="center")
        c.text(value, sx + bw // 2, by + 32, 4, INK, align="center")
    c.text("TOPS SPACEX'S JUNE ISSUE.", x, by + bh + 12, 2, GREY, weight=2)


def market_panel(c):
    """Taiwan stocks: worst week in 35 years, right column."""
    x, y, w = 624, 190, 364
    c.text("TAIWAN - STOCKS", x, y, 2, RED, weight=2)
    c.text("WORST WEEK IN", x, y + 24, 4, INK)
    c.text("35 YEARS", x, y + 54, 4, INK)
    c.text("-17.5%", x, y + 96, 6, RED)
    # Falling-week chart (schematic: only the two verified closes labelled).
    cx0, cy0, cw, ch = x, y + 164, 340, 80
    c.vline(cx0, cy0, ch, GREY, 1)
    c.hline(cx0, cy0 + ch, cw, GREY, 1)
    c.hline(cx0, cy0 + ch // 2, cw, FAINT, 1)
    pts = [(cx0 + int(f * cw), cy0 + int(t * ch)) for f, t in
           ((0.00, 0.06), (0.20, 0.24), (0.35, 0.18), (0.50, 0.46),
            (0.65, 0.56), (0.80, 0.74), (1.00, 0.94))]
    c.polyline(pts, RED, 3)
    c.dot(pts[0][0], pts[0][1], 5, RED)
    c.dot(pts[-1][0], pts[-1][1], 5, RED)
    c.text("43,675", cx0 + 4, cy0 - 16, 2, GREY, weight=2)
    c.text("36,033", cx0 + cw - 62, cy0 + ch + 6, 2, GREY, weight=2)
    c.text("FRIDAY -2,394 TO 36,033.", x, cy0 + ch + 28, 2, INK, weight=2)
    c.text("TSMC FELL TO NT$1,970.", x, cy0 + ch + 48, 2, INK, weight=2)


def diplomacy_panel(c):
    """APEC Shenzhen: Trump-Xi third meeting."""
    x, y, w = M, 522, 464
    c.text("DIPLOMACY - SHENZHEN", x, y, 2, RED, weight=2)
    c.text("TRUMP AND XI", x, y + 24, 4, INK)
    c.text("MEET A THIRD TIME", x, y + 54, 4, INK)
    # Small globe pictogram, clear of both headline lines.
    c.circle(470, y + 30, 20, BLUE, 2)
    c.ellipse_arc(470, y + 30, 20, 8, 0, 6.2832, BLUE, 1)
    c.ellipse_arc(470, y + 30, 8, 20, 0, 6.2832, BLUE, 1)
    c.hline(450, y + 30, 40, BLUE, 1)
    c.paragraph(
        "AT THE APEC SUMMIT, THE LEADERS AGREED TO WORK TOGETHER ON "
        "AI SAFETY RULES. TRUMP SAID XI BACKED HIS PUSH TO LIMIT "
        "NUCLEAR ARMS. A US-CHINA-RUSSIA SUMMIT ISSUED A PEACE "
        "DECLARATION.",
        x, y + 104, 2, INK, w - 24, 6, weight=2)


def payout_panel(c):
    """Taiwan legislature passes the NT$20,000 handout, 50-46."""
    x, y, w = 524, 522, 464
    c.text("TAIWAN - POLITICS", x, y, 2, RED, weight=2)
    c.text("NT$20,000 PAYOUT", x, y + 24, 4, INK)
    c.text("PASSES 50-46", x, y + 54, 4, INK)
    c.paragraph(
        "THE LEGISLATURE PASSED A NT$20,000 CASH HANDOUT FOR ALL. "
        "THE PREMIER'S OFFICE CALLED IT UNCONSTITUTIONAL AND A "
        "FISCAL RISK.",
        x, y + 104, 2, INK, w - 24, 6, weight=2)
    # Vote tally bars: FOR 50 vs AGAINST 46.
    for row, (label, votes, color) in enumerate(
            (("FOR 50", 50, RED), ("AGAINST 46", 46, BLUE))):
        by = y + 196 + row * 28
        c.text(label, x, by, 2, INK, weight=2)
        bar_x = x + 132
        bar_w = int(300 * votes / 50)
        c.fill_rect(bar_x, by + 1, bar_w, 14, color)


def ticker(c):
    c.fill_rect(M, 790, CW, 66, DARK)
    c.paragraph(
        "ALSO TODAY - ICJ: MYANMAR GUILTY OF ROHINGYA GENOCIDE - "
        "RUSSIAN MISSILE HITS KYIV BRIDGE, 3 DEAD - EUROPE'S YOUTH "
        "MARCH AGAINST WAR AND LIVING COSTS - TAIWAN RUSHES TO "
        "STEADY MARKETS",
        M + 16, 798, 2, WHITE, CW - 32, 4, weight=2)


def footer(c):
    c.hline(M, 872, CW, FAINT, 1)
    c.text("SOURCES: CNA - LIBERTY TIMES - PTS - 21 NOV 2026",
           512, 890, 2, GREY, weight=2, align="center")
    c.text("DRAWN BY PURE PYTHON STDLIB - NO FONTS, NO FILES, NO NETWORK",
           512, 916, 2, GREY, weight=2, align="center")


def build():
    c = Canvas(SIZE, PAPER)
    masthead(c)
    lead_story(c)
    market_panel(c)
    c.vline(612, 190, 296, FAINT, 2)
    c.hline(M, 504, CW, INK, 2)
    diplomacy_panel(c)
    payout_panel(c)
    c.vline(512, 522, 250, FAINT, 2)
    ticker(c)
    footer(c)
    return c


def output_path():
    if len(sys.argv) > 1:
        return sys.argv[1]
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    return os.path.join(out_dir, "entry.png")


def main():
    path = output_path()
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    size = write_png(path, build())
    digest = hashlib.sha256(open(path, "rb").read()).hexdigest()
    print("wrote %s 1024x1024 %d bytes sha256=%s" % (path, size, digest))


if __name__ == "__main__":
    main()
