from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse_time(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return now_utc()


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))
