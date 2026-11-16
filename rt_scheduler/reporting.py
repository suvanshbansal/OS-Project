"""Export transparent CSV measurements and timeline figures."""

from __future__ import annotations

import csv
from pathlib import Path

from rt_scheduler.models import Scenario, SimulationResult
from rt_scheduler.plotting import plot_comparison


SUMMARY_FIELDS = [
    "scenario",
    "policy",
    "offered_load_percent",
    "total_jobs",
    "completed_jobs",
    "missed_deadlines",
    "on_time_percent",
    "average_response_ms",
    "average_turnaround_ms",
    "average_waiting_ms",
    "average_tardiness_ms",
    "maximum_tardiness_ms",
    "cpu_utilization_percent",
    "makespan_ms",
]

JOB_FIELDS = [
    "scenario",
    "policy",
    "job_id",
    "task_name",
    "release_ms",
    "absolute_deadline_ms",
    "first_start_ms",
    "finish_ms",
    "execution_ms",
    "response_ms",
    "turnaround_ms",
    "waiting_ms",
    "tardiness_ms",
    "deadline_missed",
]


def write_results(
    scenario: Scenario,
    results: list[SimulationResult],
    output_dir: Path,
) -> list[Path]:
    """Write summary CSV, per-job CSV, and comparison plot."""

    output_dir.mkdir(parents=True, exist_ok=True)
    stem = scenario.name.lower().replace(" ", "_")
    summary_path = output_dir / f"{stem}_summary.csv"
    jobs_path = output_dir / f"{stem}_jobs.csv"
    plot_path = output_dir / f"{stem}_timeline.png"

    with summary_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        for result in results:
            metrics = result.metrics
            writer.writerow(
                {
                    "scenario": result.scenario_name,
                    "policy": result.policy_name,
                    "offered_load_percent": f"{metrics.offered_load_percent:.2f}",
                    "total_jobs": metrics.total_jobs,
                    "completed_jobs": metrics.completed_jobs,
                    "missed_deadlines": metrics.missed_deadlines,
                    "on_time_percent": f"{metrics.on_time_percent:.2f}",
                    "average_response_ms": f"{metrics.average_response_ms:.3f}",
                    "average_turnaround_ms": f"{metrics.average_turnaround_ms:.3f}",
                    "average_waiting_ms": f"{metrics.average_waiting_ms:.3f}",
                    "average_tardiness_ms": f"{metrics.average_tardiness_ms:.3f}",
                    "maximum_tardiness_ms": metrics.maximum_tardiness_ms,
                    "cpu_utilization_percent": f"{metrics.cpu_utilization_percent:.2f}",
                    "makespan_ms": metrics.makespan_ms,
                }
            )

    with jobs_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=JOB_FIELDS)
        writer.writeheader()
        for result in results:
            for job in result.jobs:
                writer.writerow(
                    {
                        "scenario": result.scenario_name,
                        "policy": result.policy_name,
                        "job_id": job.job_id,
                        "task_name": job.task_name,
                        "release_ms": job.release_ms,
                        "absolute_deadline_ms": job.absolute_deadline_ms,
                        "first_start_ms": job.first_start_ms,
                        "finish_ms": job.finish_ms,
                        "execution_ms": job.execution_ms,
                        "response_ms": job.response_ms,
                        "turnaround_ms": job.turnaround_ms,
                        "waiting_ms": job.waiting_ms,
                        "tardiness_ms": job.tardiness_ms,
                        "deadline_missed": job.deadline_missed,
                    }
                )

    plot_comparison(scenario, results, plot_path)
    return [summary_path, jobs_path, plot_path]
