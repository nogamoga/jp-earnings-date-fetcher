"""Merge OHLCV with events.json (backward asof by code)."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


def merge_prices(prices: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    prices = prices.copy()
    events = events.copy()
    prices["code"] = prices["code"].astype(str).str.zfill(4)
    events["code"] = events["code"].astype(str).str.zfill(4)
    prices["date"] = pd.to_datetime(prices["date"])
    events["scheduled_date"] = pd.to_datetime(events["scheduled_date"])
    prices = prices.sort_values(["code", "date"])
    events = events.sort_values(["code", "scheduled_date"])
    out = pd.merge_asof(
        prices,
        events,
        left_on="date",
        right_on="scheduled_date",
        by="code",
        direction="backward",
    )
    out["elapsed_days"] = (out["date"] - out["scheduled_date"]).dt.days
    return out.drop(columns=["scheduled_date"])


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--prices", type=Path, required=True)
    p.add_argument("--events", type=Path, default=Path("docs/v1/events.json"))
    p.add_argument("--out", type=Path, default=Path("merged.csv"))
    args = p.parse_args()

    prices = pd.read_csv(args.prices, dtype={"code": str})
    events = pd.read_json(args.events, dtype={"code": str})
    merge_prices(prices, events).to_csv(args.out, index=False)


if __name__ == "__main__":
    main()
