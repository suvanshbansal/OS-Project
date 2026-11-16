"""Data structures shared by the scheduler simulator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Task:
    """One periodic task in the simulated controller."""

    name: str
    execution_ms: int
    period_ms: int
    deadline_ms: int
    offset_ms: int = 0
    color: str = "#4C78A8"

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Task name cannot be empty.")
        for label, value in (
            ("execution_ms", self.execution_ms),
            ("period_ms", self.period_ms),
            ("deadline_ms", self.deadline_ms),
        ):
            if not isinstance(value, int) or value <= 0:
                raise ValueError(f"{label} for task {self.name!r} must be a positive integer.")
        if not isinstance(self.offset_ms, int) or self.offset_ms < 0:
            raise ValueError(f"offset_ms for task {self.name!r} must be a non-negative integer.")


@dataclass(frozen=True, slots=True)
class Scenario:
    """A finite set of periodic tasks and a release-generation horizon."""

    name: str
    description: str
    horizon_ms: int
    tasks: tuple[Task, ...]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Scenario name cannot be empty.")
        if not isinstance(self.horizon_ms, int) or self.horizon_ms <= 0:
            raise ValueError("horizon_ms must be a positive integer.")
        if not self.tasks:
            raise ValueError("A scenario must contain at least one task.")
        names = [task.name for task in self.tasks]
        if len(names) != len(set(names)):
            raise ValueError("Task names must be unique within a scenario.")

    @property
    def offered_load(self) -> float:
        """Long-run CPU demand as a fraction of one CPU."""

        return sum(task.execution_ms / task.period_ms for task in self.tasks)


@dataclass(slots=True)
class Job:
    """A single release (instance) of a periodic task."""

    job_id: str
    task: Task
    task_index: int
    release_number: int
    release_ms: int
    absolute_deadline_ms: int
    remaining_ms: int
    first_start_ms: int | None = None
    finish_ms: int | None = None
    deadline_missed: bool = False

    @property
    def is_complete(self) -> bool:
        return self.remaining_ms == 0


@dataclass(frozen=True, slots=True)
class ScheduleSegment:
    """A contiguous interval during which a job or the idle CPU was active."""

    start_ms: int
    end_ms: int
    job_id: str | None
    task_name: str | None
    color: str


@dataclass(frozen=True, slots=True)
class JobResult:
    """Measured timing values for one released job."""

    job_id: str
    task_name: str
    release_ms: int
    absolute_deadline_ms: int
    first_start_ms: int
    finish_ms: int
    execution_ms: int
    response_ms: int
    turnaround_ms: int
    waiting_ms: int
    tardiness_ms: int
    deadline_missed: bool


@dataclass(frozen=True, slots=True)
class Metrics:
    """Aggregate performance measurements for one policy."""

    total_jobs: int
    completed_jobs: int
    missed_deadlines: int
    on_time_percent: float
    average_response_ms: float
    average_turnaround_ms: float
    average_waiting_ms: float
    average_tardiness_ms: float
    maximum_tardiness_ms: int
    offered_load_percent: float
    cpu_utilization_percent: float
    makespan_ms: int


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """Complete schedule and measurements for one scenario-policy pair."""

    scenario_name: str
    policy_name: str
    jobs: tuple[JobResult, ...]
    segments: tuple[ScheduleSegment, ...]
    metrics: Metrics
    task_colors: dict[str, str] = field(default_factory=dict)


def scenario_from_mapping(data: dict[str, Any]) -> Scenario:
    """Build a validated Scenario from decoded JSON content."""

    required = {"name", "horizon_ms", "tasks"}
    missing = sorted(required - data.keys())
    if missing:
        raise ValueError(f"Scenario is missing required fields: {', '.join(missing)}")

    tasks_data = data["tasks"]
    if not isinstance(tasks_data, list):
        raise ValueError("Scenario field 'tasks' must be a list.")

    tasks: list[Task] = []
    required_task_fields = {"name", "execution_ms", "period_ms", "deadline_ms"}
    for index, item in enumerate(tasks_data, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Task #{index} must be a JSON object.")
        missing_task_fields = sorted(required_task_fields - item.keys())
        if missing_task_fields:
            raise ValueError(
                f"Task #{index} is missing required fields: "
                f"{', '.join(missing_task_fields)}"
            )
        tasks.append(
            Task(
                name=str(item["name"]),
                execution_ms=item["execution_ms"],
                period_ms=item["period_ms"],
                deadline_ms=item["deadline_ms"],
                offset_ms=item.get("offset_ms", 0),
                color=item.get("color", "#4C78A8"),
            )
        )

    return Scenario(
        name=str(data["name"]),
        description=str(data.get("description", "")),
        horizon_ms=data["horizon_ms"],
        tasks=tuple(tasks),
    )
