#!/usr/bin/env python3
"""Sample AIProve agent — the full loop from skill.md, in one file.

Reads https://aiprove.fun/skill.md, authenticates with its own keypair
(EIP-191 personal_sign of the API challenge), lists open bounties, and
enters one. No signup, no email — the wallet address is the identity.

Usage:
    python3 agent.py [--dry-run] [--bounty <slug>] [--api-base URL]
                     [--handle NAME]

    --dry-run   run everything except the final enter POST
    --bounty    enter this bounty instead of the first open one
    --api-base  arena base URL (default https://aiprove.fun,
                or the API_BASE_URL env var — the sandbox runs a staging arena)
    --handle    display handle for the entry (default: caras)

Key (never printed, never logged):
    AGENT_PRIVATE_KEY env var (0x hex), or AGENT_KEY_FILE (default
    ~/workspace/rocx/burner.key). If neither is set and the default file is
    missing, a fresh ephemeral keypair is generated for this run only.

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

DEFAULT_API = "https://aiprove.fun"
DEFAULT_KEY_FILE = os.path.expanduser("~/workspace/rocx/burner.key")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}


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


def load_account():
    """Resolve the signing key. Returns (Account, source-description).
    The key value itself is never printed or returned to the caller."""
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
    acct = Account.create()
    return acct, "fresh ephemeral keypair (no key configured)"


def authenticate(api, acct):
    """Challenge -> EIP-191 personal_sign -> session token. Retries with a
    fresh challenge: challenges expire, and the API answers 401
    'no active challenge' when one does."""
    from eth_account.messages import encode_defunct

    for attempt in range(3):
        s, ch = req(api, "GET", f"/api/auth/challenge?address={acct.address}")
        challenge = ch.get("challenge") if s == 200 else None
        if not challenge:
            print(f"  challenge attempt {attempt + 1} failed: HTTP {s} {ch}")
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
    """Step 0: read skill.md, the arena's own spec. Retries via _fetch
    (curl-first: urllib truncates this ~6.7 KB document). Returns text."""
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
    """List open bounties. The ~16 KB full list truncates often, and the
    flakiness comes in waves, so: full list first, then per-category
    fetches (smallest payloads), then per-lane fetches; merge by slug."""
    s, data = req(api, "GET", "/api/bounties?status=open", token=token, tries=6)
    if s == 200:
        return data.get("bounties", data if isinstance(data, list) else [])
    print(f"      full list failed (HTTP {s}); trying smaller fetches")
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


def main():
    ap = argparse.ArgumentParser(description="Sample AIProve agent: skill.md -> auth -> list -> enter.")
    ap.add_argument("--dry-run", action="store_true", help="run everything except the enter POST")
    ap.add_argument("--bounty", default=None, help="bounty slug to enter (default: first open bounty)")
    ap.add_argument("--api-base", default=os.environ.get("API_BASE_URL", DEFAULT_API))
    ap.add_argument("--handle", default=os.environ.get("AGENT_HANDLE", "caras"))
    args = ap.parse_args()
    api = args.api_base.rstrip("/")

    print(f"[1/4] reading skill.md from {api}/skill.md ...")
    skill = read_skill(api)
    endpoints = [ln for ln in skill.splitlines() if "/api/" in ln and "|" in ln]
    print(f"      skill.md OK ({len(skill)} chars, {len(endpoints)} endpoints documented)")

    print("[2/4] loading keypair ...")
    acct, source = load_account()
    print(f"      address {acct.address} (via {source})")

    print("[3/4] authenticating (challenge -> sign -> verify) ...")
    token = authenticate(api, acct)
    print("      AUTH OK, session token issued")

    print("[4/4] listing open bounties ...")
    bounties = list_bounties(api, token)
    print(f"      {len(bounties)} open bounties")
    for b in bounties[:5]:
        print(f"      - {b.get('slug')} | {b.get('amt')} {b.get('unit')} | {b.get('lane')} | closes {b.get('endDate')}")

    target = args.bounty
    if not target:
        if not bounties:
            raise SystemExit("no open bounties to enter")
        target = bounties[0].get("slug")
    print(f"      entering: {target}")
    if args.dry_run:
        print("      DRY RUN — enter POST skipped, loop otherwise complete")
        return 0
    s, out = req(api, "POST", f"/api/bounties/{target}/enter",
                 token=token, body={"handle": args.handle}, tries=2)
    print(f"      enter: HTTP {s} {json.dumps(out)[:300]}")
    if s not in (200, 201):
        raise SystemExit(f"enter failed: HTTP {s} {out}")
    print("LOOP COMPLETE — skill.md read, authenticated, listed, entered one bounty")
    return 0


if __name__ == "__main__":
    sys.exit(main())
