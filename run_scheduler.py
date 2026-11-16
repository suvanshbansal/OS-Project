#!/usr/bin/env python3
"""Run the automotive real-time scheduling simulator."""

from __future__ import annotations

import argparse
from pathlib import Path

from rt_scheduler.io import load_scenario
from rt_scheduler.policies import EDFPolicy, RMPolicy
from rt_scheduler.reporting import write_results
from rt_scheduler.simulator import simulate


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_SCENARIO_DIR = PROJECT_DIR / "scenarios"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Simulate periodic automotive-controller tasks with "
            "Rate Monotonic and Earliest Deadline First scheduling."
        )
    )
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--scenario",
        type=Path,
        help="JSON scenario file (default: scenarios/normal.json)",
    )
    selection.add_argument(
        "--all-scenarios",
        action="store_true",
        help="run every .json scenario in the scenarios directory",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_DIR / "outputs",
        help="folder for generated CSV files and timeline plots",
    )
    return parser.parse_args()


def find_scenarios(args: argparse.Namespace) -> list[Path]:
    if args.scenario is not None:
        path = args.scenario
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Scenario file not found: {path}")
        return [path]

    if args.all_scenarios:
        paths = sorted(DEFAULT_SCENARIO_DIR.glob("*.json"))
        if not paths:
            raise FileNotFoundError(
                f"No .json scenarios found in {DEFAULT_SCENARIO_DIR}"
            )
        return paths

    return [DEFAULT_SCENARIO_DIR / "normal.json"]


def main() -> int:
    args = parse_args()
    try:
        scenario_paths = find_scenarios(args)
        policies = [RMPolicy(), EDFPolicy()]

        for scenario_path in scenario_paths:
            scenario = load_scenario(scenario_path)
            results = [
                simulate(scenario, policy)
                for policy in policies
            ]
            files = write_results(scenario, results, args.output_dir)
            print(f"\nScenario: {scenario.name}")
            print(f"Tasks: {len(scenario.tasks)} | Horizon: {scenario.horizon_ms} ms")
            print(
                f"Offered CPU load: "
                f"{scenario.offered_load * 100:.1f}%"
            )
            print(
                "Policy  Jobs  Misses  On-time  Avg response  Avg waiting  CPU use"
            )
            for result in results:
                metrics = result.metrics
                print(
                    f"{result.policy_name:<7} "
                    f"{metrics.total_jobs:>4}  "
                    f"{metrics.missed_deadlines:>6}  "
                    f"{metrics.on_time_percent:>6.1f}%  "
                    f"{metrics.average_response_ms:>12.2f}  "
                    f"{metrics.average_waiting_ms:>11.2f}  "
                    f"{metrics.cpu_utilization_percent:>6.1f}%"
                )
            print("Generated:")
            for path in files:
                print(f"  {path}")
    except (FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}")
        return 2

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
