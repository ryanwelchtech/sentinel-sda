from __future__ import annotations
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class TrackState(BaseModel):
    x_km: float
    y_km: float
    z_km: float
    vx_kms: float
    vy_kms: float
    vz_kms: float


class Track(BaseModel):
    object_id: str
    state: TrackState
    confidence: float = Field(ge=0.0, le=1.0)
    updated_at: str


class MissionRequest(BaseModel):
    mission_id: str
    time_horizon_min: int = 30
    max_tasks: int = 5
    operator_intent: Optional[str] = None
    preferred_sensors: Optional[List[str]] = None


class ConstraintResult(BaseModel):
    passed: bool
    reasons: List[str] = Field(default_factory=list)


class TaskRecommendation(BaseModel):
    task_id: str
    object_id: str
    sensor_id: str
    sensor_type: str
    action: str = "collect_observation"
    score: float
    score_breakdown: Dict[str, float] = Field(default_factory=dict)
    constraints: ConstraintResult
    rationale: Optional[str] = None


class PlanResponse(BaseModel):
    mission_id: str
    policy_version: str
    tasks: List[TaskRecommendation]
    notes: List[str] = Field(default_factory=list)
    llm_used: bool = False
