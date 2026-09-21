from datetime import datetime
from typing import Dict, Any, List


def render_email_html(
    partner_name: str,
    sender_name: str,
    days_together: int,
    weather_data: Dict[str, Any],
    anniversaries: List[Dict[str, Any]],
    quote_info: Dict[str, Any],
    current_date_str: str = ""
) -> str:
    """
    生成精美、温暖、响应式的 HTML 邮件内容（使用行内 CSS，兼顾各类邮件客户端）。
    """
    if not current_date_str:
        now = datetime.now()
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        current_date_str = f"{now.strftime('%Y年%m月%d日')} {weekdays[now.weekday()]}"

    # 穿衣出行建议 HTML
    advice_items_html = ""
    for tip in weather_data.get("dressing_advice", []):
        advice_items_html += f"""
        <div style="background: #ffffff; border-radius: 8px; padding: 8px 12px; margin-bottom: 6px; font-size: 13px; color: #4b5563; border: 1px solid #f0f2f5; display: flex; align-items: center;">
            <span style="line-height: 1.5;">{tip}</span>
        </div>
        """

    # 纪念日列表 HTML
    anniv_items_html = ""
    for item in anniversaries[:4]:  # 最多精选展示前4个重要节点
        is_today = item.get("is_today", False)
        badge_style = "background: linear-gradient(135deg, #ff416c, #ff4b2b); color: #ffffff;" if is_today else "background: #fff0f3; color: #e11d48; border: 1px solid #fecdd3;"
        tag_text = item.get("badge_text") or ("🎉 就是今天！" if is_today else f"还剩 <strong>{item.get('days_remaining')}</strong> 天")
        
        anniv_items_html += f"""
        <tr style="border-bottom: 1px dashed #f3f4f6;">
            <td style="padding: 10px 4px; font-size: 14px; color: #374151;">
                <span style="font-size: 16px; margin-right: 6px;">{item.get('icon', '❤️')}</span>
                <strong>{item.get('name')}</strong>
                <span style="display: block; font-size: 11px; color: #9ca3af; margin-top: 2px;">{item.get('description')}</span>
            </td>
            <td style="padding: 10px 4px; text-align: right; vertical-align: middle;">
                <span style="display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 12px; {badge_style}">
                    {tag_text}
                </span>
            </td>
        </tr>
        """

    quote_text = quote_info.get("content", "醒来觉得甚是爱你。")
    quote_badge = "大模型生成" if quote_info.get("source") == "ai" else "心语甄选"

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>早安，我的宝贝</title>
</head>
<body style="margin: 0; padding: 24px 12px; background-color: #fdf5f5; font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased;">
    <div style="max-width: 520px; margin: 0 auto; background-color: #ffffff; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 30px rgba(244, 114, 182, 0.12); border: 1px solid #ffe4e6;">
        
        <!-- 头部 Header -->
        <div style="background: linear-gradient(135deg, #fb7185 0%, #f43f5e 60%, #e11d48 100%); padding: 32px 24px 28px 24px; text-align: center; color: #ffffff;">
            <div style="font-size: 13px; letter-spacing: 1px; opacity: 0.92; margin-bottom: 6px;">{current_date_str}</div>
            <h1 style="margin: 0 0 14px 0; font-size: 24px; font-weight: 700; letter-spacing: 0.5px;">早安，{partner_name} ☀️</h1>
            
            <!-- 相伴天数胶囊徽章 -->
            <div style="display: inline-block; background: rgba(255, 255, 255, 0.22); border: 1px solid rgba(255, 255, 255, 0.45); backdrop-filter: blur(8px); padding: 7px 18px; border-radius: 30px; font-size: 14px; font-weight: 500;">
                ❤️ 与你相伴的第 <span style="font-size: 20px; font-weight: 800; color: #fff; margin: 0 2px;">{days_together}</span> 天
            </div>
        </div>

        <div style="padding: 24px 20px;">
            
            <!-- 天气与出行提示卡片 -->
            <div style="background: linear-gradient(180deg, #f0fdfa 0%, #f8fafc 100%); border: 1px solid #ccfbf1; border-radius: 16px; padding: 16px 18px; margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid #e6fcf5; padding-bottom: 10px;">
                    <div>
                        <span style="font-size: 16px; font-weight: 700; color: #0f766e;">📍 {weather_data.get('city')} · {weather_data.get('condition')}</span>
                    </div>
                    <div style="font-size: 28px;">{weather_data.get('icon', '🌤️')}</div>
                </div>

                <!-- 气温与基础数据 -->
                <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 12px;">
                    <tr>
                        <td style="width: 50%; vertical-align: middle;">
                            <span style="font-size: 34px; font-weight: 800; color: #134e4a;">{weather_data.get('current_temp')}°<span style="font-size: 18px; font-weight: 500;">C</span></span>
                            <span style="display: block; font-size: 12px; color: #64748b;">体感约 {weather_data.get('feels_like')}°C</span>
                        </td>
                        <td style="width: 50%; text-align: right; vertical-align: middle; font-size: 13px; color: #334155;">
                            <div>🌡️ 气温区间: <strong>{weather_data.get('min_temp')}°C ~ {weather_data.get('max_temp')}°C</strong></div>
                            <div style="margin-top: 4px;">💧 湿度: {weather_data.get('humidity')}% · 降水: {weather_data.get('rain_chance')}%</div>
                        </td>
                    </tr>
                </table>

                <!-- 穿衣搭配与出行建议 -->
                <div>
                    <div style="font-size: 12px; font-weight: 700; color: #0d9488; margin-bottom: 6px; letter-spacing: 0.5px;">👔 今日穿衣与贴心小贴士</div>
                    {advice_items_html}
                </div>
            </div>

            <!-- 纪念日与倒计时卡片 -->
            <div style="background: #ffffff; border: 1px solid #fee2e2; border-radius: 16px; padding: 16px 18px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(239, 68, 68, 0.04);">
                <div style="font-size: 14px; font-weight: 700; color: #991b1b; margin-bottom: 10px; display: flex; align-items: center;">
                    <span style="margin-right: 6px;">📅</span> 我们的纪念日足迹
                </div>
                <table width="100%" cellpadding="0" cellspacing="0">
                    <tbody>
                        {anniv_items_html}
                    </tbody>
                </table>
            </div>

            <!-- 今日早安絮语卡片 -->
            <div style="background: linear-gradient(135deg, #fff1f2 0%, #fffbf0 100%); border-left: 4px solid #f43f5e; border-radius: 0 16px 16px 0; padding: 18px 18px; position: relative;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-size: 13px; font-weight: 700; color: #be123c;">💌 今日晨间寄语</span>
                    <span style="font-size: 11px; background: rgba(244, 63, 94, 0.12); color: #e11d48; padding: 2px 8px; border-radius: 12px;">{quote_badge}</span>
                </div>
                <p style="margin: 0; font-size: 14px; line-height: 1.8; color: #4c0519; font-style: normal; text-align: justify;">
                    “{quote_text}”
                </p>
            </div>

            <!-- 结语与爱意落款 -->
            <div style="margin-top: 26px; text-align: center;">
                <div style="font-size: 14px; color: #4b5563; margin-bottom: 6px;">
                    新的一天，愿你阳光明媚，万事顺遂！
                </div>
                <div style="font-size: 14px; font-weight: 600; color: #e11d48;">
                    爱你的：{sender_name} 💖
                </div>
            </div>

        </div>

        <!-- 页脚 Footer -->
        <div style="background-color: #fafaf9; border-top: 1px solid #f5f5f4; padding: 14px 20px; text-align: center; font-size: 11px; color: #a8a29e;">
            <div>此邮件由专属 Couple Mailer 自动化服务贴心发送 · 愿爱意永不打烊</div>
        </div>

    </div>
</body>
</html>
"""
    return html
