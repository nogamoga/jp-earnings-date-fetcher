from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, timedelta
from typing import Any

FQ_VALUES = frozenset({"FY", "1Q", "2Q", "3Q"})

_CODE_RE = re.compile(r"^\d{3,5}$")


def _nfkc(value: Any) -> str:
    return unicodedata.normalize("NFKC", str(value)).strip()


def normalize_code(value: Any) -> str | None:
    if value is None:
        return None
    text = _nfkc(value).split(".")[0]
    if not _CODE_RE.match(text):
        return None
    if len(text) <= 4:
        return text.zfill(4)
    return text


def map_fq(kind: Any) -> str | None:
    if kind is None:
        return None
    s = _nfkc(kind).replace(" ", "").replace("\u3000", "")
    if not s:
        return None
    if "第3" in s or "3Q" in s.upper() or s.startswith("3Q"):
        return "3Q"
    if "第2" in s or "2Q" in s.upper() or "中間" in s:
        return "2Q"
    if "第1" in s or "1Q" in s.upper():
        return "1Q"
    if "本決算" in s or "通期" in s or s.upper() == "FY":
        return "FY"
    return None


def parse_scheduled_date(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        # Excel serial date
        serial = int(value)
        if serial < 1:
            return None
        try:
            return (date(1899, 12, 30) + timedelta(days=serial)).isoformat()
        except OverflowError:
            return None
    text = _nfkc(value)
    if not text or text in {"未定", "-", "―", "－", "nan", "NaT", "None"}:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y/%m/%-d", "%Y年%m月%d日"):
        try:
            return datetime.strptime(text.replace("／", "/"), fmt).date().isoformat()
        except ValueError:
            continue
    try:
        return datetime.strptime(text, "%Y/%m/%d").date().isoformat()
    except ValueError:
        pass
    m = re.match(r"^(\d{4})[/-](\d{1,2})[/-](\d{1,2})", text)
    if m:
        y, mo, d = map(int, m.groups())
        try:
            return date(y, mo, d).isoformat()
        except ValueError:
            return None
    return None


def event_row(code: Any, kind: Any, scheduled: Any) -> dict[str, str] | None:
    c = normalize_code(code)
    fq = map_fq(kind)
    d = parse_scheduled_date(scheduled)
    if not c or not fq or not d:
        return None
    return {"code": c, "scheduled_date": d, "fq": fq}


def merge_events(
    existing: list[dict[str, str]], incoming: list[dict[str, str]]
) -> list[dict[str, str]]:
    by_key: dict[tuple[str, str], dict[str, str]] = {}
    for row in existing:
        by_key[(row["code"], row["scheduled_date"])] = row
    for row in incoming:
        by_key[(row["code"], row["scheduled_date"])] = row
    return sorted(by_key.values(), key=lambda r: (r["code"], r["scheduled_date"]))
