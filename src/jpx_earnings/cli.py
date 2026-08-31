from __future__ import annotations

import argparse
from pathlib import Path

from jpx_earnings.fetch import FetchError, fetch_index_and_events
from jpx_earnings.store import write_outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="jpx-earnings")
    sub = parser.add_subparsers(dest="cmd", required=True)

    fetch_p = sub.add_parser("fetch", help="Download JPX monthly xlsx and write JSON")
    fetch_p.add_argument("--out", type=Path, default=Path("docs/v1"))
    fetch_p.add_argument(
        "--replace",
        action="store_true",
        help="Do not merge with existing events.json",
    )

    args = parser.parse_args(argv)
    if args.cmd == "fetch":
        try:
            result = fetch_index_and_events()
        except FetchError as e:
            print(f"fetch failed, leaving existing JSON unchanged: {e}")
            return 1
        if not result["incoming"]:
            print("fetch returned zero dated events; leaving existing JSON unchanged")
            return 1
        events_path, manifest_path = write_outputs(
            args.out,
            result["incoming"],
            dropped_undated=result["dropped_undated"],
            dropped_unmapped_fq=result["dropped_unmapped_fq"],
            sources=result["sources"],
            merge_existing=not args.replace,
        )
        print(f"wrote {events_path} and {manifest_path}")
        return 0
    return 2
