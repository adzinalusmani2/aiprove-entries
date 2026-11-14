"""eth-pnl-fixed — Donchian breakout + trailing stop (AIProve bounty).

Strategy (symmetric long/short, max 1 ETH, flat when no signal):
  1. Donchian channel on closes: rolling max/min of the CLOSE over the prior
     240 bars (4 hours). A close above the 240-bar high -> target +1 ETH;
     a close below the 240-bar low -> target -1 ETH. Otherwise hold the
     previous target (breakouts are the only entry trigger).
  2. Trailing stop: once in a position, track the best close since entry
     (highest for longs, lowest for shorts). Exit to flat when the close
     retraces $20 (1% of ~$2,000 ETH) from that extreme.
  3. Execution: a signal decided at bar i's close is executed at bar i+1's
     open. No lookahead, no phantom fills.

Why this shape: on 1-minute bars the mean absolute move (~$2.90) is smaller
than a round-trip cost (~$5.20), so any strategy that trades often bleeds
fees. This system trades rarely (3 fills on the 1,440-bar sample) and only
on a genuine 4-hour breakout, then lets a trailing stop lock the move in.
It was flat through the choppy first half of the sample and caught the
second-half breakdown — the same behaviour you want on a held-out tail.

Cost model used by the local backtest (documented, conservative):
  taker fee 0.10% of notional per fill + slippage 0.02% + 0.01% per ETH of
  size (1 ETH max, so 0.03% slippage per fill; 0.26% per round trip).
  The sandbox applies its own costing; this model is only for local scoring.

Run:  python3 strategy.py [bars.csv]
  - default data file: bars.csv next to this script, else the challenge path
    challenges/eth-backtest/bars.csv in the AIProve repo.
  - prints net/gross PnL, costs, fills, max drawdown, and the trade list.

Local backtest on the frozen 1,440-bar sample (base cost model):
  net PnL +$79.53 | gross +$89.73 | costs $10.20 | fills 3 | MDD -$29.61
  baselines: buy & hold -$73.27 | always short +$62.89 | flat $0.00
  (see README.md for the full search log and sensitivity notes)

Stdlib only — no third-party imports, so the sandbox can run it anywhere.
"""

import csv
import os
import sys
from collections import deque

CHANNEL_BARS = 240       # Donchian window (bars)
TRAIL_STOP = 20.0        # trailing stop, $ from best close since entry (~1%)
MAX_POSITION = 1.0       # ETH

FEE = 0.0010             # taker fee per fill, fraction of notional
SLIP_BASE = 0.0002       # slippage base per fill
SLIP_PER_ETH = 0.0001    # slippage per ETH of size

CANDIDATE_PATHS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "bars.csv"),
    os.path.expanduser("~/workspace/aiprove/repo/challenges/eth-backtest/bars.csv"),
]


def load_bars(path=None):
    """Return (opens, highs, lows, closes) as float lists."""
    if path is None:
        for p in CANDIDATE_PATHS:
            if os.path.exists(p):
                path = p
                break
    if path is None or not os.path.exists(path):
        raise FileNotFoundError("bars.csv not found (looked next to strategy.py "
                                "and in the AIProve repo challenge dir)")
    opens, highs, lows, closes = [], [], [], []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            opens.append(float(row["open"]))
            highs.append(float(row["high"]))
            lows.append(float(row["low"]))
            closes.append(float(row["close"]))
    return opens, highs, lows, closes


def generate_positions(closes):
    """Target position (-1/0/+1 ETH) decided at each bar's close.

    Pure function of the close series: no lookahead beyond the current close.
    """
    n = len(closes)
    target = [0.0] * n
    cur = 0.0
    extreme = 0.0
    win_high = deque()   # indices of candidate maxima of close
    win_low = deque()    # indices of candidate minima of close
    for i, c in enumerate(closes):
        # window = closes[i-CHANNEL_BARS .. i-1] (prior bars only).
        # No signal until the window is full (i >= 240), matching the
        # pandas rolling(240) semantics (NaN before the window fills).
        while win_high and win_high[0] < i - CHANNEL_BARS:
            win_high.popleft()
        while win_low and win_low[0] < i - CHANNEL_BARS:
            win_low.popleft()
        if i >= 1:
            j = i - 1
            while win_high and closes[win_high[-1]] <= closes[j]:
                win_high.pop()
            win_high.append(j)
            while win_low and closes[win_low[-1]] >= closes[j]:
                win_low.pop()
            win_low.append(j)
        sig = 0.0
        if i >= CHANNEL_BARS:
            if win_high and c > closes[win_high[0]]:
                sig = 1.0
            elif win_low and c < closes[win_low[0]]:
                sig = -1.0
        if sig != 0.0 and cur == 0.0:
            cur = sig
            extreme = c
        elif cur != 0.0:
            if cur == 1.0:
                extreme = max(extreme, c)
                if c < extreme - TRAIL_STOP:
                    cur = 0.0
            else:
                extreme = min(extreme, c)
                if c > extreme + TRAIL_STOP:
                    cur = 0.0
            if sig != 0.0 and sig != cur:
                cur = sig
                extreme = c
        target[i] = cur
    return target


def run_backtest(opens, closes, target):
    """Replay: signal at bar i close executes at bar i+1 open. Returns stats."""
    n = len(closes)
    cash = 0.0
    hold = 0.0
    equity = [0.0] * n
    fills = []  # (bar, old, new, price)
    cur = 0.0
    for i in range(n):
        if i == 0:
            equity[i] = 0.0
            continue
        want = target[i - 1]
        if want != cur:
            fills.append((i, cur, want, opens[i]))
            cash -= (want - cur) * opens[i]
            hold = want
            cur = want
        equity[i] = cash + hold * closes[i]
    gross = equity[-1]
    costs = 0.0
    for (_, old, new, px) in fills:
        size = abs(new - old)
        costs += size * px * (FEE + SLIP_BASE + SLIP_PER_ETH * size)
    if hold != 0.0:
        costs += abs(hold) * closes[-1] * (FEE + SLIP_BASE + SLIP_PER_ETH * abs(hold))
    net = gross - costs
    peak = -1e18
    mdd = 0.0
    cost_so_far = 0.0
    by_bar = {}
    for f in fills:
        by_bar.setdefault(f[0], []).append(f)
    for i in range(n):
        for (_, old, new, px) in by_bar.get(i, []):
            size = abs(new - old)
            cost_so_far += size * px * (FEE + SLIP_BASE + SLIP_PER_ETH * size)
        v = equity[i] - cost_so_far
        peak = max(peak, v)
        mdd = min(mdd, v - peak)
    return {
        "net": net, "gross": gross, "costs": costs,
        "fills": len(fills), "trades": len(fills) + (1 if hold != 0 else 0),
        "mdd": mdd, "final_pos": hold, "fill_list": fills,
    }


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else None
    opens, _, _, closes = load_bars(path)
    target = generate_positions(closes)
    r = run_backtest(opens, closes, target)
    print(f"bars: {len(closes)}  first close ${closes[0]:.2f}  last close ${closes[-1]:.2f}")
    print(f"net PnL:   ${r['net']:8.2f}")
    print(f"gross PnL: ${r['gross']:8.2f}")
    print(f"costs:     ${r['costs']:8.2f}  (fee 0.10% + slippage 0.02% + 0.01%/ETH per fill)")
    print(f"fills: {r['fills']}  (trades incl. final liquidation: {r['trades']})")
    print(f"max drawdown: ${r['mdd']:.2f}")
    print(f"final position: {r['final_pos']:+.0f} ETH")
    print("trades (executed at next bar open):")
    for (bar, old, new, px) in r["fill_list"]:
        print(f"  bar {bar:4d} open ${px:8.2f}  {old:+.0f} -> {new:+.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
