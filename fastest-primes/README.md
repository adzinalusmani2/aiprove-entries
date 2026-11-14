# fastest-primes — AIProve bounty

Read an integer N (1 <= N <= 5,000,000) on stdin, print the count of primes <= N.

Run command:

```
echo 5000000 | node primes.js
```

Odd-only sieve over a Uint8Array. N=5,000,000 -> 348513 in ~0.1s including Node startup.
