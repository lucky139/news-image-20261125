#!/usr/bin/env python3
"""news-image-20261125: draw one 1024x1024 PNG summing up the world news of
Wednesday 25 November 2026. Standard library only, no network, no clock, no
randomness, so two runs write byte-identical files.

Layout: a masthead naming the day, then six story cards in a 2x3 grid, each
with a small pictogram, a headline and one detail line, and a footer line.
Text is rendered with a hand-built 5x7 pixel font (uppercase ASCII).
"""

import binascii
import hashlib
import os
import struct
import sys
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- font -----
# Each glyph is 7 rows of 5 cells; '#' is ink, '.' is empty.
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".....", "..#.."),
    ",": (".....", ".....", ".....", ".....", ".....", "..#..", "..#.."),
    ":": (".....", "..#..", ".....", ".....", ".....", "..#..", "....."),
    ";": (".....", "..#..", ".....", ".....", ".....", "..#..", "..#.."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "'": ("..#..", "..#..", "..#..", ".....", ".....", ".....", "....."),
    "/": ("....#", "....#", "...#.", "...#.", "..#..", ".#...", "#...."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "=": (".....", ".....", ".###.", ".....", ".###.", ".....", "....."),
    "*": (".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    "_": (".....", ".....", ".....", ".....", ".....", ".....", "#####"),
    "[": (".###.", ".#...", ".#...", ".#...", ".#...", ".#...", ".###."),
    "]": (".###.", "...#.", "...#.", "...#.", "...#.", "...#.", ".###."),
}

CHAR_W, CHAR_H = 5, 7


def text_width(text, scale):
    """Pixel width of text at the given scale (1px gap between glyphs)."""
    return len(text) * (CHAR_W * scale + scale) - scale


def wrap_text(text, max_width, scale):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    per_char = CHAR_W * scale + scale
    max_chars = max(1, (max_width + scale) // per_char)
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if len(trial) <= max_chars:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            # A single over-long word is hard-split.
            while len(word) > max_chars:
                lines.append(word[:max_chars])
                word = word[max_chars:]
            cur = word
    if cur:
        lines.append(cur)
    return lines


# -------------------------------------------------------------- canvas -----
class Canvas:
    def __init__(self, width, height, bg):
        self.w, self.h = width, height
        self.buf = bytearray(bg * (width * height))

    def px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = color

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            if 0 <= yy < self.h:
                lo, hi = max(x, 0), min(x + w, self.w)
                for xx in range(lo, hi):
                    i = (yy * self.w + xx) * 3
                    self.buf[i:i + 3] = color

    def hline(self, x, y, length, color):
        self.rect(x, y, length, 1, color)

    def vline(self, x, y, length, color):
        self.rect(x, y, 1, length, color)

    def line(self, x0, y0, x1, y1, color):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err, x, y = dx - dy, x0, y0
        while True:
            self.px(x, y, color)
            if x == x1 and y == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            dx = int((r * r - (yy - cy) ** 2) ** 0.5) if abs(yy - cy) <= r else 0
            self.rect(cx - dx, yy, 2 * dx + 1, 1, color)

    def ring(self, cx, cy, r, thick, color):
        for yy in range(cy - r - thick, cy + r + thick + 1):
            for xx in range(cx - r - thick, cx + r + thick + 1):
                d = ((xx - cx) ** 2 + (yy - cy) ** 2) ** 0.5
                if r - thick <= d <= r:
                    self.px(xx, yy, color)

    def triangle(self, p0, p1, p2, color):
        xs = sorted((p0, p1, p2), key=lambda p: p[1])
        (x0, y0), (x1, y1), (x2, y2) = xs
        if y0 == y2:
            return
        for y in range(y0, y2 + 1):
            t0 = (y - y0) / (y2 - y0) if y2 != y0 else 0
            xa = x0 + (x2 - x0) * t0
            if y < y1:
                t1 = (y - y0) / (y1 - y0) if y1 != y0 else 0
                xb = x0 + (x1 - x0) * t1
            else:
                t1 = (y - y1) / (y2 - y1) if y2 != y1 else 0
                xb = x1 + (x2 - x1) * t1
            lo, hi = int(min(xa, xb)), int(max(xa, xb))
            self.rect(lo, y, hi - lo + 1, 1, color)

    def glyph(self, x, y, ch, scale, color):
        rows = FONT.get(ch)
        if rows is None:
            rows = FONT["?"]
        for r, row in enumerate(rows):
            for c, cell in enumerate(row):
                if cell == "#":
                    self.rect(x + c * scale, y + r * scale, scale, scale, color)

    def text(self, x, y, s, scale, color):
        cx = x
        for ch in s:
            self.glyph(cx, y, ch, scale, color)
            cx += (CHAR_W + 1) * scale
        return cx

    def text_centered(self, cx, y, s, scale, color):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, color)

    def paragraph(self, x, y, s, max_width, scale, color, leading=None):
        lh = leading if leading is not None else CHAR_H * scale + 4 * scale // 2
        yy = y
        for line in wrap_text(s, max_width, scale):
            self.text(x, yy, line, scale, color)
            yy += lh
        return yy


# ------------------------------------------------------------------ png -----
def encode_png(canvas):
    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter: none
        raw += canvas.buf[y * stride:(y + 1) * stride]
    idat = zlib.compress(bytes(raw), 9)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", idat)
    png += chunk(b"IEND", b"")
    return png

# -------------------------------------------------------------- content -----
NAVY = bytes((16, 30, 51))
CARD = bytes((245, 241, 230))
INK = bytes((20, 33, 61))
GREY = bytes((90, 100, 115))
GOLD = bytes((242, 193, 78))
WHITE = bytes((255, 255, 255))
RED = bytes((192, 57, 43))
BLUE = bytes((36, 113, 163))
TEAL = bytes((20, 143, 119))
PURPLE = bytes((125, 60, 152))
ORANGE = bytes((202, 111, 30))
GREEN = bytes((30, 132, 73))

# Six stories verified against Reuters / Daily Mirror / Jerusalem Post /
# 10things.news reports of Wednesday 25 November 2026.
STORIES = [
    {
        "tag": "TRADE",
        "color": RED,
        "icon": "tariff",
        "headline": "US PLANS TARIFFS OF UP TO 20% ON CHINA, THE EU AND 12 MORE NATIONS",
        "detail": "WASHINGTON ACTS AGAINST FACTORY OVERCAPACITY",
    },
    {
        "tag": "TECH",
        "color": BLUE,
        "icon": "chip",
        "headline": "HUAWEI CONVICTED BY US JURY IN IRAN SANCTIONS TRIAL",
        "detail": "GUILTY OF FRAUD AND TRADE-SECRET THEFT",
    },
    {
        "tag": "CONFLICT",
        "color": ORANGE,
        "icon": "tower",
        "headline": "HOUTHIS STRIKE RIYADH'S TALLEST TOWER; 11 WOUNDED",
        "detail": "SAUDI-LED STRIKES HIT HODEIDAH PORT IN REPLY",
    },
    {
        "tag": "SPACE",
        "color": PURPLE,
        "icon": "rocket",
        "headline": "CHINA LAUNCHES SHENZHOU-24 WITH PAKISTAN'S FIRST ASTRONAUT",
        "detail": "FIRST FOREIGN CREW MEMBER ABOARD TIANGONG STATION",
    },
    {
        "tag": "CYBER",
        "color": TEAL,
        "icon": "shield",
        "headline": "CIA AND US SPY AGENCIES HIT BY CYBER BREACH",
        "detail": "UNCLASSIFIED SYSTEMS COMPROMISED; PROBE UNDER WAY",
    },
    {
        "tag": "LABOUR",
        "color": GREEN,
        "icon": "wage",
        "headline": "BANGLADESH RAISES GARMENT WAGE 36% AFTER PROTESTS",
        "detail": "MINIMUM PAY UP TO $139 A MONTH",
    },
]


def draw_icon(cv, kind, x, y, size, color):
    """A small flat pictogram inside a size x size box at (x, y)."""
    if kind == "tariff":  # a big percent sign, drawn geometrically
        cv.disc(x + 20, y + 20, 9, color)
        cv.disc(x + 20, y + 20, 4, CARD)
        cv.disc(x + size - 20, y + size - 20, 9, color)
        cv.disc(x + size - 20, y + size - 20, 4, CARD)
        cv.line(x + 18, y + size - 16, x + size - 18, y + 16, color)
        cv.line(x + 20, y + size - 16, x + size - 16, y + 16, color)
        cv.rect(x + 6, y + size - 12, size - 12, 5, color)
    elif kind == "chip":  # microchip with pins
        cv.rect(x + 16, y + 16, size - 32, size - 32, color)
        cv.rect(x + 26, y + 26, size - 52, size - 52, CARD)
        cv.rect(x + 34, y + 34, size - 68, size - 68, color)
        for i in range(3):
            cv.rect(x + 22 + i * 14, y + 4, 6, 12, color)
            cv.rect(x + 22 + i * 14, y + size - 16, 6, 12, color)
            cv.rect(x + 4, y + 22 + i * 14, 12, 6, color)
            cv.rect(x + size - 16, y + 22 + i * 14, 12, 6, color)
    elif kind == "tower":  # skyscraper with a blast star on top
        cv.rect(x + size // 2 - 12, y + 22, 24, size - 22, color)
        for r in range(4):
            cv.rect(x + size // 2 - 7, y + 30 + r * 12, 14, 5, CARD)
        cx, cy = x + size // 2, y + 12
        for dx, dy in ((0, -9), (0, 9), (-9, 0), (9, 0), (-6, -6), (6, -6), (-6, 6), (6, 6)):
            cv.line(cx, cy, cx + dx, cy + dy, GOLD)
        cv.disc(cx, cy, 3, GOLD)
    elif kind == "rocket":  # rocket lifting off, flame below
        cx = x + size // 2
        cv.triangle((cx, y + 6), (cx - 12, y + 34), (cx + 12, y + 34), color)
        cv.rect(cx - 12, y + 34, 24, 22, color)
        cv.triangle((cx - 12, y + 44), (cx - 22, y + 58), (cx - 12, y + 56), color)
        cv.triangle((cx + 12, y + 44), (cx + 22, y + 58), (cx + 12, y + 56), color)
        cv.disc(cx, y + 44, 5, CARD)
        cv.triangle((cx - 6, y + 56), (cx + 6, y + 56), (cx, y + size - 4), GOLD)
    elif kind == "shield":  # shield with a crack
        cv.triangle((x + 8, y + 10), (x + size - 8, y + 10), (x + size // 2, y + size - 8), color)
        cv.rect(x + 8, y + 10, size - 16, 26, color)
        cv.line(x + size // 2 - 2, y + 16, x + size // 2 + 6, y + 30, CARD)
        cv.line(x + size // 2 + 6, y + 30, x + size // 2 - 4, y + 44, CARD)
        cv.line(x + size // 2 - 4, y + 44, x + size // 2 + 2, y + 56, CARD)
    elif kind == "wage":  # banknote with an upward arrow
        cv.rect(x + 6, y + 16, size - 12, size - 34, color)
        cv.rect(x + 12, y + 22, size - 24, size - 46, CARD)
        cv.text(x + 16, y + 26, "$", 3, color)
        cv.line(x + size - 30, y + size - 24, x + size - 30, y + 26, color)
        cv.line(x + size - 30, y + 26, x + size - 38, y + 34, color)
        cv.line(x + size - 30, y + 26, x + size - 22, y + 34, color)


def draw_globe(cv, cx, cy, r):
    cv.ring(cx, cy, r, 3, GOLD)
    cv.line(cx - r, cy, cx + r, cy, GOLD)
    cv.line(cx, cy - r, cx, cy + r, GOLD)
    for k in (-2, -1, 1, 2):
        off = k * r // 3
        cv.line(cx + off, cy - r + 6, cx + off, cy + r - 6, GOLD)


def build():
    cv = Canvas(W, H, NAVY)

    # Masthead: title, date, gold rule, small globe.
    cv.text(32, 26, "WORLD NEWS", 8, WHITE)
    cv.text(32, 104, "WEDNESDAY 25 NOVEMBER 2026", 3, GOLD)
    draw_globe(cv, 936, 66, 44)
    cv.rect(32, 148, W - 64, 4, GOLD)

    # Six story cards, 2 columns x 3 rows.
    gx, gy = 32, 168
    cw, ch, gap = 472, 252, 16
    for i, s in enumerate(STORIES):
        col, row = i % 2, i // 2
        x = gx + col * (cw + gap)
        y = gy + row * (ch + gap)
        cv.rect(x, y, cw, ch, CARD)
        cv.rect(x, y, cw, 10, s["color"])
        cv.text(x + 16, y + 24, s["tag"], 2, s["color"])
        draw_icon(cv, s["icon"], x + 16, y + 56, 72, s["color"])
        cv.paragraph(x + 104, y + 56, s["headline"], cw - 120, 2, INK)
        cv.rect(x + 16, y + 168, cw - 32, 2, bytes((200, 192, 170)))
        cv.paragraph(x + 16, y + 184, s["detail"], cw - 32, 2, GREY)

    # Footer.
    cv.text_centered(W // 2, 972, "SIX STORIES FROM AROUND THE WORLD - REPORTED 25 NOVEMBER 2026",
                     2, GOLD)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    data = encode_png(build())
    path = os.path.join(out_dir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes) sha256=%s" % (path, len(data),
          hashlib.sha256(data).hexdigest()))


if __name__ == "__main__":
    main()
