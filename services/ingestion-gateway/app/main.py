import os
import time
from typing import Optional

import httpx
import jwt
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response


APP_NAME = os.getenv("SERVICE_NAME", "ingestion-gateway")
JWT_SECRET = os.getenv("JWT_SECRET", "changeme")
JWT_ISSUER = os.getenv("JWT_ISSUER", "sentinel-sda")
FORWARD_URL = os.getenv("VALIDATION_URL", "http://validation-service:8000/validate")

REQ_TIMEOUT = float(os.getenv("HTTP_TIMEOUT_SECONDS", "3.0"))

ingest_total = Counter("sda_ingest_total", "Total observations received", ["service"])
ingest_forward_fail = Counter("sda_ingest_forward_fail_total", "Forward failures", ["service"])
ingest_latency = Histogram("sda_ingest_latency_seconds", "Ingest handler latency", ["service"])


class ObservationEvent(BaseModel):
    event_id: str
    sensor_id: str
    sensor_type: str
    timestamp: str
    object_id: str
    measurement: dict = Field(default_factory=dict)
    quality: dict = Field(default_factory=dict)
    integrity: Optional[dict] = None


def verify_bearer(auth: Optional[str]) -> None:
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = auth.split(" ", 1)[1].strip()
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"], issuer=JWT_ISSUER)
        if payload.get("svc") is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except jwt.PyJWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


app = FastAPI(title=APP_NAME)


@app.get("/health")
def health():
    return {"status": "ok", "service": APP_NAME, "ts": int(time.time())}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/observations")
async def observations(evt: ObservationEvent, authorization: Optional[str] = Header(default=None)):
    start = time.time()
    verify_bearer(authorization)
    ingest_total.labels(APP_NAME).inc()

    headers = {"Authorization": authorization}
    try:
        async with httpx.AsyncClient(timeout=REQ_TIMEOUT) as client:
            resp = await client.post(FORWARD_URL, json=evt.model_dump(), headers=headers)
            if resp.status_code != 200:
                ingest_forward_fail.labels(APP_NAME).inc()
                raise HTTPException(status_code=502, detail=f"Validation forward failed: {resp.text}")
            return resp.json()
    finally:
        ingest_latency.labels(APP_NAME).observe(time.time() - start)
