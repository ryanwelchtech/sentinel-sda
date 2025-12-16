from __future__ import annotations
from typing import Dict, List
import os

from .models import MissionRequest, PlanResponse, TaskRecommendation, ConstraintResult
from .policy import load_policy, SensorDef
from .tools.track_api import fetch_tracks
from .rules_engine import check_constraints, priority_boost, score
from .llm import LLM


def build_plan(req: MissionRequest) -> PlanResponse:
    policy_path = os.getenv("POLICY_PATH", "config/policy.yaml")
    pol = load_policy(policy_path)

    horizon = int(req.time_horizon_min or pol.mission_defaults.get("time_horizon_min", 30))
    max_tasks = int(req.max_tasks or pol.mission_defaults.get("max_tasks", 5))

    tracks = fetch_tracks(limit=150)
    sensors = pol.sensors

    if req.preferred_sensors:
        allowed = set(req.preferred_sensors)
        sensors = [s for s in sensors if s.sensor_id in allowed]

    weights = pol.scoring.get("weights", {})
    hard = pol.hard_constraints

    sensor_counts: Dict[str, int] = {s.sensor_id: 0 for s in sensors}
    object_counts: Dict[str, int] = {}

    candidates: List[TaskRecommendation] = []

    for t in tracks:
        pboost = priority_boost(t, pol.priority_rules)

        for s in sensors:
            if sensor_counts[s.sensor_id] >= min(s.max_tasks, int(hard.get("max_tasks_per_sensor", 3))):
                continue

            if object_counts.get(t.object_id, 0) >= int(hard.get("max_tasks_per_object", 1)):
                continue

            cr = check_constraints(t, s, hard)
            if not cr.passed:
                continue

            sc, breakdown = score(t, pboost, weights, horizon)

            candidates.append(
                TaskRecommendation(
                    task_id=f"task-{s.sensor_id}-{t.object_id}",
                    object_id=t.object_id,
                    sensor_id=s.sensor_id,
                    sensor_type=s.sensor_type,
                    score=sc,
                    score_breakdown=breakdown,
                    constraints=cr,
                )
            )

    candidates.sort(key=lambda x: x.score, reverse=True)

    # Selection step adds "diversity" by avoiding too many tasks on same sensor
    selected: List[TaskRecommendation] = []
    for c in candidates:
        if len(selected) >= max_tasks:
            break

        if sensor_counts.get(c.sensor_id, 0) >= min(
            next((s.max_tasks for s in sensors if s.sensor_id == c.sensor_id), 3),
            int(hard.get("max_tasks_per_sensor", 3)),
        ):
            continue

        if object_counts.get(c.object_id, 0) >= int(hard.get("max_tasks_per_object", 1)):
            continue

        selected.append(c)
        sensor_counts[c.sensor_id] = sensor_counts.get(c.sensor_id, 0) + 1
        object_counts[c.object_id] = object_counts.get(c.object_id, 0) + 1

    notes: List[str] = []
    llm = LLM()
    llm_used = False

    if llm.enabled and selected:
        try:
            expl = llm.explain_plan(req.mission_id, req.operator_intent, [x.model_dump() for x in selected])
            if expl:
                notes.append(expl)
                llm_used = True
        except Exception:
            notes.append("LLM explanation unavailable; returned deterministic results only.")

    if not selected:
        notes.append("No valid task recommendations. Check track availability and policy constraints.")

    return PlanResponse(
        mission_id=req.mission_id,
        policy_version=pol.policy_version,
        tasks=selected,
        notes=notes,
        llm_used=llm_used,
    )
