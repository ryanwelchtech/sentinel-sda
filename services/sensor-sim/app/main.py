import os
import time
import json
import random
import threading
from typing import Optional

import httpx
import jwt
from fastapi import FastAPI
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response


APP_NAME = os.getenv("SERVICE_NAME", "sensor-sim")
JWT_SECRET = os.getenv("JWT_SECRET", "changeme")
JWT_ISSUER = os.getenv("JWT_ISSUER", "sentinel-sda")

SENSOR_ID = os.getenv("SENSOR_ID", "radar-1")
SENSOR_TYPE = os.getenv("SENSOR_TYPE", "radar")

INGEST_URL = os.getenv("INGEST_URL", "http://ingestion-gateway:8000/observations")
TASKING_URL = os.getenv("TASKING_URL", "http://tasking-service:8000/tasking")

BASE_RATE_HZ = float(os.getenv("BASE_RATE_HZ", "1.5"))
OBJECT_POOL = int(os.getenv("OBJECT_POOL", "25"))
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT_SECONDS", "3.0"))
TASKING_POLL_SECONDS = float(os.getenv("TASKING_POLL_SECONDS", "5.0"))

sent_total = Counter("sda_sensor_sent_total", "Sensor events sent total", ["service", "sensor_id"])
send_fail = Counter("sda_sensor_send_fail_total", "Sensor send failures total", ["service", "sensor_id"])
current_rate = Gauge("sda_sensor_current_rate_hz", "Current sensor emission rate Hz", ["service", "sensor_id"])


def issue_token() -> str:
    payload = {"svc": f"{APP_NAME}:{SENSOR_ID}", "iss": JWT_ISSUER, "iat": int(time.time())}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def rand_object_id() -> str:
    return f"obj-{random.randint(1, OBJECT_POOL):03d}"


def gen_measurement(seed: int) -> dict:
    random.seed(seed + int(time.time()))
    return {
        "x_km": random.uniform(-20000, 20000),
        "y_km": random.uniform(-20000, 20000),
        "z_km": random.uniform(-20000, 20000),
        "vx_kms": random.uniform(-2.0, 2.0),
        "vy_kms": random.uniform(-2.0, 2.0),
        "vz_kms": random.uniform(-2.0, 2.0),
    }


def gen_quality() -> dict:
    return {
        "snr_db": round(random.uniform(5, 25), 2),
        "measurement_sigma": round(random.uniform(0.1, 1.0), 2),
    }


class SensorLoop:
    def __init__(self):
        self.rate_hz = BASE_RATE_HZ
        self.stop = threading.Event()
        self.token = issue_token()
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def poll_tasking(self):
        while not self.stop.is_set():
            try:
                with httpx.Client(timeout=HTTP_TIMEOUT) as client:
                    resp = client.get(f"{TASKING_URL}/{SENSOR_ID}", headers=self.headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        task = data.get("tasking", {}) or {}
                        rate = float(task.get("rate_hz", BASE_RATE_HZ))
                        self.rate_hz = max(0.2, min(10.0, rate))
                        current_rate.labels(APP_NAME, SENSOR_ID).set(self.rate_hz)
            except Exception:
                pass
            self.stop.wait(TASKING_POLL_SECONDS)

    def emit(self):
        while not self.stop.is_set():
            # Emit one observation
            oid = rand_object_id()
            evt = {
                "event_id": f"evt-{SENSOR_ID}-{int(time.time() * 1000)}",
                "sensor_id": SENSOR_ID,
                "sensor_type": SENSOR_TYPE,
                "timestamp": now_iso(),
                "object_id": oid,
                "measurement": gen_measurement(hash(oid) % 10000),
                "quality": gen_quality(),
                "integrity": {"signed": True, "signature": "demo-signature"},
            }

            try:
                with httpx.Client(timeout=HTTP_TIMEOUT) as client:
                    resp = client.post(INGEST_URL, json=evt, headers=self.headers)
                    if resp.status_code == 200:
                        sent_total.labels(APP_NAME, SENSOR_ID).inc()
                    else:
                        send_fail.labels(APP_NAME, SENSOR_ID).inc()
            except Exception:
                send_fail.labels(APP_NAME, SENSOR_ID).inc()

            # Sleep based on current rate
            period = 1.0 / max(0.1, self.rate_hz)
            self.stop.wait(period)


app = FastAPI(title=APP_NAME)
_loop = SensorLoop()
_task_thread = threading.Thread(target=_loop.poll_tasking, daemon=True)
_emit_thread = threading.Thread(target=_loop.emit, daemon=True)


@app.on_event("startup")
def startup():
    current_rate.labels(APP_NAME, SENSOR_ID).set(_loop.rate_hz)
    if not _task_thread.is_alive():
        _task_thread.start()
    if not _emit_thread.is_alive():
        _emit_thread.start()


@app.on_event("shutdown")
def shutdown():
    _loop.stop.set()


@app.get("/health")
def health():
    return {"status": "ok", "service": APP_NAME, "sensor_id": SENSOR_ID, "sensor_type": SENSOR_TYPE, "rate_hz": _loop.rate_hz}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/debug")
def debug():
    return {"headers": _loop.headers, "ingest_url": INGEST_URL, "tasking_url": TASKING_URL}
