---
name: aw-importer-apple-screentime
description: Operate and maintain the aw-importer-apple-screentime repository, an Apple iPhone Screen Time CSV/JSON to ActivityWatch importer. Use when an agent needs to parse Screen Time exports, dry-run or import app usage into ActivityWatch, verify Screen Time buckets, debug parser behavior, or change repository code/docs/tests.
---

# AW Apple Screen Time Importer

## Overview

Use this skill to import user-provided Apple iPhone Screen Time CSV/JSON files into local ActivityWatch and to maintain the importer safely. This repo does not log into Apple services; it only parses files the user already has or prepared.

## First Checks

Run these before operating or editing:

```bash
git status --short --branch
python3 -m venv .venv
. .venv/bin/activate
pip install -e . pytest ruff
pytest -q
```

Use `ruff check .` before committing code changes. Check ActivityWatch with:

```bash
curl -fsS http://127.0.0.1:5600/api/0/info
```

## Privacy Guardrails

- Do not commit Screen Time exports, ActivityWatch dumps, or personal app-usage summaries.
- Keep raw exports in `exports/` or outside the repo. Commit only synthetic fixtures.
- Report totals, date ranges, top apps, and bucket ids by default. Do not quote raw private rows unless asked.
- Dry-run output includes up to 10 raw app/device preview rows. Do not paste this output into chats, issues, logs, or commits unless the user explicitly approves.

## Input Formats

CSV rows must include:

- App name via `app`, `application`, `name`, `display_name`, or `bundle_id`.
- Start time via `start`, `start_time`, `timestamp`, or `date`.
- Either duration via `duration`, `duration_seconds`, `seconds`, or `total_seconds`, or end time via `end` or `end_time`.

Optional CSV columns:

- `device`
- `category`

JSON can be either a top-level array or an object with an `events` array. JSON accepted fields are narrower than CSV: app name can be `app`, `name`, or `bundle_id`; start time can be `start`, `timestamp`, or `date`; duration can be `duration_seconds`, `duration`, or `seconds`. JSON does not currently support `end`/`end_time`.

Duration values can be numeric seconds or text such as `45 min`, `1 h 30 min`, or `30`.

Use timezone-qualified timestamps where possible. Naive timestamps are interpreted as UTC. CSV rows without app or start are skipped; malformed duration/end values raise errors. JSON rows are stricter and missing required fields raise errors.

## Safe Import Workflow

Always dry-run first:

```bash
aw-importer-apple-screentime import-file exports/screen-time.csv --dry-run
```

Inspect parsed count, total seconds, first/last timestamps, and the first preview rows. Treat preview rows as private. If the dry-run looks wrong, fix the source mapping or parser before writing ActivityWatch events.

Import into a clear bucket:

```bash
aw-importer-apple-screentime import-file exports/screen-time.csv \
  --bucket aw-import-screentime_ios_manual
```

Use device-specific buckets when importing multiple devices:

```bash
aw-importer-apple-screentime import-file exports/screen-time.csv \
  --bucket aw-import-screentime_ios_MY-IPHONE
```

## ActivityWatch Verification

List Screen Time buckets:

```bash
python3 - <<'PY'
import json, urllib.request
buckets = json.load(urllib.request.urlopen("http://127.0.0.1:5600/api/0/buckets/"))
for bucket_id, meta in sorted(buckets.items()):
    if bucket_id.startswith("aw-import-screentime"):
        print(bucket_id, meta.get("type"), meta.get("created"))
PY
```

Expected default bucket:

```text
aw-import-screentime_ios_manual
```

Expected event type is `app`, with event data similar to:

```json
{
  "app": "Signal",
  "device": "iPhone",
  "category": "Social",
  "source": "apple_screentime_export",
  "event_hash": "..."
}
```

After import, fetch events from the target bucket for the imported date range and verify the count is plausible, timestamps match the dry-run range, durations are positive, and event data includes `app`, `device`, `source=apple_screentime_export`, and `event_hash`.

## Idempotency

The CLI adds `event_hash`, but it does not deduplicate before inserting. Re-running the same overlapping file posts duplicate ActivityWatch events. Use a wrapper or manual verification before re-importing overlapping files.

## Development Notes

- CLI entry point lives in `src/aw_importer_apple_screentime/cli.py`.
- CSV/JSON parsing and duration handling live in `src/aw_importer_apple_screentime/parser.py`.
- ActivityWatch writes live in `src/aw_importer_apple_screentime/activitywatch.py`.
- Preserve tolerant parsing for common column names.
- Preserve stable `event_hash` generation.
- Add tests for new columns, duration formats, validation behavior, and event data.
- Use synthetic fixtures only. Do not add real Screen Time exports.
- Update `README.md`, `AGENTS.md`, and this skill when commands, bucket ids, or operational workflows change.
