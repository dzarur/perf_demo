# Efficiency Lab — Automated Performance Measurement

**Course:** Automation in Software Development  
**Time:** ~50 minutes  

---

## What this lab is about

Three versions of the same program — parsing synthetic HTTP access logs — each stress a different resource. You'll measure all three automatically and compare the numbers. The goal is not to make everything faster; it's to understand *what kind of slow* each program is, and to notice that the measurement tools are themselves a form of automation.

---

## Files

| File | Purpose |
|---|---|
| `workloads.py` | Three log-analysis workloads |
| `server.py` | Localhost HTTP server (needed for the network workload) |
| `measure.py` | Automated measurement harness |
| `visualize.py` | Generates a comparison chart |

---

## Setup (~5 min)

**1.** Install [uv](https://docs.astral.sh/uv/) if you don't have it:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**2.** Install dependencies (creates a local `.venv` automatically):

```
uv sync
```

**3.** In a **second terminal**, start the localhost server:

```
uv run python3 server.py
```

You should see: `Server listening on http://127.0.0.1:5001`  
Leave this terminal open for the rest of the lab.

---

## Part 1 — CPU-Bound Work (~10 min)

Read `cpu_workload()` in `workloads.py`. It parses 20,000 log lines with a regular expression and counts requests by HTTP status code.

Before running anything: **predict** — will CPU time be close to wall-clock time, or far apart?

Run it:

```
uv run python3 measure.py cpu
```

You'll see three numbers: wall-clock time, CPU time, and their ratio.

**Discuss:**
- Why are CPU time and wall time nearly equal here?
- If you wanted this to run faster, what would you change — the algorithm, the data structure, or something else?

---

## Part 2 — I/O-Bound (Network) Work (~12 min)

Read `network_workload()` in `workloads.py`. It makes 12 HTTP requests to `localhost:5001/logs`. Each request returns 100 log lines, but the server adds a **150 ms artificial delay** per request.

Predict: will CPU time be close to wall time here?

Run it (server must be running):

```
uv run python3 measure.py network
```

You'll see two rows — the slow endpoint and the fast one (no delay).

**Discuss:**
- Wall time is much larger than CPU time for the slow endpoint. What is the process doing during the gap?
- The fast endpoint doesn't change the code — only the server delay disappears. What does that tell you about where the bottleneck was?
- Could you reduce wall time for the slow endpoint without modifying `server.py`? How?

---

## Part 3 — Memory-Heavy Work (~8 min)

Read `memory_workload()` in `workloads.py` side by side with `cpu_workload()`. Both process the same 20,000 lines and return the same result.

Predict: which uses more peak memory, and by how much?

Run it:

```
uv run python3 measure.py memory
```

**Discuss:**
- Find the specific line(s) in `memory_workload` that explain the higher memory usage.
- The outputs are identical. If the outputs are the same, why does the implementation matter?
- What happens to each workload if the dataset is 10× larger?

---

## Part 4 — Automated Measurement (~12 min)

Run the full harness — all workloads in one pass — and generate the chart:

```
uv run python3 measure.py
uv run python3 visualize.py
```

`metrics.png` will be saved in the current directory.

Look at the chart. The left panel shows how much of wall time was actual CPU work vs waiting. The right panel shows peak memory.

Notice what just happened: the I/O wait in the network workload was completely invisible until we instrumented it. The automation didn't speed anything up — it made the *category* of slow observable, which is a prerequisite for choosing the right fix.

**Discuss:**
- Label each workload: CPU-bound, I/O-bound, or memory-bound. What single number in the table tells you?
- `measure.py` is itself a piece of automation. Without it, how would you compare three workloads? What would you risk getting wrong?

### Going deeper: from "which workload?" to "which line?"

`measure.py` told you *which workload* is slow. Now find out *why* — using `cProfile`, which is built into Python.

Run this for the CPU workload:

```
uv run python3 -m cProfile -s cumulative measure.py cpu
```

Scan the output for `cpu_workload` and the functions called beneath it. Note the `cumtime` (cumulative time) column.

Now run the same for the memory workload:

```
uv run python3 -m cProfile -s cumulative measure.py memory
```

**Do:** Find the top three functions by cumulative time in each profile. What shows up in `memory_workload`'s profile that doesn't appear (or barely appears) in `cpu_workload`'s?

That's actionable information: `cProfile` told you the specific function to look at. If you rewrote just that function, you'd know exactly what you were targeting.

*(Optional — requires `uv sync --extra profiler`)* Scalene goes one level further: per-line CPU *and* memory, simultaneously.

```
uv run scalene measure.py
```

Find `cpu_workload` in the Scalene output. Now find `memory_workload`. Scalene will show you not just which function, but which line inside it is allocating memory.

**Discuss:**
- `cProfile` → function. Scalene → line. Each layer of automation gives you more specific, more actionable information. What is the tradeoff as the tool gets more powerful?
- McLuhan argued that every medium or tool reshapes the human capacities it extends — the car extends the leg but atrophies the walk. What capacity might increasingly powerful profilers extend, and what might they atrophy in the developer who relies on them?

---

## Part 5 — Reflection (~12 min)

These questions connect today's measurements to the broader course themes. You won't answer all of them — choose the ones that feel most alive.

**On tradeoffs:**
- Is there any single change that improves all three metrics simultaneously, or do tradeoffs always appear?
- For the network workload, the bottleneck is entirely inside the server — not in your code at all. Does it make sense to "optimize" this workload? Who owns the problem?

**On measurement:**
- Which metrics today were *directly measured* and which were *calculated from something else*?
- `measure.py` measures wall time, CPU time, and memory. It does not measure energy use, developer comprehension time, fairness, or anything involving a human. The choice of what to instrument is itself a value judgment — it decides what counts as a problem. What does `measure.py` implicitly treat as not a problem?
- Could a program score well on all three metrics and still be a bad program? Describe one.

**On efficiency as a goal:**
- Jacques Ellul argued in *The Technological Society* that "technique" tends to pursue efficiency as an autonomous end, independent of whether efficiency serves human purposes. Do you see this tendency in how software engineers talk about performance?
- What would it mean to measure efficiency at the level of the whole system — user, software, hardware, organization?
- If a manager asked you to "make this code more efficient," what is the first question you should ask back?

---

## Quick reference

| Command | What it does |
|---|---|
| `uv sync` | Install dependencies (matplotlib; run once) |
| `uv sync --extra profiler` | Also install Scalene |
| `uv run python3 server.py` | Start the localhost server (separate terminal) |
| `uv run python3 measure.py [cpu\|network\|memory]` | Run one workload |
| `uv run python3 measure.py` | Run all workloads |
| `uv run python3 visualize.py` | Generate `metrics.png` |
| `uv run python3 visualize.py --no-network` | Skip network workload |
| `uv run scalene measure.py` | Line-level profiler (optional) |
