"""Round 2: regime-filtered / low-churn variants + split-sample validation."""
import numpy as np
import pandas as pd
from backtest import load, backtest, ema

df = load()
close = df.close.to_numpy()
open_ = df.open.to_numpy()
high = df.high.to_numpy()
low = df.low.to_numpy()
n = len(df)
half = n // 2


def report(name, target):
    r_full = backtest(close, open_, target)
    r1 = backtest(close[:half], open_[:half], target[:half])
    r2 = backtest(close[half:], open_[half:], target[half:])
    print(f"{name:34s} FULL ${r_full['net']:8.2f} (fills {r_full['fills']:3d} MDD ${r_full['mdd']:7.2f}) | H1 ${r1['net']:7.2f} | H2 ${r2['net']:7.2f}")
    return r_full


print("=== price vs EMA(N): always-in ===")
for N in [60, 120, 240, 360, 480]:
    e = ema(close, N)
    t = np.where(close > e, 1, -1).astype(float)
    report(f"close vs EMA{N}", t)

print("\n=== price vs EMA(N): one-sided (short only / long only) ===")
for N in [120, 240, 360]:
    e = ema(close, N)
    report(f"short-only EMA{N}", np.where(close < e, -1, 0).astype(float))
    report(f"long-only EMA{N}", np.where(close > e, 1, 0).astype(float))

print("\n=== EMA cross + hysteresis: flip only if |fast-slow| > k ===")
for fast, slow, k in [(12, 60, 3), (12, 60, 5), (20, 60, 5), (12, 120, 5), (20, 120, 8), (30, 120, 8), (12, 60, 8)]:
    f = ema(close, fast)
    s = ema(close, slow)
    diff = f - s
    t = np.zeros(n)
    cur = 0
    for i, d in enumerate(diff):
        if d > k and cur != 1:
            cur = 1
        elif d < -k and cur != -1:
            cur = -1
        t[i] = cur
    report(f"EMA{fast}/{slow} hyst{k}", t)

print("\n=== regime filter: EMA(240) direction gates EMA(20/60) cross ===")
e240 = ema(close, 240)
f = ema(close, 20)
s = ema(close, 60)
cross = np.where(f > s, 1, -1)
regime = np.where(close > e240, 1, -1)
t = np.where(regime == cross, cross, 0).astype(float)
report("regime-gated cross 20/60|240", t)
f = ema(close, 12)
s = ema(close, 60)
cross = np.where(f > s, 1, -1)
t = np.where(regime == cross, cross, 0).astype(float)
report("regime-gated cross 12/60|240", t)

print("\n=== Donchian wide ===")
for N in [90, 180, 240]:
    c = pd.Series(close)
    hi = c.rolling(N).max().shift(1)
    lo = c.rolling(N).min().shift(1)
    sig = np.zeros(n)
    sig[close > hi] = 1
    sig[close < lo] = -1
    out = np.zeros(n)
    cur = 0
    for i, v in enumerate(sig):
        if v != 0:
            cur = v
        out[i] = cur
    report(f"Donchian {N}", out)

print("\n=== ATR filter on EMA cross: only trade when ATR(60) > $x ===")
tr = np.maximum(high - low, np.maximum(np.abs(high - np.roll(close, 1)), np.abs(low - np.roll(close, 1))))
atr = pd.Series(tr).rolling(60).mean().to_numpy()
for fast, slow, k in [(12, 60, 2.0), (12, 60, 3.0), (20, 60, 3.0)]:
    f = ema(close, fast)
    s = ema(close, slow)
    raw = np.where(f > s, 1, -1).astype(float)
    t = np.where(atr > k, raw, 0)
    report(f"EMA{fast}/{slow} ATR>{k}", t)
