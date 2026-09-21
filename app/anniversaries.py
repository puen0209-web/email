from datetime import date, datetime
from typing import List, Optional
from app.config import AnniversaryItem


def calculate_days_together(start_date_str: str, target_date: Optional[date] = None) -> int:
    """
    计算两人相伴的天数（通常相恋当天记为第 1 天）。
    如果输入的开始日期晚于目标日期，则返回 0 或负倒计天数。
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
    计算单个纪念日/重要事件的倒计时信息。
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
                "next_date": item.date,
                "is_today": False,
                "description": "日期格式错误",
                "years_count": 0
            }

    if item.repeat_annually:
        # 处理 2月29日 闰年情况
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
            desc = f"今天正是 {years_count} 周年纪念日！🎉" if years_count > 0 else "今天正是这个特别的日子！🎉"
        else:
            desc = f"还有 {days_remaining} 天（{years_count} 周年）" if years_count > 0 else f"还有 {days_remaining} 天"

        return {
            "id": item.id,
            "name": item.name,
            "icon": item.icon or "❤️",
            "days_remaining": days_remaining,
            "next_date": next_date.strftime("%Y-%m-%d"),
            "is_today": is_today,
            "description": desc,
            "years_count": max(0, years_count)
        }
    else:
        # 单次事件
        days_remaining = (orig_date - target_date).days
        is_today = (days_remaining == 0)

        if is_today:
            desc = "就是今天！🎉"
        elif days_remaining > 0:
            desc = f"还有 {days_remaining} 天"
        else:
            desc = f"已过去 {abs(days_remaining)} 天"

        return {
            "id": item.id,
            "name": item.name,
            "icon": item.icon or "📌",
            "days_remaining": days_remaining,
            "next_date": orig_date.strftime("%Y-%m-%d"),
            "is_today": is_today,
            "description": desc,
            "years_count": 0
        }


def get_sorted_anniversaries(items: List[AnniversaryItem], target_date: Optional[date] = None) -> List[dict]:
    """
    计算所有纪念日并按紧迫度排序：
    1. 今天正是纪念日的排最前；
    2. 未来即将到来的按剩余天数由小到大排序；
    3. 已经过去的单次事件排在最后。
    """
    results = [calculate_next_anniversary(item, target_date) for item in items]

    def sort_key(x: dict):
        if x["is_today"]:
            return (0, 0)
        if x["days_remaining"] >= 0:
            return (1, x["days_remaining"])
        return (2, abs(x["days_remaining"]))

    results.sort(key=sort_key)
    return results
