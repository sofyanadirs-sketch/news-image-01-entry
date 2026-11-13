#!/usr/bin/env python3
"""make.fun news-image-01 entry: draws one newspaper front page that sums up
Friday 13 November 2026 in a single image.

Six stories, chosen for breadth across regions and fields, each in its own
panel with a hand-drawn icon, a headline and a short summary:

  1. MIDDLE EAST - the Gulf on edge: Iran says it destroyed a US radar in
     Bahrain; a tanker is hit by a mine in the Strait of Hormuz.
  2. EUROPE - Ukraine peace talks: Europe wins a seat at the next round;
     the biggest prisoner swap of the war is being prepared.
  3. TECH - Nvidia's CEO Jensen Huang resigns; Trump calls it "a terrible
     thing"; US officials clash over Nvidia-related chip controls.
  4. ASIA-PACIFIC - China stages huge unannounced Pacific drills around
     Taiwan, Taiwan says.
  5. ENERGY - the IEA forecasts a world oil surplus: supply of 105 million
     barrels a day outpacing demand.
  6. TECH OUTAGE - Microsoft 365 goes down worldwide: Outlook, Teams and
     Copilot fail in 74 countries; Microsoft rules out a cyberattack.

Every pixel is drawn by this program at run time: no photos, no downloaded
images, no network, no clock, no randomness. Pure standard library, so it
runs exactly the same in the grader's Python 3.13 sandbox. It writes one
1024x1024 PNG to /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).
Deterministic: two runs write byte-identical files.
"""

import math
import os
import struct
import zlib
from pathlib import Path

# Logical canvas, upscaled 4x with nearest neighbour (chunky pixel look that
# stays legible when the image is shown small).
W = 256
H = 256
SCALE = 4
OUT_W = W * SCALE
OUT_H = H * SCALE

# --- palette ---------------------------------------------------------------
PAPER = (247, 243, 234)
NAVY = (27, 42, 74)
GOLD = (255, 209, 102)
RED = (192, 57, 43)
INK = (30, 30, 34)
BODY = (70, 70, 78)
BORDER = (120, 120, 125)
WHITE = (255, 255, 255)
PANEL_BG = (255, 255, 255)

CAT_MIDEAST = (142, 43, 43)
CAT_EUROPE = (43, 76, 155)
CAT_NVIDIA = (90, 140, 0)
CAT_ASIA = (15, 118, 110)
CAT_ENERGY = (138, 90, 0)
CAT_OUTAGE = (51, 65, 85)

SEA_LIGHT = (168, 208, 235)
SEA_DARK = (52, 110, 165)
SKY_BLUE = (120, 180, 225)
UKR_BLUE = (0, 87, 183)
UKR_YELLOW = (255, 213, 0)
CHIP_GREEN = (38, 90, 10)
DARK_GRAY = (70, 72, 78)
BARREL = (40, 40, 46)
ORANGE = (235, 120, 30)
FLAME = (255, 176, 32)

# --- 5x7 pixel font (uppercase, digits, a little punctuation) --------------
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
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
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ",": ("00000", "00000", "00000", "00000", "00100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
}


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def wrap_text(text, max_chars):
    """Greedy word wrap; returns a list of lines, each <= max_chars."""
    lines = []
    for word in text.split(" "):
        if not lines or len(lines[-1]) + 1 + len(word) > max_chars:
            lines.append(word)
        else:
            lines[-1] += " " + word
    return lines


# --- canvas ----------------------------------------------------------------
class Canvas:
    def __init__(self):
        self.px = bytearray(W * H * 3)

    def set(self, x, y, color):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def fill_rect(self, x0, y0, x1, y1, color):
        for y in range(max(0, y0), min(H, y1 + 1)):
            for x in range(max(0, x0), min(W, x1 + 1)):
                self.set(x, y, color)

    def rect_outline(self, x0, y0, x1, y1, color):
        self.fill_rect(x0, y0, x1, y0, color)
        self.fill_rect(x0, y1, x1, y1, color)
        self.fill_rect(x0, y0, x0, y1, color)
        self.fill_rect(x1, y0, x1, y1, color)

    def circle(self, cx, cy, r, color):
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                    self.set(x, y, color)

    def ellipse(self, cx, cy, rx, ry, color):
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0:
                    self.set(x, y, color)

    def line(self, x0, y0, x1, y1, color, width=1):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(steps + 1):
            t = i / steps
            x = round(x0 + (x1 - x0) * t)
            y = round(y0 + (y1 - y0) * t)
            self.circle(x, y, max(0, width // 2), color)

    def arc(self, cx, cy, r, a0, a1, color, thick=2):
        """Arc of a circle; angles in degrees, y-down screen coords."""
        for y in range(cy - r - thick, cy + r + thick + 1):
            for x in range(cx - r - thick, cx + r + thick + 1):
                dx, dy = x - cx, y - cy
                d = math.hypot(dx, dy)
                if abs(d - r) > thick / 2 + 0.6:
                    continue
                ang = math.degrees(math.atan2(dy, dx))
                if a0 <= ang <= a1:
                    self.set(x, y, color)

    def ring(self, cx, cy, r0, r1, a0, a1, color):
        for y in range(cy - r1, cy + r1 + 1):
            for x in range(cx - r1, cx + r1 + 1):
                dx, dy = x - cx, y - cy
                d = math.hypot(dx, dy)
                if not (r0 <= d <= r1):
                    continue
                ang = math.degrees(math.atan2(dy, dx))
                if a0 <= ang <= a1:
                    self.set(x, y, color)

    def triangle(self, p0, p1, p2, color):
        xs = [p0[0], p1[0], p2[0]]
        ys = [p0[1], p1[1], p2[1]]

        def sign(ax, ay, bx, by, cx, cy):
            return (ax - cx) * (by - cy) - (bx - cx) * (ay - cy)

        for y in range(min(ys), max(ys) + 1):
            for x in range(min(xs), max(xs) + 1):
                d0 = sign(x, y, p0[0], p0[1], p1[0], p1[1])
                d1 = sign(x, y, p1[0], p1[1], p2[0], p2[1])
                d2 = sign(x, y, p2[0], p2[1], p0[0], p0[1])
                if (d0 >= 0 and d1 >= 0 and d2 >= 0) or (
                    d0 <= 0 and d1 <= 0 and d2 <= 0
                ):
                    self.set(x, y, color)

    def rounded_rect(self, x0, y0, x1, y1, r, color):
        self.fill_rect(x0 + r, y0, x1 - r, y1, color)
        self.fill_rect(x0, y0 + r, x1, y1 - r, color)
        self.circle(x0 + r, y0 + r, r, color)
        self.circle(x1 - r, y0 + r, r, color)
        self.circle(x0 + r, y1 - r, r, color)
        self.circle(x1 - r, y1 - r, r, color)

    def text(self, text, x, y, scale, color):
        cx = x
        for ch in text:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                for col in range(5):
                    if glyph[row][col] == "1":
                        self.fill_rect(
                            cx + col * scale,
                            y + row * scale,
                            cx + col * scale + scale - 1,
                            y + row * scale + scale - 1,
                            color,
                        )
            cx += 6 * scale

    def text_bold(self, text, x, y, scale, color):
        self.text(text, x, y, scale, color)
        self.text(text, x + 1, y, scale, color)


# --- PNG encoding (stdlib only) --------------------------------------------
def _chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(canvas):
    # Upscale 4x nearest neighbour, filter byte 0 per row.
    raw = bytearray()
    for ly in range(H):
        row = bytearray()
        for lx in range(W):
            i = (ly * W + lx) * 3
            px = canvas.px[i : i + 3]
            row += px * SCALE
        raw.append(0)
        raw += row
        for _ in range(SCALE - 1):
            raw.append(0)
            raw += row
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", struct.pack(">IIBBBBB", OUT_W, OUT_H, 8, 2, 0, 0, 0))
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    return png


# --- story icons (each drawn in a 30x30 box at ix, iy) ----------------------
def icon_gulf(c, ix, iy):
    # Sea, an oil tanker, and a blast above it: the Strait of Hormuz.
    c.fill_rect(ix, iy, ix + 29, iy + 17, SKY_BLUE)
    c.fill_rect(ix, iy + 18, ix + 29, iy + 29, SEA_DARK)
    c.line(ix, iy + 21, ix + 29, iy + 21, WHITE, width=1)
    c.line(ix, iy + 25, ix + 29, iy + 25, WHITE, width=1)
    # Tanker hull + bridge.
    c.fill_rect(ix + 3, iy + 18, ix + 24, iy + 23, DARK_GRAY)
    c.fill_rect(ix + 18, iy + 12, ix + 23, iy + 18, DARK_GRAY)
    c.fill_rect(ix + 20, iy + 9, ix + 22, iy + 12, RED)
    # Blast starburst.
    c.circle(ix + 15, iy + 7, 3, FLAME)
    for k in range(8):
        ang = math.radians(k * 45)
        c.line(
            round(ix + 15 + math.cos(ang) * 4),
            round(iy + 7 + math.sin(ang) * 4),
            round(ix + 15 + math.cos(ang) * 7),
            round(iy + 7 + math.sin(ang) * 7),
            ORANGE,
            width=1,
        )


def icon_dove(c, ix, iy):
    # Blue over yellow (Ukraine) with a white dove of peace.
    c.fill_rect(ix, iy, ix + 29, iy + 14, UKR_BLUE)
    c.fill_rect(ix, iy + 15, ix + 29, iy + 29, UKR_YELLOW)
    c.ellipse(ix + 14, iy + 15, 9, 5, WHITE)
    c.circle(ix + 22, iy + 11, 3, WHITE)
    c.triangle((ix + 25, iy + 10), (ix + 28, iy + 12), (ix + 25, iy + 13), ORANGE)
    c.arc(ix + 13, iy + 13, 5, 200, 340, (200, 200, 200), thick=2)
    c.line(ix + 6, iy + 17, ix + 2, iy + 14, WHITE, width=1)
    c.line(ix + 6, iy + 17, ix + 2, iy + 19, WHITE, width=1)
    # Olive branch.
    c.line(ix + 4, iy + 24, ix + 12, iy + 20, (60, 140, 60), width=1)
    c.circle(ix + 6, iy + 23, 1, (60, 140, 60))
    c.circle(ix + 9, iy + 22, 1, (60, 140, 60))


def icon_chip(c, ix, iy):
    # A green chip stamped NVDA, with a red falling arrow: Nvidia's CEO out.
    c.fill_rect(ix, iy, ix + 29, iy + 29, (238, 238, 232))
    for yy in (iy + 8, iy + 14, iy + 20):
        c.line(ix, yy, ix + 1, yy, DARK_GRAY, width=1)
        c.line(ix + 28, yy, ix + 29, yy, DARK_GRAY, width=1)
    c.rounded_rect(ix + 2, iy + 4, ix + 27, iy + 21, 2, CHIP_GREEN)
    c.text("NVDA", ix + 3, iy + 10, 1, WHITE)
    c.line(ix + 15, iy + 23, ix + 15, iy + 27, RED, width=2)
    c.triangle(
        (ix + 12, iy + 26), (ix + 18, iy + 26), (ix + 15, iy + 29), RED
    )


def icon_taiwan(c, ix, iy):
    # Sea, a green island, grey ships around it, a red dashed ring.
    c.fill_rect(ix, iy, ix + 29, iy + 29, SEA_LIGHT)
    c.ellipse(ix + 15, iy + 15, 6, 10, (60, 140, 60))
    c.ellipse(ix + 15, iy + 12, 4, 5, (90, 170, 90))
    for sx, sy in ((ix + 4, iy + 22), (ix + 24, iy + 8), (ix + 25, iy + 23)):
        c.triangle((sx, sy), (sx + 5, sy), (sx + 2, sy - 4), DARK_GRAY)
        c.fill_rect(sx, sy, sx + 5, sy + 2, DARK_GRAY)
    c.arc(ix + 15, iy + 15, 13, 0, 70, RED, thick=1)
    c.arc(ix + 15, iy + 15, 13, 110, 180, RED, thick=1)
    c.arc(ix + 15, iy + 15, 13, 220, 290, RED, thick=1)


def icon_oil(c, ix, iy):
    # A black oil barrel and a falling price chart.
    c.fill_rect(ix, iy, ix + 29, iy + 29, (238, 238, 232))
    c.rounded_rect(ix + 4, iy + 7, ix + 15, iy + 26, 2, BARREL)
    c.fill_rect(ix + 4, iy + 11, ix + 15, iy + 12, (120, 120, 125))
    c.fill_rect(ix + 4, iy + 20, ix + 15, iy + 21, (120, 120, 125))
    c.line(ix + 18, iy + 6, ix + 22, iy + 12, (30, 90, 160), width=2)
    c.line(ix + 22, iy + 12, ix + 25, iy + 18, (30, 90, 160), width=2)
    c.line(ix + 25, iy + 18, ix + 28, iy + 25, (30, 90, 160), width=2)
    c.triangle(
        (ix + 25, iy + 24), (ix + 29, iy + 24), (ix + 27, iy + 28),
        (30, 90, 160),
    )


def icon_outage(c, ix, iy):
    # A blue envelope (mail) crossed out in red: Outlook, Teams, Copilot down.
    c.fill_rect(ix, iy, ix + 29, iy + 29, (238, 238, 232))
    c.rounded_rect(ix + 4, iy + 8, ix + 25, iy + 23, 2, (30, 90, 160))
    c.line(ix + 4, iy + 8, ix + 15, iy + 16, WHITE, width=2)
    c.line(ix + 25, iy + 8, ix + 15, iy + 16, WHITE, width=2)
    c.line(ix + 5, iy + 8, ix + 13, iy + 23, RED, width=3)
    c.line(ix + 24, iy + 8, ix + 16, iy + 23, RED, width=3)


ICONS = {
    "gulf": icon_gulf,
    "dove": icon_dove,
    "chip": icon_chip,
    "taiwan": icon_taiwan,
    "oil": icon_oil,
    "outage": icon_outage,
}

# --- stories ----------------------------------------------------------------
# (category tag, tag colour, headline, body, icon key)
STORIES = [
    (
        "MIDDLE EAST",
        CAT_MIDEAST,
        "GULF ON EDGE",
        "IRAN CLAIMS US RADAR HIT, TANKER MINED IN HORMUZ",
        "gulf",
    ),
    (
        "EUROPE",
        CAT_EUROPE,
        "UKRAINE TALKS",
        "EUROPE JOINS NEXT PEACE ROUND, RECORD PRISONER SWAP EYED",
        "dove",
    ),
    (
        "TECH",
        CAT_NVIDIA,
        "NVIDIA CEO OUT",
        "JENSEN HUANG RESIGNS, TRUMP CALLS IT 'TERRIBLE'",
        "chip",
    ),
    (
        "ASIA-PACIFIC",
        CAT_ASIA,
        "CHINA DRILLS",
        "HUGE UNANNOUNCED PACIFIC DRILLS SURROUND TAIWAN",
        "taiwan",
    ),
    (
        "ENERGY",
        CAT_ENERGY,
        "OIL GLUT LOOMS",
        "IEA: SUPPLY 105M BARRELS A DAY, OUTPACING DEMAND",
        "oil",
    ),
    (
        "TECH OUTAGE",
        CAT_OUTAGE,
        "MICROSOFT DOWN",
        "OUTLOOK, TEAMS, COPILOT FAIL IN 74 COUNTRIES",
        "outage",
    ),
]

PANEL_W = 124
PANEL_H = 66
GRID_X = (2, 130)
GRID_Y = (42, 110, 178)


def draw_panel(c, px, py, story):
    tag, color, headline, body, icon_key = story
    c.fill_rect(px, py, px + PANEL_W - 1, py + PANEL_H - 1, PANEL_BG)
    c.rect_outline(px, py, px + PANEL_W - 1, py + PANEL_H - 1, BORDER)
    # Category strip.
    c.fill_rect(px + 1, py + 1, px + PANEL_W - 2, py + 10, color)
    c.text(tag, px + 4, py + 2, 1, WHITE)
    # Icon (30x30) at left, headline beside it.
    ICONS[icon_key](c, px + 3, py + 13)
    c.text_bold(headline, px + 37, py + 23, 1, INK)
    # Body: up to 3 wrapped lines across the full panel width.
    lines = wrap_text(body, 19)
    assert len(lines) <= 3, (headline, lines)
    for i, line in enumerate(lines):
        c.text(line, px + 3, py + 43 + i * 8, 1, BODY)


def draw_masthead(c):
    c.fill_rect(0, 0, W - 1, 36, NAVY)
    title = "THE WORLD IN ONE DAY"
    c.text_bold(title, (W - text_width(title, 2)) // 2, 5, 2, WHITE)
    date = "FRIDAY, 13 NOVEMBER 2026"
    c.text(date, (W - text_width(date, 1)) // 2, 24, 1, GOLD)
    c.fill_rect(0, 37, W - 1, 39, RED)


def build_canvas():
    c = Canvas()
    c.fill_rect(0, 0, W - 1, H - 1, PAPER)
    draw_masthead(c)
    for i, story in enumerate(STORIES):
        px = GRID_X[i % 2]
        py = GRID_Y[i // 2]
        draw_panel(c, px, py, story)
    footer = "SOURCES: REUTERS, AP, IEA, MICROSOFT"
    c.text(footer, (W - text_width(footer, 1)) // 2, 248, 1, BODY)
    return c


def main():
    output_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "entry.png").write_bytes(encode_png(build_canvas()))


if __name__ == "__main__":
    main()
