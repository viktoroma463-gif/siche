"""DeepSeek Chat Completions 客户端。不做任何本地模拟回退。"""

from __future__ import annotations

import httpx

from app.config import settings


class LLMError(RuntimeError):
    """DeepSeek 调用失败。"""


class LLMNotConfigured(LLMError):
    """未配置 API 密钥。"""


async def chat_completion(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.5,
    max_tokens: int | None = None,
) -> str:
    if not settings.llm_configured:
        raise LLMNotConfigured("未配置 DeepSeek API 密钥，请在 .env 中填写 SICHE_DEEPSEEK_API_KEY。")

    url = settings.siche_deepseek_base_url.rstrip("/") + "/chat/completions"
    payload: dict = {
        "model": settings.siche_deepseek_model,
        "messages": messages,
        "max_tokens": max_tokens or settings.siche_deepseek_max_tokens,
        "stream": False,
    }
    # deepseek-reasoner 不接受 temperature
    if "reasoner" not in settings.siche_deepseek_model:
        payload["temperature"] = temperature

    headers = {
        "Authorization": f"Bearer {settings.siche_deepseek_api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=settings.siche_deepseek_timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
    except httpx.TimeoutException as exc:
        raise LLMError("DeepSeek 响应超时，请稍后重试。") from exc
    except httpx.HTTPError as exc:
        raise LLMError(f"无法连接 DeepSeek：{exc}") from exc

    if resp.status_code >= 400:
        detail = resp.text.strip()[:300]
        raise LLMError(f"DeepSeek 接口返回 {resp.status_code}：{detail}")

    try:
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise LLMError("DeepSeek 返回格式异常，未取得有效内容。") from exc

    content = (content or "").strip()
    if not content:
        raise LLMError("DeepSeek 返回了空内容，请重试。")
    return content
