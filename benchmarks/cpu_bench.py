"""
CPU Benchmark Module
Single-core: prime sieve, timed operations
Multi-core: multiprocessing pool
"""

import time
import multiprocessing
from typing import Optional


def _prime_sieve(limit: int = 100_000) -> int:
    """Sieve of Eratosthenes — CPU-intensive pure Python."""
    sieve = [True] * limit
    sieve[0] = sieve[1] = False
    for i in range(2, int(limit ** 0.5) + 1):
        if sieve[i]:
            for j in range(i * i, limit, i):
                sieve[j] = False
    return sum(sieve)


def _worker(args):
    duration, limit = args
    count = 0
    end = time.time() + duration
    while time.time() < end:
        _prime_sieve(limit)
        count += 1
    return count


def single_core_benchmark(duration: int = 10) -> float:
    """Returns score: operations completed per 10 seconds (normalized to 1000)."""
    count = _worker((duration, 100_000))
    # Normalize: 100 ops/10s ≈ score of 500 (mid-range CPU)
    return round((count / duration) * 50, 1)


def multi_core_benchmark(duration: int = 10) -> float:
    """Runs benchmark on all available cores, returns combined score."""
    cores = multiprocessing.cpu_count()
    args = [(duration, 100_000)] * cores
    with multiprocessing.Pool(cores) as pool:
        results = pool.map(_worker, args)
    total_ops = sum(results)
    return round((total_ops / duration) * 50, 1)
