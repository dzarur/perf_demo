"""
Generate a two-panel chart from the measurement harness.

Usage:
  uv run python3 visualize.py          # all workloads (server must be running for network)
  uv run python3 visualize.py --no-network

Output: metrics.png  (also opens interactively if a display is available)
"""

import sys

try:
    import matplotlib
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
except ImportError:
    print("matplotlib is required. Run: uv sync")
    sys.exit(1)

from measure import collect_all, HEADER, RULE
from workloads import generate_logs

# ── colours ──────────────────────────────────────────────────────────────────
C_CPU  = "#4878CF"   # blue   — CPU time (actual computation)
C_WAIT = "#D9D9D9"   # grey   — wall − CPU (waiting / I/O)
C_MEM  = "#6ACC65"   # green  — peak memory


def build_chart(rows, out="metrics.png"):
    labels   = [r["label"] for r in rows]
    wall     = np.array([r["wall"]   for r in rows])
    cpu      = np.array([r["cpu"]    for r in rows])
    wait     = wall - cpu
    mem_kb   = np.array([r["mem_kb"] for r in rows])

    x = np.arange(len(labels))
    bar_w = 0.55

    fig, (ax_time, ax_mem) = plt.subplots(
        1, 2,
        figsize=(11, 5),
        gridspec_kw={"width_ratios": [3, 2]},
    )
    fig.suptitle("Log Analysis Workloads — Automated Performance Measurement",
                 fontsize=13, fontweight="bold", y=1.01)

    # ── left panel: time breakdown ────────────────────────────────────────────
    ax_time.bar(x, cpu,  bar_w, label="CPU time",       color=C_CPU,  zorder=3)
    ax_time.bar(x, wait, bar_w, bottom=cpu,             color=C_WAIT, zorder=3,
                label="Wait / I/O time", hatch="///", edgecolor="#aaaaaa", linewidth=0.5)

    for i, (w, c) in enumerate(zip(wall, cpu)):
        pct = c / w if w > 0 else 0
        ax_time.text(i, w + max(wall) * 0.02,
                     f"{pct:.0%} CPU", ha="center", va="bottom", fontsize=8.5)

    ax_time.set_xticks(x)
    ax_time.set_xticklabels(labels, fontsize=9)
    ax_time.set_ylabel("Time (seconds)")
    ax_time.set_title("Wall time = CPU time + Wait time")
    ax_time.legend(loc="upper left", fontsize=8)
    ax_time.set_ylim(0, max(wall) * 1.18)
    ax_time.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax_time.set_axisbelow(True)

    # ── right panel: peak memory ──────────────────────────────────────────────
    bars = ax_mem.barh(labels, mem_kb, color=C_MEM, zorder=3)
    for bar, val in zip(bars, mem_kb):
        label_str = f"{val:.0f} KB" if val < 1024 else f"{val/1024:.1f} MB"
        ax_mem.text(val + max(mem_kb) * 0.02, bar.get_y() + bar.get_height() / 2,
                    label_str, va="center", fontsize=8.5)

    ax_mem.set_xlabel("Peak memory (KB)")
    ax_mem.set_title("Peak memory (tracemalloc)")
    ax_mem.set_xlim(0, max(mem_kb) * 1.25)
    ax_mem.xaxis.grid(True, linestyle="--", alpha=0.5)
    ax_mem.set_axisbelow(True)

    fig.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"\nChart saved to {out}")

    try:
        plt.show()
    except Exception:
        pass  # headless environments


if __name__ == "__main__":
    include_network = "--no-network" not in sys.argv

    print("Generating 20,000 log lines...", flush=True)
    logs = generate_logs()

    print()
    print(HEADER)
    print(RULE)

    rows = collect_all(logs) if include_network else []
    if not include_network:
        from measure import run_cpu, run_memory
        rows = [run_cpu(logs), run_memory(logs)]

    if not rows:
        print("No data collected.")
        sys.exit(1)

    build_chart(rows)
