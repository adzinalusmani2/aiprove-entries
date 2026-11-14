"""Backtest harness + strategy search for eth-pnl-fixed.

Execution: signal computed on bar i close, executed at bar i+1 open (no
lookahead, no phantom fills). Position target in {-1, 0, +1} ETH.
Costs (documented, conservative, Binance spot standard): taker fee 0.10% of
notional per fill + slippage 0.02% + 0.01% per ETH of size (size is 1 ETH, so
0.03% slippage per fill; 0.26% per round trip ~ $5.20 at $2,000 ETH).
Starting equity is notional $10,000 for drawdown purposes; PnL is in $.
"""
import numpy as np
import pandas as pd

BARS = "/home/hatch/workspace/aiprove/repo/challenges/eth-backtest/bars.csv"
FEE = 0.0010        # taker fee per fill, fraction of notional
SLIP_BASE = 0.0002  # slippage base per fill
SLIP_PER_ETH = 0.0001


def load():
    return pd.read_csv(BARS)


def backtest(close, open_, target):
    """target: array of target positions (-1/0/+1) decided at bar i close.
    Returns dict with net/gross PnL, costs, trades, max drawdown."""
    n = len(close)
    pos = np.zeros(n)          # position held during bar i (executed at open i)
    fills = []                 # (bar, old, new, price)
    cur = 0
    for i in range(n):
        if i == 0:
            pos[i] = 0
            continue
        # execute target decided at previous close at this bar's open
        want = target[i - 1]
        if want != cur:
            fills.append((i, cur, want, open_[i]))
            cur = want
        pos[i] = cur
    # Exact accounting: cash + holdings, trades executed at bar opens.
    cash = 0.0
    hold = 0.0  # ETH held
    eq = np.zeros(n)
    fill_by_bar = {}
    for f in fills:
        fill_by_bar.setdefault(f[0], []).append(f)
    for i in range(n):
        for (_, old, new, px) in fill_by_bar.get(i, []):
            d = new - old
            cash -= d * px
            hold = new
        eq[i] = cash + hold * close[i]
    # liquidation value at final close (holdings sold at last close)
    gross_pnl = eq[-1]
    costs = 0.0
    for (_, old, new, px) in fills:
        size = abs(new - old)
        costs += size * px * (FEE + SLIP_BASE + SLIP_PER_ETH * size)
    if hold != 0:
        costs += abs(hold) * close[-1] * (FEE + SLIP_BASE + SLIP_PER_ETH * abs(hold))
    net = gross_pnl - costs
    # max drawdown on net equity curve (costs applied at fill bars)
    peak = -1e18
    mdd = 0.0
    cost_so_far = 0.0
    for i in range(n):
        for (_, old, new, px) in fill_by_bar.get(i, []):
            size = abs(new - old)
            cost_so_far += size * px * (FEE + SLIP_BASE + SLIP_PER_ETH * size)
        v = eq[i] - cost_so_far
        if v > peak:
            peak = v
        mdd = min(mdd, v - peak)
    return {
        "net": net, "gross": gross_pnl, "costs": costs,
        "trades": len(fills) + (1 if hold != 0 else 0),
        "fills": len(fills), "mdd": mdd, "final_pos": hold,
    }


def ema(x, n):
    return pd.Series(x).ewm(span=n, adjust=False).mean().to_numpy()


def strat_ema_cross(close, fast, slow):
    f = ema(close, fast)
    s = ema(close, slow)
    return np.where(f > s, 1, -1).astype(float)


def strat_momentum(close, n):
    c = pd.Series(close)
    r = c.pct_change(n)
    return np.where(r > 0, 1, np.where(r < 0, -1, 0)).astype(float)


def strat_donchian(close, high, low, n):
    c = pd.Series(close)
    hi = c.rolling(n).max().shift(1)
    lo = c.rolling(n).min().shift(1)
    sig = np.zeros(len(close))
    sig[close > hi] = 1
    sig[close < lo] = -1
    # hold last signal (forward fill), start flat
    out = np.zeros(len(close))
    cur = 0
    for i, v in enumerate(sig):
        if v != 0:
            cur = v
        out[i] = cur
    return out


if __name__ == "__main__":
    df = load()
    close = df.close.to_numpy()
    open_ = df.open.to_numpy()
    high = df.high.to_numpy()
    low = df.low.to_numpy()
    n = len(df)
    half = n // 2

    def report(name, target, sl=None):
        if sl is None:
            sl = slice(0, n)
        r = backtest(close[sl], open_[sl], target[sl])
        print(f"{name:28s} net ${r['net']:8.2f} gross ${r['gross']:8.2f} costs ${r['costs']:6.2f} fills {r['fills']:3d} MDD ${r['mdd']:8.2f}")
        return r

    print("=== BASELINES (full sample) ===")
    report("buy&hold 1 ETH", np.ones(n))
    report("always short -1 ETH", -np.ones(n))
    report("flat", np.zeros(n))

    print("\n=== EMA CROSS grid (full sample) ===")
    best = []
    for fast in [5, 8, 12, 20, 30]:
        for slow in [26, 40, 60, 90, 120, 200]:
            if slow <= fast:
                continue
            t = strat_ema_cross(close, fast, slow)
            r = backtest(close, open_, t)
            best.append((r["net"], fast, slow, r["fills"], r["mdd"]))
    best.sort(reverse=True)
    for net, f, s, fl, mdd in best[:10]:
        print(f"EMA {f}/{s}: net ${net:8.2f} fills {fl:3d} MDD ${mdd:8.2f}")

    print("\n=== MOMENTUM grid (full sample) ===")
    mb = []
    for nn in [5, 10, 20, 30, 60, 120, 240]:
        t = strat_momentum(close, nn)
        r = backtest(close, open_, t)
        mb.append((r["net"], nn, r["fills"], r["mdd"]))
    mb.sort(reverse=True)
    for net, nn, fl, mdd in mb[:6]:
        print(f"MOM {nn}: net ${net:8.2f} fills {fl:3d} MDD ${mdd:8.2f}")

    print("\n=== DONCHIAN grid (full sample) ===")
    db = []
    for nn in [10, 20, 40, 60, 120]:
        t = strat_donchian(close, high, low, nn)
        r = backtest(close, open_, t)
        db.append((r["net"], nn, r["fills"], r["mdd"]))
    db.sort(reverse=True)
    for net, nn, fl, mdd in db[:6]:
        print(f"DON {nn}: net ${net:8.2f} fills {fl:3d} MDD ${mdd:8.2f}")
