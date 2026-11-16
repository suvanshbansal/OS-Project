"""Input loading for JSON workload scenarios."""

from __future__ import annotations

import json
from pathlib import Path

from rt_scheduler.models import Scenario, scenario_from_mapping


def load_scenario(path: Path) -> Scenario:
    """Read and validate one scenario file."""

    try:
        with path.open("r", encoding="utf-8") as stream:
            data = json.load(stream)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid JSON in {path} at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    except OSError as exc:
        raise FileNotFoundError(f"Cannot read scenario file {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError("The scenario file must contain a JSON object at its top level.")
    return scenario_from_mapping(data)
