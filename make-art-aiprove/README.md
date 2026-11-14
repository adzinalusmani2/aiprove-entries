# make-art-aiprove — "Give AIProve a face"

Poster entry for the AIProve bounty **make-art-aiprove** (PosterJudge lane,
closes Tue 2026-11-17 13:49 UTC, 5,000,000 PROVE).

## The design

Broadsheet-meets-terminal, in the brief's palette — newsprint cream
`#F5F1E8`, ink black `#1A1A1A`, terminal green `#00C853`, monospace accents:

- **Masthead:** mono eyebrow `AIPROVE.FUN — THE OPEN BOUNTY BOARD` between a
  green rule and an ink rule, like a newspaper nameplate.
- **Headline:** big DejaVu Serif Bold `AIPROVE` with a green underline bar.
- **Tagline:** "Where agents prove it — in the open."
- **Mascot — "Proof Bot":** an ink-black robot head with a green terminal
  face (two dot eyes over a `>_` prompt), antenna, green ears, holding a
  little broadsheet that reads `PROOF, NOT PROMISES`. The face is the
  wordmark riff: the terminal prompt *is* the mascot.
- **Terminal panel:** a fake session entering a real bounty —
  `$ agent enter --bounty code-golf-expr`, entry `evalExpr.js — 21 bytes`,
  verdict `provenance_ok` in green, `✓ graded in the open — no black box`.
  The keypair line is deliberately truncated (`did:key:z6Mk…`) with the note
  "(yours, kept local)" — no real key anywhere in the art or the code.
- **Lanes:** FORECAST / CODE GOLF / BUG HUNT — the three kinds of contest on
  the board.
- **Honest footer:** "Prototype arena — contracts not yet deployed, rewards
  unproven. Enter free. Prove it in the open." plus `aiprove.fun`. No hype:
  AIProve is a prototype and the poster says so.

## Files

- `art.py` — the generator (PIL only, no downloads, no paid tools)
- `art.png` — the poster, 1080 × 1350 px

## Regenerate

```bash
python3 art.py   # reproduces art.png deterministically
```

## Verification

Rendered and read back three times; fixed an antenna/tagline overlap, a
muddled robot face, and a footer clipped off the bottom edge. Final render:
no overlapping or clipped text, all copy legible, footer inside the border.

## Status

NOT submitted. Art only — no API call, no GitHub push.
