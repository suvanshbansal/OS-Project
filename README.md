# Real-Time Task Scheduler for an Automotive Controller

**Operating Systems project | Group G10 | Batch B10 | Project P03**

**Team:** Suvansh Bansal (590023081), Bhanu Pratap (590022147), Rohit Gupta (590023408), Jinnay Amar Bhanushali (590023782)

This project is a Python simulation of periodic tasks competing for one CPU in an automotive-style controller. It compares two preemptive scheduling policies:

- **Rate Monotonic (RM):** a task with a shorter period has higher fixed priority.
- **Earliest Deadline First (EDF):** among ready jobs, the job with the soonest absolute deadline runs first.

The simulator uses a 1 ms time step. It creates periodic task releases, schedules ready jobs, records completion and deadline misses, and plots an execution timeline. It does not connect to car hardware or provide safety guarantees for a real vehicle.

## Problem and objectives

**Problem:** When several periodic controller tasks need the CPU, the execution order can affect their response time and whether they finish before their deadlines. This project models that scheduling problem so two policies can be compared on the same workload.

**Objectives:**

1. Simulate periodic automotive-style tasks on one CPU.
2. Implement preemptive Rate Monotonic and Earliest Deadline First policies.
3. Measure response time, waiting time, tardiness, CPU use and deadline misses for each released job.
4. Compare both policies under normal and overloaded task demand using CSV summaries and timeline plots.

## What the simulation models

Each periodic task has:

| Field | Meaning |
|---|---|
| Execution time, `C` | CPU time one job needs, in milliseconds |
| Period, `T` | Time between releases of new jobs, in milliseconds |
| Relative deadline, `D` | Time allowed after release for that job to finish |
| Offset | Time of the first release |

Every release creates a job with an absolute deadline `release time + D`. At each millisecond, the policy chooses one ready job. If it is unfinished at its deadline, the job is counted as a deadline miss. The simulator continues after the last release until all released jobs finish, so response and completion times are available for every job.

## Operating Systems concepts demonstrated

- CPU scheduling and ready queues
- Preemption and dispatch decisions
- Fixed priority scheduling (RM)
- Dynamic priority scheduling (EDF)
- Periodic jobs, response time, waiting time, turnaround time and deadlines
- CPU utilization and deadline-miss analysis

## How the program works

```text
Scenario JSON
    -> task and periodic-job releases
    -> RM or EDF selects a ready job each millisecond
    -> completion and deadline status are recorded
    -> summary CSV, per-job CSV and matplotlib timeline
```

The simulator creates a new job at each periodic release. RM ranks jobs by their task's period, with the shortest period first. EDF ranks ready jobs by absolute deadline, with the earliest deadline first. The selected job receives one 1 ms CPU step; the scheduler then makes a fresh choice, which allows preemption between steps.

For a job with release time `A`, execution time `C`, first start `F`, finish `X`, and absolute deadline `D`:

- Response time: `F - A`
- Turnaround time: `X - A`
- Waiting time: `(X - A) - C`
- Tardiness: `max(0, X - D)`
- Deadline miss: unfinished at time `D`

Offered load is `sum(C_i / T_i)`. The CSV also reports measured CPU use over the complete simulated makespan. Offered load can exceed 100% in the stress scenario; one CPU cannot keep up with that average demand, so deadline misses are expected.

## Run it

Requirements: Python 3.10 or newer.

```bash
python3 -m pip install -r requirements.txt
python3 run_scheduler.py
```

The default command runs `scenarios/normal.json`. Run the overloaded workload with:

```bash
python3 run_scheduler.py --scenario scenarios/stress.json
```

Run both supplied scenarios in one command:

```bash
python3 run_scheduler.py --all-scenarios
```

Choose another output folder with:

```bash
python3 run_scheduler.py --all-scenarios --output-dir outputs
```

## Generated results

For each scenario, the program creates three files in `outputs/`:

- `<scenario>_summary.csv`: one row per policy with offered load, deadline misses, response time, waiting time, tardiness and CPU use.
- `<scenario>_jobs.csv`: timing details for each released job.
- `<scenario>_timeline.png`: RM and EDF schedules on a shared time axis. Task colors show CPU execution; green circles mark jobs that met deadlines and red crosses mark misses.

The CSV files are the source for the values used in the report. Do not copy example values from another project or claim results before running this simulator with the selected workloads.

## Workload choices

The normal scenario uses four illustrative periodic tasks: Brake monitor, Engine monitor, ABS check and Dashboard update. The stress scenario increases execution requirements while keeping the same periods and deadlines. This lets the team discuss how a scheduler behaves under ordinary and overloaded demand.

The long-run offered load is calculated as:

`U = sum(C_i / T_i)`

The supplied normal workload has an offered load of 59%. The stress workload has an offered load of 118%, meaning that the average requested CPU time exceeds one CPU's capacity. These are simulation inputs, not measurements from a vehicle.

## Change a scenario

Copy one of the JSON files in `scenarios/` and edit the scenario name, horizon, task names, execution times, periods, deadlines, offsets or colors. Times must be integer milliseconds. Keep task names unique. Then pass the new file to `--scenario`.

## Project limitations

- One CPU is simulated.
- Time advances in fixed 1 ms steps.
- Tasks are periodic and CPU-bound; I/O blocking and communication delay are not modelled.
- Context-switch overhead, interrupt latency, sensor hardware and actual vehicle software are outside the model.
- A simulation result illustrates scheduling behavior for its chosen task set. It does not prove hard real-time behavior on an automotive ECU.

## Suggested team ownership

Use GitHub commits to show each member's technical work. A possible division is periodic task generation and input, RM policy, EDF policy, and simulation metrics/visualization. All members should be able to explain the simulator and both scheduling policies.

