import logging
import random
from typing import List, Optional
import httpx
from app.config import AIConfig

logger = logging.getLogger(__name__)


async def generate_morning_quote(
    ai_config: AIConfig,
    partner_name: str,
    days_together: int,
    weather_desc: str,
    temp_c: int,
    fallback_quotes: List[str]
) -> dict:
    """
    生成晨间情话：优先调用用户配置的 OpenAI 兼容大模型 API；
    若未启用、API Key 为空、请求超时或出错，则平滑降级至本地备用情话库。
    """
    if not ai_config.enabled:
        quote = get_random_fallback(fallback_quotes)
        return {"content": quote, "source": "local_fallback", "model": None}

    if not ai_config.api_key.strip():
        logger.info("AI 已开启但 API Key 为空，使用本地备用情话")
        quote = get_random_fallback(fallback_quotes)
        return {"content": quote, "source": "local_fallback", "model": None}

    # 构造更贴合当天场景的提示语
    user_prompt = (
        f"今天是美好的一天，我和我的伴侣【{partner_name}】相伴已是第 {days_together} 天。"
        f"今天我们所在城市天气为【{weather_desc}】，当前气温约为 {temp_c}°C。"
        f"请为 ta 专门写一段 50 到 80 字以内、温柔甜蜜又带有晨光气息的早安短语。不要任何多余的开头问候或标题，直接输出情话内容即可。"
    )

    try:
        content = await call_openai_compatible_api(ai_config, user_prompt)
        if content:
            return {"content": content.strip().strip('"“\''), "source": "ai", "model": ai_config.model}
    except Exception as e:
        logger.warning(f"大模型 API 调用失败 ({e})，降级使用备用情话")

    quote = get_random_fallback(fallback_quotes)
    return {"content": quote, "source": "local_fallback", "model": None}


async def call_openai_compatible_api(ai_config: AIConfig, prompt: str) -> str:
    """调用 OpenAI 兼容规范的 /chat/completions 接口"""
    base_url = ai_config.base_url.strip().rstrip("/")
    if not base_url.endswith("/chat/completions"):
        endpoint = f"{base_url}/chat/completions"
    else:
        endpoint = base_url

    headers = {
        "Authorization": f"Bearer {ai_config.api_key.strip()}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": ai_config.model.strip(),
        "messages": [
            {"role": "system", "content": ai_config.system_prompt.strip()},
            {"role": "user", "content": prompt}
        ],
        "temperature": ai_config.temperature,
        "max_tokens": ai_config.max_tokens
    }

    async with httpx.AsyncClient(timeout=12.0) as client:
        response = await client.post(endpoint, headers=headers, json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"HTTP {response.status_code}: {response.text}")
        
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise ValueError("API 返回 choices 为空")
        
        message = choices[0].get("message", {})
        return message.get("content", "")


def get_random_fallback(fallback_quotes: List[str]) -> str:
    """从本地备选语录库中随机挑选一条"""
    if not fallback_quotes:
        return "醒来觉得甚是爱你。新的一天，也要开开心心！"
    return random.choice(fallback_quotes)


async def test_ai_connection(ai_config: AIConfig) -> dict:
    """供前端 Web Admin 测试大模型连通性与配置可用性"""
    if not ai_config.api_key.strip():
        return {"success": False, "error": "请先填写 API Key 密钥"}

    test_prompt = "请用中文写一句简短温馨的早安情话（20字以内）。"
    try:
        content = await call_openai_compatible_api(ai_config, test_prompt)
        return {
            "success": True,
            "content": content.strip().strip('"“\''),
            "model": ai_config.model
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
