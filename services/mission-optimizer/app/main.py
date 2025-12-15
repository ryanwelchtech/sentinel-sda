import os
import time
import json
import threading
from typing import Optional

import jwt
import redis
import httpx
from fastapi import FastAPI, Header, HTTPException
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response


APP_NAME = os.getenv("SERVICE_NAME", "mission-optimizer")
JWT_SECRET = os.getenv("JWT_SECRET", "changeme")
JWT_ISSUER = os.getenv("JWT_ISSUER", "sentinel-sda")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

TASKING_URL = os.getenv("TASKING_URL", "http://tasking-service:8000/tasking")
OPT_INTERVAL = float(os.getenv("OPT_INTERVAL_SECONDS", "5.0"))
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT_SECONDS", "3.0"))

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

opt_runs = Counter("sda_optimizer_runs_total", "Optimizer runs total", ["service"])
opt_last_ts = Gauge("sda_optimizer_last_run_timestamp", "Last optimizer run unix timestamp", ["service"])
opt_tasking_pushed = Counter("sda_optimizer_tasking_pushed_total", "Tasking pushes total", ["service"])


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


def issue_token() -> str:
    payload = {"svc": APP_NAME, "iss": JWT_ISSUER, "iat": int(time.time())}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def idx_key() -> str:
    return "track:index"


def track_key(object_id: str) -> str:
    return f"track:{object_id}"


def compute_tasking(tracks: list[dict]) -> dict:
    """
    Simple mission logic:
    - Higher confidence tracks get less frequent re-tasking
    - Lower confidence tracks get higher priority
    - Convert into per-sensor "rate_hz" recommendations
    """
    # Default rates (Hz)
    radar_rate = 2.0
    optical_rate = 1.0
    space_rate = 1.5

    # Mission scoring: if many low-confidence tracks, increase sensor rates
    low_conf = sum(1 for t in tracks if float(t.get("confidence", 0.0)) < 0.75)
    total = max(1, len(tracks))
    pressure = low_conf / total  # 0..1

    radar_rate = min(5.0, radar_rate + 3.0 * pressure)
    optical_rate = min(3.0, optical_rate + 2.0 * pressure)
    space_rate = min(4.0, space_rate + 2.5 * pressure)

    return {
        "generated_at": int(time.time()),
        "policy": "pressure_based_v1",
        "summary": {"tracks_total": total, "low_conf_tracks": low_conf, "pressure": round(pressure, 3)},
        "sensors": {
            "radar-1": {"rate_hz": round(radar_rate, 2)},
            "optical-1": {"rate_hz": round(optical_rate, 2)},
            "space-1": {"rate_hz": round(space_rate, 2)},
        },
    }


def optimizer_loop(stop_event: threading.Event):
    token = issue_token()
    headers = {"Authorization": f"Bearer {token}"}

    while not stop_event.is_set():
        try:
            object_ids = list(r.smembers(idx_key()))
            tracks = []
            for oid in object_ids[:200]:
                raw = r.hget(track_key(oid), "json")
                if raw:
                    tracks.append(json.loads(raw))

            tasking = compute_tasking(tracks)

            with httpx.Client(timeout=HTTP_TIMEOUT) as client:
                resp = client.post(TASKING_URL, json=tasking, headers=headers)
                resp.raise_for_status()

            opt_runs.labels(APP_NAME).inc()
            opt_tasking_pushed.labels(APP_NAME).inc()
            opt_last_ts.labels(APP_NAME).set(int(time.time()))
        except Exception:
            # Intentionally swallow errors to keep loop alive in demo environments
            pass

        stop_event.wait(OPT_INTERVAL)


app = FastAPI(title=APP_NAME)
_stop = threading.Event()
_thread = threading.Thread(target=optimizer_loop, args=(_stop,), daemon=True)


@app.on_event("startup")
def startup():
    if not _thread.is_alive():
        _thread.start()


@app.on_event("shutdown")
def shutdown():
    _stop.set()


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
