import time
import numpy as np


def read_bandwidth_test(size_mb: int = 512) -> float:
    """Returns read bandwidth in GB/s."""
    elements = (size_mb * 1024 * 1024) // 8
    arr = np.ones(elements, dtype=np.float64)
    start = time.perf_counter()
    _ = arr.sum()
    elapsed = time.perf_counter() - start
    return round((size_mb / 1024) / elapsed, 2)


def write_bandwidth_test(size_mb: int = 512) -> float:
    """Returns write bandwidth in GB/s."""
    elements = (size_mb * 1024 * 1024) // 8
    start = time.perf_counter()
    arr = np.ones(elements, dtype=np.float64)
    elapsed = time.perf_counter() - start
    return round((size_mb / 1024) / elapsed, 2)
