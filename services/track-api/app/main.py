import os
import time
import json
from typing import Optional

import jwt
import redis
from fastapi import FastAPI, Header, HTTPException
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response


APP_NAME = os.getenv("SERVICE_NAME", "track-api")
JWT_SECRET = os.getenv("JWT_SECRET", "changeme")
JWT_ISSUER = os.getenv("JWT_ISSUER", "sentinel-sda")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

track_queries = Counter("sda_track_queries_total", "Track queries total", ["service"])


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


app = FastAPI(title=APP_NAME)


@app.get("/health")
def health():
    try:
        r.ping()
        redis_ok = True
    except Exception:
        redis_ok = False
    return {"status": "ok" if redis_ok else "degraded", "service": APP_NAME, "redis": redis_ok, "ts": int(time.time())}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/tracks")
def list_tracks(authorization: Optional[str] = Header(default=None), min_conf: float = 0.0, limit: int = 50):
    verify_bearer(authorization)
    track_queries.labels(APP_NAME).inc()

    object_ids = list(r.smembers(idx_key()))
    results = []
    for oid in object_ids[: max(1, limit)]:
        raw = r.hget(track_key(oid), "json")
        if not raw:
            continue
        t = json.loads(raw)
        if float(t.get("confidence", 0.0)) >= float(min_conf):
            results.append(t)

    return {"count": len(results), "tracks": results}


@app.get("/tracks/{object_id}")
def get_track(object_id: str, authorization: Optional[str] = Header(default=None)):
    verify_bearer(authorization)
    track_queries.labels(APP_NAME).inc()

    raw = r.hget(track_key(object_id), "json")
    if not raw:
        raise HTTPException(status_code=404, detail="Track not found")
    return json.loads(raw)
