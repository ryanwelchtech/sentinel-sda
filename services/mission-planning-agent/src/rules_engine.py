from __future__ import annotations
from typing import Dict, List, Tuple
from datetime import timedelta
from .util import now_utc, parse_time, clamp
from .policy import SensorDef
from .models import ConstraintResult, Track


def check_constraints(track: Track, sensor: SensorDef, hard: Dict) -> ConstraintResult:
    reasons: List[str] = []
    passed = True

    min_conf = float(hard.get("min_track_confidence", 0.0))
    if track.confidence < min_conf:
        passed = False
        reasons.append(f"confidence {track.confidence:.2f} below {min_conf:.2f}")

    allowed = hard.get("allowed_sensor_types", [])
    if allowed and sensor.sensor_type not in allowed:
        passed = False
        reasons.append(f"sensor_type {sensor.sensor_type} not allowed")

    z_floor = float(hard.get("no_task_z_km_below", -1e9))
    if track.state.z_km < z_floor:
        passed = False
        reasons.append(f"z_km {track.state.z_km:.2f} below floor {z_floor:.2f}")

    if not sensor.is_available:
        passed = False
        reasons.append("sensor unavailable")

    return ConstraintResult(passed=passed, reasons=reasons)


def priority_boost(track: Track, rules: List[Dict]) -> float:
    boost = 0.0
    updated = parse_time(track.updated_at)
    age_min = (now_utc() - updated).total_seconds() / 60.0

    for rule in rules:
        when = rule.get("when", {})
        ok = True

        z_min = when.get("z_km_min")
        if z_min is not None and track.state.z_km < float(z_min):
            ok = False

        conf_max = when.get("confidence_max")
        if conf_max is not None and track.confidence > float(conf_max):
            ok = False

        upd_within = when.get("updated_within_min")
        if upd_within is not None and age_min > float(upd_within):
            ok = False

        if ok:
            boost += float(rule.get("boost", 0.0))

    return clamp(boost, 0.0, 0.40)


def score(track: Track, pboost: float, weights: Dict[str, float], horizon_min: int) -> Tuple[float, Dict[str, float]]:
    updated = parse_time(track.updated_at)
    age_sec = max(0.0, (now_utc() - updated).total_seconds())
    recency = 1.0 - min(age_sec / max(horizon_min * 60, 1), 1.0)

    mission_priority = clamp(0.50 + pboost, 0.0, 1.0)
    confidence = clamp(float(track.confidence), 0.0, 1.0)

    geometry = 0.5  # placeholder until you add line-of-sight / look-angle constraints
    diversity = 0.5  # handled at selection time, keep neutral here

    total = (
        float(weights.get("mission_priority", 0.35)) * mission_priority
        + float(weights.get("confidence", 0.30)) * confidence
        + float(weights.get("recency", 0.15)) * recency
        + float(weights.get("geometry", 0.10)) * geometry
        + float(weights.get("diversity", 0.10)) * diversity
    )

    breakdown = {
        "mission_priority": mission_priority,
        "confidence": confidence,
        "recency": recency,
        "geometry": geometry,
        "diversity": diversity,
    }
    return total, breakdown
