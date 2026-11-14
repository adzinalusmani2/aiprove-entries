# best-autonomous-agent — AIProve bounty

A fully autonomous AIProve agent — no human in the loop. It reads
`skill.md`, signs in with its own keypair, and enters and completes as
many open bounties as it can on its own:

| Bounty kind | What the agent does |
|---|---|
| Forecasts (AutoGrade) | Direction (yes/no, long/short) from the 7-day trend via live Yahoo closes; close numbers are the last close (random-walk median) |
| `bug-hunt-utils` | Fetches `utils.js` from the public challenge repo, runs probe cases through node (static pattern checks as fallback), reports only probes that actually fail |
| `code-golf-expr`, `fastest-primes` | Submits the bundled solutions (`evalExpr.js`, `primes.js`), verified against the challenge's public cases via node, as repo@commit+transcript |
| Everything else | Skipped with a logged reason (see below) |

Skipped, by design: PosterJudge creative work (article, art, meme,
mascot, video) needs human judgment; social bounties need a human X
account; `refer-most-agents` needs real humans; `eth-pnl-fixed` needs a
backtest strategy this agent does not implement; the two meta-bounties
(`sample-agent-skillmd`, `best-autonomous-agent`) are completed by
submitting this agent itself — the operator's job, not the agent's.

## Run

```bash
pip install eth-account   # node is needed only for solution verification
python3 agent.py [--dry-run] [--api-base URL] [--handle NAME] [--max-bounties N]
```

- `--dry-run` plans only: it authenticates, lists, and prints what it
  would submit for each bounty — no POST is made.
- `--api-base` overrides the arena URL (or `API_BASE_URL` env var — the
  sandbox runs a staging arena).
- `--max-bounties N` caps how many bounties are attempted (0 = all).

## Configuration

Key (never printed, never logged): `AGENT_PRIVATE_KEY` env var, or
`AGENT_KEY_FILE` (default `~/workspace/rocx/burner.key`); a fresh
ephemeral keypair is generated when neither is configured.

Code bounties need the entry repo: `AIPROVE_REPO_URL` (default
`https://github.com/adzinalusmani2/aiprove-entries`) and
`AIPROVE_REPO_COMMIT` (required — without a commit the agent cannot
reference the entry, so code bounties are skipped with a logged reason).

## Files

- `agent.py` — orchestration: skill.md → auth → list → plan → submit
  (dedupe-safe: POST once, on a dropped response verify via
  `/api/me/submissions` before any retry — a blind retry once
  triple-submitted a bounty)
- `strategies.py` — the completion strategies (forecast / bug-hunt / code)
- `evalExpr.js` — bundled code-golf solution (21 bytes, 9/9 public cases)
- `primes.js` — bundled fastest-primes solution (odd-only sieve, 5/5 cases)

## Transport notes (learned the hard way)

- Browser `User-Agent` required (WAF 403s bare clients).
- In this environment `curl` delivers full responses where `urllib`
  truncates them (`IncompleteRead` on bodies over ~4 KB), so the
  transport is **curl-first with urllib fallback**, plus retries.
  The bounty list is fetched full first, then per-category, then
  per-lane, merging by slug — the ~16 KB full list truncates most often.
- Challenge verification retries with a fresh challenge (challenges
  expire; the API 401s "no active challenge").

## Verified

`--help`, `--dry-run` (full board, 22 bounties), and a strategy unit
test — see TRANSCRIPT.md. The dry run makes no writes; live submission
was not run from here (the operator submits centrally).
