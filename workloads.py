"""
Three workloads over the same domain (synthetic HTTP log analysis)
to expose CPU-bound, I/O-bound, and memory-heavy execution profiles.
"""

import re
import random
import time
import urllib.request

LOG_PATTERN = re.compile(r'"GET (\S+) HTTP/\S+" (\d+) (\d+)')

PATHS = ["/home", "/api/data", "/login", "/logout", "/search", "/static/app.js"]
STATUSES = [200, 200, 200, 301, 404, 500]


def generate_logs(n=20_000):
    rng = random.Random(42)
    lines = []
    for _ in range(n):
        path = rng.choice(PATHS)
        status = rng.choice(STATUSES)
        size = rng.randint(100, 9_999)
        lines.append(
            f'127.0.0.1 - - [01/Jan/2025:00:00:00 +0000] "GET {path} HTTP/1.1" {status} {size}'
        )
    return lines


def cpu_workload(logs):
    """Parse log lines and count requests per status code. CPU-bound."""
    counts = {}
    for line in logs:
        m = LOG_PATTERN.search(line)
        if m:
            status = m.group(2)
            counts[status] = counts.get(status, 0) + 1
    return counts


def network_workload(n_requests=12, url="http://127.0.0.1:5001/logs"):
    """Fetch log batches from a slow localhost endpoint. I/O-bound."""
    counts = {}
    for _ in range(n_requests):
        with urllib.request.urlopen(url, timeout=10) as resp:
            for line in resp.read().decode().splitlines():
                m = LOG_PATTERN.search(line)
                if m:
                    status = m.group(2)
                    counts[status] = counts.get(status, 0) + 1
    return counts


def network_workload_fast(n_requests=12):
    return network_workload(n_requests, url="http://127.0.0.1:5001/logs/fast")


def memory_workload(logs):
    """Parse logs into full record objects and build a per-status index. Memory-heavy."""
    records = []
    for line in logs:
        m = LOG_PATTERN.search(line)
        if m:
            records.append(
                {
                    "raw": line,
                    "path": m.group(1),
                    "status": m.group(2),
                    "bytes": int(m.group(3)),
                }
            )

    index = {}
    for rec in records:
        index.setdefault(rec["status"], []).append(rec)

    return {status: len(entries) for status, entries in index.items()}
