from app.templates import render_email_html


def test_render_email_html():
    weather_data = {
        "city": "杭州",
        "current_temp": 24,
        "feels_like": 25,
        "max_temp": 28,
        "min_temp": 19,
        "condition": "晴朗",
        "icon": "☀️",
        "humidity": 60,
        "rain_chance": 15,
        "dressing_advice": ["出门无需带伞", "早晚温差较适宜"]
    }
    anniversaries = [
        {"name": "恋爱周年", "icon": "🌹", "days_remaining": 0, "is_today": True, "description": "今天正是 2 周年！🎉"},
        {"name": "宝贝生日", "icon": "🎂", "days_remaining": 45, "is_today": False, "description": "还有 45 天"}
    ]
    quote_info = {
        "content": "我寄你的信，总要送往邮局，不喜欢放在街边的绿色邮筒中，我总疑心那里会慢一点。",
        "source": "ai"
    }

    html = render_email_html(
        partner_name="小仙女",
        sender_name="大笨熊",
        days_together=520,
        weather_data=weather_data,
        anniversaries=anniversaries,
        quote_info=quote_info
    )

    assert "小仙女" in html
    assert "大笨熊" in html
    assert "520" in html
    assert "杭州" in html
    assert "恋爱周年" in html
    assert "宝贝生日" in html
    assert "今天正是 2 周年！" in html
    assert "出门无需带伞" in html
    assert "邮筒" in html
