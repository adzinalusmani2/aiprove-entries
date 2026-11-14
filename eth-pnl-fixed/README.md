# eth-pnl-fixed — Donchian breakout + trailing stop

AIProve bounty `eth-pnl-fixed` (closes Fri 2026-11-20 13:49 UTC, 2,000,000 PROVE,
AutoGrade — highest backtest PnL on the fixed ETH dataset). Entry: this repo at
one commit + build transcript; the sandbox replays the strategy.

## Strategy

Symmetric long/short trend system, max 1 ETH, flat when no signal:

1. **Donchian breakout (240 bars = 4 hours, on closes).** A close above the
   prior 240-bar high → target +1 ETH; a close below the prior 240-bar low →
   target −1 ETH. Otherwise hold the previous target. Breakouts are the only
   entry trigger.
2. **Trailing stop ($20 ≈ 1% of ~$2,000 ETH).** Once in a position, track the
   best close since entry (highest for longs, lowest for shorts). Exit to flat
   when the close retraces $20 from that extreme.
3. **Execution.** A signal decided at bar i's close executes at bar i+1's open.
   No lookahead, no phantom fills.

## Why this shape

On 1-minute bars the mean absolute move (~$2.90) is smaller than a round-trip
cost (~$5.20), so any strategy that trades often bleeds fees — in our search,
every fast EMA/momentum variant lost money on costs alone. This system trades
rarely (3 fills on the sample) and only on a genuine 4-hour breakout, then lets
a trailing stop lock the move in. It was flat through the choppy first half of
the sample and caught the second-half breakdown — the same behaviour you want
on a held-out tail.

## Cost model (local backtest only)

Taker fee 0.10% of notional per fill + slippage 0.02% + 0.01% per ETH of size
(1 ETH max → 0.03% slippage per fill; 0.26% per round trip). Conservative,
Binance spot standard. The sandbox applies its own costing; the ranking of this
strategy vs. the baselines is stable across cheap/base/pricey cost models
(see TRANSCRIPT.md).

## Results — frozen 1,440-bar sample

| strategy | net PnL | fills | max drawdown |
|---|---|---|---|
| **Donchian 240 + trail $20 (this entry)** | **+$79.53** | 3 | -$29.61 |
| Donchian 240, no trailing stop | +$59.49 | 2 | -$49.66 |
| Always short (−1 ETH) | +$62.89 | 1 | -$57.66 |
| Buy & hold (+1 ETH) | −$73.27 | 1 | −$124.32 |
| Flat | $0.00 | 0 | $0.00 |
| Best EMA crossover (30/90) | −$53.60 | 20 | −$159.16 |

Trades: short 1 ETH @ $2,006.03 (bar 739) → flat @ $1,928.63 (bar 1082,
trailing stop) → long 1 ETH @ $1,948.26 (bar 1308) → held to $1,960.59.

## Run

```
python3 strategy.py [bars.csv]
```

Stdlib only — no third-party imports. `bars.csv` (the frozen published
dataset, copied here for self-containment) is loaded from next to the script;
pass a path explicitly to use another file. `generate_positions(closes)` is the
importable interface: it returns the target position (−1/0/+1) per bar.

## Honesty notes / overfitting

- The trailing-stop distance was selected on this sample: $18 tested slightly
  higher (+$82.79), $20 → +$79.53, $22 → +$78.12, $25 → +$75.58, $30 →
  +$68.57 — a smooth plateau, not a spike, and the stop improves every
  Donchian window tested (150–360). $20 was chosen as the round 1% value in
  the middle of the plateau, not the sample maximum. Stops below ~$16 collapse
  (noise whipsaw: $15 → +$20.87, $12 → −$28.24), so the distance must stay
  well above the ~$2.47 mean bar range.
- The Donchian window is also a plateau: 240/300/360 give identical trades and
  +$59.49 without the stop; 150 gives +$64.27 but loses in the first half.
- "Always short" (+$62.89) beats most trend variants on this sample but is a
  hardcoded directional bet, not a strategy — it would bleed on a held-out
  tail that rallies. This entry is a genuinely adaptive system instead.
- Split-sample check: first half (bars 0–719) $0.00 — the system stayed flat
  through the chop; second half (720–1439) +$79.53. The profit comes from one
  real breakdown, not from curve-fitting the noise.
- The graded PnL will differ from the local figure if the sandbox's fee /
  slippage schedule or position convention differs from the model above.
