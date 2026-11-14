"""Round 4: Donchian 240 + exit variants (trailing stop, fast exit, confirmation)."""
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
    r = backtest(close, open_, target)
    r1 = backtest(close[:half], open_[:half], target[:half])
    r2 = backtest(close[half:], open_[half:], target[half:])
    print(f"{name:36s} FULL ${r['net']:8.2f} (fills {r['fills']:3d} MDD ${r['mdd']:7.2f}) | H1 ${r1['net']:7.2f} | H2 ${r2['net']:7.2f}")
    return r


def donchian_raw(close, N, shift=True):
    c = pd.Series(close)
    if shift:
        hi = c.rolling(N).max().shift(1)
        lo = c.rolling(N).min().shift(1)
    else:
        hi = c.rolling(N).max()
        lo = c.rolling(N).min()
    sig = np.zeros(n)
    sig[close > hi] = 1
    sig[close < lo] = -1
    return sig


def hold(sig):
    out = np.zeros(n)
    cur = 0
    for i, v in enumerate(sig):
        if v != 0:
            cur = v
        out[i] = cur
    return out


print("=== (d) Donchian 240 unshifted (signal uses current bar extremes) ===")
for N in [180, 240, 300]:
    report(f"Donchian {N} unshifted", hold(donchian_raw(close, N, shift=False)))

print("\n=== (a) Donchian 240 entry + exit to flat on EMA60 cross ===")
for N in [240]:
    sig = donchian_raw(close, N)
    e60 = ema(close, 60)
    t = np.zeros(n)
    cur = 0
    for i in range(n):
        if sig[i] != 0:
            cur = sig[i]
        elif cur == 1 and close[i] < e60[i]:
            cur = 0
        elif cur == -1 and close[i] > e60[i]:
            cur = 0
        t[i] = cur
    report(f"Donchian {N} + EMA60 exit", t)

print("\n=== (b) Donchian 240 + trailing stop $X from entry extreme ===")
for stop in [15, 20, 30, 40]:
    sig = donchian_raw(close, 240)
    t = np.zeros(n)
    cur = 0
    entry = 0.0
    extreme = 0.0
    for i in range(n):
        if sig[i] != 0 and cur == 0:
            cur = sig[i]
            entry = close[i]
            extreme = close[i]
        elif cur != 0:
            if cur == 1:
                extreme = max(extreme, close[i])
                if close[i] < extreme - stop:
                    cur = 0
            else:
                extreme = min(extreme, close[i])
                if close[i] > extreme + stop:
                    cur = 0
            if sig[i] != 0 and sig[i] != cur:
                cur = sig[i]
                entry = close[i]
                extreme = close[i]
        t[i] = cur
    report(f"Donchian 240 + trail ${stop}", t)

print("\n=== (e) Donchian 240 + 2-bar confirmation ===")
sig = donchian_raw(close, 240)
t = np.zeros(n)
cur = 0
pend = 0
cnt = 0
for i in range(n):
    if sig[i] != 0 and sig[i] != cur:
        if sig[i] == pend:
            cnt += 1
        else:
            pend = sig[i]
            cnt = 1
        if cnt >= 2:
            cur = sig[i]
            pend = 0
            cnt = 0
    else:
        pend = 0
        cnt = 0
    t[i] = cur
report("Donchian 240 confirm-2", t)
