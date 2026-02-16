import os
import time
import tempfile


def sequential_write_test(size_mb: int = 256) -> tuple[str, float]:
    """Writes a temp file and returns (path, speed_mbps)."""
    data = b"A" * (1024 * 1024)  # 1 MB chunk
    fd, tmp = tempfile.mkstemp(suffix=".tmp")
    os.close(fd)  # close the fd from mkstemp, we'll open it ourselves
    start = time.perf_counter()
    with open(tmp, "wb") as f:
        for _ in range(size_mb):
            f.write(data)
        f.flush()
        os.fsync(f.fileno())
    elapsed = time.perf_counter() - start
    return tmp, round(size_mb / elapsed, 2)


def sequential_read_test(path: str) -> float:
    """Reads the temp file and returns speed in MB/s."""
    size_mb = os.path.getsize(path) / (1024 * 1024)
    start = time.perf_counter()
    with open(path, "rb") as f:
        while f.read(1024 * 1024):
            pass
    elapsed = time.perf_counter() - start
    try:
        os.remove(path)
    except Exception:
        pass
    return round(size_mb / elapsed, 2)
