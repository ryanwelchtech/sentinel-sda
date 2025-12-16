from __future__ import annotations
from typing import List, Optional
from ..policy import SensorDef, load_policy
import os

def list_sensors(preferred: Optional[List[str]] = None) -> List[SensorDef]:
    policy_path = os.getenv("POLICY_PATH", "config/policy.yaml")
    pol = load_policy(policy_path)
    sensors = pol.sensors
    if preferred:
        allowed = set(preferred)
        sensors = [s for s in sensors if s.sensor_id in allowed]
    return sensors
