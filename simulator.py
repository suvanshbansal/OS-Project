"""Discrete-time, single-CPU preemptive scheduling simulation."""

from __future__ import annotations

from collections import defaultdict

from rt_scheduler.models import (
    Job,
    JobResult,
    Metrics,
    Scenario,
    ScheduleSegment,
    SimulationResult,
)
from rt_scheduler.policies import SchedulingPolicy


IDLE_COLOR = "#D9D9D9"


def _append_segment(
    segments: list[ScheduleSegment],
    start_ms: int,
    end_ms: int,
    job: Job | None,
) -> None:
    job_id = job.job_id if job else None
    task_name = job.task.name if job else None
    color = job.task.color if job else IDLE_COLOR

    if (
        segments
        and segments[-1].end_ms == start_ms
        and segments[-1].job_id == job_id
    ):
        previous = segments[-1]
        segments[-1] = ScheduleSegment(
            start_ms=previous.start_ms,
            end_ms=end_ms,
            job_id=previous.job_id,
            task_name=previous.task_name,
            color=previous.color,
        )
        return

    segments.append(
        ScheduleSegment(
            start_ms=start_ms,
            end_ms=end_ms,
            job_id=job_id,
            task_name=task_name,
            color=color,
        )
    )


def _make_job_results(jobs: list[Job]) -> tuple[JobResult, ...]:
    results: list[JobResult] = []
    for job in jobs:
        if job.first_start_ms is None or job.finish_ms is None:
            raise RuntimeError(f"Job {job.job_id} was not completed by the simulation.")
        turnaround = job.finish_ms - job.release_ms
        response = job.first_start_ms - job.release_ms
        waiting = turnaround - job.task.execution_ms
        tardiness = max(0, job.finish_ms - job.absolute_deadline_ms)
        results.append(
            JobResult(
                job_id=job.job_id,
                task_name=job.task.name,
                release_ms=job.release_ms,
                absolute_deadline_ms=job.absolute_deadline_ms,
                first_start_ms=job.first_start_ms,
                finish_ms=job.finish_ms,
                execution_ms=job.task.execution_ms,
                response_ms=response,
                turnaround_ms=turnaround,
                waiting_ms=waiting,
                tardiness_ms=tardiness,
                deadline_missed=job.deadline_missed,
            )
        )
    return tuple(results)


def _make_metrics(
    scenario: Scenario,
    jobs: tuple[JobResult, ...],
    busy_time_ms: int,
    makespan_ms: int,
) -> Metrics:
    count = len(jobs)
    missed = sum(job.deadline_missed for job in jobs)
    completed = sum(job.finish_ms is not None for job in jobs)

    def average(values: list[int]) -> float:
        return sum(values) / len(values) if values else 0.0

    tardiness_values = [job.tardiness_ms for job in jobs]
    return Metrics(
        total_jobs=count,
        completed_jobs=completed,
        missed_deadlines=missed,
        on_time_percent=((count - missed) / count * 100) if count else 100.0,
        average_response_ms=average([job.response_ms for job in jobs]),
        average_turnaround_ms=average([job.turnaround_ms for job in jobs]),
        average_waiting_ms=average([job.waiting_ms for job in jobs]),
        average_tardiness_ms=average(tardiness_values),
        maximum_tardiness_ms=max(tardiness_values, default=0),
        offered_load_percent=scenario.offered_load * 100,
        cpu_utilization_percent=(busy_time_ms / makespan_ms * 100) if makespan_ms else 0.0,
        makespan_ms=makespan_ms,
    )


def simulate(scenario: Scenario, policy: SchedulingPolicy) -> SimulationResult:
    """Run every periodic release in a scenario using one scheduling policy.

    Time advances in 1 ms steps. All releases before ``horizon_ms`` are
    generated; after the final release, the simulator drains the ready queue
    so every job has a measured finish time. A job misses its deadline if it
    still has work remaining at its absolute deadline.
    """

    releases: dict[int, list[tuple[int, int, int]]] = defaultdict(list)
    for task_index, task in enumerate(scenario.tasks):
        release_ms = task.offset_ms
        release_number = 0
        while release_ms < scenario.horizon_ms:
            releases[release_ms].append((task_index, release_number, release_ms))
            release_number += 1
            release_ms += task.period_ms

    all_jobs: list[Job] = []
    segments: list[ScheduleSegment] = []
    now_ms = 0
    busy_time_ms = 0
    last_release_ms = max(releases, default=-1)

    while now_ms < scenario.horizon_ms or now_ms <= last_release_ms or any(
        not job.is_complete for job in all_jobs
    ):
        for task_index, release_number, release_ms in releases.get(now_ms, []):
            task = scenario.tasks[task_index]
            all_jobs.append(
                Job(
                    job_id=f"{task.name}-{release_number + 1:03d}",
                    task=task,
                    task_index=task_index,
                    release_number=release_number,
                    release_ms=release_ms,
                    absolute_deadline_ms=release_ms + task.deadline_ms,
                    remaining_ms=task.execution_ms,
                )
            )

        ready_jobs = [
            job
            for job in all_jobs
            if job.release_ms <= now_ms and not job.is_complete
        ]

        selected = policy.choose(ready_jobs) if ready_jobs else None
        if selected is not None and selected.first_start_ms is None:
            selected.first_start_ms = now_ms

        _append_segment(segments, now_ms, now_ms + 1, selected)
        if selected is None:
            now_ms += 1
            continue

        selected.remaining_ms -= 1
        busy_time_ms += 1
        now_ms += 1
        if selected.remaining_ms == 0:
            selected.finish_ms = now_ms

        for job in all_jobs:
            if (
                not job.is_complete
                and not job.deadline_missed
                and job.absolute_deadline_ms <= now_ms
            ):
                job.deadline_missed = True

    job_results = _make_job_results(all_jobs)
    makespan = max((job.finish_ms for job in job_results), default=scenario.horizon_ms)
    makespan = max(makespan, scenario.horizon_ms)
    metrics = _make_metrics(scenario, job_results, busy_time_ms, makespan)
    colors = {task.name: task.color for task in scenario.tasks}

    return SimulationResult(
        scenario_name=scenario.name,
        policy_name=policy.name,
        jobs=job_results,
        segments=tuple(segments),
        metrics=metrics,
        task_colors=colors,
    )
