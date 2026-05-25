# Agent Guide

This repository imports manually prepared Apple iPhone Screen Time CSV/JSON exports into local ActivityWatch.

## Start Here

- Use the repo-local skill at `skills/aw-importer-apple-screentime/SKILL.md` for operating, debugging, or changing this project.
- Read `README.md` for supported input formats and CLI examples.
- Check `git status --short --branch` before editing. Do not overwrite unrelated local changes.

## Privacy Rules

- Never commit Screen Time exports, ActivityWatch dumps, or personal app-usage summaries.
- Keep source exports in `exports/` or outside the repo; add only synthetic fixtures to tests.
- Report totals, date ranges, top apps, and bucket ids by default. Do not quote raw private rows unless asked.
- Dry-run output includes up to 10 raw app/device preview rows. Do not paste it into chats, issues, logs, or commits without explicit approval.

## Development Loop

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e . pytest ruff
pytest -q
ruff check .
```

ActivityWatch is expected at `http://127.0.0.1:5600/api/0`.

## Operational Checklist

- Validate ActivityWatch with `curl -fsS http://127.0.0.1:5600/api/0/info`.
- Run `aw-importer-apple-screentime import-file <export.csv|export.json> --dry-run` before importing.
- Import into a clear bucket such as `aw-import-screentime_ios_manual` or `aw-import-screentime_ios_<device-id>`.
- Verify `aw-import-screentime*` buckets and sample imported events after import.

## When Changing Code

- Preserve support for CSV and JSON input.
- Keep duration parsing tolerant of numeric seconds and human-readable values such as `45 min` or `1 h 30 min`.
- Add tests for new input columns, formats, validation behavior, and ActivityWatch event data.
- Update `README.md`, this file, and the repo-local skill whenever workflows or commands change.
