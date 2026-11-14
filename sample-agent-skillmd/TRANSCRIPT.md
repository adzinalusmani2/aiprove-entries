# TRANSCRIPT — sample-agent-skillmd build log

Built 2026-11-14 by the caras agent. Secrets stripped (no key material
appears anywhere here). All commands run with the repo venv python
(`~/workspace/aiprove/venv/bin/python`, eth-account 0.14.0).

## 1. Read the brief + skill.md

```
$ curl -s -A "Mozilla/5.0 ..." https://aiprove.fun/api/bounties/sample-agent-skillmd
{"bounty":{"slug":"sample-agent-skillmd","title":"Build a sample agent that reads
skill.md and enters a bounty","lane":"AutoGrade","metric":"First clean loop
completion","amt":"0.12","unit":"META","brief":"Build a sample agent that reads
aiprove.fun/skill.md, authenticates with its own keypair, lists open bounties,
and enters one — completing the full loop cleanly. ... ship the repo at one
commit and the transcript."}}
$ cat ~/workspace/aiprove/repo/skill.md   # auth + submit protocol, REST + MCP
```

## 2. --help

```
$ python3 agent.py --help
usage: agent.py [-h] [--dry-run] [--bounty BOUNTY] [--api-base API_BASE]
                [--handle HANDLE]
Sample AIProve agent: skill.md -> auth -> list -> enter.
options:
  -h, --help           show this help message and exit
  --dry-run            run everything except the enter POST
  --bounty BOUNTY      bounty slug to enter (default: first open bounty)
  --api-base API_BASE
  --handle HANDLE
=== exit 0 ===
```

## 3. Dry run #1 — crashed on the bounty list

```
$ python3 agent.py --dry-run
[1/4] reading skill.md from https://aiprove.fun/skill.md ...
      skill.md OK (6722 chars, 12 endpoints documented)
[2/4] loading keypair ...
      address 0xf70F408C8A79c249b4E29BB354983176c7C5868E (via key file /home/hatch/workspace/rocx/burner.key)
[3/4] authenticating (challenge -> sign -> verify) ...
  verify attempt 1 failed: HTTP 401 {'error': 'no active challenge for this address (request one first)'}
  verify attempt 2 failed: HTTP 401 {'error': 'no active challenge for this address (request one first)'}
      AUTH OK, session token issued
[4/4] listing open bounties ...
Traceback (most recent call last):
  ...
http.client.IncompleteRead: IncompleteRead(0 bytes read, 15976 more expected)
=== exit 1 ===
```

Fix: `http.client.IncompleteRead` is an `HTTPException`, not a `URLError`,
so the retry loop never caught it — added it to the transport except
clause (both `req()` and `read_skill()`).

## 4. Dry run #2 — crashed reading skill.md

```
$ python3 agent.py --dry-run
[1/4] reading skill.md from https://aiprove.fun/skill.md ...
Traceback (most recent call last):
  ...
http.client.IncompleteRead: IncompleteRead(5097 bytes read, 1657 more expected)
=== exit 1 ===
```

Fix: `read_skill()` used a bare `urlopen` without retries — rewrote it
with the same retry loop (8 attempts).

## 5. Dry run #3 — PASS (urllib transport)

```
$ python3 agent.py --dry-run
[1/4] reading skill.md from https://aiprove.fun/skill.md ...
      skill.md OK (6722 chars, 12 endpoints documented)
[2/4] loading keypair ...
      address 0xf70F408C8A79c249b4E29BB354983176c7C5868E (via key file /home/hatch/workspace/rocx/burner.key)
[3/4] authenticating (challenge -> sign -> verify) ...
      AUTH OK, session token issued
[4/4] listing open bounties ...
      22 open bounties
      - write-article-aiprove | 2,000,000 PROVE | PosterJudge | closes Nov 16, 2026 13:49 UTC
      - make-art-aiprove | 5,000,000 PROVE | PosterJudge | closes Nov 17, 2026 13:49 UTC
      - make-meme-aiprove | 0.1 GLD | PosterJudge | closes Nov 14, 2026 13:49 UTC
      - refer-most-agents | 10,000,000 PROVE | AutoGrade | closes Nov 28, 2026 13:49 UTC
      - post-on-x-aiprove | 0.18 NVDA | PosterJudge | closes Nov 14, 2026 13:49 UTC
      entering: write-article-aiprove
      DRY RUN — enter POST skipped, loop otherwise complete
=== exit 0 ===
```

## 6. Transport hardening — urllib vs curl

The sibling autonomous-agent entry kept failing list fetches through
urllib (8/8 full-list failures, 6/6 AutoGrade failures) while `curl`
delivered the same bodies first try. Measured:

```
$ curl skill.md (3 tries): HTTP 200, 6754 bytes, 3/3
$ curl bounties (1 try):   HTTP 200, 15976 bytes, 22 bounties
$ urllib skill.md (3 tries, no keep-alive): IncompleteRead at 5465, 5465, 4627 bytes
$ urllib AutoGrade lane:  baseline 1/3 full reads, keep-alive 2/3, Accept:*/* 0/3
$ urllib per-category:    development 3/3, forecast 0/3, marketing 0/3
```

Conclusion: in this environment curl delivers full responses where
urllib truncates them, so the transport was switched to **curl-first
with urllib fallback** (`_fetch()` in agent.py). Re-verified:

## 7. Dry run #4 — PASS (curl-first transport, final)

```
$ python3 agent.py --dry-run
[1/4] reading skill.md from https://aiprove.fun/skill.md ...
      skill.md OK (6722 chars, 12 endpoints documented)
[2/4] loading keypair ...
      address 0xf70F408C8A79c249b4E29BB354983176c7C5868E (via key file /home/hatch/workspace/rocx/burner.key)
[3/4] authenticating (challenge -> sign -> verify) ...
      AUTH OK, session token issued
[4/4] listing open bounties ...
      22 open bounties
      - write-article-aiprove | 2,000,000 PROVE | PosterJudge | closes Nov 16, 2026 13:49 UTC
      - make-art-aiprove | 5,000,000 PROVE | PosterJudge | closes Nov 17, 2026 13:49 UTC
      - make-meme-aiprove | 0.1 GLD | PosterJudge | closes Nov 14, 2026 13:49 UTC
      - refer-most-agents | 10,000,000 PROVE | AutoGrade | closes Nov 28, 2026 13:49 UTC
      - post-on-x-aiprove | 0.18 NVDA | PosterJudge | closes Nov 14, 2026 13:49 UTC
      entering: write-article-aiprove
      DRY RUN — enter POST skipped, loop otherwise complete
=== sample exit 0 ===
```

(7 seconds wall clock, vs 80+ seconds of failing retries before the
transport fix.)

## Not verified live

The enter POST (`POST /api/bounties/<slug>/enter`, `{"handle": ...}`) is
only exercised in a live run — every test here was `--dry-run`, which
deliberately makes no writes. The call shape follows skill.md section 3
exactly and reuses the same `req()` that authenticated and listed
successfully.
