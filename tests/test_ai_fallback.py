import asyncio
from app.config import AIConfig
from app.ai_service import generate_morning_quote, get_random_fallback


def test_ai_disabled_fallback():
    ai_cfg = AIConfig(enabled=False)
    quotes = ["春风十里不如你", "山河远阔，人间烟火，无一是你，无一不是你"]

    res = asyncio.run(generate_morning_quote(
        ai_config=ai_cfg,
        partner_name="宝贝",
        days_together=100,
        weather_desc="晴",
        temp_c=22,
        fallback_quotes=quotes
    ))

    assert res["source"] == "local_fallback"
    assert res["content"] in quotes


def test_ai_empty_key_fallback():
    ai_cfg = AIConfig(enabled=True, api_key="")
    quotes = ["测试备用语录123"]

    res = asyncio.run(generate_morning_quote(
        ai_config=ai_cfg,
        partner_name="宝贝",
        days_together=520,
        weather_desc="微雨",
        temp_c=18,
        fallback_quotes=quotes
    ))

    assert res["source"] == "local_fallback"
    assert res["content"] == "测试备用语录123"
