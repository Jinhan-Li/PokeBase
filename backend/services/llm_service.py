# backend/services/llm_service.py
"""通义千问 API 服务"""

import logging
import re
import time

from openai import OpenAI, APIConnectionError, RateLimitError, APITimeoutError
from config import DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, LLM_MODEL

logger = logging.getLogger(__name__)

client = OpenAI(
    api_key=DASHSCOPE_API_KEY,
    base_url=DASHSCOPE_BASE_URL,
    timeout=120.0,
)

MAX_RETRIES = 3
RETRY_DELAY = 1.0


def call_llm(prompt: str, temperature: float = 0.1, system_prompt: str = None) -> str:
    """调用通义千问 API，支持自动重试

    Args:
        prompt: 用户提示词
        temperature: 温度值（Cypher 生成建议 0.1，回答建议 0.3）
        system_prompt: 系统提示词（可选）

    Returns:
        LLM 返回的文本

    Raises:
        Exception: 重试耗尽后抛出异常
    """
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                temperature=temperature
            )
            content = response.choices[0].message.content
            # 思考模型（如 qwen3.5-flash）可能在 content 中包含 <think> 标签
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            logger.info(f"LLM call successful (attempt {attempt}), response length: {len(content)}")
            return content
        except (APIConnectionError, RateLimitError, APITimeoutError) as e:
            logger.warning(f"LLM call failed (attempt {attempt}/{MAX_RETRIES}): {type(e).__name__}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY * attempt)
            else:
                logger.error(f"LLM call exhausted after {MAX_RETRIES} retries")
                raise
        except Exception as e:
            logger.error(f"LLM call unexpected error: {type(e).__name__}: {e}")
            raise

    raise RuntimeError("LLM call failed unexpectedly")


if __name__ == "__main__":
    result = call_llm("1+1 等于几？请用中文回答")
    print(f"LLM 返回：{result}")
