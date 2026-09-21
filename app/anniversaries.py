from datetime import date, datetime
from typing import List, Optional
from app.config import AnniversaryItem


def calculate_days_together(start_date_str: str, target_date: Optional[date] = None) -> int:
    """
    计算两人相伴的天数（相恋当天记为第 1 天）。
    """
    if not target_date:
        target_date = date.today()

    try:
        start_date = datetime.strptime(start_date_str.strip(), "%Y-%m-%d").date()
        diff = (target_date - start_date).days
        return max(1, diff + 1)
    except Exception:
        return 1


def calculate_next_anniversary(item: AnniversaryItem, target_date: Optional[date] = None) -> dict:
    """
    计算单个纪念日/重要事件的信息。
    智能区分：
    1. 过去已发生的纪念日（在一起、生日等）：优先展示【已经度过了多久 / 已相伴多少天】，并附上下次发生倒计时。
    2. 未来的计划事件：展示【还剩多少天】倒计时。
    3. 今天正是纪念日：高亮展示【🎉 今天正是...】庆祝标语。
    """
    if not target_date:
        target_date = date.today()

    try:
        orig_date = datetime.strptime(item.date.strip(), "%Y-%m-%d").date()
    except Exception:
        # 兼容不带年份的 MM-DD
        try:
            temp = datetime.strptime(item.date.strip(), "%m-%d").date()
            orig_date = date(target_date.year, temp.month, temp.day)
        except Exception:
            return {
                "id": item.id,
                "name": item.name,
                "icon": item.icon or "❤️",
                "days_remaining": 999,
                "days_passed": 0,
                "next_date": item.date,
                "is_today": False,
                "badge_text": "格式错误",
                "description": "日期格式错误",
                "years_count": 0
            }

    name_clean = item.name.strip()
    is_birthday = any(k in name_clean for k in ["生日", "出壳", "出生", "诞生"])
    is_together = any(k in name_clean for k in ["在一起", "相恋", "相爱", "恋爱", "领证", "结婚", "相识", "认识", "牵手", "表白", "初吻"])

    # 计算历史距今天数 (已度过天数)
    is_past = (orig_date <= target_date)
    days_passed = (target_date - orig_date).days
    if is_together:
        days_passed = max(1, days_passed + 1)
    else:
        days_passed = max(0, days_passed)

    if item.repeat_annually:
        # 处理闰年 2月29日
        def get_valid_date(y: int, m: int, d: int) -> date:
            if m == 2 and d == 29:
                try:
                    return date(y, 2, 29)
                except ValueError:
                    return date(y, 2, 28)
            return date(y, m, d)

        # 今年的发生日
        current_year_anniv = get_valid_date(target_date.year, orig_date.month, orig_date.day)

        if current_year_anniv < target_date:
            # 今年已过，下一次在明年
            next_date = get_valid_date(target_date.year + 1, orig_date.month, orig_date.day)
        else:
            # 今天或今年晚些时候
            next_date = current_year_anniv

        days_remaining = (next_date - target_date).days
        years_count = next_date.year - orig_date.year
        is_today = (days_remaining == 0)

        if is_today:
            if is_birthday:
                badge_text = f"🎂 今天生日！迎来了 {years_count} 岁"
                desc = "祝最亲爱的你生日快乐，所想皆成真！🎉"
            elif is_together:
                badge_text = f"🎉 今天正是 {years_count} 周年！"
                desc = f"已相依相伴度过 {days_passed} 天"
            else:
                badge_text = f"🎉 今天正是 {years_count} 周年！"
                desc = f"已走过 {years_count} 周年"
        else:
            # 区分：在一起纪念日显示“已相伴”、生日显示“已度过”、其他展示倒数与已度过
            if is_together:
                badge_text = f"已相伴 <strong>{days_passed}</strong> 天"
                desc = f"已携手走过 {years_count-1} 周年 · 距下次还有 {days_remaining} 天" if years_count > 1 else f"距下次周年还有 {days_remaining} 天"
            elif is_birthday:
                age = target_date.year - orig_date.year - (1 if (target_date.month, target_date.day) < (orig_date.month, orig_date.day) else 0)
                badge_text = f"已度过 <strong>{days_passed}</strong> 天"
                desc = f"来到世界第 {days_passed} 天 · 距 {age+1} 岁生日还有 {days_remaining} 天"
            elif is_past:
                badge_text = f"已度过 <strong>{days_passed}</strong> 天"
                desc = f"距下次纪念还有 {days_remaining} 天（累计 {years_count} 周年）"
            else:
                badge_text = f"还剩 <strong>{days_remaining}</strong> 天"
                desc = f"距首次还有 {days_remaining} 天"

        return {
            "id": item.id,
            "name": item.name,
            "icon": item.icon or ("🎂" if is_birthday else "❤️"),
            "days_remaining": days_remaining,
            "days_passed": days_passed,
            "next_date": next_date.strftime("%Y-%m-%d"),
            "is_today": is_today,
            "badge_text": badge_text,
            "description": desc,
            "years_count": max(0, years_count)
        }
    else:
        # 单次事件
        is_today = (orig_date == target_date)
        if is_today:
            badge_text = "🎉 就是今天！"
            desc = "今天正是这个特别的日子！"
            days_remaining = 0
        elif orig_date < target_date:
            days_remaining = (orig_date - target_date).days
            badge_text = f"已度过 <strong>{days_passed}</strong> 天"
            desc = f"发生于 {orig_date.strftime('%Y-%m-%d')}"
        else:
            days_remaining = (orig_date - target_date).days
            badge_text = f"还剩 <strong>{days_remaining}</strong> 天"
            desc = f"计划日期: {orig_date.strftime('%Y-%m-%d')}"

        return {
            "id": item.id,
            "name": item.name,
            "icon": item.icon or "📌",
            "days_remaining": days_remaining,
            "days_passed": days_passed,
            "next_date": orig_date.strftime("%Y-%m-%d"),
            "is_today": is_today,
            "badge_text": badge_text,
            "description": desc,
            "years_count": 0
        }


def get_sorted_anniversaries(items: List[AnniversaryItem], target_date: Optional[date] = None) -> List[dict]:
    """
    计算所有纪念日并按紧迫度排序：
    1. 今天正是纪念日的排在最前；
    2. 即将到来的按剩余天数由小到大排序；
    3. 已经过去的单次事件排在最后。
    """
    results = [calculate_next_anniversary(item, target_date) for item in items]

    def sort_key(x: dict):
        if x["is_today"]:
            return (0, 0)
        if x.get("days_remaining", 0) >= 0:
            return (1, x["days_remaining"])
        return (2, abs(x.get("days_remaining", 0)))

    results.sort(key=sort_key)
    return results
