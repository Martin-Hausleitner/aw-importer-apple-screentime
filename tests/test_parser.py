from pathlib import Path

from aw_importer_apple_screentime.parser import load_events, parse_duration


def test_parse_duration_units():
    assert parse_duration("1 h 30 min") == 5400
    assert parse_duration("45 min") == 2700
    assert parse_duration("30") == 30


def test_load_csv(tmp_path: Path):
    p = tmp_path / "screen.csv"
    p.write_text("app,start,duration_seconds,device,category\nSignal,2026-05-09T10:00:00+00:00,120,iPhone,Social\n", encoding="utf-8")
    events = load_events(p)
    assert len(events) == 1
    assert events[0].app == "Signal"
    assert events[0].duration_seconds == 120
    assert events[0].data["category"] == "Social"
