from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from dateutil import parser as dtparser


@dataclass(frozen=True)
class ScreenTimeEvent:
    start: datetime
    duration_seconds: float
    app: str
    device: str = "iPhone"
    category: str | None = None
    source: str = "apple_screentime_export"

    @property
    def data(self) -> dict:
        data = {"app": self.app, "device": self.device, "source": self.source}
        if self.category:
            data["category"] = self.category
        return data


def parse_duration(value: str | int | float) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip().lower()
    if not s:
        raise ValueError("empty duration")
    try:
        return float(s)
    except ValueError:
        pass
    total = 0.0
    parts = s.replace(",", ".").split()
    i = 0
    while i < len(parts):
        try:
            num = float(parts[i])
        except ValueError:
            i += 1
            continue
        unit = parts[i + 1] if i + 1 < len(parts) else "seconds"
        if unit.startswith(("h", "hour", "std", "stunde")):
            total += num * 3600
        elif unit.startswith(("m", "min")):
            total += num * 60
        elif unit.startswith(("s", "sec", "sek")):
            total += num
        i += 2
    if total <= 0:
        raise ValueError(f"unsupported duration: {value!r}")
    return total


def parse_datetime(value: str) -> datetime:
    dt = dtparser.parse(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _first(row: dict, names: tuple[str, ...], default: str = "") -> str:
    lower = {str(k).strip().lower(): v for k, v in row.items()}
    for name in names:
        if name.lower() in lower and lower[name.lower()] not in (None, ""):
            return str(lower[name.lower()]).strip()
    return default


def parse_csv(path: str | Path) -> list[ScreenTimeEvent]:
    events: list[ScreenTimeEvent] = []
    with Path(path).open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            app = _first(row, ("app", "application", "name", "display_name", "bundle_id"))
            start_raw = _first(row, ("start", "start_time", "timestamp", "date"))
            end_raw = _first(row, ("end", "end_time"))
            duration_raw = _first(row, ("duration", "duration_seconds", "seconds", "total_seconds"))
            if not app or not start_raw:
                continue
            start = parse_datetime(start_raw)
            if duration_raw:
                duration = parse_duration(duration_raw)
            elif end_raw:
                duration = max(0.0, (parse_datetime(end_raw) - start).total_seconds())
            else:
                raise ValueError(f"row needs duration or end time: {row!r}")
            events.append(ScreenTimeEvent(start=start, duration_seconds=duration, app=app, device=_first(row, ("device",), "iPhone"), category=_first(row, ("category",), "") or None))
    return events


def parse_json(path: str | Path) -> list[ScreenTimeEvent]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    rows = payload.get("events", payload if isinstance(payload, list) else [])
    events: list[ScreenTimeEvent] = []
    for row in rows:
        start = parse_datetime(str(row.get("start") or row.get("timestamp") or row.get("date")))
        duration = row.get("duration_seconds", row.get("duration", row.get("seconds")))
        events.append(ScreenTimeEvent(start=start, duration_seconds=parse_duration(duration), app=str(row.get("app") or row.get("name") or row.get("bundle_id")), device=str(row.get("device") or "iPhone"), category=row.get("category")))
    return events


def load_events(path: str | Path) -> list[ScreenTimeEvent]:
    p = Path(path)
    if p.suffix.lower() == ".json":
        return parse_json(p)
    return parse_csv(p)
