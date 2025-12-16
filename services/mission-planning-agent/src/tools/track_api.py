from __future__ import annotations
from typing import List
import os
import time
import jwt
import requests
from ..models import Track


def mint_service_token() -> str:
    secret = os.getenv("JWT_SECRET", "")
    if not secret:
        raise RuntimeError("JWT_SECRET not set (expected from secret-jwt)")

    payload = {
        "sub": "mission-planning-agent",
        "role": "service",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def fetch_tracks(limit: int = 100) -> List[Track]:
    base = os.getenv("TRACK_API_BASE", "http://track-api:8000").rstrip("/")
    token = mint_service_token()

    url = f"{base}/tracks?limit={limit}"
    headers = {"Authorization": f"Bearer {token}"}

    r = requests.get(url, headers=headers, timeout=10)
    r.raise_for_status()

    data = r.json()
    if isinstance(data, dict) and "tracks" in data:
        data = data["tracks"]

    tracks: List[Track] = []
    for item in data:
        try:
            tracks.append(Track.model_validate(item))
        except Exception:
            continue
    return tracks
