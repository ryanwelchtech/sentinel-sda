import os
import time
from typing import Optional

import jwt
from fastapi import FastAPI, Header, HTTPException
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response


APP_NAME = os.getenv("SERVICE_NAME", "tasking-service")
JWT_SECRET = os.getenv("JWT_SECRET", "changeme")
JWT_ISSUER = os.getenv("JWT_ISSUER", "sentinel-sda")

tasking_updates = Counter("sda_tasking_updates_total", "Tasking updates total", ["service"])
tasking_reads = Counter("sda_tasking_reads_total", "Tasking reads total", ["service"])

# In-memory store (OK for sandbox demo; replace with Redis later if desired)
LATEST_TASKING: dict = {"generated_at": 0, "policy": "none", "summary": {}, "sensors": {}}


def verify_bearer(auth: Optional[str]) -> dict:
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = auth.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], issuer=JWT_ISSUER)
        if payload.get("svc") is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return payload
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


app = FastAPI(title=APP_NAME)


@app.get("/health")
def health():
    return {"status": "ok", "service": APP_NAME, "ts": int(time.time()), "tasking_ts": LATEST_TASKING.get("generated_at", 0)}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/tasking")
def set_tasking(body: dict, authorization: Optional[str] = Header(default=None)):
    verify_bearer(authorization)
    global LATEST_TASKING
    LATEST_TASKING = body
    tasking_updates.labels(APP_NAME).inc()
    return {"status": "ok", "stored_at": int(time.time())}


@app.get("/tasking")
def get_tasking(authorization: Optional[str] = Header(default=None)):
    verify_bearer(authorization)
    tasking_reads.labels(APP_NAME).inc()
    return LATEST_TASKING


@app.get("/tasking/{sensor_id}")
def get_tasking_for_sensor(sensor_id: str, authorization: Optional[str] = Header(default=None)):
    verify_bearer(authorization)
    tasking_reads.labels(APP_NAME).inc()
    sensors = LATEST_TASKING.get("sensors", {}) or {}
    return {"sensor_id": sensor_id, "tasking": sensors.get(sensor_id, {"rate_hz": 1.0}), "generated_at": LATEST_TASKING.get("generated_at", 0)}
