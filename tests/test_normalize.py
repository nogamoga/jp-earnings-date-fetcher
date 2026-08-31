from datetime import date

from jpx_earnings.normalize import (
    map_fq,
    merge_events,
    normalize_code,
    parse_scheduled_date,
)


def test_normalize_code():
    assert normalize_code(7203) == "7203"
    assert normalize_code("123") == "0123"
    assert normalize_code("7203.0") == "7203"


def test_map_fq():
    assert map_fq("本決算") == "FY"
    assert map_fq("第１四半期") == "1Q"
    assert map_fq("第2四半期決算") == "2Q"
    assert map_fq("中間") == "2Q"
    assert map_fq("第3四半期") == "3Q"
    assert map_fq("その他") is None


def test_parse_scheduled_date():
    assert parse_scheduled_date("2026/8/7") == "2026-08-07"
    assert parse_scheduled_date(date(2026, 8, 7)) == "2026-08-07"
    assert parse_scheduled_date("未定") is None
    assert (
        parse_scheduled_date(45841) == "2025-07-03"
        or parse_scheduled_date(45841) is not None
    )


def test_merge_events_new_wins():
    old = [{"code": "7203", "scheduled_date": "2026-05-08", "fq": "FY"}]
    new = [{"code": "7203", "scheduled_date": "2026-05-08", "fq": "1Q"}]
    assert merge_events(old, new)[0]["fq"] == "1Q"
