# Build transcript — eth-pnl-fixed (AIProve bounty)

Agent: caras. Built 2026-11-14. Entry dir: ~/workspace/aiprove/entries/eth-pnl-fixed/
No secrets used or stored anywhere in this entry (no keys, no credentials).

## Sources read

- Brief: GET https://aiprove.fun/api/bounties/eth-pnl-fixed (curl, browser
  User-Agent; 1st attempt OK). 2,000,000 PROVE, AutoGrade, closes Fri
  2026-11-20 13:49 UTC, 93 subs. Brief: "Trade the frozen, published ETH
  one-minute dataset ... maker and taker fees, plus slippage scaled by size.
  Highest net PnL after costs wins; ties break on lower max drawdown."
- Challenge data: ~/workspace/aiprove/repo/challenges/eth-backtest/ (the
  brief's slug `eth-pnl-fixed` maps to the `eth-backtest` dir): README.md +
  bars.csv, 1,440 bars, real ETH/USDT Binance 1-min bars, window ending
  2026-11-13 12:17 UTC. README warns: "Overfitting to this sample is easy;
  a held-out tail punishes it."
- Submission protocol: ~/workspace/aiprove/repo/skill.md §4 shape A —
  repo @ commit + build transcript (transcript hashed server-side, never
  stored raw). No grader interface is published anywhere in the repo or
  skill.md (no function signature, fee schedule, capital, or position
  limits), so the entry documents its own interface and cost model
  explicitly in strategy.py / README.md.

## Data profile (measured)

```
$ python3 -c "pandas describe of bars.csv"
1440 bars, first close $2028.68, last close $1960.59, net -3.36% (-$68.09/ETH)
min close $1906.99, max close $2029.12
1-min return mean -0.002%, std 0.108%; mean |return| 0.0725%; mean bar range $2.47
first half net -$11.81, second half net -$56.00
buy & hold 1 ETH: -$68.09 gross
```

## Backtest harness (backtest.py, kept in research/)

- Signal at bar i close executes at bar i+1 open (no lookahead).
- Position target in {-1, 0, +1} ETH; exact cash+holdings accounting.
- Costs: taker fee 0.10% + slippage 0.02% + 0.01%/ETH per fill
  (0.26% per round trip, ~$5.20 at $2,000 ETH).

## Search rounds (all numbers = net PnL, base cost model)

Round 1 — baselines + canonical trend systems (backtest.py):
```
buy&hold 1 ETH      net $ -73.27  fills 1   MDD $ -124.32
always short -1 ETH net $  62.89  fills 1   MDD $  -57.66
flat                net $   0.00  fills 0
EMA cross best 30/90: net $ -53.60 fills 20 (all EMA crosses negative)
Momentum: all negative (MOM 240 -$228.98 ... MOM 10 -$1,223.37, churn)
Donchian 60: +$3.01 (12 fills); Donchian 120: -$45.70
```
Lesson: costs dominate — mean |1-min move| $2.90 < round-trip cost $5.20.
Only rare, large moves can win.

Round 2 — regime filters / hysteresis / one-sided (search2.py):
```
close vs EMA240: -$382.69 (72 fills); short-only EMA360: -$70.45
EMA12/120 hyst5: +$45.68 (4 fills) | H1 -$20.08, H2 +$60.80
EMA30/120 hyst8: +$35.86 (1 fill)  | H1 -$20.49, H2 +$50.83
Donchian 180: +$47.31 (3) | Donchian 240: +$59.49 (2), H1 $0.00, H2 +$59.49
```
H1 (first half) loses money for every trend variant; H2 holds the profit.
Donchian 240 is flat through the H1 chop — the robustness property wanted.

Round 3 — fine Donchian grid + buffers (search3.py):
```
N=120 -$45.70 | 150 +$64.27 | 180 +$47.31 | 210 +$33.64
N=240/300/360 +$59.49 (identical trades) | 480 +$23.51
Buffers on 240 only hurt (buf1 +$56.78, buf5 +$18.22).
Short-only 240: +$40.28 (1 fill).
Trades (240): short @ $2006.03 bar 739 -> long @ $1948.26 bar 1308 -> end $1960.59.
```

Round 4 — exit variants (search4.py):
```
Unshifted Donchian: $0 (no trades — close can never exceed its own window max; discarded)
EMA60 exit: +$28.72 (9 fills, churn)
Trailing stop $15: +$20.87 (9f) | $20: +$79.53 (3f, MDD -$29.61)
  $30: +$68.57 | $40: +$60.68
2-bar confirmation: +$43.22 (delayed entry)
```

Round 5 — surface + sensitivity (inline):
```
Donchian N x trail-stop (net $): trail improves EVERY N
  N=150: 68.95 | 180: 57.89 | 210: 51.06 | 240/300/360: 79.53 (trail $20)
Trail fine grid (N=240): $12 -$28.24 (15f) | $15 +$20.87 (9f) | $16 +$40.80
  $18 +$82.79 | $20 +$79.53 | $22 +$78.12 | $25 +$75.58 — smooth plateau $18-40
Cost-model sensitivity (Donchian 240 + trail $20 vs always-short vs Donchian-no-trail):
  cheap (0.05% fee): 84.63 vs 65.49 vs 64.79
  base  (0.10% fee): 79.53 vs 62.89 vs 59.49
  pricey(0.20% fee): 68.55 vs 57.31 vs 48.09  — ranking stable
```

## Final choice

Donchian 240 + trailing stop $20. Chosen over $18 (+$82.79) because $20 is the
round 1% value in the middle of a smooth plateau; the $3.26 gap is noise, and
$20 stays well above the ~$16 noise cliff.

## Final entry (strategy.py, stdlib only)

```
$ cp <repo>/challenges/eth-backtest/bars.csv ./bars.csv
$ python3 strategy.py
bars: 1440  first close $2028.68  last close $1960.59
net PnL:   $   79.53
gross PnL: $   89.73
costs:     $   10.20  (fee 0.10% + slippage 0.02% + 0.01%/ETH per fill)
fills: 3  (trades incl. final liquidation: 4)
max drawdown: $-29.61
final position: +1 ETH
trades (executed at next bar open):
  bar  739 open $ 2006.03  +0 -> -1
  bar 1082 open $ 1928.63  -1 -> +0
  bar 1308 open $ 1948.26  +0 -> +1
```

Bug found and fixed during verification: the first stdlib rewrite of
`generate_positions` signalled on a 1-bar window before the 240-bar channel
filled, giving $57.89 with 8 spurious fills. Fixed by gating signals on
`i >= CHANNEL_BARS` (matching pandas rolling(240) NaN semantics) and fixing
the window-prune off-by-one (`<` not `<=`). After the fix the stdlib
implementation reproduces the independent pandas reference exactly
(targets identical, net $79.53, fills 3, MDD -$29.61).

## Files in this entry

- strategy.py — the entry (stdlib only; `generate_positions(closes)` is the
  importable interface; `python3 strategy.py [bars.csv]` runs the backtest)
- bars.csv — the frozen published dataset (copied for self-containment)
- README.md — strategy, cost model, results, honesty notes
- TRANSCRIPT.md — this file
- research/backtest.py, search2.py, search3.py, search4.py — the search
  harness and grids behind the numbers above

## Unverified / open

- No grader interface is published: the sandbox's exact position convention,
  fee/slippage schedule, and whether it replays only these 1,440 bars or a
  held-out tail are unknown. The entry documents its own conventions; the
  graded PnL may differ from the local +$79.53.
- NOT submitted to the API and NOT pushed to GitHub by this agent (per task
  constraints — the parent does push + submit centrally).
