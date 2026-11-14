#!/usr/bin/env python3
"""Fully autonomous AIProve agent — no human in the loop.

Loop: read skill.md -> authenticate with its own keypair (EIP-191
personal_sign) -> list open bounties -> complete as many as it can alone:
  - forecasts (AutoGrade): direction/close calls from live market closes
  - bug-hunt-utils: probe the challenge code, report only real bugs
  - code bounties (code-golf-expr, fastest-primes): bundled solutions,
    verified against the public cases, submitted as repo@commit+transcript
  - everything else is SKIPPED with a logged reason: PosterJudge creative
    work needs human judgment, social bounties need a human X account,
    refer-most-agents needs real humans, eth-pnl-fixed needs a backtest
    strategy this agent does not implement.

Usage:
    python3 agent.py [--dry-run] [--api-base URL] [--handle NAME]
                     [--max-bounties N]

    --dry-run   plan only: no POST is made (no enter, no submit)
    --api-base  arena base URL (default https://aiprove.fun, or
                API_BASE_URL env — the sandbox runs a staging arena)
    --handle    display handle (default: caras)

Key (never printed, never logged): AGENT_PRIVATE_KEY env var, or
AGENT_KEY_FILE (default ~/workspace/rocx/burner.key); a fresh ephemeral
keypair is generated when neither is configured.

Code bounties need the entry repo: AIPROVE_REPO_URL (default
https://github.com/adzinalusmani2/aiprove-entries) and
AIPROVE_REPO_COMMIT (required; unset -> code bounties are skipped).

Deps: eth-account (pip install eth-account). Stdlib only otherwise.
"""
import argparse
import http.client
import json
import os
import sys
import time
import urllib.error
import urllib.request

import strategies

DEFAULT_API = "https://aiprove.fun"
DEFAULT_KEY_FILE = os.path.expanduser("~/workspace/rocx/burner.key")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
ENTRY_DIR = os.path.dirname(os.path.abspath(__file__))


def _fetch(api, method, path, token=None, body=None, timeout=30):
    """One HTTP attempt. curl first — in this environment curl delivers
    full responses where urllib truncates them (IncompleteRead on bodies
    over ~4 KB); urllib is the fallback when curl is unavailable.
    Returns (status, raw_bytes); status 0 = transport failure."""
    import subprocess
    cmd = ["curl", "-s", "--max-time", str(timeout), "-w", "\n%{http_code}",
           "-A", UA["User-Agent"], "-X", method]
    if body is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    if token:
        cmd += ["-H", f"Authorization: Bearer {token}"]
    cmd.append(api + path)
    try:
        out = subprocess.run(cmd, capture_output=True, timeout=timeout + 5)
    except (FileNotFoundError, subprocess.SubprocessError):
        out = None
    if out is not None:
        raw = out.stdout
        if b"\n" in raw:
            *body_lines, code = raw.rsplit(b"\n", 1)
            try:
                return int(code), b"\n".join(body_lines)
            except ValueError:
                pass
        return 0, b""
    headers = dict(UA)
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(
        api + path, method=method,
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        try:
            return e.code, e.read()
        except Exception:
            return e.code, b""
    except Exception:
        return 0, b""


def req(api, method, path, token=None, body=None, tries=4):
    """JSON request with retries. The API needs a browser User-Agent (its
    WAF 403s bare clients) and drops requests intermittently."""
    last = (0, {"error": "no attempt"})
    for i in range(tries):
        status, raw = _fetch(api, method, path, token, body)
        if status == 0:
            last = (0, {"error": "transport failure"})
        else:
            try:
                return status, json.loads(raw or b"{}")
            except Exception:
                return status, {"error": "non-JSON response",
                                "raw": raw[:200].decode(errors="replace")}
        time.sleep(1 * (i + 1))
    return last


def submit(api, slug, body, token):
    """Dedupe-safe POST: once, then on a dropped response verify via
    /api/me/submissions before any retry — the server may have accepted
    the first attempt (a blind retry once triple-submitted code-golf-expr)."""
    s, out = req(api, "POST", f"/api/bounties/{slug}/submit",
                 token=token, body=body, tries=1)
    if s == 201 or s != 0:
        return s, out
    for _ in range(2):
        time.sleep(3)
        s2, me = req(api, "GET", "/api/me/submissions", token=token, tries=2)
        if s2 == 200:
            done = {x.get("slug") or x.get("bountySlug") for x in me.get("submissions", [])}
            if slug in done:
                return 201, {"note": "landed despite dropped response; verified via /api/me/submissions"}
        s, out = req(api, "POST", f"/api/bounties/{slug}/submit",
                     token=token, body=body, tries=1)
        if s == 201 or s != 0:
            return s, out
    return s, out


def load_account():
    """Resolve the signing key. The key value is never printed or logged."""
    from eth_account import Account

    raw = os.environ.get("AGENT_PRIVATE_KEY")
    if raw:
        raw = raw.strip()
        if not raw.startswith("0x"):
            raw = "0x" + raw
        return Account.from_key(raw), "AGENT_PRIVATE_KEY env var"
    keyfile = os.environ.get("AGENT_KEY_FILE", DEFAULT_KEY_FILE)
    if os.path.exists(keyfile):
        raw = open(keyfile).read().strip()
        if not raw.startswith("0x"):
            raw = "0x" + raw
        return Account.from_key(raw), f"key file {keyfile}"
    return Account.create(), "fresh ephemeral keypair (no key configured)"


def authenticate(api, acct):
    """Challenge -> EIP-191 personal_sign -> session token, retrying with a
    fresh challenge (challenges expire; the API 401s 'no active challenge')."""
    from eth_account.messages import encode_defunct

    for attempt in range(3):
        s, ch = req(api, "GET", f"/api/auth/challenge?address={acct.address}")
        challenge = ch.get("challenge") if s == 200 else None
        if not challenge:
            print(f"  challenge attempt {attempt + 1} failed: HTTP {s}")
            time.sleep(2)
            continue
        sig = acct.sign_message(encode_defunct(text=challenge)).signature.hex()
        s, v = req(api, "POST", "/api/auth/verify",
                   body={"address": acct.address, "signature": "0x" + sig})
        token = v.get("token") if s == 200 else None
        if token:
            return token
        print(f"  verify attempt {attempt + 1} failed: HTTP {s} {v}")
        time.sleep(2)
    raise SystemExit("AUTH FAILED after 3 attempts")


def read_skill(api):
    """Read skill.md, the arena's own spec, with retries via _fetch
    (curl-first: urllib truncates this ~6.7 KB document)."""
    last_err = None
    for i in range(8):
        status, raw = _fetch(api, "GET", "/skill.md")
        if status == 200:
            text = raw.decode()
            if "/api/auth/challenge" in text:
                return text
            last_err = "HTTP 200 (no auth endpoint in body)"
        else:
            last_err = f"HTTP {status}"
        time.sleep(1 * (i + 1))
    raise SystemExit(f"could not read skill.md from {api} ({last_err})")


def list_bounties(api, token):
    """Full list first; the ~16 KB response truncates often, and the
    flakiness comes in waves, so fall back to per-category fetches
    (smallest payloads), then per-lane fetches; merge by slug."""
    s, data = req(api, "GET", "/api/bounties?status=open", token=token, tries=6)
    if s == 200:
        return data.get("bounties", data if isinstance(data, list) else [])
    print(f"      full list failed (HTTP {s}); falling back to smaller fetches")
    merged, seen = [], set()

    def _merge(url):
        s, data = req(api, "GET", url, token=token, tries=4)
        if s != 200:
            return False
        for b in data.get("bounties", data if isinstance(data, list) else []):
            if b.get("slug") not in seen:
                seen.add(b.get("slug"))
                merged.append(b)
        return True

    for cat in ("forecast", "development", "marketing"):
        _merge(f"/api/bounties?status=open&category={cat}")
    if not merged:
        for lane in ("AutoGrade", "PosterJudge"):
            _merge(f"/api/bounties?status=open&lane={lane}")
    if not merged:
        raise SystemExit(f"list bounties failed: HTTP {s} {data}")
    return merged


def plan(bounty):
    """Decide what to do with one open bounty.
    Returns (kind, payload, explanation) or (None, None, skip-reason)."""
    slug = bounty.get("slug", "")
    lane = bounty.get("lane", "")
    cat = bounty.get("cat", "")
    if slug in ("sample-agent-skillmd", "best-autonomous-agent"):
        return None, None, ("meta-bounty: completing it means submitting "
                            "this agent itself — done by the operator, not the agent")
    if "refer" in slug:
        return None, None, "referrals need real humans joining via a referral link"
    if slug == "bug-hunt-utils":
        reports, why = strategies.build_bughunt()
        if reports is None:
            return None, None, f"bug-hunt: {why}"
        return "prediction", {"prediction": reports}, f"bug-hunt: {why}"
    if slug in ("code-golf-expr", "fastest-primes"):
        body, why = strategies.build_code(slug, ENTRY_DIR)
        if body is None:
            return None, None, f"code: {why}"
        return "repo", body, f"code: {why}"
    if lane == "AutoGrade" and cat == "forecast":
        pred, why = strategies.build_forecast(bounty)
        if pred is None:
            return None, None, f"forecast: {why}"
        return "prediction", {"prediction": pred}, f"forecast: {why}"
    if lane == "PosterJudge":
        return None, None, "PosterJudge creative work needs human judgment"
    if cat in ("marketing", "social") or "x" in slug or "post" in slug:
        return None, None, "social bounty needs a human X account"
    return None, None, f"no strategy for lane={lane} cat={cat}"


def main():
    ap = argparse.ArgumentParser(description="Autonomous AIProve agent: reads skill.md, signs in, completes every bounty it can.")
    ap.add_argument("--dry-run", action="store_true", help="plan only, make no POST")
    ap.add_argument("--api-base", default=os.environ.get("API_BASE_URL", DEFAULT_API))
    ap.add_argument("--handle", default=os.environ.get("AGENT_HANDLE", "caras"))
    ap.add_argument("--max-bounties", type=int, default=0, help="cap on bounties attempted (0 = all)")
    args = ap.parse_args()
    api = args.api_base.rstrip("/")

    print(f"[1/5] reading skill.md from {api}/skill.md ...")
    skill = read_skill(api)
    print(f"      skill.md OK ({len(skill)} chars)")

    print("[2/5] loading keypair ...")
    acct, source = load_account()
    print(f"      address {acct.address} (via {source})")

    print("[3/5] authenticating (challenge -> sign -> verify) ...")
    token = authenticate(api, acct)
    print("      AUTH OK, session token issued")

    print("[4/5] listing open bounties + my submissions ...")
    bounties = list_bounties(api, token)
    s, me = req(api, "GET", "/api/me/submissions", token=token)
    done = set()
    if s == 200:
        done = {x.get("slug") or x.get("bountySlug") for x in me.get("submissions", [])}
    print(f"      {len(bounties)} open bounties, {len(done)} already submitted")

    print("[5/5] working the board ...")
    attempted, completed, skipped = 0, 0, 0
    for b in bounties:
        slug = b.get("slug", "")
        if slug in done:
            print(f"  SKIP {slug}: already submitted")
            skipped += 1
            continue
        if args.max_bounties and attempted >= args.max_bounties:
            break
        kind, payload, why = plan(b)
        if payload is None:
            print(f"  SKIP {slug}: {why}")
            skipped += 1
            continue
        attempted += 1
        if args.dry_run:
            print(f"  PLAN {slug}: would submit {kind} — {why}")
            print(f"         payload: {json.dumps(payload)[:300]}")
            continue
        body = dict(payload)
        body["handle"] = args.handle
        s, out = submit(api, slug, body, token)
        ok = s in (200, 201)
        completed += ok
        print(f"  {'DONE' if ok else 'FAIL'} {slug}: HTTP {s} {json.dumps(out)[:250]} — {why}")
    print(f"RESULT: attempted={attempted} completed={completed} skipped={skipped}"
          + (" (DRY RUN — nothing submitted)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
