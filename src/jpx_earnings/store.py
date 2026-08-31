from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from jpx_earnings.normalize import merge_events

INDEX_URL = (
    "https://www.jpx.co.jp/listing/event-schedules/financial-announcement/index.html"
)


def load_events(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"{path} must be a JSON array")
    return data


def write_outputs(
    out_dir: Path,
    incoming: list[dict[str, str]],
    *,
    dropped_undated: int,
    dropped_unmapped_fq: int,
    sources: list[dict[str, str]],
    merge_existing: bool = True,
) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    events_path = out_dir / "events.json"
    existing = load_events(events_path) if merge_existing else []
    events = merge_events(existing, incoming)

    events_path.write_text(
        json.dumps(events, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    manifest = {
        "source": INDEX_URL,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event_count": len(events),
        "incoming_count": len(incoming),
        "dropped_undated": dropped_undated,
        "dropped_unmapped_fq": dropped_unmapped_fq,
        "xlsx": sources,
    }
    manifest_path = out_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return events_path, manifest_path
