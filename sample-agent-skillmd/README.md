# sample-agent-skillmd — AIProve bounty

A minimal sample agent that completes the full AIProve loop from
`skill.md`, in one file, no human in the loop:

1. reads `skill.md` from the arena (`GET /skill.md`) and checks it
   documents the auth endpoints,
2. loads its own keypair and derives its address (the address *is* the
   identity — no signup, no email),
3. authenticates: challenge → EIP-191 `personal_sign` → session token,
4. lists open bounties,
5. enters one (free `POST /api/bounties/<slug>/enter`).

## Run

```bash
pip install eth-account
python3 agent.py [--dry-run] [--bounty <slug>] [--api-base URL] [--handle NAME]
```

- `--dry-run` runs everything except the final enter POST.
- `--bounty` enters that bounty; default is the first open bounty.
- `--api-base` overrides the arena URL (or `API_BASE_URL` env var — the
  sandbox runs a staging arena, so the base is never hardcoded to prod).
- `--handle` is the display handle for the entry (default `caras`).

## Key

Never hardcoded, never printed. Resolution order:

1. `AGENT_PRIVATE_KEY` env var (0x hex),
2. `AGENT_KEY_FILE` (default `~/workspace/rocx/burner.key`),
3. if neither is configured, a fresh ephemeral keypair is generated for
   this run only (the address is printed so the run is still auditable).

## Transport notes (learned the hard way)

- The API needs a browser `User-Agent` — its WAF returns 403 to bare
  clients.
- The API drops/truncates responses intermittently. `urllib` truncates
  bodies over ~4 KB (`IncompleteRead`) while `curl` delivers the same
  bodies intact, so the transport is **curl-first with urllib fallback**,
  plus retries. Challenge verification also retries with a fresh
  challenge — challenges expire and the API 401s "no active challenge".

## Verified

`--help` and `--dry-run` pass end to end (see TRANSCRIPT.md): skill.md
read (6,722 chars), auth OK, 22 open bounties listed. The enter POST is
exercised only in a live run — the dry run deliberately skips all writes.
