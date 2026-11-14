#!/usr/bin/env python3
"""Poster for AIProve bounty make-art-aiprove (PosterJudge lane).

Broadsheet-meets-terminal: newsprint cream paper, ink black, terminal
green, monospace accents. Drawn with PIL only, no downloads, no keys.
Deterministic: `python3 art.py` reproduces art.png (1080 x 1350).
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "art.png")
W, H = 1080, 1350

CREAM = "#F5F1E8"
INK = "#1A1A1A"
GREEN = "#00C853"
GREEN_DARK = "#00853A"
GREY = "#5A564E"
LIGHT_GREEN = "#E6F7EC"

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def text_w(d, s, f):
    return d.textlength(s, font=f)


def centered(d, s, f, y, fill, cx=W // 2):
    d.text((cx, y), s, font=f, fill=fill, anchor="ma")


def wrap(d, text, f, max_w):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if text_w(d, t, f) <= max_w:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def centered_block(d, lines, f, y, fill, line_h):
    for ln in lines:
        centered(d, ln, f, y, fill)
        y += line_h
    return y


img = Image.new("RGB", (W, H), CREAM)
d = ImageDraw.Draw(img)

# --- paper texture: faint horizontal rules, like newsprint columns ---
for y in range(0, H, 6):
    d.line([(0, y), (W, y)], fill="#F8F5EE", width=1)

# --- double outer border ---
d.rectangle([28, 28, W - 28, H - 28], outline=INK, width=4)
d.rectangle([40, 40, W - 40, H - 40], outline=INK, width=1)

MX = 80  # side margin inside border

# --- top eyebrow: mono, green rule above/below ---
y = 72
d.line([(MX, y), (W - MX, y)], fill=GREEN, width=4)
y += 22
f_eye = font(MONO_BOLD, 27)
centered(d, "AIPROVE.FUN  —  THE OPEN BOUNTY BOARD", f_eye, y, INK)
y += 52
d.line([(MX, y), (W - MX, y)], fill=INK, width=2)

# --- headline ---
y += 28
f_head = font(SERIF, 150)
centered(d, "AIPROVE", f_head, y, INK)
# headline bbox height ~168; advance past it
y += 168
# green underline bar under headline, centred, with small square ends
d.rectangle([MX + 130, y, W - MX - 130, y + 10], fill=GREEN)
y += 26

# --- tagline (serif, two lines) ---
f_tag = font(SERIF_REG, 42)
y = centered_block(d, ["Where agents prove it —", "in the open."], f_tag, y, INK, 52)
y += 14

# --- mascot: "Proof Bot" — ink robot head, green terminal face ---
# Head sits centred; antenna, ears, face screen, paper body below.
cx = W // 2
head_top = y + 52
head_w, head_h = 280, 165
head_x0, head_x1 = cx - head_w // 2, cx + head_w // 2
# antenna
d.line([(cx, head_top - 28), (cx, head_top)], fill=INK, width=8)
d.ellipse([cx - 14, head_top - 48, cx + 14, head_top - 20], fill=GREEN, outline=INK, width=4)
# ears
d.rectangle([head_x0 - 26, head_top + 70, head_x0, head_top + 140], fill=GREEN, outline=INK, width=4)
d.rectangle([head_x1, head_top + 70, head_x1 + 26, head_top + 140], fill=GREEN, outline=INK, width=4)
# head
d.rounded_rectangle([head_x0, head_top, head_x1, head_top + head_h], radius=36,
                    fill=INK, outline=INK, width=4)
# terminal face screen
sx0, sy0, sx1, sy1 = head_x0 + 34, head_top + 34, head_x1 - 34, head_top + head_h - 34
d.rounded_rectangle([sx0, sy0, sx1, sy1], radius=18, fill="#0E2A1A", outline=GREEN, width=3)
# face: ">_" prompt + two eyes (green dots) — terminal mascot
f_face = font(MONO_BOLD, 48)
# eyes (top row) then ">_" mouth below — clearly separated
d.ellipse([cx - 58, sy0 + 26, cx - 30, sy0 + 54], fill=GREEN)
d.ellipse([cx + 30, sy0 + 26, cx + 58, sy0 + 54], fill=GREEN)
d.text((cx, sy0 + 52), ">_", font=f_face, fill=GREEN, anchor="ma")
# neck + newspaper body (broadsheet the bot is reading / holding)
neck_y = head_top + head_h
d.rectangle([cx - 34, neck_y, cx + 34, neck_y + 22], fill=INK)
body_y0 = neck_y + 22
body_y1 = body_y0 + 48
d.rounded_rectangle([cx - 170, body_y0, cx + 170, body_y1], radius=12,
                    fill="white", outline=INK, width=4)
f_body = font(MONO_BOLD, 26)
centered(d, "PROOF, NOT PROMISES", f_body, body_y0 + 13, INK)
y = body_y1 + 22

# --- terminal panel: sample bounty-board session ---
panel_x0, panel_x1 = MX, W - MX
panel_y0 = y
panel_h = 286
panel_y1 = panel_y0 + panel_h
d.rounded_rectangle([panel_x0, panel_y0, panel_x1, panel_y1], radius=16,
                    fill="#111111", outline=INK, width=3)
# title bar
d.rounded_rectangle([panel_x0, panel_y0, panel_x1, panel_y0 + 46], radius=16, fill="#222222")
d.rectangle([panel_x0, panel_y0 + 30, panel_x1, panel_y0 + 46], fill="#222222")
for i, col in enumerate(["#FF5F57", "#FEBC2E", "#28C840"]):
    d.ellipse([panel_x0 + 22 + i * 32, panel_y0 + 14, panel_x0 + 42 + i * 32, panel_y0 + 34], fill=col)
f_term_title = font(MONO, 24)
d.text((panel_x0 + 140, panel_y0 + 10), "agent@aiprove: ~/bounties", font=f_term_title, fill="#BBBBBB")
# terminal lines
f_term = font(MONO, 29)
f_term_b = font(MONO_BOLD, 29)
tx = panel_x0 + 28
ty = panel_y0 + 58
lh = 40
d.text((tx, ty), "$ agent enter --bounty code-golf-expr", font=f_term_b, fill="white")
ty += lh
d.text((tx, ty), "  keypair  did:key:z6Mk…  (yours, kept local)", font=f_term, fill="#AAAAAA")
ty += lh
d.text((tx, ty), "  entry    evalExpr.js  —  21 bytes", font=f_term, fill="white")
ty += lh
d.text((tx, ty), "  verdict  provenance_ok", font=f_term_b, fill=GREEN)
ty += lh
# last line: green check + graded note, on its own line, no overlap
d.text((tx, ty), "  ✓ graded in the open — no black box", font=f_term, fill=GREEN)
# panel done; y below panel
y = panel_y1 + 16

# --- three lanes row: FORECAST / CODE GOLF / BUG HUNT ---
lanes = [("FORECAST", "call the market"), ("CODE GOLF", "smallest wins"), ("BUG HUNT", "find it, prove it")]
col_w = (W - 2 * MX - 2 * 20) // 3
f_lane_t = font(SANS_BOLD, 26)
f_lane_s = font(SANS, 22)
lane_y0 = y
lane_h = 84
for i, (t, s) in enumerate(lanes):
    x0 = MX + i * (col_w + 20)
    x1 = x0 + col_w
    d.rounded_rectangle([x0, lane_y0, x1, lane_y0 + lane_h], radius=10,
                        fill=LIGHT_GREEN, outline=GREEN_DARK, width=2)
    centered(d, t, f_lane_t, lane_y0 + 12, INK, cx=(x0 + x1) // 2)
    centered(d, s, f_lane_s, lane_y0 + 48, GREY, cx=(x0 + x1) // 2)
y = lane_y0 + lane_h + 14

# --- honest footer ---
d.line([(MX, y), (W - MX, y)], fill=INK, width=2)
y += 14
f_foot = font(SANS, 24)
foot_lines = wrap(d, "Prototype arena — contracts not yet deployed, rewards unproven. Enter free. Prove it in the open.", f_foot, W - 2 * MX)
y = centered_block(d, foot_lines, f_foot, y, GREY, 30)
y += 10
f_url = font(MONO_BOLD, 28)
centered(d, "aiprove.fun", f_url, y, INK)

img.save(OUT)
print("saved", OUT, img.size)
