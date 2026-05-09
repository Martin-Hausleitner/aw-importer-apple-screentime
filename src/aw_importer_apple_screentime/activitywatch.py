from __future__ import annotations

import hashlib
import json
import socket

import httpx

AW_BASE_URL = "http://127.0.0.1:5600/api/0"
BUCKET_PREFIX = "aw-import-screentime"


def stable_hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class ActivityWatchClient:
    def __init__(self, base_url: str = AW_BASE_URL, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def hostname(self) -> str:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                r = client.get(f"{self.base_url}/info")
                if r.status_code == 200 and r.json().get("hostname"):
                    return str(r.json()["hostname"])
        except Exception:
            pass
        return socket.gethostname()

    def ensure_bucket(self, bucket_id: str, event_type: str = "app") -> None:
        payload = {"client": "aw-importer-apple-screentime", "type": event_type, "hostname": self.hostname()}
        with httpx.Client(timeout=self.timeout) as client:
            r = client.post(f"{self.base_url}/buckets/{bucket_id}", json=payload)
            if r.status_code not in (200, 201, 304):
                r.raise_for_status()

    def insert_event(self, bucket_id: str, event) -> int:
        self.ensure_bucket(bucket_id)
        payload = {"timestamp": event.start.isoformat(), "duration": event.duration_seconds, "data": event.data}
        with httpx.Client(timeout=self.timeout) as client:
            r = client.post(f"{self.base_url}/buckets/{bucket_id}/events", json=payload)
            r.raise_for_status()
            value = r.json()
            return int(value) if value is not None else -1
