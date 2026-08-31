from __future__ import annotations

from io import BytesIO
from urllib.parse import urljoin

import httpx
import pandas as pd
from bs4 import BeautifulSoup

from jpx_earnings.normalize import (
    event_row,
    map_fq,
    normalize_code,
    parse_scheduled_date,
)

INDEX_URL = (
    "https://www.jpx.co.jp/listing/event-schedules/financial-announcement/index.html"
)
USER_AGENT = "jp-earnings-date-fetcher/0.1 (+https://github.com/)"


class FetchError(RuntimeError):
    pass


def _client() -> httpx.Client:
    return httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=60.0,
        follow_redirects=True,
    )


def is_monthly_cohort_link(anchor_text: str, href: str) -> bool:
    if not href.lower().endswith(".xlsx"):
        return False
    text = anchor_text or ""
    if "翌営業日" in text:
        return False
    return "四半期末" in text or "期末を迎えた" in text


def list_monthly_xlsx(html: str, base_url: str = INDEX_URL) -> list[tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    found: list[tuple[str, str]] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        text = a.get_text(" ", strip=True)
        if is_monthly_cohort_link(text, href):
            found.append((urljoin(base_url, href), text))
    return found


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).split("\n")[0].strip() for c in df.columns]
    return df


def parse_xlsx_bytes(content: bytes) -> tuple[list[dict[str, str]], int, int]:
    df = pd.read_excel(BytesIO(content), engine="openpyxl", skiprows=4, header=0)
    df = _clean_columns(df)
    required = {"コード", "種別", "決算発表予定日"}
    if not required.issubset(set(df.columns)):
        raise FetchError(f"unexpected columns: {list(df.columns)}")

    events: list[dict[str, str]] = []
    dropped_undated = 0
    dropped_unmapped = 0
    for _, row in df.iterrows():
        code = normalize_code(row.get("コード"))
        fq = map_fq(row.get("種別"))
        scheduled = parse_scheduled_date(row.get("決算発表予定日"))
        if code is None:
            continue
        if scheduled is None:
            dropped_undated += 1
            continue
        if fq is None:
            dropped_unmapped += 1
            continue
        ev = event_row(code, row.get("種別"), row.get("決算発表予定日"))
        if ev:
            events.append(ev)
    return events, dropped_undated, dropped_unmapped


def fetch_index_and_events(client: httpx.Client | None = None) -> dict:
    own = client is None
    client = client or _client()
    try:
        resp = client.get(INDEX_URL)
        resp.raise_for_status()
        links = list_monthly_xlsx(resp.text)
        if not links:
            raise FetchError("no monthly xlsx links found on JPX index")

        incoming: list[dict[str, str]] = []
        dropped_undated = 0
        dropped_unmapped = 0
        sources: list[dict[str, str]] = []
        for url, label in links:
            file_resp = client.get(url)
            file_resp.raise_for_status()
            evs, u, m = parse_xlsx_bytes(file_resp.content)
            incoming.extend(evs)
            dropped_undated += u
            dropped_unmapped += m
            sources.append({"url": url, "label": label})

        return {
            "incoming": incoming,
            "dropped_undated": dropped_undated,
            "dropped_unmapped_fq": dropped_unmapped,
            "sources": sources,
        }
    finally:
        if own:
            client.close()
