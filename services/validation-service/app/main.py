import os
import time
from typing import Optional

import httpx
import jwt
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response


APP_NAME = os.getenv("SERVICE_NAME", "validation-service")
JWT_SECRET = os.getenv("JWT_SECRET", "changeme")
JWT_ISSUER = os.getenv("JWT_ISSUER", "sentinel-sda")
FUSION_URL = os.getenv("FUSION_URL", "http://fusion-engine:8000/fuse")
REQ_TIMEOUT = float(os.getenv("HTTP_TIMEOUT_SECONDS", "3.0"))

valid_total = Counter("sda_valid_total", "Validated observations total", ["service"])
invalid_total = Counter("sda_invalid_total", "Invalid observations total", ["service"])
forward_fail = Counter("sda_valid_forward_fail_total", "Forward failures", ["service"])
handler_latency = Histogram("sda_validation_latency_seconds", "Validation handler latency", ["service"])


class ObservationEvent(BaseModel):
    event_id: str
    sensor_id: str
    sensor_type: str
    timestamp: str
    object_id: str
    measurement: dict = Field(default_factory=dict)
    quality: dict = Field(default_factory=dict)
    integrity: Optional[dict] = None


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


def sanity_check(evt: ObservationEvent) -> list[str]:
    flags = []
    m = evt.measurement or {}
    # Minimal sanity: ensure numeric-ish required keys exist
    required = ["x_km", "y_km", "z_km", "vx_kms", "vy_kms", "vz_kms"]
    for k in required:
        if k not in m:
            flags.append(f"missing_measurement_{k}")
    # Basic bounds
    try:
        if abs(float(m.get("x_km", 0))) > 50000 or abs(float(m.get("y_km", 0))) > 50000 or abs(float(m.get("z_km", 0))) > 50000:
            flags.append("position_out_of_bounds")
        if abs(float(m.get("vx_kms", 0))) > 20 or abs(float(m.get("vy_kms", 0))) > 20 or abs(float(m.get("vz_kms", 0))) > 20:
            flags.append("velocity_out_of_bounds")
    except Exception:
        flags.append("non_numeric_measurement")

    # Integrity placeholder: if integrity.signed true but no signature => suspicious
    integ = evt.integrity or {}
    if integ.get("signed") is True and not integ.get("signature"):
        flags.append("signed_missing_signature")

    return flags


app = FastAPI(title=APP_NAME)


@app.get("/health")
def health():
    return {"status": "ok", "service": APP_NAME, "ts": int(time.time())}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/validate")
async def validate(evt: ObservationEvent, authorization: Optional[str] = Header(default=None)):
    start = time.time()
    verify_bearer(authorization)

    flags = sanity_check(evt)
    if flags:
        invalid_total.labels(APP_NAME).inc()
        raise HTTPException(status_code=422, detail={"reason": "validation_failed", "flags": flags})

    valid_total.labels(APP_NAME).inc()

    headers = {"Authorization": authorization}
    try:
        async with httpx.AsyncClient(timeout=REQ_TIMEOUT) as client:
            resp = await client.post(FUSION_URL, json=evt.model_dump(), headers=headers)
            if resp.status_code != 200:
                forward_fail.labels(APP_NAME).inc()
                raise HTTPException(status_code=502, detail=f"Fusion forward failed: {resp.text}")
            return resp.json()
    finally:
        handler_latency.labels(APP_NAME).observe(time.time() - start)
