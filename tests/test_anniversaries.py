from datetime import date
import pytest
from app.config import AnniversaryItem
from app.anniversaries import (
    calculate_days_together,
    calculate_next_anniversary,
    get_sorted_anniversaries,
)


def test_calculate_days_together():
    # 同一天算第 1 天
    today = date(2024, 5, 20)
    days = calculate_days_together("2024-05-20", target_date=today)
    assert days == 1

    # 隔天算第 2 天
    next_day = date(2024, 5, 21)
    days2 = calculate_days_together("2024-05-20", target_date=next_day)
    assert days2 == 2

    # 跨年 365 天 (2024-05-20 到 2025-05-20，2025不是闰年，差365天，第366天)
    year_later = date(2025, 5, 20)
    days3 = calculate_days_together("2024-05-20", target_date=year_later)
    assert days3 == 366


def test_annual_repeat_anniversary():
    today = date(2024, 6, 1)
    # 今年的 5-20 已经过去了，下一次应该是 2025-05-20
    item = AnniversaryItem(name="520", date="2020-05-20", repeat_annually=True, icon="❤️")
    res = calculate_next_anniversary(item, target_date=today)
    assert res["next_date"] == "2025-05-20"
    assert res["days_remaining"] > 300
    assert not res["is_today"]

    # 当天恰好是纪念日
    today_match = date(2024, 5, 20)
    res_today = calculate_next_anniversary(item, target_date=today_match)
    assert res_today["is_today"] is True
    assert res_today["days_remaining"] == 0
    assert res_today["years_count"] == 4


def test_non_repeating_anniversary():
    today = date(2024, 6, 1)
    # 未来单次事件
    future_item = AnniversaryItem(name="旅行", date="2024-06-11", repeat_annually=False, icon="✈️")
    res = calculate_next_anniversary(future_item, target_date=today)
    assert res["days_remaining"] == 10
    assert not res["is_today"]

    # 过去单次事件
    past_item = AnniversaryItem(name="旧事", date="2024-05-01", repeat_annually=False, icon="📌")
    res_past = calculate_next_anniversary(past_item, target_date=today)
    assert res_past["days_remaining"] == -31


def test_get_sorted_anniversaries():
    today = date(2024, 6, 1)
    items = [
        AnniversaryItem(name="很久之后", date="2024-12-01", repeat_annually=False),
        AnniversaryItem(name="今天就是", date="2020-06-01", repeat_annually=True),
        AnniversaryItem(name="明天到来", date="2024-06-02", repeat_annually=False),
    ]
    sorted_items = get_sorted_anniversaries(items, target_date=today)
    assert sorted_items[0]["name"] == "今天就是"
    assert sorted_items[1]["name"] == "明天到来"
    assert sorted_items[2]["name"] == "很久之后"
