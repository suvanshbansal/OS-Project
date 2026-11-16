"""Rate Monotonic and Earliest Deadline First selection rules."""

from __future__ import annotations

from typing import Protocol

from rt_scheduler.models import Job


class SchedulingPolicy(Protocol):
    """Interface for selecting one ready job at a CPU time step."""

    name: str

    def choose(self, ready_jobs: list[Job]) -> Job:
        """Return the highest-ranked job from a non-empty ready list."""


class RMPolicy:
    """Rate Monotonic: shorter task period means higher fixed priority."""

    name = "RM"

    def choose(self, ready_jobs: list[Job]) -> Job:
        if not ready_jobs:
            raise ValueError("RM cannot choose from an empty ready list.")
        return min(
            ready_jobs,
            key=lambda job: (
                job.task.period_ms,
                job.task_index,
                job.release_ms,
                job.release_number,
            ),
        )


class EDFPolicy:
    """Earliest Deadline First: nearest absolute deadline gets the CPU."""

    name = "EDF"

    def choose(self, ready_jobs: list[Job]) -> Job:
        if not ready_jobs:
            raise ValueError("EDF cannot choose from an empty ready list.")
        return min(
            ready_jobs,
            key=lambda job: (
                job.absolute_deadline_ms,
                job.task.period_ms,
                job.task_index,
                job.release_ms,
                job.release_number,
            ),
        )
