import json
import os
import uuid
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field


class AnniversaryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = Field(..., description="纪念日或事件名称")
    date: str = Field(..., description="日期，格式 YYYY-MM-DD")
    repeat_annually: bool = Field(default=True, description="是否每年重复")
    icon: str = Field(default="❤️", description="展示图标 Emoji")


class RecipientConfig(BaseModel):
    smtp_host: str = Field(default="smtp.qq.com", description="SMTP 服务器地址")
    smtp_port: int = Field(default=465, description="SMTP 端口 (465 SSL / 587 STARTTLS)")
    smtp_ssl: bool = Field(default=True, description="是否使用 SSL/TLS 直连 (465端口勾选)")
    sender_email: str = Field(default="", description="发件人邮箱")
    sender_password: str = Field(default="", description="发件人邮箱授权码/应用独立密码")
    sender_name: str = Field(default="你的小熊", description="发件人显示昵称")
    partner_email: str = Field(default="", description="伴侣收件人邮箱")
    partner_name: str = Field(default="亲爱的宝贝", description="伴侣称呼/昵称")
    cc_email: Optional[str] = Field(default="", description="抄送邮箱 (可选，留空则不抄送)")
    daily_time: str = Field(default="07:30", description="每日发送时间 (HH:MM 24小时制)")
    scheduler_enabled: bool = Field(default=True, description="是否开启每日定时发送")


class BasicConfig(BaseModel):
    partner_name: str = Field(default="亲爱的宝贝", description="伴侣称呼/昵称")
    city: str = Field(default="上海", description="目标城市 (支持中英文，如 上海/Shanghai)")
    relationship_start_date: str = Field(default="2023-01-01", description="相恋开始日期 (YYYY-MM-DD)")


class AIConfig(BaseModel):
    enabled: bool = Field(default=False, description="是否开启 AI 早安情话生成")
    base_url: str = Field(default="https://api.openai.com/v1", description="OpenAI 兼容 API 基础地址")
    api_key: str = Field(default="", description="API 密钥 (OpenAI / DeepSeek / 通义千问 / 本地模型等)")
    model: str = Field(default="gpt-4o-mini", description="模型名称 (如 gpt-4o-mini, deepseek-chat, qwen-plus)")
    system_prompt: str = Field(
        default="你是一个温柔体贴、深爱着对方的恋人。请用中文写一段大约50-80字的晨间问候情话，结合今日是清晨的氛围，语言自然真挚、温暖治愈、富有生活气息，不要油腻，不要说教。",
        description="早安情话提示词 / 人设语气"
    )
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="生成温度")
    max_tokens: int = Field(default=200, description="单次最大生成 token")


class WeatherRulesConfig(BaseModel):
    rain_pop_threshold: int = Field(default=30, description="降水概率预警阈值 (PoP %)")
    temp_swing_threshold: float = Field(default=8.0, description="昼夜温差提示阈值 (ΔT °C)")
    hot_threshold: float = Field(default=28.0, description="高温防暑提示阈值 (°C)")
    cold_threshold: float = Field(default=12.0, description="低温保暖提示阈值 (°C)")


class SecurityConfig(BaseModel):
    admin_password: str = Field(default="admin888", description="Web 管理面板访问口令")


DEFAULT_FALLBACK_QUOTES = [
    "醒来觉得甚是爱你。——朱生豪",
    "今天天气晴，宜收集阳光，宜想你一次又一次。",
    "我把今天的第一缕阳光和晨风，偷偷打包寄给你，早安呀。",
    "遇见你之后，每个平淡的日子都有了心动的理由。新的一天，也要开开心心！",
    "这世间所有的温柔和浪漫，都要留给我的小朋友一份。早安，我的宝贝！",
    "万物皆有回响，而我的思念回向于你。今天也要元气满满哦。",
    "你是我今天想要成为更好的人的全部理由。早安！",
    "早安！无论今天天气如何，你在我心里永远是微风不燥的晴天。",
    "愿你今天遇到的人都善意，碰到的事都顺心。记得按时吃早餐哦！",
    "早安，我最喜欢的小太阳。无论多忙，随时都有我陪着你。"
]


class AppConfig(BaseModel):
    recipient: RecipientConfig = Field(default_factory=RecipientConfig)
    basic: BasicConfig = Field(default_factory=BasicConfig)
    anniversaries: List[AnniversaryItem] = Field(
        default_factory=lambda: [
            AnniversaryItem(name="我们在一起", date="2023-01-01", repeat_annually=True, icon="❤️"),
            AnniversaryItem(name="宝贝生日", date="2000-06-18", repeat_annually=True, icon="🎂"),
            AnniversaryItem(name="下一次浪漫旅行", date="2026-10-01", repeat_annually=False, icon="✈️")
        ]
    )
    ai: AIConfig = Field(default_factory=AIConfig)
    weather_rules: WeatherRulesConfig = Field(default_factory=WeatherRulesConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    fallback_quotes: List[str] = Field(default_factory=lambda: list(DEFAULT_FALLBACK_QUOTES))


CONFIG_DIR = Path("data")
CONFIG_FILE = CONFIG_DIR / "config.json"


def get_config_path() -> Path:
    """获取配置文件路径，优先使用环境变量 CONFIG_PATH，否则使用默认 data/config.json"""
    env_path = os.getenv("CONFIG_PATH")
    if env_path:
        return Path(env_path)
    return CONFIG_FILE


def load_config(file_path: Optional[Path] = None) -> AppConfig:
    """从本地 JSON 文件读取配置，若不存在则创建默认配置"""
    path = file_path or get_config_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        default_cfg = AppConfig()
        save_config(default_cfg, path)
        return default_cfg

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return AppConfig.model_validate(data)
    except Exception as e:
        # 若配置文件格式解析失败，备份损坏文件并恢复安全默认
        backup_path = path.with_suffix(".json.bak")
        try:
            path.rename(backup_path)
        except Exception:
            pass
        default_cfg = AppConfig()
        save_config(default_cfg, path)
        return default_cfg


def save_config(config: AppConfig, file_path: Optional[Path] = None) -> None:
    """原子写入配置文件，防止掉电或并发造成损坏"""
    path = file_path or get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".tmp")

    payload = config.model_dump(mode="json")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # 原子替换
    tmp_path.replace(path)
