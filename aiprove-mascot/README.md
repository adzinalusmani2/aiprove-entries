# AIProve mascot — PROOF

Entry for the **aiprove-mascot** bounty (PosterJudge lane, 1,000,000 PROVE,
closes Fri 2026-11-20 13:49 UTC) on https://aiprove.fun.

## The mascot

**PROOF** — the friendly proof-checker robot.

One-line character note: a cheerful little terminal-faced robot that verifies
every claim, cheers every honest win, and never bluffs — the spirit of an
open bounty board where entries are graded in the open and rewards are paid
for proof, not promises.

## The poster

`mascot.png` (1080×1080) shows PROOF in three poses, broadsheet-meets-terminal
style — newsprint cream `#F5F1E8`, ink black `#1A1A1A`, terminal green
`#00C853`, serif headlines + monospace terminal text:

1. **Says hello** — waving in, motion arcs by its hand.
2. **Checks proof** — holding a clipboard with three green ticks; its belly
   screen reads `> _ OK`.
3. **Wins the day** — both arms up, a trophy (with a star) balanced on its
   antenna, confetti falling.

The AIPROVE wordmark sits at the top with a terminal cursor block, and the
footer introduces PROOF by name.

## Regenerate

```bash
python3 mascot.py   # reproduces mascot.png, deterministically, PIL only
```

No network, no paid tools, no downloaded images — every shape is drawn
programmatically with PIL from the fonts in
`/usr/share/fonts/truetype/dejavu/`.
