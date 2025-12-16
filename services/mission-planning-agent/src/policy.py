from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class SensorDef:
    sensor_id: str
    sensor_type: str
    is_available: bool = True
    max_tasks: int = 3
    coverage_hint: Optional[str] = None


@dataclass
class Policy:
    policy_version: str
    mission_defaults: Dict[str, Any]
    hard_constraints: Dict[str, Any]
    scoring: Dict[str, Any]
    priority_rules: List[Dict[str, Any]]
    tie_break: Dict[str, Any]
    sensors: List[SensorDef]


def load_policy(path: str) -> Policy:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    sensors_raw = raw.get("sensor_inventory", {}).get("sensors", [])
    sensors = []
    for s in sensors_raw:
        sensors.append(
            SensorDef(
                sensor_id=s["sensor_id"],
                sensor_type=s["sensor_type"],
                is_available=bool(s.get("is_available", True)),
                max_tasks=int(s.get("max_tasks", 3)),
                coverage_hint=s.get("coverage_hint"),
            )
        )

    return Policy(
        policy_version=str(raw.get("policy_version", "unknown")),
        mission_defaults=raw.get("mission_defaults", {}),
        hard_constraints=raw.get("hard_constraints", {}),
        scoring=raw.get("scoring", {}),
        priority_rules=raw.get("priority_rules", []),
        tie_break=raw.get("tie_break", {}),
        sensors=sensors,
    )
