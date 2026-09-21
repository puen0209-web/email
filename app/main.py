import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Header, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.config import AppConfig, load_config, save_config, AIConfig
from app.scheduler import mailer_scheduler
from app.weather import fetch_weather_data
from app.anniversaries import calculate_days_together, get_sorted_anniversaries
from app.ai_service import generate_morning_quote, test_ai_connection
from app.templates import render_email_html


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 生命周期：启动与关闭定时调度器"""
    config = load_config()
    mailer_scheduler.start(config)
    yield
    mailer_scheduler.shutdown()


app = FastAPI(
    title="Couple Daily Automation Mailer",
    description="情侣每日暖心早报与 Web 可视化管理面板",
    version="1.0.0",
    lifespan=lifespan
)

# 允许跨域（方便本地开发或反代）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_admin_access(
    x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key"),
    authorization: Optional[str] = Header(None),
    key: Optional[str] = Query(None)
):
    """
    统一安全鉴权依赖：验证客户端提供的管理密钥。
    支持 Header: X-Admin-Key、Authorization: Bearer <key> 或 URL 参数 ?key=<key>
    """
    config = load_config()
    valid_key = config.security.admin_password

    # 提取请求中的 key
    client_key = None
    if x_admin_key:
        client_key = x_admin_key
    elif authorization and authorization.startswith("Bearer "):
        client_key = authorization.split("Bearer ", 1)[1].strip()
    elif key:
        client_key = key

    if not client_key or not secrets.compare_digest(client_key, valid_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="管理访问密钥无效或未提供，请在右上角设置并输入正确的管理密码"
        )
    return True


# ==================== API 路由 ====================

@app.get("/api/status", dependencies=[Depends(verify_admin_access)])
async def get_system_status():
    """获取系统运行状态与调度信息"""
    status_data = mailer_scheduler.get_status()
    config = load_config()
    status_data["daily_time"] = config.recipient.daily_time
    status_data["partner_name"] = config.basic.partner_name
    status_data["city"] = config.basic.city
    return {"code": 0, "data": status_data}


@app.get("/api/config", dependencies=[Depends(verify_admin_access)])
async def get_configuration():
    """获取当前所有配置项"""
    config = load_config()
    return {"code": 0, "data": config.model_dump()}


@app.post("/api/config", dependencies=[Depends(verify_admin_access)])
async def update_configuration(new_config: AppConfig):
    """保存并立即热更新配置（动态重载调度器）"""
    save_config(new_config)
    mailer_scheduler.reschedule(new_config)
    return {
        "code": 0,
        "message": "配置已成功保存并立即生效，无需重启服务！",
        "data": mailer_scheduler.get_status()
    }


class TestSendPayload(BaseModel):
    override_to: Optional[str] = None


@app.post("/api/test-send", dependencies=[Depends(verify_admin_access)])
async def test_send_email(payload: Optional[TestSendPayload] = None):
    """立即执行一次早报生成与测试投递"""
    target = payload.override_to if payload else None
    success, msg, preview_data = await mailer_scheduler.execute_daily_dispatch(override_to=target)
    return {
        "code": 0 if success else 1,
        "success": success,
        "message": msg,
        "preview": preview_data
    }


@app.get("/api/preview", dependencies=[Depends(verify_admin_access)])
async def preview_email_html():
    """根据最新配置与实时天气，动态渲染 HTML 邮件视图供预览"""
    config = load_config()
    weather_data = await fetch_weather_data(config.basic.city, config.weather_rules)
    days_together = calculate_days_together(config.basic.relationship_start_date)
    anniversaries = get_sorted_anniversaries(config.anniversaries)

    quote_info = await generate_morning_quote(
        ai_config=config.ai,
        partner_name=config.basic.partner_name or "宝贝",
        days_together=days_together,
        weather_desc=weather_data.get("condition", "晴"),
        temp_c=weather_data.get("current_temp", 20),
        fallback_quotes=config.fallback_quotes
    )

    html = render_email_html(
        partner_name=config.basic.partner_name or "宝贝",
        sender_name=config.recipient.sender_name or "你的小熊",
        days_together=days_together,
        weather_data=weather_data,
        anniversaries=anniversaries,
        quote_info=quote_info
    )
    return HTMLResponse(content=html)


@app.post("/api/test-ai", dependencies=[Depends(verify_admin_access)])
async def test_ai_endpoint(ai_config: AIConfig):
    """独立测试大模型连通性与早安寄语生成效果"""
    res = await test_ai_connection(ai_config)
    return res


# ==================== 静态页面托管 ====================
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def serve_admin_index():
    """提供 Web Admin 仪表盘主页"""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return HTMLResponse("<h1>Couple Mailer 运行中</h1><p>未找到前端 index.html</p>")
