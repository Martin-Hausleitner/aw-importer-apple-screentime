from __future__ import annotations

import click

from .activitywatch import ActivityWatchClient
from .parser import load_events


@click.group()
def main() -> None:
    """Import Apple iPhone Screen Time exports into local ActivityWatch."""


@main.command()
@click.argument("export_path", type=click.Path(exists=True, dir_okay=False))
@click.option("--bucket", default="aw-import-screentime_ios_manual", show_default=True, help="ActivityWatch bucket id.")
@click.option("--aw-url", default="http://127.0.0.1:5600/api/0", show_default=True, help="ActivityWatch API base URL.")
@click.option("--dry-run", is_flag=True, help="Parse and summarize without writing to ActivityWatch.")
def import_file(export_path: str, bucket: str, aw_url: str, dry_run: bool) -> None:
    events = load_events(export_path)
    click.echo(f"parsed={len(events)} bucket={bucket}")
    if not events:
        return
    total = sum(e.duration_seconds for e in events)
    click.echo(f"total_seconds={int(total)} first={min(e.start for e in events).isoformat()} last={max(e.start for e in events).isoformat()}")
    if dry_run:
        for e in events[:10]:
            click.echo(f"{e.start.isoformat()} {int(e.duration_seconds)}s {e.app} {e.device}")
        return
    client = ActivityWatchClient(aw_url)
    inserted = 0
    for event in events:
        client.insert_event(bucket, event)
        inserted += 1
    click.echo(f"inserted={inserted}")


if __name__ == "__main__":
    main()
