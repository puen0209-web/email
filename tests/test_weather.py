from app.config import WeatherRulesConfig
from app.weather import translate_weather, generate_dressing_advice, parse_wttr_response, get_fallback_weather


def test_translate_weather():
    assert translate_weather("Sunny") == ("晴", "☀️")
    assert translate_weather("Partly cloudy") == ("多云", "⛅")
    assert translate_weather("Patchy rain possible") == ("局部阵雨", "🌦️")
    assert translate_weather("Heavy snow") == ("大雪", "❄️")
    assert translate_weather("Thunderstorm") == ("Thunderstorm", "🌤️")


def test_generate_dressing_advice():
    rules = WeatherRulesConfig(
        rain_pop_threshold=40,
        temp_swing_threshold=10.0,
        hot_threshold=30.0,
        cold_threshold=10.0
    )

    # 场景1：大温差、高降水、高温、高紫外线
    tips = generate_dressing_advice(
        current_temp=31.0,
        min_temp=18.0,
        max_temp=32.0,
        rain_chance=60,
        uv_index=7,
        rules=rules
    )
    assert any("带把伞" in t for t in tips)
    assert any("温差" in t for t in tips)
    assert any("防暑" in t or "棉麻" in t for t in tips)
    assert any("紫外线" in t or "防晒" in t for t in tips)

    # 场景2：无雨、小温差、低温
    tips2 = generate_dressing_advice(
        current_temp=8.0,
        min_temp=5.0,
        max_temp=10.0,
        rain_chance=10,
        uv_index=2,
        rules=rules
    )
    assert any("无需带伞" in t for t in tips2)
    assert any("防风厚外套" in t or "寒凉" in t for t in tips2)


def test_parse_wttr_response():
    mock_data = {
        "current_condition": [
            {
                "temp_C": "23",
                "FeelsLikeC": "24",
                "humidity": "65",
                "uvIndex": "5",
                "weatherDesc": [{"value": "Partly cloudy"}]
            }
        ],
        "weather": [
            {
                "maxtempC": "27",
                "mintempC": "19",
                "hourly": [
                    {"chanceofrain": "10"},
                    {"chanceofrain": "55"},
                    {"chanceofrain": "20"}
                ]
            }
        ]
    }
    rules = WeatherRulesConfig()
    result = parse_wttr_response("上海 · 浦东新区", mock_data, rules)
    assert result["city"] == "上海 · 浦东新区"
    assert result["current_temp"] == 23
    assert result["condition"] == "多云"
    assert result["rain_chance"] == 55
    assert len(result["dressing_advice"]) >= 2


def test_get_fallback_weather_with_district():
    rules = WeatherRulesConfig()
    fb = get_fallback_weather("墨尔本 · Carlton", rules)
    assert fb["city"] == "墨尔本 · Carlton"
    assert fb["is_fallback"] is True
