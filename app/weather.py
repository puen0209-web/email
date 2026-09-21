import logging
from typing import Dict, Any, Optional
import httpx
from app.config import WeatherRulesConfig

logger = logging.getLogger(__name__)

# WMO 及常见英文天气描述映射至中文与表情
WEATHER_DESC_MAP = {
    "sunny": ("晴", "☀️"),
    "clear": ("晴朗", "☀️"),
    "partly cloudy": ("多云", "⛅"),
    "cloudy": ("阴天", "☁️"),
    "overcast": ("阴沉", "☁️"),
    "mist": ("薄雾", "🌫️"),
    "fog": ("大雾", "🌫️"),
    "freezing fog": ("冻雾", "🌫️"),
    "patchy rain possible": ("局部阵雨", "🌦️"),
    "patchy light drizzle": ("零星小雨", "🌦️"),
    "light drizzle": ("毛毛细雨", "🌦️"),
    "patchy light rain": ("小雨", "🌦️"),
    "light rain": ("小雨", "🌧️"),
    "moderate rain at times": ("间歇性中雨", "🌧️"),
    "moderate rain": ("中雨", "🌧️"),
    "heavy rain at times": ("强降雨", "🌧️"),
    "heavy rain": ("大雨", "🌧️"),
    "light freezing rain": ("冻雨", "🌧️"),
    "thundery outbreaks possible": ("雷阵雨可能", "⛈️"),
    "patchy light rain with thunder": ("雷阵小雨", "⛈️"),
    "moderate or heavy rain with thunder": ("雷阵大雨", "⛈️"),
    "patchy snow possible": ("局部小雪", "🌨️"),
    "light snow": ("小雪", "❄️"),
    "moderate snow": ("中雪", "❄️"),
    "heavy snow": ("大雪", "❄️"),
    "blizzard": ("暴风雪", "❄️"),
}


def translate_weather(desc_en: str) -> tuple[str, str]:
    """将英文天气描述转换为中文及相应 Emoji"""
    cleaned = desc_en.strip().lower()
    for key, val in WEATHER_DESC_MAP.items():
        if key in cleaned:
            return val
    return (desc_en.strip(), "🌤️")


async def fetch_weather_data(
    city: str,
    rules: Optional[WeatherRulesConfig] = None,
    district: str = "",
    country: str = ""
) -> Dict[str, Any]:
    """
    异步获取指定城市/区县的天气数据（使用免费开放的 wttr.in JSON API）。
    支持传入国家、城市、区县/郊区进行精细化天气定位。
    """
    if not rules:
        rules = WeatherRulesConfig()

    clean_city = city.strip()
    clean_district = district.strip()
    clean_country = country.strip()

    # 构造查询词：优先使用 "区县,城市" 提高精细度
    if clean_district:
        query_location = f"{clean_district},{clean_city}"
    else:
        query_location = clean_city

    # 构造人性化展示名
    parts = []
    if clean_country and clean_country not in ["中国", "China"]:
        parts.append(clean_country)
    if clean_city:
        parts.append(clean_city)
    if clean_district:
        parts.append(clean_district)
    display_name = " · ".join(parts) if parts else (clean_city or "本地")

    url = f"https://wttr.in/{query_location}?format=j1"
    headers = {"User-Agent": "curl/7.68.0", "Accept": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                return parse_wttr_response(display_name, data, rules)
            else:
                logger.warning(f"wttr.in 返回非 200 状态码: {resp.status_code} (查询: {query_location})")
    except Exception as e:
        logger.warning(f"获取天气数据失败 ({query_location}): {e}，启用备用数据")

    # 异常降级备用数据
    return get_fallback_weather(display_name, rules)


def parse_wttr_response(city: str, data: Dict[str, Any], rules: WeatherRulesConfig) -> Dict[str, Any]:
    """解析 wttr.in 的 JSON 数据结构并生成穿衣出行贴士"""
    current = data.get("current_condition", [{}])[0]
    weather_day = data.get("weather", [{}])[0]

    current_temp = float(current.get("temp_C", 20))
    feels_like = float(current.get("FeelsLikeC", current_temp))
    humidity = int(current.get("humidity", 50))
    uv_index = int(current.get("uvIndex", 3))

    raw_desc = current.get("weatherDesc", [{}])[0].get("value", "Clear")
    desc_zh, icon = translate_weather(raw_desc)

    max_temp = float(weather_day.get("maxtempC", current_temp + 3))
    min_temp = float(weather_day.get("mintempC", current_temp - 3))

    # 计算今日最高降雨概率
    rain_chances = []
    for slot in weather_day.get("hourly", []):
        try:
            rain_chances.append(int(slot.get("chanceofrain", 0)))
        except (ValueError, TypeError):
            pass
    max_rain_chance = max(rain_chances) if rain_chances else 0

    # 规则引擎计算建议
    advice_list = generate_dressing_advice(
        current_temp=current_temp,
        min_temp=min_temp,
        max_temp=max_temp,
        rain_chance=max_rain_chance,
        uv_index=uv_index,
        rules=rules
    )

    return {
        "city": city,
        "current_temp": int(round(current_temp)),
        "feels_like": int(round(feels_like)),
        "max_temp": int(round(max_temp)),
        "min_temp": int(round(min_temp)),
        "temp_spread": round(max_temp - min_temp, 1),
        "condition": desc_zh,
        "icon": icon,
        "humidity": humidity,
        "rain_chance": max_rain_chance,
        "uv_index": uv_index,
        "dressing_advice": advice_list,
        "is_fallback": False
    }


def generate_dressing_advice(
    current_temp: float,
    min_temp: float,
    max_temp: float,
    rain_chance: int,
    uv_index: int,
    rules: WeatherRulesConfig
) -> list[str]:
    """根据温差、降水、气温及紫外线生成温馨贴士列表"""
    tips = []

    # 1. 降雨带伞提示
    if rain_chance >= rules.rain_pop_threshold:
        tips.append(f"☂️ 今日降雨概率达 {rain_chance}%，出门记得带把伞，防雨防突变哦。")
    else:
        tips.append("🌤️ 今日降雨概率低，出行轻便无需带伞。")

    # 2. 昼夜温差提示
    spread = max_temp - min_temp
    if spread >= rules.temp_swing_threshold:
        tips.append(f"🧥 早晚温差有 {spread:.1f}°C，推荐洋葱式穿衣，随身带一件轻薄外套防凉。")

    # 3. 气温着装建议
    if max_temp >= rules.hot_threshold:
        tips.append("🥤 白天气温较高，建议着轻便透气棉麻衣物，注意补水防暑。")
    elif min_temp <= rules.cold_threshold:
        tips.append("🧣 气温偏低寒凉，记得穿暖防风厚外套，不要着凉了。")
    else:
        tips.append("👕 整体体感舒适，穿长袖 T 恤、薄卫衣或休闲针织衫正合适。")

    # 4. 紫外线提示
    if uv_index >= 6:
        tips.append("🧴 紫外线指数偏高，户外活动记得涂抹防晒霜或佩戴遮阳帽。")

    return tips


def get_fallback_weather(city: str, rules: WeatherRulesConfig) -> Dict[str, Any]:
    """离线或 API 超时情况下的备用平滑数据"""
    tips = [
        "🌤️ 今日天气宜人，出行轻便无忧。",
        "👕 穿搭建议：舒适长袖、休闲衬衫，元气出发！",
        "💧 记得多喝温水，保持好心情。"
    ]
    return {
        "city": city,
        "current_temp": 22,
        "feels_like": 22,
        "max_temp": 25,
        "min_temp": 18,
        "temp_spread": 7.0,
        "condition": "晴朗多云",
        "icon": "🌤️",
        "humidity": 55,
        "rain_chance": 10,
        "uv_index": 4,
        "dressing_advice": tips,
        "is_fallback": True
    }
