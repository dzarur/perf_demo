"""
Automated measurement harness.

Usage:
  python3 measure.py           # run all workloads
  python3 measure.py cpu
  python3 measure.py network
  python3 measure.py memory
"""

import sys
import time
import tracemalloc

from workloads import (
    generate_logs,
    cpu_workload,
    memory_workload,
    network_workload,
    network_workload_fast,
)

HEADER = f"{'Workload':<26} {'Wall (s)':>9} {'CPU (s)':>9} {'CPU/Wall':>9} {'Peak mem':>11}"
RULE = "-" * len(HEADER)


def measure(label, fn, *args, **kwargs):
    tracemalloc.start()
    t_wall_0 = time.perf_counter()
    t_cpu_0 = time.process_time()

    result = fn(*args, **kwargs)

    t_cpu_1 = time.process_time()
    t_wall_1 = time.perf_counter()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    wall = t_wall_1 - t_wall_0
    cpu = t_cpu_1 - t_cpu_0
    ratio = cpu / wall if wall > 0 else 0.0
    mem_kb = peak / 1024

    print(f"{label:<26} {wall:>9.3f} {cpu:>9.3f} {ratio:>8.1%} {mem_kb:>10.1f}K")
    return {"label": label, "wall": wall, "cpu": cpu, "ratio": ratio, "mem_kb": mem_kb}


def run_cpu(logs):
    return measure("cpu_workload", cpu_workload, logs)


def run_memory(logs):
    return measure("memory_workload", memory_workload, logs)


def run_network():
    rows = []
    try:
        rows.append(measure("network (slow)", network_workload))
        rows.append(measure("network (fast)", network_workload_fast))
    except OSError as e:
        print(f"  [network skipped — is server.py running?  {e}]")
    return rows


def collect_all(logs):
    """Return all metrics as a list of dicts (used by visualize.py)."""
    rows = [run_cpu(logs), run_memory(logs)]
    rows.extend(run_network())
    return rows


def run_all(logs):
    print(HEADER)
    print(RULE)
    collect_all(logs)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    if target != "network":
        print("Generating 20,000 log lines...", flush=True)
        logs = generate_logs()
    else:
        logs = None

    print()
    print(HEADER)
    print(RULE)

    if target == "cpu":
        run_cpu(logs)
    elif target == "memory":
        run_memory(logs)
    elif target == "network":
        run_network()
    else:
        run_cpu(logs)
        run_memory(logs)
        run_network()
