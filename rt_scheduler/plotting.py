"""Matplotlib timeline plot for a scenario comparison."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

from rt_scheduler.models import Scenario, SimulationResult


def plot_comparison(
    scenario: Scenario,
    results: list[SimulationResult],
    output_path: Path,
) -> None:
    """Save a paired timeline with deadline status marks."""

    figure, axes = plt.subplots(
        nrows=len(results),
        ncols=1,
        figsize=(13, max(4.8, 2.5 * len(results))),
        sharex=True,
        squeeze=False,
    )
    flat_axes = [row[0] for row in axes]
    maximum_time = scenario.horizon_ms

    for axis, result in zip(flat_axes, results, strict=True):
        lane_y = 0.0
        metrics = result.metrics
        axis.set_title(
            f"{result.policy_name}  |  "
            f"{metrics.missed_deadlines}/{metrics.total_jobs} deadlines missed  |  "
            f"mean response {metrics.average_response_ms:.2f} ms",
            loc="left",
            fontsize=11,
            weight="bold",
        )
        for segment in result.segments:
            width = segment.end_ms - segment.start_ms
            axis.barh(
                y=lane_y,
                width=width,
                left=segment.start_ms,
                height=0.5,
                color=segment.color,
                edgecolor="white",
                linewidth=0.35,
            )
            maximum_time = max(maximum_time, segment.end_ms)

        for job in result.jobs:
            marker = "x" if job.deadline_missed else "o"
            marker_color = "#D62728" if job.deadline_missed else "#238B45"
            axis.scatter(
                [job.absolute_deadline_ms],
                [lane_y],
                marker=marker,
                color=marker_color,
                s=28,
                linewidths=1.2,
                zorder=4,
            )
            maximum_time = max(maximum_time, job.absolute_deadline_ms)

        axis.set_yticks([lane_y], [result.policy_name])
        axis.set_ylim(-0.6, 0.6)
        axis.grid(axis="x", linestyle=":", linewidth=0.7, alpha=0.65)
        axis.set_axisbelow(True)

    axes[-1][0].set_xlim(0, maximum_time + max(2, maximum_time * 0.03))
    axes[-1][0].set_xlabel("Simulated time (ms)")
    figure.suptitle(
        f"{scenario.name}: CPU timeline (1 ms time steps)",
        fontsize=14,
        weight="bold",
        y=0.99,
    )

    task_legend = [
        Patch(facecolor=task.color, label=task.name)
        for task in scenario.tasks
    ]
    status_legend = [
        Line2D([0], [0], marker="o", color="w", markerfacecolor="#238B45",
               markersize=7, label="Deadline met"),
        Line2D([0], [0], marker="x", color="#D62728", markersize=7,
               linestyle="None", label="Deadline missed"),
    ]
    figure.legend(
        handles=task_legend + status_legend,
        loc="lower center",
        ncol=min(4, len(task_legend) + 2),
        frameon=False,
        bbox_to_anchor=(0.5, 0.015),
    )
    figure.tight_layout(rect=(0, 0.12, 1, 0.94))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close(figure)
