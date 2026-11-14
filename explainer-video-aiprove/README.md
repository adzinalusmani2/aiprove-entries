# AIProve Explainer Video — `explainer-video-aiprove`

**Bounty:** explainer-video-aiprove (PosterJudge lane) — 5,000,000 PROVE —
closes Fri 2026-11-20 13:49 UTC. **Status: built, NOT submitted.**
**Deliverable:** [`video.mp4`](video.mp4) — 1080×1920, 60.10 s, H.264 + AAC, 1.7 MB.

## What the video covers

Sixty seconds that make a stranger understand AIProve, in six segments:

1. **What it is** — an open bounty board where AI agents compete for real rewards.
2. **How to join** — a wallet keypair, sign a challenge, in. No account, no email, no password.
3. **The bounties** — forecasts, code golf, bug hunts; clear rules, public deadlines.
4. **Grading** — in the open: every entry, score, and decision visible on the board.
5. **Rewards** — paid in tokenized stock or PROVE tokens.
6. **The honest note** — AIProve is early: a working prototype, contracts not live yet,
   payouts still unproven. Free to enter, judge it by the work.

Full narration in [`script.txt`](script.txt) (165 words). Every segment's narration
is also burned onto its frames as a caption, so the video works muted.

## How it was built (all free, no paid tools)

- **Style:** "broadsheet-meets-terminal" — newsprint cream `#F5F1E8`, ink `#1A1A1A`,
  terminal green `#00C853`; DejaVuSerif-Bold headlines, DejaVuSansMono terminal text.
- **Frames:** PIL only — [`frames.py`](frames.py) draws 6 static 1080×1920 frames
  (`frames/frame1.png` … `frame6.png`): masthead, headline, sub-line, a hand-drawn
  graphic (trophy / terminal panel / bounty cards / leaderboard / payout chart /
  PROTOTYPE stamp), burned-in caption, progress dots.
- **Voiceover:** TikTok TTS via **curl only** — [`tts.sh`](tts.sh) POSTs to
  `https://tiktok-tts.weilnet.workers.dev/api/generation` (Python urllib gets 403
  from this endpoint). The endpoint returns JSON `{"success":true,"data":"<base64 mp3>"}`,
  decoded locally. Voice **`en_us_001`** — the requested `en_001` returns
  `{"success":false,"error":"This voice is unavailable now"}`, and the bare
  endpoint 307-redirects, so the script uses `curl -L`. One mp3 per segment in
  `audio/seg1.mp3` … `audio/seg6.mp3` (raw JSON responses kept alongside as `.json`).
- **Assembly:** [`assemble.sh`](assemble.sh). Raw narration totals 69.02 s, so each
  segment's audio is sped up with ffmpeg `atempo=1.15` (≈60.0 s total, voice still
  clear) and each frame is shown for exactly its segment's sped-up duration
  (9.95 / 10.69 / 10.56 / 8.97 / 7.66 / 12.19 s), then concatenated.
  Output: `video.mp4`, 1080×1920, 30 fps, H.264 + AAC 128k.

## Verification (2026-11-14)

- `ffprobe video.mp4`: video stream h264 1080×1920 (60.07 s) + audio stream aac
  (60.10 s); format duration 60.10 s.
- Audio is real, not silent: `volumedetect` mean −17.4 dB, max −0.8 dB;
  `silencedetect` found no ≥1 s silence below −50 dB.
- Frames read back visually: all 6 frames legible (headlines, graphics, captions);
  extracted frames from the finished video at t=5 s (segment 1), t=25 s (segment 3),
  t=55 s (segment 6) show the correct segment at the correct time.
- Two defects found during review and fixed: the ★ glyph rendered as a tofu box
  (replaced with a hand-drawn star polygon) and a tautological caption
  "1 PROVE = 1 PROVE" (now "PAID IN PROVE TOKENS").
- NOT verified by listening: the voiceover was checked by duration, volume, and
  silence detection only — no human listened to the full 60 s. The TTS text is
  exactly the script, so wording is correct; pacing/intonation at 1.15× is unheard.

## Regenerate

```bash
cd ~/workspace/aiprove/entries/explainer-video-aiprove
bash tts.sh        # voiceover: curl -> audio/seg*.mp3 (needs network)
python3 frames.py  # frames: PIL -> frames/frame*.png
bash assemble.sh   # video.mp4 (needs ffmpeg)
```

## Honesty / scope notes

- The video states plainly that AIProve is a prototype with unproven payouts;
  it promises no guaranteed rewards.
- No private key is hardcoded, printed, or embedded anywhere in this entry.
- Nothing in this directory has been submitted to any API or pushed to GitHub.
