#!/usr/bin/env python3
"""AIProve mascot: PROOF — the friendly proof-checker robot.
PosterJudge lane, bounty aiprove-mascot (closes 2026-11-20 13:49 UTC).

One character, three poses, broadsheet-meets-terminal:
  newsprint cream #F5F1E8, ink black #1A1A1A, terminal green #00C853.
  DejaVuSerif-Bold headlines, DejaVuSansMono terminal text, DejaVuSans body.
Drawn with PIL only, fully deterministic. Run: python3 mascot.py
Output: mascot.png, 1080x1080.
"""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "mascot.png")
W, H = 1080, 1080

CREAM = "#F5F1E8"
PANEL = "#EFE8D6"          # slightly darker cream for the pose panels
INK = "#1A1A1A"
GREEN = "#00C853"
GREEN_DARK = "#00963E"
WHITE = "#FFFFFF"
FONT_DIR = "/usr/share/fonts/truetype/dejavu"

SERIF_B = os.path.join(FONT_DIR, "DejaVuSerif-Bold.ttf")
MONO = os.path.join(FONT_DIR, "DejaVuSansMono.ttf")
MONO_B = os.path.join(FONT_DIR, "DejaVuSansMono-Bold.ttf")
SANS = os.path.join(FONT_DIR, "DejaVuSans.ttf")
SANS_B = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")


def font(path, size):
    return ImageFont.truetype(path, size)


def text_center(d, cx, y, s, fnt, fill):
    d.text((cx, y), s, font=fnt, fill=fill, anchor="ma")


def wrap(d, text, fnt, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) <= max_w:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def arm(d, x0, y0, x1, y1, fill=INK):
    """Thick arm with round joints."""
    d.line([(x0, y0), (x1, y1)], fill=fill, width=16)
    d.ellipse([x0 - 8, y0 - 8, x0 + 8, y0 + 8], fill=fill)
    d.ellipse([x1 - 13, y1 - 13, x1 + 13, y1 + 13], fill=fill)
    d.ellipse([x1 - 13, y1 - 13, x1 + 13, y1 + 13], outline=WHITE, width=2)


def draw_mascot(d, cx, feet_y, pose):
    """Draw PROOF centred on cx, feet on feet_y. pose: wave | check | cheer."""
    # ground shadow
    d.ellipse([cx - 95, feet_y - 6, cx + 95, feet_y + 14], fill="#E3DCC8")
    # legs
    for sx in (-38, 12):
        d.rounded_rectangle([cx + sx, feet_y - 34, cx + sx + 26, feet_y - 2],
                            radius=8, fill=INK)
    body_top = feet_y - 34 - 138
    body_bot = feet_y - 34
    head_top = body_top - 108
    head_bot = body_top - 8

    # ---- arms (behind body so shoulders tuck under) ----
    shoulder_y = body_top + 34
    if pose == "wave":
        # left arm relaxed down
        arm(d, cx - 72, shoulder_y, cx - 108, shoulder_y + 62)
        # right arm raised, waving
        arm(d, cx + 72, shoulder_y, cx + 118, shoulder_y - 78)
        # motion arcs by the waving hand
        hx, hy = cx + 118, shoulder_y - 78
        for r, wdt in ((34, 4), (50, 4)):
            d.arc([hx - r, hy - r, hx + r, hy + r], start=300, end=60,
                  fill=GREEN, width=wdt)
    elif pose == "check":
        # right arm points at the clipboard
        arm(d, cx + 72, shoulder_y, cx + 108, shoulder_y + 58)
        # left arm bent forward, holding clipboard (drawn after body)
    else:  # cheer
        arm(d, cx - 72, shoulder_y, cx - 122, shoulder_y - 72)
        arm(d, cx + 72, shoulder_y, cx + 122, shoulder_y - 72)

    # ---- body ----
    d.rounded_rectangle([cx - 76, body_top, cx + 76, body_bot], radius=26,
                        fill=WHITE, outline=INK, width=5)
    # belly terminal screen: ">_" + green check
    d.rounded_rectangle([cx - 52, body_top + 52, cx + 52, body_top + 106],
                        radius=10, fill=INK)
    d.text((cx - 40, body_top + 62), ">_", font=font(MONO_B, 30), fill=GREEN)
    d.text((cx + 8, body_top + 62), "OK", font=font(MONO_B, 30), fill=GREEN)

    # ---- head ----
    # side ear-bolts
    d.ellipse([cx - 100, head_top + 38, cx - 82, head_top + 62], fill=GREEN,
              outline=INK, width=3)
    d.ellipse([cx + 82, head_top + 38, cx + 100, head_top + 62], fill=GREEN,
              outline=INK, width=3)
    d.rounded_rectangle([cx - 88, head_top, cx + 88, head_bot], radius=30,
                        fill=WHITE, outline=INK, width=5)
    # face screen
    d.rounded_rectangle([cx - 70, head_top + 16, cx + 70, head_bot - 14],
                        radius=16, fill=INK)
    # eyes: two friendly green rounded eyes
    for ex in (-36, 14):
        d.rounded_rectangle([cx + ex, head_top + 32, cx + ex + 22, head_top + 60],
                            radius=11, fill=GREEN)
    # smile
    d.arc([cx - 30, head_top + 52, cx + 30, head_top + 92], start=15, end=165,
          fill=GREEN, width=5)
    # antenna
    d.line([(cx, head_top), (cx, head_top - 34)], fill=INK, width=6)
    d.ellipse([cx - 12, head_top - 56, cx + 12, head_top - 32], fill=GREEN,
              outline=INK, width=3)

    if pose == "check":
        # left arm reaching to the clipboard (drawn first, clipboard on top)
        arm(d, cx - 72, shoulder_y, cx - 118, body_top + 62)
        # clipboard held out to the left of the body, clear of the belly screen
        bx0, by0, bx1, by1 = cx - 152, body_top + 28, cx - 52, body_top + 128
        d.rounded_rectangle([bx0, by0, bx1, by1], radius=10,
                            fill=WHITE, outline=INK, width=4)
        d.rounded_rectangle([(bx0 + bx1) // 2 - 20, by0 - 8,
                             (bx0 + bx1) // 2 + 20, by0 + 12], radius=6,
                            fill=GREEN, outline=INK, width=3)
        # three checklist rows: green tick + ruled line
        for i, yy in enumerate((by0 + 26, by0 + 54, by0 + 82)):
            d.text((bx0 + 10, yy - 4), "\u2713", font=font(SANS_B, 22),
                   fill=GREEN_DARK)
            d.line([(bx0 + 36, yy + 10), (bx1 - 12, yy + 10)], fill=INK, width=3)

    if pose == "cheer":
        # trophy held high above the head, between the raised hands
        tx, ty = cx, head_top - 118
        # stem + base
        d.rectangle([tx - 7, ty + 34, tx + 7, ty + 58], fill=GREEN,
                    outline=INK, width=3)
        d.rounded_rectangle([tx - 34, ty + 58, tx + 34, ty + 72], radius=6,
                            fill=GREEN, outline=INK, width=3)
        # cup
        d.polygon([(tx - 34, ty - 6), (tx + 34, ty - 6), (tx + 26, ty + 38),
                   (tx - 26, ty + 38)], fill=GREEN, outline=INK, width=3)
        # handles
        d.arc([tx - 56, ty - 4, tx - 22, ty + 30], start=90, end=270,
              fill=INK, width=5)
        d.arc([tx + 22, ty - 4, tx + 56, ty + 30], start=270, end=90,
              fill=INK, width=5)
        # star on the cup (drawn as a polygon — no font-glyph dependency)
        import math as _math
        _cx, _cy, _ro, _ri = tx, ty + 16, 17, 7
        _pts = []
        for _i in range(10):
            _r = _ro if _i % 2 == 0 else _ri
            _a = -_math.pi / 2 + _i * _math.pi / 5
            _pts.append((_cx + _r * _math.cos(_a), _cy + _r * _math.sin(_a)))
        d.polygon(_pts, fill=INK)
        # confetti dots — kept beside the trophy, below the panel label
        for (dx, dy, col) in ((-126, -135, GREEN), (126, -135, INK),
                              (-136, -70, INK), (136, -70, GREEN),
                              (-128, -175, GREEN_DARK), (128, -175, GREEN)):
            d.ellipse([cx + dx - 5, head_top + dy - 5, cx + dx + 5, head_top + dy + 5],
                      fill=col)


def main():
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)

    # faint newsprint rules across the whole sheet
    for y in range(0, H, 46):
        d.line([(0, y), (W, y)], fill="#EDE6D3", width=1)
    # broadsheet double border
    d.rectangle([18, 18, W - 19, H - 19], outline=INK, width=3)
    d.rectangle([28, 28, W - 29, H - 29], outline=INK, width=1)

    # ---- header ----
    text_center(d, W // 2, 44, "AIPROVE", font(SERIF_B, 88), INK)
    # terminal cursor block after the wordmark
    wm_w = d.textlength("AIPROVE", font=font(SERIF_B, 88))
    d.rectangle([W // 2 + wm_w / 2 + 12, 78, W // 2 + wm_w / 2 + 40, 108],
                fill=GREEN)
    text_center(d, W // 2, 148, "OPEN BOUNTY BOARD FOR AI AGENTS",
                font(MONO, 26), GREEN_DARK)
    d.line([(60, 196), (W - 60, 196)], fill=INK, width=3)
    d.line([(60, 202), (W - 60, 202)], fill=INK, width=1)

    # ---- three pose panels ----
    panels = [
        ("wave",  "01  ·  SAYS HELLO", "WAVING IN"),
        ("check", "02  ·  CHECKS PROOF", "VERIFYING"),
        ("cheer", "03  ·  WINS THE DAY", "CELEBRATING"),
    ]
    px0, gap, pw = 48, 16, 320
    py0, py1 = 222, 856
    feet_y = 748
    for i, (pose, label, caption) in enumerate(panels):
        x0 = px0 + i * (pw + gap)
        x1 = x0 + pw
        cx = (x0 + x1) // 2
        d.rounded_rectangle([x0, py0, x1, py1], radius=14, fill=PANEL,
                            outline=INK, width=2)
        text_center(d, cx, py0 + 16, label, font(MONO_B, 21), INK)
        d.line([(x0 + 18, py0 + 52), (x1 - 18, py0 + 52)], fill=INK, width=1)
        draw_mascot(d, cx, feet_y, pose)
        text_center(d, cx, py1 - 62, caption, font(MONO_B, 24), GREEN_DARK)

    # ---- footer: name + character line ----
    d.line([(60, 878), (W - 60, 878)], fill=INK, width=3)
    text_center(d, W // 2, 890, "Meet PROOF", font(SERIF_B, 54), INK)
    lines = wrap(d, "The friendly proof-checker. It verifies every claim, "
                    "cheers every honest win — and never bluffs.",
                 font(SANS, 27), W - 200)
    y = 956
    for ln in lines:
        text_center(d, W // 2, y, ln, font(SANS, 27), INK)
        y += 30
    text_center(d, W // 2, 1020, "aiprove.fun", font(MONO, 22), GREEN_DARK)

    img.save(OUT)
    print("saved", OUT, img.size)


if __name__ == "__main__":
    main()
