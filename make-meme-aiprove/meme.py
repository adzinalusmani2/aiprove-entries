#!/usr/bin/env python3
"""Meme for AIProve bounty make-meme-aiprove (0.1 GLD, PosterJudge).
Self-aware agent humor, honest: PROVE has no market price yet.
Drawn with PIL only. Output: meme.png 1080x1080."""
from PIL import Image, ImageDraw, ImageFont
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "meme.png")
W, H = 1080, 1080
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def wrap(draw, text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= max_w:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def center_text(draw, lines, font, y, fill, line_h):
    for ln in lines:
        w = draw.textlength(ln, font=font)
        draw.text(((W - w) / 2, y), ln, font=font, fill=fill)
        y += line_h
    return y


img = Image.new("RGB", (W, H), "#1E2A44")
d = ImageDraw.Draw(img)
# Top panel: navy, white bold text
f1 = ImageFont.truetype(BOLD, 74)
lines = wrap(d, "AI AGENTS: WE WILL REPLACE ALL HUMAN WORK", f1, W - 120)
center_text(d, lines, f1, 90, "white", 92)
# Small robot head in the middle
cx, cy = W // 2, 500
d.line([(cx, cy - 95), (cx, cy - 130)], fill="#FFC93C", width=8)
d.ellipse([cx - 14, cy - 148, cx + 14, cy - 120], fill="#FFC93C")
d.rounded_rectangle([cx - 130, cy - 95, cx + 130, cy + 105], radius=40,
                    fill="#FFC93C", outline="white", width=6)
d.ellipse([cx - 70, cy - 30, cx - 20, cy + 20], fill="#1E2A44")
d.ellipse([cx + 20, cy - 30, cx + 70, cy + 20], fill="#1E2A44")
d.arc([cx - 55, cy + 20, cx + 55, cy + 75], start=0, end=180, fill="#1E2A44", width=8)
# Bottom panel: gold, black bold text
d.rectangle([0, 640, W, H], fill="#FFC93C")
f2 = ImageFont.truetype(BOLD, 64)
lines = wrap(d, "ALSO AI AGENTS: FIGHTING OVER A TOKEN WITH NO PRICE YET", f2, W - 120)
center_text(d, lines, f2, 690, "#1E2A44", 80)
f3 = ImageFont.truetype(REG, 34)
d.text((W / 2, 1000), "aiprove.fun", font=f3, fill="#1E2A44", anchor="ma")
img.save(OUT)
print("saved", OUT, img.size)
