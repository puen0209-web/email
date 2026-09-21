import asyncio
import logging
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import AppConfig, load_config
from app.weather import fetch_weather_data
from app.anniversaries import calculate_days_together, get_sorted_anniversaries
from app.ai_service import generate_morning_quote
from app.templates import render_email_html
from app.mailer import send_email_async

logger = logging.getLogger(__name__)

JOB_ID = "daily_couple_email_job"


class DailyMailerScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.last_run_time: Optional[str] = None
        self.last_status: Optional[str] = None
        self.last_error: Optional[str] = None
        self.last_preview_data: Optional[Dict[str, Any]] = None

    def start(self, config: AppConfig):
        """初始化并启动后台定时调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("APScheduler 调度器已启动")
        self.reschedule(config)

    def shutdown(self):
        """优雅关闭调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("APScheduler 调度器已停止")

    def reschedule(self, config: AppConfig):
        """
        根据最新配置热重载定时任务，无需重启服务。
        """
        # 移除已有任务
        if self.scheduler.get_job(JOB_ID):
            self.scheduler.remove_job(JOB_ID)

        if not config.recipient.scheduler_enabled:
            logger.info("每日自动定时发送已在配置中禁用")
            return

        daily_time = config.recipient.daily_time.strip()
        try:
            parts = daily_time.split(":")
            hour = int(parts[0])
            minute = int(parts[1]) if len(parts) > 1 else 0
        except Exception:
            logger.error(f"时间格式无效 ({daily_time})，使用默认 07:30")
            hour, minute = 7, 30

        trigger = CronTrigger(hour=hour, minute=minute)
        self.scheduler.add_job(
            self._job_worker,
            trigger=trigger,
            id=JOB_ID,
            replace_existing=True,
            misfire_grace_time=3600
        )
        job = self.scheduler.get_job(JOB_ID)
        next_fire = getattr(job, "next_run_time", None)
        logger.info(f"已动态更新定时调度：每天 {hour:02d}:{minute:02d} 发送，下一次预计执行时间: {next_fire}")

    def _job_worker(self):
        """同步包装器，在后台调度线程中调用异步执行流程"""
        try:
            asyncio.run(self.execute_daily_dispatch())
        except Exception as e:
            logger.exception(f"定时任务后台执行失败: {e}")

    async def execute_daily_dispatch(self, override_to: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        执行完整每日晨报生成与投递流程：
        1. 抓取城市天气与穿衣建议
        2. 计算相恋天数与重要纪念日
        3. 调用大模型生成早安语录（支持降级）
        4. 渲染精美 HTML 邮件
        5. 调用 SMTP 进行投递
        """
        self.last_run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config = load_config()

        logger.info("开始构建并发送每日早报...")

        try:
            # 1. 天气与穿衣
            weather_data = await fetch_weather_data(
                city=config.basic.city,
                rules=config.weather_rules,
                district=getattr(config.basic, "district", ""),
                country=getattr(config.basic, "country", "")
            )

            # 2. 纪念日计算
            days_together = calculate_days_together(config.basic.relationship_start_date)
            anniversaries = get_sorted_anniversaries(config.anniversaries)

            # 3. AI 或备选情话
            quote_info = await generate_morning_quote(
                ai_config=config.ai,
                partner_name=config.basic.partner_name or "宝贝",
                days_together=days_together,
                weather_desc=weather_data.get("condition", "晴"),
                temp_c=weather_data.get("current_temp", 20),
                fallback_quotes=config.fallback_quotes
            )

            # 4. 渲染 HTML
            html_content = render_email_html(
                partner_name=config.basic.partner_name or "宝贝",
                sender_name=config.recipient.sender_name or "你的小熊",
                days_together=days_together,
                weather_data=weather_data,
                anniversaries=anniversaries,
                quote_info=quote_info
            )

            # 暂存预览数据
            self.last_preview_data = {
                "weather": weather_data,
                "days_together": days_together,
                "anniversaries": anniversaries,
                "quote_info": quote_info,
                "html": html_content
            }

            # 邮件主题
            subject = f"☀️ 早安！与你相伴第 {days_together} 天 · {weather_data.get('city')}今日天气与贴心早报"

            # 5. 投递
            success, msg = await send_email_async(
                recipient_cfg=config.recipient,
                subject=subject,
                html_content=html_content,
                override_to=override_to
            )

            self.last_status = "成功" if success else "失败"
            self.last_error = None if success else msg
            return success, msg, self.last_preview_data

        except Exception as e:
            err = f"执行晨报生成任务发生异常: {str(e)}"
            logger.exception(err)
            self.last_status = "异常"
            self.last_error = err
            return False, err, {}

    def get_status(self) -> dict:
        """获取调度器的当前运行状态及下次执行时间"""
        job = self.scheduler.get_job(JOB_ID)
        next_run = None
        if job:
            next_run_val = getattr(job, "next_run_time", None)
            if next_run_val:
                next_run = next_run_val.strftime("%Y-%m-%d %H:%M:%S")

        return {
            "scheduler_running": self.scheduler.running,
            "job_exists": job is not None,
            "next_run_time": next_run,
            "last_run_time": self.last_run_time,
            "last_status": self.last_status,
            "last_error": self.last_error
        }


# 全局单例调度器
mailer_scheduler = DailyMailerScheduler()
