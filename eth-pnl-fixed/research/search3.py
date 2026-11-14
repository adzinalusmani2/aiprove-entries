"""Round 3: fine Donchian grid + buffers + trade inspection."""
import numpy as np
import pandas as pd
from backtest import load, backtest

df = load()
close = df.close.to_numpy()
open_ = df.open.to_numpy()
n = len(df)
half = n // 2


def donchian(close, N, buf=0.0, short_only=False):
    c = pd.Series(close)
    hi = c.rolling(N).max().shift(1)
    lo = c.rolling(N).min().shift(1)
    sig = np.zeros(n)
    sig[close > hi + buf] = 1
    sig[close < lo - buf] = -1
    if short_only:
        sig[sig == 1] = 0
    out = np.zeros(n)
    cur = 0
    for i, v in enumerate(sig):
        if v != 0:
            cur = v
        out[i] = cur
    return out


def report(name, target):
    r = backtest(close, open_, target)
    r1 = backtest(close[:half], open_[:half], target[:half])
    r2 = backtest(close[half:], open_[half:], target[half:])
    print(f"{name:32s} FULL ${r['net']:8.2f} (fills {r['fills']:3d} MDD ${r['mdd']:7.2f}) | H1 ${r1['net']:7.2f} | H2 ${r2['net']:7.2f}")
    return r


print("=== Donchian fine grid ===")
for N in [120, 150, 180, 210, 240, 300, 360, 480]:
    report(f"Donchian {N}", donchian(close, N))

print("\n=== Donchian 240 + buffer ===")
for buf in [0, 1, 2, 3, 5]:
    report(f"Donchian 240 buf{buf}", donchian(close, 240, buf))
for buf in [0, 2, 5]:
    report(f"Donchian 180 buf{buf}", donchian(close, 180, buf))

print("\n=== Donchian short-only ===")
for N in [180, 240, 300]:
    report(f"Donchian {N} short-only", donchian(close, N, short_only=True))

print("\n=== trade inspection: Donchian 240 ===")
t = donchian(close, 240)
# reproduce fills
cur = 0
for i in range(n):
    if i == 0:
        continue
    want = t[i - 1]
    if want != cur:
        print(f"bar {i:4d} open ${open_[i]:8.2f} close ${close[i]:8.2f} {cur:+.0f} -> {want:+.0f}")
        cur = want
print("final target", t[-1])
print("price at bars 700-720:", close[700:721:4])
print("price at bars 1000-1020:", close[1000:1021:4])
print("price at bars 1400-1439:", close[1400:1440:8])
