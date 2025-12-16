from __future__ import annotations
import os
from fastapi import FastAPI
from dotenv import load_dotenv

from .models import MissionRequest, PlanResponse
from .policy import load_policy
from .planner import build_plan

load_dotenv()

app = FastAPI(title="Mission Planning Agent", version="1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/policy")
def get_policy():
    path = os.getenv("POLICY_PATH", "config/policy.yaml")
    pol = load_policy(path)
    return {
        "policy_version": pol.policy_version,
        "hard_constraints": pol.hard_constraints,
        "scoring": pol.scoring,
        "priority_rules": pol.priority_rules,
        "tie_break": pol.tie_break,
        "sensor_count": len(pol.sensors),
    }


@app.post("/plan", response_model=PlanResponse)
def plan(req: MissionRequest):
    return build_plan(req)


def run():
    import uvicorn
    port = int(os.getenv("PORT", "9000"))
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)


if __name__ == "__main__":
    run()
