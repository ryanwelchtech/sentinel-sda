import os
import time
from typing import Optional, Any

import jwt
import redis
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response


APP_NAME = os.getenv("SERVICE_NAME", "fusion-engine")
JWT_SECRET = os.getenv("JWT_SECRET", "changeme")
JWT_ISSUER = os.getenv("JWT_ISSUER", "sentinel-sda")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

fuse_total = Counter("sda_fuse_total", "Fused observations total", ["service"])
fuse_latency = Histogram("sda_fuse_latency_seconds", "Fusion handler latency", ["service"])


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


def track_key(object_id: str) -> str:
    return f"track:{object_id}"


def idx_key() -> str:
    return "track:index"


def safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def fuse(prev: Optional[dict], obs: ObservationEvent) -> dict:
    m = obs.measurement or {}
    # Previous state
    if prev is None:
        prev_state = {
            "x_km": safe_float(m.get("x_km")),
            "y_km": safe_float(m.get("y_km")),
            "z_km": safe_float(m.get("z_km")),
            "vx_kms": safe_float(m.get("vx_kms")),
            "vy_kms": safe_float(m.get("vy_kms")),
            "vz_kms": safe_float(m.get("vz_kms")),
        }
        confidence = 0.6
        sources = [{"sensor_id": obs.sensor_id, "timestamp": obs.timestamp}]
        flags = ["OK"]
    else:
        prev_state = prev.get("state", {})
        # Weighted update: give new obs weight w
        w = 0.35
        new_state = {}
        for k in ["x_km", "y_km", "z_km", "vx_kms", "vy_kms", "vz_kms"]:
            new_state[k] = (1 - w) * safe_float(prev_state.get(k)) + w * safe_float(m.get(k))
        prev_conf = safe_float(prev.get("confidence"), 0.6)
        confidence = min(0.99, prev_conf + 0.02)
        sources = (prev.get("sources") or [])[-9:] + [{"sensor_id": obs.sensor_id, "timestamp": obs.timestamp}]
        flags = prev.get("flags") or ["OK"]
        prev_state = new_state

    return {
        "track_id": f"trk-{obs.object_id}",
        "object_id": obs.object_id,
        "last_update": obs.timestamp,
        "state": prev_state,
        "confidence": round(confidence, 3),
        "sources": sources,
        "flags": flags,
    }


app = FastAPI(title=APP_NAME)


@app.get("/health")
def health():
    # ping redis
    try:
        r.ping()
        redis_ok = True
    except Exception:
        redis_ok = False
    return {"status": "ok" if redis_ok else "degraded", "service": APP_NAME, "redis": redis_ok, "ts": int(time.time())}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/fuse")
def fuse_observation(evt: ObservationEvent, authorization: Optional[str] = Header(default=None)):
    start = time.time()
    verify_bearer(authorization)

    key = track_key(evt.object_id)
    prev = r.hgetall(key) or None
    prev_obj = None
    if prev:
        # redis hash stores flattened fields; we store JSON as a single field to keep it simple
        # but for backward-compat, try json field first.
        import json
        raw = prev.get("json")
        if raw:
            prev_obj = json.loads(raw)

    updated = fuse(prev_obj, evt)

    import json
    r.hset(key, mapping={"json": json.dumps(updated)})
    r.sadd(idx_key(), evt.object_id)

    fuse_total.labels(APP_NAME).inc()
    fuse_latency.labels(APP_NAME).observe(time.time() - start)

    return {"status": "ok", "track": updated}
